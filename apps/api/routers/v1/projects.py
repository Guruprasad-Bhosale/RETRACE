"""Projects API Router backed by ProjectRepository."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.repositories.project_repo import ProjectRepository
from packages.db.session import get_db_session
from packages.domain.models import ApplicationVersion, Project

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProjectRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None


class CreateVersionRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    base_url: str = Field(example="http://localhost:3000")
    git_repo_url: str | None = None
    git_commit_hash: str | None = None
    branch: str | None = None
    build_id: str | None = None
    environment_variables: dict[str, str] = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)


@router.get("", response_model=list[Project])
async def list_projects(db: AsyncSession = Depends(get_db_session)) -> list[Project]:
    """List all registered projects."""
    repo = ProjectRepository(db)
    return await repo.list_projects()


@router.post("", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    req: CreateProjectRequest, db: AsyncSession = Depends(get_db_session)
) -> Project:
    """Register a new investigation project."""
    repo = ProjectRepository(db)
    return await repo.create_project(name=req.name, description=req.description)


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db_session)) -> Project:
    """Get project details by ID."""
    repo = ProjectRepository(db)
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )
    return project


@router.post(
    "/{project_id}/versions", response_model=ApplicationVersion, status_code=status.HTTP_201_CREATED
)
async def create_project_version(
    project_id: UUID, req: CreateVersionRequest, db: AsyncSession = Depends(get_db_session)
) -> ApplicationVersion:
    """Register an application version under a project."""
    repo = ProjectRepository(db)
    project = await repo.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )
    return await repo.create_version(
        project_id=project_id,
        name=req.name,
        base_url=req.base_url,
        git_repo_url=req.git_repo_url,
        git_commit_hash=req.git_commit_hash,
        branch=req.branch,
        build_id=req.build_id,
        environment_variables=req.environment_variables,
        metadata=req.metadata,
    )


@router.get("/{project_id}/versions", response_model=list[ApplicationVersion])
async def list_project_versions(
    project_id: UUID, db: AsyncSession = Depends(get_db_session)
) -> list[ApplicationVersion]:
    """List all application versions belonging to a project."""
    repo = ProjectRepository(db)
    return await repo.list_versions_by_project(project_id)
