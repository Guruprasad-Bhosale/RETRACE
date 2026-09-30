"""Unit tests for repeated runs stability analysis."""

from uuid import uuid4

from apps.worker.evaluation.metrics import summarize_suite_metrics
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


def test_repeated_run_determinism_calculation():
    results = [
        EvaluationResult(
            case_id="REP-01",
            workflow_id="W1",
            analysis_id=uuid4(),
            end_to_end_status=EndToEndStatus.COMPLETE_SUCCESS,
            detection=DetectionEvaluation(is_regression_expected=True, is_regression_detected=True, true_positive=True),
            classification=ClassificationEvaluation(expected_category="API", observed_category="API", category_matched=True),
            reproduction=ReproductionEvaluation(expected_reproduced=True, actual_reproduced=True, reproduction_matched=True),
            root_cause=RootCauseEvaluation(file_matched=True),
            synthesis=SynthesisEvaluation(expected_synthesized=True, test_generated=True),
            timing=TimingMetrics(),
            resources=ResourceMetrics(),
            deterministic_signature="SIG-12345",
        ),
        EvaluationResult(
            case_id="REP-01",
            workflow_id="W2",
            analysis_id=uuid4(),
            end_to_end_status=EndToEndStatus.COMPLETE_SUCCESS,
            detection=DetectionEvaluation(is_regression_expected=True, is_regression_detected=True, true_positive=True),
            classification=ClassificationEvaluation(expected_category="API", observed_category="API", category_matched=True),
            reproduction=ReproductionEvaluation(expected_reproduced=True, actual_reproduced=True, reproduction_matched=True),
            root_cause=RootCauseEvaluation(file_matched=True),
            synthesis=SynthesisEvaluation(expected_synthesized=True, test_generated=True),
            timing=TimingMetrics(),
            resources=ResourceMetrics(),
            deterministic_signature="SIG-12345",
        ),
    ]

    summary = summarize_suite_metrics(results, repeat_runs_total=2, identical_runs_count=2)
    assert summary.repeat_runs_total == 2
    assert summary.identical_runs_count == 2
    assert summary.determinism_rate == 1.0
