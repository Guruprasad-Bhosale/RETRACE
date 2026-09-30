"""Console and Unhandled Error Semantic Difference Analyzer.

Extracts deterministic differences in console error counts, warnings,
and unhandled runtime script errors.
"""

from apps.worker.alignment.models import AlignmentRelation, AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    ComparisonStatus,
    ConsoleDifference,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    compute_deterministic_diff_id,
)
from apps.worker.diff.normalization import DiffNormalizer


class ConsoleDiffer:
    """Compares observable console error logs and runtime exceptions."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[ConsoleDifference]:
        """Extract deterministic console differences from an AlignmentResult."""
        if not self.config.enable_console_diff:
            return []

        differences: list[ConsoleDifference] = []
        align = alignment_result.alignment

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
            canonical_subj = f"console:{route}"

            errs_a = sig_a.observational.console_errors_count
            errs_b = sig_b.observational.console_errors_count

            if errs_a != errs_b:
                kind = (
                    DifferenceKind.CONSOLE_ERROR_ADDED
                    if errs_b > errs_a
                    else DifferenceKind.CONSOLE_ERROR_REMOVED
                )
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.CONSOLE,
                    kind=kind,
                    canonical_subject=canonical_subj,
                    before_identity=str(errs_a),
                    after_identity=str(errs_b),
                )
                evidence = DifferenceEvidence(
                    canonical_subject=canonical_subj,
                    before_value=errs_a,
                    after_value=errs_b,
                    state_a_id=sa.state_a_id,
                    state_b_id=sa.state_b_id,
                    observation_a_id=sa.observation_a_id,
                    observation_b_id=sa.observation_b_id,
                    details={"console_errors_a": errs_a, "console_errors_b": errs_b, "route": route},
                )
                desc = (
                    f"Console error count increased at route '{route}': "
                    f"Version A logged {errs_a} error(s), Version B logged {errs_b} error(s)."
                    if errs_b > errs_a
                    else f"Console error count decreased at route '{route}': "
                    f"Version A logged {errs_a} error(s), Version B logged {errs_b} error(s)."
                )
                differences.append(
                    ConsoleDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.CONSOLE,
                        kind=kind,
                        canonical_subject=canonical_subj,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=desc,
                        evidence=[evidence],
                    )
                )

        return differences
