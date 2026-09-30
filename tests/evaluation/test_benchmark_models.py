"""Unit tests for formal benchmark schema and domain models."""

from uuid import uuid4

from apps.worker.orchestration.models import VersionConfig
from benchmarks.models import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkInput,
    BenchmarkOracle,
    ExpectedOutcome,
    ExpectedSourceRegion,
)


def test_benchmark_input_isolation():
    """Verify that BenchmarkInput contains zero ground truth fields."""
    v_a = VersionConfig(version_id=uuid4(), name="v1", base_url="http://localhost:3000")
    v_b = VersionConfig(version_id=uuid4(), name="v2", base_url="http://localhost:3001")

    b_input = BenchmarkInput(
        project_id="test-proj",
        version_a=v_a,
        version_b=v_b,
    )

    dump = b_input.model_dump()
    assert "oracle" not in dump
    assert "expected_outcome" not in dump
    assert "expected_category" not in dump
    assert "ground_truth_root_cause" not in dump


def test_benchmark_oracle_model():
    """Verify BenchmarkOracle structured expectation representation."""
    oracle = BenchmarkOracle(
        expected_outcome=ExpectedOutcome.REGRESSION,
        expected_category=BenchmarkCategory.API_CONTRACT,
        expected_severity="HIGH",
        expected_reproducible=True,
        expected_source_regions=[
            ExpectedSourceRegion(file_path="app.py", symbol_name="apply_coupon")
        ],
        expected_commits=["8f31c2a"],
    )

    assert oracle.expected_outcome == ExpectedOutcome.REGRESSION
    assert oracle.expected_category == BenchmarkCategory.API_CONTRACT
    assert len(oracle.expected_source_regions) == 1
    assert oracle.expected_source_regions[0].file_path == "app.py"


def test_benchmark_case_composition():
    """Verify complete BenchmarkCase composition."""
    v_a = VersionConfig(version_id=uuid4(), name="v1", base_url="http://localhost:3000")
    v_b = VersionConfig(version_id=uuid4(), name="v2", base_url="http://localhost:3001")

    case = BenchmarkCase(
        case_id="CASE-01",
        name="Test Case",
        description="A test case",
        input_config=BenchmarkInput(
            project_id="test-proj",
            version_a=v_a,
            version_b=v_b,
        ),
        oracle=BenchmarkOracle(
            expected_outcome=ExpectedOutcome.NON_REGRESSION,
            expected_category=BenchmarkCategory.NON_REGRESSION,
            expected_severity="INFO",
            expected_reproducible=False,
        ),
        tags=["unit", "test"],
    )

    assert case.case_id == "CASE-01"
    assert case.oracle.expected_outcome == ExpectedOutcome.NON_REGRESSION
    assert len(case.tags) == 2
