"""RETRACE Tracing Helpers and Decorators.

Provides span context managers and decorators for instrumenting API, Worker,
Database, Redis, and Browser execution stages.
"""

import functools
from collections.abc import Callable
from typing import Any

from packages.telemetry.provider import start_trace_span


def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Callable[..., Any]:
    """Decorator to trace an asynchronous or synchronous function execution."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if functools.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                span_attrs = dict(attributes or {})
                with start_trace_span(name=name, attributes=span_attrs) as span:
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as exc:
                        span.record_exception(exc)
                        raise

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                span_attrs = dict(attributes or {})
                with start_trace_span(name=name, attributes=span_attrs) as span:
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as exc:
                        span.record_exception(exc)
                        raise

            return sync_wrapper

    return decorator


class TraceContext:
    """Helper for manual span lifecycle management across async worker phases."""

    @staticmethod
    def span(
        name: str,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Any:
        return start_trace_span(
            name=name,
            trace_id=trace_id,
            parent_span_id=parent_span_id,
            attributes=attributes,
        )
