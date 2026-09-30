"""Commit History and Ancestry Analyzer.

Provides deterministic analysis of commit sequences, ancestor walking,
and commit-to-diff linkage without recency-based speculation.
"""

from pathlib import Path

from apps.worker.rootcause.config import GitAnalysisConfig
from apps.worker.rootcause.git.repository import GitRepository
from apps.worker.rootcause.models import CommitMetadata


class CommitAnalyzer:
    """Deterministic analyzer for commit ancestry and commit metadata."""

    def __init__(self, git_repo: GitRepository | None = None, config: GitAnalysisConfig | None = None):
        self.config = config or GitAnalysisConfig()
        self.git_repo = git_repo or GitRepository(config=self.config)

    def get_commit_lineage(
        self, repo_path: str | Path, baseline_ref: str | None, target_ref: str | None
    ) -> list[CommitMetadata]:
        """Retrieve ordered commits between baseline_ref and target_ref."""
        if not self.git_repo.is_git_repository(repo_path):
            return []

        return self.git_repo.list_commits(
            repo_path=repo_path,
            baseline_ref=baseline_ref,
            target_ref=target_ref,
            max_count=self.config.max_commits_to_walk,
        )

    def find_commits_for_file(
        self, repo_path: str | Path, file_path: str, baseline_ref: str | None, target_ref: str | None
    ) -> list[CommitMetadata]:
        """List commits modifying a specific file between baseline and target."""
        if not self.git_repo.is_git_repository(repo_path):
            return []

        p = Path(repo_path).resolve()
        args = ["log", f"-n{self.config.max_commits_to_walk}"]
        fmt = "%H%x1f%an%x1f%ae%x1f%aI%x1f%P%x1f%s"
        args.append(f"--format={fmt}")

        if baseline_ref and target_ref:
            args.append(f"{baseline_ref}..{target_ref}")
        elif target_ref:
            args.append(target_ref)

        args.extend(["--", file_path])
        out = self.git_repo._run_git(p, args)

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
