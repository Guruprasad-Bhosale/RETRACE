"""Unit tests for Git repository safety, diff extraction, and commit metadata retrieval."""

from pathlib import Path

import pytest

from apps.worker.rootcause.config import GitAnalysisConfig
from apps.worker.rootcause.errors import RepositoryAnalysisError, UnsafePathError
from apps.worker.rootcause.git.repository import GitRepository


def test_git_repository_path_validation(tmp_path):
    """Verify repository path sanitization and non-existent path rejection."""
    git_repo = GitRepository()

    with pytest.raises(RepositoryAnalysisError, match="Repository path does not exist"):
        git_repo._sanitize_path(tmp_path / "non_existent_folder_xyz")

    dummy_file = tmp_path / "file.txt"
    dummy_file.write_text("hello", encoding="utf-8")
    with pytest.raises(RepositoryAnalysisError, match="Repository path is not a directory"):
        git_repo._sanitize_path(dummy_file)


def test_git_repository_unsafe_argument_rejection():
    """Verify rejection of command line flags disguised as refs or file paths."""
    git_repo = GitRepository()

    with pytest.raises(UnsafePathError, match="Unsafe argument starting with flag delimiter"):
        git_repo._validate_ref_or_path("--exec=whoami")

    with pytest.raises(UnsafePathError, match="Unsafe argument starting with flag delimiter"):
        git_repo._validate_ref_or_path("-v")

    with pytest.raises(UnsafePathError, match="Git argument cannot be empty"):
        git_repo._validate_ref_or_path("   ")


def test_git_repository_is_git_repo_on_current_repo():
    """Verify is_git_repository on current repository workspace."""
    git_repo = GitRepository()
    assert git_repo.is_git_repository(Path.cwd()) is True
    assert git_repo.is_git_repository(Path.cwd() / "non_existent") is False


def test_git_repository_list_commits_and_metadata():
    """Verify reading commit log and metadata from the active Git repository."""
    git_repo = GitRepository(config=GitAnalysisConfig(max_commits_to_walk=5))
    commits = git_repo.list_commits(Path.cwd(), max_count=3)
    assert len(commits) >= 1

    head_commit = commits[0]
    assert len(head_commit.commit_hash) == 40
    assert head_commit.author_name != ""
    assert head_commit.timestamp != ""

    # Test single commit metadata retrieval
    single = git_repo.get_commit_metadata(Path.cwd(), head_commit.commit_hash)
    assert single.commit_hash == head_commit.commit_hash
    assert single.author_name == head_commit.author_name
