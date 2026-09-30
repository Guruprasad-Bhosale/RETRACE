"""Deterministic Path Planner for Causal Reproduction Trajectories."""

import hashlib
from uuid import UUID

from apps.worker.exploration.state import ExplorationGraph
from apps.worker.exploration.transition import ExplorationTransition
from apps.worker.regression.models import RegressionClassification
from apps.worker.reproduction.errors import PathPlanningError
from apps.worker.reproduction.models import ReproductionPath, ReproductionStep
from apps.worker.reproduction.path import (
    compute_reproduction_path_signature,
    validate_reproduction_path,
)
from packages.domain.models import Action


class ReproductionPathPlanner:
    """Extracts minimal, deterministic causal action sequences from historical graph evidence."""

    @classmethod
    def plan_path_from_graph(
        cls,
        classification: RegressionClassification,
        graph: ExplorationGraph,
        seed_url: str,
        trajectory_id: UUID,
    ) -> ReproductionPath:
        """Construct minimal reproduction path using ExplorationGraph topology."""
        evidence = classification.evidence
        target_state_id = evidence.state_a_id or evidence.state_b_id
        target_trans_id = evidence.transition_a_id or evidence.transition_b_id

        # 1. Resolve transition sequence leading to the triggering condition
        transitions: list[ExplorationTransition] = []

        if target_trans_id and target_trans_id in graph.transition_lookup:
            triggering_trans = graph.transition_lookup[target_trans_id]
            leadup_transitions = graph.get_path_from_seed(triggering_trans.from_state_id)
            transitions = leadup_transitions + [triggering_trans]
        elif target_state_id and target_state_id in graph.states:
            transitions = graph.get_path_from_seed(target_state_id)
        else:
            # Fallback: check if target_state_id is seed itself (0-step path)
            if target_state_id == graph.seed_state_id:
                transitions = []
            else:
                raise PathPlanningError(
                    f"Unable to locate target state '{target_state_id}' or transition "
                    f"'{target_trans_id}' in exploration graph for classification '{classification.classification_id}'"
                )

        # 2. Build ReproductionStep sequence
        steps: list[ReproductionStep] = []
        state_ids: list[str] = [graph.seed_state_id or "seed"]
        transition_ids: list[str] = []
        action_ids: list[str] = []
        observation_ids: list[UUID] = []

        for idx, trans in enumerate(transitions):
            step = ReproductionStep(
                step_index=idx + 1,
                action_type=trans.action_type,
                stable_target_identity=trans.target_identity or trans.target,
                target_role=None,
                accessible_name=None,
                target_strategy="auto",
                raw_target=trans.target,
                value=trans.value,
                coordinates=None,
                expected_from_state_id=trans.from_state_id,
                expected_to_state_id=trans.to_state_id,
                source_action_id=str(trans.action_id),
                source_transition_id=trans.transition_id,
                timeout_ms=10000.0,
            )
            steps.append(step)
            transition_ids.append(trans.transition_id)
            if trans.to_state_id and trans.to_state_id not in state_ids:
                state_ids.append(trans.to_state_id)
            if trans.observation_id:
                observation_ids.append(trans.observation_id)

        path_sig = compute_reproduction_path_signature(seed_url, steps)
        path_id = hashlib.sha256(
            f"{classification.classification_id}:{path_sig}".encode()
        ).hexdigest()[:16]

        path = ReproductionPath(
            path_id=path_id,
            trajectory_id=trajectory_id,
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            seed_url=seed_url,
            steps=steps,
            path_signature=path_sig,
            state_ids=state_ids,
            transition_ids=transition_ids,
            action_ids=action_ids,
            observation_ids=observation_ids,
        )

        validate_reproduction_path(path)
        return path

    @classmethod
    def plan_path_from_actions(
        cls,
        classification: RegressionClassification,
        actions: list[Action],
        seed_url: str,
        trajectory_id: UUID,
        target_step_index: int | None = None,
    ) -> ReproductionPath:
        """Construct reproduction path from an ordered list of trajectory Actions."""
        if not actions and target_step_index and target_step_index > 0:
            raise PathPlanningError("Cannot plan path from empty action list when steps are expected.")

        # Slice actions up to target step if provided
        action_slice = actions
        if target_step_index is not None and target_step_index <= len(actions):
            action_slice = actions[:target_step_index]

        steps: list[ReproductionStep] = []
        action_ids: list[str] = []

        for idx, act in enumerate(action_slice):
            step = ReproductionStep(
                step_index=idx + 1,
                action_type=act.action_type,
                stable_target_identity=act.selector,
                target_role=act.metadata.get("role") if act.metadata else None,
                accessible_name=act.metadata.get("name") if act.metadata else None,
                target_strategy=act.metadata.get("target_strategy", "auto") if act.metadata else "auto",
                raw_target=act.selector,
                value=act.value,
                coordinates=act.coordinates,
                source_action_id=str(act.id),
                timeout_ms=10000.0,
            )
            steps.append(step)
            action_ids.append(str(act.id))

        path_sig = compute_reproduction_path_signature(seed_url, steps)
        path_id = hashlib.sha256(
            f"{classification.classification_id}:{path_sig}".encode()
        ).hexdigest()[:16]

        path = ReproductionPath(
            path_id=path_id,
            trajectory_id=trajectory_id,
            classification_id=classification.classification_id,
            difference_id=classification.difference_id,
            seed_url=seed_url,
            steps=steps,
            path_signature=path_sig,
            action_ids=action_ids,
        )

        validate_reproduction_path(path)
        return path
