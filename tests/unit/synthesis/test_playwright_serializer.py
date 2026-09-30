"""Unit tests for Playwright TypeScript serializer."""

from apps.worker.synthesis.config import SynthesisConfig
from apps.worker.synthesis.models import (
    AssertionCategory,
    GeneratedTest,
    SelectorStrategy,
    SynthesisStatus,
    TestAssertion,
    TestFramework,
    TestLanguage,
    TestProvenance,
    TestStep,
    ValidationStatus,
)
from apps.worker.synthesis.playwright import PlaywrightTypeScriptSerializer
from packages.domain.models import ActionType


def test_serialize_playwright_typescript_structure():
    """Verify clean structure and imports of serialized Playwright TypeScript script."""
    steps = [
        TestStep(
            step_index=0,
            action_type=ActionType.NAVIGATE,
            raw_target="/cart",
            resolved_selector="page.goto(`${BASE_URL}/cart`)",
            selector_strategy=SelectorStrategy.ACTION_LOCATOR,
            description="Navigate to /cart",
        ),
        TestStep(
            step_index=1,
            action_type=ActionType.CLICK,
            raw_target="#checkout-btn",
            resolved_selector="page.locator('#checkout-btn')",
            selector_strategy=SelectorStrategy.STABLE_ID,
            description="Click checkout button",
        ),
    ]
    assertions = [
        TestAssertion(
            assertion_id="ast_1",
            category=AssertionCategory.NAVIGATION,
            assertion_type="toHaveURL",
            subject="page",
            expected_value="**/checkout",
            evidence_id="diff_123",
            reasoning="Expected navigation to checkout.",
        )
    ]
    prov = TestProvenance(
        classification_id="clf_123",
        difference_id="diff_123",
        source_locations=["src/cart.ts:10-20"],
        commit_hashes=["abcdef12"],
    )
    test_model = GeneratedTest(
        test_id="test_cart_001",
        regression_id="clf_123",
        framework=TestFramework.PLAYWRIGHT,
        language=TestLanguage.TYPESCRIPT,
        title="Checkout Navigation Regression",
        description="Verifies checkout button navigates properly",
        steps=steps,
        assertions=assertions,
        provenance=prov,
        status=SynthesisStatus.SYNTHESIZED,
        validation_status=ValidationStatus.NOT_VALIDATED,
        generated_source="",
    )

    serializer = PlaywrightTypeScriptSerializer(config=SynthesisConfig())
    source = serializer.serialize(test_model)

    assert "import { test, expect } from '@playwright/test';" in source
    assert "process.env.RETRACE_TARGET_URL" in source
    assert "test.describe('Checkout Navigation Regression'" in source
    assert "await page.goto(`${BASE_URL}/cart`);" in source
    assert "await page.locator('#checkout-btn').click();" in source
    assert "await expect(page).toHaveURL(new RegExp('/checkout'));" in source
    assert "src/cart.ts:10-20" in source
    assert "abcdef12" in source
