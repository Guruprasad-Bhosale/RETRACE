"""Unit tests for RouteMatcher and RouteAligner."""

from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.matcher import RouteMatcher
from apps.worker.alignment.route_alignment import RouteAligner


def test_route_matcher_exact() -> None:
    config = AlignmentConfig(route_matching_policy="exact")
    is_match, match_type = RouteMatcher.match("/cart", "/cart", config)
    assert is_match is True
    assert match_type == "exact"

    is_match_diff, match_type_diff = RouteMatcher.match("/cart", "/checkout", config)
    assert is_match_diff is False
    assert match_type_diff == "mismatch"


def test_route_matcher_strip_query() -> None:
    config = AlignmentConfig(route_matching_policy="strip_query")
    is_match, match_type = RouteMatcher.match("/products?page=1", "/products?page=2", config)
    assert is_match is True
    assert match_type == "stripped_query"


def test_route_matcher_aliases() -> None:
    config = AlignmentConfig(
        route_matching_policy="allow_aliases",
        route_aliases={"/": ["/home", "/index.html"]},
    )
    is_match, match_type = RouteMatcher.match("/", "/home", config)
    assert is_match is True
    assert match_type == "alias"


def test_route_aligner_summary() -> None:
    config = AlignmentConfig()
    routes_a = ["/", "/cart", "/checkout", "/legacy"]
    routes_b = ["/", "/cart", "/checkout", "/new-feature"]

    summary = RouteAligner.align_routes(routes_a, routes_b, config)
    assert len(summary.aligned_routes) == 3
    assert summary.unmatched_routes_a == ["/legacy"]
    assert summary.unmatched_routes_b == ["/new-feature"]
