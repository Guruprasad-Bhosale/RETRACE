"""Deterministic Selector Resolver for Playwright Test Synthesis.

Translates reproduction path steps and observed DOM identities into robust, deterministic
Playwright locator expressions following accessible and semantic selector hierarchies.
"""

import re

from apps.worker.reproduction.models import ReproductionStep
from apps.worker.synthesis.models import SelectorStrategy


class DeterministicSelectorResolver:
    """Resolves deterministic Playwright locators from reproduction step identities."""

    @classmethod
    def resolve_step_locator(
        cls, step: ReproductionStep
    ) -> tuple[str, SelectorStrategy, str]:
        """Resolve Playwright locator expression and strategy for a step.

        Returns:
            Tuple of (playwright_locator_expression, strategy_used, description)
        """
        role = step.target_role.strip().lower() if step.target_role else None
        name = step.accessible_name.strip() if step.accessible_name else None
        stable_id = step.stable_target_identity.strip() if step.stable_target_identity else None
        raw_target = step.raw_target.strip() if step.raw_target else None

        # 1. Prefer Role + Accessible Name (most resilient accessible pattern)
        if role and name:
            safe_name = name.replace("'", "\\'")
            locator = f"page.getByRole('{role}', {{ name: '{safe_name}' }})"
            desc = f"element with role '{role}' and name '{name}'"
            return locator, SelectorStrategy.ROLE_AND_NAME, desc

        # 2. Test ID attribute check (e.g. [data-testid="xyz"] or data-test-id)
        if stable_id:
            testid_match = re.search(r'data-testid=["\']?([^"\'\]]+)["\']?', stable_id)
            if testid_match:
                tid = testid_match.group(1)
                locator = f"page.getByTestId('{tid}')"
                desc = f"element with testid '{tid}'"
                return locator, SelectorStrategy.TEST_ID, desc

        # 3. Stable element ID (e.g. #checkout-btn, #cart-total)
        if stable_id and stable_id.startswith("#") and " " not in stable_id:
            elem_id = stable_id[1:]
            locator = f"page.locator('#{elem_id}')"
            desc = f"element with id '{elem_id}'"
            return locator, SelectorStrategy.STABLE_ID, desc

        if raw_target and raw_target.startswith("#") and " " not in raw_target:
            elem_id = raw_target[1:]
            locator = f"page.locator('#{elem_id}')"
            desc = f"element with id '{elem_id}'"
            return locator, SelectorStrategy.STABLE_ID, desc

        # 4. Accessible Name alone (Label / Text)
        if name:
            safe_name = name.replace("'", "\\'")
            locator = f"page.getByLabel('{safe_name}')"
            desc = f"element with label '{name}'"
            return locator, SelectorStrategy.LABEL, desc

        # 5. Semantic attributes (e.g. [name="coupon"], [placeholder="..."])
        for candidate in [stable_id, raw_target]:
            if candidate:
                attr_match = re.search(r'\[(name|placeholder|type|aria-label)=["\']([^"\']+)["\']\]', candidate)
                if attr_match:
                    attr_name, attr_val = attr_match.group(1), attr_match.group(2)
                    locator = f"page.locator('[{attr_name}=\"{attr_val}\"]')"
                    desc = f"element with [{attr_name}=\"{attr_val}\"]"
                    return locator, SelectorStrategy.SEMANTIC_ATTRIBUTE, desc

        # 6. Action locator from reproduction
        if raw_target:
            safe_target = raw_target.replace("'", "\\'")
            locator = f"page.locator('{safe_target}')"
            desc = f"locator '{raw_target}'"
            return locator, SelectorStrategy.ACTION_LOCATOR, desc

        if stable_id:
            safe_id = stable_id.replace("'", "\\'")
            locator = f"page.locator('{safe_id}')"
            desc = f"locator '{stable_id}'"
            return locator, SelectorStrategy.ACTION_LOCATOR, desc

        # 7. Fallback to generic locator or body
        locator = "page.locator('body')"
        desc = "page body fallback"
        return locator, SelectorStrategy.FALLBACK_CSS, desc
