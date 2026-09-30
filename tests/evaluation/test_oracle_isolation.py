"""Static analysis test verifying strict ground truth oracle isolation."""

import ast
from pathlib import Path


def test_production_code_never_imports_ground_truth_oracle():
    """Verify that production runtime packages never import or reference benchmark oracles."""
    repo_root = Path(__file__).resolve().parent.parent.parent

    # Scanned production packages
    target_dirs = [
        repo_root / "apps" / "api",
        repo_root / "packages",
    ]

    # Include apps/worker excluding apps/worker/evaluation
    worker_dir = repo_root / "apps" / "worker"
    for item in worker_dir.iterdir():
        if item.is_dir() and item.name != "evaluation" and item.name != "__pycache__":
            target_dirs.append(item)
        elif item.is_file() and item.suffix == ".py":
            # Direct files in apps/worker
            target_dirs.append(item)

    forbidden_import_substrings = [
        "lab.benchmark.ground_truth",
        "benchmarks.corpus",
        "benchmarks.models",
        "apps.worker.evaluation",
    ]

    violations: list[str] = []

    for target in target_dirs:
        if target.is_file() and target.suffix == ".py":
            py_files = [target]
        elif target.is_dir():
            py_files = list(target.rglob("*.py"))
        else:
            continue

        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(content, filename=str(py_file))
            except Exception:
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for forbidden in forbidden_import_substrings:
                            if forbidden in alias.name:
                                violations.append(f"{py_file}: imports '{alias.name}'")
                elif isinstance(node, ast.ImportFrom):
                    mod = node.module or ""
                    for forbidden in forbidden_import_substrings:
                        if forbidden in mod:
                            violations.append(f"{py_file}: imports from '{mod}'")

    assert not violations, "Ground-truth oracle isolation violated in production code:\n" + "\n".join(violations)
