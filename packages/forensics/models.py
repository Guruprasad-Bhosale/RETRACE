"""Forensic Intelligence & Evidence Graph 2.0 Domain Models.

Provides strongly typed, deterministic representations for forensic evidence items,
semantic evidence graph nodes/edges, explicit hypothesis lifecycles, transparent confidence models,
and testable falsification conditions.
"""

import hashlib
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.models import ArtifactReference


def utc_now() -> datetime:
    """Return current UTC timestamp with timezone."""
    return datetime.now(UTC)


class ForensicEvidenceType(StrEnum):
    """Categorized forensic evidence types preserving strict provenance."""

    DOM_OBSERVATION = "dom_observation"
    NETWORK_OBSERVATION = "network_observation"
    CONSOLE_OBSERVATION = "console_observation"
    VISUAL_DIFF = "visual_diff"
    ACCESSIBILITY_DIFF = "accessibility_diff"
    PERFORMANCE_DIFF = "performance_diff"
    STATE_DIFF = "state_diff"
    REPRODUCTION = "reproduction"
    GIT_DIFF = "git_diff"
    AST_DIFF = "ast_diff"
    SOURCE_REFERENCE = "source_reference"
    TEST_RESULT = "test_result"


class EdgeType(StrEnum):
    """Explicit semantic relationships connecting evidence graph nodes."""

    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CAUSED_BY = "CAUSED_BY"
    CORRELATES_WITH = "CORRELATES_WITH"
    REPRODUCES = "REPRODUCES"
    DERIVED_FROM = "DERIVED_FROM"
    LOCATED_AT = "LOCATED_AT"
    INVALIDATES = "INVALIDATES"


class HypothesisStatus(StrEnum):
    """Formal hypothesis lifecycle states."""

    PROPOSED = "PROPOSED"
    SUPPORTED = "SUPPORTED"
    WEAKENED = "WEAKENED"
    ELIMINATED = "ELIMINATED"
    CONFIRMED = "CONFIRMED"
    UNRESOLVED = "UNRESOLVED"


class HypothesisCategory(StrEnum):
    """Diagnostic categorization for regression hypotheses."""

    CALCULATION_LOGIC = "CALCULATION_LOGIC"
    DOM_RENDER_LOGIC = "DOM_RENDER_LOGIC"
    API_CONTRACT = "API_CONTRACT"
    TIMING_RACE_CONDITION = "TIMING_RACE_CONDITION"
    STYLING_FORMATTING = "STYLING_FORMATTING"
    STATE_PERSISTENCE = "STATE_PERSISTENCE"
    NAVIGATION_ROUTING = "NAVIGATION_ROUTING"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(StrEnum):
    """Non-arbitrary confidence levels based on deterministic verification."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INSUFFICIENT = "INSUFFICIENT"


class ForensicEvidenceItem(BaseModel):
    """Verifiable forensic evidence item with deterministic identity and immutable provenance."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Deterministic SHA-256 identifier derived from authoritative content")
    investigation_id: str
    evidence_type: ForensicEvidenceType
    source: str = Field(description="Subsystem or collector origin, e.g. Playwright, AST Parser, Git Engine")
    observation: str = Field(description="Human and machine readable observation summary")
    payload: dict[str, Any] = Field(default_factory=dict, description="Structured verified payload")
    artifact_reference: ArtifactReference | None = None
    confidence_weight: float = Field(default=1.0, ge=0.0, le=1.0)
    supports: list[str] = Field(default_factory=list, description="Target node/hypothesis IDs supported")
    contradicts: list[str] = Field(default_factory=list, description="Target node/hypothesis IDs contradicted")
    is_untrusted_input: bool = Field(default=True, description="True if payload derived from page/DOM/network")
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


def compute_deterministic_evidence_id(
    investigation_id: str,
    evidence_type: ForensicEvidenceType | str,
    content_key: str,
) -> str:
    """Compute stable SHA-256 evidence item identifier."""
    raw = f"{investigation_id}:{evidence_type}:{content_key}"
    return f"ev_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


class EvidenceGraphNode(BaseModel):
    """A node in the forensic DAG representing an observation, difference, hypothesis, source, or test."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    node_type: str = Field(description="Node type: OBSERVATION, DIFF, HYPOTHESIS, SOURCE_DIFF, REPRODUCTION, ROOT_CAUSE")
    title: str
    status: str = "CONFIRMED"
    evidence_item_ids: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceGraphEdge(BaseModel):
    """Directed semantic edge connecting two evidence graph nodes."""

    model_config = ConfigDict(extra="forbid")

    edge_id: str
    source_node_id: str
    target_node_id: str
    relationship: EdgeType
    weight: float = Field(default=1.0, ge=-1.0, le=1.0)
    explanation: str = ""


def compute_deterministic_edge_id(
    source_node_id: str,
    target_node_id: str,
    relationship: EdgeType | str,
) -> str:
    """Compute stable SHA-256 edge identifier."""
    raw = f"{source_node_id}->{relationship}->{target_node_id}"
    return f"edge_{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:12]}"


class EvidenceGraph(BaseModel):
    """Directed Acyclic Graph (DAG) representing the complete forensic evidence structure."""

    model_config = ConfigDict(extra="forbid")

    graph_id: str
    investigation_id: str
    nodes: list[EvidenceGraphNode] = Field(default_factory=list)
    edges: list[EvidenceGraphEdge] = Field(default_factory=list)
    deterministic_hash: str = ""
    created_at: datetime = Field(default_factory=utc_now)


class ForensicHypothesis(BaseModel):
    """An explicit diagnostic hypothesis evaluated against observed evidence."""

    model_config = ConfigDict(extra="forbid")

    hypothesis_id: str
    title: str
    description: str
    category: HypothesisCategory
    status: HypothesisStatus = HypothesisStatus.PROPOSED
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    elimination_reason: str | None = None
    score: float = Field(default=0.0, ge=-1.0, le=1.0)


class ConfidenceAssessment(BaseModel):
    """Transparent, defensible confidence evaluation without hidden probabilistic fabrication."""

    model_config = ConfigDict(extra="forbid")

    level: ConfidenceLevel
    score: float = Field(ge=0.0, le=1.0)
    supporting_count: int = Field(ge=0)
    contradicting_count: int = Field(ge=0)
    unresolved_count: int = Field(ge=0)
    rationale: str


class FalsificationCondition(BaseModel):
    """Defines what specific observable evidence or test condition would prove the conclusion false."""

    model_config = ConfigDict(extra="forbid")

    condition_id: str
    statement: str
    testable_verification: str
    potential_confounders: list[str] = Field(default_factory=list)


class AlternativeExplanation(BaseModel):
    """A plausible alternative hypothesis that was systematically evaluated and ruled out."""

    model_config = ConfigDict(extra="forbid")

    alternative_id: str
    title: str
    category: HypothesisCategory
    status: HypothesisStatus
    elimination_reason: str
    evidence_references: list[str] = Field(default_factory=list)


class ForensicInvestigationExplanation(BaseModel):
    """Comprehensive forensic explanation package linking observations, hypotheses, root causes, and falsification."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: str
    root_cause_summary: str
    root_cause_status: str
    primary_hypothesis: ForensicHypothesis
    eliminated_alternatives: list[AlternativeExplanation] = Field(default_factory=list)
    evidence_graph: EvidenceGraph
    confidence: ConfidenceAssessment
    falsification: FalsificationCondition
    provenance_chain: list[str] = Field(default_factory=list)
    evidence_graph_available: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class InvestigationReplaySnapshot(BaseModel):
    """Immutable, auditable snapshot of investigation evidence and deterministic inputs."""

    model_config = ConfigDict(extra="forbid")

    investigation_id: str
    schema_version: str = "v1"
    analysis_version: str = "forensics-v1"
    snapshot_hash: str = Field(description="Canonical SHA-256 hash of immutable inputs")
    evidence_items: list[ForensicEvidenceItem] = Field(default_factory=list)
    observations: list[dict[str, Any]] = Field(default_factory=list)
    diffs: list[dict[str, Any]] = Field(default_factory=list)
    hypotheses: list[ForensicHypothesis] = Field(default_factory=list)
    source_references: list[dict[str, Any]] = Field(default_factory=list)
    reproduction_results: list[dict[str, Any]] = Field(default_factory=list)
    deterministic_config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class ReplayResult(BaseModel):
    """Result of deterministic offline replay verification."""

    model_config = ConfigDict(extra="forbid")

    replay_id: str = Field(description="Deterministic replay identifier derived from investigation_id and snapshot_hash")
    investigation_id: str
    snapshot_hash: str
    analysis_version: str
    graph_hash: str
    hypothesis_hash: str
    explanation_hash: str
    status: str = Field(description="REPRODUCIBLE, DIVERGENCE_DETECTED, or UNSUPPORTED_VERSION")
    is_reproducible: bool
    divergence_details: list[str] = Field(default_factory=list)
    replayed_explanation: ForensicInvestigationExplanation | None = None
    created_at: datetime = Field(default_factory=utc_now)


class GraphDiffItem(BaseModel):
    """Individual graph diff element between two investigation states."""

    model_config = ConfigDict(extra="forbid")

    diff_type: str = Field(description="ADDED_NODE, REMOVED_NODE, CHANGED_EDGE, CHANGED_STATE, CHANGED_ROOT_CAUSE")
    node_or_edge_id: str
    details: str
    severity: str = "INFO"


class InvestigationComparisonResult(BaseModel):
    """Forensic comparison between two investigation runs or versions."""

    model_config = ConfigDict(extra="forbid")

    investigation_a_id: str
    investigation_b_id: str
    shared_evidence_count: int
    unique_evidence_a_count: int
    unique_evidence_b_count: int
    root_cause_matches: bool
    hypothesis_matches: bool
    graph_diff: list[GraphDiffItem] = Field(default_factory=list)
    explanation_diff: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


def compute_canonical_hash(payload: Any) -> str:
    """Compute deterministic SHA-256 hash of a normalized JSON-serializable structure."""
    import json

    def normalize(val: Any) -> Any:
        if isinstance(val, BaseModel):
            return normalize(val.model_dump(mode="json"))
        if isinstance(val, dict):
            return {k: normalize(v) for k, v in sorted(val.items()) if not k.startswith("_") and k not in ("created_at", "timestamp")}
        if isinstance(val, list | tuple | set):
            return [normalize(v) for v in val]
        return val

    normalized = normalize(payload)
    canonical_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def compute_graph_hash(graph: EvidenceGraph) -> str:
    """Compute canonical hash of an evidence graph's topology and node states."""
    nodes_payload = [
        {
            "node_id": n.node_id,
            "node_type": n.node_type,
            "title": n.title,
            "status": n.status,
            "evidence_item_ids": sorted(n.evidence_item_ids),
        }
        for n in sorted(graph.nodes, key=lambda x: x.node_id)
    ]
    edges_payload = [
        {
            "edge_id": e.edge_id,
            "source_node_id": e.source_node_id,
            "target_node_id": e.target_node_id,
            "relationship": e.relationship.value if hasattr(e.relationship, "value") else str(e.relationship),
        }
        for e in sorted(graph.edges, key=lambda x: x.edge_id)
    ]
    return compute_canonical_hash({"nodes": nodes_payload, "edges": edges_payload})


def compute_hypotheses_hash(hypotheses: list[ForensicHypothesis]) -> str:
    """Compute canonical hash of evaluated hypotheses."""
    payload = [
        {
            "hypothesis_id": h.hypothesis_id,
            "category": h.category.value if hasattr(h.category, "value") else str(h.category),
            "status": h.status.value if hasattr(h.status, "value") else str(h.status),
            "supporting": sorted(h.supporting_evidence_ids),
            "contradicting": sorted(h.contradicting_evidence_ids),
            "elimination_reason": h.elimination_reason or "",
        }
        for h in sorted(hypotheses, key=lambda x: x.hypothesis_id)
    ]
    return compute_canonical_hash(payload)


def compute_explanation_hash(explanation: ForensicInvestigationExplanation) -> str:
    """Compute canonical hash of root cause, confidence, and falsification conditions."""
    payload = {
        "investigation_id": explanation.investigation_id,
        "root_cause_summary": explanation.root_cause_summary,
        "root_cause_status": explanation.root_cause_status,
        "primary_hypothesis_id": explanation.primary_hypothesis.hypothesis_id,
        "primary_hypothesis_status": explanation.primary_hypothesis.status.value,
        "confidence_level": explanation.confidence.level.value,
        "confidence_score": round(explanation.confidence.score, 4),
        "falsification_statement": explanation.falsification.statement,
        "provenance": sorted(explanation.provenance_chain),
    }
    return compute_canonical_hash(payload)

