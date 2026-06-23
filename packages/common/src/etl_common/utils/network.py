import http.client
import random
import time
from collections.abc import Callable
from typing import Any

from etl_common.observability import get_logger

_log = get_logger(__name__)

MAX_RETRIES = 5
INITIAL_BACKOFF = 2
MAX_BACKOFF = 60

_RETRYABLE = (
    http.client.ResponseNotReady,
    http.client.HTTPException,
    ConnectionError,
    BrokenPipeError,
    TimeoutError,
)


def execute_with_retry(
    func: Callable[..., Any],
    *args: Any,
    operation_name: str = "Operation",
    **kwargs: Any,
) -> Any:
    """Exponential-backoff retry for transient network errors."""
    retry_count = 0
    backoff_time = INITIAL_BACKOFF

    while retry_count <= MAX_RETRIES:
        try:
            return func(*args, **kwargs)
        except _RETRYABLE as e:
            retry_count += 1

            if retry_count > MAX_RETRIES:
                _log.error(
                    "operation_exhausted",
                    operation=operation_name,
                    retries=MAX_RETRIES,
                    error=type(e).__name__,
                )
                raise

            jitter = random.uniform(0, 0.1 * backoff_time)
            wait_time = backoff_time + jitter

            _log.warning(
                "operation_retry",
                operation=operation_name,
                attempt=retry_count,
                max_retries=MAX_RETRIES,
                error=type(e).__name__,
                wait_seconds=round(wait_time, 2),
            )

            time.sleep(wait_time)

            backoff_time = min(backoff_time * 2, MAX_BACKOFF)
        except Exception as e:
            _log.error(
                "operation_failed",
                operation=operation_name,
                error_type=type(e).__name__,
                error=str(e),
            )
            raise
