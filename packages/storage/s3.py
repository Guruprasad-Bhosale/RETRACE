"""S3 and MinIO compatible artifact storage implementation."""

import asyncio
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from packages.storage.base import ArtifactStorage


class S3ArtifactStorage(ArtifactStorage):
    """Stores artifacts in AWS S3 or MinIO S3-compatible storage."""

    def __init__(
        self,
        bucket_name: str,
        endpoint_url: str | None = None,
        access_key: str | None = None,
        secret_key: str | None = None,
        region: str = "us-east-1",
        use_ssl: bool = True,
        prefix: str = "artifacts",
    ) -> None:
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.prefix = prefix.strip("/")
        self.client_kwargs: dict[str, Any] = {
            "service_name": "s3",
            "region_name": region,
            "use_ssl": use_ssl,
            "config": Config(
                signature_version="s3v4",
                connect_timeout=5,
                read_timeout=10,
                retries={"max_attempts": 3, "mode": "standard"},
            ),
        }
        if endpoint_url:
            self.client_kwargs["endpoint_url"] = endpoint_url
        if access_key and secret_key:
            self.client_kwargs["aws_access_key_id"] = access_key
            self.client_kwargs["aws_secret_access_key"] = secret_key

    def _get_client(self) -> Any:
        return boto3.client(**self.client_kwargs)

    def _sanitize_key(self, key: str) -> str:
        clean = key.removeprefix(f"s3://{self.bucket_name}/").lstrip("/").replace("\\", "/")
        parts = [p for p in clean.split("/") if p and p != "." and p != ".."]
        normalized = "/".join(parts)
        if self.prefix and not normalized.startswith(f"{self.prefix}/") and normalized != self.prefix:
            return f"{self.prefix}/{normalized}"
        return normalized

    async def put(
        self, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        clean_key = self._sanitize_key(key)

        def _sync_put() -> None:
            client = self._get_client()
            client.put_object(
                Bucket=self.bucket_name,
                Key=clean_key,
                Body=data,
                ContentType=content_type,
            )

        await asyncio.to_thread(_sync_put)
        return f"s3://{self.bucket_name}/{clean_key}"

    async def get(self, key: str) -> bytes:
        clean_key = self._sanitize_key(key)

        def _sync_get() -> bytes:
            client = self._get_client()
            try:
                response = client.get_object(Bucket=self.bucket_name, Key=clean_key)
                return response["Body"].read()
            except ClientError as e:
                if e.response["Error"]["Code"] in ("NoSuchKey", "404"):
                    raise FileNotFoundError(f"Artifact not found at key: {key}") from e
                raise

        return await asyncio.to_thread(_sync_get)

    async def delete(self, key: str) -> bool:
        clean_key = self._sanitize_key(key)

        def _sync_delete() -> bool:
            client = self._get_client()
            try:
                client.delete_object(Bucket=self.bucket_name, Key=clean_key)
                return True
            except ClientError:
                return False

        return await asyncio.to_thread(_sync_delete)

    async def exists(self, key: str) -> bool:
        clean_key = self._sanitize_key(key)

        def _sync_head() -> bool:
            client = self._get_client()
            try:
                client.head_object(Bucket=self.bucket_name, Key=clean_key)
                return True
            except ClientError:
                return False

        return await asyncio.to_thread(_sync_head)

    async def check_health(self) -> dict[str, Any]:
        """Perform readiness probe on S3 bucket."""
        def _sync_health() -> dict[str, Any]:
            client = self._get_client()
            try:
                client.head_bucket(Bucket=self.bucket_name)
                return {
                    "status": "connected",
                    "healthy": True,
                    "backend": "s3",
                    "bucket": self.bucket_name,
                }
            except ClientError as e:
                return {
                    "status": "degraded",
                    "healthy": False,
                    "backend": "s3",
                    "bucket": self.bucket_name,
                    "error": str(e),
                }
            except Exception as e:
                return {
                    "status": "disconnected",
                    "healthy": False,
                    "backend": "s3",
                    "error": str(e),
                }

        return await asyncio.to_thread(_sync_health)
