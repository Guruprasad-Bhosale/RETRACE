"""Integration test verifying synthesized Playwright test structure against Commerce Lab regression."""

from uuid import uuid4

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.reproduction.models import (
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
from apps.worker.synthesis.models import ValidationStatus
from packages.domain.models import ActionType


def test_generated_test_structure_matches_commerce_regression():
    """Verify synthesized test matches the Commerce Lab v1 vs v2 checkout discrepancy."""
    clf = RegressionClassification(
        classification_id="clf_comm_cart_01",
        difference_id="diff_comm_cart_01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.FUNCTIONAL,
        rule_id="RULE-COMMERCE-CART-ADD-DISABLED",
        reason="Add to cart button became disabled.",
        evidence=ClassificationEvidence(
            difference_id="diff_comm_cart_01",
            canonical_subject="button#add-to-cart",
            details={"selector": "#add-to-cart", "text_a": "Add to Cart", "text_b": "Out of Stock"},
        ),
    )

    steps = [
        ReproductionStep(
            step_index=0,
            action_type=ActionType.NAVIGATE,
            value="/",
            raw_target="/",
        ),
        ReproductionStep(
            step_index=1,
            action_type=ActionType.CLICK,
            stable_target_identity="#product-1",
            target_role="link",
            accessible_name="Product 1",
        ),
        ReproductionStep(
            step_index=2,
            action_type=ActionType.CLICK,
            stable_target_identity="#add-to-cart-btn",
            target_role="button",
            accessible_name="Add to Cart",
        ),
    ]

    repro = ReproductionResult(
        reproduction_id="repro_comm_cart_01",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        rule_id=clf.rule_id,
        category=clf.category.value,
        status=ReproductionStatus.REPRODUCED,
        strategy=ReproductionStrategy.DIRECT_REPLAY,
        path=ReproductionPath(
            path_id="path_comm_01",
            trajectory_id=uuid4(),
            classification_id=clf.classification_id,
            difference_id=clf.difference_id,
            seed_url="http://127.0.0.1:3000/",
            steps=steps,
            path_signature="nav->click_prod->click_cart",
        ),
    )

    loc = SourceLocation(
        file_path="lab/applications/commerce/v2/routes/cart.py",
        start_line=25,
        end_line=35,
        symbol_name="add_to_cart",
    )
    attr = RootCauseAttribution(
        attribution_id="attr_comm_cart_01",
        source_location=loc,
        relationship_type=AttributionRelationshipType.DIRECTLY_CHANGED,
        commit=CommitMetadata(commit_hash="c0ffee01", author_name="Commerce Dev", message="Disable inventory"),
        commit_attribution_type=CommitAttributionType.CAUSAL_COMMIT,
        explanation="Inventory logic check broken in cart handler.",
    )
    rc = RootCauseResult(
        root_cause_id="rc_comm_cart_01",
        classification_id=clf.classification_id,
        difference_id=clf.difference_id,
        category=clf.category.value,
        status=RootCauseStatus.LOCATED,
        primary_attribution=attr,
        attributions=[attr],
        provenance=RootCauseProvenance(classification_id=clf.classification_id, difference_id=clf.difference_id),
    )

    engine = TestSynthesisEngine()
    gen_test = engine.synthesize_test(clf, reproduction=repro, root_cause=rc)

    assert gen_test.validation_status == ValidationStatus.STRUCTURALLY_VALIDATED
    assert len(gen_test.steps) == 3
    assert len(gen_test.assertions) >= 1

    source = gen_test.generated_source
    assert "import { test, expect } from '@playwright/test';" in source
    assert "page.getByRole('link', { name: 'Product 1' })" in source
    assert "page.getByRole('button', { name: 'Add to Cart' })" in source
    assert "lab/applications/commerce/v2/routes/cart.py:25-35" in source
    assert "c0ffee01" in source
