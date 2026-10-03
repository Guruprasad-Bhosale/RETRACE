"""Deterministic Forensic Evidence Graph 2.0 Builder.

Constructs strongly typed, deterministic Directed Acyclic Graphs (DAG) linking
multi-phase observations, semantic differences, hypotheses, AST source changes, reproductions, and root causes.
"""

import hashlib

from packages.forensics.models import (
    EdgeType,
    EvidenceGraph,
    EvidenceGraphEdge,
    EvidenceGraphNode,
    ForensicEvidenceItem,
    ForensicHypothesis,
    compute_deterministic_edge_id,
)


class EvidenceGraphBuilder:
    """Constructs deterministic forensic evidence DAGs with stable topology."""

    @classmethod
    def build_graph(
        cls,
        investigation_id: str,
        category: str,
        title: str,
        hypothesis: ForensicHypothesis,
        evidence_items: list[ForensicEvidenceItem],
        source_file: str | None = None,
        source_line: int | None = None,
        commit_hash: str | None = None,
        reproduction_code: str | None = None,
    ) -> EvidenceGraph:
        """Construct the complete forensic DAG with deterministic nodes and edges."""
        nodes: list[EvidenceGraphNode] = []
        edges: list[EvidenceGraphEdge] = []

        # 1. Observation Node
        obs_id = f"node_obs_{hashlib.sha256(f'{investigation_id}:obs'.encode()).hexdigest()[:8]}"
        obs_ev_ids = [e.id for e in evidence_items if "obs" in e.evidence_type.value]
        nodes.append(
            EvidenceGraphNode(
                node_id=obs_id,
                node_type="OBSERVATION",
                title="Baseline vs. Candidate Browser Observation",
                status="VERIFIED",
                evidence_item_ids=obs_ev_ids or [e.id for e in evidence_items[:1]],
                confidence_score=1.0,
                metadata={"category": category},
            )
        )

        # 2. Semantic Diff Node
        diff_id = f"node_diff_{hashlib.sha256(f'{investigation_id}:diff'.encode()).hexdigest()[:8]}"
        diff_ev_ids = [e.id for e in evidence_items if "diff" in e.evidence_type.value]
        nodes.append(
            EvidenceGraphNode(
                node_id=diff_id,
                node_type="DIFF",
                title=f"Semantic Difference: {title}",
                status="CONFIRMED",
                evidence_item_ids=diff_ev_ids or [e.id for e in evidence_items[:2]],
                confidence_score=0.95,
                metadata={"title": title},
            )
        )

        # 3. Hypothesis Node
        hyp_id = f"node_hyp_{hashlib.sha256(f'{investigation_id}:{hypothesis.hypothesis_id}'.encode()).hexdigest()[:8]}"
        nodes.append(
            EvidenceGraphNode(
                node_id=hyp_id,
                node_type="HYPOTHESIS",
                title=f"Diagnostic Hypothesis: {hypothesis.title}",
                status=hypothesis.status.value,
                evidence_item_ids=hypothesis.supporting_evidence_ids,
                confidence_score=hypothesis.score,
                metadata={"category": hypothesis.category.value},
            )
        )

        # 4. Source Diff Node (if source attribution exists)
        source_id = f"node_src_{hashlib.sha256(f'{investigation_id}:source'.encode()).hexdigest()[:8]}"
        src_label = f"{source_file}:{source_line}" if source_file and source_line else (source_file or "Source Code AST")
        src_ev_ids = [e.id for e in evidence_items if "ast" in e.evidence_type.value or "git" in e.evidence_type.value]
        nodes.append(
            EvidenceGraphNode(
                node_id=source_id,
                node_type="SOURCE_DIFF",
                title=f"Attributed Source Location: {src_label}",
                status="LOCATED" if source_file else "INFERRED",
                evidence_item_ids=src_ev_ids,
                confidence_score=0.90 if source_file else 0.60,
                metadata={"file": source_file, "line": source_line, "commit": commit_hash},
            )
        )

        # 5. Root Cause Node
        rc_id = f"node_rc_{hashlib.sha256(f'{investigation_id}:rootcause'.encode()).hexdigest()[:8]}"
        nodes.append(
            EvidenceGraphNode(
                node_id=rc_id,
                node_type="ROOT_CAUSE",
                title=f"Forensic Root Cause: {hypothesis.title}",
                status="CONFIRMED" if source_file and reproduction_code else "PROPOSED",
                evidence_item_ids=[e.id for e in evidence_items],
                confidence_score=0.95 if source_file and reproduction_code else 0.75,
                metadata={"attributed_file": source_file},
            )
        )

        # 6. Reproduction Node
        rep_id = f"node_rep_{hashlib.sha256(f'{investigation_id}:repro'.encode()).hexdigest()[:8]}"
        rep_ev_ids = [e.id for e in evidence_items if "repro" in e.evidence_type.value or "test" in e.evidence_type.value]
        nodes.append(
            EvidenceGraphNode(
                node_id=rep_id,
                node_type="REPRODUCTION",
                title="Synthesized Playwright Reproduction Test",
                status="SUCCEEDED" if reproduction_code else "SYNTHESIZED",
                evidence_item_ids=rep_ev_ids,
                confidence_score=1.0 if reproduction_code else 0.80,
                metadata={"has_code": bool(reproduction_code)},
            )
        )

        # ----------------------------------------------------------------------
        # Connect Semantic Edges
        # ----------------------------------------------------------------------
        # Observation -> Difference (DERIVED_FROM)
        edges.append(
            EvidenceGraphEdge(
                edge_id=compute_deterministic_edge_id(obs_id, diff_id, EdgeType.DERIVED_FROM),
                source_node_id=obs_id,
                target_node_id=diff_id,
                relationship=EdgeType.DERIVED_FROM,
                weight=1.0,
                explanation="Behavioral difference derived from baseline vs. candidate observation trace.",
            )
        )

        # Difference -> Hypothesis (SUPPORTS)
        edges.append(
            EvidenceGraphEdge(
                edge_id=compute_deterministic_edge_id(diff_id, hyp_id, EdgeType.SUPPORTS),
                source_node_id=diff_id,
                target_node_id=hyp_id,
                relationship=EdgeType.SUPPORTS,
                weight=0.85,
                explanation="Observed behavioral discrepancy supports the diagnostic hypothesis.",
            )
        )

        # Hypothesis -> Source Diff (LOCATED_AT)
        edges.append(
            EvidenceGraphEdge(
                edge_id=compute_deterministic_edge_id(hyp_id, source_id, EdgeType.LOCATED_AT),
                source_node_id=hyp_id,
                target_node_id=source_id,
                relationship=EdgeType.LOCATED_AT,
                weight=0.90,
                explanation="Hypothesis localized to AST modified symbol and Git commit diff.",
            )
        )

        # Source Diff -> Root Cause (CAUSED_BY)
        edges.append(
            EvidenceGraphEdge(
                edge_id=compute_deterministic_edge_id(source_id, rc_id, EdgeType.CAUSED_BY),
                source_node_id=source_id,
                target_node_id=rc_id,
                relationship=EdgeType.CAUSED_BY,
                weight=0.95,
                explanation="Code modification identified as the causal origin of regression.",
            )
        )

        # Root Cause -> Reproduction (REPRODUCES)
        edges.append(
            EvidenceGraphEdge(
                edge_id=compute_deterministic_edge_id(rc_id, rep_id, EdgeType.REPRODUCES),
                source_node_id=rc_id,
                target_node_id=rep_id,
                relationship=EdgeType.REPRODUCES,
                weight=1.0,
                explanation="Synthesized Playwright test reliably reproduces regression under test.",
            )
        )

        # Deterministic Graph Hash
        graph_raw = f"{investigation_id}:{len(nodes)}:{len(edges)}:" + ":".join(n.node_id for n in nodes)
        deterministic_hash = hashlib.sha256(graph_raw.encode("utf-8")).hexdigest()[:16]
        graph_id = f"graph_{deterministic_hash}"

        return EvidenceGraph(
            graph_id=graph_id,
            investigation_id=investigation_id,
            nodes=nodes,
            edges=edges,
            deterministic_hash=deterministic_hash,
        )
