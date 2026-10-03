"""Unit tests for EvidenceGraphBuilder DAG construction and determinism."""

import pytest

from packages.forensics.graph_builder import EvidenceGraphBuilder
from packages.forensics.models import (
    EdgeType,
    ForensicEvidenceItem,
    ForensicEvidenceType,
    ForensicHypothesis,
    HypothesisCategory,
    HypothesisStatus,
)


@pytest.fixture
def sample_hypothesis():
    return ForensicHypothesis(
        hypothesis_id="hyp_calc_01",
        title="Calculation logic regression",
        description="Discount logic altered in cart calculation",
        category=HypothesisCategory.CALCULATION_LOGIC,
        status=HypothesisStatus.CONFIRMED,
        supporting_evidence_ids=["ev_1", "ev_2"],
        score=0.95,
    )


@pytest.fixture
def sample_evidence():
    return [
        ForensicEvidenceItem(
            id="ev_1",
            investigation_id="inv_test",
            evidence_type=ForensicEvidenceType.DOM_OBSERVATION,
            source="Browser Observation Engine",
            observation="Total displayed as $90 instead of $80",
        ),
        ForensicEvidenceItem(
            id="ev_2",
            investigation_id="inv_test",
            evidence_type=ForensicEvidenceType.AST_DIFF,
            source="AST Parser",
            observation="compute_discount modified on line 55",
        ),
    ]


def test_evidence_graph_builder_topology(sample_hypothesis, sample_evidence):
    """Verify graph builder constructs all expected node types and semantic relationships."""
    graph = EvidenceGraphBuilder.build_graph(
        investigation_id="inv_test",
        category="calculation",
        title="Checkout Discount Calculation Mismatch",
        hypothesis=sample_hypothesis,
        evidence_items=sample_evidence,
        source_file="cart.py",
        source_line=55,
        commit_hash="a1b2c3d4e5f6",
        reproduction_code="await page.click('#checkout')",
    )

    node_types = [n.node_type for n in graph.nodes]
    assert "OBSERVATION" in node_types
    assert "DIFF" in node_types
    assert "HYPOTHESIS" in node_types
    assert "SOURCE_DIFF" in node_types
    assert "ROOT_CAUSE" in node_types
    assert "REPRODUCTION" in node_types

    edge_relationships = [e.relationship for e in graph.edges]
    assert EdgeType.DERIVED_FROM in edge_relationships
    assert EdgeType.SUPPORTS in edge_relationships
    assert EdgeType.LOCATED_AT in edge_relationships
    assert EdgeType.CAUSED_BY in edge_relationships
    assert EdgeType.REPRODUCES in edge_relationships


def test_evidence_graph_determinism(sample_hypothesis, sample_evidence):
    """Verify building the graph twice produces identical hashes and node IDs."""
    graph1 = EvidenceGraphBuilder.build_graph(
        investigation_id="inv_test",
        category="calculation",
        title="Checkout Discount Calculation Mismatch",
        hypothesis=sample_hypothesis,
        evidence_items=sample_evidence,
        source_file="cart.py",
        source_line=55,
    )

    graph2 = EvidenceGraphBuilder.build_graph(
        investigation_id="inv_test",
        category="calculation",
        title="Checkout Discount Calculation Mismatch",
        hypothesis=sample_hypothesis,
        evidence_items=sample_evidence,
        source_file="cart.py",
        source_line=55,
    )

    assert graph1.graph_id == graph2.graph_id
    assert graph1.deterministic_hash == graph2.deterministic_hash
    assert [n.node_id for n in graph1.nodes] == [n.node_id for n in graph2.nodes]
    assert [e.edge_id for e in graph1.edges] == [e.edge_id for e in graph2.edges]
