"""Integration test for unmatched states (Additional states in B / Missing states in A)."""

from uuid import uuid4

from apps.worker.alignment.models import DivergenceType
from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.exploration.coverage import CoverageMetrics
from apps.worker.exploration.diagnostics import ExplorationResult


def test_additional_state_in_version_b_remains_unmatched() -> None:
    """CRITICAL TEST:

    Version A: A0 -> A1 -> A2
    Version B: B0 -> B1 -> B2 -> B3 (where B3 is an additional state)

    Expected:
    A0 <-> B0
    A1 <-> B1
    A2 <-> B2
    B3 -> in unmatched_b_states (NOT forced into any A state).
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
        unique_routes=["/", "/cart", "/checkout"],
        termination_reason="max_depth",
        elapsed_time_sec=0.3,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {"state_id": "A0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {"state_id": "A1", "route": "/cart", "depth": 1, "metadata": {"http_status": 200}},
            {"state_id": "A2", "route": "/checkout", "depth": 2, "metadata": {"http_status": 200}},
        ],
        state_graph_edges=[
            {
                "transition_id": "t_A0_A1",
                "from_state_id": "A0",
                "to_state_id": "A1",
                "action_type": "CLICK",
                "target_element_id": "cart-link",
                "metadata": {"tag": "a", "accessible_name": "Cart"},
            },
            {
                "transition_id": "t_A1_A2",
                "from_state_id": "A1",
                "to_state_id": "A2",
                "action_type": "CLICK",
                "target_element_id": "checkout-btn",
                "metadata": {"tag": "button", "accessible_name": "Checkout"},
            },
        ],
    )

    res_b = ExplorationResult(
        run_id=uuid4(),
        trajectory_id=uuid4(),
        seed_url="http://localhost:3002/",
        total_steps=4,
        states_discovered=4,
        transitions_count=3,
        successful_transitions=3,
        failed_transitions=0,
        skipped_candidates=0,
        unique_routes=["/", "/cart", "/checkout", "/order-confirmation"],
        termination_reason="max_depth",
        elapsed_time_sec=0.4,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {"state_id": "B0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {"state_id": "B1", "route": "/cart", "depth": 1, "metadata": {"http_status": 200}},
            {"state_id": "B2", "route": "/checkout", "depth": 2, "metadata": {"http_status": 200}},
            {"state_id": "B3", "route": "/order-confirmation", "depth": 3, "metadata": {"http_status": 200}},
        ],
        state_graph_edges=[
            {
                "transition_id": "t_B0_B1",
                "from_state_id": "B0",
                "to_state_id": "B1",
                "action_type": "CLICK",
                "target_element_id": "cart-link",
                "metadata": {"tag": "a", "accessible_name": "Cart"},
            },
            {
                "transition_id": "t_B1_B2",
                "from_state_id": "B1",
                "to_state_id": "B2",
                "action_type": "CLICK",
                "target_element_id": "checkout-btn",
                "metadata": {"tag": "button", "accessible_name": "Checkout"},
            },
            {
                "transition_id": "t_B2_B3",
                "from_state_id": "B2",
                "to_state_id": "B3",
                "action_type": "CLICK",
                "target_element_id": "confirm-btn",
                "metadata": {"tag": "button", "accessible_name": "Confirm"},
            },
        ],
    )

    alignment_res = aligner.align(res_a, res_b)
    align = alignment_res.alignment

    # Assert 3 matched states: A0 <-> B0, A1 <-> B1, A2 <-> B2
    matched_pairs = {(st.state_a_id, st.state_b_id) for st in align.aligned_states}
    assert ("A0", "B0") in matched_pairs
    assert ("A1", "B1") in matched_pairs
    assert ("A2", "B2") in matched_pairs

    # Assert B3 is NOT in any matched pair and is in unmatched_b_states
    assert "B3" in align.unmatched_b_states
    assert len(align.unmatched_a_states) == 0

    # Assert neutral ADDITIONAL_STATE divergence is recorded for B3
    div_types = {d.divergence_type for d in align.divergences}
    assert DivergenceType.ADDITIONAL_STATE in div_types
    add_div = next(d for d in align.divergences if d.divergence_type == DivergenceType.ADDITIONAL_STATE)
    assert add_div.state_b_id == "B3"
