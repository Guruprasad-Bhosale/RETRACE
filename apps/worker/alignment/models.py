"""Alignment Domain Models.

Core models representing deterministic structural alignment between Version A and Version B
exploration graphs, behavioral trajectories, states, actions, transitions, and evidence-backed divergences.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ActionType, ArtifactReference


class AlignmentRelation(StrEnum):
    """Deterministic structural relation between two entities."""

    EXACT_MATCH = "EXACT_MATCH"
    STRONG_MATCH = "STRONG_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    AMBIGUOUS = "AMBIGUOUS"
    UNMATCHED = "UNMATCHED"


class EvidenceStrength(StrEnum):
    """Deterministic strength of matching evidence."""

    EXACT = "EXACT"
    STRONG = "STRONG"
    PARTIAL = "PARTIAL"
    NONE = "NONE"


class DivergenceType(StrEnum):
    """Types of neutral observed divergences between Version A and Version B."""

    ROUTE_DIVERGENCE = "ROUTE_DIVERGENCE"
    ACTION_DIVERGENCE = "ACTION_DIVERGENCE"
    STATE_DIVERGENCE = "STATE_DIVERGENCE"
    TRANSITION_DIVERGENCE = "TRANSITION_DIVERGENCE"
    MISSING_STATE = "MISSING_STATE"
    ADDITIONAL_STATE = "ADDITIONAL_STATE"
    MISSING_ACTION = "MISSING_ACTION"
    ADDITIONAL_ACTION = "ADDITIONAL_ACTION"
    HTTP_STATUS_DIVERGENCE = "HTTP_STATUS_DIVERGENCE"
    CONSOLE_ERROR_DIVERGENCE = "CONSOLE_ERROR_DIVERGENCE"
    OBSERVATIONAL_DIVERGENCE = "OBSERVATIONAL_DIVERGENCE"


class MatchEvidence(BaseModel):
    """Structural evidence supporting an alignment or ambiguity decision."""

    model_config = ConfigDict(extra="forbid")

    evidence_strength: EvidenceStrength = EvidenceStrength.NONE
    route_match: bool = False
    parent_match: bool = False
    action_match: bool = False
    inventory_match: bool = False
    accessibility_match: bool = False
    matched_features: list[str] = Field(default_factory=list)
    mismatched_features: list[str] = Field(default_factory=list)
    ambiguity_candidates: list[str] = Field(
        default_factory=list,
        description="Candidate IDs when multiple candidates have equal evidence.",
    )


class ActionSignature(BaseModel):
    """Deterministic normalized signature representing an interactive action."""

    model_config = ConfigDict(extra="forbid")

    action_type: ActionType
    stable_target_identity: str
    target_role: str | None = None
    accessible_name: str | None = None
    semantic_attributes: dict[str, str] = Field(default_factory=dict)
    normalized_input_class: str | None = None
    raw_target: str = ""

    def compute_signature_hash(self) -> str:
        """Deterministic string representation for exact signature lookup."""
        attrs = ",".join(f"{k}={v}" for k, v in sorted(self.semantic_attributes.items()))
        return (
            f"type={self.action_type.value}|target={self.stable_target_identity}|"
            f"role={self.target_role or ''}|name={self.accessible_name or ''}|"
            f"input_class={self.normalized_input_class or ''}|attrs={attrs}"
        )


class StateObservationalFeatures(BaseModel):
    """Observational state features used for divergence detection, strictly separated from identity."""

    model_config = ConfigDict(extra="forbid")

    http_status: int | None = None
    page_title: str | None = None
    console_errors_count: int = 0
    network_failures_count: int = 0
    interactive_elements_count: int = 0


class StateSignature(BaseModel):
    """Deterministic structural state signature separating identity features from observational features."""

    model_config = ConfigDict(extra="forbid")

    state_id: str
    normalized_route: str
    inventory_signature: str
    a11y_signature: str
    ui_state_signature: str
    observational: StateObservationalFeatures = Field(default_factory=StateObservationalFeatures)


class ActionAlignment(BaseModel):
    """Structural alignment between an action in Version A and an action in Version B."""

    model_config = ConfigDict(extra="forbid")

    action_a_id: str | None = None
    action_b_id: str | None = None
    signature_a: ActionSignature | None = None
    signature_b: ActionSignature | None = None
    relation: AlignmentRelation
    evidence: MatchEvidence


class StateAlignment(BaseModel):
    """Structural alignment between a state in Version A and a state in Version B."""

    model_config = ConfigDict(extra="forbid")

    state_a_id: str | None = None
    state_b_id: str | None = None
    observation_a_id: UUID | None = None
    observation_b_id: UUID | None = None
    signature_a: StateSignature | None = None
    signature_b: StateSignature | None = None
    relation: AlignmentRelation
    evidence: MatchEvidence


class TransitionAlignment(BaseModel):
    """Structural alignment between a directed transition in Version A and Version B."""

    model_config = ConfigDict(extra="forbid")

    transition_a_id: str | None = None
    transition_b_id: str | None = None
    from_state_a_id: str | None = None
    from_state_b_id: str | None = None
    to_state_a_id: str | None = None
    to_state_b_id: str | None = None
    action_alignment: ActionAlignment | None = None
    relation: AlignmentRelation
    evidence: MatchEvidence


class Divergence(BaseModel):
    """Neutral, evidence-backed observation divergence between Version A and Version B."""

    model_config = ConfigDict(extra="forbid")

    divergence_id: str
    divergence_type: DivergenceType
    description: str
    state_a_id: str | None = None
    state_b_id: str | None = None
    observation_a_id: UUID | None = None
    observation_b_id: UUID | None = None
    action_a_id: str | None = None
    action_b_id: str | None = None
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TrajectoryAlignment(BaseModel):
    """Complete structural alignment between Version A and Version B exploration trajectories."""

    model_config = ConfigDict(extra="forbid")

    aligned_states: list[StateAlignment] = Field(default_factory=list)
    aligned_transitions: list[TransitionAlignment] = Field(default_factory=list)
    unmatched_a_states: list[str] = Field(default_factory=list)
    unmatched_b_states: list[str] = Field(default_factory=list)
    ambiguous_states: list[StateAlignment] = Field(default_factory=list)
    unmatched_a_transitions: list[str] = Field(default_factory=list)
    unmatched_b_transitions: list[str] = Field(default_factory=list)
    divergences: list[Divergence] = Field(default_factory=list)
    unique_routes_a: list[str] = Field(default_factory=list)
    unique_routes_b: list[str] = Field(default_factory=list)
    aligned_routes_count: int = 0


class AlignmentResult(BaseModel):
    """Top-level container holding exploration results, alignment topology, and diagnostics."""

    model_config = ConfigDict(extra="forbid")

    run_a_id: UUID
    run_b_id: UUID
    trajectory_a_id: UUID
    trajectory_b_id: UUID
    alignment: TrajectoryAlignment
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
