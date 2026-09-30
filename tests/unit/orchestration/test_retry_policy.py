"""Unit tests for orchestration retry policy and failure classification."""

from apps.worker.orchestration.models import (
    ExecutionPolicy,
    FailureType,
    WorkflowStatus,
)


def test_execution_policy_defaults():
    policy = ExecutionPolicy()
    assert policy.max_retries == 2
    assert policy.retry_on_transient is True
    assert policy.fail_fast is False


def test_failure_type_enumeration():
    types = [
        FailureType.TRANSIENT_FAILURE,
        FailureType.PERMANENT_FAILURE,
        FailureType.INVALID_INPUT,
        FailureType.SECURITY_FAILURE,
        FailureType.RESOURCE_EXHAUSTION,
        FailureType.UPSTREAM_INCONCLUSIVE,
    ]
    assert len(types) == 6
    assert all(isinstance(t.value, str) for t in types)


def test_workflow_status_distinctions():
    # Verify strict distinction between FAILED and INCONCLUSIVE
    assert WorkflowStatus.FAILED != WorkflowStatus.INCONCLUSIVE
    assert WorkflowStatus.FAILED.value == "FAILED"
    assert WorkflowStatus.INCONCLUSIVE.value == "INCONCLUSIVE"
    assert WorkflowStatus.CANCELLED.value == "CANCELLED"
    assert WorkflowStatus.COMPLETED.value == "COMPLETED"
