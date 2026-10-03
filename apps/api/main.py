"""RETRACE Core FastAPI Application Entrypoint."""

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from apps.api.routers.health import router as health_router
from apps.api.routers.v1 import v1_router
from packages.config.settings import get_settings
from packages.db.session import close_database
from packages.logging.logger import (
    LogEvents,
    clear_correlation_context,
    get_logger,
    set_correlation_context,
    setup_logging,
)
from packages.redis_client.client import close_redis
from packages.telemetry.metrics import metrics_registry
from packages.telemetry.provider import setup_telemetry, start_trace_span

settings = get_settings()

# Initialize structured logging
setup_logging(
    service_name=settings.SERVICE_NAME,
    log_level=settings.LOG_LEVEL,
    environment=settings.ENVIRONMENT,
)

# Initialize OpenTelemetry provider
setup_telemetry(
    service_name=settings.SERVICE_NAME,
    environment=settings.ENVIRONMENT,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and graceful shutdown lifecycle."""
    logger.info(
        "RETRACE API server starting up",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        version="1.0.0",
    )
    yield
    logger.info("RETRACE API server shutting down gracefully")
    await close_database(settings)
    await close_redis(settings)


# Build FastAPI app
app = FastAPI(
    title="RETRACE API",
    description="Autonomous Software Regression Investigation Platform API",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" or settings.DEBUG else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" or settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" or settings.DEBUG else None,
    lifespan=lifespan,
)

# Trusted Host Middleware
if settings.ALLOWED_HOSTS and "*" not in settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Trace-ID", "X-Response-Time"],
)


@app.middleware("http")
async def operational_telemetry_and_correlation_middleware(
    request: Request, call_next: callable
) -> Response:
    """Inject correlation context, capture OpenTelemetry spans, and record Prometheus metrics."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    trace_id = request.headers.get("X-Trace-ID") or uuid.uuid4().hex
    org_id = request.headers.get("X-Organization-ID")
    user_id = request.headers.get("X-User-ID")

    set_correlation_context(
        request_id=request_id,
        trace_id=trace_id,
        organization_id=org_id,
        user_id=user_id,
    )

    start_time = time.perf_counter()
    route_path = request.url.path

    with start_trace_span(
        name="http.request",
        trace_id=trace_id,
        attributes={
            "http.method": request.method,
            "http.route": route_path,
            "http.client_ip": request.client.host if request.client else None,
        },
    ) as span:
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            span.record_exception(exc)
            metrics_registry.http_errors_total.inc(
                method=request.method,
                route=route_path,
                error_type=type(exc).__name__,
            )
            clear_correlation_context()
            raise

        duration_s = time.perf_counter() - start_time
        duration_ms = round(duration_s * 1000, 2)

        span.set_attribute("http.status_code", response.status_code)

        # Standard correlation headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Response-Time"] = f"{duration_ms}ms"

        # Security Hardening Headers
        if settings.ENABLE_SECURITY_HEADERS:
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
            if settings.ENVIRONMENT == "production":
                response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Prometheus Metrics recording
        status_bucket = f"{response.status_code // 100}xx"
        metrics_registry.http_requests_total.inc(
            method=request.method,
            route=route_path,
            status=status_bucket,
        )
        metrics_registry.http_request_duration_seconds.observe(
            duration_s,
            method=request.method,
            route=route_path,
        )
        if response.status_code >= 400:
            metrics_registry.http_errors_total.inc(
                method=request.method,
                route=route_path,
                error_type=f"HTTP_{response.status_code}",
            )

        # Structured audit log
        logger.info(
            "HTTP Request Handled",
            event_type=LogEvents.API_REQUEST,
            method=request.method,
            path=route_path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
            trace_id=trace_id,
            client_ip=request.client.host if request.client else None,
        )

        clear_correlation_context()
        return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global standardized exception handler ensuring zero leak of internal traces in production."""
    request_id = request.headers.get("X-Request-ID", "unknown")
    logger.exception(
        "Unhandled exception in API request",
        event_type=LogEvents.API_ERROR,
        path=request.url.path,
        method=request.method,
        request_id=request_id,
        error=str(exc),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred processing your request.",
            "request_id": request_id,
            "detail": str(exc) if settings.DEBUG else None,
        },
    )


# Register route trees
app.include_router(health_router)
app.include_router(v1_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
