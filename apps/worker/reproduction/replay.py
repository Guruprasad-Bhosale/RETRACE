"""Deterministic Replay Engine Coordinating Multi-Modal Browser Sessions."""

from uuid import UUID, uuid4

from apps.worker.browser.actions import ExplicitActionRequest
from apps.worker.browser.config import BrowserConfig, RunContext
from apps.worker.browser.manager import BrowserManager
from apps.worker.reproduction.artifacts import ReproductionArtifactMapper
from apps.worker.reproduction.config import ReproductionConfig
from apps.worker.reproduction.models import (
    ReproductionEvidence,
    ReproductionObservation,
    ReproductionPath,
)
from apps.worker.reproduction.recovery import BoundedRecoveryManager
from packages.domain.models import ArtifactReference
from packages.storage.base import ArtifactStorage


class ReproductionReplayEngine:
    """Executes deterministic action paths against Version A and Version B browser sessions."""

    def __init__(
        self,
        browser_manager: BrowserManager,
        storage: ArtifactStorage,
        config: ReproductionConfig,
    ) -> None:
        self.browser_manager = browser_manager
        self.storage = storage
        self.config = config

    async def execute_single_replay(
        self,
        path: ReproductionPath,
        version_id: UUID,
        target_url: str,
        analysis_id: UUID,
        session_id: UUID,
    ) -> tuple[list[ReproductionObservation], list[ArtifactReference], bool, str | None]:
        """Replay a ReproductionPath sequentially on a single application version."""
        run_id = uuid4()
        run_context = RunContext(
            analysis_id=analysis_id,
            version_id=version_id,
            run_id=run_id,
            trajectory_id=path.trajectory_id,
        )

        browser_config = BrowserConfig()
        browser_config.navigation_timeout_ms = self.config.replay.navigation_timeout_ms
        browser_config.action_timeout_ms = self.config.replay.action_timeout_ms
        browser_config.stabilization_timeout_ms = self.config.replay.stabilization_timeout_ms

        observations: list[ReproductionObservation] = []
        recovery_manager = BoundedRecoveryManager(self.config.recovery)
        overall_success = True
        failure_reason: str | None = None

        session = await self.browser_manager.create_session(
            config=browser_config,
            run_context=run_context,
            storage=self.storage,
        )

        try:
            # 1. Navigate to target seed URL & initialize Step 0
            await session.page.goto(target_url, timeout=self.config.replay.navigation_timeout_ms)
            step_0_obs = await session.initialize()
            observations.append(
                ReproductionArtifactMapper.from_domain_observation(
                    step_0_obs, version_id=version_id, action_success=True
                )
            )

            # 2. Step through each causal action in sequence
            for step in path.steps:
                target_identity = step.stable_target_identity or step.raw_target
                action_req = ExplicitActionRequest(
                    action_type=step.action_type,
                    target=target_identity,
                    target_strategy=step.target_strategy if step.target_strategy in ("auto", "testid", "role", "label", "text", "css", "url") else "auto",
                    value=step.value,
                    coordinates=step.coordinates,
                    timeout_ms=step.timeout_ms,
                    metadata={"role": step.target_role, "name": step.accessible_name},
                )

                action_res, obs = await session.step(action_req)

                # If action failed, check bounded precondition recovery
                if not action_res.success and recovery_manager.can_attempt_recovery():
                    restored = await recovery_manager.restore_precondition(
                        session=session,
                        step=step,
                        expected_url=observations[-1].url if observations else None,
                    )
                    if restored:
                        # Retry the exact same step once
                        action_res, obs = await session.step(action_req)

                repro_obs = ReproductionArtifactMapper.from_domain_observation(
                    obs,
                    version_id=version_id,
                    duration_ms=action_res.duration_ms,
                    action_success=action_res.success,
                    error_message=action_res.error_message,
                )
                observations.append(repro_obs)

                if not action_res.success:
                    overall_success = False
                    failure_reason = action_res.error_message or f"Action failed at step {step.step_index}"
                    # Do not continue sequence if intermediate precondition is broken
                    break

        except Exception as ex:
            overall_success = False
            failure_reason = str(ex)
        finally:
            session_artifacts = await session.close()

        return observations, session_artifacts, overall_success, failure_reason

    async def execute_dual_replay(
        self,
        path: ReproductionPath,
        version_a_id: UUID,
        version_b_id: UUID,
        seed_url_a: str,
        seed_url_b: str,
        analysis_id: UUID,
        session_id: UUID,
        is_performance_classification: bool = False,
    ) -> ReproductionEvidence:
        """Execute dual-version replay across Version A and Version B."""
        # 1. Version A Replay
        obs_a, artifacts_a, _, _ = await self.execute_single_replay(
            path=path,
            version_id=version_a_id,
            target_url=seed_url_a,
            analysis_id=analysis_id,
            session_id=session_id,
        )

        # 2. Version B Replay
        obs_b, artifacts_b, _, _ = await self.execute_single_replay(
            path=path,
            version_id=version_b_id,
            target_url=seed_url_b,
            analysis_id=analysis_id,
            session_id=session_id,
        )

        samples_a: list[float] = [obs_a[-1].duration_ms] if obs_a else []
        samples_b: list[float] = [obs_b[-1].duration_ms] if obs_b else []

        # 3. Repeated performance sampling if requested
        if is_performance_classification and self.config.performance_sampling.sample_runs > 1:
            for _ in range(self.config.performance_sampling.sample_runs - 1):
                s_obs_a, _, _, _ = await self.execute_single_replay(
                    path=path,
                    version_id=version_a_id,
                    target_url=seed_url_a,
                    analysis_id=analysis_id,
                    session_id=session_id,
                )
                s_obs_b, _, _, _ = await self.execute_single_replay(
                    path=path,
                    version_id=version_b_id,
                    target_url=seed_url_b,
                    analysis_id=analysis_id,
                    session_id=session_id,
                )
                if s_obs_a:
                    samples_a.append(s_obs_a[-1].duration_ms)
                if s_obs_b:
                    samples_b.append(s_obs_b[-1].duration_ms)

        combined_artifacts = artifacts_a + artifacts_b

        return ReproductionEvidence(
            attempt_id=uuid4(),
            observations_a=obs_a,
            observations_b=obs_b,
            sample_measurements_ms_a=samples_a,
            sample_measurements_ms_b=samples_b,
            artifact_references=combined_artifacts,
        )
