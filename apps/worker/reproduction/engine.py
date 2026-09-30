"""Autonomous Regression Reproduction Engine Facade."""

import time
from uuid import UUID, uuid4

from apps.worker.browser.manager import BrowserManager
from apps.worker.exploration.state import ExplorationGraph
from apps.worker.regression.models import (
    ClassificationStatus,
    RegressionClassification,
    RegressionClassificationResult,
)
from apps.worker.reproduction.config import ReproductionConfig
from apps.worker.reproduction.errors import PathPlanningError, SafetyViolationError
from apps.worker.reproduction.models import (
    MatchStatus,
    ReproductionAttemptResult,
    ReproductionEvidence,
    ReproductionPath,
    ReproductionResult,
    ReproductionStatus,
    ReproductionStrategy,
    ReproductionSuiteResult,
    ReproductionSummary,
    compute_deterministic_reproduction_id,
)
from apps.worker.reproduction.planner import ReproductionPathPlanner
from apps.worker.reproduction.replay import ReproductionReplayEngine
from apps.worker.reproduction.safety import ReproductionSafetyGuard
from apps.worker.reproduction.verification import ReproductionVerifier
from packages.domain.models import Action
from packages.storage.base import ArtifactStorage


class ReproductionEngine:
    """Coordinates deterministic path planning, safety validation, dual replay, and regression verification."""

    def __init__(
        self,
        browser_manager: BrowserManager,
        storage: ArtifactStorage,
        config: ReproductionConfig | None = None,
    ) -> None:
        self.browser_manager = browser_manager
        self.storage = storage
        self.config = config or ReproductionConfig()
        self.replay_engine = ReproductionReplayEngine(
            browser_manager=self.browser_manager,
            storage=self.storage,
            config=self.config,
        )
        self.safety_guard = ReproductionSafetyGuard(self.config.safety)

    async def reproduce_classification(
        self,
        classification: RegressionClassification,
        seed_url_a: str,
        seed_url_b: str,
        version_a_id: UUID,
        version_b_id: UUID,
        analysis_id: UUID,
        session_id: UUID,
        trajectory_id: UUID,
        graph: ExplorationGraph | None = None,
        actions: list[Action] | None = None,
    ) -> ReproductionResult:
        """Attempt to deterministically reproduce a single classified regression."""
        start_time = time.perf_counter()
        strategy = ReproductionStrategy.DIRECT_REPLAY

        # 1. Path Planning
        try:
            if graph is not None:
                path = ReproductionPathPlanner.plan_path_from_graph(
                    classification=classification,
                    graph=graph,
                    seed_url=seed_url_a,
                    trajectory_id=trajectory_id,
                )
            elif actions is not None:
                path = ReproductionPathPlanner.plan_path_from_actions(
                    classification=classification,
                    actions=actions,
                    seed_url=seed_url_a,
                    trajectory_id=trajectory_id,
                )
            else:
                raise PathPlanningError("Neither graph nor actions provided for path planning.")
        except Exception as ex:
            empty_path = ReproductionPath(
                path_id="invalid",
                trajectory_id=trajectory_id,
                classification_id=classification.classification_id,
                difference_id=classification.difference_id,
                seed_url=seed_url_a,
                path_signature="invalid",
            )
            repro_id = compute_deterministic_reproduction_id(
                classification.classification_id,
                version_a_id,
                version_b_id,
                trajectory_id,
                "invalid",
                strategy,
            )
            return ReproductionResult(
                reproduction_id=repro_id,
                classification_id=classification.classification_id,
                difference_id=classification.difference_id,
                rule_id=classification.rule_id,
                category=classification.category.value,
                status=ReproductionStatus.FAILED,
                strategy=strategy,
                path=empty_path,
                attempts=[],
                total_duration_ms=(time.perf_counter() - start_time) * 1000.0,
                metadata={"failure_reason": f"Path planning failed: {ex}"},
            )

        # 2. Safety Validation
        try:
            self.safety_guard.validate_path_safety(path)
        except SafetyViolationError as s_ex:
            repro_id = compute_deterministic_reproduction_id(
                classification.classification_id,
                version_a_id,
                version_b_id,
                trajectory_id,
                path.path_signature,
                strategy,
            )
            return ReproductionResult(
                reproduction_id=repro_id,
                classification_id=classification.classification_id,
                difference_id=classification.difference_id,
                rule_id=classification.rule_id,
                category=classification.category.value,
                status=ReproductionStatus.BLOCKED,
                strategy=strategy,
                path=path,
                attempts=[],
                total_duration_ms=(time.perf_counter() - start_time) * 1000.0,
                metadata={"blocked_reason": str(s_ex)},
            )

        # 3. Dual-Version Replay Execution & Verification Loop
        attempts: list[ReproductionAttemptResult] = []
        final_status = ReproductionStatus.NOT_REPRODUCED
        final_verification = None

        is_perf = classification.category.value == "PERFORMANCE" or classification.rule_id.startswith("PERF-")

        for attempt_num in range(1, self.config.max_attempts_per_classification + 1):
            att_start = time.perf_counter()
            current_strategy = (
                strategy if attempt_num == 1 else ReproductionStrategy.RECOVERY_REPLAY
            )

            try:
                evidence = await self.replay_engine.execute_dual_replay(
                    path=path,
                    version_a_id=version_a_id,
                    version_b_id=version_b_id,
                    seed_url_a=seed_url_a,
                    seed_url_b=seed_url_b,
                    analysis_id=analysis_id,
                    session_id=session_id,
                    is_performance_classification=is_perf,
                )

                # Verification
                verification = ReproductionVerifier.verify(
                    classification=classification,
                    observations_a=evidence.observations_a,
                    observations_b=evidence.observations_b,
                    policy=self.config.verification,
                    sample_timings_a=evidence.sample_measurements_ms_a,
                    sample_timings_b=evidence.sample_measurements_ms_b,
                )
                final_verification = verification

                if verification.match_status == MatchStatus.FULL_MATCH:
                    att_status = ReproductionStatus.REPRODUCED
                elif verification.match_status == MatchStatus.PARTIAL_MATCH:
                    att_status = (
                        ReproductionStatus.REPRODUCED
                        if self.config.verification.allow_partial_match_as_reproduced
                        else ReproductionStatus.INCONCLUSIVE
                    )
                elif verification.match_status == MatchStatus.NOT_COMPARABLE:
                    att_status = ReproductionStatus.INCONCLUSIVE
                else:
                    att_status = ReproductionStatus.NOT_REPRODUCED

                attempt_result = ReproductionAttemptResult(
                    attempt_id=uuid4(),
                    attempt_number=attempt_num,
                    strategy=current_strategy,
                    status=att_status,
                    verification=verification,
                    evidence=evidence,
                    duration_ms=(time.perf_counter() - att_start) * 1000.0,
                )
                attempts.append(attempt_result)

                if att_status == ReproductionStatus.REPRODUCED:
                    final_status = ReproductionStatus.REPRODUCED
                    break
                else:
                    final_status = att_status

            except Exception as ex:
                attempt_result = ReproductionAttemptResult(
                    attempt_id=uuid4(),
                    attempt_number=attempt_num,
                    strategy=current_strategy,
                    status=ReproductionStatus.FAILED,
                    evidence=ReproductionEvidence(attempt_id=uuid4()),
                    failure_reason=str(ex),
                    duration_ms=(time.perf_counter() - att_start) * 1000.0,
                )
                attempts.append(attempt_result)
                final_status = ReproductionStatus.FAILED

        repro_id = compute_deterministic_reproduction_id(
            classification.classification_id,
            version_a_id,
            version_b_id,
            trajectory_id,
            path.path_signature,
            strategy,
        )

        return ReproductionResult(
            reproduction_id=repro_id,
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            rule_id=classification.rule_id,
            category=classification.category.value,
            status=final_status,
            strategy=strategy,
            path=path,
            attempts=attempts,
            final_verification=final_verification,
            total_duration_ms=(time.perf_counter() - start_time) * 1000.0,
        )

    async def reproduce_suite(
        self,
        classification_result: RegressionClassificationResult,
        seed_url_a: str,
        seed_url_b: str,
        version_a_id: UUID,
        version_b_id: UUID,
        analysis_id: UUID,
        session_id: UUID,
        graph_a: ExplorationGraph | None = None,
        actions_a: list[Action] | None = None,
    ) -> ReproductionSuiteResult:
        """Execute autonomous reproduction across all candidate regression classifications."""
        # Filter candidate regressions
        candidates = [
            c
            for c in classification_result.classifications
            if c.status == ClassificationStatus.REGRESSION_CANDIDATE
        ]
        # Sort deterministically
        sorted_candidates = sorted(candidates, key=lambda c: c.deterministic_sort_key())

        results: list[ReproductionResult] = []
        summary = ReproductionSummary()

        for c in sorted_candidates:
            res = await self.reproduce_classification(
                classification=c,
                seed_url_a=seed_url_a,
                seed_url_b=seed_url_b,
                version_a_id=version_a_id,
                version_b_id=version_b_id,
                analysis_id=analysis_id,
                session_id=session_id,
                trajectory_id=classification_result.trajectory_a_id,
                graph=graph_a,
                actions=actions_a,
            )
            results.append(res)
            summary.total_reproductions_attempted += 1

            if res.status == ReproductionStatus.REPRODUCED:
                summary.reproduced += 1
            elif res.status == ReproductionStatus.NOT_REPRODUCED:
                summary.not_reproduced += 1
            elif res.status == ReproductionStatus.INCONCLUSIVE:
                summary.inconclusive += 1
            elif res.status == ReproductionStatus.BLOCKED:
                summary.blocked += 1
            elif res.status == ReproductionStatus.FAILED:
                summary.failed += 1

        return ReproductionSuiteResult(
            run_a_id=classification_result.run_a_id,
            run_b_id=classification_result.run_b_id,
            trajectory_a_id=classification_result.trajectory_a_id,
            trajectory_b_id=classification_result.trajectory_b_id,
            results=results,
            summary=summary,
        )
