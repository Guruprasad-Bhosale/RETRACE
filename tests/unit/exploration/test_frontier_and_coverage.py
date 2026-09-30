"""Unit tests for exploration frontier queue and coverage tracker."""

from uuid import uuid4

from apps.worker.exploration.candidate import CandidateAction
from apps.worker.exploration.coverage import CoverageTracker
from apps.worker.exploration.frontier import ExplorationFrontier, FrontierItem
from packages.domain.models import ActionType


def test_exploration_frontier_fifo_ordering():
    frontier = ExplorationFrontier()

    c1 = CandidateAction(
        candidate_id="c1",
        action_type=ActionType.CLICK,
        target="btn1",
        stable_element_id="id:btn1",
        source_state_id="s0",
        source_observation_id=uuid4(),
        document_order=0,
    )
    c2 = CandidateAction(
        candidate_id="c2",
        action_type=ActionType.CLICK,
        target="btn2",
        stable_element_id="id:btn2",
        source_state_id="s0",
        source_observation_id=uuid4(),
        document_order=1,
    )

    frontier.push(FrontierItem(from_state_id="s0", candidate=c1, depth=1), "t1")
    frontier.push(FrontierItem(from_state_id="s0", candidate=c2, depth=1), "t2")

    # Duplicate push should be ignored
    assert frontier.push(FrontierItem(from_state_id="s0", candidate=c1, depth=1), "t1") is False

    assert frontier.size() == 2
    item1 = frontier.pop()
    assert item1.candidate.candidate_id == "c1"
    item2 = frontier.pop()
    assert item2.candidate.candidate_id == "c2"
    assert frontier.is_empty() is True


def test_coverage_tracker_metrics():
    tracker = CoverageTracker()
    tracker.record_transition("btn:checkout", success=True, depth=1)
    tracker.record_transition("btn:checkout", success=True, depth=2, is_repeated_state=True)
    tracker.record_transition("inp:search", success=False, depth=2)
    tracker.record_skipped_candidate()

    metrics = tracker.build_metrics(unique_states_count=3, routes=["/", "/cart.html"])
    assert metrics.unique_states_count == 3
    assert metrics.unique_routes_count == 2
    assert metrics.transitions_attempted == 3
    assert metrics.transitions_successful == 2
    assert metrics.transitions_failed == 1
    assert metrics.candidates_skipped == 1
    assert metrics.repeated_state_visits == 1
    assert metrics.max_depth_reached == 2
