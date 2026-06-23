from dataclasses import dataclass


@dataclass
class SyncStats:
    """Typed value object carrying per-batch accumulation counters.

    Passed to checkpoint() so the control row can accumulate run-level
    KPIs without the pipeline knowing about the storage schema.
    """

    records_processed: int
    records_inserted: int
    records_failed: int
    source_api_calls: int
