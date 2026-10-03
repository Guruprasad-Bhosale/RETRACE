"""Unit tests for S3 and local storage production features."""

import tempfile

import pytest

from packages.storage.local import LocalDiskArtifactStorage
from packages.storage.s3 import S3ArtifactStorage


def test_s3_storage_key_sanitization_and_prefix():
    """Verify S3 key sanitization and prefix scoping."""
    storage = S3ArtifactStorage(bucket_name="test-bucket", prefix="custom-prefix")
    assert storage._sanitize_key("screenshots/step1.png") == "custom-prefix/screenshots/step1.png"
    assert storage._sanitize_key("/leading/slash.png") == "custom-prefix/leading/slash.png"
    assert storage._sanitize_key("custom-prefix/already_prefixed.png") == "custom-prefix/already_prefixed.png"


@pytest.mark.asyncio
async def test_local_storage_put_get_delete():
    """Verify local storage CRUD and directory traversal prevention."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage = LocalDiskArtifactStorage(base_dir=tmp_dir)

        # 1. Put
        uri = await storage.put("trace/log.txt", b"log_content", content_type="text/plain")
        assert "file://" in uri
        assert await storage.exists("trace/log.txt") is True

        # 2. Get
        content = await storage.get("trace/log.txt")
        assert content == b"log_content"

        # 3. Delete
        assert await storage.delete("trace/log.txt") is True
        assert await storage.exists("trace/log.txt") is False

        # 4. Traversal attack blocked
        with pytest.raises(PermissionError):
            await storage.put("../attack.txt", b"malicious")
