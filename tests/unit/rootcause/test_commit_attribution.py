"""Unit tests for commit attribution and blame mapping."""

from apps.worker.rootcause.attribution.commits import CommitAttributor
from apps.worker.rootcause.localization.behavioral import LocalizedCandidate
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitAttributionType,
    CommitMetadata,
    DiffHunk,
    DiffLine,
    LineChangeType,
    RepositoryContext,
    SourceLocation,
)


def test_commit_attribution_with_context_commits():
    """Verify commit attribution when commits are provided in RepositoryContext."""
    sample_commit = CommitMetadata(
        commit_hash="a" * 40,
        author_name="Alice Dev",
        author_email="alice@example.com",
        timestamp="2026-09-30T10:00:00Z",
        message="refactor coupon schema",
    )
    repo_ctx = RepositoryContext(
        is_git_repository=False,
        commits=[sample_commit],
    )

    hunk = DiffHunk(
        old_start=1,
        old_lines=1,
        new_start=1,
        new_lines=2,
        lines=[DiffLine(change_type=LineChangeType.LINE_ADDED, content="+ val = 2", new_line_number=2)],
        added_lines=[2],
    )
    loc = SourceLocation(file_path="app.py", start_line=1, end_line=2)
    candidate = LocalizedCandidate(
        source_location=loc,
        symbol=None,
        diff_hunk=hunk,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        explanation="Direct change",
    )

    attributor = CommitAttributor()
    commit_meta, commit_type = attributor.attribute_commit(candidate, repo_ctx)

    assert commit_meta is not None
    assert commit_meta.commit_hash == "a" * 40
    assert commit_type == CommitAttributionType.RELATED_COMMIT


def test_commit_attribution_no_commits():
    """Verify commit attribution when no git repository or commits exist."""
    repo_ctx = RepositoryContext(is_git_repository=False, commits=[])
    loc = SourceLocation(file_path="app.py", start_line=1, end_line=2)
    candidate = LocalizedCandidate(
        source_location=loc,
        symbol=None,
        diff_hunk=None,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        explanation="Direct change",
    )

    attributor = CommitAttributor()
    commit_meta, commit_type = attributor.attribute_commit(candidate, repo_ctx)

    assert commit_meta is None
    assert commit_type == CommitAttributionType.NO_ATTRIBUTABLE_COMMIT


def test_causal_commit_attribution_on_located_regression():
    """Verify that a confirmed LOCATED root cause upgrades commit attribution to CAUSAL_COMMIT."""
    from apps.worker.regression.models import (
        ClassificationEvidence,
        ClassificationStatus,
        RegressionCategory,
        RegressionClassification,
    )
    from apps.worker.rootcause.ast.models import ASTFileIndex, ASTNodeInfo
    from apps.worker.rootcause.attribution.engine import AttributionEngine
    from apps.worker.rootcause.models import (
        ASTNodeType,
        FileChangeType,
        FileDiff,
        LanguageType,
        RootCauseStatus,
    )

    sample_commit = CommitMetadata(
        commit_hash="8f31c2" + "0" * 34,
        author_name="Alice Dev",
        author_email="alice@example.com",
        timestamp="2026-09-30T10:00:00Z",
        message="refactor coupon schema",
    )
    repo_ctx = RepositoryContext(
        is_git_repository=False,
        commits=[sample_commit],
    )

    hunk = DiffHunk(
        old_start=3,
        old_lines=2,
        new_start=3,
        new_lines=2,
        lines=[DiffLine(change_type=LineChangeType.LINE_ADDED, content='+ code = payload.get("couponCode")', new_line_number=3)],
        added_lines=[3],
    )
    fd = FileDiff(
        change_type=FileChangeType.FILE_MODIFIED,
        old_path="app.py",
        new_path="app.py",
        hunks=[hunk],
        language=LanguageType.PYTHON,
    )
    idx = ASTFileIndex(
        file_path="app.py",
        language=LanguageType.PYTHON,
        nodes=[
            ASTNodeInfo(
                name="apply_coupon",
                kind=ASTNodeType.ROUTE_HANDLER,
                start_line=1,
                end_line=6,
                route_path="/api/coupons/apply",
            )
        ],
    )

    classification = RegressionClassification(
        classification_id="class-api-01",
        difference_id="diff-api-01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.API_CONTRACT,
        rule_id="RULE-API-400",
        reason="API returned 400 Bad Request",
        evidence=ClassificationEvidence(
            difference_id="diff-api-01",
            canonical_subject="/api/coupons/apply",
            details={"endpoint": "/api/coupons/apply", "key": "couponCode"},
        ),
    )

    engine = AttributionEngine()
    result = engine.attribute(
        classification=classification,
        reproduction=None,
        diffs=[fd],
        ast_indices={"app.py": idx},
        repo_ctx=repo_ctx,
    )

    assert result.status == RootCauseStatus.LOCATED
    assert result.primary_attribution is not None
    assert result.primary_attribution.commit_attribution_type == CommitAttributionType.CAUSAL_COMMIT
    assert result.primary_attribution.commit.commit_hash == sample_commit.commit_hash
