"""Unit tests verifying deterministic execution and output reproducibility."""

from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
    RegressionClassificationResult,
)
from apps.worker.rootcause.engine import RootCauseEngine
from apps.worker.rootcause.models import RepositoryContext


def test_repeated_root_cause_analysis_determinism(tmp_path):
    """Verify repeated execution on identical inputs yields byte-equivalent results."""
    dir_a = tmp_path / "v1"
    dir_b = tmp_path / "v2"
    dir_a.mkdir()
    dir_b.mkdir()

    (dir_a / "app.py").write_text("def calc():\n    return 10\n", encoding="utf-8")
    (dir_b / "app.py").write_text("def calc():\n    return 20\n", encoding="utf-8")

    run_a_id = uuid4()
    run_b_id = uuid4()

    classification = RegressionClassification(
        classification_id="class-det-01",
        difference_id="diff-det-01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.CALCULATION,
        rule_id="RULE-CALC",
        reason="Calculation mismatch",
        evidence=ClassificationEvidence(
            difference_id="diff-det-01",
            canonical_subject="calc",
            details={"subject": "calc"},
        ),
    )

    class_res = RegressionClassificationResult(
        run_a_id=run_a_id,
        run_b_id=run_b_id,
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        classifications=[classification],
    )

    repo_ctx = RepositoryContext(
        version_a_path=str(dir_a),
        version_b_path=str(dir_b),
    )

    engine = RootCauseEngine()
    res1 = engine.analyze(class_res, repository_context=repo_ctx)
    res2 = engine.analyze(class_res, repository_context=repo_ctx)

    assert res1.summary == res2.summary
    assert len(res1.results) == len(res2.results)
    assert res1.results[0].root_cause_id == res2.results[0].root_cause_id
    assert res1.results[0].status == res2.results[0].status
    assert res1.results[0].primary_attribution.attribution_id == res2.results[0].primary_attribution.attribution_id
