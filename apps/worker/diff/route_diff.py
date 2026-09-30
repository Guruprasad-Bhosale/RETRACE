"""Route Semantic Difference Analyzer.

Extracts deterministic route-level differences between Version A and Version B.
"""

from apps.worker.alignment.models import AlignmentResult
from apps.worker.diff.config import DiffConfig
from apps.worker.diff.models import (
    ComparisonStatus,
    DifferenceCategory,
    DifferenceEvidence,
    DifferenceKind,
    RouteDifference,
    compute_deterministic_diff_id,
)
from apps.worker.diff.normalization import DiffNormalizer


class RouteDiffer:
    """Computes semantic route additions, removals, and structural route deviations."""

    def __init__(self, config: DiffConfig | None = None) -> None:
        self.config = config or DiffConfig()

    def diff(self, alignment_result: AlignmentResult) -> list[RouteDifference]:
        """Extract deterministic route differences from an AlignmentResult."""
        if not self.config.enable_route_diff:
            return []

        differences: list[RouteDifference] = []
        align = alignment_result.alignment

        norm_routes_a = {
            DiffNormalizer.normalize_route(r, self.config): r
            for r in align.unique_routes_a
        }
        norm_routes_b = {
            DiffNormalizer.normalize_route(r, self.config): r
            for r in align.unique_routes_b
        }

        # Routes present in A but missing in B
        for norm_r, raw_r in sorted(norm_routes_a.items()):
            if norm_r not in norm_routes_b:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.ROUTE,
                    kind=DifferenceKind.ROUTE_REMOVED,
                    canonical_subject=norm_r,
                    before_identity=raw_r,
                    after_identity="none",
                )
                evidence = DifferenceEvidence(
                    canonical_subject=norm_r,
                    before_value=raw_r,
                    after_value=None,
                    details={"side": "A", "raw_route_a": raw_r},
                )
                differences.append(
                    RouteDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.ROUTE,
                        kind=DifferenceKind.ROUTE_REMOVED,
                        canonical_subject=norm_r,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=f"Route '{norm_r}' is present in Version A but absent in Version B.",
                        evidence=[evidence],
                    )
                )

        # Routes present in B but missing in A
        for norm_r, raw_r in sorted(norm_routes_b.items()):
            if norm_r not in norm_routes_a:
                diff_id = compute_deterministic_diff_id(
                    category=DifferenceCategory.ROUTE,
                    kind=DifferenceKind.ROUTE_ADDED,
                    canonical_subject=norm_r,
                    before_identity="none",
                    after_identity=raw_r,
                )
                evidence = DifferenceEvidence(
                    canonical_subject=norm_r,
                    before_value=None,
                    after_value=raw_r,
                    details={"side": "B", "raw_route_b": raw_r},
                )
                differences.append(
                    RouteDifference(
                        diff_id=diff_id,
                        category=DifferenceCategory.ROUTE,
                        kind=DifferenceKind.ROUTE_ADDED,
                        canonical_subject=norm_r,
                        comparison_status=ComparisonStatus.COMPARED,
                        description=f"Route '{norm_r}' was discovered in Version B but has no baseline in Version A.",
                        evidence=[evidence],
                    )
                )

        return differences
