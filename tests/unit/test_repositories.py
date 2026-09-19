"""Unit tests for thin domain-specific repositories."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.repositories import (
    AnalysisSessionRepository,
    ConcurrencyError,
    FindingRepository,
    ProjectRepository,
    TrajectoryRepository,
)
from packages.domain.models import (
    Action,
    ActionType,
    AnalysisStatus,
    ApplicationStateSnapshot,
    ApplicationVersion,
    ArtifactKind,
    ArtifactReference,
    Evidence,
    EvidenceType,
    Finding,
    FindingCategory,
    FindingSeverity,
    HypothesisType,
    Observation,
    Provenance,
    Report,
    ReproductionAttempt,
    ReproductionStatus,
    RootCause,
    VerificationStatus,
)


@pytest.mark.asyncio
async def test_project_repository_crud(db_session: AsyncSession):
    repo = ProjectRepository(db_session)

    # 1. Create project
    project = await repo.create_project(name="E-Commerce Store", description="Store app for tests")
    assert project.name == "E-Commerce Store"
    assert project.id is not None

    # 2. Get project
    retrieved = await repo.get_project(project.id)
    assert retrieved is not None
    assert retrieved.id == project.id
    assert retrieved.name == "E-Commerce Store"

    # 3. Create versions
    v_a = await repo.create_version(
        project_id=project.id,
        name="Baseline (v1.0)",
        base_url="http://localhost:3001",
        git_commit_hash="commit_a_123",
    )
    v_b = await repo.create_version(
        project_id=project.id,
        name="Candidate (v1.1)",
        base_url="http://localhost:3002",
        git_commit_hash="commit_b_456",
    )
    assert v_a.name == "Baseline (v1.0)"
    assert v_b.name == "Candidate (v1.1)"

    versions = await repo.list_versions_by_project(project.id)
    assert len(versions) == 2
    assert versions[0].name == "Baseline (v1.0)"
    assert versions[1].name == "Candidate (v1.1)"


@pytest.mark.asyncio
async def test_analysis_repository_optimistic_locking(db_session: AsyncSession):
    proj_repo = ProjectRepository(db_session)
    project = await proj_repo.create_project(name="Locking Test Project")

    v_a = ApplicationVersion(name="vA", base_url="http://localhost:3001")
    v_b = ApplicationVersion(name="vB", base_url="http://localhost:3002")

    analysis_repo = AnalysisSessionRepository(db_session)
    session = await analysis_repo.create_analysis_session(
        project_id=project.id,
        version_a=v_a,
        version_b=v_b,
        config={"max_depth": 5},
    )
    assert session.version == 1
    assert session.status == AnalysisStatus.PENDING

    # 1. Successful state update: version 1 -> version 2
    updated = await analysis_repo.update_status(
        session_id=session.id,
        expected_version=1,
        new_status=AnalysisStatus.RUNNING,
    )
    assert updated.version == 2
    assert updated.status == AnalysisStatus.RUNNING
    assert updated.started_at is not None

    # 2. Failed state update with stale version 1 (optimistic lock conflict)
    with pytest.raises(ConcurrencyError):
        await analysis_repo.update_status(
            session_id=session.id,
            expected_version=1,  # Stale version! Current version is 2
            new_status=AnalysisStatus.COMPLETED,
        )

    # 3. Successful subsequent update: version 2 -> version 3
    final = await analysis_repo.update_status(
        session_id=session.id,
        expected_version=2,
        new_status=AnalysisStatus.COMPLETED,
    )
    assert final.version == 3
    assert final.status == AnalysisStatus.COMPLETED
    assert final.completed_at is not None


@pytest.mark.asyncio
async def test_trajectory_timeline_ordered_sequence(db_session: AsyncSession):
    proj_repo = ProjectRepository(db_session)
    project = await proj_repo.create_project(name="Trajectory Test Project")

    v_a = ApplicationVersion(name="vA", base_url="http://localhost:3001")
    v_b = ApplicationVersion(name="vB", base_url="http://localhost:3002")

    analysis_repo = AnalysisSessionRepository(db_session)
    session = await analysis_repo.create_analysis_session(
        project_id=project.id,
        version_a=v_a,
        version_b=v_b,
    )

    traj_repo = TrajectoryRepository(db_session)
    trajectory = await traj_repo.create_trajectory(
        session_id=session.id,
        version_id=v_a.id,
        name="Cart Checkout Flow",
    )

    # Step 0: Observation 0
    obs_0 = Observation(
        session_id=session.id,
        version_id=v_a.id,
        trajectory_id=trajectory.id,
        step_index=0,
        state=ApplicationStateSnapshot(url="http://localhost:3001/products", page_title="Products"),
        provenance=Provenance(analysis_id=session.id, version_id=v_a.id, step_index=0),
    )
    await traj_repo.record_observation(obs_0)

    # Step 1: Action 1 (Click Add to Cart)
    act_1 = Action(
        session_id=session.id,
        version_id=v_a.id,
        trajectory_id=trajectory.id,
        step_index=1,
        action_type=ActionType.CLICK,
        selector=".add-to-cart-btn",
        prior_observation_id=obs_0.id,
    )
    await traj_repo.record_action(act_1)

    # Step 1: Observation 1 (Cart Updated)
    obs_1 = Observation(
        session_id=session.id,
        version_id=v_a.id,
        trajectory_id=trajectory.id,
        step_index=1,
        state=ApplicationStateSnapshot(
            url="http://localhost:3001/cart", page_title="Shopping Cart"
        ),
        provenance=Provenance(analysis_id=session.id, version_id=v_a.id, step_index=1),
        prior_observation_id=obs_0.id,
        caused_by_action_id=act_1.id,
    )
    await traj_repo.record_observation(obs_1)

    # Retrieve timeline and verify sequence order
    traj, observations, actions = await traj_repo.get_trajectory_timeline(trajectory.id)
    assert traj is not None
    assert len(observations) == 2
    assert len(actions) == 1

    assert observations[0].step_index == 0
    assert observations[0].state.page_title == "Products"
    assert observations[1].step_index == 1
    assert observations[1].state.page_title == "Shopping Cart"
    assert actions[0].action_type == ActionType.CLICK


@pytest.mark.asyncio
async def test_finding_with_multiple_reproductions_and_root_cause(db_session: AsyncSession):
    proj_repo = ProjectRepository(db_session)
    project = await proj_repo.create_project(name="Finding Test Project")

    v_a = ApplicationVersion(name="vA", base_url="http://localhost:3001")
    v_b = ApplicationVersion(name="vB", base_url="http://localhost:3002")

    analysis_repo = AnalysisSessionRepository(db_session)
    session = await analysis_repo.create_analysis_session(
        project_id=project.id,
        version_a=v_a,
        version_b=v_b,
    )

    finding_repo = FindingRepository(db_session)

    # 1. Record Evidence
    evidence = Evidence(
        session_id=session.id,
        version_id=v_b.id,
        evidence_type=EvidenceType.NETWORK_RESPONSE,
        description="POST /api/coupon returned 400 Bad Request",
        payload={"status_code": 400, "error": "Invalid field couponCode"},
        artifacts=[
            ArtifactReference(
                kind=ArtifactKind.HAR_TRACE,
                storage_uri="file:///storage/har/trace.har",
                mime_type="application/json",
            )
        ],
        provenance=Provenance(analysis_id=session.id, version_id=v_b.id),
    )
    saved_evidence = await finding_repo.record_evidence(evidence)
    assert saved_evidence.id == evidence.id

    # 2. Create Finding
    finding_id = uuid4()
    finding = Finding(
        id=finding_id,
        session_id=session.id,
        category=FindingCategory.API_CONTRACT,
        severity=FindingSeverity.HIGH,
        title="Coupon validation failure",
        description="Payload schema mismatch on POST /api/coupon",
        confidence=0.96,
        status=VerificationStatus.CANDIDATE,
        evidence_ids=[saved_evidence.id],
    )
    await finding_repo.create_finding(finding)

    # 3. Record Multiple Reproduction Attempts
    attempt_1 = ReproductionAttempt(
        finding_id=finding_id,
        session_id=session.id,
        attempt_number=1,
        framework="playwright_python",
        script_code="async def test_coupon(): pass",
        status=ReproductionStatus.SUCCEEDED,
        duration_ms=1100.0,
    )
    attempt_2 = ReproductionAttempt(
        finding_id=finding_id,
        session_id=session.id,
        attempt_number=2,
        framework="playwright_python",
        script_code="async def test_coupon(): pass",
        status=ReproductionStatus.SUCCEEDED,
        duration_ms=950.0,
    )
    await finding_repo.record_reproduction_attempt(attempt_1)
    await finding_repo.record_reproduction_attempt(attempt_2)

    # 4. Record Root Cause (Observed Fact & Inferred Hypothesis)
    fact = RootCause(
        finding_id=finding_id,
        session_id=session.id,
        hypothesis_type=HypothesisType.OBSERVED_FACT,
        commit_hash="8f31c2",
        file_path="src/checkout.ts",
        line_number=18,
        diff_chunk="- code: str\n+ couponCode: str",
        explanation="Field renamed in TypeScript API contract",
        confidence=1.0,
        supporting_evidence_ids=[saved_evidence.id],
    )
    await finding_repo.record_root_cause(fact)

    # 5. Fetch Finding and verify relationships
    retrieved_finding = await finding_repo.get_finding(finding_id)
    assert retrieved_finding is not None
    assert len(retrieved_finding.reproductions) == 2
    assert retrieved_finding.reproductions[0].attempt_number == 1
    assert retrieved_finding.reproductions[1].attempt_number == 2
    assert len(retrieved_finding.root_causes) == 1
    assert retrieved_finding.root_causes[0].hypothesis_type == HypothesisType.OBSERVED_FACT

    # 6. Update finding status to CONFIRMED
    updated_finding = await finding_repo.update_finding_status(
        finding_id=finding_id,
        new_status=VerificationStatus.CONFIRMED,
    )
    assert updated_finding is not None
    assert updated_finding.status == VerificationStatus.CONFIRMED

    # 7. Create Derived Report
    report = Report(
        session_id=session.id,
        summary="Automated investigation confirmed 1 API contract regression",
        findings=[updated_finding],
        total_workflows=12,
        verified_regressions=1,
        false_positives_filtered=0,
        duration_seconds=24.5,
    )
    await finding_repo.create_or_update_report(report)

    retrieved_report = await finding_repo.get_report_by_session(session.id)
    assert retrieved_report is not None
    assert retrieved_report.verified_regressions == 1
    assert len(retrieved_report.findings) == 1
