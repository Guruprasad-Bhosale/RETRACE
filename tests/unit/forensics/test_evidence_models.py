"""Unit tests for Forensic Evidence Models and Graph Entities."""


from packages.forensics.models import (
    EdgeType,
    EvidenceGraph,
    EvidenceGraphEdge,
    EvidenceGraphNode,
    ForensicEvidenceItem,
    ForensicEvidenceType,
    compute_deterministic_edge_id,
    compute_deterministic_evidence_id,
)


def test_deterministic_evidence_id_generation():
    """Verify evidence ID calculation is deterministic across multiple invocations."""
    id1 = compute_deterministic_evidence_id("inv_100", ForensicEvidenceType.DOM_OBSERVATION, "checkout_diff")
    id2 = compute_deterministic_evidence_id("inv_100", ForensicEvidenceType.DOM_OBSERVATION, "checkout_diff")
    id3 = compute_deterministic_evidence_id("inv_100", ForensicEvidenceType.NETWORK_OBSERVATION, "checkout_diff")

    assert id1 == id2
    assert id1.startswith("ev_")
    assert id1 != id3


def test_deterministic_edge_id_generation():
    """Verify edge ID calculation is deterministic."""
    edge1 = compute_deterministic_edge_id("node_a", "node_b", EdgeType.SUPPORTS)
    edge2 = compute_deterministic_edge_id("node_a", "node_b", EdgeType.SUPPORTS)
    edge3 = compute_deterministic_edge_id("node_a", "node_b", EdgeType.CONTRADICTS)

    assert edge1 == edge2
    assert edge1.startswith("edge_")
    assert edge1 != edge3


def test_forensic_evidence_item_creation():
    """Verify ForensicEvidenceItem validates properly and enforces type constraints."""
    item = ForensicEvidenceItem(
        id="ev_test_123",
        investigation_id="inv_456",
        evidence_type=ForensicEvidenceType.AST_DIFF,
        source="AST Parser",
        observation="Modified discount calculation on line 42",
        payload={"file": "cart.py", "line": 42},
        confidence_weight=0.95,
        supports=["hyp_01"],
    )

    assert item.id == "ev_test_123"
    assert item.evidence_type == ForensicEvidenceType.AST_DIFF
    assert item.confidence_weight == 0.95
    assert item.is_untrusted_input is True


def test_evidence_graph_model_validation():
    """Verify EvidenceGraph model aggregates nodes and edges with deterministic hash."""
    node1 = EvidenceGraphNode(node_id="n1", node_type="OBSERVATION", title="Obs 1")
    node2 = EvidenceGraphNode(node_id="n2", node_type="DIFF", title="Diff 1")
    edge = EvidenceGraphEdge(
        edge_id="e1",
        source_node_id="n1",
        target_node_id="n2",
        relationship=EdgeType.DERIVED_FROM,
        weight=1.0,
    )

    graph = EvidenceGraph(
        graph_id="graph_001",
        investigation_id="inv_001",
        nodes=[node1, node2],
        edges=[edge],
        deterministic_hash="hash123",
    )

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].relationship == EdgeType.DERIVED_FROM
