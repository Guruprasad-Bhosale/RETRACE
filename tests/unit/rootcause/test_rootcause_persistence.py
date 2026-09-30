"""Unit tests for mapping RootCauseResult to domain entities and SQLAlchemy ORM models."""

from uuid import uuid4

from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitAttributionType,
    CommitMetadata,
    DiffHunk,
    DiffLine,
    LineChangeType,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
)
from apps.worker.rootcause.persistence import RootCausePersistenceMapper
from packages.db.models import RootCauseModel
from packages.domain.models import HypothesisType, RootCause


def test_persistence_mapping_to_domain_and_orm():
    """Verify mapping RootCauseResult to domain RootCause and SQLAlchemy RootCauseModel."""
    finding_id = uuid4()
    session_id = uuid4()

    loc = SourceLocation(
        file_path="app.py",
        symbol_name="calc_tax",
        start_line=10,
        end_line=15,
    )
    commit = CommitMetadata(
        commit_hash="c" * 40,
        author_name="Dev",
        message="update tax",
    )
    hunk = DiffHunk(
        old_start=10,
        old_lines=5,
        new_start=10,
        new_lines=6,
        lines=[DiffLine(change_type=LineChangeType.LINE_ADDED, content="+ tax = 2.0", new_line_number=12)],
        added_lines=[12],
    )

    attr = RootCauseAttribution(
        attribution_id="attr-01",
        source_location=loc,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=commit,
        commit_attribution_type=CommitAttributionType.INTRODUCING_COMMIT,
        diff_hunk=hunk,
        explanation="Tax calculation formula changed",
        evidence=[],
    )

    prov = RootCauseProvenance(
        classification_id="class-01",
        difference_id="diff-01",
    )

    res = RootCauseResult(
        root_cause_id="rc-01",
        classification_id="class-01",
        difference_id="diff-01",
        category="CALCULATION",
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=prov,
    )

    # Convert to domain RootCause
    domain_rc = RootCausePersistenceMapper.to_domain_root_cause(
        result=res,
        finding_id=finding_id,
        session_id=session_id,
    )

    assert domain_rc is not None
    assert isinstance(domain_rc, RootCause)
    assert domain_rc.finding_id == finding_id
    assert domain_rc.session_id == session_id
    assert domain_rc.file_path == "app.py"
    assert domain_rc.line_number == 10
    assert domain_rc.commit_hash == "c" * 40
    assert domain_rc.hypothesis_type == HypothesisType.OBSERVED_FACT

    # Convert to ORM model
    orm_model = RootCausePersistenceMapper.to_orm_root_cause(domain_rc)
    assert isinstance(orm_model, RootCauseModel)
    assert orm_model.id == domain_rc.id
    assert orm_model.file_path == "app.py"
    assert orm_model.line_number == 10
    assert orm_model.commit_hash == "c" * 40
