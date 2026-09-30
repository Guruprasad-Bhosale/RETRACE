"""Unit tests for ResourceBudget enforcement."""

from apps.worker.orchestration.models import ResourceBudget


def test_resource_budget_defaults():
    budget = ResourceBudget()
    assert budget.max_workflow_duration_sec == 600
    assert budget.max_node_duration_sec == 120
    assert budget.max_exploration_steps == 15
    assert budget.max_reproduction_attempts == 3
    assert budget.max_concurrent_browsers == 2


def test_resource_budget_custom_values():
    budget = ResourceBudget(
        max_workflow_duration_sec=600,
        max_node_duration_sec=120,
        max_exploration_steps=20,
        max_reproduction_attempts=2,
        max_concurrent_browsers=1,
    )
    assert budget.max_workflow_duration_sec == 600
    assert budget.max_node_duration_sec == 120
    assert budget.max_exploration_steps == 20
    assert budget.max_reproduction_attempts == 2
    assert budget.max_concurrent_browsers == 1
