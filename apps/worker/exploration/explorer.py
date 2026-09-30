"""Autonomous Deterministic State-Space Exploration Engine."""

import time

from apps.worker.browser.actions import ExplicitActionRequest
from apps.worker.browser.session import BrowserSession
from apps.worker.exploration.backtracking import Backtracker
from apps.worker.exploration.candidate import CandidateGenerator
from apps.worker.exploration.config import ExplorationConfig
from apps.worker.exploration.coverage import CoverageTracker
from apps.worker.exploration.diagnostics import ExplorationResult
from apps.worker.exploration.frontier import ExplorationFrontier, FrontierItem
from apps.worker.exploration.guards import ActionSafetyGuard, URLSafetyGuard
from apps.worker.exploration.route_tracker import RouteTracker
from apps.worker.exploration.state import ExplorationGraph, ExplorationState
from apps.worker.exploration.state_identity import StateIdentityCalculator
from apps.worker.exploration.transition import ExplorationTransition, compute_transition_id
from packages.domain.models import ActionType, ArtifactReference


class AutonomousExplorer:
    """Orchestrates deterministic breadth-first application state exploration."""

    def __init__(
        self,
        config: ExplorationConfig,
        session: BrowserSession,
    ) -> None:
        self.config = config
        self.session = session
        self.safety_guard = ActionSafetyGuard(config)
        self.url_guard = URLSafetyGuard(config)
        self.candidate_generator = CandidateGenerator(
            config=config,
            safety_guard=self.safety_guard,
            url_guard=self.url_guard,
        )
        self.graph = ExplorationGraph()
        self.frontier = ExplorationFrontier()
        self.backtracker = Backtracker(graph=self.graph, seed_url=config.seed_url)
        self.route_tracker = RouteTracker()
        self.coverage_tracker = CoverageTracker()

        self.consecutive_action_failures: int = 0
        self.consecutive_nav_failures: int = 0
        self.current_state_id: str | None = None
        self.start_time: float = 0.0

    async def explore(self) -> ExplorationResult:
        """Execute deterministic autonomous exploration starting from seed URL."""
        self.start_time = time.perf_counter()
        termination_reason = "frontier_exhausted"

        # ----------------------------------------------------------------------
        # 1. Seed URL Navigation & Root State Discovery (Step 0)
        # ----------------------------------------------------------------------
        seed_req = ExplicitActionRequest(
            action_type=ActionType.NAVIGATE,
            target=self.config.seed_url,
            timeout_ms=self.config.action_timeout_ms,
        )
        act_res_0, obs_0 = await self.session.step(seed_req)
        if not act_res_0.success:
            return self._build_result(
                termination_reason=f"seed_navigation_failed: {act_res_0.error_message}"
            )

        root_route = self.route_tracker.record_url(obs_0.state.url)
        root_ident = StateIdentityCalculator.calculate(obs_0)
        self.current_state_id = root_ident.state_id

        # Capture element inventory on root state
        root_inventory = await self.session.inventory.capture(self.session.page)
        root_candidates = self.candidate_generator.generate_candidates(
            inventory=root_inventory,
            source_state_id=root_ident.state_id,
            source_observation_id=obs_0.id,
            current_url=obs_0.state.url,
        )

        root_state = ExplorationState(
            state_id=root_ident.state_id,
            observation_id=obs_0.id,
            url=obs_0.state.url,
            route=root_route,
            depth=0,
            visit_count=1,
            available_candidates=root_candidates,
        )
        self.graph.add_state(root_state)

        # Enqueue root candidates to BFS frontier
        for candidate in root_candidates:
            trans_id = compute_transition_id(
                from_state_id=root_ident.state_id,
                action_type=candidate.action_type,
                stable_target_identity=candidate.stable_element_id,
                normalized_input=candidate.value,
            )
            self.frontier.push(
                FrontierItem(from_state_id=root_ident.state_id, candidate=candidate, depth=1),
                transition_id=trans_id,
            )

        # ----------------------------------------------------------------------
        # 2. Main Deterministic BFS Exploration Loop
        # ----------------------------------------------------------------------
        while not self.frontier.is_empty():
            # Check hard limits
            elapsed = time.perf_counter() - self.start_time
            if elapsed >= self.config.exploration_timeout_sec:
                termination_reason = "timeout"
                break

            if len(self.session.actions) >= self.config.max_steps:
                termination_reason = "max_steps_reached"
                break

            if self.consecutive_action_failures >= self.config.max_action_failures:
                termination_reason = "excessive_action_failures"
                break

            if self.consecutive_nav_failures >= self.config.max_navigation_failures:
                termination_reason = "excessive_navigation_failures"
                break

            # Pop next candidate transition from BFS FIFO queue
            item = self.frontier.pop()
            if not item:
                break

            from_state = self.graph.get_state(item.from_state_id)
            if not from_state:
                continue

            # Check if parent state exceeded repeated visits
            if from_state.visit_count > self.config.max_repeated_state_visits:
                self.coverage_tracker.record_skipped_candidate()
                continue

            if item.depth > self.config.max_depth:
                self.coverage_tracker.record_skipped_candidate()
                continue

            # Backtrack if current browser page is not at the candidate's source state
            if self.current_state_id != item.from_state_id:
                try:
                    await self.backtracker.recover_to_state(
                        session=self.session,
                        current_state_id=self.current_state_id or "",
                        target_state_id=item.from_state_id,
                    )
                    self.current_state_id = item.from_state_id
                    self.consecutive_nav_failures = 0
                except Exception:
                    self.consecutive_nav_failures += 1
                    self.coverage_tracker.record_skipped_candidate()
                    continue

            # Execute candidate action through Phase 3
            candidate = item.candidate
            action_req = ExplicitActionRequest(
                action_type=candidate.action_type,
                target=candidate.target,
                target_strategy=candidate.target_strategy,
                value=candidate.value,
                timeout_ms=self.config.action_timeout_ms,
            )
            act_res, next_obs = await self.session.step(action_req)

            if not act_res.success:
                self.consecutive_action_failures += 1
            else:
                self.consecutive_action_failures = 0

            # Calculate resulting state identity
            next_ident = StateIdentityCalculator.calculate(next_obs)
            next_route = self.route_tracker.record_url(next_obs.state.url)
            is_repeated = self.graph.has_state(next_ident.state_id)

            # Record transition in state graph & coverage tracker
            trans_id = compute_transition_id(
                from_state_id=item.from_state_id,
                action_type=candidate.action_type,
                stable_target_identity=candidate.stable_element_id,
                normalized_input=candidate.value,
            )
            transition = ExplorationTransition(
                transition_id=trans_id,
                from_state_id=item.from_state_id,
                to_state_id=next_ident.state_id,
                action_id=act_res.action.id,
                action_type=candidate.action_type,
                target=candidate.target,
                target_identity=candidate.stable_element_id,
                value=candidate.value,
                observation_id=next_obs.id,
                success=act_res.success,
                error_message=act_res.error_message,
                duration_ms=act_res.duration_ms,
                step_index=self.session.current_step,
            )
            self.graph.record_transition(transition)
            self.coverage_tracker.record_transition(
                target_identity=candidate.stable_element_id,
                success=act_res.success,
                depth=item.depth,
                is_repeated_state=is_repeated,
            )

            # If resulting state is newly discovered, inspect element inventory and enqueue candidates
            if not is_repeated and act_res.success:
                new_inventory = await self.session.inventory.capture(self.session.page)
                new_candidates = self.candidate_generator.generate_candidates(
                    inventory=new_inventory,
                    source_state_id=next_ident.state_id,
                    source_observation_id=next_obs.id,
                    current_url=next_obs.state.url,
                )

                new_state = ExplorationState(
                    state_id=next_ident.state_id,
                    observation_id=next_obs.id,
                    url=next_obs.state.url,
                    route=next_route,
                    depth=item.depth,
                    visit_count=1,
                    parent_state_id=item.from_state_id,
                    incoming_transition_id=trans_id,
                    available_candidates=new_candidates,
                )
                self.graph.add_state(new_state)

                # Push next candidates to frontier if within depth limit
                if item.depth < self.config.max_depth:
                    for next_cand in new_candidates:
                        cand_trans_id = compute_transition_id(
                            from_state_id=next_ident.state_id,
                            action_type=next_cand.action_type,
                            stable_target_identity=next_cand.stable_element_id,
                            normalized_input=next_cand.value,
                        )
                        self.frontier.push(
                            FrontierItem(
                                from_state_id=next_ident.state_id,
                                candidate=next_cand,
                                depth=item.depth + 1,
                            ),
                            transition_id=cand_trans_id,
                        )
            elif is_repeated:
                # Increment state visit count on existing state
                existing_state = self.graph.get_state(next_ident.state_id)
                if existing_state:
                    existing_state.visit_count += 1

            self.current_state_id = next_ident.state_id

        return self._build_result(termination_reason=termination_reason)

    def _build_result(self, termination_reason: str) -> ExplorationResult:
        """Assemble structured exploration result summary."""
        elapsed = max(0.0, time.perf_counter() - self.start_time)
        routes = self.route_tracker.get_routes()
        coverage = self.coverage_tracker.build_metrics(
            unique_states_count=len(self.graph.states),
            routes=routes,
        )

        all_artifacts: list[ArtifactReference] = []
        for obs in self.session.observations:
            all_artifacts.extend(obs.artifacts)

        return ExplorationResult(
            run_id=self.session.run_context.run_id,
            trajectory_id=self.session.run_context.trajectory_id,
            seed_url=self.config.seed_url,
            total_steps=len(self.session.actions),
            states_discovered=len(self.graph.states),
            transitions_count=len(self.graph.transitions),
            successful_transitions=self.coverage_tracker.transitions_successful,
            failed_transitions=self.coverage_tracker.transitions_failed,
            skipped_candidates=self.coverage_tracker.candidates_skipped,
            unique_routes=routes,
            termination_reason=termination_reason,
            elapsed_time_sec=elapsed,
            coverage=coverage,
            state_graph_nodes=[s.model_dump() for s in self.graph.states.values()],
            state_graph_edges=[t.model_dump() for t in self.graph.transitions],
            artifact_references=all_artifacts,
        )
