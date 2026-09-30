"""Local filesystem artifact storage implementation."""

import os
from pathlib import Path

import aiofiles

from packages.storage.base import ArtifactStorage


class LocalDiskArtifactStorage(ArtifactStorage):
    """Stores artifacts on local disk for local development, tests, and CI."""

    def __init__(self, base_dir: str | Path = "./storage_data/artifacts") -> None:
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, key: str) -> Path:
        # Sanitize key to prevent path traversal
        clean_key = key.lstrip("/").replace("..", "_")
        target = (self.base_dir / clean_key).resolve()
        # On Windows, support paths > 260 characters via \\?\ extended-length path syntax
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
