"""Unit tests for ExplorationConfig."""

import pytest
from pydantic import ValidationError

from apps.worker.exploration.config import ExplorationConfig


def test_exploration_config_defaults():
    config = ExplorationConfig(seed_url="http://localhost:3001")
    assert config.seed_url == "http://localhost:3001"
    assert config.max_steps == 50
    assert config.max_depth == 10
    assert config.max_actions_per_state == 8
    assert config.max_repeated_state_visits == 3
    assert config.traversal_strategy == "bfs"
    assert config.allow_destructive_actions is False
    assert "retrace-test" in config.synthetic_inputs["text"]


def test_exploration_config_effective_allowed_domains():
    config = ExplorationConfig(
        seed_url="http://localhost:3001/catalog",
        allowed_domains=["api.example.com"],
    )
    domains = config.get_effective_allowed_domains()
    assert "localhost:3001" in domains
    assert "api.example.com" in domains


def test_exploration_config_validation():
    with pytest.raises(ValidationError):
        # max_steps must be at least 1
        ExplorationConfig(seed_url="http://test.com", max_steps=0)
