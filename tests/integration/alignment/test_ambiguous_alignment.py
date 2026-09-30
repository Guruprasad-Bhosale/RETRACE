"""Integration test for ambiguous state alignments."""

from uuid import uuid4

from apps.worker.alignment.models import AlignmentRelation
from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.exploration.coverage import CoverageMetrics
from apps.worker.exploration.diagnostics import ExplorationResult


def test_ambiguous_candidates_preserved_without_guessing() -> None:
    aligner = TrajectoryAligner()

    # State A1 has two identical structural candidates B1 and B2 in target version
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
        unique_routes=["/", "/item"],
        termination_reason="max_depth",
        elapsed_time_sec=0.2,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {"state_id": "A0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            {"state_id": "A1", "route": "/item", "depth": 1, "inventory_signature": "count=2", "metadata": {"http_status": 200}},
        ],
        state_graph_edges=[],
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
        unique_routes=["/", "/item"],
        termination_reason="max_depth",
        elapsed_time_sec=0.2,
        coverage=CoverageMetrics(),
        state_graph_nodes=[
            {"state_id": "B0", "route": "/", "depth": 0, "metadata": {"http_status": 200}},
            # Two competing states on same route with identical inventory signatures
            {"state_id": "B1", "route": "/item", "depth": 1, "inventory_signature": "count=2", "metadata": {"http_status": 200}},
            {"state_id": "B2", "route": "/item", "depth": 1, "inventory_signature": "count=2", "metadata": {"http_status": 200}},
        ],
        state_graph_edges=[],
    )

    alignment_res = aligner.align(res_a, res_b)
    align = alignment_res.alignment

    # Assert A0 <-> B0 aligned
    assert any(st.state_a_id == "A0" and st.state_b_id == "B0" for st in align.aligned_states)

    # Assert A1 is preserved in ambiguous_states with candidate set [B1, B2]
    assert len(align.ambiguous_states) == 1
    ambig = align.ambiguous_states[0]
    assert ambig.state_a_id == "A1"
    assert ambig.relation == AlignmentRelation.AMBIGUOUS
    assert "B1" in ambig.evidence.ambiguity_candidates
    assert "B2" in ambig.evidence.ambiguity_candidates
