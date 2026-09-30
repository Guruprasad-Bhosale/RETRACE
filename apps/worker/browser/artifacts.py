"""Multi-Modal Artifact Collector and Storage Persistence Layer."""

import hashlib
import json
from uuid import uuid4

from apps.worker.browser.config import RunContext
from packages.domain.models import ArtifactKind, ArtifactReference
from packages.storage.base import ArtifactStorage


class ArtifactCollector:
    """Manages writing multi-modal observation and trace artifacts to ArtifactStorage."""

    def __init__(self, storage: ArtifactStorage, run_context: RunContext) -> None:
        self.storage = storage
        self.run_context = run_context

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Calculate SHA-256 hash of binary data."""
        return hashlib.sha256(data).hexdigest()

    async def persist_bytes(
        self,
        data: bytes,
        filename: str,
        kind: ArtifactKind,
        mime_type: str,
        metadata: dict | None = None,
    ) -> ArtifactReference:
        """Store raw binary data and return a typed ArtifactReference."""
        storage_key = self.run_context.artifact_namespace(filename)
        sha256_hash = self.compute_sha256(data)
        size_bytes = len(data)

        storage_uri = await self.storage.put(
            key=storage_key,
            data=data,
            content_type=mime_type,
        )

        meta = metadata.copy() if metadata else {}
        meta["filename"] = filename
        meta["storage_key"] = storage_key

        return ArtifactReference(
            id=uuid4(),
            kind=kind,
            storage_uri=storage_uri,
            mime_type=mime_type,
            size_bytes=size_bytes,
            sha256_hash=sha256_hash,
            metadata=meta,
        )

    async def persist_screenshot(
        self,
        screenshot_bytes: bytes,
        step_index: int,
        is_full_page: bool = False,
    ) -> ArtifactReference:
        """Persist PNG screenshot artifact."""
        prefix = f"step_{step_index:03d}_full" if is_full_page else f"step_{step_index:03d}_viewport"
        filename = f"{prefix}_{uuid4().hex[:8]}.png"
        return await self.persist_bytes(
            data=screenshot_bytes,
            filename=filename,
            kind=ArtifactKind.SCREENSHOT,
            mime_type="image/png",
            metadata={"step_index": step_index, "full_page": is_full_page},
        )

    async def persist_dom_html(
        self,
        html_content: str,
        step_index: int,
    ) -> ArtifactReference:
        """Persist normalized DOM HTML artifact."""
        filename = f"step_{step_index:03d}_dom_{uuid4().hex[:8]}.html"
        data = html_content.encode("utf-8")
        return await self.persist_bytes(
            data=data,
            filename=filename,
            kind=ArtifactKind.DOM_SNAPSHOT,
            mime_type="text/html",
            metadata={"step_index": step_index},
        )

    async def persist_a11y_tree(
        self,
        a11y_content: str | dict,
        step_index: int,
    ) -> ArtifactReference:
        """Persist accessibility tree snapshot."""
        if isinstance(a11y_content, dict):
            data = json.dumps(a11y_content, indent=2, sort_keys=True).encode("utf-8")
            mime = "application/json"
            ext = "json"
        else:
            data = a11y_content.encode("utf-8")
            mime = "text/yaml"
            ext = "yaml"

        filename = f"step_{step_index:03d}_a11y_{uuid4().hex[:8]}.{ext}"
        return await self.persist_bytes(
            data=data,
            filename=filename,
            kind=ArtifactKind.A11Y_TREE,
            mime_type=mime,
            metadata={"step_index": step_index},
        )

    async def persist_console_log(
        self,
        console_records: list[dict],
        step_index: int,
    ) -> ArtifactReference:
        """Persist structured console log JSON."""
        filename = f"step_{step_index:03d}_console_{uuid4().hex[:8]}.json"
        data = json.dumps(console_records, indent=2, sort_keys=True, default=str).encode("utf-8")
        return await self.persist_bytes(
            data=data,
            filename=filename,
            kind=ArtifactKind.CONSOLE_LOG,
            mime_type="application/json",
            metadata={"step_index": step_index, "log_count": len(console_records)},
        )

    async def persist_network_log(
        self,
        network_records: list[dict],
        step_index: int,
    ) -> ArtifactReference:
        """Persist structured network log JSON."""
        filename = f"step_{step_index:03d}_network_{uuid4().hex[:8]}.json"
        data = json.dumps(network_records, indent=2, sort_keys=True, default=str).encode("utf-8")
        return await self.persist_bytes(
            data=data,
            filename=filename,
            kind=ArtifactKind.HAR_TRACE,
            mime_type="application/json",
            metadata={"step_index": step_index, "record_count": len(network_records)},
        )

    async def persist_trace_zip(
        self,
        trace_bytes: bytes,
    ) -> ArtifactReference:
        """Persist session Playwright trace zip."""
        filename = f"playwright_trace_{uuid4().hex[:8]}.zip"
        return await self.persist_bytes(
            data=trace_bytes,
            filename=filename,
            kind=ArtifactKind.PLAYWRIGHT_TRACE,
            mime_type="application/zip",
            metadata={"session_level": True},
        )

    async def persist_session_har(
        self,
        har_bytes: bytes,
    ) -> ArtifactReference:
        """Persist session HAR archive."""
        filename = f"session_network_{uuid4().hex[:8]}.har"
        return await self.persist_bytes(
            data=har_bytes,
            filename=filename,
            kind=ArtifactKind.HAR_TRACE,
            mime_type="application/json",
            metadata={"session_level": True},
        )
