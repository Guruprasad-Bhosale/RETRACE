"""Automated test asserting zero benchmark ground-truth imports or defect-specific logic in exploration."""

import ast
from pathlib import Path


def test_no_ground_truth_imports_or_defect_references():
    """Verify apps/worker/exploration contains NO imports of ground truth or references to DEF-001..DEF-006."""
    exploration_dir = Path(__file__).parent.parent.parent.parent / "apps" / "worker" / "exploration"
    py_files = list(exploration_dir.glob("*.py"))

    assert len(py_files) > 0, "Exploration directory should contain python modules"

    forbidden_terms = [
        "ground_truth",
        "ground_truth.json",
        "DEF-001",
        "DEF-002",
        "DEF-003",
        "DEF-004",
        "DEF-005",
        "DEF-006",
        "BenchmarkValidator",
    ]

    for py_file in py_files:
        code = py_file.read_text(encoding="utf-8")

        # 1. Textual search for forbidden defect codes
        for term in forbidden_terms:
            assert term not in code, f"Forbidden term '{term}' found in {py_file.name}"

        # 2. AST parsing to verify imports
        tree = ast.parse(code, filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "ground_truth" not in alias.name, f"Import of ground_truth found in {py_file.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert "ground_truth" not in node.module, f"ImportFrom ground_truth in {py_file.name}"
                    assert "benchmark" not in node.module or "lab.benchmark" not in node.module
