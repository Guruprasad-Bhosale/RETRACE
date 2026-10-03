"""Artifact Storage Abstract Interface.

Provides a unified contract for storing and retrieving screenshots, DOM snapshots,
HAR network traces, logs, generated Playwright scripts, and reports with SHA-256 integrity.
"""

import hashlib
from abc import ABC, abstractmethod
from typing import Any


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

    @abstractmethod
    async def check_health(self) -> dict[str, Any]:
        """Perform storage readiness probe ensuring read/write capability."""
        pass

    async def put_with_integrity(
        self,
        key: str,
        data: bytes,
        expected_sha256: str | None = None,
        content_type: str = "application/octet-stream",
    ) -> tuple[str, str]:
        """Store artifact after verifying or calculating SHA-256 digest."""
        computed_sha256 = hashlib.sha256(data).hexdigest()
        if expected_sha256 and computed_sha256 != expected_sha256.lower():
            raise ValueError(
                f"Artifact SHA-256 integrity check failed for '{key}': "
                f"expected {expected_sha256}, computed {computed_sha256}"
            )
        uri = await self.put(key=key, data=data, content_type=content_type)
        return uri, computed_sha256
