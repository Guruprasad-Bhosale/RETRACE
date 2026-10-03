"""Artifact Storage Factory."""

from typing import Any

from packages.config.settings import Settings, get_settings
from packages.storage.base import ArtifactStorage
from packages.storage.local import LocalDiskArtifactStorage
from packages.storage.s3 import S3ArtifactStorage


def get_artifact_storage(settings: Settings | None = None) -> ArtifactStorage:
    """Instantiate and return the configured ArtifactStorage implementation."""
    cfg = settings or get_settings()

    if cfg.STORAGE_BACKEND == "s3":
        return S3ArtifactStorage(
            bucket_name=cfg.STORAGE_S3_BUCKET,
            endpoint_url=cfg.STORAGE_S3_ENDPOINT_URL,
            access_key=cfg.STORAGE_S3_ACCESS_KEY,
            secret_key=cfg.STORAGE_S3_SECRET_KEY,
            region=cfg.STORAGE_S3_REGION,
            use_ssl=cfg.STORAGE_S3_USE_SSL,
            prefix=cfg.STORAGE_S3_PREFIX,
        )

    return LocalDiskArtifactStorage(base_dir=cfg.STORAGE_LOCAL_DIR)


async def check_storage_health(settings: Settings | None = None) -> dict[str, Any]:
    """Perform storage readiness probe on configured storage backend."""
    storage = get_artifact_storage(settings)
    return await storage.check_health()
