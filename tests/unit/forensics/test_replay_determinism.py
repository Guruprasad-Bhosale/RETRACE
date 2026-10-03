"""Unit tests for InvestigationReplayEngine determinism, snapshot hashing, and offline verification."""

from packages.forensics.engine import ForensicIntelligenceEngine
from packages.forensics.models import compute_graph_hash
from packages.forensics.replay import InvestigationReplayEngine


def test_snapshot_creation_canonical_hash():
    """Verify snapshot creation generates stable canonical hash."""
    from apps.api.routers.v1.investigations import (
        _INVESTIGATION_REGISTRY,
        clear_investigations,
        seed_sample_investigations,
    )

    clear_investigations()
    seed_sample_investigations()
    inv = _INVESTIGATION_REGISTRY["inv_comm_cart_01"]

    snapshot1 = InvestigationReplayEngine.create_snapshot(inv)
    snapshot2 = InvestigationReplayEngine.create_snapshot(inv)

    assert snapshot1.snapshot_hash == snapshot2.snapshot_hash
    assert len(snapshot1.snapshot_hash) == 64
    assert snapshot1.analysis_version == "forensics-v1"


def test_replay_determinism_multi_iteration():
    """Verify repeated offline replay execution produces 100% identical hashes across 10 iterations."""
    from apps.api.routers.v1.investigations import (
        _INVESTIGATION_REGISTRY,
        clear_investigations,
        seed_sample_investigations,
    )

    clear_investigations()
    seed_sample_investigations()
    inv = _INVESTIGATION_REGISTRY["inv_comm_cart_01"]

    baseline = InvestigationReplayEngine.replay_investigation(inv)
    assert baseline.is_reproducible is True
    assert baseline.status == "REPRODUCIBLE"
    assert len(baseline.divergence_details) == 0

    for _ in range(10):
        result = InvestigationReplayEngine.replay_investigation(inv)
        assert result.graph_hash == baseline.graph_hash
        assert result.hypothesis_hash == baseline.hypothesis_hash
        assert result.explanation_hash == baseline.explanation_hash
        assert result.replay_id == baseline.replay_id


def test_unsupported_analysis_version_handling():
    """Verify replay gracefully rejects unknown/unsupported analysis engine versions."""
    from apps.api.routers.v1.investigations import (
        _INVESTIGATION_REGISTRY,
        clear_investigations,
        seed_sample_investigations,
    )

    clear_investigations()
    seed_sample_investigations()
    inv = _INVESTIGATION_REGISTRY["inv_comm_cart_01"]

    result = InvestigationReplayEngine.replay_investigation(inv, analysis_version="forensics-v99.0-unsupported")
    assert result.is_reproducible is False
    assert result.status == "REPLAY NOT AVAILABLE FOR THIS VERSION"
    assert len(result.divergence_details) > 0


def test_graph_hash_stability():
    """Verify graph hash remains strictly identical for identical graph topology."""
    from apps.api.routers.v1.investigations import (
        _INVESTIGATION_REGISTRY,
        clear_investigations,
        seed_sample_investigations,
    )

    clear_investigations()
    seed_sample_investigations()
    inv = _INVESTIGATION_REGISTRY["inv_comm_cart_01"]

    exp1 = ForensicIntelligenceEngine.explain_investigation(inv)
    exp2 = ForensicIntelligenceEngine.explain_investigation(inv)

    hash1 = compute_graph_hash(exp1.evidence_graph)
    hash2 = compute_graph_hash(exp2.evidence_graph)

    assert hash1 == hash2
