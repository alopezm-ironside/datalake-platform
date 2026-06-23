"""Sync-state control-plane port.

Concrete adapters (BigQuerySyncState, …) must implement this interface.
The pipeline depends only on this port — it never imports BigQuery or any
storage detail.
"""

from abc import ABC, abstractmethod

from etl_common.interfaces.sync_stats import SyncStats


class SyncStateInterface(ABC):
    """Abstract control-plane port for run lifecycle and watermark management.

    One run row per pipeline execution, updated in place:
    - start()      → INSERT row with status="running", return sync_batch_id
    - checkpoint() → UPDATE row advancing last_processed_id + counters
    - finish()     → UPDATE row with final status and completed_at

    Watermark semantics: stale watermark causes reprocess, not data loss,
    because save_batch is append-only (Bronze tolerates duplicate versions).
    """

    @abstractmethod
    def get_watermark(self, module_name: str) -> int:
        """Return last_processed_id from the most recent success run.

        Args:
            module_name: Logical ETL module identifier (e.g. "accounting").

        Returns:
            Last successfully processed ID, or 0 if no prior run exists.
        """

    @abstractmethod
    def start(self, module_name: str, sync_type: str = "incremental") -> str:
        """Insert a new run row and return its sync_batch_id.

        The returned sync_batch_id is used as Bronze sync_batch_id for all
        batches in the run, and for checkpoint/finish calls.

        Args:
            module_name: Logical ETL module identifier.
            sync_type:   "incremental" (default) or "full".

        Returns:
            Unique sync_batch_id (uuid4 string).
        """

    @abstractmethod
    def checkpoint(
        self,
        sync_batch_id: str,
        last_processed_id: int,
        stats: SyncStats,
    ) -> None:
        """Update the run row in place after a data commit.

        Must be called AFTER repository.save_batch() commits — never before.
        A crash between save_batch and checkpoint causes the next run to
        reprocess from the previous watermark, which is safe (Bronze append).

        Args:
            sync_batch_id:      ID of the active run row.
            last_processed_id:  Highest entity ID successfully committed.
            stats:              Accumulation counters for this batch.
        """

    @abstractmethod
    def finish(
        self,
        sync_batch_id: str,
        status: str,
        last_processed_id: int,
        error_message: str | None = None,
    ) -> None:
        """Finalize the run row.

        Args:
            sync_batch_id:      ID of the active run row.
            status:             "success" or "failed".
            last_processed_id:  Final watermark for this run.
            error_message:      Error detail when status="failed".
        """
