"""Architecture and Hygiene Test: Verifies zero ground-truth leakage and zero regression classification."""

import re
from pathlib import Path


def test_no_ground_truth_imports_or_defect_references_in_alignment() -> None:
    """Ensure apps/worker/alignment has zero imports or mentions of ground truth, DEF-xxx, or bug severity."""
    alignment_dir = Path("apps/worker/alignment")
    assert alignment_dir.exists()

    forbidden_patterns = [
        r"ground_truth\.json",
        r"DEF-\d{3}",
        r"regression_score",
        r"severity_level",
        r"bug_severity",
        r"defect_detected",
    ]

    for py_file in alignment_dir.glob("**/*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            matches = re.findall(pattern, content, flags=re.IGNORECASE)
            assert not matches, f"Forbidden token '{pattern}' found in {py_file}: {matches}"
