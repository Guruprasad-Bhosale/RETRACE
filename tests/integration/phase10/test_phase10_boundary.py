"""Integration boundary tests enforcing strict Phase 10 isolation and non-leakage invariants."""

from pathlib import Path


def test_zero_ground_truth_imports_in_phase10_subsystems():
    """Verify that apps/worker/synthesis, reporting, and investigation contain 0 benchmark oracle imports."""
    forbidden_tokens = [
        "lab.ground_truth",
        "ground_truth.json",
        "DEF-001",
        "DEF-002",
        "DEF-003",
        "DEF-004",
        "DEF-005",
        "DEF-006",
        "openai",
        "langchain",
        "transformers",
        "torch",
        "chromadb",
        "pinecone",
    ]

    directories_to_check = [
        Path("apps/worker/synthesis"),
        Path("apps/worker/reporting"),
        Path("apps/worker/investigation"),
        Path("apps/api/routers/v1/investigations.py"),
    ]

    for target_path in directories_to_check:
        if target_path.is_file():
            files = [target_path]
        else:
            files = list(target_path.rglob("*.py"))

        for py_file in files:
            content = py_file.read_text(encoding="utf-8")
            for token in forbidden_tokens:
                assert token.lower() not in content.lower(), (
                    f"Forbidden token '{token}' found in {py_file}!"
                )


def test_zero_severity_ranking_in_reports():
    """Verify generated investigation reports do not contain arbitrary severity or ranking scores."""
    from apps.worker.regression.models import (
        ClassificationEvidence,
        ClassificationStatus,
        RegressionCategory,
        RegressionClassification,
    )
    from apps.worker.reporting.engine import EvidenceReportEngine

    clf = RegressionClassification(
        classification_id="clf_bound_1",
        difference_id="diff_bound_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-DOM",
        reason="Test finding",
        evidence=ClassificationEvidence(difference_id="diff_bound_1"),
    )
    engine = EvidenceReportEngine()
    report = engine.generate_report(clf)

    md = report.markdown_content.lower()
    assert "severity" not in md
    assert "critical" not in md
    assert "priority" not in md
    assert "score" not in md
