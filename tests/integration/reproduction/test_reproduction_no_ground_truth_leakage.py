"""Integration test verifying zero ground-truth leakage in Phase 8 reproduction module."""

from pathlib import Path


def test_reproduction_engine_has_no_ground_truth_leakage():
    """Verify that apps/worker/reproduction/ contains no ground truth references or defect IDs."""
    reproduction_dir = Path("apps/worker/reproduction")
    assert reproduction_dir.exists(), "Reproduction package directory must exist"

    forbidden_tokens = [
        "DEF-001",
        "DEF-002",
        "DEF-003",
        "DEF-004",
        "DEF-005",
        "DEF-006",
        "DEF-007",
        "DEF-008",
        "DEF-009",
        "DEF-010",
        "ground_truth.json",
        "lab.ground_truth",
        "benchmark_oracle",
    ]

    violations = []
    for file_path in reproduction_dir.rglob("*.py"):
        content = file_path.read_text(encoding="utf-8")
        for token in forbidden_tokens:
            if token in content:
                violations.append(f"File {file_path} contains forbidden token '{token}'")

    assert not violations, "Ground-truth leakage detected in Phase 8:\n" + "\n".join(violations)
