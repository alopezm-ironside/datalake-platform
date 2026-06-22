import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from etl_common.models.sync_metadata import SyncMetadata

logger = logging.getLogger(__name__)


class SyncTracker:
    """Rastrea el estado de las sincronizaciones usando SQLAlchemy."""

    def __init__(self, session: Session, module_name: str):
        self.session = session
        self.module_name = module_name
        self.sync_id = str(uuid.uuid4())
        self.started_at = None
        self.metadata_record = None
        self.stats = {
            'records_processed': 0,
            'records_inserted': 0,
            'records_failed': 0,
            'odoo_api_calls': 0,
        }

    def start(self, sync_type: str = 'incremental'):
        """Inicia el tracking de una sincronización."""
        self.started_at = datetime.now(timezone.utc)
        self.sync_type = sync_type

        # Crear registro en BigQuery
        self.metadata_record = SyncMetadata(
            sync_id=self.sync_id,
            module_name=self.module_name,
            sync_type=sync_type,
            started_at=self.started_at,
            status='running',
            records_processed=0,
            records_inserted=0,
            records_failed=0,
            odoo_api_calls=0
        )

        self.session.add(self.metadata_record)
        self.session.commit()

        logger.info(f"🚀 Sincronización iniciada: {self.sync_id}")
        logger.info(f"   Módulo: {self.module_name}")
        logger.info(f"   Tipo: {sync_type}")

    def update_stats(self, **kwargs):
        """Actualiza estadísticas del sync."""
        for key, value in kwargs.items():
            if key in self.stats:
                self.stats[key] += value

    def finish(self, status: str, last_processed_id: int, error_message: Optional[str] = None):
        """Finaliza el tracking y actualiza metadata en BigQuery."""
        completed_at = datetime.now(timezone.utc)
        execution_time = (completed_at - self.started_at).total_seconds()

        # Actualizar registro
        self.metadata_record.completed_at = completed_at
        self.metadata_record.status = status
        self.metadata_record.last_processed_id = last_processed_id
        self.metadata_record.records_processed = self.stats['records_processed']
        self.metadata_record.records_inserted = self.stats['records_inserted']
        self.metadata_record.records_failed = self.stats['records_failed']
        self.metadata_record.odoo_api_calls = self.stats['odoo_api_calls']
        self.metadata_record.execution_time_seconds = execution_time
        self.metadata_record.error_message = error_message

        self.session.commit()

        logger.info(f"✅ Sincronización completada: {status}")
        logger.info(f"   Registros procesados: {self.stats['records_processed']}")
        logger.info(f"   Tiempo: {execution_time:.2f}s")
