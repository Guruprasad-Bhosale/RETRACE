"""Unit tests for forensic investigation comparison and graph diff detection."""

from packages.forensics.replay import InvestigationReplayEngine


def test_compare_identical_investigations():
    """Verify comparing an investigation against itself results in zero graph diffs and matching root cause."""
    from apps.api.routers.v1.investigations import (
        _INVESTIGATION_REGISTRY,
        clear_investigations,
        seed_sample_investigations,
    )

    clear_investigations()
    seed_sample_investigations()
    inv = _INVESTIGATION_REGISTRY["inv_comm_cart_01"]

    comparison = InvestigationReplayEngine.compare_investigations(inv, inv)
    assert comparison.investigation_a_id == "inv_comm_cart_01"
    assert comparison.investigation_b_id == "inv_comm_cart_01"
    assert comparison.root_cause_matches is True
    assert comparison.hypothesis_matches is True
    assert comparison.unique_evidence_a_count == 0
    assert comparison.unique_evidence_b_count == 0
    assert len(comparison.graph_diff) == 0


def test_compare_distinct_investigations():
    """Verify comparing different investigations surfaces root cause divergence and graph diffs."""
    from apps.api.routers.v1.investigations import (
        _INVESTIGATION_REGISTRY,
        clear_investigations,
        seed_sample_investigations,
    )

    clear_investigations()
    seed_sample_investigations()
    inv_cart = _INVESTIGATION_REGISTRY["inv_comm_cart_01"]
    inv_modal = _INVESTIGATION_REGISTRY["inv_comm_modal_02"]

    comparison = InvestigationReplayEngine.compare_investigations(inv_cart, inv_modal)
    assert comparison.root_cause_matches is False
    assert len(comparison.graph_diff) > 0

    diff_types = [item.diff_type for item in comparison.graph_diff]
    assert "CHANGED_ROOT_CAUSE" in diff_types or "CHANGED_STATE" in diff_types or "ADDED_NODE" in diff_types
