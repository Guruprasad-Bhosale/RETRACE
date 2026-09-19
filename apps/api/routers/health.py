"""Health and Readiness Probes."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from packages.db.session import check_database_health
from packages.redis_client.client import check_redis_health

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    service: str = "retrace-api"


class ReadinessResponse(BaseModel):
    status: str
    database: dict[str, str | bool]
    redis: dict[str, str | bool]


@router.get("/health", response_model=HealthResponse, summary="Liveness Probe")
async def liveness_probe() -> HealthResponse:
    """Liveness probe indicating that the FastAPI process is running and responding."""
    return HealthResponse(status="healthy", service="retrace-api")


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness Probe")
async def readiness_probe(response: Response) -> ReadinessResponse:
    """Readiness probe checking connectivity to PostgreSQL database and Redis."""
    db_health = await check_database_health()
    redis_health = await check_redis_health()

    is_ready = bool(db_health.get("healthy")) and bool(redis_health.get("healthy"))
    if not is_ready:
        # Return 503 Service Unavailable if any critical dependency is down
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(
        status="ready" if is_ready else "degraded",
        database=db_health,
        redis=redis_health,
    )
