"""Route Alignment and Route Divergence Module."""

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.matcher import RouteMatcher


class RouteAlignmentPair(BaseModel):
    """Pair of aligned application routes between Version A and Version B."""

    model_config = ConfigDict(extra="forbid")

    route_a: str
    route_b: str
    match_type: str


class RouteAlignmentSummary(BaseModel):
    """Deterministic summary of route matching across Version A and Version B."""

    model_config = ConfigDict(extra="forbid")

    aligned_routes: list[RouteAlignmentPair] = Field(default_factory=list)
    unmatched_routes_a: list[str] = Field(default_factory=list)
    unmatched_routes_b: list[str] = Field(default_factory=list)


class RouteAligner:
    """Computes route correspondence and detects route divergences."""

    @classmethod
    def align_routes(
        cls,
        routes_a: list[str],
        routes_b: list[str],
        config: AlignmentConfig,
    ) -> RouteAlignmentSummary:
        """Deterministically match discovered routes and record unmatched routes."""
        aligned: list[RouteAlignmentPair] = []
        matched_b_indices: set[int] = set()
        unmatched_a: list[str] = []

        # Sort for deterministic processing
        sorted_a = sorted(set(routes_a))
        sorted_b = sorted(set(routes_b))

        for r_a in sorted_a:
            matched_pair = False
            for idx_b, r_b in enumerate(sorted_b):
                if idx_b in matched_b_indices:
                    continue
                is_match, match_type = RouteMatcher.match(r_a, r_b, config)
                if is_match:
                    aligned.append(
                        RouteAlignmentPair(
                            route_a=r_a,
                            route_b=r_b,
                            match_type=match_type,
                        )
                    )
                    matched_b_indices.add(idx_b)
                    matched_pair = True
                    break

            if not matched_pair:
                unmatched_a.append(r_a)

        unmatched_b = [r_b for idx_b, r_b in enumerate(sorted_b) if idx_b not in matched_b_indices]

        return RouteAlignmentSummary(
            aligned_routes=aligned,
            unmatched_routes_a=unmatched_a,
            unmatched_routes_b=unmatched_b,
        )
