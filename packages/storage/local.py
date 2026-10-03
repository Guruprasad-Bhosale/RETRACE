"""Local filesystem artifact storage implementation."""

import os
from pathlib import Path
from typing import Any

import aiofiles

from packages.storage.base import ArtifactStorage


class LocalDiskArtifactStorage(ArtifactStorage):
    """Stores artifacts on local disk for local development, tests, and CI."""

    def __init__(self, base_dir: str | Path = "./storage_data/artifacts") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        normalized_key = key.replace("\\", "/")
        if normalized_key.startswith("file://"):
            normalized_key = normalized_key[7:]
            # On Windows, file:///C:/path or file://C:/path -> C:/path
            if normalized_key.startswith("/") and len(normalized_key) > 2 and normalized_key[2] == ":":
                normalized_key = normalized_key[1:]

        p = Path(normalized_key)
        if p.is_absolute():
            target = p.resolve()
        else:
            if ".." in normalized_key.split("/"):
                raise PermissionError(f"Path traversal detected for artifact key: {key}")
            clean_key = normalized_key.lstrip("/")
            parts = [part for part in clean_key.split("/") if part and part != "." and part != ".."]
            target = self.base_dir.joinpath(*parts).resolve()

        # Verify resolved path is strictly within base_dir
        try:
            target.relative_to(self.base_dir)
        except ValueError as exc:
            raise PermissionError(f"Path traversal detected for artifact key: {key}") from exc

        target_str = str(target)
        if target_str.startswith("\\\\?\\"):
            return Path(target_str)
        if len(target_str) >= 240 and os.name == "nt":
            return Path(f"\\\\?\\{target_str}")
        return target

    async def put(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        target_path = self._resolve_path(key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(str(target_path), "wb") as f:
            await f.write(data)
        clean_uri = str(target_path).replace("\\\\?\\", "").replace("\\", "/")
        return f"file://{clean_uri}"

    async def get(self, key: str) -> bytes:
        target_path = self._resolve_path(key)
        if not target_path.is_file():
            raise FileNotFoundError(f"Artifact not found at key: {key}")
        async with aiofiles.open(target_path, "rb") as f:
            return await f.read()

    async def delete(self, key: str) -> bool:
        target_path = self._resolve_path(key)
        if target_path.is_file():
            target_path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        target_path = self._resolve_path(key)
        return target_path.is_file()

    async def check_health(self) -> dict[str, Any]:
        """Perform storage readiness probe ensuring directory is writable."""
        test_key = "_health_probe.tmp"
        try:
            test_path = self._resolve_path(test_key)
            test_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(str(test_path), "wb") as f:
                await f.write(b"health_check")
            if test_path.is_file():
                test_path.unlink()
            return {
                "status": "connected",
                "healthy": True,
                "backend": "local",
                "path": str(self.base_dir),
            }
        except Exception as e:
            return {
                "status": "degraded",
                "healthy": False,
                "backend": "local",
                "error": str(e),
            }
