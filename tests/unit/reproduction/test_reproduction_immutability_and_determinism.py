"""Unit Tests for Reproduction Immutability and Planning Determinism."""

import copy
from uuid import uuid4

from apps.worker.exploration.state import ExplorationGraph, ExplorationState
from apps.worker.exploration.transition import ExplorationTransition
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reproduction.models import (
    ReproductionStrategy,
    compute_deterministic_reproduction_id,
)
from apps.worker.reproduction.planner import ReproductionPathPlanner
from packages.domain.models import ActionType


def test_input_immutability():
    """Verify ReproductionPathPlanner does not mutate input RegressionClassificationResult."""
    graph = ExplorationGraph()
    state = ExplorationState(
        state_id="state-seed",
        observation_id=uuid4(),
        url="http://localhost:3000/",
        route="/",
    )
    graph.add_state(state)

    classification = RegressionClassification(
        classification_id="class-immutable",
        difference_id="diff-immutable",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="FUNC-HTTP-STATUS-ERROR",
        reason="Immutability check",
        evidence=ClassificationEvidence(difference_id="diff-immutable", state_a_id="state-seed"),
    )

    original_classification = copy.deepcopy(classification)

    ReproductionPathPlanner.plan_path_from_graph(
        classification=classification,
        graph=graph,
        seed_url="http://localhost:3000/",
        trajectory_id=uuid4(),
    )

    assert classification == original_classification


def test_planning_determinism():
    """Verify running path planner multiple times produces identical paths and reproduction IDs."""
    graph = ExplorationGraph()
    obs_0 = uuid4()
    obs_1 = uuid4()
    state_0 = ExplorationState(state_id="s0", observation_id=obs_0, url="http://localhost:3000/", route="/")
    state_1 = ExplorationState(state_id="s1", observation_id=obs_1, url="http://localhost:3000/cart", route="/cart", parent_state_id="s0", incoming_transition_id="t1")
    trans = ExplorationTransition(
        transition_id="t1",
        from_state_id="s0",
        to_state_id="s1",
        action_id=uuid4(),
        action_type=ActionType.CLICK,
        target="#add",
        target_identity="btn-add",
        observation_id=obs_1,
        success=True,
    )

    graph.add_state(state_0)
    graph.add_state(state_1)
    graph.record_transition(trans)

    classification = RegressionClassification(
        classification_id="class-det",
        difference_id="diff-det",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="FUNC-HTTP-STATUS-ERROR",
        reason="Determinism test",
        evidence=ClassificationEvidence(difference_id="diff-det", state_a_id="s1", transition_a_id="t1"),
    )

    traj_id = uuid4()
    v_a = uuid4()
    v_b = uuid4()

    path_1 = ReproductionPathPlanner.plan_path_from_graph(
        classification=classification,
        graph=graph,
        seed_url="http://localhost:3000/",
        trajectory_id=traj_id,
    )
    path_2 = ReproductionPathPlanner.plan_path_from_graph(
        classification=classification,
        graph=graph,
        seed_url="http://localhost:3000/",
        trajectory_id=traj_id,
    )

    assert path_1.path_signature == path_2.path_signature
    assert path_1.path_id == path_2.path_id

    id1 = compute_deterministic_reproduction_id(
        classification.classification_id, v_a, v_b, traj_id, path_1.path_signature, ReproductionStrategy.DIRECT_REPLAY
    )
    id2 = compute_deterministic_reproduction_id(
        classification.classification_id, v_a, v_b, traj_id, path_2.path_signature, ReproductionStrategy.DIRECT_REPLAY
    )
    assert id1 == id2
