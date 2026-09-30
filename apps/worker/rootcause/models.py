"""Root Cause Localization & Code/Commit Attribution Domain Models.

Provides strongly typed models for deterministic source location mapping,
AST representation, unified diff normalization, commit attribution, and provenance.
"""

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ArtifactReference


class RootCauseStatus(StrEnum):
    """Formal status of root cause localization."""

    LOCATED = "LOCATED"
    PARTIALLY_LOCATED = "PARTIALLY_LOCATED"
    CANDIDATE_ONLY = "CANDIDATE_ONLY"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNSUPPORTED = "UNSUPPORTED"


class FileChangeType(StrEnum):
    """Category of file-level difference."""

    FILE_ADDED = "FILE_ADDED"
    FILE_DELETED = "FILE_DELETED"
    FILE_MODIFIED = "FILE_MODIFIED"
    FILE_RENAMED = "FILE_RENAMED"
    FILE_COPIED = "FILE_COPIED"


class LineChangeType(StrEnum):
    """Line-level diff modification category."""

    LINE_ADDED = "LINE_ADDED"
    LINE_DELETED = "LINE_DELETED"
    LINE_CONTEXT = "LINE_CONTEXT"


class SymbolChangeType(StrEnum):
    """AST symbol-level difference."""

    SYMBOL_ADDED = "SYMBOL_ADDED"
    SYMBOL_DELETED = "SYMBOL_DELETED"
    SYMBOL_MODIFIED = "SYMBOL_MODIFIED"
    SYMBOL_MOVED = "SYMBOL_MOVED"
    SYMBOL_UNCHANGED = "SYMBOL_UNCHANGED"


class LanguageType(StrEnum):
    """Supported source code languages."""

    PYTHON = "PYTHON"
    JAVASCRIPT = "JAVASCRIPT"
    TYPESCRIPT = "TYPESCRIPT"
    HTML = "HTML"
    CSS = "CSS"
    JSON = "JSON"
    UNSUPPORTED_LANGUAGE = "UNSUPPORTED_LANGUAGE"


class ASTNodeType(StrEnum):
    """High-level semantic AST node classifications."""

    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    CLASS = "CLASS"
    COMPONENT = "COMPONENT"
    ROUTE_HANDLER = "ROUTE_HANDLER"
    API_CALL = "API_CALL"
    CALCULATION = "CALCULATION"
    STATE_MUTATION = "STATE_MUTATION"
    DOM_BINDING = "DOM_BINDING"
    CONFIGURATION = "CONFIGURATION"
    IMPORT = "IMPORT"
    EXPRESSION = "EXPRESSION"
    STATEMENT = "STATEMENT"
    UNKNOWN = "UNKNOWN"


class AttributionRelationshipType(StrEnum):
    """Explicit causal relationship between behavioral regression and source change."""

    DIRECTLY_CHANGED = "DIRECTLY_CHANGED"
    AFFECTED_SYMBOL = "AFFECTED_SYMBOL"
    AFFECTED_CALL_SITE = "AFFECTED_CALL_SITE"
    AFFECTED_ROUTE = "AFFECTED_ROUTE"
    AFFECTED_CONFIGURATION = "AFFECTED_CONFIGURATION"
    ANCESTOR_CHANGE = "ANCESTOR_CHANGE"
    RELATED_CHANGE = "RELATED_CHANGE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class CommitAttributionType(StrEnum):
    """Commit linkage classification distinguishing source-history from causal attribution."""

    CAUSAL_COMMIT = "CAUSAL_COMMIT"  # Strong behavioral + source evidence supports causality
    INTRODUCING_COMMIT = "INTRODUCING_COMMIT"  # Introduced or modified relevant source lines in Git
    MODIFYING_COMMIT = "MODIFYING_COMMIT"  # Touched the file in the investigated commit range
    RELATED_COMMIT = "RELATED_COMMIT"  # Co-occurring commit in the investigated range
    NO_ATTRIBUTABLE_COMMIT = "NO_ATTRIBUTABLE_COMMIT"


# ------------------------------------------------------------------------------
# Core Structural & Source Code Models
# ------------------------------------------------------------------------------


class SourceLocation(BaseModel):
    """Canonical, reproducible source code location."""

    model_config = ConfigDict(extra="forbid")

    repository_path: str = Field(default="")
    commit_hash: str | None = None
    file_path: str
    symbol_name: str | None = None
    symbol_kind: ASTNodeType | None = None
    start_line: int = Field(ge=1, description="1-indexed starting line")
    start_column: int = Field(default=0, ge=0, description="0-indexed starting column")
    end_line: int = Field(ge=1, description="1-indexed ending line (inclusive)")
    end_column: int = Field(default=0, ge=0, description="0-indexed ending column")
    snippet: str | None = None

    def deterministic_key(self) -> str:
        """Deterministic string key for sorting and identity."""
        return f"{self.file_path}:{self.start_line}-{self.end_line}:{self.symbol_name or ''}"


class DiffLine(BaseModel):
    """A single line inside a diff hunk with line number mappings."""

    model_config = ConfigDict(extra="forbid")

    change_type: LineChangeType
    content: str
    old_line_number: int | None = None
    new_line_number: int | None = None


class DiffHunk(BaseModel):
    """Normalized unified diff hunk representation with line number mappings."""

    model_config = ConfigDict(extra="forbid")

    old_start: int = Field(ge=0)
    old_lines: int = Field(ge=0)
    new_start: int = Field(ge=0)
    new_lines: int = Field(ge=0)
    header: str = ""
    lines: list[DiffLine] = Field(default_factory=list)
    added_lines: list[int] = Field(default_factory=list)
    deleted_lines: list[int] = Field(default_factory=list)


class FileDiff(BaseModel):
    """Normalized file-level diff representation."""

    model_config = ConfigDict(extra="forbid")

    change_type: FileChangeType
    old_path: str | None = None
    new_path: str | None = None
    hunks: list[DiffHunk] = Field(default_factory=list)
    is_binary: bool = False
    language: LanguageType = LanguageType.UNSUPPORTED_LANGUAGE

    def primary_path(self) -> str:
        """Return the relevant target path (or old path if deleted)."""
        return self.new_path or self.old_path or ""


class CommitMetadata(BaseModel):
    """Structured read-only Git commit metadata."""

    model_config = ConfigDict(extra="forbid")

    commit_hash: str
    author_name: str = ""
    author_email: str = ""
    timestamp: str = ""
    message: str = ""
    parent_hashes: list[str] = Field(default_factory=list)
    is_merge: bool = False


class ASTSymbol(BaseModel):
    """Structured AST symbol declaration or definition."""

    model_config = ConfigDict(extra="forbid")

    name: str
    kind: ASTNodeType
    location: SourceLocation
    parent_symbol: str | None = None
    parameters: list[str] = Field(default_factory=list)
    docstring: str | None = None
    route_path: str | None = None
    http_methods: list[str] = Field(default_factory=list)
    state_keys: list[str] = Field(default_factory=list)


class RepositoryContext(BaseModel):
    """Explicit representation of analyzed repository boundaries and versions."""

    model_config = ConfigDict(extra="forbid")

    repository_id: str = "default"
    repository_path: str | None = None
    version_a_path: str | None = None
    version_b_path: str | None = None
    baseline_ref: str | None = None
    target_ref: str | None = None
    is_git_repository: bool = False
    commits: list[CommitMetadata] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# Attribution & Provenance Models
# ------------------------------------------------------------------------------


class AttributionEvidence(BaseModel):
    """Causal evidence linking behavioral regression to a concrete source change."""

    model_config = ConfigDict(extra="forbid")

    source_location: SourceLocation
    relationship_type: AttributionRelationshipType
    classification_id: str
    difference_id: str
    reproduction_id: str | None = None
    reproduction_observation_ids: list[UUID] = Field(default_factory=list)
    diff_hunk: DiffHunk | None = None
    commit_evidence: CommitMetadata | None = None
    commit_attribution_type: CommitAttributionType = CommitAttributionType.NO_ATTRIBUTABLE_COMMIT
    explanation: str
    details: dict[str, Any] = Field(default_factory=dict)


def compute_deterministic_attribution_id(
    classification_id: str,
    file_path: str,
    start_line: int,
    end_line: int,
    relationship_type: AttributionRelationshipType,
) -> str:
    """Compute deterministic SHA-256 slice ID based strictly on structural attribution data."""
    raw = f"{classification_id}:{file_path}:{start_line}:{end_line}:{relationship_type.value}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class RootCauseAttribution(BaseModel):
    """Detailed attribution binding for a localized source change."""

    model_config = ConfigDict(extra="forbid")

    attribution_id: str
    source_location: SourceLocation
    affected_symbol: ASTSymbol | None = None
    relationship_type: AttributionRelationshipType
    commit: CommitMetadata | None = None
    commit_attribution_type: CommitAttributionType = CommitAttributionType.NO_ATTRIBUTABLE_COMMIT
    diff_hunk: DiffHunk | None = None
    explanation: str
    evidence: list[AttributionEvidence] = Field(default_factory=list)

    def deterministic_sort_key(self) -> tuple[str, str, int, str]:
        """Stable sorting key excluding timestamps."""
        return (
            self.relationship_type.value,
            self.source_location.file_path,
            self.source_location.start_line,
            self.attribution_id,
        )


class ComparativeBehavioralEvidence(BaseModel):
    """Historical comparative observations captured in Phases 4-7."""

    model_config = ConfigDict(extra="forbid")

    classification_id: str
    difference_id: str
    historical_observation_ids: list[UUID] = Field(default_factory=list)
    artifact_references: list[ArtifactReference] = Field(default_factory=list)


class FreshReproductionEvidence(BaseModel):
    """Fresh replay observations captured in Phase 8."""

    model_config = ConfigDict(extra="forbid")

    reproduction_id: str | None = None
    fresh_observation_ids: list[UUID] = Field(default_factory=list)
    reproduced: bool = False


class SourceHistoryEvidence(BaseModel):
    """Authoritative source code changes, diffs, and Git commit metadata captured in Phase 9."""

    model_config = ConfigDict(extra="forbid")

    repository_path: str = ""
    baseline_ref: str | None = None
    target_ref: str | None = None
    commit_hashes: list[str] = Field(default_factory=list)
    diff_files_count: int = 0


class RootCauseProvenance(BaseModel):
    """Immutable provenance record establishing full origin lineage across all phases with strict evidence segregation."""

    model_config = ConfigDict(extra="forbid")

    classification_id: str
    difference_id: str
    reproduction_id: str | None = None
    comparative_evidence: ComparativeBehavioralEvidence | None = None
    reproduction_evidence: FreshReproductionEvidence | None = None
    source_history_evidence: SourceHistoryEvidence | None = None
    historical_observation_ids: list[UUID] = Field(default_factory=list)
    fresh_reproduction_observation_ids: list[UUID] = Field(default_factory=list)
    artifact_references: list[ArtifactReference] = Field(default_factory=list)
    repository_path: str = ""
    baseline_ref: str | None = None
    target_ref: str | None = None
    commit_hashes: list[str] = Field(default_factory=list)
    analyzed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


def compute_deterministic_root_cause_id(
    classification_id: str,
    difference_id: str,
    status: RootCauseStatus,
    primary_location_key: str = "",
) -> str:
    """Compute deterministic SHA-256 slice ID based strictly on structural identifiers."""
    raw = f"{classification_id}:{difference_id}:{status.value}:{primary_location_key}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class RootCauseResult(BaseModel):
    """Complete authoritative outcome of localizing root cause for a regression."""

    model_config = ConfigDict(extra="forbid")

    root_cause_id: str
    classification_id: str
    difference_id: str
    reproduction_id: str | None = None
    category: str
    status: RootCauseStatus
    primary_attribution: RootCauseAttribution | None = None
    attributions: list[RootCauseAttribution] = Field(default_factory=list)
    candidate_locations: list[SourceLocation] = Field(default_factory=list)
    provenance: RootCauseProvenance
    diagnostics: dict[str, Any] = Field(default_factory=dict)
    # created_at is observational metadata ONLY and must never participate in root_cause_id, sorting, or equality
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def deterministic_sort_key(self) -> tuple[str, str, str]:
        """Stable sorting key excluding timestamps."""
        return (
            self.category,
            self.status.value,
            self.root_cause_id,
        )


class RootCauseSummary(BaseModel):
    """Statistical summary count of localized regressions."""

    model_config = ConfigDict(extra="forbid")

    total_regressions_analyzed: int = 0
    located_count: int = 0
    partially_located_count: int = 0
    candidate_only_count: int = 0
    inconclusive_count: int = 0
    unsupported_count: int = 0


class RootCauseSuiteResult(BaseModel):
    """Top-level immutable container holding all root cause localization results in a run."""

    model_config = ConfigDict(extra="forbid")

    run_a_id: UUID
    run_b_id: UUID
    results: list[RootCauseResult] = Field(default_factory=list)
    summary: RootCauseSummary = Field(default_factory=RootCauseSummary)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
