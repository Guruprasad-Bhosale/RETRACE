"""Structured Logging System for RETRACE.

Provides unified JSON / console formatted structured logging with contextual fields
(service, environment, request_id, trace_id, organization_id, user_id, analysis_id, job_id)
and automatic redaction of sensitive credentials.
"""

import logging
import sys
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

import structlog

# Context variable holders for correlation
_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
_org_id_var: ContextVar[str | None] = ContextVar("organization_id", default=None)
_user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)
_analysis_id_var: ContextVar[str | None] = ContextVar("analysis_id", default=None)

# Sensitive keys to automatically redact
SENSITIVE_KEYS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "cookie",
    "cookies",
    "aws_secret_access_key",
    "secret_key",
    "jwt",
    "access_token",
}


class LogEvents:
    """Standardized operational log event names."""

    API_REQUEST = "api.request"
    API_ERROR = "api.error"
    ANALYSIS_CREATED = "analysis.created"
    ANALYSIS_STARTED = "analysis.started"
    ANALYSIS_COMPLETED = "analysis.completed"
    ANALYSIS_FAILED = "analysis.failed"
    WORKER_JOB_CLAIMED = "worker.job.claimed"
    WORKER_JOB_COMPLETED = "worker.job.completed"
    WORKER_JOB_FAILED = "worker.job.failed"
    ARTIFACT_CREATED = "artifact.created"
    ARTIFACT_UPLOADED = "artifact.uploaded"
    ARTIFACT_DELETED = "artifact.deleted"
    AUTH_LOGIN = "auth.login"
    AUTH_FAILURE = "auth.failure"
    AUTHORIZATION_DENIED = "authorization.denied"


def set_correlation_context(
    request_id: str | None = None,
    trace_id: str | None = None,
    organization_id: str | None = None,
    user_id: str | None = None,
    analysis_id: str | None = None,
) -> None:
    """Bind correlation context for current async task/thread."""
    if request_id is not None:
        _request_id_var.set(request_id)
    if trace_id is not None:
        _trace_id_var.set(trace_id)
    if organization_id is not None:
        _org_id_var.set(organization_id)
    if user_id is not None:
        _user_id_var.set(user_id)
    if analysis_id is not None:
        _analysis_id_var.set(analysis_id)


def clear_correlation_context() -> None:
    """Clear all correlation context."""
    _request_id_var.set(None)
    _trace_id_var.set(None)
    _org_id_var.set(None)
    _user_id_var.set(None)
    _analysis_id_var.set(None)


def redact_sensitive_data(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Scrub passwords, keys, and tokens from structured log event dictionary."""
    def _sanitize(val: Any) -> Any:
        if isinstance(val, dict):
            return {
                k: "[REDACTED]" if any(s in k.lower() for s in SENSITIVE_KEYS) else _sanitize(v)
                for k, v in val.items()
            }
        if isinstance(val, list):
            return [_sanitize(item) for item in val]
        return val

    for key, value in list(event_dict.items()):
        if any(s in key.lower() for s in SENSITIVE_KEYS):
            event_dict[key] = "[REDACTED]"
        elif isinstance(value, (dict, list)):
            event_dict[key] = _sanitize(value)

    return event_dict


def add_correlation_context(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Inject active correlation variables into every log record."""
    req_id = _request_id_var.get()
    trace_id = _trace_id_var.get()
    org_id = _org_id_var.get()
    u_id = _user_id_var.get()
    a_id = _analysis_id_var.get()

    if req_id and "request_id" not in event_dict:
        event_dict["request_id"] = req_id
    if trace_id and "trace_id" not in event_dict:
        event_dict["trace_id"] = trace_id
    if org_id and "organization_id" not in event_dict:
        event_dict["organization_id"] = org_id
    if u_id and "user_id" not in event_dict:
        event_dict["user_id"] = u_id
    if a_id and "analysis_id" not in event_dict:
        event_dict["analysis_id"] = a_id

    return event_dict


def setup_logging(
    service_name: str = "retrace-api",
    log_level: str = "INFO",
    environment: str = "development",
) -> None:
    """Configure structured logging for the application."""
    level = getattr(logging, log_level.upper(), logging.INFO)

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_correlation_context,
        redact_sensitive_data,
    ]

    # Add default application context
    def add_app_context(
        logger: Any, method_name: str, event_dict: dict[str, Any]
    ) -> dict[str, Any]:
        event_dict.setdefault("service", service_name)
        event_dict.setdefault("environment", environment)
        return event_dict

    shared_processors.insert(0, add_app_context)

    if environment in ("production", "staging"):
        renderer: Callable[..., str] = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = True
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Return a configured structured logger bound to the provided name."""
    return structlog.get_logger(name)
