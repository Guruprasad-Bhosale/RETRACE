"""Unit tests for Performance Timing Semantic Differ."""

from uuid import uuid4

from apps.worker.alignment.models import (
    ActionAlignment,
    ActionSignature,
    AlignmentRelation,
    AlignmentResult,
    MatchEvidence,
    TrajectoryAlignment,
    TransitionAlignment,
)
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import DifferenceCategory, DifferenceKind
from apps.worker.diff.performance_diff import PerformanceDiffer
from packages.domain.models import ActionType


def test_performance_timing_diff_above_threshold():
    cfg = DiffConfig(timing_min_observable_delta_ms=100.0)
    differ = PerformanceDiffer(cfg)

    sig_a = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn:search",
        semantic_attributes={"duration_ms": "250.0"},
    )
    sig_b = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn:search",
        semantic_attributes={"duration_ms": "850.0"},
    )

    act_align = ActionAlignment(
        action_a_id="act_1",
        action_b_id="act_2",
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(action_match=True),
    )

    ta = TransitionAlignment(
        transition_a_id="t1",
        transition_b_id="t2",
        action_alignment=act_align,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(action_match=True),
    )

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(aligned_transitions=[ta]),
    )

    diffs = differ.diff(align_res)
    assert len(diffs) == 1
    diff = diffs[0]
    assert diff.category == DifferenceCategory.PERFORMANCE
    assert diff.kind == DifferenceKind.NAVIGATION_DURATION_CHANGED
    assert diff.evidence[0].before_value == "250.0 ms"
    assert diff.evidence[0].after_value == "850.0 ms"
    assert diff.evidence[0].details["delta_ms"] == 600.0


def test_performance_timing_diff_below_threshold_ignored():
    cfg = DiffConfig(timing_min_observable_delta_ms=100.0)
    differ = PerformanceDiffer(cfg)

    sig_a = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn:search",
        semantic_attributes={"duration_ms": "250.0"},
    )
    sig_b = ActionSignature(
        action_type=ActionType.CLICK,
        stable_target_identity="btn:search",
        semantic_attributes={"duration_ms": "290.0"},  # 40ms delta < 100ms threshold
    )

    act_align = ActionAlignment(
        action_a_id="act_1",
        action_b_id="act_2",
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(action_match=True),
    )

    ta = TransitionAlignment(
        transition_a_id="t1",
        transition_b_id="t2",
        action_alignment=act_align,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(action_match=True),
    )

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(aligned_transitions=[ta]),
    )

    diffs = differ.diff(align_res)
    assert len(diffs) == 0
