"""Falsification Condition Synthesis Engine.

Formulates testable, scientific falsification criteria for root-cause conclusions,
answering what exact counter-observation or code state would invalidate the finding.
"""

import hashlib

from packages.forensics.models import (
    FalsificationCondition,
    ForensicHypothesis,
    HypothesisCategory,
)


class FalsificationEngine:
    """Generates scientifically testable falsification conditions for forensic conclusions."""

    @staticmethod
    def generate_falsification_condition(
        hypothesis: ForensicHypothesis,
        source_file: str | None = None,
        line_number: int | None = None,
        commit_hash: str | None = None,
    ) -> FalsificationCondition:
        """Formulate explicit falsification criteria based on hypothesis category and source attribution."""
        loc_str = f" in {source_file}:{line_number}" if source_file and line_number else (
            f" in {source_file}" if source_file else ""
        )
        commit_str = f" from commit {commit_hash[:8]}" if commit_hash else ""

        if hypothesis.category == HypothesisCategory.CALCULATION_LOGIC:
            statement = (
                f"If the application in Version B reproduces the calculation discrepancy even when the "
                f"modified arithmetic/computation logic{loc_str}{commit_str} is reverted to the baseline version, "
                "the current root-cause hypothesis is falsified."
            )
            verification = (
                "Revert the identified computation patch and re-run the synthesized Playwright reproduction "
                "test to confirm whether the regression output ceases."
            )
            confounders = [
                "Server-side calculation override",
                "Intermediate state caching in LocalStorage/SessionStorage",
                "Client-side locale number formatting differences",
            ]

        elif hypothesis.category == HypothesisCategory.API_CONTRACT:
            statement = (
                f"If the network request payload and response contract in Version B match Version A exactly "
                f"while the discrepancy persists, the API contract hypothesis{loc_str} is falsified."
            )
            verification = (
                "Inspect network HAR trace to verify endpoint status codes, schema fields, and payload responses."
            )
            confounders = [
                "Backend API gateway rate limiting",
                "Stale HTTP cache headers (ETag/Cache-Control)",
                "Network timeout during exploration",
            ]

        elif hypothesis.category == HypothesisCategory.DOM_RENDER_LOGIC:
            statement = (
                f"If the DOM element state in Version B renders correctly under altered timing or viewport "
                f"conditions without modifying component logic{loc_str}, this rendering hypothesis is falsified."
            )
            verification = (
                "Verify component mounting lifecycle and DOM snapshot stability across multiple viewport resolutions."
            )
            confounders = [
                "CSS animation / transition race condition",
                "Lazy-loaded asset delay",
                "Viewport responsive breakpoint shifts",
            ]

        elif hypothesis.category == HypothesisCategory.TIMING_RACE_CONDITION:
            statement = (
                "If the behavioral discrepancy occurs deterministically on 100% of consecutive attempts "
                "regardless of artificial network latency throttling, the race-condition hypothesis is falsified."
            )
            verification = (
                "Execute 5 repeated reproduction runs under both 3G throttling and 0ms latency to test variance."
            )
            confounders = [
                "CPU throttling in test container",
                "Event loop microtask scheduling differences",
            ]

        elif hypothesis.category == HypothesisCategory.STYLING_FORMATTING:
            statement = (
                f"If the visual difference persists even when CSS rules{loc_str} are reset to baseline styles, "
                "the styling hypothesis is falsified."
            )
            verification = (
                "Perform pixel-diff comparison with baseline CSS applied to Version B."
            )
            confounders = [
                "Font rendering engine differences across operating systems",
                "Device pixel ratio / high-DPI scaling factors",
            ]

        else:
            statement = (
                f"If Version B demonstrates matching behavioral output with Version A without reverting "
                f"the candidate change{loc_str}, this conclusion is falsified."
            )
            verification = (
                "Execute clean environment replay comparing baseline and candidate builds."
            )
            confounders = [
                "Test harness execution jitter",
                "External dependency availability",
            ]

        cond_raw = f"{hypothesis.hypothesis_id}:{statement}"
        cond_id = f"fals_{hashlib.sha256(cond_raw.encode('utf-8')).hexdigest()[:10]}"

        return FalsificationCondition(
            condition_id=cond_id,
            statement=statement,
            testable_verification=verification,
            potential_confounders=confounders,
        )
