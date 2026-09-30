"""Unit tests for generated test structural validator."""

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
from apps.worker.synthesis.validator import GeneratedTestValidator
from packages.domain.models import ActionType


def test_validator_detects_clean_valid_test():
    """Verify clean valid test passes structural validation."""
    prov = TestProvenance(classification_id="clf_val_1", difference_id="diff_val_1")
    steps = [
        TestStep(
            step_index=0,
            action_type=ActionType.CLICK,
            resolved_selector="page.locator('#btn')",
            selector_strategy=SelectorStrategy.STABLE_ID,
        )
    ]
    assertions = [
        TestAssertion(
            assertion_id="ast_1",
            category=AssertionCategory.UI_STATE,
            assertion_type="toBeVisible",
            subject="page.locator('#btn')",
            expected_value="visible",
            evidence_id="diff_val_1",
            reasoning="Valid UI state.",
        )
    ]
    test_model = GeneratedTest(
        test_id="test_val_1",
        regression_id="clf_val_1",
        framework=TestFramework.PLAYWRIGHT,
        language=TestLanguage.TYPESCRIPT,
        title="Valid Test",
        description="Clean test",
        steps=steps,
        assertions=assertions,
        provenance=prov,
        status=SynthesisStatus.SYNTHESIZED,
        generated_source="import { test, expect } from '@playwright/test'; test('sample', async ({ page }) => { await page.locator('#btn').click(); });",
    )
    status, notes = GeneratedTestValidator.validate(test_model)
    assert status == ValidationStatus.STRUCTURALLY_VALIDATED
    assert len(notes) >= 1


def test_validator_rejects_unbalanced_delimiters():
    """Verify validator flags syntax issues like unclosed braces."""
    prov = TestProvenance(classification_id="clf_val_2", difference_id="diff_val_2")
    test_model = GeneratedTest(
        test_id="test_val_2",
        regression_id="clf_val_2",
        framework=TestFramework.PLAYWRIGHT,
        language=TestLanguage.TYPESCRIPT,
        title="Broken Delimiters Test",
        description="Broken test",
        steps=[],
        assertions=[],
        provenance=prov,
        status=SynthesisStatus.SYNTHESIZED,
        generated_source="import { test, expect } from '@playwright/test'; test('broken', async ({ page }) => { if (true) { ; });",
    )
    status, notes = GeneratedTestValidator.validate(test_model)
    assert status == ValidationStatus.VALIDATION_FAILED
    assert any("delimiter" in n.lower() for n in notes)


def test_validator_rejects_benchmark_ground_truth_leakage():
    """Verify validator immediately fails if benchmark defect tags are present."""
    prov = TestProvenance(classification_id="clf_val_3", difference_id="diff_val_3")
    test_model = GeneratedTest(
        test_id="test_val_3",
        regression_id="clf_val_3",
        framework=TestFramework.PLAYWRIGHT,
        language=TestLanguage.TYPESCRIPT,
        title="Defect Leakage Test",
        description="Bad test",
        steps=[],
        assertions=[],
        provenance=prov,
        status=SynthesisStatus.SYNTHESIZED,
        generated_source="import { test, expect } from '@playwright/test'; // Reproducing DEF-002 from ground_truth.json\ntest('x', async () => {});",
    )
    status, notes = GeneratedTestValidator.validate(test_model)
    assert status == ValidationStatus.VALIDATION_FAILED
    assert any("forbidden benchmark ground-truth" in n.lower() for n in notes)
