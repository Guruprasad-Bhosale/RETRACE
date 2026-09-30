"""Expected vs Actual Regression Reproduction Verifier."""

import statistics
from typing import Any

from apps.worker.regression.models import RegressionClassification
from apps.worker.reproduction.config import VerificationPolicy
from apps.worker.reproduction.models import (
    MatchStatus,
    ReproductionObservation,
    ReproductionVerification,
)


class ReproductionVerifier:
    """Verifies whether fresh multi-modal replay observations reproduce expected regression classifications."""

    @classmethod
    def verify(
        cls,
        classification: RegressionClassification,
        observations_a: list[ReproductionObservation],
        observations_b: list[ReproductionObservation],
        policy: VerificationPolicy,
        sample_timings_a: list[float] | None = None,
        sample_timings_b: list[float] | None = None,
    ) -> ReproductionVerification:
        """Compare expected regression semantics against fresh Version A and Version B observations."""
        matched_evidence: list[str] = []
        mismatched_evidence: list[str] = []
        observed_summary: dict[str, Any] = {}

        if not observations_a and not observations_b:
            return ReproductionVerification(
                expected_difference_id=classification.difference_id,
                expected_classification_id=classification.classification_id,
                expected_rule_id=classification.rule_id,
                expected_category=classification.category.value,
                match_status=MatchStatus.NOT_COMPARABLE,
                observed_match=False,
                mismatched_evidence=["No fresh observations captured for comparison."],
                notes="Neither Version A nor Version B produced replay observations.",
            )

        # Get final or triggering step observations
        final_obs_a = observations_a[-1] if observations_a else None
        final_obs_b = observations_b[-1] if observations_b else None

        rule_id = classification.rule_id
        category = classification.category.value

        match_status = MatchStatus.NO_MATCH
        observed_match = False

        # 1. Functional / HTTP Status Regressions
        if rule_id in ("FUNC-HTTP-STATUS-ERROR", "API-REQUEST-STATUS-ERROR", "API-REQUEST-FAILURE"):
            status_a = final_obs_a.http_status if final_obs_a else None
            status_b = final_obs_b.http_status if final_obs_b else None
            observed_summary["http_status_a"] = status_a
            observed_summary["http_status_b"] = status_b

            if status_b and status_b >= 400 and (status_a is None or status_a < 400):
                matched_evidence.append(
                    f"Target Version B returned error status {status_b} while Baseline Version A was {status_a}."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            elif final_obs_b and final_obs_b.network_failures_count > 0:
                matched_evidence.append(
                    f"Target Version B recorded {final_obs_b.network_failures_count} network failures."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            else:
                mismatched_evidence.append(
                    f"Expected HTTP error in Version B, but got status A={status_a}, B={status_b}."
                )

        # 2. Navigation / Route Divergence
        elif rule_id in ("NAV-ROUTE-REMOVED", "NAV-TRANSITION-TARGET"):
            url_a = final_obs_a.url if final_obs_a else ""
            url_b = final_obs_b.url if final_obs_b else ""
            observed_summary["final_url_a"] = url_a
            observed_summary["final_url_b"] = url_b

            if (final_obs_b and final_obs_b.http_status == 404) or (url_a and url_b and url_a != url_b):
                matched_evidence.append(
                    f"Navigation target diverged: Version A reached '{url_a}', Version B reached '{url_b}' (status={final_obs_b.http_status if final_obs_b else 'N/A'})."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            else:
                mismatched_evidence.append(
                    f"Expected route divergence or removal, but both versions reached equivalent URLs (A='{url_a}', B='{url_b}')."
                )

        # 3. Runtime Errors (Console / Unhandled Page Errors)
        elif rule_id in ("RUNTIME-PAGE-ERROR", "RUNTIME-CONSOLE-ERROR", "RUNTIME-CONSOLE-WARNING"):
            page_errors_b = sum(o.page_errors_count for o in observations_b)
            console_errors_b = sum(o.console_errors_count for o in observations_b)
            page_errors_a = sum(o.page_errors_count for o in observations_a)
            console_errors_a = sum(o.console_errors_count for o in observations_a)

            observed_summary["page_errors_a"] = page_errors_a
            observed_summary["page_errors_b"] = page_errors_b
            observed_summary["console_errors_a"] = console_errors_a
            observed_summary["console_errors_b"] = console_errors_b

            if rule_id == "RUNTIME-PAGE-ERROR" and page_errors_b > page_errors_a:
                matched_evidence.append(
                    f"Version B emitted {page_errors_b} unhandled page error(s) while Version A emitted {page_errors_a}."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            elif rule_id == "RUNTIME-CONSOLE-ERROR" and console_errors_b > console_errors_a:
                matched_evidence.append(
                    f"Version B emitted {console_errors_b} console error(s) while Version A emitted {console_errors_a}."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            elif page_errors_b > 0 or console_errors_b > 0:
                matched_evidence.append(
                    f"Version B exhibited runtime diagnostics (page_errors={page_errors_b}, console_errors={console_errors_b})."
                )
                match_status = MatchStatus.PARTIAL_MATCH
                observed_match = policy.allow_partial_match_as_reproduced
            else:
                mismatched_evidence.append("Expected runtime errors in Version B, but none were observed.")

        # 4. UI Behavior & State Constraints (Action Removed / Disabled)
        elif rule_id in (
            "UI-ACTION-REMOVED",
            "UI-ACTION-DISABLED",
            "STATE-ACTION-DISABLED",
            "STATE-FORM-REQUIRED",
            "FUNC-TRANSITION-TARGET-ERROR",
        ):
            # Check if action executed in A but failed/disappeared in B at the triggering step
            success_a = all(o.action_success for o in observations_a) if observations_a else True
            failed_steps_b = [o for o in observations_b if not o.action_success]

            observed_summary["action_success_a"] = success_a
            observed_summary["failed_steps_b_count"] = len(failed_steps_b)

            if failed_steps_b and success_a:
                first_fail = failed_steps_b[0]
                matched_evidence.append(
                    f"Action at step {first_fail.step_index} failed in Version B ({first_fail.error_message or 'Element not actionable'}) while succeeding in Version A."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            elif final_obs_a and final_obs_b and final_obs_a.dom_hash != final_obs_b.dom_hash:
                matched_evidence.append(
                    f"DOM state divergence observed at final step (DOM hash A={final_obs_a.dom_hash[:8]}, B={final_obs_b.dom_hash[:8]})."
                )
                match_status = MatchStatus.PARTIAL_MATCH
                observed_match = policy.allow_partial_match_as_reproduced
            else:
                mismatched_evidence.append(
                    "Expected action removal or failure in Version B, but action execution succeeded identically."
                )

        # 5. Calculation Output Changed
        elif rule_id in ("CALC-OUTPUT-CHANGED", "CALCULATION"):
            dom_hash_a = final_obs_a.dom_hash if final_obs_a else ""
            dom_hash_b = final_obs_b.dom_hash if final_obs_b else ""
            observed_summary["dom_hash_a"] = dom_hash_a
            observed_summary["dom_hash_b"] = dom_hash_b

            if dom_hash_a and dom_hash_b and dom_hash_a != dom_hash_b:
                matched_evidence.append(
                    f"Calculation / structural state output diverged: DOM hash A={dom_hash_a[:8]}, B={dom_hash_b[:8]}."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            else:
                mismatched_evidence.append(
                    "Expected calculation/output divergence, but DOM structures matched."
                )

        # 6. Performance Regressions (Repeated Sampling Support)
        elif rule_id in ("PERF-NAVIGATION-SLOWDOWN", "PERF-STABILIZATION-SLOWDOWN"):
            dur_a = (
                statistics.median(sample_timings_a)
                if sample_timings_a
                else (final_obs_a.duration_ms if final_obs_a else 0.0)
            )
            dur_b = (
                statistics.median(sample_timings_b)
                if sample_timings_b
                else (final_obs_b.duration_ms if final_obs_b else 0.0)
            )
            delta = dur_b - dur_a
            observed_summary["duration_a_ms"] = dur_a
            observed_summary["duration_b_ms"] = dur_b
            observed_summary["delta_ms"] = delta

            if delta >= policy.performance_delta_threshold_ms:
                matched_evidence.append(
                    f"Observed performance degradation: Version B was {delta:.2f}ms slower than Version A (threshold={policy.performance_delta_threshold_ms}ms)."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            else:
                mismatched_evidence.append(
                    f"Performance delta {delta:.2f}ms did not satisfy threshold {policy.performance_delta_threshold_ms}ms."
                )

        # 7. Generic Fallback
        else:
            if final_obs_a and final_obs_b and (
                final_obs_a.dom_hash != final_obs_b.dom_hash
                or final_obs_a.http_status != final_obs_b.http_status
            ):
                matched_evidence.append(
                    f"Generic state divergence reproduced for category {category}."
                )
                match_status = MatchStatus.FULL_MATCH
                observed_match = True
            else:
                mismatched_evidence.append(
                    f"No observable behavioral difference detected for {rule_id}."
                )

        return ReproductionVerification(
            expected_difference_id=classification.difference_id,
            expected_classification_id=classification.classification_id,
            expected_rule_id=classification.rule_id,
            expected_category=classification.category.value,
            match_status=match_status,
            observed_match=observed_match,
            matched_evidence=matched_evidence,
            mismatched_evidence=mismatched_evidence,
            notes=f"Evaluated {len(observations_a)} step(s) in A and {len(observations_b)} step(s) in B.",
            observed_difference_summary=observed_summary,
        )
