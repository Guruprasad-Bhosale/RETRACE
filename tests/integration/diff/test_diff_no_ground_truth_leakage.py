"""Static architectural test ensuring apps/worker/diff contains no ground-truth references."""

import ast
import re
from pathlib import Path


def test_diff_package_has_no_ground_truth_or_defect_leakage():
    diff_dir = Path("g:/RETRACE/apps/worker/diff")
    assert diff_dir.exists(), "apps/worker/diff directory must exist"

    python_files = list(diff_dir.glob("*.py"))
    assert len(python_files) >= 10, "Diff package should have core modules"

    forbidden_patterns = [
        r"DEF-\d{3}",
        r"ground_truth",
        r"validator\.py",
        r"lab\.applications\.commerce\.ground_truth",
        r"openai",
        r"langgraph",
        r"langchain",
        r"playwright\.async_api",  # Diff engine must not directly control Playwright
    ]

    for py_file in python_files:
        code = py_file.read_text(encoding="utf-8")

        for pattern in forbidden_patterns:
            matches = re.findall(pattern, code, re.IGNORECASE)
            assert not matches, (
                f"Forbidden pattern '{pattern}' found in {py_file.name}: {matches}"
            )

        # Check AST for forbidden imports
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
