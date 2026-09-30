"""Unit Tests for Phase 8 Reproduction Domain Models."""

from uuid import uuid4

from apps.worker.reproduction.models import (
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStep,
    ReproductionStrategy,
    compute_deterministic_reproduction_id,
)
from packages.domain.models import ActionType


def test_reproduction_step_signature():
    """Verify deterministic step signature computation."""
    step = ReproductionStep(
        step_index=1,
        action_type=ActionType.CLICK,
        stable_target_identity='button[data-testid="search"]',
        target_role="button",
        accessible_name="Search",
        value=None,
    )
    sig = step.compute_step_signature()
    assert "step=1" in sig
    assert "type=click" in sig
    assert "target=button[data-testid=\"search\"]" in sig
    assert "role=button" in sig
    assert "name=Search" in sig


def test_deterministic_reproduction_id():
    """Verify compute_deterministic_reproduction_id is stable and timestamp-free."""
    v_a = uuid4()
    v_b = uuid4()
    traj = uuid4()

    id1 = compute_deterministic_reproduction_id(
        classification_id="class-123",
        version_a_id=v_a,
        version_b_id=v_b,
        trajectory_id=traj,
        path_signature="sig-abc",
        strategy=ReproductionStrategy.DIRECT_REPLAY,
    )
    id2 = compute_deterministic_reproduction_id(
        classification_id="class-123",
        version_a_id=v_a,
        version_b_id=v_b,
        trajectory_id=traj,
        path_signature="sig-abc",
        strategy=ReproductionStrategy.DIRECT_REPLAY,
    )
    assert id1 == id2
    assert len(id1) == 16


def test_reproduction_result_deterministic_sort_key():
    """Verify ReproductionResult sorting order by category, status, rule_id, reproduction_id."""
    path = ReproductionPath(
        path_id="p1",
        trajectory_id=uuid4(),
        classification_id="c1",
        difference_id="d1",
        seed_url="http://localhost:3000/",
        path_signature="sig1",
    )
    res1 = ReproductionResult(
        reproduction_id="rep1",
        classification_id="c1",
        difference_id="d1",
        rule_id="FUNC-HTTP-STATUS-ERROR",
        category="FUNCTIONAL",
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=path,
    )
    res2 = ReproductionResult(
        reproduction_id="rep2",
        classification_id="c2",
        difference_id="d2",
        rule_id="NAV-ROUTE-REMOVED",
        category="NAVIGATION",
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=path,
    )

    key1 = res1.deterministic_sort_key()
    key2 = res2.deterministic_sort_key()
    assert key1 < key2  # "FUNCTIONAL" < "NAVIGATION"
