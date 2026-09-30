"""Deterministic State Backtracking and Verified Recovery Engine."""

from apps.worker.browser.actions import ExplicitActionRequest
from apps.worker.browser.session import BrowserSession
from apps.worker.exploration.errors import BacktrackingFailedError, RecoveryMismatchError
from apps.worker.exploration.state import ExplorationGraph
from apps.worker.exploration.state_identity import StateIdentityCalculator
from packages.domain.models import ActionType, Observation


class Backtracker:
    """Restores application browser state to a target exploration node with identity verification."""

    def __init__(self, graph: ExplorationGraph, seed_url: str) -> None:
        self.graph = graph
        self.seed_url = seed_url

    async def recover_to_state(
        self,
        session: BrowserSession,
        current_state_id: str,
        target_state_id: str,
    ) -> Observation:
        """Navigate or replay path to target state and verify resulting state identity."""
        if current_state_id == target_state_id:
            # Already at the target state
            return session.observations[-1]

        target_state = self.graph.get_state(target_state_id)
        if not target_state:
            raise BacktrackingFailedError(f"Target state {target_state_id} not found in graph")

        # 1. First Attempt: Direct URL Navigation (Fast Path)
        try:
            req_nav = ExplicitActionRequest(
                action_type=ActionType.NAVIGATE,
                target=target_state.url,
            )
            _, obs_nav = await session.step(req_nav)
            ident = StateIdentityCalculator.calculate(obs_nav)
            if ident.state_id == target_state_id:
                return obs_nav
        except Exception:
            pass

        # 2. Second Attempt: Path Replay from Seed (Deterministic Root-to-Node Traversal)
        path = self.graph.get_path_from_seed(target_state_id)

        # Navigate to Seed
        req_seed = ExplicitActionRequest(
            action_type=ActionType.NAVIGATE,
            target=self.seed_url,
        )
        _, current_obs = await session.step(req_seed)

        # Replay each transition along the BFS tree path
        for transition in path:
            req_step = ExplicitActionRequest(
                action_type=transition.action_type,
                target=transition.target,
                value=transition.value,
            )
            act_res, current_obs = await session.step(req_step)
            if not act_res.success:
                raise BacktrackingFailedError(
                    f"Failed during path replay transition {transition.transition_id}: {act_res.error_message}"
                )

        # 3. Verify State Identity on Replayed State
        replayed_ident = StateIdentityCalculator.calculate(current_obs)
        if replayed_ident.state_id != target_state_id:
            raise RecoveryMismatchError(
                f"State recovery mismatch: expected {target_state_id} (route={target_state.route}), "
                f"got {replayed_ident.state_id} (route={replayed_ident.normalized_route})"
            )

        return current_obs
