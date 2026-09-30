"""Investigation Workflow Runner.

Coordinates asynchronous execution, cooperative cancellation,
checkpoint-based resumption, and event audit histories for RETRACE workflows.
"""

import asyncio
from typing import Any
from uuid import uuid4

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from apps.worker.browser.manager import BrowserManager
from apps.worker.orchestration.checkpoint import get_default_checkpointer
from apps.worker.orchestration.events import WorkflowEventBus, default_event_bus
from apps.worker.orchestration.graph import create_investigation_graph
from apps.worker.orchestration.models import (
    InvestigationRequest,
    InvestigationWorkflowState,
    WorkflowEvent,
    WorkflowEventType,
    WorkflowStatus,
)
from apps.worker.orchestration.nodes import InvestigationNodeAdapters
from packages.storage.base import ArtifactStorage
from packages.storage.local import LocalDiskArtifactStorage


class InvestigationWorkflowRunner:
    """Production runner executing and managing LangGraph investigation workflows."""

    def __init__(
        self,
        graph: CompiledStateGraph | None = None,
        adapters: InvestigationNodeAdapters | None = None,
        checkpointer: BaseCheckpointSaver | None = None,
        storage: ArtifactStorage | None = None,
        browser_manager: BrowserManager | None = None,
        event_bus: WorkflowEventBus | None = None,
    ) -> None:
        self.storage = storage or LocalDiskArtifactStorage()
        self.browser_manager = browser_manager
        self.checkpointer = checkpointer or get_default_checkpointer()
        self.event_bus = event_bus or default_event_bus
        self.adapters = adapters or InvestigationNodeAdapters(
            storage=self.storage,
            browser_manager=self.browser_manager,
            event_bus=self.event_bus,
        )
        self.graph = graph or create_investigation_graph(
            adapters=self.adapters,
            checkpointer=self.checkpointer,
        )

        self._active_tasks: dict[str, asyncio.Task[Any]] = {}
        self._active_states: dict[str, dict[str, Any]] = {}
        self._events: dict[str, list[WorkflowEvent]] = {}

        # Subscribe internal event recorder
        self.event_bus.subscribe(self._record_event)

    def _record_event(self, event: WorkflowEvent) -> None:
        """Internal callback accumulating events per workflow_id."""
        if event.workflow_id not in self._events:
            self._events[event.workflow_id] = []
        self._events[event.workflow_id].append(event)

    def _build_initial_state(
        self, request: InvestigationRequest, workflow_id: str
    ) -> InvestigationWorkflowState:
        """Create initial state payload for LangGraph invocation."""
        analysis_id_str = str(request.analysis_id)

        return InvestigationWorkflowState(
            workflow_id=workflow_id,
            project_id=request.project_id,
            analysis_id=analysis_id_str,
            version_a=request.version_a.model_dump(mode="json"),
            version_b=request.version_b.model_dump(mode="json"),
            budget=request.budget.model_dump(mode="json"),
            policy=request.policy.model_dump(mode="json"),
            status=WorkflowStatus.PENDING.value,
            current_phase="initialized",
            cancellation_requested=False,
            exploration_result_a=None,
            exploration_result_b=None,
            alignment_result=None,
            semantic_diff_result=None,
            classification_result=None,
            reproduction_suite=None,
            root_cause_suite=None,
            investigation_suite=None,
            artifacts=[],
            history=[],
            events=[],
            diagnostics=request.metadata,
            error_message=None,
            failure_type=None,
            retry_counts={},
        )

    async def run(
        self,
        request: InvestigationRequest,
        workflow_id: str | None = None,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Execute a complete investigation workflow asynchronously to completion."""
        w_id = workflow_id or f"wf_{request.analysis_id}"
        t_id = thread_id or w_id

        initial_state = self._build_initial_state(request, w_id)
        self._active_states[w_id] = dict(initial_state)

        self.event_bus.emit(
            WorkflowEventType.WORKFLOW_STARTED,
            workflow_id=w_id,
            analysis_id=request.analysis_id,
            node_name=None,
            details={"project_id": request.project_id},
        )

        config = {"configurable": {"thread_id": t_id}}
        result_state = await self.graph.ainvoke(initial_state, config=config)
        self._active_states[w_id] = dict(result_state)
        return result_state

    def start_background(
        self,
        request: InvestigationRequest,
        workflow_id: str | None = None,
        thread_id: str | None = None,
    ) -> str:
        """Launch investigation workflow in non-blocking background task."""
        w_id = workflow_id or f"wf_{request.analysis_id}"
        t_id = thread_id or w_id

        task = asyncio.create_task(self.run(request, workflow_id=w_id, thread_id=t_id))
        self._active_tasks[w_id] = task
        return w_id

    async def resume(
        self,
        workflow_id: str,
        thread_id: str | None = None,
    ) -> dict[str, Any]:
        """Resume an existing workflow from its last valid checkpoint."""
        t_id = thread_id or workflow_id
        config = {"configurable": {"thread_id": t_id}}

        self.event_bus.emit(
            WorkflowEventType.WORKFLOW_RESUMED,
            workflow_id=workflow_id,
            analysis_id=uuid4(),
            node_name=None,
            details={"thread_id": t_id},
        )

        # Retrieve checkpointed state or fallback to cached state
        state = dict(self._active_states.get(workflow_id, {}))
        state["status"] = WorkflowStatus.RUNNING.value
        state["failure_type"] = None
        state["error_message"] = None

        # Determine last completed node to resume from
        as_node = "validate_inputs"
        if state.get("root_cause_suite") is not None:
            as_node = "root_cause"
        elif state.get("reproduction_suite") is not None:
            as_node = "reproduce"
        elif state.get("classification_result") is not None:
            as_node = "classify"
        elif state.get("semantic_diff_result") is not None:
            as_node = "diff"
        elif state.get("alignment_result") is not None:
            as_node = "align"
        elif state.get("exploration_result_a") is not None:
            as_node = "explore"
        elif state.get("version_a") is not None:
            as_node = "prepare_versions"

        try:
            self.graph.update_state(config, state, as_node=as_node)
            result_state = await self.graph.ainvoke(None, config=config)
        except Exception:
            result_state = await self.graph.ainvoke(state, config=config)

        self._active_states[workflow_id] = dict(result_state)
        return result_state

    async def cancel(self, workflow_id: str) -> bool:
        """Request cooperative cancellation for an active workflow."""
        if workflow_id in self._active_states:
            self._active_states[workflow_id]["cancellation_requested"] = True

        task = self._active_tasks.get(workflow_id)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if workflow_id in self._active_states:
            self._active_states[workflow_id]["status"] = WorkflowStatus.CANCELLED.value

        self.event_bus.emit(
            WorkflowEventType.WORKFLOW_CANCELLED,
            workflow_id=workflow_id,
            analysis_id=uuid4(),
            node_name=None,
        )
        return True

    async def start_investigation(
        self,
        request: InvestigationRequest,
        workflow_id: str | None = None,
    ) -> str:
        """Start an investigation asynchronously and return workflow ID."""
        w_id = workflow_id or f"wf_{request.analysis_id}"
        await self.run(request, workflow_id=w_id)
        return w_id

    def get_status(self, workflow_id: str) -> dict[str, Any] | None:
        """Retrieve operational status dictionary for a workflow."""
        state = self._active_states.get(workflow_id)
        if not state:
            return None
        return {
            "workflow_id": workflow_id,
            "analysis_id": state.get("analysis_id"),
            "status": state.get("status"),
            "current_phase": state.get("current_phase"),
            "history": state.get("history", []),
            "failure_type": state.get("failure_type"),
            "error_message": state.get("error_message"),
        }

    async def resume_workflow(
        self,
        workflow_id: str,
        thread_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Resume an existing workflow or return None if not present."""
        if workflow_id not in self._active_states:
            return None
        return await self.resume(workflow_id=workflow_id, thread_id=thread_id)

    def get_state(self, workflow_id: str) -> dict[str, Any] | None:
        """Retrieve the latest in-memory state of a workflow."""
        return self._active_states.get(workflow_id)

    def get_events(self, workflow_id: str) -> list[WorkflowEvent]:
        """Retrieve all operational events emitted for a workflow."""
        return list(self._events.get(workflow_id, []))

    def get_history(self, workflow_id: str) -> list[dict[str, Any]]:
        """Retrieve node execution history for a workflow."""
        state = self._active_states.get(workflow_id)
        if not state:
            return []
        return list(state.get("history", []))


# Global default runner singleton
default_workflow_runner = InvestigationWorkflowRunner()

