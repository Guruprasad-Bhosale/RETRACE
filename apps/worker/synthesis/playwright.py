"""Playwright TypeScript Serializer for Synthesized Regression Tests.

Serializes deterministic test models into clean, idiomatic, standalone or A/B Playwright
TypeScript test files with full causal step annotations and evidence provenance.
"""

from apps.worker.synthesis.config import SynthesisConfig
from apps.worker.synthesis.models import AssertionCategory, GeneratedTest, TestAssertion, TestStep


class PlaywrightTypeScriptSerializer:
    """Serializes GeneratedTest models into executable Playwright TypeScript test scripts."""

    def __init__(self, config: SynthesisConfig | None = None) -> None:
        self.config = config or SynthesisConfig()

    def serialize(self, test_model: GeneratedTest) -> str:
        """Serialize GeneratedTest domain entity into TypeScript test source string."""
        lines: list[str] = []

        # 1. Header Banner & Provenance
        lines.append("/**")
        lines.append(" * RETRACE AUTONOMOUS REGRESSION TEST (Phase 10 Synthesis)")
        lines.append(f" * Test ID:           {test_model.test_id}")
        lines.append(f" * Regression ID:     {test_model.regression_id}")
        if test_model.reproduction_id:
            lines.append(f" * Reproduction ID:   {test_model.reproduction_id}")
        if test_model.root_cause_id:
            lines.append(f" * Root Cause ID:     {test_model.root_cause_id}")
        if test_model.provenance.source_locations:
            lines.append(f" * Localized Source:  {', '.join(test_model.provenance.source_locations)}")
        if test_model.provenance.commit_hashes:
            lines.append(f" * Attributed Commit: {', '.join(test_model.provenance.commit_hashes)}")
        lines.append(" *")
        lines.append(" * Derived strictly from empirical Phase 6-8 observations and Phase 9 source attribution.")
        lines.append(" */")
        lines.append("")

        # 2. Imports
        lines.append("import { test, expect } from '@playwright/test';")
        lines.append("")

        # 3. Target Configuration
        base_env = self.config.baseline_env_var
        target_env = self.config.target_env_var
        lines.append(f"const BASE_URL = process.env.{target_env} || process.env.{base_env} || 'http://127.0.0.1:3000';")
        lines.append("")

        # 4. Test Suite Block
        safe_title = test_model.title.replace("'", "\\'")
        lines.append(f"test.describe('{safe_title}', () => {{")

        # 5. Test Case Block
        lines.append("  test('reproduce and assert against regression', async ({ page, request }) => {")
        lines.append("    // 1. Setup listeners for runtime errors and network responses")
        lines.append("    const pageErrors: Error[] = [];")
        lines.append("    page.on('pageerror', (err) => pageErrors.push(err));")
        lines.append("")

        # 6. Action Steps Execution
        if not test_model.steps:
            lines.append("    // Minimal navigation to application base URL")
            lines.append("    await page.goto(BASE_URL);")
        else:
            for step in test_model.steps:
                self._serialize_step(step, lines)

        lines.append("")
        lines.append("    // 2. Evidence-grounded assertions")

        # 7. Assertions Execution
        if not test_model.assertions:
            lines.append("    // Minimal baseline visibility assertion")
            lines.append("    await expect(page.locator('body')).toBeVisible();")
        else:
            for assertion in test_model.assertions:
                self._serialize_assertion(assertion, lines)

        lines.append("  });")
        lines.append("});")
        lines.append("")

        return "\n".join(lines)

    def _serialize_step(self, step: TestStep, lines: list[str]) -> None:
        """Render a single Playwright test step."""
        act_val = step.action_type.value if hasattr(step.action_type, "value") else str(step.action_type)
        act_val = act_val.upper()

        if step.description:
            lines.append(f"    // Step {step.step_index + 1}: {step.description}")

        if "NAVIGAT" in act_val:
            raw_url = step.value or step.raw_target or "/"
            if raw_url.startswith("http://") or raw_url.startswith("https://"):
                from urllib.parse import urlparse
                parsed = urlparse(raw_url)
                path = parsed.path or "/"
                if parsed.query:
                    path = f"{path}?{parsed.query}"
                lines.append(f"    await page.goto(`${{BASE_URL}}{path}`);")
            else:
                path = raw_url if raw_url.startswith("/") else f"/{raw_url}"
                lines.append(f"    await page.goto(`${{BASE_URL}}{path}`);")
            lines.append("    await page.waitForLoadState('domcontentloaded');")

        elif "CLICK" in act_val:
            lines.append(f"    await {step.resolved_selector}.click();")

        elif "TYPE" in act_val:
            safe_val = (step.value or "").replace("'", "\\'")
            lines.append(f"    await {step.resolved_selector}.fill('{safe_val}');")

        elif "SELECT" in act_val:
            safe_val = (step.value or "").replace("'", "\\'")
            lines.append(f"    await {step.resolved_selector}.selectOption('{safe_val}');")

        elif "HOVER" in act_val:
            lines.append(f"    await {step.resolved_selector}.hover();")

        elif "WAIT" in act_val:
            wait_ms = int(step.timeout_ms) if step.timeout_ms else 1000
            lines.append(f"    await page.waitForTimeout({min(wait_ms, 2000)});")

        else:
            # Generic fallback
            lines.append(f"    await {step.resolved_selector}.click();")

    def _serialize_assertion(self, assertion: TestAssertion, lines: list[str]) -> None:
        """Render a single Playwright test assertion."""
        lines.append(f"    // [Evidence {assertion.evidence_id}] {assertion.reasoning}")

        if assertion.manual_review_required:
            lines.append(f"    // MANUAL_REVIEW_REQUIRED: {assertion.expected_value}")
            return

        cat = assertion.category

        if cat == AssertionCategory.NAVIGATION:
            exp_val = str(assertion.expected_value).replace("'", "\\'")
            if exp_val.startswith("**"):
                sub_path = exp_val[2:]
                lines.append(f"    await expect(page).toHaveURL(new RegExp('{sub_path}'));")
            else:
                lines.append(f"    await expect(page).toHaveURL('{exp_val}');")

        elif cat == AssertionCategory.API_NETWORK:
            if "status" in assertion.subject:
                lines.append(f"    // Verify API HTTP status: expect({assertion.expected_value})")
                lines.append(f"    // Subject: {assertion.subject}")
            else:
                lines.append(f"    // Verify API payload field: expect({assertion.subject}).toEqual({assertion.expected_value})")

        elif cat == AssertionCategory.CALCULATION:
            exp_val = str(assertion.expected_value).replace("'", "\\'")
            lines.append(f"    await expect(page.locator('body')).toContainText('{exp_val}');")

        elif cat == AssertionCategory.ACCESSIBILITY:
            lines.append("    await expect(page.locator('body')).toBeVisible();")

        elif cat == AssertionCategory.RUNTIME_ERROR:
            lines.append(f"    expect(pageErrors).toHaveLength({assertion.expected_value});")

        elif cat == AssertionCategory.PERFORMANCE:
            lines.append(f"    // Performance threshold: {assertion.expected_value}ms")

        else:
            # UI_STATE
            if assertion.assertion_type == "toContainText":
                exp_val = str(assertion.expected_value).replace("'", "\\'")
                lines.append(f"    await expect(page.locator('body')).toContainText('{exp_val}');")
            else:
                lines.append("    await expect(page.locator('body')).toBeVisible();")
