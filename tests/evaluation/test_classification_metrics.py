"""Unit tests for classification confusion matrix and per-category metrics."""

from uuid import uuid4

from apps.worker.evaluation.metrics import compute_category_metrics, compute_confusion_matrix
from apps.worker.evaluation.models import (
    ClassificationEvaluation,
    DetectionEvaluation,
    EndToEndStatus,
    EvaluationResult,
    ReproductionEvaluation,
    ResourceMetrics,
    RootCauseEvaluation,
    SynthesisEvaluation,
    TimingMetrics,
)


def _make_eval_result(case_id: str, exp_cat: str, obs_cat: str) -> EvaluationResult:
    return EvaluationResult(
        case_id=case_id,
        workflow_id=f"wf-{case_id}",
        analysis_id=uuid4(),
        end_to_end_status=EndToEndStatus.COMPLETE_SUCCESS if exp_cat == obs_cat else EndToEndStatus.FAILURE,
        detection=DetectionEvaluation(is_regression_expected=True, is_regression_detected=True, true_positive=True),
        classification=ClassificationEvaluation(
            expected_category=exp_cat,
            observed_category=obs_cat,
            category_matched=(exp_cat == obs_cat),
        ),
        reproduction=ReproductionEvaluation(expected_reproduced=True, actual_reproduced=True, reproduction_matched=True),
        root_cause=RootCauseEvaluation(file_matched=True),
        synthesis=SynthesisEvaluation(expected_synthesized=True, test_generated=True),
        timing=TimingMetrics(),
        resources=ResourceMetrics(),
    )


def test_confusion_matrix_generation():
    results = [
        _make_eval_result("C1", "NAVIGATION", "NAVIGATION"),
        _make_eval_result("C2", "NAVIGATION", "NAVIGATION"),
        _make_eval_result("C3", "API_CONTRACT", "API_CONTRACT"),
        _make_eval_result("C4", "CALCULATION", "STATE"),
    ]

    matrix = compute_confusion_matrix(results)
    assert matrix["NAVIGATION"]["NAVIGATION"] == 2
    assert matrix["API_CONTRACT"]["API_CONTRACT"] == 1
    assert matrix["CALCULATION"]["STATE"] == 1


def test_insufficient_sample_reporting():
    # Only 1 sample for API_CONTRACT -> below min_sample_size of 2
    results = [
        _make_eval_result("C1", "API_CONTRACT", "API_CONTRACT"),
    ]

    metrics = compute_category_metrics(results, min_sample_size=2)
    assert len(metrics) == 1
    assert metrics[0].category == "API_CONTRACT"
    assert metrics[0].sample_size == 1
    assert metrics[0].precision == "INSUFFICIENT_SAMPLE"
    assert metrics[0].recall == "INSUFFICIENT_SAMPLE"
    assert metrics[0].f1 == "INSUFFICIENT_SAMPLE"
