"""Deterministic Report Formatter.

Renders complete, canonical Markdown and JSON investigation reports from structured sections.
"""

from typing import Any

from apps.worker.reporting.models import EvidenceChain, ReportSection, ReportStatus


class ReportFormatter:
    """Formats structured report sections into deterministic Markdown and JSON documents."""

    @classmethod
    def format_markdown(
        cls,
        title: str,
        status: ReportStatus,
        summary: str,
        sections: list[ReportSection],
        evidence_chain: EvidenceChain | None = None,
    ) -> str:
        """Assemble all sections into a single clean, canonical Markdown document."""
        lines: list[str] = []

        # Document Header
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"> **Investigation Status**: `{status.value}`")
        lines.append("")
        lines.append("---")
        lines.append("")

        for section in sections:
            lines.append(f"## {section.title}")
            lines.append("")
            lines.append(section.content_markdown.strip())
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines).strip() + "\n"

    @classmethod
    def format_json(
        cls,
        report_id: str,
        regression_id: str,
        title: str,
        status: ReportStatus,
        summary: str,
        sections: list[ReportSection],
        evidence_chain: EvidenceChain | None,
        provenance_dict: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert report structures into a deterministic, canonical JSON-compatible dictionary."""
        return {
            "report_id": report_id,
            "regression_id": regression_id,
            "title": title,
            "status": status.value,
            "summary": summary,
            "sections": [
                {
                    "section_id": sec.section_id,
                    "section_number": sec.section_number,
                    "title": sec.title,
                    "content_markdown": sec.content_markdown,
                    "evidence_ids": sec.evidence_ids,
                    "metadata": sec.metadata,
                }
                for sec in sections
            ],
            "evidence_chain": (
                {
                    "chain_id": evidence_chain.chain_id,
                    "root_node_id": evidence_chain.root_node_id,
                    "leaf_node_id": evidence_chain.leaf_node_id,
                    "nodes": [
                        {
                            "node_id": n.node_id,
                            "node_type": n.node_type.value,
                            "title": n.title,
                            "phase_origin": n.phase_origin,
                            "status": n.status,
                            "evidence_ids": n.evidence_ids,
                            "summary": n.summary,
                            "details": n.details,
                        }
                        for n in evidence_chain.nodes
                    ],
                }
                if evidence_chain
                else None
            ),
            "provenance": provenance_dict,
        }
