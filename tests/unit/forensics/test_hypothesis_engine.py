"""Unit tests for HypothesisEngine lifecycle, formulation, and systematic elimination."""

from packages.forensics.hypothesis_engine import HypothesisEngine
from packages.forensics.models import (
    ForensicEvidenceItem,
    ForensicEvidenceType,
    HypothesisCategory,
    HypothesisStatus,
)


def test_hypothesis_formulation_and_alternatives_elimination():
    """Verify primary hypothesis is confirmed and alternative explanations are eliminated with reasons."""
    evidence = [
        ForensicEvidenceItem(
            id="ev_obs_1",
            investigation_id="inv_test_01",
            evidence_type=ForensicEvidenceType.DOM_OBSERVATION,
            source="Playwright",
            observation="Price total calculation mismatch",
        ),
        ForensicEvidenceItem(
            id="ev_ast_1",
            investigation_id="inv_test_01",
            evidence_type=ForensicEvidenceType.AST_DIFF,
            source="AST Parser",
            observation="discount computation function modified",
        ),
    ]

    primary, alternatives = HypothesisEngine.evaluate_hypotheses(
        investigation_id="inv_test_01",
        category="calculation",
        title="Cart Price Total Discrepancy",
        description="Calculation logic altered",
        evidence_items=evidence,
        has_reproduction=True,
        source_file="pricing.py",
        source_function="calculate_subtotal",
    )

    # Primary hypothesis checks
    assert primary.category == HypothesisCategory.CALCULATION_LOGIC
    assert primary.status == HypothesisStatus.CONFIRMED
    assert primary.score >= 0.90
    assert "ev_obs_1" in primary.supporting_evidence_ids

    # Alternatives checks
    assert len(alternatives) >= 2
    alt_categories = [alt.category for alt in alternatives]
    assert HypothesisCategory.STYLING_FORMATTING in alt_categories
    assert HypothesisCategory.API_CONTRACT in alt_categories

    for alt in alternatives:
        assert alt.status in (HypothesisStatus.ELIMINATED, HypothesisStatus.WEAKENED)
        assert len(alt.elimination_reason) > 10
        assert len(alt.evidence_references) > 0
