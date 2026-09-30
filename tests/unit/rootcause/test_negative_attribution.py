"""Negative unit tests proving Phase 9 does NOT falsely attribute non-regressions or unrelated changes."""

from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)
from apps.worker.rootcause.engine import RootCauseEngine
from apps.worker.rootcause.models import RepositoryContext, RootCauseStatus


def test_negative_attribution_non_regression_changes(tmp_path):
    """Verify that NON_REGRESSION classifications produce INCONCLUSIVE root causes without false attributions."""
    dir_a = tmp_path / "v1"
    dir_b = tmp_path / "v2"
    dir_a.mkdir()
    dir_b.mkdir()

    # Branding/cosmetic header change
    (dir_a / "index.html").write_text("<h1>Store</h1>", encoding="utf-8")
    (dir_b / "index.html").write_text("<h1>Store 🛍️</h1>", encoding="utf-8")

    classification = RegressionClassification(
        classification_id="class-nonreg-01",
        difference_id="diff-nonreg-01",
        status=ClassificationStatus.NON_REGRESSION,
        category=RegressionCategory.NON_REGRESSION,
        rule_id="RULE-NON-REG-AESTHETIC",
        reason="Cosmetic header brand styling change",
        evidence=ClassificationEvidence(
            difference_id="diff-nonreg-01",
            canonical_subject="header",
        ),
    )

    class_res = RegressionClassificationResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        classifications=[classification],
    )

    repo_ctx = RepositoryContext(
        version_a_path=str(dir_a),
        version_b_path=str(dir_b),
    )

    engine = RootCauseEngine()
    suite = engine.analyze(class_res, repository_context=repo_ctx)

    assert len(suite.results) == 1
    res = suite.results[0]
    assert res.status == RootCauseStatus.INCONCLUSIVE
    assert res.primary_attribution is None
    assert len(res.attributions) == 0


def test_negative_attribution_no_matching_diff(tmp_path):
    """Verify that regression with no relevant source diff returns INCONCLUSIVE without inventing root cause."""
    dir_a = tmp_path / "v1"
    dir_b = tmp_path / "v2"
    dir_a.mkdir()
    dir_b.mkdir()

    # Diff in completely unrelated file
    (dir_a / "readme.md").write_text("v1", encoding="utf-8")
    (dir_b / "readme.md").write_text("v2", encoding="utf-8")

    classification = RegressionClassification(
        classification_id="class-no-match",
        difference_id="diff-no-match",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.API_CONTRACT,
        rule_id="RULE-API-400",
        reason="Payment gateway timeout",
        evidence=ClassificationEvidence(
            difference_id="diff-no-match",
            canonical_subject="/api/payment/charge",
            details={"endpoint": "/api/payment/charge"},
        ),
    )

    class_res = RegressionClassificationResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        classifications=[classification],
    )

    repo_ctx = RepositoryContext(
        version_a_path=str(dir_a),
        version_b_path=str(dir_b),
    )

    engine = RootCauseEngine()
    suite = engine.analyze(class_res, repository_context=repo_ctx)

    assert len(suite.results) == 1
    res = suite.results[0]
    # Since only unrelated readme.md changed, it should be CANDIDATE_ONLY or INCONCLUSIVE, not LOCATED
    assert res.status in (RootCauseStatus.CANDIDATE_ONLY, RootCauseStatus.INCONCLUSIVE)
    if res.primary_attribution:
        assert res.primary_attribution.relationship_type.value == "RELATED_CHANGE"
