"""Unit tests for deterministic evaluation signatures."""

from apps.worker.evaluation.adapter import EvaluationAdapter
from benchmarks.models import BenchmarkCase, BenchmarkInput, BenchmarkOracle, ExpectedOutcome


def test_deterministic_signature_consistency():
    case = BenchmarkCase(
        case_id="DET-01",
        name="Deterministic Case",
        description="Deterministic Case",
        input_config=BenchmarkInput(version_a={"base_url": "http://a"}, version_b={"base_url": "http://b"}),
        oracle=BenchmarkOracle(
            expected_outcome=ExpectedOutcome.NON_REGRESSION,
            expected_category="NON_REGRESSION",
        ),
    )

    state1 = {"status": "COMPLETED", "history": []}
    state2 = {"status": "COMPLETED", "history": []}

    res1 = EvaluationAdapter.evaluate_case(case, state1)
    res2 = EvaluationAdapter.evaluate_case(case, state2)

    assert res1.deterministic_signature == res2.deterministic_signature
    assert len(res1.deterministic_signature) > 0
