"""Unit tests for detection metrics calculation."""

from uuid import uuid4

from apps.worker.evaluation.metrics import evaluate_detection, summarize_suite_metrics
from apps.worker.evaluation.models import (
    ClassificationEvaluation,
    EndToEndStatus,
    EvaluationResult,
    ReproductionEvaluation,
    ResourceMetrics,
    RootCauseEvaluation,
    SynthesisEvaluation,
    TimingMetrics,
)
from benchmarks.models import ExpectedOutcome


def test_evaluate_detection_outcomes():
    # 1. True Positive: Expected regression detected
    d_tp = evaluate_detection(ExpectedOutcome.REGRESSION, True)
    assert d_tp.true_positive is True
    assert d_tp.false_positive is False
    assert d_tp.false_negative is False
    assert d_tp.true_negative is False

    # 2. False Positive: Non-regression falsely detected
    d_fp = evaluate_detection(ExpectedOutcome.NON_REGRESSION, True)
    assert d_fp.true_positive is False
    assert d_fp.false_positive is True

    # 3. False Negative: Expected regression missed
    d_fn = evaluate_detection(ExpectedOutcome.REGRESSION, False)
    assert d_fn.true_positive is False
    assert d_fn.false_negative is True

    # 4. True Negative: Non-regression correctly ignored
    d_tn = evaluate_detection(ExpectedOutcome.NON_REGRESSION, False)
    assert d_tn.true_negative is True
    assert d_tn.false_positive is False


def test_summarize_detection_rates():
    results = [
        EvaluationResult(
            case_id="C1",
            workflow_id="W1",
            analysis_id=uuid4(),
            end_to_end_status=EndToEndStatus.COMPLETE_SUCCESS,
            detection=evaluate_detection(ExpectedOutcome.REGRESSION, True),
            classification=ClassificationEvaluation(expected_category="API", observed_category="API", category_matched=True),
            reproduction=ReproductionEvaluation(expected_reproduced=True, actual_reproduced=True, reproduction_matched=True),
            root_cause=RootCauseEvaluation(file_matched=True),
            synthesis=SynthesisEvaluation(expected_synthesized=True, test_generated=True, structurally_validated=True),
            timing=TimingMetrics(),
            resources=ResourceMetrics(),
        ),
        EvaluationResult(
            case_id="C2",
            workflow_id="W2",
            analysis_id=uuid4(),
            end_to_end_status=EndToEndStatus.COMPLETE_SUCCESS,
            detection=evaluate_detection(ExpectedOutcome.NON_REGRESSION, False),
            classification=ClassificationEvaluation(expected_category="NON_REGRESSION", observed_category="NON_REGRESSION", category_matched=True),
            reproduction=ReproductionEvaluation(expected_reproduced=False, actual_reproduced=False, reproduction_matched=True),
            root_cause=RootCauseEvaluation(file_matched=True),
            synthesis=SynthesisEvaluation(expected_synthesized=False, test_generated=False),
            timing=TimingMetrics(),
            resources=ResourceMetrics(),
        ),
    ]

    summary = summarize_suite_metrics(results)
    assert summary.total_cases == 2
    assert summary.detection_tp == 1
    assert summary.detection_tn == 1
    assert summary.detection_fp == 0
    assert summary.detection_fn == 0
    assert summary.detection_precision == 1.0
    assert summary.detection_recall == 1.0
    assert summary.detection_specificity == 1.0
