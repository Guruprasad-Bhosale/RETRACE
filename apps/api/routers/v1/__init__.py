"""API v1 Aggregator Router."""

from fastapi import APIRouter

from apps.api.routers.v1.analyses import router as analyses_router
from apps.api.routers.v1.projects import router as projects_router
from apps.api.routers.v1.system import router as system_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(system_router)
v1_router.include_router(projects_router)
v1_router.include_router(analyses_router)

__all__ = ["v1_router"]
