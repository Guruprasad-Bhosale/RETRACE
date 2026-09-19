"""System status and platform diagnostic endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from packages.config.settings import get_settings
from packages.db.session import check_database_health
from packages.redis_client.client import check_redis_health

router = APIRouter(prefix="/system", tags=["System"])


class SystemStatusResponse(BaseModel):
    environment: str
    service_name: str
    api_status: str
    database_status: str
    redis_status: str
    storage_backend: str


@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status() -> SystemStatusResponse:
    """Return unified platform subsystem status for frontend dashboard."""
    settings = get_settings()
    db_health = await check_database_health(settings)
    redis_health = await check_redis_health(settings)

    return SystemStatusResponse(
        environment=settings.ENVIRONMENT,
        service_name=settings.SERVICE_NAME,
        api_status="online",
        database_status=str(db_health.get("status", "unknown")),
        redis_status=str(redis_health.get("status", "unknown")),
        storage_backend=settings.STORAGE_BACKEND,
    )
