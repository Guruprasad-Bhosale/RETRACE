"""Resilience tests for Database operations, transactions, and concurrency safety."""

from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.models import AnalysisSessionModel
from packages.db.repositories.analysis_repo import AnalysisSessionRepository, ConcurrencyError
from packages.db.repositories.project_repo import ProjectRepository
from packages.domain.models import AnalysisStatus, ApplicationVersion
from tests.resilience.failure_injection import DatabaseUnavailableError, FaultInjector


@pytest.mark.asyncio
async def test_transaction_rollback_on_unhandled_failure(db_session: AsyncSession):
    """Verify that if an error occurs mid-transaction, all changes roll back atomically."""
    project_repo = ProjectRepository(db_session)
    project = await project_repo.create_project(name="Rollback Test Project", description="Before failure")

    # Attempt a nested transaction that fails
    try:
        async with db_session.begin_nested():
            analysis_repo = AnalysisSessionRepository(db_session)
            v_a = ApplicationVersion(id=uuid4(), project_id=project.id, name="v1.0", base_url="http://localhost:3001")
            v_b = ApplicationVersion(id=uuid4(), project_id=project.id, name="v1.1", base_url="http://localhost:3002")
            await analysis_repo.create_analysis_session(
                project_id=project.id,
                version_a=v_a,
                version_b=v_b,
            )
            # Deliberately raise exception inside nested transaction
            raise ValueError("Intentional crash during multi-table write")
    except ValueError:
        pass

    # Verify project exists, but the analysis was cleanly rolled back
    res = await db_session.execute(
        select(AnalysisSessionModel).where(AnalysisSessionModel.project_id == project.id)
    )
    analyses = res.scalars().all()
    assert len(analyses) == 0, "Failed transaction was not rolled back cleanly"


@pytest.mark.asyncio
async def test_optimistic_locking_prevents_stale_overwrites(db_session: AsyncSession):
    """Verify optimistic locking increments version and raises ConcurrencyError on stale updates."""
    project_repo = ProjectRepository(db_session)
    project = await project_repo.create_project(name="Concurrency Test", description="Testing version column")

    analysis_repo = AnalysisSessionRepository(db_session)
    v_a = ApplicationVersion(id=uuid4(), project_id=project.id, name="v1.0", base_url="http://localhost:3001")
    v_b = ApplicationVersion(id=uuid4(), project_id=project.id, name="v1.1", base_url="http://localhost:3002")
    analysis = await analysis_repo.create_analysis_session(
        project_id=project.id,
        version_a=v_a,
        version_b=v_b,
    )
    assert analysis.version == 1

    # First update: expected_version=1 -> succeeds, version becomes 2
    updated_1 = await analysis_repo.update_status(
        session_id=analysis.id,
        new_status=AnalysisStatus.RUNNING,
        expected_version=1,
    )
    assert updated_1 is not None
    assert updated_1.version == 2
    assert updated_1.status == AnalysisStatus.RUNNING

    # Stale update: trying to update with stale expected_version=1 -> raises ConcurrencyError
    with pytest.raises(ConcurrencyError, match="Optimistic lock conflict"):
        await analysis_repo.update_status(
            session_id=analysis.id,
            new_status=AnalysisStatus.COMPLETED,
            expected_version=1,  # Stale! Database is at version 2
        )

    # Valid update: expected_version=2 -> succeeds, version becomes 3
    updated_2 = await analysis_repo.update_status(
        session_id=analysis.id,
        new_status=AnalysisStatus.COMPLETED,
        expected_version=2,
    )
    assert updated_2 is not None
    assert updated_2.version == 3
    assert updated_2.status == AnalysisStatus.COMPLETED


@pytest.mark.asyncio
async def test_database_fault_injection_handled_gracefully(db_session: AsyncSession):
    """Verify system handles simulated database connectivity loss cleanly."""
    project_repo = ProjectRepository(db_session)

    async with FaultInjector.inject_database_failure(fail_on="execute"):
        with pytest.raises(DatabaseUnavailableError):
            await project_repo.get_project(uuid4())
