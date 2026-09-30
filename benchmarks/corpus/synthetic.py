"""Synthetic Benchmark Corpus Loader.

Provides synthetic benchmark cases for fine-grained unit testing of
reproduction NO_MATCH, inconclusive root-cause, non-regression UI updates,
and exact commit attribution.
"""

from uuid import uuid4

from apps.worker.orchestration.models import ResourceBudget, VersionConfig
from benchmarks.models import (
    BenchmarkCase,
    BenchmarkCategory,
    BenchmarkInput,
    BenchmarkOracle,
    BenchmarkSuite,
    ExpectedOutcome,
    ExpectedSourceRegion,
)


def load_synthetic_suite() -> BenchmarkSuite:
    """Load curated synthetic benchmark test cases."""
    v_a = VersionConfig(version_id=uuid4(), name="Synth v1", base_url="http://localhost:8001")
    v_b = VersionConfig(version_id=uuid4(), name="Synth v2", base_url="http://localhost:8002")

    cases = [
        # Case 1: Defect with exact AST localization expected
        BenchmarkCase(
            case_id="SYNTH-001",
            name="Synthetic Calculation Price Overflow",
            description="Calculation regression in checkout total summing algorithm.",
            input_config=BenchmarkInput(
                project_id="synthetic-lab",
                version_a=v_a,
                version_b=v_b,
                budget=ResourceBudget(max_exploration_steps=10),
            ),
            oracle=BenchmarkOracle(
                expected_outcome=ExpectedOutcome.REGRESSION,
                expected_category=BenchmarkCategory.CALCULATION,
                expected_severity="HIGH",
                expected_reproducible=True,
                expected_source_regions=[
                    ExpectedSourceRegion(file_path="src/pricing.py", symbol_name="calculate_total", start_line=10, end_line=25)
                ],
                expected_commits=["c0ffee1"],
                expected_test_synthesized=True,
            ),
            tags=["synthetic", "calculation"],
        ),
        # Case 2: Intentional pure CSS refactoring (Non-regression)
        BenchmarkCase(
            case_id="SYNTH-002",
            name="Synthetic Button Color Styling Update",
            description="Button background changed from blue to purple with no behavioral difference.",
            input_config=BenchmarkInput(
                project_id="synthetic-lab",
                version_a=v_a,
                version_b=v_b,
                budget=ResourceBudget(max_exploration_steps=10),
            ),
            oracle=BenchmarkOracle(
                expected_outcome=ExpectedOutcome.NON_REGRESSION,
                expected_category=BenchmarkCategory.NON_REGRESSION,
                expected_severity="INFO",
                expected_reproducible=False,
                expected_test_synthesized=False,
            ),
            tags=["synthetic", "non-regression"],
        ),
        # Case 3: Flaky / Non-reproducible transient variation (Expected Inconclusive)
        BenchmarkCase(
            case_id="SYNTH-003",
            name="Synthetic Intermittent Flaky DOM Flash",
            description="Flaky animation DOM difference that fails clean isolated replay.",
            input_config=BenchmarkInput(
                project_id="synthetic-lab",
                version_a=v_a,
                version_b=v_b,
                budget=ResourceBudget(max_exploration_steps=10),
            ),
            oracle=BenchmarkOracle(
                expected_outcome=ExpectedOutcome.INCONCLUSIVE,
                expected_category=BenchmarkCategory.FUNCTIONAL,
                expected_severity="LOW",
                expected_reproducible=False,
                expected_test_synthesized=False,
            ),
            tags=["synthetic", "inconclusive"],
        ),
    ]

    return BenchmarkSuite(
        suite_id="synthetic-suite",
        name="RETRACE Synthetic Benchmark Suite",
        description="Controlled synthetic scenarios for exact boundary validation.",
        cases=cases,
    )
