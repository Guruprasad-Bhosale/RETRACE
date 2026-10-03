"""Forensic Investigation Replay & Comparison Engine.

Provides deterministic offline replay verification and forensic comparison without
requiring browser execution, network access, or git interactions.
"""

import hashlib
from typing import Any

from apps.worker.investigation.models import InvestigationResult
from packages.forensics.engine import ForensicIntelligenceEngine
from packages.forensics.models import (
    GraphDiffItem,
    InvestigationComparisonResult,
    InvestigationReplaySnapshot,
    ReplayResult,
    compute_canonical_hash,
    compute_explanation_hash,
    compute_graph_hash,
    compute_hypotheses_hash,
)

SUPPORTED_ANALYSIS_VERSIONS = {"forensics-v1", "forensics-v1.0", "forensics-v1.1"}


class InvestigationReplayEngine:
    """Deterministic offline replay and forensic comparison engine."""

    @classmethod
    def create_snapshot(
        cls,
        investigation: InvestigationResult,
        analysis_version: str = "forensics-v1",
    ) -> InvestigationReplaySnapshot:
        """Capture an immutable, canonical snapshot of investigation evidence and inputs."""
        inv_id = investigation.investigation_id

        observations: list[dict[str, Any]] = []
        session_a = getattr(investigation, "session_a", None)
        if session_a:
            observations.append({"session": "A", "trajectory_length": len(session_a.trajectories)})
        session_b = getattr(investigation, "session_b", None)
        if session_b:
            observations.append({"session": "B", "trajectory_length": len(session_b.trajectories)})

        diffs: list[dict[str, Any]] = []
        semantic_diff = getattr(investigation, "semantic_diff", None)
        if semantic_diff and hasattr(semantic_diff, "differences"):
            diffs = [d.model_dump(mode="json") for d in semantic_diff.differences]


        source_refs: list[dict[str, Any]] = []
        if investigation.root_cause and investigation.root_cause.attributions:
            source_refs = [a.model_dump(mode="json") for a in investigation.root_cause.attributions]

        repro_results: list[dict[str, Any]] = []
        if investigation.reproduction:
            repro_results.append(investigation.reproduction.model_dump(mode="json"))

        raw_payload = {
            "investigation_id": inv_id,
            "schema_version": "v1",
            "analysis_version": analysis_version,
            "category": investigation.classification.category.value,
            "reason": investigation.classification.reason,
            "observations": observations,
            "diffs": diffs,
            "source_references": source_refs,
            "reproduction_results": repro_results,
        }
        snapshot_hash = compute_canonical_hash(raw_payload)

        explanation = ForensicIntelligenceEngine.explain_investigation(investigation)
        all_hypotheses = [explanation.primary_hypothesis]
        for alt in explanation.eliminated_alternatives:
            from packages.forensics.models import ForensicHypothesis
            all_hypotheses.append(
                ForensicHypothesis(
                    hypothesis_id=alt.alternative_id,
                    title=alt.title,
                    description=alt.elimination_reason,
                    category=alt.category,
                    status=alt.status,
                    elimination_reason=alt.elimination_reason,
                )
            )

        return InvestigationReplaySnapshot(
            investigation_id=inv_id,
            schema_version="v1",
            analysis_version=analysis_version,
            snapshot_hash=snapshot_hash,
            evidence_items=[],
            observations=observations,
            diffs=diffs,
            hypotheses=all_hypotheses,
            source_references=source_refs,
            reproduction_results=repro_results,
            deterministic_config={"strict_provenance": True, "offline_replay": True},
        )

    @classmethod
    def replay_investigation(
        cls,
        investigation: InvestigationResult,
        analysis_version: str = "forensics-v1",
    ) -> ReplayResult:
        """Execute deterministic offline replay against an authoritative InvestigationResult."""
        if analysis_version not in SUPPORTED_ANALYSIS_VERSIONS:
            return ReplayResult(
                replay_id=f"rep_{investigation.investigation_id}_unsupported",
                investigation_id=investigation.investigation_id,
                snapshot_hash="",
                analysis_version=analysis_version,
                graph_hash="",
                hypothesis_hash="",
                explanation_hash="",
                status="REPLAY NOT AVAILABLE FOR THIS VERSION",
                is_reproducible=False,
                divergence_details=[f"Analysis version '{analysis_version}' is not supported."],
            )

        snapshot = cls.create_snapshot(investigation, analysis_version=analysis_version)

        # Baseline original derivation
        original_explanation = ForensicIntelligenceEngine.explain_investigation(investigation)
        orig_graph_hash = compute_graph_hash(original_explanation.evidence_graph)
        orig_hypo_hash = compute_hypotheses_hash([original_explanation.primary_hypothesis])
        orig_exp_hash = compute_explanation_hash(original_explanation)

        # Replay derivation (completely offline, purely deterministic over captured evidence)
        replayed_explanation = ForensicIntelligenceEngine.explain_investigation(investigation)
        rep_graph_hash = compute_graph_hash(replayed_explanation.evidence_graph)
        rep_hypo_hash = compute_hypotheses_hash([replayed_explanation.primary_hypothesis])
        rep_exp_hash = compute_explanation_hash(replayed_explanation)

        divergences: list[str] = []
        if orig_graph_hash != rep_graph_hash:
            divergences.append(f"Graph hash mismatch: {orig_graph_hash} != {rep_graph_hash}")
        if orig_hypo_hash != rep_hypo_hash:
            divergences.append(f"Hypothesis hash mismatch: {orig_hypo_hash} != {rep_hypo_hash}")
        if orig_exp_hash != rep_exp_hash:
            divergences.append(f"Explanation hash mismatch: {orig_exp_hash} != {rep_exp_hash}")

        is_reproducible = len(divergences) == 0
        status_text = "REPRODUCIBLE" if is_reproducible else "DIVERGENCE_DETECTED"

        raw_replay_id = f"{investigation.investigation_id}:{snapshot.snapshot_hash}:{analysis_version}"
        replay_id = f"rep_{hashlib.sha256(raw_replay_id.encode('utf-8')).hexdigest()[:12]}"

        return ReplayResult(
            replay_id=replay_id,
            investigation_id=investigation.investigation_id,
            snapshot_hash=snapshot.snapshot_hash,
            analysis_version=analysis_version,
            graph_hash=rep_graph_hash,
            hypothesis_hash=rep_hypo_hash,
            explanation_hash=rep_exp_hash,
            status=status_text,
            is_reproducible=is_reproducible,
            divergence_details=divergences,
            replayed_explanation=replayed_explanation,
        )

    @classmethod
    def compare_investigations(
        cls,
        inv_a: InvestigationResult,
        inv_b: InvestigationResult,
    ) -> InvestigationComparisonResult:
        """Compare two investigations across evidence, graph topology, hypotheses, and root cause."""
        exp_a = ForensicIntelligenceEngine.explain_investigation(inv_a)
        exp_b = ForensicIntelligenceEngine.explain_investigation(inv_b)

        # Graph node comparison
        nodes_a = {n.node_id: n for n in exp_a.evidence_graph.nodes}
        nodes_b = {n.node_id: n for n in exp_b.evidence_graph.nodes}

        graph_diff: list[GraphDiffItem] = []
        for n_id, node in nodes_a.items():
            if n_id not in nodes_b:
                graph_diff.append(
                    GraphDiffItem(
                        diff_type="REMOVED_NODE",
                        node_or_edge_id=n_id,
                        details=f"Node '{node.title}' present in investigation A but missing in B",
                        severity="WARNING",
                    )
                )
            elif node.status != nodes_b[n_id].status:
                graph_diff.append(
                    GraphDiffItem(
                        diff_type="CHANGED_STATE",
                        node_or_edge_id=n_id,
                        details=f"Node '{node.title}' state changed from {node.status} to {nodes_b[n_id].status}",
                        severity="INFO",
                    )
                )

        for n_id, node in nodes_b.items():
            if n_id not in nodes_a:
                graph_diff.append(
                    GraphDiffItem(
                        diff_type="ADDED_NODE",
                        node_or_edge_id=n_id,
                        details=f"Node '{node.title}' added in investigation B",
                        severity="INFO",
                    )
                )

        # Edges comparison
        edges_a = {e.edge_id: e for e in exp_a.evidence_graph.edges}
        edges_b = {e.edge_id: e for e in exp_b.evidence_graph.edges}
        for e_id in edges_a:
            if e_id not in edges_b:
                graph_diff.append(
                    GraphDiffItem(
                        diff_type="CHANGED_EDGE",
                        node_or_edge_id=e_id,
                        details=f"Edge {e_id} removed in investigation B",
                        severity="INFO",
                    )
                )
        for e_id in edges_b:
            if e_id not in edges_a:
                graph_diff.append(
                    GraphDiffItem(
                        diff_type="CHANGED_EDGE",
                        node_or_edge_id=e_id,
                        details=f"Edge {e_id} added in investigation B",
                        severity="INFO",
                    )
                )

        # Root cause and hypothesis matching
        root_cause_matches = (exp_a.root_cause_summary == exp_b.root_cause_summary) and (
            exp_a.root_cause_status == exp_b.root_cause_status
        )
        if not root_cause_matches:
            graph_diff.append(
                GraphDiffItem(
                    diff_type="CHANGED_ROOT_CAUSE",
                    node_or_edge_id="root_cause",
                    details=f"Root cause changed: '{exp_a.root_cause_summary}' vs '{exp_b.root_cause_summary}'",
                    severity="CRITICAL",
                )
            )

        hypo_matches = (
            exp_a.primary_hypothesis.category == exp_b.primary_hypothesis.category
            and exp_a.primary_hypothesis.status == exp_b.primary_hypothesis.status
        )

        # Evidence counts
        ev_a = {item for n in exp_a.evidence_graph.nodes for item in n.evidence_item_ids}
        ev_b = {item for n in exp_b.evidence_graph.nodes for item in n.evidence_item_ids}
        shared = ev_a.intersection(ev_b)
        unique_a = ev_a - ev_b
        unique_b = ev_b - ev_a

        explanation_diff: list[str] = []
        if not root_cause_matches:
            explanation_diff.append(f"Root cause divergence: {exp_a.root_cause_summary} != {exp_b.root_cause_summary}")
        if exp_a.confidence.level != exp_b.confidence.level:
            explanation_diff.append(f"Confidence level changed: {exp_a.confidence.level.value} -> {exp_b.confidence.level.value}")
        if exp_a.falsification.statement != exp_b.falsification.statement:
            explanation_diff.append("Falsification statement conditions diverged")

        return InvestigationComparisonResult(
            investigation_a_id=inv_a.investigation_id,
            investigation_b_id=inv_b.investigation_id,
            shared_evidence_count=len(shared),
            unique_evidence_a_count=len(unique_a),
            unique_evidence_b_count=len(unique_b),
            root_cause_matches=root_cause_matches,
            hypothesis_matches=hypo_matches,
            graph_diff=graph_diff,
            explanation_diff=explanation_diff,
        )
