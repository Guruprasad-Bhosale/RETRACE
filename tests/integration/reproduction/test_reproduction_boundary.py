"""Integration test verifying strict architectural boundaries for Phase 8."""

from pathlib import Path


def test_reproduction_engine_boundary_invariants():
    """Verify that apps/worker/reproduction/ contains no root-cause, Git, AST, ranking, or LLM code."""
    reproduction_dir = Path("apps/worker/reproduction")
    assert reproduction_dir.exists()

    forbidden_tokens = [
        "openai",
        "langgraph",
        "anthropic",
        "chat_completion",
        "git.repo",
        "git.commit",
        "ast.parse",
        "root_cause_analysis",
        "severity_ranking",
        "bug_score",
        "priority_score",
    ]

    violations = []
    for file_path in reproduction_dir.rglob("*.py"):
        content = file_path.read_text(encoding="utf-8").lower()
        for token in forbidden_tokens:
            if token in content:
                violations.append(f"File {file_path} contains forbidden boundary token '{token}'")

    assert not violations, "Boundary invariant violations in Phase 8:\n" + "\n".join(violations)
