"""Unit tests for Accessibility Semantic Differ."""

from uuid import uuid4

from apps.worker.alignment.models import (
    AlignmentRelation,
    AlignmentResult,
    MatchEvidence,
    StateAlignment,
    StateObservationalFeatures,
    StateSignature,
    TrajectoryAlignment,
)
from apps.worker.diff.accessibility_diff import AccessibilityDiffer
from apps.worker.diff.models import DifferenceCategory, DifferenceKind


def test_a11y_structure_changed():
    differ = AccessibilityDiffer()

    sig_a = StateSignature(
        state_id="st_1",
        normalized_route="/settings",
        inventory_signature="i1",
        a11y_signature="hash_a11y_v1",
        ui_state_signature="u1",
        observational=StateObservationalFeatures(),
    )
    sig_b = StateSignature(
        state_id="st_2",
        normalized_route="/settings",
        inventory_signature="i1",
        a11y_signature="hash_a11y_v2",
        ui_state_signature="u1",
        observational=StateObservationalFeatures(),
    )

    sa = StateAlignment(
        state_a_id="st_1",
        state_b_id="st_2",
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.STRONG_MATCH,
        evidence=MatchEvidence(route_match=True),
    )

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(aligned_states=[sa]),
    )

    diffs = differ.diff(align_res)
    assert len(diffs) == 1
    diff = diffs[0]
    assert diff.category == DifferenceCategory.ACCESSIBILITY
    assert diff.kind == DifferenceKind.A11Y_STRUCTURE_CHANGED
    assert diff.evidence[0].before_value == "hash_a11y_v1"
    assert diff.evidence[0].after_value == "hash_a11y_v2"
