"""LangGraph State Graph Assembly for RETRACE Investigation Pipeline."""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from apps.worker.orchestration.checkpoint import get_default_checkpointer
from apps.worker.orchestration.models import InvestigationWorkflowState
from apps.worker.orchestration.nodes import InvestigationNodeAdapters
from apps.worker.orchestration.routing import (
    route_after_align,
    route_after_assemble,
    route_after_classify,
    route_after_diff,
    route_after_explore,
    route_after_prepare,
    route_after_reproduce,
    route_after_root_cause,
    route_after_validate,
)


def create_investigation_graph(
    adapters: InvestigationNodeAdapters | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """Build and compile the authoritative LangGraph state graph for investigations."""
    node_adapters = adapters or InvestigationNodeAdapters()
    effective_checkpointer = (
        checkpointer if checkpointer is not None else get_default_checkpointer()
    )

    builder = StateGraph(InvestigationWorkflowState)

    # 1. Register Graph Nodes
    builder.add_node("validate_inputs", node_adapters.validate_inputs)
    builder.add_node("prepare_versions", node_adapters.prepare_versions)
    builder.add_node("explore", node_adapters.explore)
    builder.add_node("align", node_adapters.align)
    builder.add_node("diff", node_adapters.diff)
    builder.add_node("classify", node_adapters.classify)
    builder.add_node("reproduce", node_adapters.reproduce)
    builder.add_node("root_cause", node_adapters.root_cause)
    builder.add_node("assemble", node_adapters.assemble)
    builder.add_node("finalize", node_adapters.finalize)
    builder.add_node("finalize_no_regression", node_adapters.finalize_no_regression)

    # 2. Wire Linear & Conditional Edges
    builder.add_edge(START, "validate_inputs")
    builder.add_conditional_edges("validate_inputs", route_after_validate)
    builder.add_conditional_edges("prepare_versions", route_after_prepare)
    builder.add_conditional_edges("explore", route_after_explore)
    builder.add_conditional_edges("align", route_after_align)
    builder.add_conditional_edges("diff", route_after_diff)
    builder.add_conditional_edges("classify", route_after_classify)
    builder.add_conditional_edges("reproduce", route_after_reproduce)
    builder.add_conditional_edges("root_cause", route_after_root_cause)
    builder.add_conditional_edges("assemble", route_after_assemble)
    builder.add_edge("finalize", END)
    builder.add_edge("finalize_no_regression", END)

    return builder.compile(checkpointer=effective_checkpointer)
