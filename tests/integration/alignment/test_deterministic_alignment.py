"""Integration test verifying alignment determinism and discovery order invariance."""

from uuid import uuid4

from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.exploration.coverage import CoverageMetrics
from apps.worker.exploration.diagnostics import ExplorationResult


def test_alignment_order_invariance() -> None:
    """CRITICAL TEST:
    Version A discovers children in order: [A1, A2]
    Version B discovers children in reverse order: [B2, B1]

    The resulting pairings must be identical: (A1 <-> B1), (A2 <-> B2).
    """
    aligner = TrajectoryAligner()

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
        unique_routes=["/", "/cart", "/account"],
        termination_reason="max_depth",
        elapsed_time_sec=0.3,
        coverage=CoverageMetrics(),
        # Discovery order A1 then A2
        state_graph_nodes=[
            {"state_id": "A0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {"state_id": "A1", "route": "/cart", "depth": 1, "metadata": {"http_status": 200}},
            {"state_id": "A2", "route": "/account", "depth": 1, "metadata": {"http_status": 200}},
        ],
        state_graph_edges=[
            {
                "transition_id": "t_A0_A1",
                "from_state_id": "A0",
                "to_state_id": "A1",
                "action_type": "CLICK",
                "target_element_id": "cart_btn",
                "metadata": {"tag": "button", "accessible_name": "Cart"},
            },
            {
                "transition_id": "t_A0_A2",
                "from_state_id": "A0",
                "to_state_id": "A2",
                "action_type": "CLICK",
                "target_element_id": "account_btn",
                "metadata": {"tag": "button", "accessible_name": "Account"},
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
        unique_routes=["/", "/account", "/cart"],
        termination_reason="max_depth",
        elapsed_time_sec=0.3,
        coverage=CoverageMetrics(),
        # Discovery order B2 then B1 (reversed)
        state_graph_nodes=[
            {"state_id": "B0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {"state_id": "B2", "route": "/account", "depth": 1, "metadata": {"http_status": 200}},
            {"state_id": "B1", "route": "/cart", "depth": 1, "metadata": {"http_status": 200}},
        ],
        state_graph_edges=[
            {
                "transition_id": "t_B0_B2",
                "from_state_id": "B0",
                "to_state_id": "B2",
                "action_type": "CLICK",
                "target_element_id": "account_btn",
                "metadata": {"tag": "button", "accessible_name": "Account"},
            },
            {
                "transition_id": "t_B0_B1",
                "from_state_id": "B0",
                "to_state_id": "B1",
                "action_type": "CLICK",
                "target_element_id": "cart_btn",
                "metadata": {"tag": "button", "accessible_name": "Cart"},
            },
        ],
    )

    alignment_res = aligner.align(res_a, res_b)
    align = alignment_res.alignment

    matched_pairs = {(st.state_a_id, st.state_b_id) for st in align.aligned_states}
    assert ("A0", "B0") in matched_pairs
    assert ("A1", "B1") in matched_pairs
    assert ("A2", "B2") in matched_pairs
