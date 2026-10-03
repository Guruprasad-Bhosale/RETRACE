"""RETRACE Failure Injection & Fault Simulation Framework for Reliability Testing.

Provides isolated, deterministic fault injection hooks for simulating:
- Database connectivity loss, transaction aborts, and query timeouts
- Redis Stream disconnection, message delivery drops, and unacknowledged processing
- Artifact storage write failures, bit-rot/checksum mismatch, and missing keys
- Browser process crashes, navigation timeouts, and detached frames
- Worker node crashes at specific orchestration boundaries
"""

from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

from packages.storage.base import ArtifactStorage


class FaultInjectionError(Exception):
    """Base exception for deliberately injected resilience faults."""


class DatabaseUnavailableError(FaultInjectionError):
    """Simulates database connection timeout or pool exhaustion."""


class RedisUnavailableError(FaultInjectionError):
    """Simulates Redis instance drop or network partition."""


class StorageUnavailableError(FaultInjectionError):
    """Simulates S3/disk write failure or permissions error."""


class BrowserCrashError(FaultInjectionError):
    """Simulates Chromium process SIGKILL or renderer crash."""


class NavigationTimeoutError(FaultInjectionError):
    """Simulates page navigation exceeding timeout threshold."""


class WorkerCrashSimulation(FaultInjectionError):
    """Simulates worker node crash during LangGraph execution."""


class FaultInjector:
    """Helper for orchestrating controlled failure injection in resilience tests."""

    @staticmethod
    @asynccontextmanager
    async def inject_database_failure(
        fail_on: str = "execute",
        error: Exception | None = None,
    ) -> AsyncGenerator[None, None]:
        """Inject failure into SQLAlchemy session execution or commit."""
        exc = error or DatabaseUnavailableError("Simulated database failure during resilience test")

        if fail_on == "commit":
            with patch("sqlalchemy.ext.asyncio.AsyncSession.commit", side_effect=exc):
                yield
        else:
            with patch("sqlalchemy.ext.asyncio.AsyncSession.execute", side_effect=exc):
                yield

    @staticmethod
    @asynccontextmanager
    async def inject_redis_failure(
        fail_on: str = "xreadgroup",
        error: Exception | None = None,
    ) -> AsyncGenerator[None, None]:
        """Inject failure into Redis stream client."""
        exc = error or RedisUnavailableError("Simulated Redis connection failure")
        target = f"redis.asyncio.Redis.{fail_on}"
        with patch(target, side_effect=exc):
            yield

    @staticmethod
    def wrap_storage_with_corruptor(
        real_storage: ArtifactStorage,
        corrupt_on_get: bool = False,
        fail_on_put: bool = False,
    ) -> ArtifactStorage:
        """Create a proxy storage that can simulate bit-rot or write failure."""
        class FaultyStorage(ArtifactStorage):
            def __init__(self, inner: ArtifactStorage) -> None:
                self._inner = inner

            async def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
                if fail_on_put:
                    raise StorageUnavailableError(f"Simulated write failure for key '{key}'")
                return await self._inner.put(key, data, content_type)

            async def get(self, key: str) -> bytes:
                data = await self._inner.get(key)
                if corrupt_on_get:
                    # Invert bytes to simulate bit-rot / corrupted file
                    return b"CORRUPTED_" + data[10:] if len(data) > 10 else b"CORRUPTED"
                return data

            async def delete(self, key: str) -> bool:
                return await self._inner.delete(key)

            async def exists(self, key: str) -> bool:
                return await self._inner.exists(key)

            async def check_health(self) -> dict[str, Any]:
                if fail_on_put:
                    return {"status": "degraded", "healthy": False, "error": "Simulated disk failure"}
                return await self._inner.check_health()

        return FaultyStorage(real_storage)

    @staticmethod
    @asynccontextmanager
    async def inject_browser_crash(
        crash_during: str = "goto",
    ) -> AsyncGenerator[None, None]:
        """Inject Playwright browser crash or navigation timeout."""
        if crash_during == "goto":
            with patch("playwright.async_api.Page.goto", side_effect=NavigationTimeoutError("Navigation timed out after 30000ms")):
                yield
        elif crash_during == "launch":
            with patch("playwright.async_api.BrowserType.launch", side_effect=BrowserCrashError("Chromium failed to launch: exit code 1")):
                yield
        else:
            yield

    @staticmethod
    def create_crash_at_node_hook(target_node: str) -> Callable[[str, dict[str, Any]], None]:
        """Creates a workflow node hook that raises WorkerCrashSimulation when target_node executes."""
        def hook(node_name: str, state: dict[str, Any]) -> None:
            if node_name == target_node:
                raise WorkerCrashSimulation(f"Simulated worker node crash at boundary: '{target_node}'")
        return hook
