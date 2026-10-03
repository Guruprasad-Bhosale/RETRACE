"""RETRACE Operational Telemetry and Observability Package.

Contains OpenTelemetry tracing abstractions, Prometheus metrics registry,
and request correlation utilities.
"""

from packages.telemetry.metrics import metrics_registry
from packages.telemetry.provider import get_tracer, setup_telemetry
from packages.telemetry.tracer import trace_span

__all__ = ["get_tracer", "metrics_registry", "setup_telemetry", "trace_span"]
