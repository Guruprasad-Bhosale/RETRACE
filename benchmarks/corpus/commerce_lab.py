"""Commerce Lab Benchmark Corpus Loader.

Loads formal benchmark cases from the canonical Commerce Lab dataset,
constructing strongly typed BenchmarkCase instances with strict separation
between BenchmarkInput and BenchmarkOracle.
"""

import json
from pathlib import Path
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


def _map_category(cat: str) -> BenchmarkCategory:
    mapping = {
        "api_contract": BenchmarkCategory.API_CONTRACT,
        "navigation": BenchmarkCategory.NAVIGATION,
        "state_persistence": BenchmarkCategory.STATE,
        "state": BenchmarkCategory.STATE,
        "calculation": BenchmarkCategory.CALCULATION,
        "accessibility": BenchmarkCategory.ACCESSIBILITY,
        "performance": BenchmarkCategory.PERFORMANCE,
        "functional": BenchmarkCategory.FUNCTIONAL,
        "runtime_error": BenchmarkCategory.RUNTIME_ERROR,
        "non_regression": BenchmarkCategory.NON_REGRESSION,
        "visual_styling": BenchmarkCategory.NON_REGRESSION,
        "copywriting": BenchmarkCategory.NON_REGRESSION,
        "optional_feature": BenchmarkCategory.NON_REGRESSION,
    }
    return mapping.get(cat.lower(), BenchmarkCategory.UNKNOWN)


def load_commerce_lab_suite(
    ground_truth_path: Path | str | None = None,
    base_url_a: str = "http://localhost:3001",
    base_url_b: str = "http://localhost:3002",
) -> BenchmarkSuite:
    """Load the complete Commerce Lab benchmark suite."""
    if ground_truth_path is None:
        gt_path = Path(__file__).resolve().parent.parent.parent / "lab" / "benchmark" / "ground_truth.json"
    else:
        gt_path = Path(ground_truth_path)

    if not gt_path.exists():
        raise FileNotFoundError(f"Ground truth file not found at: {gt_path}")

    with gt_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    version_a_cfg = VersionConfig(
        version_id=uuid4(),
        name="Commerce Lab v1",
        base_url=base_url_a,
        repository_path="lab/applications/commerce/v1",
    )
    version_b_cfg = VersionConfig(
        version_id=uuid4(),
        name="Commerce Lab v2",
        base_url=base_url_b,
        repository_path="lab/applications/commerce/v2",
    )

    cases: list[BenchmarkCase] = []

    # 1. Load Defects
    for defect in data.get("defects", []):
        case_id = defect["defect_id"]
        source_regions = [
            ExpectedSourceRegion(
                file_path=file_path,
            )
            for file_path in defect.get("affected_files", [])
        ]
        commits = [defect["introducing_commit"]] if defect.get("introducing_commit") else []

        oracle = BenchmarkOracle(
            expected_outcome=ExpectedOutcome.REGRESSION,
            expected_category=_map_category(defect.get("category", "functional")),
            expected_severity=defect.get("severity", "medium").upper(),
            expected_behavior_a=defect.get("expected_behavior_vA", ""),
            expected_behavior_b=defect.get("observed_behavior_vB", ""),
            expected_reproducible=True,
            expected_source_regions=source_regions,
            expected_commits=commits,
            expected_test_synthesized=True,
            ground_truth_root_cause=defect.get("ground_truth_root_cause", ""),
            canonical_reproduction_steps=defect.get("canonical_reproduction_steps", []),
            oracle_metadata={"affected_flow": defect.get("affected_flow", "")},
        )

        input_config = BenchmarkInput(
            project_id="commerce-lab",
            version_a=version_a_cfg,
            version_b=version_b_cfg,
            budget=ResourceBudget(
                max_workflow_duration_s=300,
                max_exploration_steps=20,
                max_reproduction_attempts=3,
            ),
            metadata={"case_id": case_id},
        )

        case = BenchmarkCase(
            case_id=case_id,
            name=defect.get("title", case_id),
            description=defect.get("title", ""),
            input_config=input_config,
            oracle=oracle,
            tags=["commerce-lab", "regression", defect.get("category", "")],
        )
        cases.append(case)

    # 2. Load Intentional Non-Regressions
    for non_reg in data.get("non_regressions", []):
        case_id = non_reg["non_reg_id"]
        oracle = BenchmarkOracle(
            expected_outcome=ExpectedOutcome.NON_REGRESSION,
            expected_category=BenchmarkCategory.NON_REGRESSION,
            expected_severity="INFO",
            expected_reproducible=False,
            expected_test_synthesized=False,
            ground_truth_root_cause=non_reg.get("reasoning", ""),
            oracle_metadata={"type": non_reg.get("type", "")},
        )

        input_config = BenchmarkInput(
            project_id="commerce-lab",
            version_a=version_a_cfg,
            version_b=version_b_cfg,
            budget=ResourceBudget(
                max_workflow_duration_s=300,
                max_exploration_steps=15,
                max_reproduction_attempts=1,
            ),
            metadata={"case_id": case_id},
        )

        case = BenchmarkCase(
            case_id=case_id,
            name=f"Non-Regression: {non_reg.get('type', case_id)}",
            description=non_reg.get("description", ""),
            input_config=input_config,
            oracle=oracle,
            tags=["commerce-lab", "non-regression", non_reg.get("type", "")],
        )
        cases.append(case)

    return BenchmarkSuite(
        suite_id="commerce-lab-suite",
        name="RETRACE Commerce Lab Benchmark Suite",
        description="Authoritative suite evaluating 6 known defects and 3 intentional non-regressions.",
        cases=cases,
    )
