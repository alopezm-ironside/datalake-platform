"""Structured JSON logging for the modular ETL engine — ADR-8.

Public surface:
    configure_logging()  — wire the structlog processor chain once at app start.
    get_logger(name)     — return a bound structlog logger for a module.

Processor chain (produces single-line JSON to stdout with GCP keys):
    merge_contextvars
    → _add_severity  (custom: maps stdlib level → "severity" GCP key)
    → TimeStamper(fmt="iso", utc=True)
    → EventRenamer("message")   (renames "event" → "message")
    → JSONRenderer()

Cloud Run + Cloud Logging auto-parse single-line JSON on stdout —
no logging agent or sink config required in app code.

Context binding (caller responsibility):
    from structlog.contextvars import bind_contextvars, clear_contextvars
    bind_contextvars(module="accounting", sync_batch_id="...")
    # ... log lines automatically carry those fields ...
    clear_contextvars()

Idempotency: a module-level sentinel prevents double-configuration so
calling configure_logging() from tests or re-used processes is safe.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

import structlog
from structlog.types import EventDict

# Sentinel: True once the processor chain is wired. Guards against
# duplicate processor registration in re-used or test processes.
_configured: bool = False

# GCP severity levels mapped from structlog/stdlib level names.
_LEVEL_TO_SEVERITY: dict[str, str] = {
    "debug": "DEBUG",
    "info": "INFO",
    "warning": "WARNING",
    "warn": "WARNING",
    "error": "ERROR",
    "critical": "CRITICAL",
}


def _add_severity(
    _logger: Any,
    method: str,
    event_dict: MutableMapping[str, Any],
) -> EventDict:
    """Processor: add GCP-recognised 'severity' key from the log method name.

    Replaces the default 'level' key so Cloud Logging can parse the log level
    without additional configuration.
    """
    # method is the log method name: "debug", "info", "warning", "error", etc.
    event_dict["severity"] = _LEVEL_TO_SEVERITY.get(method.lower(), method.upper())
    return event_dict


def configure_logging() -> None:
    """Configure structlog to render single-line JSON to stdout.

    Idempotent: calling more than once is safe and has no effect after
    the first call. Must be called ONCE at the composition root before
    any log call, and BEFORE injecting context via bind_contextvars.
    """
    global _configured
    if _configured:
        return

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_severity,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.EventRenamer("message"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    _configured = True


def get_logger(name: str) -> Any:
    """Return a structlog bound logger for the given module name.

    Returns Any to avoid strict-mypy complications with structlog's
    highly generic BoundLogger type. Callers should use duck-typing
    (log.info / log.error / log.warning) rather than the concrete type.

    Args:
        name: Typically __name__ of the calling module.
    """
    return structlog.get_logger(name)
