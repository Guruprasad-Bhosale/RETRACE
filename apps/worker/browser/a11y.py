"""Deterministic Accessibility Observer.

Captures accessibility tree representations using the supported snapshot API
in the installed Playwright environment, coupled with structured ARIA metadata.
"""

import hashlib
import json
from typing import Any

from playwright.async_api import Page
from pydantic import BaseModel, ConfigDict, Field


class A11yNode(BaseModel):
    """Structured representation of an accessible node."""

    model_config = ConfigDict(extra="forbid")

    role: str
    name: str | None = None
    value: str | None = None
    description: str | None = None
    disabled: bool = False
    checked: bool | None = None
    expanded: bool | None = None
    level: int | None = None
    children: list["A11yNode"] = Field(default_factory=list)


class A11ySnapshot(BaseModel):
    """Accessibility capture results."""

    model_config = ConfigDict(extra="forbid")

    aria_snapshot_yaml: str
    structured_tree: dict[str, Any]
    a11y_hash: str
    api_used: str
    node_count: int


class AccessibilityObserver:
    """Captures accessibility information reliably across Playwright versions."""

    @staticmethod
    def compute_hash(text: str) -> str:
        """Calculate SHA-256 hash of accessibility string."""
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    async def capture(self, page: Page) -> A11ySnapshot:
        """Capture accessibility tree using available Playwright API."""
        api_used = "unknown"
        aria_yaml = ""

        # 1. Check for standard modern Playwright aria_snapshot (Playwright 1.49+)
        if hasattr(page, "aria_snapshot"):
            try:
                aria_yaml = await page.aria_snapshot()
                api_used = "page.aria_snapshot"
            except Exception:
                aria_yaml = ""

        # 2. Check for page.accessibility.snapshot (Legacy Playwright)
        if not aria_yaml and hasattr(page, "accessibility"):
            try:
                legacy_snap = await page.accessibility.snapshot()  # type: ignore[attr-defined]
                if legacy_snap:
                    aria_yaml = json.dumps(legacy_snap, sort_keys=True, indent=2)
                    api_used = "page.accessibility.snapshot"
            except Exception:
                aria_yaml = ""

        # 3. Fallback: Structured DOM ARIA inspection via JavaScript evaluation
        structured_tree: dict[str, Any] = await page.evaluate(
            """() => {
                function extractA11y(el) {
                    if (!el || el.nodeType !== Node.ELEMENT_NODE) return null;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden') return null;

                    const role = el.getAttribute('role') || el.tagName.toLowerCase();
                    const name = el.getAttribute('aria-label') ||
                                 el.getAttribute('aria-labelledby') ||
                                 el.getAttribute('title') ||
                                 el.innerText?.trim() ||
                                 el.getAttribute('placeholder') || '';

                    const node = {
                        tag: el.tagName.toLowerCase(),
                        role: role,
                        name: name.slice(0, 100),
                        disabled: el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true',
                        id: el.id || undefined,
                        testid: el.getAttribute('data-testid') || undefined
                    };

                    const children = [];
                    for (const child of el.children) {
                        const childNode = extractA11y(child);
                        if (childNode) children.push(childNode);
                    }
                    if (children.length > 0) {
                        node.children = children;
                    }
                    return node;
                }
                return extractA11y(document.body) || { tag: 'body', role: 'document', name: '' };
            }"""
        )

        if not aria_yaml:
            aria_yaml = json.dumps(structured_tree, sort_keys=True, indent=2)
            api_used = "dom_aria_evaluation"

        a11y_hash = self.compute_hash(aria_yaml)

        # Count total accessible nodes in tree
        def count_nodes(tree: dict[str, Any]) -> int:
            count = 1
            for child in tree.get("children", []):
                count += count_nodes(child)
            return count

        return A11ySnapshot(
            aria_snapshot_yaml=aria_yaml,
            structured_tree=structured_tree,
            a11y_hash=a11y_hash,
            api_used=api_used,
            node_count=count_nodes(structured_tree),
        )
