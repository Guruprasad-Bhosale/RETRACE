"""Analysis Sessions API Router backed by AnalysisSessionRepository."""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.repositories.analysis_repo import AnalysisSessionRepository, ConcurrencyError
from packages.db.repositories.project_repo import ProjectRepository
from packages.db.session import get_db_session
from packages.domain.models import (
    AnalysisSession,
    AnalysisStatus,
    ApplicationVersion,
)

router = APIRouter(prefix="/analyses", tags=["Analyses"])


class StartAnalysisRequest(BaseModel):
    project_id: UUID
    version_a_name: str = Field(default="Version A (Baseline)")
    version_a_url: str = Field(example="http://localhost:3001")
    version_b_name: str = Field(default="Version B (Candidate)")
    version_b_url: str = Field(example="http://localhost:3002")
    config: dict = Field(default_factory=dict)


class UpdateAnalysisStatusRequest(BaseModel):
    current_version: int = Field(ge=1, description="Expected version for optimistic locking")
    status: AnalysisStatus
    error_message: str | None = None


@router.get("", response_model=list[AnalysisSession])
async def list_analyses(
    project_id: UUID | None = None, db: AsyncSession = Depends(get_db_session)
) -> list[AnalysisSession]:
    """List analysis sessions, optionally filtered by project."""
    repo = AnalysisSessionRepository(db)
    if project_id:
        return await repo.list_by_project(project_id)
    return await repo.list_recent()


@router.post("", response_model=AnalysisSession, status_code=status.HTTP_201_CREATED)
async def start_analysis(
    req: StartAnalysisRequest, db: AsyncSession = Depends(get_db_session)
) -> AnalysisSession:
    """Trigger a new dual-version exploration and regression analysis session."""
    proj_repo = ProjectRepository(db)
    project = await proj_repo.get_project(req.project_id)
    if not project:
        # Create project if not exists for convenience in early prototyping
        project = await proj_repo.create_project(
            name=f"Project-{req.project_id}", description="Auto-created project"
        )

    v_a = ApplicationVersion(
        id=uuid4(),
        project_id=project.id,
        name=req.version_a_name,
        base_url=req.version_a_url,
    )
    v_b = ApplicationVersion(
        id=uuid4(),
        project_id=project.id,
        name=req.version_b_name,
        base_url=req.version_b_url,
    )

    analysis_repo = AnalysisSessionRepository(db)
    return await analysis_repo.create_analysis_session(
        project_id=project.id,
        version_a=v_a,
        version_b=v_b,
        config=req.config,
    )


@router.get("/{analysis_id}", response_model=AnalysisSession)
async def get_analysis(
    analysis_id: UUID, db: AsyncSession = Depends(get_db_session)
) -> AnalysisSession:
    """Get analysis session details by ID."""
    repo = AnalysisSessionRepository(db)
    session = await repo.get_analysis_session(analysis_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis session with ID '{analysis_id}' not found",
        )
    return session


@router.patch("/{analysis_id}/status", response_model=AnalysisSession)
async def update_analysis_status(
    analysis_id: UUID,
    req: UpdateAnalysisStatusRequest,
    db: AsyncSession = Depends(get_db_session),
) -> AnalysisSession:
    """Update analysis status with optimistic concurrency control."""
    repo = AnalysisSessionRepository(db)
    try:
        return await repo.update_status(
            session_id=analysis_id,
            expected_version=req.current_version,
            new_status=req.status,
            error_message=req.error_message,
        )
    except ConcurrencyError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
