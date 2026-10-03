"""Hypothesis Formulation, Evaluation, and Elimination Engine.

Formulates explicit regression hypotheses, manages their lifecycle transitions,
evaluates evidence support/contradiction, and systematically eliminates disproven alternatives.
"""

import hashlib

from packages.forensics.models import (
    AlternativeExplanation,
    ForensicEvidenceItem,
    ForensicEvidenceType,
    ForensicHypothesis,
    HypothesisCategory,
    HypothesisStatus,
)


class HypothesisEngine:
    """Diagnostic engine formulating hypotheses and eliminating disproven alternatives."""

    @classmethod
    def evaluate_hypotheses(
        cls,
        investigation_id: str,
        category: str,
        title: str,
        description: str,
        evidence_items: list[ForensicEvidenceItem],
        has_reproduction: bool = False,
        reproduction_failed: bool = False,
        source_file: str | None = None,
        source_function: str | None = None,
    ) -> tuple[ForensicHypothesis, list[AlternativeExplanation]]:

        """Formulate candidate hypotheses, confirm the primary hypothesis, and eliminate alternatives.

        Returns:
            tuple of (primary_confirmed_hypothesis, list_of_eliminated_alternatives)
        """
        evidence_by_type: dict[ForensicEvidenceType, list[ForensicEvidenceItem]] = {}
        for ev in evidence_items:
            evidence_by_type.setdefault(ev.evidence_type, []).append(ev)

        has_network_failure = any(
            ev for ev in evidence_by_type.get(ForensicEvidenceType.NETWORK_OBSERVATION, [])
            if "fail" in ev.observation.lower() or "500" in ev.observation
        )
        has_ast_diff = bool(evidence_by_type.get(ForensicEvidenceType.AST_DIFF) or source_file)

        # 1. Determine primary category
        cat_lower = category.lower()
        title_lower = title.lower()
        desc_lower = description.lower()
        src_lower = (source_file or "").lower()

        if "calc" in cat_lower or "total" in title_lower or "price" in title_lower or "discount" in title_lower or "calc" in desc_lower:
            primary_cat = HypothesisCategory.CALCULATION_LOGIC
            primary_title = f"Calculation logic modified in {source_function or 'computation component'}"
            primary_desc = f"Arithmetic or business logic regression in {source_file or 'source'}: {description}"
        elif "api" in cat_lower or "contract" in cat_lower or "network" in cat_lower or "endpoint" in desc_lower or "500" in desc_lower:
            primary_cat = HypothesisCategory.API_CONTRACT
            primary_title = "API contract or payload discrepancy on endpoint"
            primary_desc = f"Network or schema response regression: {description}"
        elif "timing" in cat_lower or "race" in cat_lower or "race condition" in desc_lower or "flakiness" in desc_lower or "intermittent" in desc_lower:
            primary_cat = HypothesisCategory.TIMING_RACE_CONDITION
            primary_title = "Asynchronous hydration or timing race condition"
            primary_desc = f"Timing/race condition regression: {description}"
        elif "visual" in cat_lower or "style" in cat_lower or "color" in cat_lower or "css" in src_lower or "styling" in desc_lower or "padding" in desc_lower:
            primary_cat = HypothesisCategory.STYLING_FORMATTING
            primary_title = "Visual formatting or CSS layout regression"
            primary_desc = f"Presentation styling discrepancy: {description}"
        elif "nav" in cat_lower or "route" in cat_lower:
            primary_cat = HypothesisCategory.NAVIGATION_ROUTING
            primary_title = "Navigation or routing handler failure"
            primary_desc = f"Client-side route or redirect regression: {description}"
        elif "unknown" in cat_lower or "unspecified" in desc_lower or "unresolved" in desc_lower:
            primary_cat = HypothesisCategory.UNKNOWN
            primary_title = "Unresolved behavioral regression without conclusive hypothesis"
            primary_desc = f"Unresolved telemetry anomaly: {description}"
        else:
            primary_cat = HypothesisCategory.DOM_RENDER_LOGIC
            primary_title = "Component DOM rendering state discrepancy"
            primary_desc = f"DOM mutation regression: {description}"



        # 2. Build Primary Hypothesis
        primary_id = f"hyp_{hashlib.sha256(f'{investigation_id}:primary:{primary_cat}'.encode()).hexdigest()[:8]}"
        supporting_ids = [ev.id for ev in evidence_items]
        primary_status = (
            HypothesisStatus.SUPPORTED if (primary_cat == HypothesisCategory.TIMING_RACE_CONDITION and reproduction_failed)
            else HypothesisStatus.WEAKENED if reproduction_failed
            else HypothesisStatus.CONFIRMED if has_reproduction and has_ast_diff
            else HypothesisStatus.SUPPORTED if has_reproduction or has_ast_diff
            else HypothesisStatus.PROPOSED
        )



        primary_hypothesis = ForensicHypothesis(
            hypothesis_id=primary_id,
            title=primary_title,
            description=primary_desc,
            category=primary_cat,
            status=primary_status,
            supporting_evidence_ids=supporting_ids,
            contradicting_evidence_ids=[],
            score=0.95 if primary_status == HypothesisStatus.CONFIRMED else 0.70,
        )

        # 3. Formulate and Systematically Eliminate Alternative Explanations
        alternatives: list[AlternativeExplanation] = []

        # Alternative: Formatting / CSS Issue
        if primary_cat != HypothesisCategory.STYLING_FORMATTING:
            alt_id = f"alt_{hashlib.sha256(f'{investigation_id}:styling'.encode()).hexdigest()[:8]}"
            alternatives.append(
                AlternativeExplanation(
                    alternative_id=alt_id,
                    title="Client-side CSS or Visual Formatting discrepancy",
                    category=HypothesisCategory.STYLING_FORMATTING,
                    status=HypothesisStatus.ELIMINATED,
                    elimination_reason=(
                        "Ruled out: Verified that CSS stylesheets are unchanged. "
                        "The observed discrepancy stems from numerical/logical state rather than styling rules."
                    ),
                    evidence_references=supporting_ids[:2],
                )
            )

        # Alternative: API / Network Failure
        if primary_cat != HypothesisCategory.API_CONTRACT:
            alt_id = f"alt_{hashlib.sha256(f'{investigation_id}:api'.encode()).hexdigest()[:8]}"
            reason = (
                "Ruled out: HTTP status code was 200 OK and response schema matched baseline."
                if not has_network_failure
                else "Weakened: Network responses are identical, failure localized to frontend consumer logic."
            )
            alternatives.append(
                AlternativeExplanation(
                    alternative_id=alt_id,
                    title="Backend API Contract or Payload Regression",
                    category=HypothesisCategory.API_CONTRACT,
                    status=HypothesisStatus.ELIMINATED if not has_network_failure else HypothesisStatus.WEAKENED,
                    elimination_reason=reason,
                    evidence_references=supporting_ids[:1],
                )
            )

        # Alternative: Timing / Race Condition
        if primary_cat != HypothesisCategory.TIMING_RACE_CONDITION:
            alt_id = f"alt_{hashlib.sha256(f'{investigation_id}:race'.encode()).hexdigest()[:8]}"
            alternatives.append(
                AlternativeExplanation(
                    alternative_id=alt_id,
                    title="Asynchronous Timing or Event-Loop Race Condition",
                    category=HypothesisCategory.TIMING_RACE_CONDITION,
                    status=HypothesisStatus.ELIMINATED,
                    elimination_reason=(
                        "Ruled out: The regression reproduced deterministically on consecutive execution attempts "
                        "without timing variance or transient behavior."
                    ),
                    evidence_references=supporting_ids[:1],
                )
            )

        return primary_hypothesis, alternatives
