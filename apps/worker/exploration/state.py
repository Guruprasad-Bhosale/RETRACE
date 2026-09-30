"""Exploration State and Graph Topology Module."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.exploration.candidate import CandidateAction
from apps.worker.exploration.transition import ExplorationTransition


class ExplorationState(BaseModel):
    """Represents a unique discovered application state in the exploration graph."""

    model_config = ConfigDict(extra="forbid")

    state_id: str
    observation_id: UUID
    url: str
    route: str
    depth: int = 0
    visit_count: int = 1
    parent_state_id: str | None = None
    incoming_transition_id: str | None = None
    available_candidates: list[CandidateAction] = Field(default_factory=list)
    explored_transition_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def has_unexplored_candidates(self) -> bool:
        """Check if this state has candidates that have not yet been transitioned."""
        return len(self.explored_transition_ids) < len(self.available_candidates)


class ExplorationGraph:
    """Manages discovered application state topology and directed exploration transitions."""

    def __init__(self) -> None:
        self.states: dict[str, ExplorationState] = {}
        self.transitions: list[ExplorationTransition] = []
        self.transition_lookup: dict[str, ExplorationTransition] = {}
        self.seed_state_id: str | None = None

    def add_state(self, state: ExplorationState) -> None:
        """Register a new state or increment visit count on an existing state."""
        if state.state_id in self.states:
            existing = self.states[state.state_id]
            existing.visit_count += 1
            existing.observation_id = state.observation_id
            existing.url = state.url
            # Merge any new candidates if previously empty
            if not existing.available_candidates and state.available_candidates:
                existing.available_candidates = state.available_candidates
        else:
            self.states[state.state_id] = state
            if self.seed_state_id is None:
                self.seed_state_id = state.state_id

    def get_state(self, state_id: str) -> ExplorationState | None:
        return self.states.get(state_id)

    def has_state(self, state_id: str) -> bool:
        return state_id in self.states

    def record_transition(self, transition: ExplorationTransition) -> None:
        """Record an executed transition edge and mark state explored transition."""
        self.transitions.append(transition)
        self.transition_lookup[transition.transition_id] = transition

        source = self.states.get(transition.from_state_id)
        if source and transition.transition_id not in source.explored_transition_ids:
            source.explored_transition_ids.append(transition.transition_id)

    def is_transition_explored(self, transition_id: str) -> bool:
        """Check if an exact edge transition has already been executed."""
        return transition_id in self.transition_lookup

    def get_path_from_seed(self, target_state_id: str) -> list[ExplorationTransition]:
        """Reconstruct ordered sequence of transitions from seed state to target state via parent pointers."""
        path: list[ExplorationTransition] = []
        curr_id = target_state_id

        visited_states = set()
        while curr_id and curr_id != self.seed_state_id:
            if curr_id in visited_states:
                # Cycle prevention in parent chain
                break
            visited_states.add(curr_id)

            state = self.states.get(curr_id)
            if not state or not state.incoming_transition_id:
                break

            trans = self.transition_lookup.get(state.incoming_transition_id)
            if not trans:
                break

            path.append(trans)
            curr_id = state.parent_state_id

        path.reverse()
        return path
