"""BigQuery implementation of SyncStateInterface.

Owns one row in control.sync_metadata per pipeline run, updated in place:
- start()      → INSERT row with status="running"
- checkpoint() → UPDATE row advancing last_processed_id + counters
- finish()     → UPDATE row with final status and completed_at
"""

import uuid
from datetime import datetime, timezone

from etl_common.infrastructure.bigquery_connection import BigQueryConnection
from etl_common.interfaces.sync_state_interface import SyncStateInterface
from etl_common.interfaces.sync_stats import SyncStats
from etl_common.models.sync_metadata import SyncMetadata
from sqlalchemy import update
from sqlalchemy.orm import Session


class BigQuerySyncState(SyncStateInterface):
    """Control-plane adapter that tracks sync runs in control.sync_metadata."""

    def __init__(self, connection: BigQueryConnection, control_dataset: str) -> None:
        self._engine = connection.engine
        self._control_dataset = control_dataset

    def get_watermark(self, module_name: str) -> int:
        """Return last_processed_id from the most recent success run, else 0."""
        with Session(self._engine) as session:
            row = (
                session.query(SyncMetadata)
                .filter(SyncMetadata.module_name == module_name)
                .filter(SyncMetadata.status == "success")
                .order_by(SyncMetadata.started_at.desc())
                .first()
            )
            if row and row.last_processed_id is not None:
                return row.last_processed_id
            return 0

    def start(self, module_name: str, sync_type: str = "incremental") -> str:
        """Insert a new run row with status=running and return its sync_batch_id."""
        sync_batch_id = str(uuid.uuid4())
        row = SyncMetadata(
            sync_id=sync_batch_id,
            module_name=module_name,
            sync_type=sync_type,
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        with Session(self._engine) as session:
            session.add(row)
            session.commit()
        return sync_batch_id

    def checkpoint(
        self,
        sync_batch_id: str,
        last_processed_id: int,
        stats: SyncStats,
    ) -> None:
        """UPDATE the run row in place after a data commit."""
        stmt = (
            update(SyncMetadata)
            .where(SyncMetadata.sync_id == sync_batch_id)
            .values(
                last_processed_id=last_processed_id,
                records_processed=stats.records_processed,
                records_inserted=stats.records_inserted,
                records_failed=stats.records_failed,
            )
        )
        with Session(self._engine) as session:
            session.execute(stmt)
            session.commit()

    def finish(
        self,
        sync_batch_id: str,
        status: str,
        last_processed_id: int,
        error_message: str | None = None,
    ) -> None:
        """UPDATE the run row with final status and completed_at."""
        completed_at = datetime.now(timezone.utc)
        stmt = (
            update(SyncMetadata)
            .where(SyncMetadata.sync_id == sync_batch_id)
            .values(
                status=status,
                last_processed_id=last_processed_id,
                completed_at=completed_at,
                error_message=error_message,
            )
        )
        with Session(self._engine) as session:
            session.execute(stmt)
            session.commit()
