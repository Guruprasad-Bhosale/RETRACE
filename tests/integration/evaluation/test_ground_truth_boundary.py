"""Integration test asserting that no production packages reference ground-truth defect identifiers."""

import re
from pathlib import Path


def test_production_code_contains_no_defect_identifiers():
    """Verify that production source code contains no hardcoded DEF-00x defect tokens."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent

    production_paths = [
        repo_root / "apps" / "api",
        repo_root / "packages",
    ]

    worker_dir = repo_root / "apps" / "worker"
    for item in worker_dir.iterdir():
        if item.is_dir() and item.name != "evaluation" and item.name != "__pycache__":
            production_paths.append(item)
        elif item.is_file() and item.suffix == ".py":
            production_paths.append(item)

    defect_pattern = re.compile(r"\bDEF-00[1-6]\b")
    violations: list[str] = []

    for target in production_paths:
        if target.is_file() and target.suffix == ".py":
            py_files = [target]
        elif target.is_dir():
            py_files = list(target.rglob("*.py"))
        else:
            continue

        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            matches = defect_pattern.findall(content)
            if matches:
                violations.append(f"{py_file}: contains benchmark tokens {set(matches)}")

    assert not violations, "Hardcoded benchmark tokens leaked into production runtime code:\n" + "\n".join(violations)
