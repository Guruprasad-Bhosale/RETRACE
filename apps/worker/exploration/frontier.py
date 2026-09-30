"""Deterministic Breadth-First Exploration Frontier Module."""

from collections import deque

from pydantic import BaseModel, ConfigDict, Field

from apps.worker.exploration.candidate import CandidateAction


class FrontierItem(BaseModel):
    """An unexplored candidate action waiting in the exploration frontier."""

    model_config = ConfigDict(extra="forbid")

    from_state_id: str
    candidate: CandidateAction
    depth: int = Field(ge=0)


class ExplorationFrontier:
    """Deterministic FIFO queue managing unexplored state transitions for BFS traversal."""

    def __init__(self) -> None:
        self._queue: deque[FrontierItem] = deque()
        self._enqueued_transition_ids: set[str] = set()

    def push(self, item: FrontierItem, transition_id: str) -> bool:
        """Enqueue a candidate transition if not already queued."""
        if transition_id in self._enqueued_transition_ids:
            return False

        self._enqueued_transition_ids.add(transition_id)
        self._queue.append(item)
        return True

    def pop(self) -> FrontierItem | None:
        """Pop the next candidate transition in strict BFS FIFO order."""
        if not self._queue:
            return None
        return self._queue.popleft()

    def is_empty(self) -> bool:
        return len(self._queue) == 0

    def size(self) -> int:
        return len(self._queue)

    def clear(self) -> None:
        self._queue.clear()
        self._enqueued_transition_ids.clear()
