"""etl_common.observability — structured logging for the ETL pipeline.

Re-exports the public surface of the logging module so callers can do:
    from etl_common.observability import configure_logging, get_logger
"""

from etl_common.observability.logging import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
