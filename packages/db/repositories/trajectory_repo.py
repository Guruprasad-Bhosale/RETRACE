"""Domain-Specific Trajectory, Action, and Observation Repository."""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.models import ActionModel, ObservationModel, TrajectoryModel
from packages.domain.models import (
    Action,
    ActionType,
    ApplicationStateSnapshot,
    ArtifactReference,
    Observation,
    Provenance,
    Trajectory,
)


class TrajectoryRepository:
    """Thin repository handling ordered action trajectories, observations, and actions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _trajectory_to_domain(self, model: TrajectoryModel) -> Trajectory:
        return Trajectory(
            id=model.id,
            session_id=model.session_id,
            version_id=model.version_id,
            name=model.name,
            status=model.status,
            step_count=model.step_count,
            started_at=model.started_at,
            completed_at=model.completed_at,
            metadata=model.metadata_json or {},
        )

    async def create_trajectory(
        self,
        session_id: uuid.UUID,
        version_id: uuid.UUID,
        name: str = "Main Exploration Trajectory",
        metadata: dict | None = None,
    ) -> Trajectory:
        """Create a new exploration trajectory."""
        traj_id = uuid.uuid4()
        model = TrajectoryModel(
            id=traj_id,
            session_id=session_id,
            version_id=version_id,
            name=name,
            status="active",
            step_count=0,
            metadata_json=metadata or {},
        )
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._trajectory_to_domain(model)

    async def record_action(self, action: Action) -> Action:
        """Persist a sequence-aware browser action."""
        coords = (
            {"x": action.coordinates[0], "y": action.coordinates[1]} if action.coordinates else None
        )
        model = ActionModel(
            id=action.id,
            session_id=action.session_id,
            version_id=action.version_id,
            trajectory_id=action.trajectory_id,
            step_index=action.step_index,
            action_type=action.action_type.value,
            selector=action.selector,
            value=action.value,
            coordinates=coords,
            duration_ms=action.duration_ms,
            prior_observation_id=action.prior_observation_id,
            resulting_observation_id=action.resulting_observation_id,
            metadata_json=action.metadata,
            timestamp=action.timestamp,
        )
        self.session.add(model)
        # Increment step count on trajectory
        await self.session.execute(
            update(TrajectoryModel)
            .where(TrajectoryModel.id == action.trajectory_id)
            .values(step_count=TrajectoryModel.step_count + 1)
        )
        await self.session.flush()
        return action

    async def record_observation(self, observation: Observation) -> Observation:
        """Persist a sequence-aware rich state observation."""
        artifacts_json = [a.model_dump(mode="json") for a in observation.artifacts]
        provenance_json = observation.provenance.model_dump(mode="json")
        state_json = observation.state.model_dump(mode="json")

        model = ObservationModel(
            id=observation.id,
            session_id=observation.session_id,
            version_id=observation.version_id,
            trajectory_id=observation.trajectory_id,
            step_index=observation.step_index,
            url=observation.state.url,
            page_title=observation.state.page_title,
            http_status=observation.state.http_status,
            dom_hash=observation.state.dom_hash,
            a11y_hash=observation.state.a11y_tree_hash,
            state_snapshot=state_json,
            artifacts=artifacts_json,
            provenance=provenance_json,
            prior_observation_id=observation.prior_observation_id,
            caused_by_action_id=observation.caused_by_action_id,
            timestamp=observation.timestamp,
        )
        self.session.add(model)
        await self.session.flush()
        return observation

    async def get_trajectory_timeline(
        self, trajectory_id: uuid.UUID
    ) -> tuple[Trajectory | None, list[Observation], list[Action]]:
        """Retrieve full ordered timeline (Observations & Actions) for a trajectory."""
        # Get Trajectory
        traj_stmt = select(TrajectoryModel).where(TrajectoryModel.id == trajectory_id)
        traj_res = await self.session.execute(traj_stmt)
        traj_model = traj_res.scalar_one_or_none()
        if not traj_model:
            return None, [], []

        trajectory = self._trajectory_to_domain(traj_model)

        # Get Observations ordered by step_index
        obs_stmt = (
            select(ObservationModel)
            .where(ObservationModel.trajectory_id == trajectory_id)
            .order_by(ObservationModel.step_index.asc())
        )
        obs_res = await self.session.execute(obs_stmt)
        obs_models = obs_res.scalars().all()

        observations = []
        for m in obs_models:
            state = ApplicationStateSnapshot.model_validate(m.state_snapshot)
            artifacts = [ArtifactReference.model_validate(a) for a in m.artifacts]
            prov = Provenance.model_validate(m.provenance)
            observations.append(
                Observation(
                    id=m.id,
                    session_id=m.session_id,
                    version_id=m.version_id,
                    trajectory_id=m.trajectory_id,
                    step_index=m.step_index,
                    state=state,
                    artifacts=artifacts,
                    provenance=prov,
                    prior_observation_id=m.prior_observation_id,
                    caused_by_action_id=m.caused_by_action_id,
                    timestamp=m.timestamp,
                )
            )

        # Get Actions ordered by step_index
        act_stmt = (
            select(ActionModel)
            .where(ActionModel.trajectory_id == trajectory_id)
            .order_by(ActionModel.step_index.asc())
        )
        act_res = await self.session.execute(act_stmt)
        act_models = act_res.scalars().all()

        actions = []
        for a in act_models:
            coords = (a.coordinates["x"], a.coordinates["y"]) if a.coordinates else None
            actions.append(
                Action(
                    id=a.id,
                    session_id=a.session_id,
                    version_id=a.version_id,
                    trajectory_id=a.trajectory_id,
                    step_index=a.step_index,
                    action_type=ActionType(a.action_type),
                    selector=a.selector,
                    value=a.value,
                    coordinates=coords,
                    duration_ms=a.duration_ms,
                    prior_observation_id=a.prior_observation_id,
                    resulting_observation_id=a.resulting_observation_id,
                    metadata=a.metadata_json,
                    timestamp=a.timestamp,
                )
            )

        return trajectory, observations, actions
