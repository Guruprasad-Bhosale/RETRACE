"""Health, Readiness, Liveness, and Metrics Endpoints for RETRACE API."""

from typing import Any

from fastapi import APIRouter, Response, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from packages.config.settings import get_settings
from packages.db.session import check_database_health
from packages.redis_client.client import check_redis_health
from packages.storage.factory import check_storage_health
from packages.telemetry.metrics import metrics_registry

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str = "retrace-api"
    version: str = "1.0.0"


class ReadinessResponse(BaseModel):
    status: str
    database: dict[str, Any]
    redis: dict[str, Any]
    storage: dict[str, Any]


@router.get("/health", response_model=HealthResponse, summary="Service Health Overview")
@router.get("/liveness", response_model=HealthResponse, summary="Liveness Probe")
async def liveness_probe() -> HealthResponse:
    """Liveness probe indicating that the FastAPI process is running and responding.

    CRITICAL: Does NOT depend on external databases or networks so a transient DB hiccup
    does not cause ECS/K8s to endlessly reboot a healthy process.
    """
    return HealthResponse(status="healthy", service="retrace-api", version="1.0.0")


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness Probe")
@router.get("/readiness", response_model=ReadinessResponse, summary="Readiness Probe (Alias)")
async def readiness_probe(response: Response) -> ReadinessResponse:
    """Readiness probe checking connectivity to PostgreSQL database, Redis, and Artifact Storage."""
    settings = get_settings()
    db_health = await check_database_health(settings)
    redis_health = await check_redis_health(settings)
    storage_health = await check_storage_health(settings)

    is_ready = (
        bool(db_health.get("healthy"))
        and bool(redis_health.get("healthy"))
        and bool(storage_health.get("healthy"))
    )
    if not is_ready:
        # Return 503 Service Unavailable if any critical dependency is down
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "degraded",
        database=db_health,
        redis=redis_health,
        storage=storage_health,
    )


@router.get("/metrics", response_class=PlainTextResponse, summary="Prometheus Metrics")
async def prometheus_metrics() -> PlainTextResponse:
    """Expose Prometheus formatted metrics."""
    exposition = metrics_registry.generate_exposition()
    return PlainTextResponse(content=exposition, media_type="text/plain; version=0.0.4")
