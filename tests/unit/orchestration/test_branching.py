"""Unit tests for conditional workflow routing logic."""

from uuid import uuid4

from apps.worker.orchestration.models import (
    InvestigationWorkflowState,
    WorkflowStatus,
)
from apps.worker.orchestration.routing import (
    route_after_classify,
    route_after_validate,
)
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)


def test_route_after_validate_success_and_failure():
    """Verify route after validate directs to prepare_versions or ends on failure."""
    valid_state: InvestigationWorkflowState = {
        "status": WorkflowStatus.RUNNING.value,
    }
    assert route_after_validate(valid_state) == "prepare_versions"

    failed_state: InvestigationWorkflowState = {
        "status": WorkflowStatus.FAILED.value,
    }
    assert route_after_validate(failed_state) == "__end__"


def test_route_after_classify_with_candidates():
    """Verify routing proceeds to reproduce when regression candidates are detected."""
    clf = RegressionClassification(
        classification_id="clf_01",
        difference_id="diff_01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-01",
        reason="Cart broken",
        evidence=ClassificationEvidence(
            difference_id="diff_01",
            canonical_subject="button#cart",
            details={},
        ),
    )
    clf_result = RegressionClassificationResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        classifications=[clf],
    )

    state: InvestigationWorkflowState = {
        "status": WorkflowStatus.RUNNING.value,
        "classification_result": clf_result,
    }

    assert route_after_classify(state) == "reproduce"


def test_route_after_classify_zero_regressions_short_circuit():
    """Verify routing short-circuits to finalize_no_regression when 0 regressions are detected."""
    clf_non = RegressionClassification(
        classification_id="clf_non_01",
        difference_id="diff_non_01",
        status=ClassificationStatus.NON_REGRESSION,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-NON",
        reason="Harmless update",
        evidence=ClassificationEvidence(
            difference_id="diff_non_01",
            canonical_subject="div#header",
            details={},
        ),
    )
    clf_result = RegressionClassificationResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        classifications=[clf_non],
    )

    state: InvestigationWorkflowState = {
        "status": WorkflowStatus.RUNNING.value,
        "classification_result": clf_result,
    }

    assert route_after_classify(state) == "finalize_no_regression"
