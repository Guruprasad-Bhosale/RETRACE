"""Unit tests for deterministic graph routing and state transitions."""

from apps.worker.orchestration.models import WorkflowStatus
from apps.worker.orchestration.routing import (
    route_after_align,
    route_after_assemble,
    route_after_classify,
    route_after_diff,
    route_after_explore,
    route_after_prepare,
    route_after_reproduce,
    route_after_root_cause,
    route_after_validate,
)


def test_routing_determinism():
    # 1. Successful state transitions are deterministic
    running_state = {"status": WorkflowStatus.RUNNING.value}
    assert route_after_validate(running_state) == "prepare_versions"
    assert route_after_prepare(running_state) == "explore"
    assert route_after_explore(running_state) == "align"
    assert route_after_align(running_state) == "diff"
    assert route_after_diff(running_state) == "classify"
    assert route_after_reproduce(running_state) == "root_cause"
    assert route_after_root_cause(running_state) == "assemble"
    assert route_after_assemble(running_state) == "finalize"

    # 2. Failure transitions always route to END deterministically
    failed_state = {"status": WorkflowStatus.FAILED.value}
    assert route_after_validate(failed_state) == "__end__"
    assert route_after_prepare(failed_state) == "__end__"
    assert route_after_explore(failed_state) == "__end__"
    assert route_after_align(failed_state) == "__end__"
    assert route_after_diff(failed_state) == "__end__"
    assert route_after_classify(failed_state) == "__end__"
    assert route_after_reproduce(failed_state) == "__end__"
    assert route_after_root_cause(failed_state) == "__end__"
    assert route_after_assemble(failed_state) == "__end__"
