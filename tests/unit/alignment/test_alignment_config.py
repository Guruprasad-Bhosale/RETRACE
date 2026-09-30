"""Unit tests for AlignmentConfig."""

from apps.worker.alignment.config import AlignmentConfig


def test_alignment_config_defaults() -> None:
    config = AlignmentConfig()
    assert config.version_a_base_url == "http://localhost:3001"
    assert config.version_b_base_url == "http://localhost:3002"
    assert config.route_matching_policy == "exact"
    assert config.route_aliases == {}
    assert config.deterministic_tie_breaker == "lexicographical"


def test_alignment_config_custom_aliases() -> None:
    config = AlignmentConfig(
        route_matching_policy="allow_aliases",
        route_aliases={"/": ["/home", "/index.html"]},
    )
    assert config.route_matching_policy == "allow_aliases"
    assert "/home" in config.route_aliases["/"]
