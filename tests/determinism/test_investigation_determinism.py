"""Determinism & Replay Stability Tests for Investigation Subsystems.

Verifies that 5x repeated executions of semantic diffing,
classification, root cause attribution, and test synthesis produce identical
structural outputs regardless of dictionary ordering or runtime jitter.
"""

from uuid import uuid4

import pytest

from apps.worker.alignment.models import AlignmentResult, TrajectoryAlignment
from apps.worker.diff.engine import SemanticDiffEngine
from apps.worker.diff.models import (
    DifferenceCategory,
    DifferenceKind,
    SemanticDifference,
    SemanticDiffResult,
)
from apps.worker.investigation.assembler import InvestigationAssembler
from apps.worker.regression.classifier import RegressionClassifier
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
from packages.storage.local import LocalDiskArtifactStorage


def test_semantic_diff_engine_determinism_5x():
    """Verify SemanticDiffEngine produces identical differences on 5 successive runs."""
    diff_engine = SemanticDiffEngine()
    alignment = AlignmentResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        alignment=TrajectoryAlignment(),
    )

    outputs = []
    for _ in range(5):
        diff_res = diff_engine.compare(alignment)
        outputs.append([d.category for d in diff_res.differences])

    # All 5 runs must produce identical difference lists
    first = outputs[0]
    for idx, out in enumerate(outputs[1:], start=2):
        assert out == first, f"Semantic diff diverged on run {idx}"


def test_classification_engine_determinism_5x():
    """Verify RegressionClassifier produces identical classification on 5 successive runs."""
    classifier = RegressionClassifier()
    diff = SemanticDifference(
        diff_id="diff_det_1",
        category=DifferenceCategory.NETWORK,
        kind=DifferenceKind.NETWORK_STATUS_CHANGED,
        canonical_subject="POST /api/checkout",
        description="Checkout submission failed with 500 status",
        evidence=[],
    )
    diff_result = SemanticDiffResult(
        run_a_id=uuid4(),
        run_b_id=uuid4(),
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        differences=[diff],
    )

    results = []
    for _ in range(5):
        clf_result = classifier.classify(diff_result)
        results.append([c.status for c in clf_result.classifications])

    first = results[0]
    for idx, res in enumerate(results[1:], start=2):
        assert res == first, f"Classification diverged on run {idx}: {res} vs {first}"


@pytest.mark.asyncio
async def test_investigation_assembly_and_test_synthesis_determinism_5x(tmp_path):
    """Verify InvestigationAssembler synthesizes structurally identical test code across 5 runs."""
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "det_artifacts")
    assembler = InvestigationAssembler(storage=storage)

    analysis_id = uuid4()
    clf = RegressionClassification(
        classification_id="clf_det_1",
        difference_id="diff_det_1",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-CHECKOUT-FAIL",
        reason="Checkout button unresponsive",
        evidence=ClassificationEvidence(difference_id="diff_det_1"),
    )
    repro = ReproductionResult(
        reproduction_id="repro_det_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="p1",
            trajectory_id=uuid4(),
            classification_id=clf.classification_id,
            difference_id=clf.difference_id,
            seed_url="http://127.0.0.1:3000/",
            steps=[
                ReproductionStep(
                    step_index=0,
                    action_type=ActionType.CLICK,
                    stable_target_identity="#checkout-btn",
                )
            ],
            path_signature="click_checkout",
        ),
    )
    attr = RootCauseAttribution(
        attribution_id="attr_det_1",
        source_location=SourceLocation(file_path="src/checkout.ts", start_line=10, end_line=20),
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=CommitMetadata(commit_hash="deadbeef123", author_name="Dev", message="refactor checkout"),
        commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
        explanation="Direct change to checkout handler",
    )
    rc = RootCauseResult(
        root_cause_id="rc_det_1",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        category=clf.category.value,
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=RootCauseProvenance(classification_id=clf.classification_id, difference_id=clf.difference_id),
    )

    synthesized_specs = []
    for _ in range(5):
        inv = await assembler.assemble_investigation(
            analysis_id=analysis_id,
            classification=clf,
            reproduction=repro,
            root_cause=rc,
        )
        assert inv.generated_test is not None
        synthesized_specs.append(inv.generated_test.generated_source)

    first_spec = synthesized_specs[0]
    for idx, spec in enumerate(synthesized_specs[1:], start=2):
        assert spec == first_spec, f"Synthesized Playwright test code diverged on run {idx}"
