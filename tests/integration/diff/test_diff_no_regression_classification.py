"""Integration boundary test ensuring Phase 6 Semantic Diff Engine performs zero regression classification."""

import inspect
from uuid import uuid4

import apps.worker.diff.models as diff_models
from apps.worker.alignment.models import (
    AlignmentRelation,
    AlignmentResult,
    MatchEvidence,
    StateAlignment,
    StateObservationalFeatures,
    StateSignature,
    TrajectoryAlignment,
)
from apps.worker.diff.semantic_diff import SemanticDiffEngine


def test_diff_models_contain_no_regression_fields():
    classes_to_check = [
        diff_models.SemanticDifference,
        diff_models.SemanticDiffResult,
        diff_models.SemanticDiffSummary,
        diff_models.DifferenceEvidence,
    ]

    forbidden_field_names = [
        "regression",
        "regressions",
        "is_regression",
        "severity",
        "bug_count",
        "bug_priority",
        "priority",
        "root_cause",
        "root_causes",
        "confidence_score",
        "regression_confidence",
        "bug_confidence",
        "root_cause_confidence",
    ]

    for cls in classes_to_check:
        fields = cls.model_fields.keys()
        for forbidden in forbidden_field_names:
            assert forbidden not in fields, (
                f"Model {cls.__name__} has forbidden field '{forbidden}'"
            )


def test_engine_output_has_no_regression_payload():
    engine = SemanticDiffEngine()

    sig_a = StateSignature(
        state_id="st_1",
        normalized_route="/checkout",
        inventory_signature="inv_a",
        a11y_signature="a11y_a",
        ui_state_signature="ui_a",
        observational=StateObservationalFeatures(http_status=200, console_errors_count=0),
    )
    sig_b = StateSignature(
        state_id="st_2",
        normalized_route="/checkout",
        inventory_signature="inv_b",
        a11y_signature="a11y_b",
        ui_state_signature="ui_b",
        observational=StateObservationalFeatures(http_status=404, console_errors_count=2),
    )

    sa = StateAlignment(
        state_a_id="st_1",
        state_b_id="st_2",
        signature_a=sig_a,
        signature_b=sig_b,
        relation=AlignmentRelation.EXACT_MATCH,
        evidence=MatchEvidence(route_match=True),
    )

    align_res = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(aligned_states=[sa]),
    )

    result = engine.compare(align_res)

    dumped = result.model_dump(mode="json")
    raw_text = str(dumped).lower()

    assert "regression" not in raw_text
    assert "severity" not in raw_text
    assert "root_cause" not in raw_text
    assert "priority" not in raw_text
    assert "bug" not in raw_text


def test_diff_engine_methods_boundary():
    engine = SemanticDiffEngine()
    methods = [m for m, _ in inspect.getmembers(engine, predicate=inspect.ismethod)]
    for method_name in methods:
        assert "regression" not in method_name
        assert "classify" not in method_name
        assert "root_cause" not in method_name
