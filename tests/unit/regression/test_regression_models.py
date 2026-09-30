"""Unit tests for Regression Domain Models, Serialization, and Deterministic IDs."""

from datetime import UTC, datetime
from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    ClassificationSummary,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
    compute_deterministic_classification_id,
)


def test_compute_deterministic_classification_id():
    cid1 = compute_deterministic_classification_id("diff_123", RegressionCategory.FUNCTIONAL, "FUNC-HTTP-STATUS-ERROR")
    cid2 = compute_deterministic_classification_id("diff_123", RegressionCategory.FUNCTIONAL, "FUNC-HTTP-STATUS-ERROR")
    assert cid1 == cid2
    assert len(cid1) == 16


def test_regression_classification_serialization():
    cid = compute_deterministic_classification_id("diff_abc", RegressionCategory.NAVIGATION, "NAV-ROUTE-REMOVED")
    c = RegressionClassification(
        classification_id=cid,
        difference_id="diff_abc",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.NAVIGATION,
        rule_id="NAV-ROUTE-REMOVED",
        reason="Route was removed.",
        evidence=ClassificationEvidence(
            difference_id="diff_abc",
            canonical_subject="/cart",
            details={"route": "/cart"},
        ),
    )

    dumped = c.model_dump()
    assert dumped["classification_id"] == cid
    assert dumped["category"] == "NAVIGATION"
    assert dumped["status"] == "REGRESSION_CANDIDATE"
    assert dumped["rule_id"] == "NAV-ROUTE-REMOVED"


def test_timestamp_does_not_affect_sorting():
    c1 = RegressionClassification(
        classification_id="cid_1",
        difference_id="d1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="FUNC-1",
        reason="reason",
        evidence=ClassificationEvidence(difference_id="d1"),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    c2 = RegressionClassification(
        classification_id="cid_1",
        difference_id="d1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="FUNC-1",
        reason="reason",
        evidence=ClassificationEvidence(difference_id="d1"),
        created_at=datetime(2026, 9, 22, tzinfo=UTC),
    )
    assert c1.deterministic_sort_key() == c2.deterministic_sort_key()


def test_regression_classification_result_model():
    run_a = uuid4()
    run_b = uuid4()
    traj_a = uuid4()
    traj_b = uuid4()

    res = RegressionClassificationResult(
        run_a_id=run_a,
        run_b_id=run_b,
        trajectory_a_id=traj_a,
        trajectory_b_id=traj_b,
        classifications=[],
        summary=ClassificationSummary(),
    )
    json_data = res.model_dump(mode="json")
    assert json_data["run_a_id"] == str(run_a)
    assert json_data["summary"]["regression_candidates"] == 0
