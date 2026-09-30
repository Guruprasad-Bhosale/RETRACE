"""Deterministic Commit Attribution Layer.

Correlates localized source locations to introducing or modifying commits via Git inspection and blame.
"""

from pathlib import Path

from apps.worker.rootcause.git.blame import BlameAnalyzer
from apps.worker.rootcause.git.commits import CommitAnalyzer
from apps.worker.rootcause.git.repository import GitRepository
from apps.worker.rootcause.localization.behavioral import LocalizedCandidate
from apps.worker.rootcause.models import (
    CommitAttributionType,
    CommitMetadata,
    RepositoryContext,
)


class CommitAttributor:
    """Deterministic attributor linking source candidates to Git commits."""

    def __init__(
        self,
        git_repo: GitRepository | None = None,
        commit_analyzer: CommitAnalyzer | None = None,
        blame_analyzer: BlameAnalyzer | None = None,
    ):
        self.git_repo = git_repo or GitRepository()
        self.commit_analyzer = commit_analyzer or CommitAnalyzer(git_repo=self.git_repo)
        self.blame_analyzer = blame_analyzer or BlameAnalyzer(git_repo=self.git_repo)

    def attribute_commit(
        self,
        candidate: LocalizedCandidate,
        repo_ctx: RepositoryContext,
    ) -> tuple[CommitMetadata | None, CommitAttributionType]:
        """Determine the most authoritative commit for a localized candidate."""
        if not repo_ctx.is_git_repository or not repo_ctx.repository_path:
            # Check if synthetic commit metadata exists in repo_ctx
            if repo_ctx.commits:
                return repo_ctx.commits[0], CommitAttributionType.RELATED_COMMIT
            return None, CommitAttributionType.NO_ATTRIBUTABLE_COMMIT

        repo_path = Path(repo_ctx.repository_path)
        target_ref = repo_ctx.target_ref or "HEAD"
        baseline_ref = repo_ctx.baseline_ref

        # 1. Try git blame for the specific hunk / added lines
        commit_hash: str | None = None
        if candidate.diff_hunk and candidate.diff_hunk.added_lines:
            commit_hash = self.blame_analyzer.attribute_hunk_commit(
                repo_path=repo_path,
                ref=target_ref,
                relative_path=candidate.source_location.file_path,
                hunk=candidate.diff_hunk,
            )
            if commit_hash:
                try:
                    meta = self.git_repo.get_commit_metadata(repo_path, commit_hash)
                    return meta, CommitAttributionType.INTRODUCING_COMMIT
                except Exception:
                    pass

        # 2. Try blame for start line
        commit_hash = self.blame_analyzer.attribute_location_commit(
            repo_path=repo_path,
            ref=target_ref,
            location=candidate.source_location,
        )
        if commit_hash:
            try:
                meta = self.git_repo.get_commit_metadata(repo_path, commit_hash)
                return meta, CommitAttributionType.MODIFYING_COMMIT
            except Exception:
                pass

        # 3. Try commit history for the file
        file_commits = self.commit_analyzer.find_commits_for_file(
            repo_path=repo_path,
            file_path=candidate.source_location.file_path,
            baseline_ref=baseline_ref,
            target_ref=target_ref,
        )
        if file_commits:
            return file_commits[0], CommitAttributionType.MODIFYING_COMMIT

        # 4. Fallback to top commit in range
        if repo_ctx.commits:
            return repo_ctx.commits[0], CommitAttributionType.RELATED_COMMIT

        return None, CommitAttributionType.NO_ATTRIBUTABLE_COMMIT
