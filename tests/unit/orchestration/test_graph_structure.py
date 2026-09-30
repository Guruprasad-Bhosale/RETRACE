"""Unit tests for LangGraph investigation graph structure and compilation."""


from apps.worker.orchestration.graph import create_investigation_graph
from apps.worker.orchestration.nodes import InvestigationNodeAdapters


def test_graph_node_registration_and_compilation():
    """Verify all 11 required investigation nodes are present in the compiled graph."""
    adapters = InvestigationNodeAdapters()
    graph = create_investigation_graph(adapters=adapters)

    assert graph is not None
    # Verify graph contains the expected nodes
    nodes = graph.nodes
    expected_nodes = [
        "validate_inputs",
        "prepare_versions",
        "explore",
        "align",
        "diff",
        "classify",
        "reproduce",
        "root_cause",
        "assemble",
        "finalize",
        "finalize_no_regression",
    ]
    for node_name in expected_nodes:
        assert node_name in nodes, f"Missing node: {node_name}"
