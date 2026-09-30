"""Integration test for graph branching and multi-path alignment."""

from uuid import uuid4

from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.exploration.coverage import CoverageMetrics
from apps.worker.exploration.diagnostics import ExplorationResult


def test_branching_paths_align_correctly() -> None:
    aligner = TrajectoryAligner()

    # Root s0 branches into s1 (cart) and s2 (search)
    res_a = ExplorationResult(
        run_id=uuid4(),
        trajectory_id=uuid4(),
        seed_url="http://localhost:3001/",
        total_steps=3,
        states_discovered=3,
        transitions_count=2,
        successful_transitions=2,
        failed_transitions=0,
        skipped_candidates=0,
        unique_routes=["/", "/cart", "/search"],
        termination_reason="max_depth",
        elapsed_time_sec=0.4,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {"state_id": "s0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {"state_id": "s1", "route": "/cart", "depth": 1, "metadata": {"http_status": 200}},
            {"state_id": "s2", "route": "/search", "depth": 1, "metadata": {"http_status": 200}},
        ],
        state_graph_edges=[
            {
                "transition_id": "t_cart_a",
                "from_state_id": "s0",
                "to_state_id": "s1",
                "action_type": "CLICK",
                "target_element_id": "btn_cart",
                "metadata": {"tag": "button", "accessible_name": "Cart"},
            },
            {
                "transition_id": "t_search_a",
                "from_state_id": "s0",
                "to_state_id": "s2",
                "action_type": "CLICK",
                "target_element_id": "btn_search",
                "metadata": {"tag": "button", "accessible_name": "Search"},
            },
        ],
    )

    res_b = ExplorationResult(
        run_id=uuid4(),
        trajectory_id=uuid4(),
        seed_url="http://localhost:3002/",
        total_steps=3,
        states_discovered=3,
        transitions_count=2,
        successful_transitions=2,
        failed_transitions=0,
        skipped_candidates=0,
        unique_routes=["/", "/cart", "/search"],
        termination_reason="max_depth",
        elapsed_time_sec=0.4,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {"state_id": "s0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {"state_id": "s1", "route": "/cart", "depth": 1, "metadata": {"http_status": 200}},
            {"state_id": "s2", "route": "/search", "depth": 1, "metadata": {"http_status": 200}},
        ],
        state_graph_edges=[
            {
                "transition_id": "t_cart_b",
                "from_state_id": "s0",
                "to_state_id": "s1",
                "action_type": "CLICK",
                "target_element_id": "btn_cart",
                "metadata": {"tag": "button", "accessible_name": "Cart"},
            },
            {
                "transition_id": "t_search_b",
                "from_state_id": "s0",
                "to_state_id": "s2",
                "action_type": "CLICK",
                "target_element_id": "btn_search",
                "metadata": {"tag": "button", "accessible_name": "Search"},
            },
        ],
    )

    alignment_res = aligner.align(res_a, res_b)
    align = alignment_res.alignment

    assert len(align.aligned_states) == 3
    assert len(align.aligned_transitions) == 2
