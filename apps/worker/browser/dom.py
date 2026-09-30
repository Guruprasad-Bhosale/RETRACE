"""Deterministic DOM Observer and Conservative Normalizer."""

import hashlib
import re
from typing import Any

from playwright.async_api import Page
from pydantic import BaseModel, ConfigDict


class DOMSnapshot(BaseModel):
    """Structured result of a captured and normalized DOM state."""

    model_config = ConfigDict(extra="forbid")

    raw_html: str
    normalized_html: str
    dom_hash: str
    node_count: int
    element_counts: dict[str, int]


class DOMObserver:
    """Captures and deterministically normalizes DOM HTML."""

    @staticmethod
    def normalize_html(html: str) -> str:
        """Conservatively normalizes HTML without destroying meaningful state.

        Preserves:
        - All text content and node hierarchy
        - Input values, checked, disabled, and selected states
        - ARIA roles, labels, and accessibility attributes
        - Test IDs and identifiers

        Normalizes:
        - Carriage returns (\r\n -> \n)
        - Whitespace between tags (conservative)
        - Attribute ordering per tag (alphabetical)
        """
        if not html:
            return ""

        # Normalize line endings
        normalized = html.replace("\r\n", "\n").replace("\r", "\n")

        # Function to sort attributes in a tag deterministically
        def sort_attrs(match: re.Match[str]) -> str:
            tag_name = match.group(1)
            raw_attrs = match.group(2) or ""
            closing_slash = match.group(3) or ""

            if not raw_attrs.strip():
                return f"<{tag_name}{closing_slash}>"

            # Parse attribute key-value pairs conservatively
            attr_pattern = r'([a-zA-Z0-9_\-:@.]+)(?:\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s>]+)))?'
            found_attrs = re.findall(attr_pattern, raw_attrs)

            sorted_attrs_list = []
            for name, val_double, val_single, val_raw in sorted(found_attrs, key=lambda x: x[0].lower()):
                val = val_double or val_single or val_raw
                if val:
                    sorted_attrs_list.append(f'{name}="{val}"')
                else:
                    sorted_attrs_list.append(name)

            attr_str = " " + " ".join(sorted_attrs_list) if sorted_attrs_list else ""
            return f"<{tag_name}{attr_str}{closing_slash}>"

        # Sort attributes on HTML tags
        tag_pattern = r'<([a-zA-Z0-9\-]+)(\s+[^>]*?)?(\s*/?)>'
        normalized = re.sub(tag_pattern, sort_attrs, normalized)

        # Collapse redundant blank lines
        normalized = re.sub(r"\n\s*\n", "\n", normalized).strip()

        return normalized

    @staticmethod
    def compute_hash(content: str) -> str:
        """Calculate SHA-256 hash of normalized content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    async def capture(self, page: Page) -> DOMSnapshot:
        """Capture DOM snapshot directly from the active Playwright page."""
        raw_html = await page.content()
        normalized_html = self.normalize_html(raw_html)
        dom_hash = self.compute_hash(normalized_html)

        # Extract basic DOM node statistics via JS evaluation
        stats: dict[str, Any] = await page.evaluate(
            """() => {
                return {
                    node_count: document.querySelectorAll('*').length,
                    buttons: document.querySelectorAll('button, input[type="button"], input[type="submit"]').length,
                    inputs: document.querySelectorAll('input, textarea, select').length,
                    links: document.querySelectorAll('a[href]').length,
                    forms: document.querySelectorAll('forms').length
                };
            }"""
        )

        return DOMSnapshot(
            raw_html=raw_html,
            normalized_html=normalized_html,
            dom_hash=dom_hash,
            node_count=stats.get("node_count", 0),
            element_counts={
                "buttons": stats.get("buttons", 0),
                "inputs": stats.get("inputs", 0),
                "links": stats.get("links", 0),
                "forms": stats.get("forms", 0),
            },
        )
