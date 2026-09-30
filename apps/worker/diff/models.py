"""Semantic Difference Domain Models.

Provides strongly typed models for deterministic, evidence-backed semantic difference
representation between Version A and Version B without regression classification.
"""

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ArtifactReference


class DifferenceCategory(StrEnum):
    """Explicit structural categories of observed differences."""

    STATE = "STATE"
    ROUTE = "ROUTE"
    ACTION = "ACTION"
    TRANSITION = "TRANSITION"
    DOM = "DOM"
    ACCESSIBILITY = "ACCESSIBILITY"
    INTERACTION = "INTERACTION"
    NETWORK = "NETWORK"
    CONSOLE = "CONSOLE"
    PERFORMANCE = "PERFORMANCE"


class DifferenceKind(StrEnum):
    """Deterministic, granular semantic change kinds."""

    # Route
    ROUTE_ADDED = "ROUTE_ADDED"
    ROUTE_REMOVED = "ROUTE_REMOVED"
    ROUTE_CHANGED = "ROUTE_CHANGED"
    ROUTE_TARGET_CHANGED = "ROUTE_TARGET_CHANGED"

    # State
    STATE_ONLY_IN_A = "STATE_ONLY_IN_A"
    STATE_ONLY_IN_B = "STATE_ONLY_IN_B"
    STATE_AMBIGUOUS = "STATE_AMBIGUOUS"
    HTTP_STATUS_CHANGED = "HTTP_STATUS_CHANGED"
    PAGE_TITLE_CHANGED = "PAGE_TITLE_CHANGED"
    STATE_STRUCTURE_CHANGED = "STATE_STRUCTURE_CHANGED"

    # DOM
    DOM_STRUCTURE_CHANGED = "DOM_STRUCTURE_CHANGED"
    DOM_TEXT_CHANGED = "DOM_TEXT_CHANGED"
    DOM_ATTRIBUTE_CHANGED = "DOM_ATTRIBUTE_CHANGED"
    DOM_FORM_STATE_CHANGED = "DOM_FORM_STATE_CHANGED"
    DOM_ELEMENT_ADDED = "DOM_ELEMENT_ADDED"
    DOM_ELEMENT_REMOVED = "DOM_ELEMENT_REMOVED"

    # Form & Interactive State
    FORM_VALUE_CHANGED = "FORM_VALUE_CHANGED"
    FORM_REQUIRED_CHANGED = "FORM_REQUIRED_CHANGED"
    FORM_DISABLED_CHANGED = "FORM_DISABLED_CHANGED"
    FORM_CHECKED_CHANGED = "FORM_CHECKED_CHANGED"
    ACTION_ADDED = "ACTION_ADDED"
    ACTION_REMOVED = "ACTION_REMOVED"
    ACTION_TARGET_CHANGED = "ACTION_TARGET_CHANGED"
    ACTION_NAME_CHANGED = "ACTION_NAME_CHANGED"
    ACTION_INPUT_BEHAVIOR_CHANGED = "ACTION_INPUT_BEHAVIOR_CHANGED"
    ACTION_STATE_CHANGED = "ACTION_STATE_CHANGED"
    INTERACTION_ELEMENT_ADDED = "INTERACTION_ELEMENT_ADDED"
    INTERACTION_ELEMENT_REMOVED = "INTERACTION_ELEMENT_REMOVED"

    # Transition
    TRANSITION_ONLY_IN_A = "TRANSITION_ONLY_IN_A"
    TRANSITION_ONLY_IN_B = "TRANSITION_ONLY_IN_B"
    TRANSITION_TARGET_CHANGED = "TRANSITION_TARGET_CHANGED"
    TRANSITION_ACTION_CHANGED = "TRANSITION_ACTION_CHANGED"
    TRANSITION_AMBIGUOUS = "TRANSITION_AMBIGUOUS"

    # Accessibility
    A11Y_STRUCTURE_CHANGED = "A11Y_STRUCTURE_CHANGED"
    A11Y_ROLE_CHANGED = "A11Y_ROLE_CHANGED"
    A11Y_NAME_CHANGED = "A11Y_NAME_CHANGED"
    A11Y_STATE_CHANGED = "A11Y_STATE_CHANGED"
    A11Y_LABEL_CHANGED = "A11Y_LABEL_CHANGED"

    # Network
    NETWORK_REQUEST_ADDED = "NETWORK_REQUEST_ADDED"
    NETWORK_REQUEST_REMOVED = "NETWORK_REQUEST_REMOVED"
    NETWORK_METHOD_CHANGED = "NETWORK_METHOD_CHANGED"
    NETWORK_STATUS_CHANGED = "NETWORK_STATUS_CHANGED"
    NETWORK_RESOURCE_TYPE_CHANGED = "NETWORK_RESOURCE_TYPE_CHANGED"
    NETWORK_FAILURE_CHANGED = "NETWORK_FAILURE_CHANGED"
    NETWORK_TIMING_CHANGED = "NETWORK_TIMING_CHANGED"

    # Console
    CONSOLE_ERROR_ADDED = "CONSOLE_ERROR_ADDED"
    CONSOLE_ERROR_REMOVED = "CONSOLE_ERROR_REMOVED"
    CONSOLE_WARNING_CHANGED = "CONSOLE_WARNING_CHANGED"
    PAGE_ERROR_ADDED = "PAGE_ERROR_ADDED"

    # Performance
    NAVIGATION_DURATION_CHANGED = "NAVIGATION_DURATION_CHANGED"
    NETWORK_DURATION_CHANGED = "NETWORK_DURATION_CHANGED"
    RESOURCE_TIMING_CHANGED = "RESOURCE_TIMING_CHANGED"
    STABILIZATION_DURATION_CHANGED = "STABILIZATION_DURATION_CHANGED"


class ComparisonStatus(StrEnum):
    """Quality and feasibility state of semantic comparison."""

    COMPARED = "COMPARED"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class DifferenceEvidence(BaseModel):
    """Authoritative, verifiable evidence lineage supporting a semantic difference."""

    model_config = ConfigDict(extra="forbid")

    canonical_subject: str = Field(
        default="",
        description="Normalized entity identifier (e.g. route, element ID, transition path).",
    )
    before_value: Any | None = None
    after_value: Any | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    observation_a_id: UUID | None = None
    observation_b_id: UUID | None = None
    state_a_id: str | None = None
    state_b_id: str | None = None
    action_a_id: str | None = None
    action_b_id: str | None = None
    transition_a_id: str | None = None
    transition_b_id: str | None = None
    source_state_id: str | None = None
    target_state_id: str | None = None
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    comparison_completeness: str = Field(
        default="full",
        description="Indicates whether comparison was full, partial, or fallback.",
    )
    evidence_availability: str = Field(
        default="available",
        description="Availability status of the underlying evidence sensor.",
    )


def compute_deterministic_diff_id(
    category: DifferenceCategory,
    kind: DifferenceKind,
    canonical_subject: str,
    before_identity: str = "",
    after_identity: str = "",
) -> str:
    """Compute deterministic SHA-256 slice ID based strictly on structural identifiers.

    Note: Timestamps and transient execution metadata MUST NEVER participate in this hash.
    """
    raw = f"{category.value}:{kind.value}:{canonical_subject}:{before_identity}:{after_identity}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class SemanticDifference(BaseModel):
    """A distinct observable semantic difference between Version A and Version B."""

    model_config = ConfigDict(extra="forbid")

    diff_id: str
    category: DifferenceCategory
    kind: DifferenceKind
    canonical_subject: str
    comparison_status: ComparisonStatus = ComparisonStatus.COMPARED
    description: str
    evidence: list[DifferenceEvidence] = Field(default_factory=list)
    # created_at is observational metadata ONLY and must never participate in diff_id, sorting, or equality
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def deterministic_sort_key(self) -> tuple[str, str, str, str]:
        """Stable sorting key excluding volatile timestamps."""
        return (
            self.category.value,
            self.kind.value,
            self.canonical_subject,
            self.diff_id,
        )


class StateDifference(SemanticDifference):
    """Typed semantic difference occurring at the state level."""


class TransitionDifference(SemanticDifference):
    """Typed semantic difference occurring at the transition level."""


class ActionDifference(SemanticDifference):
    """Typed semantic difference occurring at the action/interaction level."""


class RouteDifference(SemanticDifference):
    """Typed semantic difference occurring at the route level."""


class NetworkDifference(SemanticDifference):
    """Typed semantic difference occurring in network interactions."""


class ConsoleDifference(SemanticDifference):
    """Typed semantic difference occurring in console and error logs."""


class AccessibilityDifference(SemanticDifference):
    """Typed semantic difference occurring in accessibility structures."""


class InteractionDifference(SemanticDifference):
    """Typed semantic difference occurring in actionable DOM elements."""


class PerformanceDifference(SemanticDifference):
    """Typed semantic difference occurring in execution timings."""


class SemanticDiffSummary(BaseModel):
    """Neutral statistical overview of compared entities and detected differences."""

    model_config = ConfigDict(extra="forbid")

    states_compared: int = 0
    states_only_in_a: int = 0
    states_only_in_b: int = 0
    states_ambiguous: int = 0
    actions_compared: int = 0
    transitions_compared: int = 0
    transitions_only_in_a: int = 0
    transitions_only_in_b: int = 0
    routes_compared: int = 0
    dom_differences: int = 0
    accessibility_differences: int = 0
    interaction_differences: int = 0
    network_differences: int = 0
    console_differences: int = 0
    performance_differences: int = 0
    total_differences: int = 0


class SemanticDiffResult(BaseModel):
    """Top-level immutable container holding all semantic differences and statistics."""

    model_config = ConfigDict(extra="forbid")

    run_a_id: UUID
    run_b_id: UUID
    trajectory_a_id: UUID
    trajectory_b_id: UUID
    differences: list[SemanticDifference] = Field(default_factory=list)
    summary: SemanticDiffSummary = Field(default_factory=SemanticDiffSummary)
    comparison_statistics: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
