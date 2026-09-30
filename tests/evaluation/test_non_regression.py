"""Unit tests for intentional non-regression evaluation."""

from apps.worker.evaluation.adapter import EvaluationAdapter
from apps.worker.evaluation.models import EndToEndStatus
from benchmarks.models import BenchmarkCase, BenchmarkInput, BenchmarkOracle, ExpectedOutcome


def test_non_regression_evaluation_true_negative():
    case = BenchmarkCase(
        case_id="NONREG-01",
        name="Header Visual Refresh",
        description="Gradient change",
        input_config=BenchmarkInput(version_a={"base_url": "http://a"}, version_b={"base_url": "http://b"}),
        oracle=BenchmarkOracle(
            expected_outcome=ExpectedOutcome.NON_REGRESSION,
            expected_category="NON_REGRESSION",
            expected_severity="INFO",
            expected_reproducible=False,
            expected_test_synthesized=False,
        ),
    )

    # Simulated investigation output with zero regression candidate
    workflow_state = {
        "status": "COMPLETED",
        "current_phase": "finalize_no_regression",
        "classification_result": None,
        "investigation_suite": None,
        "history": [],
    }

    eval_res = EvaluationAdapter.evaluate_case(case, workflow_state)
    assert eval_res.end_to_end_status == EndToEndStatus.COMPLETE_SUCCESS
    assert eval_res.detection.true_negative is True
    assert eval_res.detection.false_positive is False
    assert eval_res.classification.category_matched is True
    assert eval_res.reproduction.reproduction_matched is True
    assert len(eval_res.failure_taxonomy) == 0
