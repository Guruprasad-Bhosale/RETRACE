"""Deterministic Trajectory Graph Alignment Engine.

Aligns ExplorationResult graphs from Version A and Version B across states,
transitions, actions, and routes without LLM models or arbitrary numeric thresholds.
"""

from collections import deque
from typing import Any
from uuid import UUID

from apps.worker.alignment.action_signature import ActionSignatureCalculator
from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.divergence import DivergenceExtractor
from apps.worker.alignment.matcher import ActionMatcher, StateMatcher
from apps.worker.alignment.models import (
    ActionAlignment,
    ActionSignature,
    AlignmentRelation,
    AlignmentResult,
    EvidenceStrength,
    MatchEvidence,
    StateAlignment,
    StateObservationalFeatures,
    StateSignature,
    TrajectoryAlignment,
    TransitionAlignment,
)
from apps.worker.alignment.route_alignment import RouteAligner
from apps.worker.exploration.diagnostics import ExplorationResult
from packages.domain.models import ActionType


class TrajectoryAligner:
    """Consumes two ExplorationResults and builds a deterministic behavioral trajectory alignment."""

    def __init__(self, config: AlignmentConfig | None = None) -> None:
        self.config = config or AlignmentConfig()

    def _build_state_signature(
        self,
        node: dict[str, Any],
    ) -> StateSignature:
        """Construct StateSignature from an ExplorationResult state graph node."""
        state_id = node.get("state_id", "")
        route = node.get("route", "/")
        inv_sig = node.get("inventory_signature", "")
        a11y_sig = node.get("a11y_signature", "")
        ui_sig = node.get("ui_state_signature", "")

        meta = node.get("metadata", {})
        obs_features = StateObservationalFeatures(
            http_status=meta.get("http_status", 200),
            page_title=meta.get("page_title"),
            console_errors_count=meta.get("console_errors_count", 0),
            network_failures_count=meta.get("network_failures_count", 0),
            interactive_elements_count=meta.get("interactive_elements_count", 0),
        )

        return StateSignature(
            state_id=state_id,
            normalized_route=route,
            inventory_signature=inv_sig,
            a11y_signature=a11y_sig,
            ui_state_signature=ui_sig,
            observational=obs_features,
        )

    def _build_action_signature_from_edge(self, edge: dict[str, Any]) -> ActionSignature:
        """Construct ActionSignature from a transition graph edge dictionary."""
        act_type_raw = str(edge.get("action_type", "click")).lower()
        try:
            act_type = ActionType(act_type_raw)
        except ValueError:
            try:
                act_type = ActionType[act_type_raw.upper()]
            except KeyError:
                act_type = ActionType.CLICK

        target_id = (
            edge.get("target_identity")
            or edge.get("target")
            or edge.get("target_element_id")
            or ""
        )
        val = edge.get("value") or edge.get("input_value")
        meta = edge.get("metadata") or {}

        input_class = None
        if act_type in (ActionType.TYPE, ActionType.SELECT):
            input_class = ActionSignatureCalculator.classify_input_value(
                value=val,
                tag=meta.get("tag", ""),
                name_hint=target_id,
            )

        return ActionSignature(
            action_type=act_type,
            stable_target_identity=target_id,
            target_role=meta.get("tag"),
            accessible_name=meta.get("accessible_name"),
            semantic_attributes=meta,
            normalized_input_class=input_class,
            raw_target=edge.get("target") or target_id,
        )

    @staticmethod
    def _parse_uuid(val: Any) -> UUID | None:
        """Safely parse UUID whether val is UUID, str, or None."""
        if not val:
            return None
        if isinstance(val, UUID):
            return val
        try:
            return UUID(str(val))
        except Exception:
            return None

    def align(
        self,
        result_a: ExplorationResult,
        result_b: ExplorationResult,
    ) -> AlignmentResult:
        """Deterministically align exploration graphs of Version A and Version B."""
        # 1. Parse and sort state nodes deterministically
        nodes_a = {n["state_id"]: n for n in result_a.state_graph_nodes}
        nodes_b = {n["state_id"]: n for n in result_b.state_graph_nodes}

        sigs_a = {sid: self._build_state_signature(node) for sid, node in nodes_a.items()}
        sigs_b = {sid: self._build_state_signature(node) for sid, node in nodes_b.items()}

        # Map transitions by from_state
        transitions_a_by_from: dict[str, list[dict[str, Any]]] = {}
        for edge in sorted(result_a.state_graph_edges, key=lambda e: e.get("transition_id", "")):
            from_id = edge.get("from_state_id", "")
            transitions_a_by_from.setdefault(from_id, []).append(edge)

        transitions_b_by_from: dict[str, list[dict[str, Any]]] = {}
        for edge in sorted(result_b.state_graph_edges, key=lambda e: e.get("transition_id", "")):
            from_id = edge.get("from_state_id", "")
            transitions_b_by_from.setdefault(from_id, []).append(edge)

        aligned_states: list[StateAlignment] = []
        ambiguous_states: list[StateAlignment] = []
        matched_state_ids_a: set[str] = set()
        matched_state_ids_b: set[str] = set()

        aligned_transitions: list[TransitionAlignment] = []
        matched_transition_ids_a: set[str] = set()
        matched_transition_ids_b: set[str] = set()

        frontier: deque[tuple[str, str]] = deque()

        # Step 1: Match seed states (depth 0 nodes or root states)
        seed_nodes_a = [n for n in nodes_a.values() if n.get("depth", 0) == 0]
        seed_nodes_b = [n for n in nodes_b.values() if n.get("depth", 0) == 0]

        if seed_nodes_a and seed_nodes_b:
            seed_a = seed_nodes_a[0]
            seed_b = seed_nodes_b[0]
            sa_id = seed_a["state_id"]
            sb_id = seed_b["state_id"]

            sig_a = sigs_a[sa_id]
            sig_b = sigs_b[sb_id]
            rel, ev = StateMatcher.match(sig_a, sig_b, self.config)

            aligned_states.append(
                StateAlignment(
                    state_a_id=sa_id,
                    state_b_id=sb_id,
                    observation_a_id=self._parse_uuid(seed_a.get("observation_id")),
                    observation_b_id=self._parse_uuid(seed_b.get("observation_id")),
                    signature_a=sig_a,
                    signature_b=sig_b,
                    relation=rel,
                    evidence=ev,
                )
            )
            matched_state_ids_a.add(sa_id)
            matched_state_ids_b.add(sb_id)
            frontier.append((sa_id, sb_id))

        # Step 2: Match exact states (identical state_id and route)
        for sid_a in sorted(nodes_a.keys()):
            if sid_a in matched_state_ids_a:
                continue
            sig_a = sigs_a[sid_a]

            for sid_b in sorted(nodes_b.keys()):
                if sid_b in matched_state_ids_b:
                    continue
                sig_b = sigs_b[sid_b]

                if sig_a.state_id == sig_b.state_id and sig_a.normalized_route == sig_b.normalized_route:
                    rel, ev = StateMatcher.match(sig_a, sig_b, self.config)
                    node_a = nodes_a[sid_a]
                    node_b = nodes_b[sid_b]
                    aligned_states.append(
                        StateAlignment(
                            state_a_id=sid_a,
                            state_b_id=sid_b,
                            observation_a_id=self._parse_uuid(node_a.get("observation_id")),
                            observation_b_id=self._parse_uuid(node_b.get("observation_id")),
                            signature_a=sig_a,
                            signature_b=sig_b,
                            relation=rel,
                            evidence=ev,
                        )
                    )
                    matched_state_ids_a.add(sid_a)
                    matched_state_ids_b.add(sid_b)
                    frontier.append((sid_a, sid_b))
                    break

        # Step 3: Match parent-guided transitions and child states across BFS frontier
        while frontier:
            st_a_id, st_b_id = frontier.popleft()

            trans_list_a = transitions_a_by_from.get(st_a_id, [])
            trans_list_b = transitions_b_by_from.get(st_b_id, [])

            for edge_a in trans_list_a:
                tid_a = edge_a.get("transition_id", "")
                if tid_a in matched_transition_ids_a:
                    continue

                asig_a = self._build_action_signature_from_edge(edge_a)

                matching_candidates_b: list[tuple[dict[str, Any], ActionSignature, AlignmentRelation, MatchEvidence]] = []

                for edge_b in trans_list_b:
                    tid_b = edge_b.get("transition_id", "")
                    if tid_b in matched_transition_ids_b:
                        continue

                    asig_b = self._build_action_signature_from_edge(edge_b)

                    act_rel, act_ev = ActionMatcher.match(asig_a, asig_b)
                    if act_rel in (AlignmentRelation.EXACT_MATCH, AlignmentRelation.STRONG_MATCH, AlignmentRelation.PARTIAL_MATCH):
                        matching_candidates_b.append((edge_b, asig_b, act_rel, act_ev))

                if matching_candidates_b:
                    max_strength = max(
                        (c[3].evidence_strength for c in matching_candidates_b),
                        key=lambda s: 3 if s == EvidenceStrength.EXACT else (2 if s == EvidenceStrength.STRONG else (1 if s == EvidenceStrength.PARTIAL else 0)),
                    )
                    matching_candidates_b = [c for c in matching_candidates_b if c[3].evidence_strength == max_strength]

                if len(matching_candidates_b) == 1:
                    best_edge_b, best_asig_b, best_rel, best_ev = matching_candidates_b[0]
                    tid_b = best_edge_b.get("transition_id", "")

                    act_align = ActionAlignment(
                        action_a_id=tid_a,
                        action_b_id=tid_b,
                        signature_a=asig_a,
                        signature_b=best_asig_b,
                        relation=best_rel,
                        evidence=best_ev,
                    )

                    aligned_transitions.append(
                        TransitionAlignment(
                            transition_a_id=tid_a,
                            transition_b_id=tid_b,
                            from_state_a_id=st_a_id,
                            from_state_b_id=st_b_id,
                            to_state_a_id=edge_a.get("to_state_id"),
                            to_state_b_id=best_edge_b.get("to_state_id"),
                            action_alignment=act_align,
                            relation=best_rel,
                            evidence=best_ev,
                        )
                    )
                    matched_transition_ids_a.add(tid_a)
                    matched_transition_ids_b.add(tid_b)

                    # Now evaluate destination states reached by this aligned transition
                    dest_id_a = edge_a.get("to_state_id")
                    dest_id_b = best_edge_b.get("to_state_id")

                    if dest_id_a and dest_id_b and dest_id_a in sigs_a and dest_id_b in sigs_b:
                        if dest_id_a not in matched_state_ids_a and dest_id_b not in matched_state_ids_b:
                            dest_sig_a = sigs_a[dest_id_a]
                            dest_sig_b = sigs_b[dest_id_b]
                            st_rel, st_ev = StateMatcher.match(
                                dest_sig_a,
                                dest_sig_b,
                                self.config,
                                parent_match=True,
                                action_match=True,
                            )
                            if st_rel != AlignmentRelation.UNMATCHED:
                                node_a = nodes_a[dest_id_a]
                                node_b = nodes_b[dest_id_b]
                                aligned_states.append(
                                    StateAlignment(
                                        state_a_id=dest_id_a,
                                        state_b_id=dest_id_b,
                                        observation_a_id=self._parse_uuid(node_a.get("observation_id")),
                                        observation_b_id=self._parse_uuid(node_b.get("observation_id")),
                                        signature_a=dest_sig_a,
                                        signature_b=dest_sig_b,
                                        relation=st_rel,
                                        evidence=st_ev,
                                    )
                                )
                                matched_state_ids_a.add(dest_id_a)
                                matched_state_ids_b.add(dest_id_b)
                                frontier.append((dest_id_a, dest_id_b))

                elif len(matching_candidates_b) > 1:
                    # Ambiguous matching candidates: do NOT guess
                    ambig_cands = [cb[0].get("transition_id", "") for cb in matching_candidates_b]
                    aligned_transitions.append(
                        TransitionAlignment(
                            transition_a_id=tid_a,
                            from_state_a_id=st_a_id,
                            to_state_a_id=edge_a.get("to_state_id"),
                            relation=AlignmentRelation.AMBIGUOUS,
                            evidence=MatchEvidence(
                                evidence_strength=EvidenceStrength.PARTIAL,
                                matched_features=["multiple_candidate_transitions"],
                                ambiguity_candidates=ambig_cands,
                            ),
                        )
                    )
                    matched_transition_ids_a.add(tid_a)

        # Step 4: Check for remaining unmatched states for partial route/structure matches or ambiguity
        for sid_a in sorted(nodes_a.keys()):
            if sid_a in matched_state_ids_a:
                continue
            sig_a = sigs_a[sid_a]

            candidates: list[tuple[str, StateSignature, AlignmentRelation, MatchEvidence]] = []
            for sid_b in sorted(nodes_b.keys()):
                if sid_b in matched_state_ids_b:
                    continue
                sig_b = sigs_b[sid_b]
                rel, ev = StateMatcher.match(sig_a, sig_b, self.config)
                if rel in (AlignmentRelation.EXACT_MATCH, AlignmentRelation.STRONG_MATCH, AlignmentRelation.PARTIAL_MATCH):
                    candidates.append((sid_b, sig_b, rel, ev))

            if len(candidates) == 1:
                best_sid_b, best_sig_b, best_rel, best_ev = candidates[0]
                node_a = nodes_a[sid_a]
                node_b = nodes_b[best_sid_b]
                aligned_states.append(
                    StateAlignment(
                        state_a_id=sid_a,
                        state_b_id=best_sid_b,
                        observation_a_id=self._parse_uuid(node_a.get("observation_id")),
                        observation_b_id=self._parse_uuid(node_b.get("observation_id")),
                        signature_a=sig_a,
                        signature_b=best_sig_b,
                        relation=best_rel,
                        evidence=best_ev,
                    )
                )
                matched_state_ids_a.add(sid_a)
                matched_state_ids_b.add(best_sid_b)
            elif len(candidates) > 1:
                # Ambiguous state candidate set
                ambig_ids = [c[0] for c in candidates]
                ambig_align = StateAlignment(
                    state_a_id=sid_a,
                    signature_a=sig_a,
                    relation=AlignmentRelation.AMBIGUOUS,
                    evidence=MatchEvidence(
                        evidence_strength=EvidenceStrength.PARTIAL,
                        matched_features=["multiple_candidate_states"],
                        ambiguity_candidates=ambig_ids,
                    ),
                )
                ambiguous_states.append(ambig_align)
                matched_state_ids_a.add(sid_a)

        # Step 5: Identify unmatched states and unmatched transitions
        unmatched_a_states = [sid for sid in sorted(nodes_a.keys()) if sid not in matched_state_ids_a]
        unmatched_b_states = [sid for sid in sorted(nodes_b.keys()) if sid not in matched_state_ids_b]

        unmatched_a_transitions: list[str] = []
        for edge in result_a.state_graph_edges:
            tid = edge.get("transition_id", "")
            if tid not in matched_transition_ids_a:
                unmatched_a_transitions.append(tid)
                aligned_transitions.append(
                    TransitionAlignment(
                        transition_a_id=tid,
                        from_state_a_id=edge.get("from_state_id"),
                        to_state_a_id=edge.get("to_state_id"),
                        relation=AlignmentRelation.UNMATCHED,
                        evidence=MatchEvidence(
                            evidence_strength=EvidenceStrength.NONE,
                            mismatched_features=["unmatched_in_target"],
                        ),
                    )
                )

        unmatched_b_transitions: list[str] = []
        for edge in result_b.state_graph_edges:
            tid = edge.get("transition_id", "")
            if tid not in matched_transition_ids_b:
                unmatched_b_transitions.append(tid)
                aligned_transitions.append(
                    TransitionAlignment(
                        transition_b_id=tid,
                        from_state_b_id=edge.get("from_state_id"),
                        to_state_b_id=edge.get("to_state_id"),
                        relation=AlignmentRelation.UNMATCHED,
                        evidence=MatchEvidence(
                            evidence_strength=EvidenceStrength.NONE,
                            mismatched_features=["unmatched_in_baseline"],
                        ),
                    )
                )

        # Step 6: Route alignment
        route_summary = RouteAligner.align_routes(
            routes_a=result_a.unique_routes,
            routes_b=result_b.unique_routes,
            config=self.config,
        )

        # Step 7: Evidence-backed neutral divergences
        divergences = (
            DivergenceExtractor.extract_route_divergences(route_summary)
            + DivergenceExtractor.extract_state_observational_divergences(
                aligned_states,
                artifacts_a=result_a.artifact_references,
                artifacts_b=result_b.artifact_references,
            )
            + DivergenceExtractor.extract_unmatched_state_divergences(
                unmatched_a_states,
                unmatched_b_states,
                nodes_a,
                nodes_b,
            )
            + DivergenceExtractor.extract_unmatched_transition_divergences(
                aligned_transitions,
            )
        )

        trajectory_align = TrajectoryAlignment(
            aligned_states=aligned_states,
            aligned_transitions=aligned_transitions,
            unmatched_a_states=unmatched_a_states,
            unmatched_b_states=unmatched_b_states,
            ambiguous_states=ambiguous_states,
            unmatched_a_transitions=unmatched_a_transitions,
            unmatched_b_transitions=unmatched_b_transitions,
            divergences=divergences,
            unique_routes_a=result_a.unique_routes,
            unique_routes_b=result_b.unique_routes,
            aligned_routes_count=len(route_summary.aligned_routes),
        )

        return AlignmentResult(
            run_a_id=result_a.run_id,
            run_b_id=result_b.run_id,
            trajectory_a_id=result_a.trajectory_id,
            trajectory_b_id=result_b.trajectory_id,
            alignment=trajectory_align,
        )
