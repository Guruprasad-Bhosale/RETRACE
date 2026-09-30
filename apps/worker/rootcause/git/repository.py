"""Safe, Read-Only Git Repository Inspection Layer.

Enforces strict security boundaries, path sanitization, timeout controls,
and argument construction without invoking arbitrary repository scripts or mutating git state.
"""

import os
import shutil
import subprocess
from pathlib import Path

from apps.worker.rootcause.config import GitAnalysisConfig
from apps.worker.rootcause.errors import (
    GitExecutionError,
    RepositoryAnalysisError,
    UnsafePathError,
)
from apps.worker.rootcause.models import CommitMetadata


class GitRepository:
    """Safe read-only interface to Git repositories."""

    def __init__(self, config: GitAnalysisConfig | None = None):
        self.config = config or GitAnalysisConfig()
        self._git_bin = shutil.which("git")

    def _sanitize_path(self, path: str | Path) -> Path:
        """Validate and sanitize a repository path."""
        p = Path(path).resolve()
        if not p.exists():
            raise RepositoryAnalysisError(f"Repository path does not exist: {p}")
        if not p.is_dir():
            raise RepositoryAnalysisError(f"Repository path is not a directory: {p}")
        return p

    def _validate_ref_or_path(self, value: str) -> str:
        """Reject flags or dangerous arguments disguised as git refs/paths."""
        s = str(value).strip()
        if not s:
            raise UnsafePathError("Git argument cannot be empty")
        if s.startswith("-"):
            raise UnsafePathError(f"Unsafe argument starting with flag delimiter: '{s}'")
        return s

    def _run_git(self, repo_path: Path, args: list[str]) -> str:
        """Execute a controlled read-only git command."""
        if not self._git_bin:
            raise GitExecutionError("Git binary is not available on this system")

        cmd = [self._git_bin, "-C", str(repo_path)] + args
        env = {
            "LC_ALL": "C",
            "PATH": os.environ.get("PATH", ""),
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
            "WINDIR": os.environ.get("WINDIR", ""),
        }

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.git_timeout_seconds,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as exc:
            raise GitExecutionError(
                f"Git command timed out after {self.config.git_timeout_seconds}s: {' '.join(cmd)}"
            ) from exc
        except Exception as exc:
            raise GitExecutionError(f"Failed to execute git command: {exc}") from exc

        if res.returncode != 0:
            err_msg = res.stderr.strip() or res.stdout.strip()
            raise GitExecutionError(f"Git command failed (exit {res.returncode}): {err_msg}")

        return res.stdout

    def is_git_repository(self, path: str | Path) -> bool:
        """Check whether the specified path is inside a valid git repository."""
        try:
            repo_path = self._sanitize_path(path)
            out = self._run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
            return out.strip().lower() == "true"
        except Exception:
            return False

    def resolve_ref(self, repo_path: str | Path, ref: str) -> str:
        """Resolve a git branch, tag, or symbol ref to a 40-character commit hash."""
        p = self._sanitize_path(repo_path)
        safe_ref = self._validate_ref_or_path(ref)
        out = self._run_git(p, ["rev-parse", "--verify", f"{safe_ref}^{{commit}}"])
        return out.strip()

    def get_commit_metadata(self, repo_path: str | Path, commit_hash: str) -> CommitMetadata:
        """Retrieve structured metadata for a single commit."""
        p = self._sanitize_path(repo_path)
        safe_hash = self._validate_ref_or_path(commit_hash)
        # Format: hash%x1fauthor%x1femail%x1fiso_date%x1fparents%x1fmessage
        fmt = "%H%x1f%an%x1f%ae%x1f%aI%x1f%P%x1f%B"
        out = self._run_git(p, ["log", "-n", "1", f"--format={fmt}", safe_hash])
        parts = out.split("\x1f")
        if len(parts) < 6:
            raise GitExecutionError(f"Failed to parse commit log for {commit_hash}")

        h, an, ae, date, parents, msg = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
        parent_list = [pr.strip() for pr in parents.split() if pr.strip()]
        return CommitMetadata(
            commit_hash=h.strip(),
            author_name=an.strip(),
            author_email=ae.strip(),
            timestamp=date.strip(),
            message=msg.strip(),
            parent_hashes=parent_list,
            is_merge=len(parent_list) > 1,
        )

    def list_commits(
        self,
        repo_path: str | Path,
        baseline_ref: str | None = None,
        target_ref: str | None = None,
        max_count: int = 100,
    ) -> list[CommitMetadata]:
        """List commits in ancestry between baseline_ref and target_ref."""
        p = self._sanitize_path(repo_path)
        args = ["log", f"-n{max(1, min(max_count, self.config.max_commits_to_walk))}"]
        fmt = "%H%x1f%an%x1f%ae%x1f%aI%x1f%P%x1f%s"
        args.append(f"--format={fmt}")

        if baseline_ref and target_ref:
            safe_base = self._validate_ref_or_path(baseline_ref)
            safe_target = self._validate_ref_or_path(target_ref)
            args.append(f"{safe_base}..{safe_target}")
        elif target_ref:
            safe_target = self._validate_ref_or_path(target_ref)
            args.append(safe_target)

        out = self._run_git(p, args)
        commits: list[CommitMetadata] = []
        for line in out.strip().splitlines():
            line_str = line.strip()
            if not line_str:
                continue
            parts = line_str.split("\x1f")
            if len(parts) >= 6:
                h, an, ae, date, parents, subj = parts[0], parts[1], parts[2], parts[3], parts[4], parts[5]
                parent_list = [pr.strip() for pr in parents.split() if pr.strip()]
                commits.append(
                    CommitMetadata(
                        commit_hash=h.strip(),
                        author_name=an.strip(),
                        author_email=ae.strip(),
                        timestamp=date.strip(),
                        message=subj.strip(),
                        parent_hashes=parent_list,
                        is_merge=len(parent_list) > 1,
                    )
                )
        return commits

    def get_diff(
        self,
        repo_path: str | Path,
        baseline_ref: str,
        target_ref: str,
        paths: list[str] | None = None,
    ) -> str:
        """Get unified diff between two refs."""
        p = self._sanitize_path(repo_path)
        safe_base = self._validate_ref_or_path(baseline_ref)
        safe_target = self._validate_ref_or_path(target_ref)
        args = ["diff", "--unified=3", safe_base, safe_target]
        if paths:
            args.append("--")
            for path_str in paths:
                args.append(self._validate_ref_or_path(path_str))
        return self._run_git(p, args)

    def get_file_at_ref(self, repo_path: str | Path, ref: str, relative_path: str) -> str:
        """Retrieve the exact text content of a file at a specific git ref."""
        p = self._sanitize_path(repo_path)
        safe_ref = self._validate_ref_or_path(ref)
        safe_rel = self._validate_ref_or_path(relative_path).replace("\\", "/")
        return self._run_git(p, ["show", f"{safe_ref}:{safe_rel}"])

    def get_blame_lines(
        self, repo_path: str | Path, ref: str, relative_path: str
    ) -> list[tuple[int, str]]:
        """Run git blame --porcelain and return a list of (1-indexed line_number, commit_hash)."""
        p = self._sanitize_path(repo_path)
        safe_ref = self._validate_ref_or_path(ref)
        safe_rel = self._validate_ref_or_path(relative_path).replace("\\", "/")
        out = self._run_git(p, ["blame", "--porcelain", safe_ref, "--", safe_rel])

        lines_result: list[tuple[int, str]] = []
        for line in out.splitlines():
            # Line format in porcelain: "<hash> <orig_line> <final_line> [<group_lines>]"
            parts = line.strip().split()
            if len(parts) >= 3 and len(parts[0]) == 40:
                commit_h = parts[0]
                try:
                    final_line = int(parts[2])
                    lines_result.append((final_line, commit_h))
                except ValueError:
                    continue
        return lines_result
