"""Integration tests for ForensicIntelligenceEngine with InvestigationResult."""

from packages.forensics.engine import ForensicIntelligenceEngine
from packages.forensics.models import (
    ConfidenceLevel,
    ForensicInvestigationExplanation,
    HypothesisCategory,
    HypothesisStatus,
)


def test_forensic_intelligence_engine_end_to_end():
    """Verify ForensicIntelligenceEngine synthesizes complete explanation from InvestigationResult."""
    from apps.api.routers.v1.investigations import (
        _INVESTIGATION_REGISTRY,
        clear_investigations,
        seed_sample_investigations,
    )

    clear_investigations()
    seed_sample_investigations()
    sample_inv = _INVESTIGATION_REGISTRY["inv_comm_cart_01"]

    explanation = ForensicIntelligenceEngine.explain_investigation(sample_inv)

    assert isinstance(explanation, ForensicInvestigationExplanation)
    assert explanation.investigation_id == sample_inv.investigation_id
    assert explanation.evidence_graph_available is True

    # Graph structure
    graph = explanation.evidence_graph
    assert len(graph.nodes) >= 5
    assert len(graph.edges) >= 4
    assert graph.deterministic_hash != ""

    # Primary hypothesis
    hyp = explanation.primary_hypothesis
    assert hyp.status == HypothesisStatus.CONFIRMED
    assert hyp.category in (HypothesisCategory.DOM_RENDER_LOGIC, HypothesisCategory.CALCULATION_LOGIC)

    # Eliminated alternatives
    assert len(explanation.eliminated_alternatives) >= 2
    for alt in explanation.eliminated_alternatives:
        assert alt.status in (HypothesisStatus.ELIMINATED, HypothesisStatus.WEAKENED)
        assert len(alt.elimination_reason) > 0

    # Confidence assessment
    assert explanation.confidence.level in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM)
    assert explanation.confidence.supporting_count >= 1
    assert explanation.confidence.contradicting_count == 0

    # Falsification condition
    assert explanation.falsification.condition_id.startswith("fals_")
    assert len(explanation.falsification.potential_confounders) >= 2
