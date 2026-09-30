"""State Semantic Difference Analyzer.

Extracts deterministic state-level differences including HTTP status, title,
missing/additional states, and ambiguous state alignments.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    StateDifference,
    compute_deterministic_diff_id,
)
from apps.worker.diff.normalization import DiffNormalizer


class StateDiffer:
    """Compares aligned state pairs and reports unmatched/ambiguous state structures."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[StateDifference]:
        """Extract deterministic state differences from an AlignmentResult."""
        if not self.config.enable_state_diff:
            return []

        differences: list[StateDifference] = []
        align = alignment_result.alignment

        # 1. Aligned State Pairs
        for sa in align.aligned_states:
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

            route = DiffNormalizer.normalize_route(sig_a.normalized_route, self.config)
            canonical_subj = f"state:{route}"

            # 1.1 HTTP Status Difference
            status_a = sig_a.observational.http_status
            status_b = sig_b.observational.http_status
            if status_a is not None and status_b is not None and status_a != status_b:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.STATE,
                    kind=DifferenceKind.HTTP_STATUS_CHANGED,
                    canonical_subject=canonical_subj,
                    before_identity=str(status_a),
                    after_identity=str(status_b),
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=status_a,
                    after_value=status_b,
                    state_a_id=sa.state_a_id,
                    state_b_id=sa.state_b_id,
                    observation_a_id=sa.observation_a_id,
                    observation_b_id=sa.observation_b_id,
                    details={
                        "route_a": sig_a.normalized_route,
                        "route_b": sig_b.normalized_route,
                        "status_a": status_a,
                        "status_b": status_b,
                    },
                )
                differences.append(
                    StateDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.STATE,
                        kind=DifferenceKind.HTTP_STATUS_CHANGED,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=(
                            f"HTTP status code difference at route '{route}': "
                            f"Version A returned HTTP {status_a}, Version B returned HTTP {status_b}."
                        ),
                        evidence=[evidence],
                    )
                )

            # 1.2 Page Title Difference
            title_a = sig_a.observational.page_title
            title_b = sig_b.observational.page_title
            norm_title_a = DiffNormalizer.normalize_text(title_a)
            norm_title_b = DiffNormalizer.normalize_text(title_b)
            if norm_title_a and norm_title_b and norm_title_a != norm_title_b:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.STATE,
                    kind=DifferenceKind.PAGE_TITLE_CHANGED,
                    canonical_subject=canonical_subj,
                    before_identity=norm_title_a,
                    after_identity=norm_title_b,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=title_a,
                    after_value=title_b,
                    state_a_id=sa.state_a_id,
                    state_b_id=sa.state_b_id,
                    observation_a_id=sa.observation_a_id,
                    observation_b_id=sa.observation_b_id,
                    details={"title_a": title_a, "title_b": title_b},
                )
                differences.append(
                    StateDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.STATE,
                        kind=DifferenceKind.PAGE_TITLE_CHANGED,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=(
                            f"Page title difference at route '{route}': "
                            f"Version A title is '{title_a}', Version B title is '{title_b}'."
                        ),
                        evidence=[evidence],
                    )
                )

        # 2. Unmatched States in Version A (Missing in B)
        for sid_a in sorted(align.unmatched_a_states):
            diff_id = compute_deterministic_diff_id(
                category=DifferenceCategory.STATE,
                kind=DifferenceKind.STATE_ONLY_IN_A,
                canonical_subject=f"state:{sid_a}",
                before_identity=sid_a,
                after_identity="none",
            )
            evidence = DifferenceEvidence(
                canonical_subject=f"state:{sid_a}",
                before_value=sid_a,
                after_value=None,
                state_a_id=sid_a,
                details={"unmatched_side": "A"},
            )
            differences.append(
                StateDifference(
                    diff_id=diff_id,
                    category=DifferenceCategory.STATE,
                    kind=DifferenceKind.STATE_ONLY_IN_A,
                    canonical_subject=f"state:{sid_a}",
                    comparison_status=ComparisonStatus.COMPARED,
                    description=f"State '{sid_a}' exists in Version A but was not reached/matched in Version B.",
                    evidence=[evidence],
                )
            )

        # 3. Unmatched States in Version B (Additional in B)
        for sid_b in sorted(align.unmatched_b_states):
            diff_id = compute_deterministic_diff_id(
                category=DifferenceCategory.STATE,
                kind=DifferenceKind.STATE_ONLY_IN_B,
                canonical_subject=f"state:{sid_b}",
                before_identity="none",
                after_identity=sid_b,
            )
            evidence = DifferenceEvidence(
                canonical_subject=f"state:{sid_b}",
                before_value=None,
                after_value=sid_b,
                state_b_id=sid_b,
                details={"unmatched_side": "B"},
            )
            differences.append(
                StateDifference(
                    diff_id=diff_id,
                    category=DifferenceCategory.STATE,
                    kind=DifferenceKind.STATE_ONLY_IN_B,
                    canonical_subject=f"state:{sid_b}",
                    comparison_status=ComparisonStatus.COMPARED,
                    description=f"State '{sid_b}' was discovered in Version B with no corresponding baseline in Version A.",
                    evidence=[evidence],
                )
            )

        # 4. Ambiguous States (Multiple candidates with identical structural evidence)
        for ambig in align.ambiguous_states:
            sid_a = ambig.state_a_id or "unknown"
            diff_id = compute_deterministic_diff_id(
                category=DifferenceCategory.STATE,
                kind=DifferenceKind.STATE_AMBIGUOUS,
                canonical_subject=f"state:{sid_a}",
                before_identity=sid_a,
                after_identity="ambiguous",
            )
            evidence = DifferenceEvidence(
                canonical_subject=f"state:{sid_a}",
                before_value=sid_a,
                after_value=None,
                state_a_id=sid_a,
                details={"ambiguity_candidates": ambig.evidence.ambiguity_candidates},
                comparison_completeness="ambiguous",
            )
            differences.append(
                StateDifference(
                    diff_id=diff_id,
                    category=DifferenceCategory.STATE,
                    kind=DifferenceKind.STATE_AMBIGUOUS,
                    canonical_subject=f"state:{sid_a}",
                    comparison_status=ComparisonStatus.NOT_COMPARABLE,
                    description=(
                        f"State alignment for '{sid_a}' is ambiguous between multiple candidate target states: "
                        f"{', '.join(ambig.evidence.ambiguity_candidates)}."
                    ),
                    evidence=[evidence],
                )
            )

        return differences
