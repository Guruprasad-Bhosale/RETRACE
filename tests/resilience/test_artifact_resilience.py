"""Resilience tests for Artifact Storage integrity, error recovery, and path security."""

import hashlib
from pathlib import Path

import pytest

from packages.storage.local import LocalDiskArtifactStorage
from tests.resilience.failure_injection import FaultInjector, StorageUnavailableError


@pytest.mark.asyncio
async def test_artifact_sha256_checksum_verification(tmp_path: Path):
    """Verify put_with_integrity validates SHA-256 digest correctly and rejects mismatches."""
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    data = b"Autonomous investigation trace payload v1"
    correct_hash = hashlib.sha256(data).hexdigest()
    bad_hash = hashlib.sha256(b"tampered content").hexdigest()

    # 1. Valid hash succeeds
    uri, digest = await storage.put_with_integrity(
        key="traces/valid_trace.json",
        data=data,
        expected_sha256=correct_hash,
    )
    assert uri.startswith("file://")
    assert digest == correct_hash
    assert await storage.exists("traces/valid_trace.json")

    # 2. Corrupted / mismatched hash raises ValueError and aborts storage
    with pytest.raises(ValueError, match="integrity check failed"):
        await storage.put_with_integrity(
            key="traces/corrupted_trace.json",
            data=data,
            expected_sha256=bad_hash,
        )


@pytest.mark.asyncio
async def test_artifact_path_traversal_rejection(tmp_path: Path):
    """Verify LocalDiskArtifactStorage strictly rejects path traversal attempts with '..'."""
    storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    malicious_keys = [
        "../secret.txt",
        "../../etc/passwd",
        "nested/../../outside.log",
        "..\\..\\windows\\system32",
    ]

    for key in malicious_keys:
        with pytest.raises(PermissionError, match="Path traversal detected"):
            await storage.put(key, b"malicious data")

        with pytest.raises(PermissionError, match="Path traversal detected"):
            await storage.get(key)


@pytest.mark.asyncio
async def test_artifact_storage_fault_injection_simulates_write_failure(tmp_path: Path):
    """Verify system handles simulated storage full / unwritable disk cleanly."""
    real_storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    faulty_storage = FaultInjector.wrap_storage_with_corruptor(real_storage, fail_on_put=True)

    with pytest.raises(StorageUnavailableError, match="Simulated write failure"):
        await faulty_storage.put("reports/test_report.md", b"# Report")

    health = await faulty_storage.check_health()
    assert health["healthy"] is False
    assert health["status"] == "degraded"


@pytest.mark.asyncio
async def test_artifact_storage_bit_rot_detection(tmp_path: Path):
    """Verify corrupted artifact bytes are detected when reading from storage."""
    real_storage = LocalDiskArtifactStorage(base_dir=tmp_path / "artifacts")
    payload = b"Original uncorrupted test trace"
    key = "traces/trace_001.bin"
    await real_storage.put(key, payload)

    # Wrap with corruptor that flips bytes on get()
    corrupt_storage = FaultInjector.wrap_storage_with_corruptor(real_storage, corrupt_on_get=True)
    corrupted_data = await corrupt_storage.get(key)

    original_hash = hashlib.sha256(payload).hexdigest()
    corrupted_hash = hashlib.sha256(corrupted_data).hexdigest()

    assert original_hash != corrupted_hash
    assert corrupted_data.startswith(b"CORRUPTED_")
