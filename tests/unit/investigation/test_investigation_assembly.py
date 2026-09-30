"""Unit tests for investigation package assembler and API endpoints."""

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from apps.api.main import app
from apps.api.routers.v1.investigations import clear_investigations, register_investigation
from apps.worker.investigation.assembler import InvestigationAssembler
from apps.worker.investigation.models import InvestigationStatus
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reproduction.models import (
    ActionType,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStep,
    ReproductionStrategy,
)
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitAttributionType,
    CommitMetadata,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
)
from packages.domain.models import ArtifactKind
from packages.storage.local import LocalDiskArtifactStorage


@pytest.fixture(autouse=True)
def cleanup():
    clear_investigations()
    yield
    clear_investigations()


@pytest.mark.asyncio
async def test_assemble_investigation_with_storage(tmp_path):
    """Verify investigation assembly persists test and report artifacts to storage."""
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    analysis_id = uuid4()

    clf = RegressionClassification(
        classification_id="clf_inv_1",
        difference_id="diff_inv_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-BUTTON-BROKEN",
        reason="Button broken.",
        evidence=ClassificationEvidence(difference_id="diff_inv_1"),
    )
    repro = ReproductionResult(
        reproduction_id="repro_inv_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="p1", trajectory_id=uuid4(), classification_id=clf.classification_id,
            difference_id=clf.difference_id, seed_url="http://127.0.0.1:3000/", steps=[
                ReproductionStep(step_index=0, action_type=ActionType.CLICK, stable_target_identity="#btn")
            ], path_signature="click",
        ),
    )
    attr = RootCauseAttribution(
        attribution_id="attr_inv_1",
        source_location=SourceLocation(file_path="src/btn.ts", start_line=1, end_line=5),
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=CommitMetadata(commit_hash="deadbeef00", author_name="Dev", message="broke button"),
        commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
        explanation="Direct change",
    )
    rc = RootCauseResult(
        root_cause_id="rc_inv_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        category=clf.category.value,
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=RootCauseProvenance(classification_id=clf.classification_id, difference_id=clf.difference_id),
    )

    assembler = InvestigationAssembler(storage=storage)
    inv = await assembler.assemble_investigation(
        analysis_id=analysis_id,
        classification=clf,
        reproduction=repro,
        root_cause=rc,
    )

    assert inv.investigation_id is not None
    assert inv.status == InvestigationStatus.COMPLETED
    assert inv.generated_test is not None
    assert len(inv.artifacts) >= 3  # Test spec, report.md, report.json

    kinds = [a.kind for a in inv.artifacts]
    assert ArtifactKind.GENERATED_TEST in kinds

    # Verify physical file existence via storage
    for art in inv.artifacts:
        exists = await storage.exists(art.storage_uri)
        assert exists is True


@pytest.mark.asyncio
async def test_investigation_api_endpoints():
    """Verify FastAPI investigation endpoints."""
    analysis_id = uuid4()
    clf = RegressionClassification(
        classification_id="clf_api_inv_1",
        difference_id="diff_api_inv_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.NAVIGATION,
        rule_id="RULE-NAV",
        reason="Nav failure",
        evidence=ClassificationEvidence(difference_id="diff_api_inv_1"),
    )
    assembler = InvestigationAssembler()
    inv = await assembler.assemble_investigation(
        analysis_id=analysis_id,
        classification=clf,
    )
    register_investigation(inv)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List investigations
        res = await client.get("/api/v1/investigations")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["investigation_id"] == inv.investigation_id

        # 2. Get investigation by ID
        res = await client.get(f"/api/v1/investigations/{inv.investigation_id}")
        assert res.status_code == 200
        assert res.json()["investigation_id"] == inv.investigation_id

        # 3. Get synthesized test
        res = await client.get(f"/api/v1/investigations/{inv.investigation_id}/test")
        assert res.status_code == 200
        assert "@playwright/test" in res.text

        # 4. Get report markdown
        res = await client.get(f"/api/v1/investigations/{inv.investigation_id}/report?format=markdown")
        assert res.status_code == 200
        assert "# RETRACE Investigation Report:" in res.text

        # 5. Get report JSON
        res = await client.get(f"/api/v1/investigations/{inv.investigation_id}/report?format=json")
        assert res.status_code == 200
        assert res.json()["report_id"] == inv.report.report_id
