"""Integration boundary test ensuring Phase 7 performs zero root cause inference, test generation, or severity ranking."""

import inspect
from uuid import uuid4

import apps.worker.regression.models as regression_models
from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    SemanticDifference,
    SemanticDiffResult,
    SemanticDiffSummary,
)
from apps.worker.regression.classifier import RegressionClassifier


def test_regression_models_contain_no_root_cause_or_severity_fields():
    classes_to_check = [
        regression_models.RegressionClassification,
        regression_models.RegressionClassificationResult,
        regression_models.ClassificationSummary,
        regression_models.ClassificationEvidence,
    ]

    forbidden_field_names = [
        "severity",
        "priority",
        "rank",
        "score",
        "regression_score",
        "root_cause",
        "root_causes",
        "hypothesis",
        "git_commit",
        "source_file",
        "ast_node",
        "reproduction_script",
        "playwright_code",
    ]

    for cls in classes_to_check:
        fields = cls.model_fields.keys()
        for forbidden in forbidden_field_names:
            assert forbidden not in fields, (
                f"Model {cls.__name__} has forbidden field '{forbidden}'"
            )


def test_classifier_output_has_no_root_cause_or_rankings():
    classifier = RegressionClassifier()

    diff = SemanticDifference(
        diff_id="diff_1",
        category=DifferenceCategory.STATE,
        kind=DifferenceKind.HTTP_STATUS_CHANGED,
        canonical_subject="state:/checkout",
        comparison_status=ComparisonStatus.COMPARED,
        description="200 -> 500",
        evidence=[DifferenceEvidence(canonical_subject="state:/checkout", before_value=200, after_value=500)],
    )

    diff_res = SemanticDiffResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        differences=[diff],
        summary=SemanticDiffSummary(total_differences=1),
    )

    result = classifier.classify(diff_res)
    dumped = result.model_dump(mode="json")
    raw_text = str(dumped).lower()

    assert "severity" not in raw_text
    assert "priority" not in raw_text
    assert "critical" not in raw_text
    assert "root_cause" not in raw_text
    assert "git_commit" not in raw_text
    assert "source_file" not in raw_text


def test_classifier_methods_boundary():
    classifier = RegressionClassifier()
    methods = [m for m, _ in inspect.getmembers(classifier, predicate=inspect.ismethod)]
    for method_name in methods:
        assert "reproduce" not in method_name
        assert "generate_test" not in method_name
        assert "root_cause" not in method_name
        assert "rank" not in method_name
