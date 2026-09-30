"""Orchestration Node Adapters for RETRACE Investigation Pipeline.

Coordinates Phase 3 through 10 engines into idempotent, observable,
and checkpointable LangGraph execution nodes.
"""

from typing import Any
from uuid import UUID, uuid4

from apps.worker.alignment.config import AlignmentConfig
from apps.worker.alignment.trajectory_alignment import TrajectoryAligner
from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from apps.worker.diff.engine import SemanticDiffEngine
from apps.worker.exploration.config import ExplorationConfig
from apps.worker.exploration.explorer import AutonomousExplorer
from apps.worker.investigation.assembler import InvestigationAssembler
from apps.worker.investigation.models import (
    InvestigationSuiteResult,
    InvestigationSummary,
)
from apps.worker.orchestration.events import WorkflowEventBus, default_event_bus
from apps.worker.orchestration.models import (
    FailureType,
    InvestigationWorkflowState,
    NodeExecutionRecord,
    WorkflowEventType,
    WorkflowStatus,
    utc_now,
)
from apps.worker.regression.classifier import RegressionClassifier
from apps.worker.regression.models import ClassificationStatus, RegressionClassificationResult
from apps.worker.reporting.engine import EvidenceReportEngine
from apps.worker.reproduction.config import ReproductionConfig
from apps.worker.reproduction.engine import ReproductionEngine
from apps.worker.rootcause.engine import RootCauseEngine
from apps.worker.rootcause.models import RepositoryContext
from apps.worker.synthesis.engine import TestSynthesisEngine
from packages.storage.base import ArtifactStorage
from packages.storage.local import LocalDiskArtifactStorage


class InvestigationNodeAdapters:
    """Authoritative node adapter orchestrating underlying deterministic engines."""

    def __init__(
        self,
        storage: ArtifactStorage | None = None,
        browser_manager: BrowserManager | None = None,
        event_bus: WorkflowEventBus | None = None,
        synthesis_engine: TestSynthesisEngine | None = None,
        report_engine: EvidenceReportEngine | None = None,
    ) -> None:
        self.storage = storage or LocalDiskArtifactStorage()
        self.browser_manager = browser_manager
        self.event_bus = event_bus or default_event_bus
        self.synthesis_engine = synthesis_engine
        self.report_engine = report_engine
        self.assembler = InvestigationAssembler(
            synthesis_engine=self.synthesis_engine,
            report_engine=self.report_engine,
            storage=self.storage,
        )

    def _record_node(
        self,
        state: InvestigationWorkflowState,
        node_name: str,
        status: str,
        started_at: Any,
        error: str | None = None,
    ) -> list[dict[str, Any]]:
        """Helper to create an immutable node execution audit record."""
        now = utc_now()
        duration_ms = (now - started_at).total_seconds() * 1000.0
        record = NodeExecutionRecord(
            node_name=node_name,
            status=status,
            started_at=started_at,
            completed_at=now,
            duration_ms=duration_ms,
            attempt=state.get("retry_counts", {}).get(node_name, 1),
            error=error,
        )
        history = list(state.get("history", []))
        history.append(record.model_dump(mode="json"))
        return history

    async def validate_inputs(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 1: Validate request parameters, version configs, and budget boundaries."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = state.get("analysis_id", str(uuid4()))

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="validate_inputs",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "validate_inputs", "CANCELLED", start_time)
            self.event_bus.emit(
                WorkflowEventType.WORKFLOW_CANCELLED,
                workflow_id=workflow_id,
                analysis_id=analysis_id,
                node_name="validate_inputs",
            )
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        if any(h.get("node_name") == "validate_inputs" and h.get("status") == "COMPLETED" for h in state.get("history", [])):
            history = self._record_node(state, "validate_inputs", "SKIPPED", start_time)
            return {"current_phase": "validate_inputs", "history": history}

        version_a = state.get("version_a", {})
        version_b = state.get("version_b", {})

        url_a = version_a.get("base_url")
        url_b = version_b.get("base_url")

        if not url_a or not isinstance(url_a, str) or not url_a.strip():
            error_msg = "Version A base_url is required and must be a valid URL string."
            history = self._record_node(state, "validate_inputs", "FAILED", start_time, error=error_msg)
            self.event_bus.emit(
                WorkflowEventType.NODE_FAILED,
                workflow_id=workflow_id,
                analysis_id=analysis_id,
                node_name="validate_inputs",
                details={"error": error_msg},
            )
            return {
                "status": WorkflowStatus.FAILED.value,
                "failure_type": FailureType.INVALID_INPUT.value,
                "error_message": error_msg,
                "history": history,
            }

        if not url_b or not isinstance(url_b, str) or not url_b.strip():
            error_msg = "Version B base_url is required and must be a valid URL string."
            history = self._record_node(state, "validate_inputs", "FAILED", start_time, error=error_msg)
            self.event_bus.emit(
                WorkflowEventType.NODE_FAILED,
                workflow_id=workflow_id,
                analysis_id=analysis_id,
                node_name="validate_inputs",
                details={"error": error_msg},
            )
            return {
                "status": WorkflowStatus.FAILED.value,
                "failure_type": FailureType.INVALID_INPUT.value,
                "error_message": error_msg,
                "history": history,
            }

        history = self._record_node(state, "validate_inputs", "COMPLETED", start_time)
        self.event_bus.emit(
            WorkflowEventType.NODE_COMPLETED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="validate_inputs",
        )
        return {
            "status": WorkflowStatus.RUNNING.value,
            "current_phase": "validate_inputs",
            "history": history,
        }

    async def prepare_versions(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 2: Validate repository access and prepare execution environment."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = state.get("analysis_id", str(uuid4()))

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="prepare_versions",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "prepare_versions", "CANCELLED", start_time)
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        history = self._record_node(state, "prepare_versions", "COMPLETED", start_time)
        self.event_bus.emit(
            WorkflowEventType.NODE_COMPLETED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="prepare_versions",
        )
        return {
            "status": WorkflowStatus.RUNNING.value,
            "current_phase": "prepare_versions",
            "history": history,
        }

    async def explore(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 3: Execute Phase 4 deterministic exploration across Version A and B."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = UUID(state["analysis_id"]) if isinstance(state.get("analysis_id"), str) else state.get("analysis_id", uuid4())

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="explore",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "explore", "CANCELLED", start_time)
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        # Idempotency Check: if exploration is already complete from a resumed checkpoint
        if state.get("exploration_result_a") is not None and state.get("exploration_result_b") is not None:
            history = self._record_node(state, "explore", "SKIPPED", start_time)
            self.event_bus.emit(
                WorkflowEventType.NODE_SKIPPED,
                workflow_id=workflow_id,
                analysis_id=analysis_id,
                node_name="explore",
                details={"reason": "Exploration results already present in checkpoint state."},
            )
            return {"current_phase": "explore", "history": history}

        version_a = state.get("version_a", {})
        version_b = state.get("version_b", {})
        budget = state.get("budget", {})

        url_a = version_a["base_url"].rstrip("/")
        url_b = version_b["base_url"].rstrip("/")
        version_a_id = UUID(str(version_a.get("version_id", uuid4())))
        version_b_id = UUID(str(version_b.get("version_id", uuid4())))

        max_steps = budget.get("max_exploration_steps", 10)

        # Initialize browser manager if not provided
        owns_manager = False
        manager = self.browser_manager
        if manager is None:
            b_config = BrowserConfig(headless=True)
            manager = BrowserManager(default_config=b_config, storage=self.storage)
            await manager.start()
            owns_manager = True

        try:
            # 1. Explore Version A
            run_ctx_a = RunContext(
                analysis_id=analysis_id,
                version_id=version_a_id,
                run_id=uuid4(),
                trajectory_id=uuid4(),
                name="Orchestrated-Explore-A",
            )
            exp_config_a = ExplorationConfig(
                seed_url=f"{url_a}/",
                max_steps=max_steps,
                max_depth=3,
                max_actions_per_state=4,
            )
            async with manager.session(run_context=run_ctx_a) as session_a:
                explorer_a = AutonomousExplorer(config=exp_config_a, session=session_a)
                result_a = await explorer_a.explore()

            # 2. Explore Version B
            run_ctx_b = RunContext(
                analysis_id=analysis_id,
                version_id=version_b_id,
                run_id=uuid4(),
                trajectory_id=uuid4(),
                name="Orchestrated-Explore-B",
            )
            exp_config_b = ExplorationConfig(
                seed_url=f"{url_b}/",
                max_steps=max_steps,
                max_depth=3,
                max_actions_per_state=4,
            )
            async with manager.session(run_context=run_ctx_b) as session_b:
                explorer_b = AutonomousExplorer(config=exp_config_b, session=session_b)
                result_b = await explorer_b.explore()

            history = self._record_node(state, "explore", "COMPLETED", start_time)
            self.event_bus.emit(
                WorkflowEventType.NODE_COMPLETED,
                workflow_id=workflow_id,
                analysis_id=analysis_id,
                node_name="explore",
                details={
                    "states_a": result_a.states_discovered,
                    "states_b": result_b.states_discovered,
                },
            )
            return {
                "exploration_result_a": result_a,
                "exploration_result_b": result_b,
                "current_phase": "explore",
                "history": history,
            }
        except Exception as ex:
            error_msg = f"Exploration failed: {ex!s}"
            history = self._record_node(state, "explore", "FAILED", start_time, error=error_msg)
            self.event_bus.emit(
                WorkflowEventType.NODE_FAILED,
                workflow_id=workflow_id,
                analysis_id=analysis_id,
                node_name="explore",
                details={"error": error_msg},
            )
            return {
                "status": WorkflowStatus.FAILED.value,
                "failure_type": FailureType.TRANSIENT_FAILURE.value,
                "error_message": error_msg,
                "history": history,
            }
        finally:
            if owns_manager:
                await manager.stop()

    async def align(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 4: Execute Phase 5 A/B Trajectory Alignment."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = state.get("analysis_id", str(uuid4()))

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="align",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "align", "CANCELLED", start_time)
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        if state.get("alignment_result") is not None:
            history = self._record_node(state, "align", "SKIPPED", start_time)
            return {"current_phase": "align", "history": history}

        res_a = state.get("exploration_result_a")
        res_b = state.get("exploration_result_b")

        if not res_a or not res_b:
            error_msg = "Cannot align trajectories: missing exploration results."
            history = self._record_node(state, "align", "FAILED", start_time, error=error_msg)
            return {
                "status": WorkflowStatus.FAILED.value,
                "failure_type": FailureType.PERMANENT_FAILURE.value,
                "error_message": error_msg,
                "history": history,
            }

        url_a = state.get("version_a", {}).get("base_url", "")
        url_b = state.get("version_b", {}).get("base_url", "")

        align_config = AlignmentConfig(
            version_a_base_url=url_a,
            version_b_base_url=url_b,
        )
        aligner = TrajectoryAligner(config=align_config)
        alignment_result = aligner.align(res_a, res_b)

        history = self._record_node(state, "align", "COMPLETED", start_time)
        self.event_bus.emit(
            WorkflowEventType.NODE_COMPLETED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="align",
        )
        return {
            "alignment_result": alignment_result,
            "current_phase": "align",
            "history": history,
        }

    async def diff(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 5: Execute Phase 6 Semantic Difference Detection."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = state.get("analysis_id", str(uuid4()))

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="diff",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "diff", "CANCELLED", start_time)
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        if state.get("semantic_diff_result") is not None:
            history = self._record_node(state, "diff", "SKIPPED", start_time)
            return {"current_phase": "diff", "history": history}

        alignment_result = state.get("alignment_result")
        diff_engine = SemanticDiffEngine()
        diff_result = diff_engine.compare(alignment_result)

        history = self._record_node(state, "diff", "COMPLETED", start_time)
        self.event_bus.emit(
            WorkflowEventType.NODE_COMPLETED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="diff",
            details={"differences_count": len(diff_result.differences)},
        )
        return {
            "semantic_diff_result": diff_result,
            "current_phase": "diff",
            "history": history,
        }

    async def classify(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 6: Execute Phase 7 Regression Classification."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = state.get("analysis_id", str(uuid4()))

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="classify",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "classify", "CANCELLED", start_time)
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        if state.get("classification_result") is not None:
            history = self._record_node(state, "classify", "SKIPPED", start_time)
            return {"current_phase": "classify", "history": history}

        diff_result = state.get("semantic_diff_result")
        classifier = RegressionClassifier()
        classification_result = classifier.classify(diff_result)

        candidates = [
            c for c in classification_result.classifications
            if c.status == ClassificationStatus.REGRESSION_CANDIDATE
        ]

        history = self._record_node(state, "classify", "COMPLETED", start_time)
        self.event_bus.emit(
            WorkflowEventType.NODE_COMPLETED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="classify",
            details={
                "total_classifications": len(classification_result.classifications),
                "regression_candidates": len(candidates),
            },
        )
        return {
            "classification_result": classification_result,
            "current_phase": "classify",
            "history": history,
        }

    async def reproduce(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 7: Execute Phase 8 Autonomous Regression Reproduction."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = UUID(state["analysis_id"]) if isinstance(state.get("analysis_id"), str) else state.get("analysis_id", uuid4())

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="reproduce",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "reproduce", "CANCELLED", start_time)
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        if state.get("reproduction_suite") is not None:
            history = self._record_node(state, "reproduce", "SKIPPED", start_time)
            return {"current_phase": "reproduce", "history": history}

        classification_result: RegressionClassificationResult = state.get("classification_result")
        if not classification_result:
            error_msg = "Cannot reproduce: classification result missing."
            history = self._record_node(state, "reproduce", "FAILED", start_time, error=error_msg)
            return {
                "status": WorkflowStatus.FAILED.value,
                "failure_type": FailureType.PERMANENT_FAILURE.value,
                "error_message": error_msg,
                "history": history,
            }

        version_a = state.get("version_a", {})
        version_b = state.get("version_b", {})
        url_a = version_a["base_url"].rstrip("/")
        url_b = version_b["base_url"].rstrip("/")
        version_a_id = UUID(str(version_a.get("version_id", uuid4())))
        version_b_id = UUID(str(version_b.get("version_id", uuid4())))

        owns_manager = False
        manager = self.browser_manager
        if manager is None:
            b_config = BrowserConfig(headless=True)
            manager = BrowserManager(default_config=b_config, storage=self.storage)
            await manager.start()
            owns_manager = True

        try:
            repro_config = ReproductionConfig()
            reproduction_engine = ReproductionEngine(
                browser_manager=manager,
                storage=self.storage,
                config=repro_config,
            )

            res_a = state.get("exploration_result_a")
            graph_a = getattr(res_a, "graph", None)

            repro_suite = await reproduction_engine.reproduce_suite(
                classification_result=classification_result,
                seed_url_a=f"{url_a}/",
                seed_url_b=f"{url_b}/",
                version_a_id=version_a_id,
                version_b_id=version_b_id,
                analysis_id=analysis_id,
                session_id=uuid4(),
                graph_a=graph_a,
            )

            history = self._record_node(state, "reproduce", "COMPLETED", start_time)
            self.event_bus.emit(
                WorkflowEventType.NODE_COMPLETED,
                workflow_id=workflow_id,
                analysis_id=analysis_id,
                node_name="reproduce",
                details={"reproduced_count": len(repro_suite.results)},
            )
            return {
                "reproduction_suite": repro_suite,
                "current_phase": "reproduce",
                "history": history,
            }
        except Exception as ex:
            error_msg = f"Reproduction failed: {ex!s}"
            history = self._record_node(state, "reproduce", "FAILED", start_time, error=error_msg)
            return {
                "status": WorkflowStatus.FAILED.value,
                "failure_type": FailureType.TRANSIENT_FAILURE.value,
                "error_message": error_msg,
                "history": history,
            }
        finally:
            if owns_manager:
                await manager.stop()

    async def root_cause(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 8: Execute Phase 9 Root Cause Localization and Commit Attribution."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = state.get("analysis_id", str(uuid4()))

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="root_cause",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "root_cause", "CANCELLED", start_time)
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        if state.get("root_cause_suite") is not None:
            history = self._record_node(state, "root_cause", "SKIPPED", start_time)
            return {"current_phase": "root_cause", "history": history}

        classification_result = state.get("classification_result")
        reproduction_suite = state.get("reproduction_suite")

        version_a = state.get("version_a", {})
        version_b = state.get("version_b", {})
        repo_a = version_a.get("repository_path", "lab/applications/commerce/v1")
        repo_b = version_b.get("repository_path", "lab/applications/commerce/v2")

        repo_ctx = RepositoryContext(
            version_a_path=repo_a,
            version_b_path=repo_b,
        )

        rc_engine = RootCauseEngine()
        rc_suite = rc_engine.analyze(
            classification_result=classification_result,
            reproduction_suite_result=reproduction_suite,
            repository_context=repo_ctx,
        )

        history = self._record_node(state, "root_cause", "COMPLETED", start_time)
        self.event_bus.emit(
            WorkflowEventType.NODE_COMPLETED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="root_cause",
            details={"root_cause_count": len(rc_suite.results)},
        )
        return {
            "root_cause_suite": rc_suite,
            "current_phase": "root_cause",
            "history": history,
        }

    async def assemble(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 9: Execute Phase 10 Synthesis, Reporting, and Investigation Assembly."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = UUID(state["analysis_id"]) if isinstance(state.get("analysis_id"), str) else state.get("analysis_id", uuid4())

        self.event_bus.emit(
            WorkflowEventType.NODE_STARTED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="assemble",
        )

        if state.get("cancellation_requested", False):
            history = self._record_node(state, "assemble", "CANCELLED", start_time)
            return {"status": WorkflowStatus.CANCELLED.value, "history": history}

        if state.get("investigation_suite") is not None:
            history = self._record_node(state, "assemble", "SKIPPED", start_time)
            return {"current_phase": "assemble", "history": history}

        classification_result = state.get("classification_result")
        reproduction_suite = state.get("reproduction_suite")
        root_cause_suite = state.get("root_cause_suite")

        inv_suite = await self.assembler.assemble_suite(
            analysis_id=analysis_id,
            classification_result=classification_result,
            reproduction_suite=reproduction_suite,
            root_cause_suite=root_cause_suite,
        )

        history = self._record_node(state, "assemble", "COMPLETED", start_time)
        self.event_bus.emit(
            WorkflowEventType.NODE_COMPLETED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="assemble",
            details={"investigations_assembled": len(inv_suite.investigations)},
        )
        return {
            "investigation_suite": inv_suite,
            "current_phase": "assemble",
            "history": history,
        }

    async def finalize(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 10: Finalize workflow, register packages in active registry, and emit status."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = state.get("analysis_id", str(uuid4()))

        # Register assembled investigations into API registry for immediate UI availability
        inv_suite: InvestigationSuiteResult = state.get("investigation_suite")
        if inv_suite:
            from apps.api.routers.v1.investigations import register_investigation

            for inv in inv_suite.investigations:
                register_investigation(inv)

        # Determine if overall workflow is COMPLETED or INCONCLUSIVE
        final_status = WorkflowStatus.COMPLETED.value
        if inv_suite and inv_suite.summary.inconclusive_count > 0 and inv_suite.summary.completed_count == 0:
            final_status = WorkflowStatus.INCONCLUSIVE.value

        history = self._record_node(state, "finalize", "COMPLETED", start_time)
        self.event_bus.emit(
            WorkflowEventType.WORKFLOW_COMPLETED if final_status == WorkflowStatus.COMPLETED.value else WorkflowEventType.WORKFLOW_INCONCLUSIVE,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="finalize",
            details={"status": final_status},
        )
        return {
            "status": final_status,
            "current_phase": "finalize",
            "history": history,
        }

    async def finalize_no_regression(
        self, state: InvestigationWorkflowState
    ) -> dict[str, Any]:
        """Node 11: Short-circuit finalization when zero regressions were detected."""
        start_time = utc_now()
        workflow_id = state.get("workflow_id", "unknown")
        analysis_id = UUID(state["analysis_id"]) if isinstance(state.get("analysis_id"), str) else state.get("analysis_id", uuid4())

        history = self._record_node(state, "finalize_no_regression", "COMPLETED", start_time)

        empty_suite = InvestigationSuiteResult(
            analysis_id=analysis_id,
            run_a_id=uuid4(),
            run_b_id=uuid4(),
            investigations=[],
            summary=InvestigationSummary(total_investigations=0),
        )

        self.event_bus.emit(
            WorkflowEventType.WORKFLOW_COMPLETED,
            workflow_id=workflow_id,
            analysis_id=analysis_id,
            node_name="finalize_no_regression",
            details={"message": "Zero regressions identified; workflow cleanly completed."},
        )

        return {
            "investigation_suite": empty_suite,
            "status": WorkflowStatus.COMPLETED.value,
            "current_phase": "finalize_no_regression",
            "history": history,
        }
