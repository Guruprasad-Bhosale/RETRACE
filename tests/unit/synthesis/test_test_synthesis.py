"""Unit tests for Test Synthesis Engine and Domain Models."""

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
from apps.worker.synthesis.models import (
    GeneratedTest,
    SynthesisStatus,
    TestFramework,
    TestLanguage,
    ValidationStatus,
)


def _make_sample_classification() -> RegressionClassification:
    return RegressionClassification(
        classification_id="clf_cart_btn_1234",
        difference_id="diff_cart_btn_9999",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-DOM-BUTTON-DISABLED",
        reason="Add to cart button became disabled following item selection.",
        evidence=ClassificationEvidence(
            difference_id="diff_cart_btn_9999",
            canonical_subject="button#add-to-cart",
            details={"selector": "#add-to-cart", "text_a": "Add to Cart", "text_b": "Out of Stock"},
        ),
    )


def _make_sample_reproduction(clf: RegressionClassification) -> ReproductionResult:
    steps = [
        ReproductionStep(
            step_index=0,
            action_type=ActionType.NAVIGATE,
            raw_target="/products/1",
            value="/products/1",
        ),
        ReproductionStep(
            step_index=1,
            action_type=ActionType.CLICK,
            stable_target_identity="#add-to-cart",
            target_role="button",
            accessible_name="Add to Cart",
        ),
    ]
    path = ReproductionPath(
        path_id="path_repro_123",
        trajectory_id=uuid4(),
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        seed_url="http://127.0.0.1:3000/products/1",
        steps=steps,
        path_signature="nav->click_btn",
    )
    return ReproductionResult(
        reproduction_id="repro_cart_555",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=path,
    )


def _make_sample_root_cause(clf: RegressionClassification) -> RootCauseResult:
    loc = SourceLocation(
        file_path="src/components/CartButton.tsx",
        start_line=45,
        end_line=50,
        symbol_name="CartButton",
    )
    commit = CommitMetadata(
        commit_hash="c0ffee1234567890",
        author_name="Dev User",
        author_email="dev@example.com",
        message="Update stock checking logic",
    )
    attr = RootCauseAttribution(
        attribution_id="attr_cart_001",
        source_location=loc,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=commit,
        commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
        explanation="Inventory check flag inverted in CartButton.",
    )
    prov = RootCauseProvenance(
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        reproduction_id="repro_cart_555",
    )
    return RootCauseResult(
        root_cause_id="rc_cart_777",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        reproduction_id="repro_cart_555",
        category=clf.category.value,
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=prov,
    )


def test_synthesize_single_test_success():
    """Verify synthesis of a complete, structurally validated Playwright test."""
    clf = _make_sample_classification()
    repro = _make_sample_reproduction(clf)
    rc = _make_sample_root_cause(clf)

    engine = TestSynthesisEngine()
    gen_test: GeneratedTest = engine.synthesize_test(
        classification=clf,
        reproduction=repro,
        root_cause=rc,
    )

    assert gen_test.test_id is not None
    assert gen_test.regression_id == clf.classification_id
    assert gen_test.reproduction_id == repro.reproduction_id
    assert gen_test.root_cause_id == rc.root_cause_id
    assert gen_test.framework == TestFramework.PLAYWRIGHT
    assert gen_test.language == TestLanguage.TYPESCRIPT
    assert gen_test.status == SynthesisStatus.SYNTHESIZED
    assert gen_test.validation_status == ValidationStatus.STRUCTURALLY_VALIDATED
    assert len(gen_test.steps) == 2
    assert len(gen_test.assertions) >= 1
    assert "import { test, expect } from '@playwright/test';" in gen_test.generated_source
    assert "getByRole('button', { name: 'Add to Cart' })" in gen_test.generated_source


def test_synthesize_suite_success():
    """Verify multi-test suite synthesis."""
    clf = _make_sample_classification()
    repro = _make_sample_reproduction(clf)
    rc = _make_sample_root_cause(clf)

    engine = TestSynthesisEngine()
    run_a = uuid4()
    run_b = uuid4()

    from apps.worker.reproduction.models import ReproductionSuiteResult, ReproductionSummary
    from apps.worker.rootcause.models import RootCauseSuiteResult, RootCauseSummary

    repro_suite = ReproductionSuiteResult(
        run_a_id=run_a,
        run_b_id=run_b,
        trajectory_a_id=uuid4(),
        trajectory_b_id=uuid4(),
        results=[repro],
        summary=ReproductionSummary(reproduced=1),
    )
    rc_suite = RootCauseSuiteResult(
        run_a_id=run_a,
        run_b_id=run_b,
        results=[rc],
        summary=RootCauseSummary(located_count=1),
    )

    suite_result = engine.synthesize_suite(
        classifications=[clf],
        run_a_id=run_a,
        run_b_id=run_b,
        reproduction_suite=repro_suite,
        root_cause_suite=rc_suite,
    )

    assert suite_result.run_a_id == run_a
    assert suite_result.run_b_id == run_b
    assert suite_result.summary.total_regressions_analyzed == 1
    assert suite_result.summary.synthesized_count == 1
    assert suite_result.summary.structurally_validated_count == 1
    assert len(suite_result.tests) == 1
