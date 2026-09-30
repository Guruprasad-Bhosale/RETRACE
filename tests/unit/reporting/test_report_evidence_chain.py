"""Unit tests for report evidence chain construction."""

from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reporting.evidence import EvidenceChainBuilder
from apps.worker.reporting.models import EvidenceNodeType
from apps.worker.reproduction.models import (
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStrategy,
)
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitMetadata,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
)


def test_evidence_chain_unbroken_lineage():
    """Verify unbroken causal chain connects difference through attribution."""
    clf = RegressionClassification(
        classification_id="clf_chain_1",
        difference_id="diff_chain_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.CALCULATION,
        rule_id="RULE-CALC-DISCREPANCY",
        reason="Calculation mismatch.",
        evidence=ClassificationEvidence(difference_id="diff_chain_1"),
    )
    repro = ReproductionResult(
        reproduction_id="repro_chain_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="p1", trajectory_id=uuid4(), classification_id=clf.classification_id,
            difference_id=clf.difference_id, seed_url="http://127.0.0.1/", path_signature="nav",
        ),
    )
    attr = RootCauseAttribution(
        attribution_id="attr_chain_1",
        source_location=SourceLocation(file_path="src/calc.py", start_line=1, end_line=5),
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=CommitMetadata(commit_hash="11223344", author_name="Bob", message="Update math"),
        explanation="Direct math change.",
    )
    rc = RootCauseResult(
        root_cause_id="rc_chain_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        category=clf.category.value,
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=RootCauseProvenance(classification_id=clf.classification_id, difference_id=clf.difference_id),
    )

    chain = EvidenceChainBuilder.build_chain(classification=clf, reproduction=repro, root_cause=rc)

    assert len(chain.nodes) >= 6
    types = [n.node_type for n in chain.nodes]
    assert EvidenceNodeType.OBSERVED_DIFFERENCE in types
    assert EvidenceNodeType.REGRESSION_CLASSIFICATION in types
    assert EvidenceNodeType.REPRODUCTION_REPLAY in types
    assert EvidenceNodeType.ROOT_CAUSE_LOCALIZATION in types
    assert EvidenceNodeType.CHANGED_SOURCE_REGION in types
    assert EvidenceNodeType.COMMIT_ATTRIBUTION in types
