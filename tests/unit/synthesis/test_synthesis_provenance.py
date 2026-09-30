"""Unit tests for test synthesis provenance lineage."""

from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reproduction.models import (
    ActionType,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStep,
    ReproductionStrategy,
)
from apps.worker.rootcause.models import (
    AttributionRelationshipType,
    CommitAttributionType,
    CommitMetadata,
    RootCauseAttribution,
    RootCauseProvenance,
    RootCauseResult,
    RootCauseStatus,
    SourceLocation,
)
from apps.worker.synthesis.engine import TestSynthesisEngine


def test_test_provenance_full_lineage():
    """Verify test provenance links all upstream artifact and execution IDs."""
    traj_id = uuid4()
    obs_id = uuid4()

    clf = RegressionClassification(
        classification_id="clf_prov_100",
        difference_id="diff_prov_100",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.NAVIGATION,
        rule_id="RULE-NAV-MISMATCH",
        reason="Navigation failed.",
        evidence=ClassificationEvidence(difference_id="diff_prov_100"),
    )

    repro = ReproductionResult(
        reproduction_id="repro_prov_200",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="path_prov_300",
            trajectory_id=traj_id,
            classification_id=clf.classification_id,
            difference_id=clf.difference_id,
            seed_url="http://127.0.0.1:3000/",
            steps=[
                ReproductionStep(
                    step_index=0,
                    action_type=ActionType.NAVIGATE,
                    value="/",
                )
            ],
            observation_ids=[obs_id],
            path_signature="nav",
        ),
    )

    loc = SourceLocation(file_path="src/routes/app.py", start_line=25, end_line=30)
    attr = RootCauseAttribution(
        attribution_id="attr_prov_400",
        source_location=loc,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=CommitMetadata(commit_hash="deadbeef1234", author_name="Coder", message="Fix route"),
        commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
        explanation="Changed route definition",
    )
    rc = RootCauseResult(
        root_cause_id="rc_prov_500",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        category=clf.category.value,
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=RootCauseProvenance(
            classification_id=clf.classification_id,
            difference_id=clf.difference_id,
        ),
    )

    engine = TestSynthesisEngine()
    gen_test = engine.synthesize_test(clf, reproduction=repro, root_cause=rc)

    p = gen_test.provenance
    assert p.classification_id == "clf_prov_100"
    assert p.difference_id == "diff_prov_100"
    assert p.reproduction_id == "repro_prov_200"
    assert p.root_cause_id == "rc_prov_500"
    assert p.trajectory_id == traj_id
    assert obs_id in p.observation_ids
    assert any("src/routes/app.py:25-30" in loc_str for loc_str in p.source_locations)
    assert any("deadbeef" in cmt for cmt in p.commit_hashes)
