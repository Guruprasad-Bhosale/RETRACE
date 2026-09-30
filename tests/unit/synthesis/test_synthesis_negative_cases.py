"""Unit tests for synthesis negative cases and boundary safety."""

from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reproduction.models import (
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStrategy,
)
from apps.worker.synthesis.engine import TestSynthesisEngine
from apps.worker.synthesis.models import SynthesisStatus


def test_non_regression_classification_skipped():
    """Verify non-regression changes produce INCOMPLETE synthesis status with note."""
    clf = RegressionClassification(
        classification_id="clf_nonreg_1",
        difference_id="diff_nonreg_1",
        status=ClassificationStatus.NON_REGRESSION,
        category=RegressionCategory.NON_REGRESSION,
        rule_id="RULE-BENIGN-TEXT-UPDATE",
        reason="Benign copywriting update.",
        evidence=ClassificationEvidence(difference_id="diff_nonreg_1"),
    )
    engine = TestSynthesisEngine()
    gen_test = engine.synthesize_test(clf)

    assert gen_test.status == SynthesisStatus.INCOMPLETE
    assert "non-regression" in gen_test.title.lower()
    assert "no regression test generated" in gen_test.generated_source


def test_missing_reproduction_produces_incomplete_synthesis():
    """Verify missing reproduction result yields INCOMPLETE status without crashing."""
    clf = RegressionClassification(
        classification_id="clf_norepro_1",
        difference_id="diff_norepro_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-DOM-MISMATCH",
        reason="Discrepancy detected.",
        evidence=ClassificationEvidence(difference_id="diff_norepro_1"),
    )
    engine = TestSynthesisEngine()
    gen_test = engine.synthesize_test(clf, reproduction=None)

    assert gen_test.status == SynthesisStatus.INCOMPLETE
    assert len(gen_test.steps) == 0


def test_failed_reproduction_status_marked_appropriately():
    """Verify reproduction that failed is marked as not fully synthesized."""
    clf = RegressionClassification(
        classification_id="clf_failrepro_1",
        difference_id="diff_failrepro_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-DOM-MISMATCH",
        reason="Discrepancy detected.",
        evidence=ClassificationEvidence(difference_id="diff_failrepro_1"),
    )
    repro = ReproductionResult(
        reproduction_id="repro_fail_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.NOT_REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="p_fail",
            trajectory_id=uuid4(),
            classification_id=clf.classification_id,
            difference_id=clf.difference_id,
            seed_url="http://127.0.0.1:3000/",
            steps=[],
            path_signature="empty",
        ),
    )
    engine = TestSynthesisEngine()
    gen_test = engine.synthesize_test(clf, reproduction=repro)

    assert gen_test.status == SynthesisStatus.INCOMPLETE
