"""Integration test for route and observational HTTP status divergences."""

from uuid import uuid4

from apps.worker.alignment.models import DivergenceType
from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.exploration.coverage import CoverageMetrics
from apps.worker.exploration.diagnostics import ExplorationResult


def test_checkout_http_status_divergence() -> None:
    """Version A: /checkout -> HTTP 200
    Version B: /checkout -> HTTP 404

    Expected:
    - State matches (aligned by route and incoming transition)
    - Generates HTTP_STATUS_DIVERGENCE, NOT an unmatched state!
    """
    aligner = TrajectoryAligner()

    obs_a = uuid4()
    obs_b = uuid4()

    res_a = ExplorationResult(
        run_id=uuid4(),
        trajectory_id=uuid4(),
        seed_url="http://localhost:3001/",
        total_steps=2,
        states_discovered=2,
        transitions_count=1,
        successful_transitions=1,
        failed_transitions=0,
        skipped_candidates=0,
        unique_routes=["/", "/checkout"],
        termination_reason="max_depth",
        elapsed_time_sec=0.3,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {"state_id": "s0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {
                "state_id": "s_checkout_a",
                "observation_id": str(obs_a),
                "route": "/checkout",
                "depth": 1,
                "metadata": {"http_status": 200, "page_title": "Checkout"},
            },
        ],
        state_graph_edges=[
            {
                "transition_id": "t_chk_a",
                "from_state_id": "s0",
                "to_state_id": "s_checkout_a",
                "action_type": "CLICK",
                "target_element_id": "btn_checkout",
                "metadata": {"tag": "button", "accessible_name": "Checkout"},
            }
        ],
    )

    res_b = ExplorationResult(
        run_id=uuid4(),
        trajectory_id=uuid4(),
        seed_url="http://localhost:3002/",
        total_steps=2,
        states_discovered=2,
        transitions_count=1,
        successful_transitions=1,
        failed_transitions=0,
        skipped_candidates=0,
        unique_routes=["/", "/checkout"],
        termination_reason="max_depth",
        elapsed_time_sec=0.3,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {"state_id": "s0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {
                "state_id": "s_checkout_b",
                "observation_id": str(obs_b),
                "route": "/checkout",
                "depth": 1,
                "metadata": {"http_status": 404, "page_title": "Not Found"},
            },
        ],
        state_graph_edges=[
            {
                "transition_id": "t_chk_b",
                "from_state_id": "s0",
                "to_state_id": "s_checkout_b",
                "action_type": "CLICK",
                "target_element_id": "btn_checkout",
                "metadata": {"tag": "button", "accessible_name": "Checkout"},
            }
        ],
    )

    alignment_res = aligner.align(res_a, res_b)
    align = alignment_res.alignment

    # Assert state alignment survived
    matched_pairs = {(st.state_a_id, st.state_b_id) for st in align.aligned_states}
    assert ("s_checkout_a", "s_checkout_b") in matched_pairs

    # Assert HTTP_STATUS_DIVERGENCE recorded
    http_divs = [d for d in align.divergences if d.divergence_type == DivergenceType.HTTP_STATUS_DIVERGENCE]
    assert len(http_divs) == 1
    assert http_divs[0].details["status_a"] == 200
    assert http_divs[0].details["status_b"] == 404
    assert http_divs[0].observation_a_id == obs_a
    assert http_divs[0].observation_b_id == obs_b
