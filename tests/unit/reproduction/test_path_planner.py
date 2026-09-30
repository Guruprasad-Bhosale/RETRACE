"""Unit Tests for Reproduction Path Planner."""

from uuid import uuid4

from apps.worker.exploration.state import ExplorationGraph, ExplorationState
from apps.worker.exploration.transition import ExplorationTransition
from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reproduction.planner import ReproductionPathPlanner
from packages.domain.models import Action, ActionType


def test_plan_path_from_graph():
    """Verify minimal causal path planning using ExplorationGraph parent pointers."""
    graph = ExplorationGraph()

    obs_0 = uuid4()
    obs_1 = uuid4()
    obs_2 = uuid4()

    state_0 = ExplorationState(
        state_id="state-seed",
        observation_id=obs_0,
        url="http://localhost:3000/",
        route="/",
    )
    state_1 = ExplorationState(
        state_id="state-cart",
        observation_id=obs_1,
        url="http://localhost:3000/cart",
        route="/cart",
        parent_state_id="state-seed",
        incoming_transition_id="trans-1",
    )
    state_2 = ExplorationState(
        state_id="state-checkout",
        observation_id=obs_2,
        url="http://localhost:3000/checkout",
        route="/checkout",
        parent_state_id="state-cart",
        incoming_transition_id="trans-2",
    )

    trans_1 = ExplorationTransition(
        transition_id="trans-1",
        from_state_id="state-seed",
        to_state_id="state-cart",
        action_id=uuid4(),
        action_type=ActionType.CLICK,
        target='button[data-testid="add-cart"]',
        target_identity="btn-add-cart",
        observation_id=obs_1,
        success=True,
    )
    trans_2 = ExplorationTransition(
        transition_id="trans-2",
        from_state_id="state-cart",
        to_state_id="state-checkout",
        action_id=uuid4(),
        action_type=ActionType.CLICK,
        target='button[data-testid="checkout"]',
        target_identity="btn-checkout",
        observation_id=obs_2,
        success=True,
    )

    graph.add_state(state_0)
    graph.add_state(state_1)
    graph.add_state(state_2)
    graph.record_transition(trans_1)
    graph.record_transition(trans_2)

    classification = RegressionClassification(
        classification_id="class-checkout-404",
        difference_id="diff-404",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="FUNC-HTTP-STATUS-ERROR",
        reason="HTTP 404 observed on checkout",
        evidence=ClassificationEvidence(
            difference_id="diff-404",
            state_a_id="state-checkout",
            transition_a_id="trans-2",
        ),
    )

    traj_id = uuid4()
    path = ReproductionPathPlanner.plan_path_from_graph(
        classification=classification,
        graph=graph,
        seed_url="http://localhost:3000/",
        trajectory_id=traj_id,
    )

    assert path.trajectory_id == traj_id
    assert len(path.steps) == 2
    assert path.steps[0].step_index == 1
    assert path.steps[0].stable_target_identity == "btn-add-cart"
    assert path.steps[1].step_index == 2
    assert path.steps[1].stable_target_identity == "btn-checkout"
    assert path.steps[1].expected_to_state_id == "state-checkout"


def test_plan_path_from_actions():
    """Verify causal path planning from ordered list of Action objects."""
    traj_id = uuid4()
    sess_id = uuid4()
    v_id = uuid4()

    actions = [
        Action(
            session_id=sess_id,
            version_id=v_id,
            trajectory_id=traj_id,
            step_index=0,
            action_type=ActionType.CLICK,
            selector='button[data-testid="search"]',
            metadata={"role": "button", "name": "Search"},
        ),
        Action(
            session_id=sess_id,
            version_id=v_id,
            trajectory_id=traj_id,
            step_index=1,
            action_type=ActionType.TYPE,
            selector='input[name="query"]',
            value="laptop",
            metadata={"role": "textbox", "name": "Query"},
        ),
    ]

    classification = RegressionClassification(
        classification_id="class-search-perf",
        difference_id="diff-perf",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.PERFORMANCE,
        rule_id="PERF-NAVIGATION-SLOWDOWN",
        reason="Slowdown during search",
        evidence=ClassificationEvidence(difference_id="diff-perf"),
    )

    path = ReproductionPathPlanner.plan_path_from_actions(
        classification=classification,
        actions=actions,
        seed_url="http://localhost:3000/",
        trajectory_id=traj_id,
    )

    assert len(path.steps) == 2
    assert path.steps[0].step_index == 1
    assert path.steps[0].action_type == ActionType.CLICK
    assert path.steps[1].step_index == 2
    assert path.steps[1].action_type == ActionType.TYPE
    assert path.steps[1].value == "laptop"
