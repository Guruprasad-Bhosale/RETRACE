"""Integration test for seed state alignment."""

from uuid import uuid4

from apps.worker.alignment.models import AlignmentRelation
from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.exploration.coverage import CoverageMetrics
from apps.worker.exploration.diagnostics import ExplorationResult


def test_seed_states_align_deterministically() -> None:
    aligner = TrajectoryAligner()

    obs_a = uuid4()
    obs_b = uuid4()

    res_a = ExplorationResult(
        run_id=uuid4(),
        trajectory_id=uuid4(),
        seed_url="http://localhost:3001/",
        total_steps=1,
        states_discovered=1,
        transitions_count=0,
        successful_transitions=0,
        failed_transitions=0,
        skipped_candidates=0,
        unique_routes=["/"],
        termination_reason="max_depth",
        elapsed_time_sec=0.1,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {
                "state_id": "seed-state-hash",
                "observation_id": str(obs_a),
                "url": "http://localhost:3001/",
                "route": "/",
                "depth": 0,
                "inventory_signature": "count=10",
                "a11y_signature": "a11y_hash",
                "ui_state_signature": "title=Store",
                "metadata": {"http_status": 200, "page_title": "Store"},
            }
        ],
        state_graph_edges=[],
    )

    res_b = ExplorationResult(
        run_id=uuid4(),
        trajectory_id=uuid4(),
        seed_url="http://localhost:3002/",
        total_steps=1,
        states_discovered=1,
        transitions_count=0,
        successful_transitions=0,
        failed_transitions=0,
        skipped_candidates=0,
        unique_routes=["/"],
        termination_reason="max_depth",
        elapsed_time_sec=0.1,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {
                "state_id": "seed-state-hash",
                "observation_id": str(obs_b),
                "url": "http://localhost:3002/",
                "route": "/",
                "depth": 0,
                "inventory_signature": "count=10",
                "a11y_signature": "a11y_hash",
                "ui_state_signature": "title=Store",
                "metadata": {"http_status": 200, "page_title": "Store"},
            }
        ],
        state_graph_edges=[],
    )

    alignment_res = aligner.align(res_a, res_b)
    align = alignment_res.alignment

    assert len(align.aligned_states) == 1
    seed_pair = align.aligned_states[0]
    assert seed_pair.state_a_id == "seed-state-hash"
    assert seed_pair.state_b_id == "seed-state-hash"
    assert seed_pair.relation == AlignmentRelation.EXACT_MATCH
    assert seed_pair.observation_a_id == obs_a
    assert seed_pair.observation_b_id == obs_b
