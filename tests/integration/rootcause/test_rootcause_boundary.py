"""Integration test verifying strict architectural boundaries for Phase 9."""

from pathlib import Path


def test_root_cause_engine_boundary_invariants():
    """Verify that apps/worker/rootcause/ contains no LLM, embeddings, vector search, or severity ranking."""
    rootcause_dir = Path("apps/worker/rootcause")
    assert rootcause_dir.exists(), "Root cause package directory must exist"

    forbidden_tokens = [
        "openai",
        "langgraph",
        "langchain",
        "anthropic",
        "chat_completion",
        "vector_search",
        "semantic_search",
        "embeddings",
        "severity_ranking",
        "bug_score",
        "priority_score",
        "bayesian_score",
    ]

    violations = []
    for file_path in rootcause_dir.rglob("*.py"):
        content = file_path.read_text(encoding="utf-8").lower()
        for token in forbidden_tokens:
            if token in content:
                violations.append(f"File {file_path} contains forbidden boundary token '{token}'")

    assert not violations, "Boundary invariant violations in Phase 9:\n" + "\n".join(violations)
