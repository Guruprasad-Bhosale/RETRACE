"""Static architectural test ensuring apps/worker/regression contains no ground-truth references."""

import ast
import re
from pathlib import Path


def test_regression_package_has_no_ground_truth_or_defect_leakage():
    regression_dir = Path("g:/RETRACE/apps/worker/regression")
    assert regression_dir.exists(), "apps/worker/regression directory must exist"

    python_files = list(regression_dir.glob("*.py"))
    assert len(python_files) >= 10, "Regression package should have core modules"

    forbidden_patterns = [
        r"DEF-\d{3}",
        r"ground_truth",
        r"validator\.py",
        r"lab\.applications\.commerce\.ground_truth",
        r"openai",
        r"langgraph",
        r"langchain",
        r"playwright\.async_api",
    ]

    for py_file in python_files:
        code = py_file.read_text(encoding="utf-8")

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            assert not matches, (
                f"Forbidden pattern '{pattern}' found in {py_file.name}: {matches}"
            )

        tree = ast.parse(code, filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "openai" not in alias.name
                    assert "langgraph" not in alias.name
                    assert "playwright" not in alias.name
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    assert "openai" not in node.module
                    assert "langgraph" not in node.module
                    assert "playwright" not in node.module
                    assert "ground_truth" not in node.module
