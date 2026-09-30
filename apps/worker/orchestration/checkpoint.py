"""Durable Checkpointing Configuration for LangGraph Investigation Workflows."""


from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver


def get_default_checkpointer() -> BaseCheckpointSaver:
    """Return default in-memory durable checkpointer for testing and orchestration runtime."""
    return MemorySaver()
