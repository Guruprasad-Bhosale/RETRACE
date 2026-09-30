"""Unit tests for deterministic selector resolution."""

from apps.worker.reproduction.models import ActionType, ReproductionStep
from apps.worker.synthesis.models import SelectorStrategy
from apps.worker.synthesis.selectors import DeterministicSelectorResolver


def test_resolve_role_and_name():
    """Verify role and accessible name produce getByRole selector."""
    step = ReproductionStep(
        step_index=0,
        action_type=ActionType.CLICK,
        target_role="button",
        accessible_name="Submit Order",
    )
    locator, strategy, desc = DeterministicSelectorResolver.resolve_step_locator(step)
    assert strategy == SelectorStrategy.ROLE_AND_NAME
    assert locator == "page.getByRole('button', { name: 'Submit Order' })"


def test_resolve_test_id():
    """Verify data-testid in stable identity produces getByTestId selector."""
    step = ReproductionStep(
        step_index=0,
        action_type=ActionType.CLICK,
        stable_target_identity='button[data-testid="checkout-btn"]',
    )
    locator, strategy, desc = DeterministicSelectorResolver.resolve_step_locator(step)
    assert strategy == SelectorStrategy.TEST_ID
    assert locator == "page.getByTestId('checkout-btn')"


def test_resolve_stable_id():
    """Verify single hash id produces locator('#id')."""
    step = ReproductionStep(
        step_index=0,
        action_type=ActionType.CLICK,
        stable_target_identity="#checkout-button",
    )
    locator, strategy, desc = DeterministicSelectorResolver.resolve_step_locator(step)
    assert strategy == SelectorStrategy.STABLE_ID
    assert locator == "page.locator('#checkout-button')"


def test_resolve_label():
    """Verify accessible name without role produces getByLabel."""
    step = ReproductionStep(
        step_index=0,
        action_type=ActionType.TYPE,
        accessible_name="Email Address",
        value="test@example.com",
    )
    locator, strategy, desc = DeterministicSelectorResolver.resolve_step_locator(step)
    assert strategy == SelectorStrategy.LABEL
    assert locator == "page.getByLabel('Email Address')"


def test_resolve_semantic_attribute():
    """Verify semantic attribute [name="..."] produces attribute locator."""
    step = ReproductionStep(
        step_index=0,
        action_type=ActionType.TYPE,
        raw_target='input[name="coupon_code"]',
        value="SAVE10",
    )
    locator, strategy, desc = DeterministicSelectorResolver.resolve_step_locator(step)
    assert strategy == SelectorStrategy.SEMANTIC_ATTRIBUTE
    assert locator == "page.locator('[name=\"coupon_code\"]')"


def test_resolve_fallback():
    """Verify fallback to body when no selectors are provided."""
    step = ReproductionStep(
        step_index=0,
        action_type=ActionType.WAIT,
    )
    locator, strategy, desc = DeterministicSelectorResolver.resolve_step_locator(step)
    assert strategy == SelectorStrategy.FALLBACK_CSS
    assert locator == "page.locator('body')"
