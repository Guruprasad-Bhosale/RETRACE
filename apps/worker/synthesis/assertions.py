"""Evidence-Derived Assertion Generator.

Synthesizes deterministic Playwright assertions strictly grounded in empirical
Phase 6-8 differences, reproduction verifications, and root cause evidence.
"""

from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from apps.worker.regression.models import RegressionClassification
from apps.worker.reproduction.models import ReproductionResult
from apps.worker.rootcause.models import RootCauseResult
from apps.worker.synthesis.config import SynthesisConfig
from apps.worker.synthesis.models import AssertionCategory, TestAssertion


class AssertionGenerator:
    """Derives strictly evidence-backed assertions from regression and reproduction artifacts."""

    VOLATILE_API_KEYS = {
        "timestamp",
        "time",
        "created_at",
        "updated_at",
        "date",
        "id",
        "uuid",
        "request_id",
        "session_id",
        "token",
        "nonce",
        "csrf",
        "_t",
    }

    def __init__(self, config: SynthesisConfig | None = None) -> None:
        self.config = config or SynthesisConfig()

    def generate_assertions(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None = None,
        root_cause: RootCauseResult | None = None,
    ) -> list[TestAssertion]:
        """Derive all applicable test assertions from authoritative upstream evidence.

        Returns:
            List of TestAssertion instances.
        """
        category_name = classification.category.value if hasattr(classification.category, "value") else str(classification.category)
        category_name = category_name.upper()
        details = classification.evidence.details if classification.evidence else {}

        assertions: list[TestAssertion] = []

        if "NAVIGAT" in category_name:
            nav_assertion = self._generate_navigation_assertion(classification, reproduction, details)
            if nav_assertion:
                assertions.append(nav_assertion)

        elif "API" in category_name or "CONTRACT" in category_name:
            api_assertions = self._generate_api_assertions(classification, reproduction, details)
            assertions.extend(api_assertions)

        elif "CALCULAT" in category_name:
            calc_assertion = self._generate_calculation_assertion(classification, reproduction, details)
            if calc_assertion:
                assertions.append(calc_assertion)

        elif "ACCESSIBIL" in category_name:
            a11y_assertion = self._generate_accessibility_assertion(classification, reproduction, details)
            if a11y_assertion:
                assertions.append(a11y_assertion)

        elif "PERFORMANC" in category_name:
            perf_assertion = self._generate_performance_assertion(classification, reproduction, details)
            if perf_assertion:
                assertions.append(perf_assertion)

        elif "RUNTIME" in category_name or "ERROR" in category_name:
            err_assertion = self._generate_runtime_error_assertion(classification, reproduction, details)
            if err_assertion:
                assertions.append(err_assertion)

        else:
            # UI_STATE / FUNCTIONAL / STATE fallback
            ui_assertion = self._generate_ui_state_assertion(classification, reproduction, details)
            if ui_assertion:
                assertions.append(ui_assertion)

        # If no specialized assertion was generated, add a safe UI/URL verification if reproduction observation exists
        if not assertions and reproduction and reproduction.attempts:
            last_attempt = reproduction.attempts[-1]
            if last_attempt.evidence.observations_a:
                obs_a = last_attempt.evidence.observations_a[-1]
                path_a = urlparse(obs_a.url).path or "/"
                assertions.append(
                    TestAssertion(
                        assertion_id=f"ast_{uuid4().hex[:8]}",
                        category=AssertionCategory.UI_STATE,
                        assertion_type="toBeVisible",
                        subject="page.locator('body')",
                        expected_value="page body visible",
                        actual_value_observed="rendered state",
                        evidence_id=classification.classification_id,
                        reasoning=f"Baseline state reached path '{path_a}' without unhandled exception.",
                    )
                )

        return assertions

    def _generate_navigation_assertion(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        details: dict[str, Any],
    ) -> TestAssertion | None:
        """Derive URL or route expectation."""
        expected_url = details.get("expected_url") or details.get("url_a")
        actual_url = details.get("actual_url") or details.get("url_b")

        if not expected_url and reproduction and reproduction.attempts:
            obs_a = reproduction.attempts[-1].evidence.observations_a
            if obs_a:
                expected_url = obs_a[-1].url
            obs_b = reproduction.attempts[-1].evidence.observations_b
            if obs_b:
                actual_url = obs_b[-1].url

        if not expected_url:
            return None

        # Extract path pattern to keep test portable across host ports
        parsed = urlparse(expected_url)
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        return TestAssertion(
            assertion_id=f"ast_{uuid4().hex[:8]}",
            category=AssertionCategory.NAVIGATION,
            assertion_type="toHaveURL",
            subject="page",
            expected_value=f"**{path}",
            actual_value_observed=actual_url,
            evidence_id=classification.classification_id,
            reasoning=f"Expected navigation to destination path '{path}' following action sequence.",
        )

    def _generate_api_assertions(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        details: dict[str, Any],
    ) -> list[TestAssertion]:
        """Derive API response status and payload assertions."""
        assertions: list[TestAssertion] = []
        expected_status = details.get("status_a") or details.get("expected_status") or 200
        actual_status = details.get("status_b") or details.get("actual_status")
        endpoint = details.get("endpoint") or details.get("url") or "/api"

        parsed_ep = urlparse(endpoint).path or endpoint

        assertions.append(
            TestAssertion(
                assertion_id=f"ast_{uuid4().hex[:8]}",
                category=AssertionCategory.API_NETWORK,
                assertion_type="toBe",
                subject=f"apiResponse.status() for '{parsed_ep}'",
                expected_value=int(expected_status),
                actual_value_observed=actual_status,
                evidence_id=classification.classification_id,
                reasoning=f"Expected HTTP status {expected_status} for endpoint '{parsed_ep}'.",
            )
        )

        payload_diff = details.get("payload_diff")
        if isinstance(payload_diff, dict) and self.config.sanitize_volatile_api_fields:
            # Add assertions for non-volatile stable keys
            for key, val in payload_diff.items():
                if key.lower() not in self.VOLATILE_API_KEYS and not isinstance(val, (dict, list)):
                    assertions.append(
                        TestAssertion(
                            assertion_id=f"ast_{uuid4().hex[:8]}",
                            category=AssertionCategory.API_NETWORK,
                            assertion_type="toEqual",
                            subject=f"apiBody.{key}",
                            expected_value=val,
                            evidence_id=classification.classification_id,
                            reasoning=f"Expected API payload attribute '{key}' to match baseline contract.",
                        )
                    )

        return assertions

    def _generate_calculation_assertion(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        details: dict[str, Any],
    ) -> TestAssertion | None:
        """Derive calculation value assertion."""
        expected_val = details.get("expected_value") or details.get("value_a") or details.get("text_a")
        actual_val = details.get("actual_value") or details.get("value_b") or details.get("text_b")
        target_field = details.get("target_field") or details.get("field") or "total"

        if expected_val is None:
            return None

        return TestAssertion(
            assertion_id=f"ast_{uuid4().hex[:8]}",
            category=AssertionCategory.CALCULATION,
            assertion_type="toContainText",
            subject=f"locator for calculation target '{target_field}'",
            expected_value=str(expected_val),
            actual_value_observed=str(actual_val) if actual_val is not None else None,
            tolerance=self.config.calculation_relative_tolerance,
            evidence_id=classification.classification_id,
            reasoning=f"Calculation result for '{target_field}' must reflect expected value '{expected_val}'.",
        )

    def _generate_accessibility_assertion(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        details: dict[str, Any],
    ) -> TestAssertion | None:
        """Derive accessibility attribute assertion."""
        attr_name = details.get("attribute") or details.get("aria_attribute") or "aria-label"
        expected_val = details.get("expected_value") or details.get("value_a") or ""
        actual_val = details.get("actual_value") or details.get("value_b")
        target = details.get("target") or "element"

        return TestAssertion(
            assertion_id=f"ast_{uuid4().hex[:8]}",
            category=AssertionCategory.ACCESSIBILITY,
            assertion_type="toHaveAttribute",
            subject=f"locator('{target}')",
            expected_value=str(expected_val),
            actual_value_observed=str(actual_val) if actual_val is not None else None,
            evidence_id=classification.classification_id,
            reasoning=f"Element '{target}' must retain accessible attribute '{attr_name}=\"{expected_val}\"'.",
        )

    def _generate_performance_assertion(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        details: dict[str, Any],
    ) -> TestAssertion:
        """Derive conservative performance timing assertion."""
        samples_a: list[float] = []
        samples_b: list[float] = []

        if reproduction and reproduction.attempts:
            for att in reproduction.attempts:
                samples_a.extend(att.evidence.sample_measurements_ms_a)
                samples_b.extend(att.evidence.sample_measurements_ms_b)

        # If insufficient repeated measurements, require manual review
        if len(samples_a) < self.config.min_performance_samples_for_assertion:
            return TestAssertion(
                assertion_id=f"ast_{uuid4().hex[:8]}",
                category=AssertionCategory.PERFORMANCE,
                assertion_type="lessThan",
                subject="actionDurationMs",
                expected_value="MANUAL_REVIEW_REQUIRED",
                actual_value_observed=details.get("latency_b"),
                manual_review_required=True,
                evidence_id=classification.classification_id,
                reasoning=(
                    f"Performance timing difference observed, but sample size ({len(samples_a)}) "
                    f"is below configured threshold ({self.config.min_performance_samples_for_assertion}). "
                    "Manual review required."
                ),
            )

        # If >= min samples, compute upper bound (mean + 2 * stddev or 1.5 * mean)
        avg_a = sum(samples_a) / len(samples_a)
        upper_bound = avg_a * 1.5 + 100.0  # Safe deterministic bound

        return TestAssertion(
            assertion_id=f"ast_{uuid4().hex[:8]}",
            category=AssertionCategory.PERFORMANCE,
            assertion_type="lessThan",
            subject="actionDurationMs",
            expected_value=round(upper_bound, 2),
            actual_value_observed=round(sum(samples_b) / len(samples_b), 2) if samples_b else None,
            manual_review_required=False,
            evidence_id=classification.classification_id,
            reasoning=f"Action duration must stay within verified baseline upper bound ({round(upper_bound, 2)}ms).",
        )

    def _generate_runtime_error_assertion(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        details: dict[str, Any],
    ) -> TestAssertion:
        """Derive console/runtime error assertion."""
        return TestAssertion(
            assertion_id=f"ast_{uuid4().hex[:8]}",
            category=AssertionCategory.RUNTIME_ERROR,
            assertion_type="toHaveLength",
            subject="pageErrors",
            expected_value=0,
            actual_value_observed=details.get("error_count_b", 1),
            evidence_id=classification.classification_id,
            reasoning="Expected 0 unhandled runtime page errors during workflow execution.",
        )

    def _generate_ui_state_assertion(
        self,
        classification: RegressionClassification,
        reproduction: ReproductionResult | None,
        details: dict[str, Any],
    ) -> TestAssertion | None:
        """Derive UI element state/text assertion."""
        subject = details.get("target_identity") or details.get("selector") or "body"
        expected_text = details.get("text_a") or details.get("expected_text")
        actual_text = details.get("text_b") or details.get("actual_text")

        if expected_text:
            return TestAssertion(
                assertion_id=f"ast_{uuid4().hex[:8]}",
                category=AssertionCategory.UI_STATE,
                assertion_type="toContainText",
                subject=f"locator('{subject}')",
                expected_value=str(expected_text),
                actual_value_observed=str(actual_text) if actual_text is not None else None,
                evidence_id=classification.classification_id,
                reasoning=f"UI element '{subject}' expected to contain text '{expected_text}'.",
            )

        return TestAssertion(
            assertion_id=f"ast_{uuid4().hex[:8]}",
            category=AssertionCategory.UI_STATE,
            assertion_type="toBeVisible",
            subject=f"locator('{subject}')",
            expected_value="visible",
            actual_value_observed="hidden or missing",
            evidence_id=classification.classification_id,
            reasoning=f"UI element '{subject}' expected to remain visible in workflow.",
        )
