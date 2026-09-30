"""Interactive Element and Form Semantic Difference Analyzer.

Extracts deterministic differences in interactive element inventories, form states,
DOM structure signatures, and button/input enablements.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    InteractionDifference,
    compute_deterministic_diff_id,
)
from apps.worker.diff.normalization import DiffNormalizer


class InteractionDiffer:
    """Compares interactive inventory structures, form states, and actionable element properties."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[InteractionDifference]:
        """Extract deterministic interaction and DOM inventory differences."""
        if not self.config.enable_interaction_diff and not self.config.enable_dom_diff:
            return []

        differences: list[InteractionDifference] = []
        align = alignment_result.alignment

        # 1. State-level inventory & DOM structure comparison
        for sa in align.aligned_states:
            if sa.relation not in (
                AlignmentRelation.EXACT_MATCH,
                AlignmentRelation.STRONG_MATCH,
                AlignmentRelation.PARTIAL_MATCH,
            ):
                continue

            sig_a = sa.signature_a
            sig_b = sa.signature_b
            if not sig_a or not sig_b:
                continue

            route = DiffNormalizer.normalize_route(sig_a.normalized_route, self.config)
            canonical_subj = f"dom:{route}"

            # 1.1 DOM / Inventory Structure Signature Changed
            inv_a = sig_a.inventory_signature
            inv_b = sig_b.inventory_signature
            if self.config.enable_dom_diff and inv_a and inv_b and inv_a != inv_b:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.DOM,
                    kind=DifferenceKind.DOM_STRUCTURE_CHANGED,
                    canonical_subject=canonical_subj,
                    before_identity=inv_a,
                    after_identity=inv_b,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=inv_a,
                    after_value=inv_b,
                    state_a_id=sa.state_a_id,
                    state_b_id=sa.state_b_id,
                    observation_a_id=sa.observation_a_id,
                    observation_b_id=sa.observation_b_id,
                    details={"inventory_signature_a": inv_a, "inventory_signature_b": inv_b, "route": route},
                    comparison_completeness="signature_level",
                )
                differences.append(
                    InteractionDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.DOM,
                        kind=DifferenceKind.DOM_STRUCTURE_CHANGED,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=f"DOM interactive element hierarchy changed at route '{route}'.",
                        evidence=[evidence],
                    )
                )

            # 1.2 Interactive Element Counts
            count_a = sig_a.observational.interactive_elements_count
            count_b = sig_b.observational.interactive_elements_count
            if self.config.enable_interaction_diff and count_a != count_b:
                kind = (
                    DifferenceKind.INTERACTION_ELEMENT_ADDED
                    if count_b > count_a
                    else DifferenceKind.INTERACTION_ELEMENT_REMOVED
                )
                subj = f"interaction:{route}"
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.INTERACTION,
                    kind=kind,
                    canonical_subject=subj,
                    before_identity=str(count_a),
                    after_identity=str(count_b),
                )
                evidence = DifferenceEvidence(
                    canonical_subject=subj,
                    before_value=count_a,
                    after_value=count_b,
                    state_a_id=sa.state_a_id,
                    state_b_id=sa.state_b_id,
                    observation_a_id=sa.observation_a_id,
                    observation_b_id=sa.observation_b_id,
                    details={"elements_count_a": count_a, "elements_count_b": count_b, "route": route},
                )
                desc = (
                    f"Actionable element count increased at route '{route}': "
                    f"Version A had {count_a} element(s), Version B has {count_b} element(s)."
                    if count_b > count_a
                    else f"Actionable element count decreased at route '{route}': "
                    f"Version A had {count_a} element(s), Version B has {count_b} element(s)."
                )
                differences.append(
                    InteractionDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.INTERACTION,
                        kind=kind,
                        canonical_subject=subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=desc,
                        evidence=[evidence],
                    )
                )

        # 2. Action-level form/interactive attribute differences
        for ta in align.aligned_transitions:
            act_align = ta.action_alignment
            if not act_align or not act_align.signature_a or not act_align.signature_b:
                continue

            sig_a = act_align.signature_a
            sig_b = act_align.signature_b
            attrs_a = sig_a.semantic_attributes
            attrs_b = sig_b.semantic_attributes

            subj = f"action:{sig_a.stable_target_identity}"

            # 2.1 Form Required Flag Changed
            req_a = DiffNormalizer.normalize_attribute_value("required", attrs_a.get("is_required") or attrs_a.get("required"))
            req_b = DiffNormalizer.normalize_attribute_value("required", attrs_b.get("is_required") or attrs_b.get("required"))
            if req_a != req_b and (req_a or req_b):
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.DOM,
                    kind=DifferenceKind.FORM_REQUIRED_CHANGED,
                    canonical_subject=subj,
                    before_identity=req_a,
                    after_identity=req_b,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=subj,
                    before_value=req_a,
                    after_value=req_b,
                    action_a_id=act_align.action_a_id,
                    action_b_id=act_align.action_b_id,
                    transition_a_id=ta.transition_a_id,
                    transition_b_id=ta.transition_b_id,
                    details={"required_a": req_a, "required_b": req_b},
                )
                differences.append(
                    InteractionDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.DOM,
                        kind=DifferenceKind.FORM_REQUIRED_CHANGED,
                        canonical_subject=subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=f"Form required constraint changed for '{sig_a.stable_target_identity}': A={req_a}, B={req_b}.",
                        evidence=[evidence],
                    )
                )

            # 2.2 Disabled / Enabled State Changed
            dis_a = DiffNormalizer.normalize_attribute_value("disabled", attrs_a.get("disabled") or (not attrs_a.get("is_enabled", True)))
            dis_b = DiffNormalizer.normalize_attribute_value("disabled", attrs_b.get("disabled") or (not attrs_b.get("is_enabled", True)))
            if dis_a != dis_b and (dis_a or dis_b):
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.INTERACTION,
                    kind=DifferenceKind.ACTION_STATE_CHANGED,
                    canonical_subject=subj,
                    before_identity=dis_a,
                    after_identity=dis_b,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=subj,
                    before_value=dis_a,
                    after_value=dis_b,
                    action_a_id=act_align.action_a_id,
                    action_b_id=act_align.action_b_id,
                    transition_a_id=ta.transition_a_id,
                    transition_b_id=ta.transition_b_id,
                    details={"disabled_a": dis_a, "disabled_b": dis_b},
                )
                differences.append(
                    InteractionDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.INTERACTION,
                        kind=DifferenceKind.ACTION_STATE_CHANGED,
                        canonical_subject=subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=f"Actionable state changed for '{sig_a.stable_target_identity}': disabled A={dis_a}, B={dis_b}.",
                        evidence=[evidence],
                    )
                )

        return differences
