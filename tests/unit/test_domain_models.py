"""Comprehensive Unit Tests for RETRACE Core Domain Models."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.domain.models import (
    Action,
    ActionType,
    AnalysisSession,
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
    Project,
    Provenance,
    Report,
    ReproductionAttempt,
    ReproductionStatus,
    RootCause,
    VerificationStatus,
)


def test_project_model_validation():
    proj = Project(name="Checkout Service", description="E-Commerce checkout flow")
    assert proj.name == "Checkout Service"
    assert proj.id is not None
    assert proj.created_at is not None

    with pytest.raises(ValidationError):
        Project(name="")  # min_length is 1


def test_application_version_attributes():
    v = ApplicationVersion(
        name="Baseline v1.4.0",
        base_url="https://app.example.com/v1",
        git_commit_hash="8f31c2a",
        branch="main",
        build_id="build-4921",
        environment_variables={"FEATURE_COUPON": "true"},
    )
    assert v.name == "Baseline v1.4.0"
    assert v.base_url == "https://app.example.com/v1"
    assert v.git_commit_hash == "8f31c2a"
    assert v.environment_variables["FEATURE_COUPON"] == "true"


def test_first_class_artifact_reference():
    artifact = ArtifactReference(
        kind=ArtifactKind.SCREENSHOT,
        storage_uri="s3://retrace-artifacts/sessions/123/step1.png",
        mime_type="image/png",
        size_bytes=1048576,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        metadata={"width": 1920, "height": 1080},
    )
    assert artifact.kind == ArtifactKind.SCREENSHOT
    assert artifact.storage_uri.startswith("s3://")
    assert artifact.size_bytes == 1048576
    assert artifact.metadata["width"] == 1920


def test_trajectory_and_sequence_aware_observation():
    session_id = uuid4()
    version_id = uuid4()
    traj_id = uuid4()

    state = ApplicationStateSnapshot(
        url="https://app.example.com/checkout",
        page_title="Checkout - MyStore",
        http_status=200,
        viewport={"width": 1280, "height": 720},
        dom_hash="sha256-dom-12345",
        console_errors_count=0,
        network_requests_count=12,
        interactive_elements_count=8,
    )

    provenance = Provenance(
        analysis_id=session_id,
        version_id=version_id,
        trajectory_id=traj_id,
        step_index=0,
        collector_service="playwright-explorer-v1",
    )

    screenshot = ArtifactReference(
        kind=ArtifactKind.SCREENSHOT,
        storage_uri="file:///storage/screenshot_0.png",
        mime_type="image/png",
    )

    obs = Observation(
        session_id=session_id,
        version_id=version_id,
        trajectory_id=traj_id,
        step_index=0,
        state=state,
        artifacts=[screenshot],
        provenance=provenance,
    )

    assert obs.step_index == 0
    assert obs.state.url == "https://app.example.com/checkout"
    assert len(obs.artifacts) == 1
    assert obs.provenance.collector_service == "playwright-explorer-v1"


def test_action_trajectory_transition():
    session_id = uuid4()
    version_id = uuid4()
    traj_id = uuid4()
    obs_0_id = uuid4()
    obs_1_id = uuid4()

    action = Action(
        session_id=session_id,
        version_id=version_id,
        trajectory_id=traj_id,
        step_index=1,
        action_type=ActionType.CLICK,
        selector="#apply-coupon-btn",
        duration_ms=45.5,
        prior_observation_id=obs_0_id,
        resulting_observation_id=obs_1_id,
    )

    assert action.step_index == 1
    assert action.action_type == ActionType.CLICK
    assert action.prior_observation_id == obs_0_id
    assert action.resulting_observation_id == obs_1_id


def test_evidence_provenance_chain():
    session_id = uuid4()
    version_id = uuid4()

    prov = Provenance(
        analysis_id=session_id,
        version_id=version_id,
        step_index=2,
        collector_service="semantic-diff-engine",
    )

    evidence = Evidence(
        session_id=session_id,
        version_id=version_id,
        evidence_type=EvidenceType.DOM_DIFF,
        description="Discount badge missing from cart summary in Version B",
        payload={"element": ".discount-amount", "vA_text": "-$20.00", "vB_text": None},
        provenance=prov,
    )

    assert evidence.evidence_type == EvidenceType.DOM_DIFF
    assert evidence.provenance.step_index == 2
    assert evidence.payload["vA_text"] == "-$20.00"


def test_multiple_reproduction_attempts_on_finding():
    session_id = uuid4()
    finding_id = uuid4()

    attempt_1 = ReproductionAttempt(
        finding_id=finding_id,
        session_id=session_id,
        attempt_number=1,
        framework="playwright_python",
        script_code="async def test_attempt_1(): pass",
        status=ReproductionStatus.SUCCEEDED,
        duration_ms=1200.0,
    )

    attempt_2 = ReproductionAttempt(
        finding_id=finding_id,
        session_id=session_id,
        attempt_number=2,
        framework="playwright_python",
        script_code="async def test_attempt_2(): pass",
        status=ReproductionStatus.FAILED,
        duration_ms=850.0,
        execution_output="AssertionError: Coupon input was disabled",
    )

    finding = Finding(
        id=finding_id,
        session_id=session_id,
        category=FindingCategory.FUNCTIONAL,
        severity=FindingSeverity.HIGH,
        title="Coupon SAVE20 no longer applies discount",
        description="Version A applied 20% off while Version B rejects valid coupon.",
        confidence=0.95,
        status=VerificationStatus.CONFIRMED,
        reproductions=[attempt_1, attempt_2],
    )

    assert len(finding.reproductions) == 2
    assert finding.reproductions[0].attempt_number == 1
    assert finding.reproductions[0].status == ReproductionStatus.SUCCEEDED
    assert finding.reproductions[1].status == ReproductionStatus.FAILED


def test_root_cause_hypothesis_types():
    finding_id = uuid4()
    session_id = uuid4()
    ev_id = uuid4()

    fact = RootCause(
        finding_id=finding_id,
        session_id=session_id,
        hypothesis_type=HypothesisType.OBSERVED_FACT,
        commit_hash="8f31c2",
        file_path="src/api/coupon.ts",
        line_number=42,
        diff_chunk="- request.code\n+ request.couponCode",
        explanation="Commit 8f31c2 renamed the request payload key from 'code' to 'couponCode'",
        confidence=1.0,
        supporting_evidence_ids=[ev_id],
    )

    hypothesis = RootCause(
        finding_id=finding_id,
        session_id=session_id,
        hypothesis_type=HypothesisType.HYPOTHESIS,
        explanation="Frontend UI was not updated to use the new couponCode field, resulting in 400 Bad Request",
        confidence=0.94,
        affected_components=["Frontend Checkout Form", "Backend Coupon API"],
    )

    assert fact.hypothesis_type == HypothesisType.OBSERVED_FACT
    assert fact.confidence == 1.0
    assert hypothesis.hypothesis_type == HypothesisType.HYPOTHESIS
    assert len(hypothesis.affected_components) == 2


def test_analysis_session_optimistic_locking_version():
    v_a = ApplicationVersion(name="vA", base_url="http://localhost:3001")
    v_b = ApplicationVersion(name="vB", base_url="http://localhost:3002")
    session = AnalysisSession(
        project_id=uuid4(),
        version_a=v_a,
        version_b=v_b,
        status=AnalysisStatus.PENDING,
        version=1,
    )
    assert session.version == 1
    assert session.status == AnalysisStatus.PENDING


def test_report_composition_and_json_roundtrip():
    session_id = uuid4()
    finding = Finding(
        session_id=session_id,
        category=FindingCategory.FUNCTIONAL,
        severity=FindingSeverity.HIGH,
        title="Sample Regression",
        description="Detailed description",
        confidence=0.9,
    )
    report = Report(
        session_id=session_id,
        summary="Found 1 verified regression",
        findings=[finding],
        total_workflows=5,
        verified_regressions=1,
        false_positives_filtered=2,
        duration_seconds=34.2,
    )

    json_data = report.model_dump(mode="json")
    restored = Report.model_validate(json_data)
    assert restored.session_id == session_id
    assert len(restored.findings) == 1
    assert restored.verified_regressions == 1
