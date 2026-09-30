"""Unit tests for root-cause domain models, extra field rejection, and deterministic IDs."""

import pytest
from pydantic import ValidationError

from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitMetadata,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
    compute_deterministic_attribution_id,
    compute_deterministic_root_cause_id,
)


def test_deterministic_id_computation():
    """Verify deterministic hash IDs are consistent and exclude timestamps."""
    attr_id_1 = compute_deterministic_attribution_id(
        classification_id="class-01",
        file_path="app.py",
        start_line=10,
        end_line=20,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
    )
    attr_id_2 = compute_deterministic_attribution_id(
        classification_id="class-01",
        file_path="app.py",
        start_line=10,
        end_line=20,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
    )
    assert attr_id_1 == attr_id_2
    assert len(attr_id_1) == 16

    rc_id_1 = compute_deterministic_root_cause_id(
        classification_id="class-01",
        difference_id="diff-01",
        status=RootCauseStatus.LOCATED,
        primary_location_key="app.py:10-20:func",
    )
    rc_id_2 = compute_deterministic_root_cause_id(
        classification_id="class-01",
        difference_id="diff-01",
        status=RootCauseStatus.LOCATED,
        primary_location_key="app.py:10-20:func",
    )
    assert rc_id_1 == rc_id_2
    assert len(rc_id_1) == 16


def test_models_extra_forbid():
    """Verify that models forbid extraneous arbitrary fields."""
    with pytest.raises(ValidationError):
        SourceLocation(
            file_path="test.py",
            start_line=1,
            end_line=10,
            non_existent_field="bad",
        )

    with pytest.raises(ValidationError):
        CommitMetadata(
            commit_hash="abc",
            unexpected_field=123,
        )


def test_root_cause_result_deterministic_sort():
    """Verify stable sorting key excludes timestamps."""
    prov = RootCauseProvenance(
        classification_id="c1",
        difference_id="d1",
    )
    r1 = RootCauseResult(
        root_cause_id="rc-b",
        classification_id="c1",
        difference_id="d1",
        category="NAVIGATION",
        status=RootCauseStatus.LOCATED,
        provenance=prov,
    )
    r2 = RootCauseResult(
        root_cause_id="rc-a",
        classification_id="c2",
        difference_id="d2",
        category="API_CONTRACT",
        status=RootCauseStatus.LOCATED,
        provenance=prov,
    )

    sorted_results = sorted([r1, r2], key=lambda r: r.deterministic_sort_key())
    assert sorted_results[0].category == "API_CONTRACT"
    assert sorted_results[1].category == "NAVIGATION"
