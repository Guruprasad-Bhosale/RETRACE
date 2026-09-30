"""Neutral Divergence Extraction Module.

Extracts evidence-backed observed differences across routes, states, actions, HTTP statuses,
and console logs between Version A and Version B.
CRITICAL: Divergences are neutral behavioral differences, NEVER labeled as bugs or regressions.
"""

import hashlib
from typing import Any
from uuid import UUID

from apps.worker.alignment.models import (
    AlignmentRelation,
    Divergence,
    DivergenceType,
    StateAlignment,
    TransitionAlignment,
)
from apps.worker.alignment.route_alignment import RouteAlignmentSummary
from packages.domain.models import ArtifactReference


class DivergenceExtractor:
    """Extracts neutral, evidence-linked Divergence instances from aligned trajectories."""

    @staticmethod
    def _compute_div_id(div_type: DivergenceType, key: str) -> str:
        raw = f"{div_type.value}:{key}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def extract_route_divergences(
        cls,
        route_summary: RouteAlignmentSummary,
    ) -> list[Divergence]:
        """Extract divergences from unmatched routes in Version A and Version B."""
        divergences: list[Divergence] = []

        for r_a in route_summary.unmatched_routes_a:
            div_id = cls._compute_div_id(DivergenceType.ROUTE_DIVERGENCE, f"unmatched_a:{r_a}")
            divergences.append(
                Divergence(
                    divergence_id=div_id,
                    divergence_type=DivergenceType.ROUTE_DIVERGENCE,
                    description=f"Route '{r_a}' was discovered in Version A but not reached in Version B.",
                    details={"route_a": r_a, "side": "A"},
                )
            )

        for r_b in route_summary.unmatched_routes_b:
            div_id = cls._compute_div_id(DivergenceType.ROUTE_DIVERGENCE, f"unmatched_b:{r_b}")
            divergences.append(
                Divergence(
                    divergence_id=div_id,
                    divergence_type=DivergenceType.ROUTE_DIVERGENCE,
                    description=f"Route '{r_b}' was discovered in Version B but not reached in Version A.",
                    details={"route_b": r_b, "side": "B"},
                )
            )

        return divergences

    @classmethod
    def extract_state_observational_divergences(
        cls,
        state_alignments: list[StateAlignment],
        artifacts_a: list[ArtifactReference] | None = None,
        artifacts_b: list[ArtifactReference] | None = None,
    ) -> list[Divergence]:
        """Extract HTTP status, console error, and structural differences on aligned states."""
        divergences: list[Divergence] = []

        for sa in state_alignments:
            if sa.relation not in (
                AlignmentRelation.EXACT_MATCH,
                AlignmentRelation.STRONG_MATCH,
                AlignmentRelation.PARTIAL_MATCH,
            ):
                continue

            sig_a = sa.signature_a
            sig_b = sa.signature_b
            if not sig_a or not sig_b:
                continue

            # 1. HTTP Status Divergence (e.g. 200 in A vs 404/500 in B)
            status_a = sig_a.observational.http_status
            status_b = sig_b.observational.http_status
            if status_a is not None and status_b is not None and status_a != status_b:
                div_id = cls._compute_div_id(
                    DivergenceType.HTTP_STATUS_DIVERGENCE,
                    f"{sa.state_a_id}:{sa.state_b_id}:{status_a}:{status_b}",
                )
                divergences.append(
                    Divergence(
                        divergence_id=div_id,
                        divergence_type=DivergenceType.HTTP_STATUS_DIVERGENCE,
                        description=(
                            f"HTTP status code divergence at route '{sig_a.normalized_route}': "
                            f"Version A returned HTTP {status_a}, Version B returned HTTP {status_b}."
                        ),
                        state_a_id=sa.state_a_id,
                        state_b_id=sa.state_b_id,
                        observation_a_id=sa.observation_a_id,
                        observation_b_id=sa.observation_b_id,
                        artifact_references=(artifacts_a or []) + (artifacts_b or []),
                        details={
                            "route_a": sig_a.normalized_route,
                            "route_b": sig_b.normalized_route,
                            "status_a": status_a,
                            "status_b": status_b,
                        },
                    )
                )

            # 2. Console Error Divergence
            errs_a = sig_a.observational.console_errors_count
            errs_b = sig_b.observational.console_errors_count
            if errs_a != errs_b:
                div_id = cls._compute_div_id(
                    DivergenceType.CONSOLE_ERROR_DIVERGENCE,
                    f"{sa.state_a_id}:{sa.state_b_id}:{errs_a}:{errs_b}",
                )
                divergences.append(
                    Divergence(
                        divergence_id=div_id,
                        divergence_type=DivergenceType.CONSOLE_ERROR_DIVERGENCE,
                        description=(
                            f"Console error count divergence at route '{sig_a.normalized_route}': "
                            f"Version A logged {errs_a} error(s), Version B logged {errs_b} error(s)."
                        ),
                        state_a_id=sa.state_a_id,
                        state_b_id=sa.state_b_id,
                        observation_a_id=sa.observation_a_id,
                        observation_b_id=sa.observation_b_id,
                        details={"console_errors_a": errs_a, "console_errors_b": errs_b},
                    )
                )

            # 3. Observational Page Title Divergence
            title_a = sig_a.observational.page_title
            title_b = sig_b.observational.page_title
            if title_a and title_b and title_a != title_b:
                div_id = cls._compute_div_id(
                    DivergenceType.OBSERVATIONAL_DIVERGENCE,
                    f"title:{sa.state_a_id}:{sa.state_b_id}",
                )
                divergences.append(
                    Divergence(
                        divergence_id=div_id,
                        divergence_type=DivergenceType.OBSERVATIONAL_DIVERGENCE,
                        description=(
                            f"Page title divergence at route '{sig_a.normalized_route}': "
                            f"Version A title is '{title_a}', Version B title is '{title_b}'."
                        ),
                        state_a_id=sa.state_a_id,
                        state_b_id=sa.state_b_id,
                        observation_a_id=sa.observation_a_id,
                        observation_b_id=sa.observation_b_id,
                        details={"title_a": title_a, "title_b": title_b},
                    )
                )

        return divergences

    @classmethod
    def extract_unmatched_state_divergences(
        cls,
        unmatched_a: list[str],
        unmatched_b: list[str],
        state_lookup_a: dict[str, Any],
        state_lookup_b: dict[str, Any],
    ) -> list[Divergence]:
        """Extract missing/additional state divergences."""
        divergences: list[Divergence] = []

        for sid_a in unmatched_a:
            st = state_lookup_a.get(sid_a)
            route = st.get("route", "/") if st else "/"
            obs_id = UUID(st.get("observation_id")) if st and st.get("observation_id") else None
            div_id = cls._compute_div_id(DivergenceType.MISSING_STATE, sid_a)
            divergences.append(
                Divergence(
                    divergence_id=div_id,
                    divergence_type=DivergenceType.MISSING_STATE,
                    description=f"State {sid_a[:8]} (route '{route}') in Version A has no corresponding state in Version B.",
                    state_a_id=sid_a,
                    observation_a_id=obs_id,
                    details={"route": route, "side": "A"},
                )
            )

        for sid_b in unmatched_b:
            st = state_lookup_b.get(sid_b)
            route = st.get("route", "/") if st else "/"
            obs_id = UUID(st.get("observation_id")) if st and st.get("observation_id") else None
            div_id = cls._compute_div_id(DivergenceType.ADDITIONAL_STATE, sid_b)
            divergences.append(
                Divergence(
                    divergence_id=div_id,
                    divergence_type=DivergenceType.ADDITIONAL_STATE,
                    description=f"Additional state {sid_b[:8]} (route '{route}') was discovered in Version B with no baseline in Version A.",
                    state_b_id=sid_b,
                    observation_b_id=obs_id,
                    details={"route": route, "side": "B"},
                )
            )

        return divergences

    @classmethod
    def extract_unmatched_transition_divergences(
        cls,
        transition_alignments: list[TransitionAlignment],
    ) -> list[Divergence]:
        """Extract unmatched transition divergences."""
        divergences: list[Divergence] = []

        for ta in transition_alignments:
            if ta.relation != AlignmentRelation.UNMATCHED:
                continue

            if ta.transition_a_id and not ta.transition_b_id:
                div_id = cls._compute_div_id(DivergenceType.MISSING_ACTION, ta.transition_a_id)
                divergences.append(
                    Divergence(
                        divergence_id=div_id,
                        divergence_type=DivergenceType.MISSING_ACTION,
                        description=f"Transition {ta.transition_a_id[:8]} from state {ta.from_state_a_id} in Version A was not executed/matched in Version B.",
                        state_a_id=ta.from_state_a_id,
                        action_a_id=ta.transition_a_id,
                        details={"from_state_a": ta.from_state_a_id, "to_state_a": ta.to_state_a_id},
                    )
                )
            elif ta.transition_b_id and not ta.transition_a_id:
                div_id = cls._compute_div_id(DivergenceType.ADDITIONAL_ACTION, ta.transition_b_id)
                divergences.append(
                    Divergence(
                        divergence_id=div_id,
                        divergence_type=DivergenceType.ADDITIONAL_ACTION,
                        description=f"Additional transition {ta.transition_b_id[:8]} executed from state {ta.from_state_b_id} in Version B without matching transition in Version A.",
                        state_b_id=ta.from_state_b_id,
                        action_b_id=ta.transition_b_id,
                        details={"from_state_b": ta.from_state_b_id, "to_state_b": ta.to_state_b_id},
                    )
                )

        return divergences
