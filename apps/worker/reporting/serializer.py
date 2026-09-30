"""Report Serializer.

Serializes EvidenceReport objects into binary payloads for artifact storage and streaming.
"""

import json

from apps.worker.reporting.models import EvidenceReport, ReportFormat


class ReportSerializer:
    """Serializes EvidenceReport instances into binary buffers."""

    @classmethod
    def serialize(cls, report: EvidenceReport, fmt: ReportFormat = ReportFormat.MARKDOWN) -> bytes:
        """Serialize report to UTF-8 encoded bytes according to requested format."""
        if fmt == ReportFormat.MARKDOWN:
            return report.markdown_content.encode("utf-8")
        elif fmt == ReportFormat.JSON:
            return json.dumps(report.json_content, indent=2, sort_keys=True).encode("utf-8")
        else:
            return report.markdown_content.encode("utf-8")
