"""Conditional Routing Logic for LangGraph Investigation Workflows."""

from typing import Literal

from apps.worker.orchestration.models import (
    InvestigationWorkflowState,
    WorkflowStatus,
)
from apps.worker.regression.models import ClassificationStatus, RegressionClassificationResult


def route_after_validate(
    state: InvestigationWorkflowState,
) -> Literal["prepare_versions", "__end__"]:
    """Determine next step after input validation."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"
    return "prepare_versions"


def route_after_prepare(
    state: InvestigationWorkflowState,
) -> Literal["explore", "__end__"]:
    """Determine next step after environment preparation."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"
    return "explore"


def route_after_explore(
    state: InvestigationWorkflowState,
) -> Literal["align", "__end__"]:
    """Determine next step after exploration."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"
    return "align"


def route_after_align(
    state: InvestigationWorkflowState,
) -> Literal["diff", "__end__"]:
    """Determine next step after trajectory alignment."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"
    return "diff"


def route_after_diff(
    state: InvestigationWorkflowState,
) -> Literal["classify", "__end__"]:
    """Determine next step after semantic diff."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"
    return "classify"


def route_after_classify(
    state: InvestigationWorkflowState,
) -> Literal["reproduce", "finalize_no_regression", "__end__"]:
    """Determine whether regression candidates exist or if the workflow should short-circuit."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"

    clf_result: RegressionClassificationResult | None = state.get("classification_result")
    if not clf_result or not clf_result.classifications:
        return "finalize_no_regression"

    candidates = [
        c for c in clf_result.classifications
        if c.status == ClassificationStatus.REGRESSION_CANDIDATE
    ]

    if candidates:
        return "reproduce"
    return "finalize_no_regression"


def route_after_reproduce(
    state: InvestigationWorkflowState,
) -> Literal["root_cause", "__end__"]:
    """Determine next step after reproduction."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"
    return "root_cause"


def route_after_root_cause(
    state: InvestigationWorkflowState,
) -> Literal["assemble", "__end__"]:
    """Determine next step after root cause localization."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"
    return "assemble"


def route_after_assemble(
    state: InvestigationWorkflowState,
) -> Literal["finalize", "__end__"]:
    """Determine next step after assembly."""
    if state.get("status") in [WorkflowStatus.FAILED.value, WorkflowStatus.CANCELLED.value]:
        return "__end__"
    return "finalize"
