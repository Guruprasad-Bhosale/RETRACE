"""Artifact Storage Abstract Interface.

Provides a unified contract for storing and retrieving screenshots, DOM snapshots,
HAR network traces, logs, generated Playwright scripts, and reports.
"""

from abc import ABC, abstractmethod


class ArtifactStorage(ABC):
    """Abstract interface for multi-modal artifact persistence."""

    @abstractmethod
    async def put(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        """Store binary artifact data and return storage URI / key."""
        pass

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """Retrieve binary artifact data by key/URI."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete artifact by key/URI. Return True if deleted."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if an artifact exists."""
        pass
