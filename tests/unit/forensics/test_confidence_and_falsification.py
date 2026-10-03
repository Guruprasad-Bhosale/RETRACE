"""Unit tests for ConfidenceCalculator and FalsificationEngine."""

from packages.forensics.confidence import ConfidenceCalculator
from packages.forensics.falsification import FalsificationEngine
from packages.forensics.models import (
    ConfidenceLevel,
    ForensicEvidenceItem,
    ForensicEvidenceType,
    ForensicHypothesis,
    HypothesisCategory,
    HypothesisStatus,
)


def test_confidence_calculator_high_confidence():
    """Verify high confidence is assigned when reproduction and source attribution exist with 0 contradictions."""
    hyp = ForensicHypothesis(
        hypothesis_id="hyp_01",
        title="Checkout Discount Logic",
        description="Discount logic altered",
        category=HypothesisCategory.CALCULATION_LOGIC,
        status=HypothesisStatus.CONFIRMED,
        supporting_evidence_ids=["ev_1", "ev_2"],
        contradicting_evidence_ids=[],
    )

    catalog = {
        "ev_1": ForensicEvidenceItem(
            id="ev_1",
            investigation_id="inv_01",
            evidence_type=ForensicEvidenceType.REPRODUCTION,
            source="Playwright",
            observation="Reproduced",
        ),
        "ev_2": ForensicEvidenceItem(
            id="ev_2",
            investigation_id="inv_01",
            evidence_type=ForensicEvidenceType.AST_DIFF,
            source="AST Parser",
            observation="Source match",
        ),
    }

    assessment = ConfidenceCalculator.evaluate(
        primary_hypothesis=hyp,
        evidence_catalog=catalog,
        has_reproduction=True,
        has_source_match=True,
    )

    assert assessment.level == ConfidenceLevel.HIGH
    assert assessment.score >= 0.75
    assert assessment.supporting_count == 2
    assert assessment.contradicting_count == 0


def test_confidence_calculator_contradiction_penalty():
    """Verify contradicting evidence penalizes score and reduces confidence level."""
    hyp = ForensicHypothesis(
        hypothesis_id="hyp_02",
        title="Network Failure",
        description="API failed",
        category=HypothesisCategory.API_CONTRACT,
        status=HypothesisStatus.WEAKENED,
        supporting_evidence_ids=["ev_1"],
        contradicting_evidence_ids=["ev_contra"],
    )

    catalog = {
        "ev_1": ForensicEvidenceItem(
            id="ev_1",
            investigation_id="inv_02",
            evidence_type=ForensicEvidenceType.NETWORK_OBSERVATION,
            source="Network",
            observation="500 error candidate",
        ),
        "ev_contra": ForensicEvidenceItem(
            id="ev_contra",
            investigation_id="inv_02",
            evidence_type=ForensicEvidenceType.NETWORK_OBSERVATION,
            source="Network",
            observation="200 OK verified on second run",
        ),
    }

    assessment = ConfidenceCalculator.evaluate(
        primary_hypothesis=hyp,
        evidence_catalog=catalog,
        has_reproduction=False,
        has_source_match=False,
    )

    assert assessment.contradicting_count == 1
    assert assessment.level in (ConfidenceLevel.LOW, ConfidenceLevel.INSUFFICIENT)


def test_falsification_engine_generation():
    """Verify FalsificationEngine produces testable condition and confounders."""
    hyp = ForensicHypothesis(
        hypothesis_id="hyp_calc",
        title="Calculation logic regression",
        description="Subtotal discount calculation",
        category=HypothesisCategory.CALCULATION_LOGIC,
        status=HypothesisStatus.CONFIRMED,
    )

    falsification = FalsificationEngine.generate_falsification_condition(
        hypothesis=hyp,
        source_file="apps/commerce-lab/cart.py",
        line_number=45,
        commit_hash="c0ffee123456",
    )

    assert falsification.condition_id.startswith("fals_")
    assert "revert" in falsification.statement.lower()
    assert "cart.py:45" in falsification.statement
    assert len(falsification.potential_confounders) >= 2
