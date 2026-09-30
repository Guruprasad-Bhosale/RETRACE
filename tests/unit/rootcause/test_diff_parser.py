"""Unit tests for unified diff parsing and directory tree comparison."""

from apps.worker.rootcause.git.diff import DiffParser
from apps.worker.rootcause.models import FileChangeType, LanguageType, LineChangeType

SAMPLE_DIFF = """diff --git a/app.py b/app.py
index e69de29..b853a0a 100644
--- a/app.py
+++ b/app.py
@@ -10,6 +10,8 @@ def calculate_tax(subtotal: float) -> float:
     base_tax = subtotal * 0.10
+    # Extra surcharge
+    surcharge = 2.00
     return base_tax
@@ -25,4 +27,4 @@ def get_version():
-    return "1.0.0"
+    return "2.0.0"
"""


def test_diff_parser_unified_diff():
    """Verify parsing unified diff into normalized FileDiff and DiffHunk models."""
    diffs = DiffParser.parse_unified_diff(SAMPLE_DIFF)
    assert len(diffs) == 1

    fd = diffs[0]
    assert fd.change_type == FileChangeType.FILE_MODIFIED
    assert fd.old_path == "app.py"
    assert fd.new_path == "app.py"
    assert fd.language == LanguageType.PYTHON
    assert len(fd.hunks) == 2

    hunk1 = fd.hunks[0]
    assert hunk1.old_start == 10
    assert hunk1.old_lines == 6
    assert hunk1.new_start == 10
    assert hunk1.new_lines == 8
    assert len(hunk1.added_lines) == 2
    assert hunk1.added_lines == [11, 12]

    # Verify line changes
    added_lines = [dline for dline in hunk1.lines if dline.change_type == LineChangeType.LINE_ADDED]
    assert len(added_lines) == 2
    assert added_lines[0].content == "    # Extra surcharge"
    assert added_lines[0].new_line_number == 11

    hunk2 = fd.hunks[1]
    assert hunk2.old_start == 25
    assert hunk2.new_start == 27
    assert hunk2.deleted_lines == [25]
    assert hunk2.added_lines == [27]


def test_diff_parser_directory_comparison(tmp_path):
    """Verify comparing two directory structures."""
    dir_a = tmp_path / "v1"
    dir_b = tmp_path / "v2"
    dir_a.mkdir()
    dir_b.mkdir()

    # Identical file
    (dir_a / "same.txt").write_text("hello\nworld\n", encoding="utf-8")
    (dir_b / "same.txt").write_text("hello\nworld\n", encoding="utf-8")

    # Modified file
    (dir_a / "calc.py").write_text("def calc():\n    return 10\n", encoding="utf-8")
    (dir_b / "calc.py").write_text("def calc():\n    return 20\n", encoding="utf-8")

    # Added file
    (dir_b / "new.js").write_text("console.log('new');\n", encoding="utf-8")

    # Deleted file
    (dir_a / "old.html").write_text("<p>old</p>\n", encoding="utf-8")

    diffs = DiffParser.compare_directories(dir_a, dir_b)
    assert len(diffs) == 3

    paths = {d.primary_path(): d.change_type for d in diffs}
    assert paths["calc.py"] == FileChangeType.FILE_MODIFIED
    assert paths["new.js"] == FileChangeType.FILE_ADDED
    assert paths["old.html"] == FileChangeType.FILE_DELETED
