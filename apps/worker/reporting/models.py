"""Evidence Reporting Domain Models.

Provides strongly typed models for evidence-backed investigation reports,
unbroken causal chains, structured report sections, and deterministic export formats.
"""

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ArtifactReference


class ReportStatus(StrEnum):
    """Overall status of an evidence investigation report."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    EVIDENCE_INSUFFICIENT = "EVIDENCE_INSUFFICIENT"


class ReportFormat(StrEnum):
    """Supported export formats for evidence reports."""

    MARKDOWN = "MARKDOWN"
    JSON = "JSON"


class EvidenceNodeType(StrEnum):
    """Semantic node type within the unbroken causal evidence chain."""

    OBSERVED_DIFFERENCE = "OBSERVED_DIFFERENCE"
    REGRESSION_CLASSIFICATION = "REGRESSION_CLASSIFICATION"
    REPRODUCTION_REPLAY = "REPRODUCTION_REPLAY"
    ROOT_CAUSE_LOCALIZATION = "ROOT_CAUSE_LOCALIZATION"
    CHANGED_SOURCE_REGION = "CHANGED_SOURCE_REGION"
    GIT_DIFF_HUNK = "GIT_DIFF_HUNK"
    COMMIT_ATTRIBUTION = "COMMIT_ATTRIBUTION"
    SYNTHESIZED_TEST = "SYNTHESIZED_TEST"


class EvidenceChainNode(BaseModel):
    """A verifiable node in the causal lineage graph connecting observation to source code."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: EvidenceNodeType
    title: str
    phase_origin: str = Field(description="Origin phase, e.g. Phase 6, Phase 7, Phase 8, Phase 9, Phase 10")
    status: str
    evidence_ids: list[str] = Field(default_factory=list)
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)


class EvidenceChain(BaseModel):
    """Ordered sequence of verifiable evidence nodes forming the causal attribution path."""

    model_config = ConfigDict(extra="forbid")

    chain_id: str
    nodes: list[EvidenceChainNode] = Field(default_factory=list)
    root_node_id: str | None = None
    leaf_node_id: str | None = None


class ReportSection(BaseModel):
    """A structured, numbered section within the comprehensive investigation report."""

    model_config = ConfigDict(extra="forbid")

    section_id: str
    section_number: int = Field(ge=1)
    title: str
    content_markdown: str
    evidence_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReportProvenance(BaseModel):
    """Provenance tracking for the generated report and underlying evidence."""

    model_config = ConfigDict(extra="forbid")

    classification_id: str
    difference_id: str
    reproduction_id: str | None = None
    root_cause_id: str | None = None
    test_id: str | None = None
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def compute_deterministic_report_id(
    classification_id: str,
    difference_id: str,
    reproduction_id: str | None,
    root_cause_id: str | None,
    test_id: str | None,
) -> str:
    """Compute deterministic SHA-256 slice ID based strictly on structural upstream identifiers."""
    raw = f"{classification_id}:{difference_id}:{reproduction_id or ''}:{root_cause_id or ''}:{test_id or ''}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class EvidenceReport(BaseModel):
    """Complete evidence-backed engineering investigation report."""

    model_config = ConfigDict(extra="forbid")

    report_id: str
    investigation_id: str | None = None
    regression_id: str
    title: str
    status: ReportStatus
    summary: str
    sections: list[ReportSection] = Field(default_factory=list)
    evidence_chain: EvidenceChain
    markdown_content: str
    json_content: dict[str, Any] = Field(default_factory=dict)
    provenance: ReportProvenance
    metadata: dict[str, Any] = Field(default_factory=dict)
    # created_at is observational metadata ONLY and must never participate in report_id or sorting
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def deterministic_sort_key(self) -> tuple[str, str]:
        """Stable sorting key excluding timestamps."""
        return (
            self.status.value,
            self.report_id,
        )


class ReportSummary(BaseModel):
    """Statistical summary of generated reports."""

    model_config = ConfigDict(extra="forbid")

    total_reports_generated: int = 0
    complete_count: int = 0
    partial_count: int = 0
    insufficient_evidence_count: int = 0


class ReportSuiteResult(BaseModel):
    """Top-level immutable container for all evidence reports generated in an analysis run."""

    model_config = ConfigDict(extra="forbid")

    run_a_id: UUID
    run_b_id: UUID
    reports: list[EvidenceReport] = Field(default_factory=list)
    summary: ReportSummary = Field(default_factory=ReportSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
