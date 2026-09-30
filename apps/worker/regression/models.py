"""Regression Classification Domain Models.

Provides strongly typed models for deterministic, evidence-backed regression candidate
classification between Version A and Version B without severity ranking or root cause inference.
"""

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ArtifactReference


class RegressionCategory(StrEnum):
    """Explicit semantic regression categories."""

    FUNCTIONAL = "FUNCTIONAL"
    NAVIGATION = "NAVIGATION"
    API_CONTRACT = "API_CONTRACT"
    STATE = "STATE"
    CALCULATION = "CALCULATION"
    ACCESSIBILITY = "ACCESSIBILITY"
    PERFORMANCE = "PERFORMANCE"
    UI_BEHAVIOR = "UI_BEHAVIOR"
    RUNTIME_ERROR = "RUNTIME_ERROR"
    UNKNOWN = "UNKNOWN"
    NON_REGRESSION = "NON_REGRESSION"


class ClassificationStatus(StrEnum):
    """Classification state for an evaluated difference."""

    REGRESSION_CANDIDATE = "REGRESSION_CANDIDATE"
    NON_REGRESSION = "NON_REGRESSION"
    UNCLASSIFIED = "UNCLASSIFIED"


class ClassificationEvidence(BaseModel):
    """Evidence lineage linking a regression classification directly to source differences and artifacts."""

    model_config = ConfigDict(extra="forbid")

    difference_id: str
    canonical_subject: str = Field(default="")
    observation_a_id: UUID | None = None
    observation_b_id: UUID | None = None
    state_a_id: str | None = None
    state_b_id: str | None = None
    action_a_id: str | None = None
    action_b_id: str | None = None
    transition_a_id: str | None = None
    transition_b_id: str | None = None
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class RuleEvaluation(BaseModel):
    """Internal result of evaluating a single deterministic rule against a semantic difference."""

    model_config = ConfigDict(extra="forbid")

    applicable: bool
    status: ClassificationStatus = ClassificationStatus.UNCLASSIFIED
    reason: str = ""
    evidence: ClassificationEvidence | None = None


def compute_deterministic_classification_id(
    difference_id: str,
    category: RegressionCategory,
    rule_id: str,
) -> str:
    """Compute deterministic SHA-256 slice ID based strictly on structural identifiers.

    Note: Timestamps and transient runtime metadata MUST NEVER participate in this hash.
    """
    raw = f"{difference_id}:{category.value}:{rule_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class RegressionClassification(BaseModel):
    """An evidence-linked classification of an observed difference by a deterministic rule."""

    model_config = ConfigDict(extra="forbid")

    classification_id: str
    difference_id: str
    status: ClassificationStatus
    category: RegressionCategory
    rule_id: str
    reason: str
    evidence: ClassificationEvidence
    # created_at is observational metadata ONLY and must never participate in classification_id, sorting, or equality
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def deterministic_sort_key(self) -> tuple[str, str, str, str]:
        """Stable sorting key excluding volatile timestamps."""
        return (
            self.category.value,
            self.status.value,
            self.rule_id,
            self.classification_id,
        )


class ClassificationSummary(BaseModel):
    """Statistical summary count of analyzed differences and resulting classifications."""

    model_config = ConfigDict(extra="forbid")

    total_differences_analyzed: int = 0
    regression_candidates: int = 0
    non_regressions: int = 0
    unclassified: int = 0
    candidates_by_category: dict[RegressionCategory, int] = Field(default_factory=dict)


class RegressionClassificationResult(BaseModel):
    """Top-level immutable container holding all regression classifications and diagnostics."""

    model_config = ConfigDict(extra="forbid")

    run_a_id: UUID
    run_b_id: UUID
    trajectory_a_id: UUID
    trajectory_b_id: UUID
    classifications: list[RegressionClassification] = Field(default_factory=list)
    summary: ClassificationSummary = Field(default_factory=ClassificationSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
