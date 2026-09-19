"""Unit tests for Artifact Storage."""

import pytest

from packages.storage.local import LocalDiskArtifactStorage


@pytest.mark.asyncio
async def test_local_disk_storage_crud(tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path)

    key = "sessions/123/screenshot.png"
    data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

    # Put
    uri = await storage.put(key, data, content_type="image/png")
    assert uri.startswith("file://")
    assert await storage.exists(key) is True

    # Get
    retrieved = await storage.get(key)
    assert retrieved == data

    # Delete
    deleted = await storage.delete(key)
    assert deleted is True
    assert await storage.exists(key) is False


@pytest.mark.asyncio
async def test_local_disk_storage_not_found(tmp_path):
    storage = LocalDiskArtifactStorage(base_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        await storage.get("non_existent.txt")
