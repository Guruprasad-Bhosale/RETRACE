"""Unified Diff Parser and Normalizer.

Parses Git unified diffs and direct directory comparisons into structured,
reproducible FileDiff and DiffHunk domain models with exact line number alignments.
"""

import difflib
import re
from pathlib import Path

from apps.worker.rootcause.models import (
    DiffHunk,
    DiffLine,
    FileChangeType,
    FileDiff,
    LanguageType,
    LineChangeType,
)


class DiffParser:
    """Deterministic parser for unified diffs and filesystem directory comparison."""

    HUNK_HEADER_RE = re.compile(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@(.*)$")

    @classmethod
    def detect_language(cls, file_path: str) -> LanguageType:
        """Infer LanguageType from file extension."""
        lower = file_path.lower()
        if lower.endswith(".py"):
            return LanguageType.PYTHON
        if lower.endswith((".js", ".mjs", ".cjs")):
            return LanguageType.JAVASCRIPT
        if lower.endswith((".ts", ".tsx")):
            return LanguageType.TYPESCRIPT
        if lower.endswith((".html", ".htm")):
            return LanguageType.HTML
        if lower.endswith((".css", ".scss", ".sass", ".less")):
            return LanguageType.CSS
        if lower.endswith(".json"):
            return LanguageType.JSON
        return LanguageType.UNSUPPORTED_LANGUAGE

    @classmethod
    def parse_unified_diff(cls, diff_text: str) -> list[FileDiff]:
        """Parse unified diff text (e.g. from git diff) into a list of FileDiff models."""
        file_diffs: list[FileDiff] = []
        lines = diff_text.splitlines()
        i = 0
        n = len(lines)

        current_old_path: str | None = None
        current_new_path: str | None = None
        current_change_type = FileChangeType.FILE_MODIFIED
        current_hunks: list[DiffHunk] = []

        def flush_current_file():
            nonlocal current_old_path, current_new_path, current_change_type, current_hunks
            if current_old_path is not None or current_new_path is not None:
                p = current_new_path or current_old_path or ""
                lang = cls.detect_language(p)
                file_diffs.append(
                    FileDiff(
                        change_type=current_change_type,
                        old_path=current_old_path,
                        new_path=current_new_path,
                        hunks=current_hunks,
                        is_binary=False,
                        language=lang,
                    )
                )
                current_old_path = None
                current_new_path = None
                current_change_type = FileChangeType.FILE_MODIFIED
                current_hunks = []

        while i < n:
            line = lines[i]

            # Detect git diff file header
            if line.startswith("diff --git "):
                flush_current_file()
                i += 1
                continue

            if line.startswith("new file mode "):
                current_change_type = FileChangeType.FILE_ADDED
                i += 1
                continue
            if line.startswith("deleted file mode "):
                current_change_type = FileChangeType.FILE_DELETED
                i += 1
                continue
            if line.startswith("rename from "):
                current_change_type = FileChangeType.FILE_RENAMED
                current_old_path = line[12:].strip()
                i += 1
                continue
            if line.startswith("rename to "):
                current_new_path = line[10:].strip()
                i += 1
                continue

            if line.startswith("--- "):
                path_part = line[4:].strip()
                if path_part.startswith("a/"):
                    path_part = path_part[2:]
                elif path_part == "/dev/null":
                    path_part = None
                    current_change_type = FileChangeType.FILE_ADDED
                current_old_path = path_part
                i += 1
                continue

            if line.startswith("+++ "):
                path_part = line[4:].strip()
                if path_part.startswith("b/"):
                    path_part = path_part[2:]
                elif path_part == "/dev/null":
                    path_part = None
                    current_change_type = FileChangeType.FILE_DELETED
                current_new_path = path_part
                i += 1
                continue

            # Detect hunk header
            hunk_match = cls.HUNK_HEADER_RE.match(line)
            if hunk_match:
                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1
                header_extra = hunk_match.group(5).strip()

                hunk_lines: list[DiffLine] = []
                added_lines: list[int] = []
                deleted_lines: list[int] = []

                curr_old_line = old_start
                curr_new_line = new_start

                i += 1
                while i < n:
                    hline = lines[i]
                    if hline.startswith("@@") or hline.startswith("diff --git ") or hline.startswith("--- "):
                        break

                    if hline.startswith("+"):
                        added_lines.append(curr_new_line)
                        hunk_lines.append(
                            DiffLine(
                                change_type=LineChangeType.LINE_ADDED,
                                content=hline[1:],
                                old_line_number=None,
                                new_line_number=curr_new_line,
                            )
                        )
                        curr_new_line += 1
                    elif hline.startswith("-"):
                        deleted_lines.append(curr_old_line)
                        hunk_lines.append(
                            DiffLine(
                                change_type=LineChangeType.LINE_DELETED,
                                content=hline[1:],
                                old_line_number=curr_old_line,
                                new_line_number=None,
                            )
                        )
                        curr_old_line += 1
                    elif hline.startswith(" ") or hline == "":
                        content = hline[1:] if hline.startswith(" ") else hline
                        hunk_lines.append(
                            DiffLine(
                                change_type=LineChangeType.LINE_CONTEXT,
                                content=content,
                                old_line_number=curr_old_line,
                                new_line_number=curr_new_line,
                            )
                        )
                        curr_old_line += 1
                        curr_new_line += 1
                    elif hline.startswith("\\ No newline at end of file"):
                        i += 1
                        continue
                    else:
                        break
                    i += 1

                current_hunks.append(
                    DiffHunk(
                        old_start=old_start,
                        old_lines=old_count,
                        new_start=new_start,
                        new_lines=new_count,
                        header=header_extra,
                        lines=hunk_lines,
                        added_lines=added_lines,
                        deleted_lines=deleted_lines,
                    )
                )
                continue

            i += 1

        flush_current_file()
        return file_diffs

    @classmethod
    def compare_directories(cls, dir_a: Path, dir_b: Path) -> list[FileDiff]:
        """Compute unified diffs between two directory trees on disk."""
        path_a = Path(dir_a).resolve()
        path_b = Path(dir_b).resolve()

        if not path_a.is_dir() or not path_b.is_dir():
            return []

        files_a = {p.relative_to(path_a).as_posix(): p for p in path_a.rglob("*") if p.is_file()}
        files_b = {p.relative_to(path_b).as_posix(): p for p in path_b.rglob("*") if p.is_file()}

        # Filter out caches and hidden files
        ignored_substrings = [".git", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules"]

        def is_ignored(rel: str) -> bool:
            return any(ign in rel for ign in ignored_substrings)

        all_rel_paths = sorted(
            {rel for rel in list(files_a.keys()) + list(files_b.keys()) if not is_ignored(rel)}
        )

        file_diffs: list[FileDiff] = []

        for rel in all_rel_paths:
            file_a = files_a.get(rel)
            file_b = files_b.get(rel)

            if file_a and not file_b:
                # Deleted
                content_a = file_a.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                diff_gen = difflib.unified_diff(content_a, [], fromfile=f"a/{rel}", tofile="/dev/null")
                diff_str = "".join(diff_gen)
                parsed = cls.parse_unified_diff(diff_str)
                if parsed:
                    parsed[0].change_type = FileChangeType.FILE_DELETED
                    parsed[0].old_path = rel
                    parsed[0].new_path = None
                    file_diffs.extend(parsed)
            elif not file_a and file_b:
                # Added
                content_b = file_b.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                diff_gen = difflib.unified_diff([], content_b, fromfile="/dev/null", tofile=f"b/{rel}")
                diff_str = "".join(diff_gen)
                parsed = cls.parse_unified_diff(diff_str)
                if parsed:
                    parsed[0].change_type = FileChangeType.FILE_ADDED
                    parsed[0].old_path = None
                    parsed[0].new_path = rel
                    file_diffs.extend(parsed)
            elif file_a and file_b:
                content_a = file_a.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                content_b = file_b.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
                if content_a == content_b:
                    continue
                diff_gen = difflib.unified_diff(content_a, content_b, fromfile=f"a/{rel}", tofile=f"b/{rel}")
                diff_str = "".join(diff_gen)
                parsed = cls.parse_unified_diff(diff_str)
                if parsed:
                    parsed[0].change_type = FileChangeType.FILE_MODIFIED
                    parsed[0].old_path = rel
                    parsed[0].new_path = rel
                    file_diffs.extend(parsed)

        return file_diffs
