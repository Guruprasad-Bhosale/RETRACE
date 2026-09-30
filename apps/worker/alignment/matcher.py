"""Deterministic Feature-Based Matchers Module.

Implements structural matching for routes, actions, and states without arbitrary numeric thresholds.
Produces explicit AlignmentRelation and MatchEvidence.
"""

from urllib.parse import urlparse

from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.models import (
    ActionSignature,
    AlignmentRelation,
    EvidenceStrength,
    MatchEvidence,
    StateSignature,
)


class RouteMatcher:
    """Deterministic comparison engine for URL routes."""

    @staticmethod
    def match(route_a: str, route_b: str, config: AlignmentConfig) -> tuple[bool, str]:
        """Compare two route strings according to the configured route matching policy."""
        norm_a = route_a.strip()
        norm_b = route_b.strip()

        if norm_a == norm_b:
            return True, "exact"

        if config.route_matching_policy == "strip_query":
            path_a = urlparse(norm_a).path or "/"
            path_b = urlparse(norm_b).path or "/"
            if path_a == path_b:
                return True, "stripped_query"

        if config.route_matching_policy == "allow_aliases":
            for canonical, aliases in config.route_aliases.items():
                in_group_a = norm_a == canonical or norm_a in aliases
                in_group_b = norm_b == canonical or norm_b in aliases
                if in_group_a and in_group_b:
                    return True, "alias"

        return False, "mismatch"


class ActionMatcher:
    """Deterministic structural comparison between ActionSignatures."""

    @classmethod
    def match(
        cls,
        sig_a: ActionSignature | None,
        sig_b: ActionSignature | None,
    ) -> tuple[AlignmentRelation, MatchEvidence]:
        """Compare two action signatures using explicit feature hierarchy."""
        if not sig_a or not sig_b:
            return AlignmentRelation.UNMATCHED, MatchEvidence(
                evidence_strength=EvidenceStrength.NONE,
                matched_features=[],
                mismatched_features=["missing_signature"],
            )

        matched: list[str] = []
        mismatched: list[str] = []

        # 1. Action Type must match
        if sig_a.action_type == sig_b.action_type:
            matched.append(f"action_type:{sig_a.action_type.value}")
        else:
            mismatched.append("action_type")
            return AlignmentRelation.UNMATCHED, MatchEvidence(
                evidence_strength=EvidenceStrength.NONE,
                action_match=False,
                matched_features=matched,
                mismatched_features=mismatched,
            )

        # 2. Target identity
        target_exact = sig_a.stable_target_identity == sig_b.stable_target_identity
        if target_exact:
            matched.append(f"target:{sig_a.stable_target_identity}")
        else:
            mismatched.append("target_identity")

        # 3. Accessible Name
        name_exact = (
            sig_a.accessible_name
            and sig_b.accessible_name
            and sig_a.accessible_name.strip().lower() == sig_b.accessible_name.strip().lower()
        )
        if name_exact:
            matched.append(f"accessible_name:{sig_a.accessible_name}")
        elif sig_a.accessible_name != sig_b.accessible_name:
            mismatched.append("accessible_name")

        # 4. Normalized Input Class
        input_class_match = sig_a.normalized_input_class == sig_b.normalized_input_class
        if sig_a.normalized_input_class:
            if input_class_match:
                matched.append(f"input_class:{sig_a.normalized_input_class}")
            else:
                mismatched.append("input_class")

        # 5. Role / Tag
        role_match = sig_a.target_role == sig_b.target_role
        if sig_a.target_role and role_match:
            matched.append(f"role:{sig_a.target_role}")

        # Relation evaluation
        if target_exact and input_class_match:
            relation = AlignmentRelation.EXACT_MATCH
            strength = EvidenceStrength.EXACT
        elif target_exact:
            relation = AlignmentRelation.STRONG_MATCH
            strength = EvidenceStrength.STRONG
        elif name_exact and (role_match or not sig_a.target_role or not sig_b.target_role):
            relation = AlignmentRelation.STRONG_MATCH
            strength = EvidenceStrength.STRONG
        elif name_exact:
            relation = AlignmentRelation.PARTIAL_MATCH
            strength = EvidenceStrength.PARTIAL
        else:
            relation = AlignmentRelation.UNMATCHED
            strength = EvidenceStrength.NONE

        return relation, MatchEvidence(
            evidence_strength=strength,
            action_match=relation in (AlignmentRelation.EXACT_MATCH, AlignmentRelation.STRONG_MATCH),
            matched_features=matched,
            mismatched_features=mismatched,
        )


class StateMatcher:
    """Deterministic structural comparison between StateSignatures."""

    @classmethod
    def match(
        cls,
        sig_a: StateSignature,
        sig_b: StateSignature,
        config: AlignmentConfig,
        parent_match: bool = False,
        action_match: bool = False,
    ) -> tuple[AlignmentRelation, MatchEvidence]:
        """Compare two state signatures using explicit feature hierarchy."""
        matched: list[str] = []
        mismatched: list[str] = []

        # 1. Route match
        route_matched, route_type = RouteMatcher.match(
            sig_a.normalized_route,
            sig_b.normalized_route,
            config,
        )
        if route_matched:
            matched.append(f"route:{sig_a.normalized_route} ({route_type})")
        else:
            mismatched.append(f"route_diff:{sig_a.normalized_route}!={sig_b.normalized_route}")

        # 2. State ID match (projection equality)
        state_id_matched = sig_a.state_id == sig_b.state_id
        if state_id_matched:
            matched.append(f"state_id:{sig_a.state_id[:12]}")
        else:
            mismatched.append("state_id")

        # 3. Inventory signature match
        inv_matched = (
            bool(sig_a.inventory_signature)
            and sig_a.inventory_signature == sig_b.inventory_signature
        )
        if inv_matched:
            matched.append("inventory_signature")
        elif sig_a.inventory_signature != sig_b.inventory_signature:
            mismatched.append("inventory_signature")

        # 4. Accessibility signature match
        a11y_matched = (
            bool(sig_a.a11y_signature)
            and sig_a.a11y_signature == sig_b.a11y_signature
        )
        if a11y_matched:
            matched.append("a11y_signature")
        elif sig_a.a11y_signature != sig_b.a11y_signature:
            mismatched.append("a11y_signature")

        # 5. UI state signature match
        ui_matched = (
            bool(sig_a.ui_state_signature)
            and sig_a.ui_state_signature == sig_b.ui_state_signature
        )
        if ui_matched:
            matched.append("ui_state_signature")
        elif sig_a.ui_state_signature != sig_b.ui_state_signature:
            mismatched.append("ui_state_signature")

        if parent_match:
            matched.append("parent_state_aligned")
        if action_match:
            matched.append("incoming_action_aligned")

        # Decision Hierarchy
        if route_matched and state_id_matched:
            relation = AlignmentRelation.EXACT_MATCH
            strength = EvidenceStrength.EXACT
        elif route_matched and parent_match and action_match:
            relation = AlignmentRelation.STRONG_MATCH
            strength = EvidenceStrength.STRONG
        elif route_matched and (inv_matched or a11y_matched or ui_matched or parent_match):
            relation = AlignmentRelation.STRONG_MATCH
            strength = EvidenceStrength.STRONG
        elif route_matched:
            relation = AlignmentRelation.PARTIAL_MATCH
            strength = EvidenceStrength.PARTIAL
        elif parent_match and action_match and (inv_matched or a11y_matched):
            # Route divergence case where state was reached via identical parent and action
            relation = AlignmentRelation.PARTIAL_MATCH
            strength = EvidenceStrength.PARTIAL
        else:
            relation = AlignmentRelation.UNMATCHED
            strength = EvidenceStrength.NONE

        return relation, MatchEvidence(
            evidence_strength=strength,
            route_match=route_matched,
            parent_match=parent_match,
            action_match=action_match,
            inventory_match=inv_matched,
            accessibility_match=a11y_matched,
            matched_features=matched,
            mismatched_features=mismatched,
        )
