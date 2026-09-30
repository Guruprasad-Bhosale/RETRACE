"""Unit tests for test synthesis determinism."""

from uuid import uuid4

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
from apps.worker.synthesis.engine import TestSynthesisEngine


def test_synthesis_repeated_execution_is_deterministic():
    """Verify multiple executions on identical inputs yield identical test IDs and sources."""
    clf = RegressionClassification(
        classification_id="clf_det_10",
        difference_id="diff_det_10",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.UI_BEHAVIOR,
        rule_id="RULE-UI-MODAL-DISMISSED",
        reason="Modal failed to render.",
        evidence=ClassificationEvidence(
            difference_id="diff_det_10",
            details={"selector": "#modal-dialog", "text_a": "Welcome", "text_b": ""},
        ),
    )
    repro = ReproductionResult(
        reproduction_id="repro_det_10",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="path_det_10",
            trajectory_id=uuid4(),
            classification_id=clf.classification_id,
            difference_id=clf.difference_id,
            seed_url="http://127.0.0.1:3000/",
            steps=[
                ReproductionStep(
                    step_index=0,
                    action_type=ActionType.CLICK,
                    stable_target_identity="#open-modal-btn",
                    target_role="button",
                    accessible_name="Open Modal",
                )
            ],
            path_signature="click_modal",
        ),
    )

    engine1 = TestSynthesisEngine()
    engine2 = TestSynthesisEngine()

    test1 = engine1.synthesize_test(clf, reproduction=repro)
    test2 = engine2.synthesize_test(clf, reproduction=repro)

    assert test1.test_id == test2.test_id
    assert test1.generated_source == test2.generated_source
    assert len(test1.steps) == len(test2.steps)
    assert len(test1.assertions) == len(test2.assertions)
