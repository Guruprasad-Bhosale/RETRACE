"""RETRACE Benchmark Runner.

Executes autonomous investigation workflows against benchmark suites in isolated
environments, measures operational timings, evaluates subsystem outputs against
oracles, and computes aggregated suite statistics.
"""

import time
from pathlib import Path
from uuid import uuid4

from apps.worker.evaluation.adapter import EvaluationAdapter
from apps.worker.evaluation.metrics import summarize_suite_metrics
from apps.worker.evaluation.models import (
    EvaluationResult,
    EvaluationSuiteResult,
)
from apps.worker.orchestration.models import (
    InvestigationRequest,
)
from apps.worker.orchestration.runner import InvestigationWorkflowRunner
from benchmarks.models import BenchmarkCase, BenchmarkSuite
from packages.storage.local import LocalDiskArtifactStorage


class BenchmarkRunner:
    """Orchestrates benchmark case executions and evaluates outputs against oracles."""

    def __init__(
        self,
        workflow_runner: InvestigationWorkflowRunner | None = None,
        storage_root: Path | str | None = None,
    ) -> None:
        self.storage_root = Path(storage_root) if storage_root else Path("artifacts/evaluation")
        self.storage = LocalDiskArtifactStorage(base_dir=self.storage_root)
        self.workflow_runner = workflow_runner or InvestigationWorkflowRunner(storage=self.storage)
        self.adapter = EvaluationAdapter()

    async def run_case(self, case: BenchmarkCase, repeat_index: int = 0) -> EvaluationResult:
        """Execute a single benchmark case and evaluate its result."""
        wf_id = f"eval_{case.case_id}_{uuid4().hex[:8]}"
        t_start = time.perf_counter()

        # Build clean investigation request from BenchmarkInput ONLY
        req = InvestigationRequest(
            project_id=case.input_config.project_id,
            version_a=case.input_config.version_a,
            version_b=case.input_config.version_b,
            budget=case.input_config.budget,
            policy=case.input_config.policy,
            metadata={"benchmark_case_id": case.case_id, "repeat_index": repeat_index},
        )

        try:
            workflow_state = await self.workflow_runner.run(req, workflow_id=wf_id)
        except Exception as ex:
            workflow_state = {
                "status": "FAILED",
                "error_message": str(ex),
                "history": [],
            }

        elapsed = time.perf_counter() - t_start

        # Extract phase durations from state history
        phase_timings: dict[str, float] = {}
        for record in workflow_state.get("history", []):
            node = record.get("node_name") or record.get("node") or "unknown"
            duration = record.get("duration_ms", 0.0) / 1000.0
            phase_timings[node] = duration

        phase_timings["total"] = elapsed

        # Evaluate against oracle
        eval_res = self.adapter.evaluate_case(
            case=case,
            investigation_output=workflow_state,
            workflow_id=wf_id,
            analysis_id=req.analysis_id,
            phase_timings=phase_timings,
            resource_stats={"nodes_executed": len(workflow_state.get("history", []))},
        )

        return eval_res

    async def run_suite(
        self,
        suite: BenchmarkSuite,
        case_filter: list[str] | None = None,
    ) -> EvaluationSuiteResult:
        """Execute all cases in a benchmark suite and produce a suite summary."""
        results: list[EvaluationResult] = []

        cases_to_run = [
            c for c in suite.cases
            if case_filter is None or c.case_id in case_filter or any(tag in case_filter for tag in c.tags)
        ]

        for case in cases_to_run:
            res = await self.run_case(case)
            results.append(res)

        summary = summarize_suite_metrics(results)

        return EvaluationSuiteResult(
            suite_id=suite.suite_id,
            suite_name=suite.name,
            results=results,
            summary=summary,
            environment_info={"total_suite_cases": len(suite.cases), "executed_cases": len(results)},
        )

    async def run_repeated_case(
        self,
        case: BenchmarkCase,
        repetitions: int = 3,
    ) -> tuple[list[EvaluationResult], float]:
        """Execute a single benchmark case N times to evaluate deterministic stability."""
        results: list[EvaluationResult] = []
        signatures: set[str] = set()

        for i in range(repetitions):
            res = await self.run_case(case, repeat_index=i)
            results.append(res)
            signatures.add(res.deterministic_signature)

        identical_runs = 0
        if results:
            first_sig = results[0].deterministic_signature
            identical_runs = sum(1 for r in results if r.deterministic_signature == first_sig)

        stability_rate = identical_runs / repetitions if repetitions > 0 else 1.0
        return results, stability_rate
