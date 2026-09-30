"""Investigation Assembly Domain Models.

Provides authoritative models for complete, developer-usable RETRACE investigation packages
unifying Phase 7 classification, Phase 8 reproduction, Phase 9 root cause, and Phase 10 synthesis/reporting.
"""

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.regression.models import RegressionClassification
from apps.worker.reporting.models import EvidenceReport
from apps.worker.reproduction.models import ReproductionResult
from apps.worker.rootcause.models import RootCauseResult
from apps.worker.synthesis.models import GeneratedTest
from packages.domain.models import ArtifactReference


class InvestigationStatus(StrEnum):
    """Overall status of an end-to-end investigation."""

    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAILED = "FAILED"


class InvestigationProvenance(BaseModel):
    """Unified multi-phase provenance for an investigation package."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: UUID
    classification_id: str
    difference_id: str
    reproduction_id: str | None = None
    root_cause_id: str | None = None
    test_id: str | None = None
    report_id: str | None = None
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def compute_deterministic_investigation_id(
    analysis_id: UUID,
    classification_id: str,
    difference_id: str,
) -> str:
    """Compute deterministic SHA-256 slice ID for an investigation package."""
    raw = f"{analysis_id}:{classification_id}:{difference_id}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class InvestigationResult(BaseModel):
    """Complete, developer-usable engineering investigation package."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: str
    analysis_id: UUID
    regression_id: str
    classification: RegressionClassification
    reproduction: ReproductionResult | None = None
    root_cause: RootCauseResult | None = None
    generated_test: GeneratedTest | None = None
    report: EvidenceReport
    artifacts: list[ArtifactReference] = Field(default_factory=list)
    provenance: InvestigationProvenance
    status: InvestigationStatus
    metadata: dict[str, Any] = Field(default_factory=dict)
    # created_at is observational metadata ONLY and must never participate in investigation_id or sorting
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def deterministic_sort_key(self) -> tuple[str, str, str]:
        """Stable sorting key excluding timestamps."""
        return (
            self.status.value,
            self.regression_id,
            self.investigation_id,
        )


class InvestigationSummary(BaseModel):
    """Statistical summary count of investigated regressions."""

    model_config = ConfigDict(extra="forbid")

    total_investigations: int = 0
    completed_count: int = 0
    partial_count: int = 0
    inconclusive_count: int = 0
    failed_count: int = 0


class InvestigationSuiteResult(BaseModel):
    """Top-level container holding all investigation packages for an analysis session."""

    model_config = ConfigDict(extra="forbid")

    analysis_id: UUID
    run_a_id: UUID
    run_b_id: UUID
    investigations: list[InvestigationResult] = Field(default_factory=list)
    summary: InvestigationSummary = Field(default_factory=InvestigationSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
