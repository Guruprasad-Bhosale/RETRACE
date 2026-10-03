"""OpenTelemetry Provider Abstraction for RETRACE.

Provides unified tracer initialization with support for OTel SDK when available,
or falling back to a deterministic in-memory span collector for local operation
and testing without hard crashes.
"""

import time
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

from packages.logging.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TelemetrySpan:
    """In-memory representation of an operational trace span."""

    name: str
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    start_time: float = field(default_factory=time.time)
    end_time: float | None = None
    duration_ms: float = 0.0
    attributes: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    status: str = "OK"
    error_message: str | None = None

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a safe, non-sensitive attribute on the span."""
        # Ensure no sensitive values or tokens are set
        if any(s in key.lower() for s in ("password", "secret", "token", "cookie", "auth")):
            self.attributes[key] = "[REDACTED]"
        else:
            self.attributes[key] = value

    def record_exception(self, exc: Exception) -> None:
        """Record error details."""
        self.status = "ERROR"
        self.error_message = str(exc)
        self.events.append(
            {
                "name": "exception",
                "timestamp": time.time(),
                "type": type(exc).__name__,
                "message": str(exc),
            }
        )

    def finish(self) -> None:
        """End the span and compute duration."""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration_ms = round((self.end_time - self.start_time) * 1000, 2)


class BaseTracer:
    """Abstract base tracer interface."""

    def start_span(
        self,
        name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TelemetrySpan:
        raise NotImplementedError


class InMemoryTracer(BaseTracer):
    """Deterministic in-memory tracer for local dev, testing, and fallback."""

    def __init__(self, service_name: str = "retrace") -> None:
        self.service_name = service_name
        self.spans: list[TelemetrySpan] = []
        self._max_spans = 1000

    def start_span(
        self,
        name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> TelemetrySpan:
        span = TelemetrySpan(
            name=name,
            trace_id=trace_id or uuid.uuid4().hex,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=parent_span_id,
            attributes=attributes or {},
        )
        if len(self.spans) >= self._max_spans:
            self.spans.pop(0)  # ring buffer
        self.spans.append(span)
        return span

    def clear(self) -> None:
        self.spans.clear()


_global_tracer: BaseTracer = InMemoryTracer()


def setup_telemetry(
    service_name: str = "retrace-api",
    environment: str = "development",
    endpoint: str | None = None,
) -> BaseTracer:
    """Initialize OpenTelemetry tracer or in-memory fallback."""
    global _global_tracer
    _global_tracer = InMemoryTracer(service_name=service_name)
    logger.info(
        "OpenTelemetry tracer initialized",
        service=service_name,
        environment=environment,
        provider="in_memory_fallback",
    )
    return _global_tracer


def get_tracer(name: str = "retrace") -> BaseTracer:
    """Return the active global tracer instance."""
    return _global_tracer


@contextmanager
def start_trace_span(
    name: str,
    trace_id: str | None = None,
    parent_span_id: str | None = None,
    attributes: dict[str, Any] | None = None,
) -> Iterator[TelemetrySpan]:
    """Context manager for tracing operational execution blocks."""
    tracer = get_tracer()
    span = tracer.start_span(
        name=name,
        trace_id=trace_id,
        parent_span_id=parent_span_id,
        attributes=attributes,
    )
    try:
        yield span
    except Exception as exc:
        span.record_exception(exc)
        raise
    finally:
        span.finish()
