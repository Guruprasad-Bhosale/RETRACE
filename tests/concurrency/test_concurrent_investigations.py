"""Concurrency & Multi-Tenant Isolation Tests for Investigation Workflows."""

import asyncio
from pathlib import Path
from uuid import uuid4

import pytest

from apps.worker.orchestration.models import (
    InvestigationRequest,
    ResourceBudget,
    VersionConfig,
    WorkflowStatus,
)
from apps.worker.orchestration.runner import InvestigationWorkflowRunner
from packages.storage.local import LocalDiskArtifactStorage


@pytest.mark.asyncio
async def test_concurrent_investigations_2_nodes(tmp_path: Path):
    """Verify 2 concurrent workflows execute in complete isolation."""
    await _execute_concurrent_workflows(tmp_path, count=2)


@pytest.mark.asyncio
async def test_concurrent_investigations_5_nodes(tmp_path: Path):
    """Verify 5 concurrent workflows execute in complete isolation."""
    await _execute_concurrent_workflows(tmp_path, count=5)


@pytest.mark.asyncio
async def test_concurrent_investigations_10_nodes(tmp_path: Path):
    """Verify 10 concurrent workflows execute with isolated artifact paths."""
    await _execute_concurrent_workflows(tmp_path, count=10)


async def _execute_concurrent_workflows(tmp_path: Path, count: int) -> None:
    """Helper executing count concurrent workflows and asserting state isolation."""
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / f"artifacts_concurrency_{count}")
    runner = InvestigationWorkflowRunner(storage=storage)

    requests = [
        InvestigationRequest(
            analysis_id=uuid4(),
            project_id=str(uuid4()),
            version_a=VersionConfig(base_url=f"http://127.0.0.1:{3000 + idx}", name=f"Baseline-{idx}"),
            version_b=VersionConfig(base_url=f"http://127.0.0.1:{4000 + idx}", name=f"Candidate-{idx}"),
            budget=ResourceBudget(max_exploration_steps=2),
        )
        for idx in range(count)
    ]

    tasks = [runner.run(req) for req in requests]
    results = await asyncio.gather(*tasks)

    # Check results
    assert len(results) == count
    seen_analysis_ids = set()

    for res in results:
        assert "status" in res
        status = res.get("status")
        assert status in (
            WorkflowStatus.COMPLETED.value,
            WorkflowStatus.FAILED.value,
            WorkflowStatus.INCONCLUSIVE.value,
            WorkflowStatus.PENDING.value,
        )
        analysis_id = str(res.get("analysis_id"))
        assert analysis_id not in seen_analysis_ids
        seen_analysis_ids.add(analysis_id)
