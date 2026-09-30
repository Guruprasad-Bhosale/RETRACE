"""Git Blame Lineage Analyzer.

Parses git blame annotations and correlates source line ranges to exact introducing commits.
"""

from pathlib import Path

from apps.worker.rootcause.git.repository import GitRepository
from apps.worker.rootcause.models import DiffHunk, SourceLocation


class BlameAnalyzer:
    """Deterministic analyzer mapping line ranges to git commits via blame inspection."""

    def __init__(self, git_repo: GitRepository | None = None):
        self.git_repo = git_repo or GitRepository()

    def get_commits_for_lines(
        self,
        repo_path: str | Path,
        ref: str,
        relative_path: str,
        line_numbers: list[int],
    ) -> dict[int, str]:
        """Map 1-indexed line numbers to 40-character commit hashes."""
        if not self.git_repo.is_git_repository(repo_path):
            return {}

        blame_lines = self.git_repo.get_blame_lines(repo_path, ref, relative_path)
        blame_map = dict(blame_lines)

        result: dict[int, str] = {}
        for ln in line_numbers:
            if ln in blame_map:
                result[ln] = blame_map[ln]
        return result

    def attribute_location_commit(
        self,
        repo_path: str | Path,
        ref: str,
        location: SourceLocation,
    ) -> str | None:
        """Find the primary commit responsible for a given SourceLocation."""
        target_lines = list(range(location.start_line, location.end_line + 1))
        mapping = self.get_commits_for_lines(
            repo_path=repo_path,
            ref=ref,
            relative_path=location.file_path,
            line_numbers=target_lines,
        )
        if not mapping:
            return None

        # Return the commit corresponding to the start line, or most frequent
        if location.start_line in mapping:
            return mapping[location.start_line]
        return next(iter(mapping.values()))

    def attribute_hunk_commit(
        self,
        repo_path: str | Path,
        ref: str,
        relative_path: str,
        hunk: DiffHunk,
    ) -> str | None:
        """Find the commit responsible for the added lines in a DiffHunk."""
        if not hunk.added_lines:
            return None

        mapping = self.get_commits_for_lines(
            repo_path=repo_path,
            ref=ref,
            relative_path=relative_path,
            line_numbers=hunk.added_lines,
        )
        if not mapping:
            return None
        return mapping.get(hunk.added_lines[0]) or next(iter(mapping.values()))
