"""Interactive Element Inventory Observer.

Extracts actionable interactive elements with stable target identity hierarchies
and comprehensive attribute/state metadata.
"""

from typing import Any

from playwright.async_api import Page
from pydantic import BaseModel, ConfigDict, Field


class ElementBoundingBox(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x: float
    y: float
    width: float
    height: float


class ActionableElement(BaseModel):
    """Structured representation of an actionable DOM element."""

    model_config = ConfigDict(extra="forbid")

    tag: str
    element_type: str | None = None
    role: str | None = None
    accessible_name: str | None = None
    associated_label: str | None = None
    test_id: str | None = None
    dom_id: str | None = None
    name_attr: str | None = None
    href: str | None = None
    placeholder: str | None = None
    value: str | None = None
    is_visible: bool = True
    is_enabled: bool = True
    is_checked: bool | None = None
    is_required: bool = False
    bounding_box: ElementBoundingBox | None = None
    stable_identity: str
    selector_candidates: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)


class ElementInventory(BaseModel):
    """Full actionable element inventory for a page."""

    model_config = ConfigDict(extra="forbid")

    elements: list[ActionableElement] = Field(default_factory=list)
    total_count: int = 0
    by_tag: dict[str, int] = Field(default_factory=dict)


class ElementInventoryObserver:
    """Discovers actionable elements with stable identifier resolution."""

    async def capture(self, page: Page) -> ElementInventory:
        """Evaluate page and return structured list of all interactive elements."""
        raw_elements: list[dict[str, Any]] = await page.evaluate(
            """() => {
                const results = [];
                const selector = 'button, a[href], input, select, textarea, [role="button"], [role="link"], [role="checkbox"], [role="menuitem"], [role="tab"], form';
                const nodes = document.querySelectorAll(selector);

                nodes.forEach((el, index) => {
                    const rect = el.getBoundingClientRect();
                    const style = window.getComputedStyle(el);
                    const isVisible = style.display !== 'none' &&
                                      style.visibility !== 'hidden' &&
                                      style.opacity !== '0' &&
                                      rect.width > 0 &&
                                      rect.height > 0;

                    // Test ID resolution
                    const testId = el.getAttribute('data-testid') ||
                                   el.getAttribute('data-test') ||
                                   el.getAttribute('data-cy') ||
                                   null;

                    // Label resolution
                    let label = null;
                    if (el.id) {
                        const labelEl = document.querySelector(`label[for="${el.id}"]`);
                        if (labelEl) label = labelEl.innerText.trim();
                    }
                    if (!label && el.closest('label')) {
                        label = el.closest('label').innerText.trim();
                    }

                    // Accessible name
                    const accessibleName = el.getAttribute('aria-label') ||
                                           (el.getAttribute('aria-labelledby') ? document.getElementById(el.getAttribute('aria-labelledby'))?.innerText?.trim() : null) ||
                                           label ||
                                           el.getAttribute('title') ||
                                           el.getAttribute('placeholder') ||
                                           el.innerText?.trim() ||
                                           el.getAttribute('value') ||
                                           null;

                    // Attributes collection
                    const attrs = {};
                    for (let i = 0; i < el.attributes.length; i++) {
                        const a = el.attributes[i];
                        if (['class', 'style', 'id', 'name', 'type', 'href', 'placeholder', 'data-testid', 'role'].includes(a.name) || a.name.startsWith('aria-')) {
                            attrs[a.name] = a.value;
                        }
                    }

                    results.push({
                        tag: el.tagName.toLowerCase(),
                        element_type: el.getAttribute('type') || null,
                        role: el.getAttribute('role') || null,
                        accessible_name: accessibleName ? accessibleName.slice(0, 120) : null,
                        associated_label: label ? label.slice(0, 120) : null,
                        test_id: testId,
                        dom_id: el.id || null,
                        name_attr: el.getAttribute('name') || null,
                        href: el.getAttribute('href') || null,
                        placeholder: el.getAttribute('placeholder') || null,
                        value: (el.tagName.toLowerCase() === 'input' || el.tagName.toLowerCase() === 'textarea') ? el.value : null,
                        is_visible: isVisible,
                        is_enabled: !el.hasAttribute('disabled') && el.getAttribute('aria-disabled') !== 'true',
                        is_checked: el.checked !== undefined ? el.checked : (el.getAttribute('aria-checked') === 'true' ? true : null),
                        is_required: el.hasAttribute('required') || el.getAttribute('aria-required') === 'true',
                        bounding_box: {
                            x: Math.round(rect.x * 10) / 10,
                            y: Math.round(rect.y * 10) / 10,
                            width: Math.round(rect.width * 10) / 10,
                            height: Math.round(rect.height * 10) / 10
                        },
                        attributes: attrs
                    });
                });

                return results;
            }"""
        )

        elements: list[ActionableElement] = []
        by_tag: dict[str, int] = {}

        for raw in raw_elements:
            tag = raw["tag"]
            by_tag[tag] = by_tag.get(tag, 0) + 1

            candidates = []
            stable_id = ""

            # 1. Test ID strategy
            if raw.get("test_id"):
                candidates.append(f'[data-testid="{raw["test_id"]}"]')
                stable_id = f"testid:{raw['test_id']}"
            elif raw.get("dom_id"):
                candidates.append(f'#{raw["dom_id"]}')
                if not stable_id:
                    stable_id = f"id:{raw['dom_id']}"

            # 2. Accessible Role + Name strategy
            role = raw.get("role") or tag
            name = raw.get("accessible_name")
            if name:
                candidates.append(f'role={role}[name="{name}"]')
                if not stable_id:
                    stable_id = f"role:{role}[name='{name}']"

            # 3. Associated Label strategy
            label = raw.get("associated_label")
            if label:
                candidates.append(f'label="{label}"')
                if not stable_id:
                    stable_id = f"label:{label}"

            # 4. Semantic attribute strategy
            if raw.get("name_attr"):
                candidates.append(f'{tag}[name="{raw["name_attr"]}"]')
                if not stable_id:
                    stable_id = f"{tag}[name='{raw['name_attr']}']"
            elif raw.get("placeholder"):
                candidates.append(f'{tag}[placeholder="{raw["placeholder"]}"]')
                if not stable_id:
                    stable_id = f"{tag}[placeholder='{raw['placeholder']}']"

            # 5. Stable CSS fallback
            if not stable_id:
                stable_id = f"{tag}:{raw.get('bounding_box', {}).get('x', 0)},{raw.get('bounding_box', {}).get('y', 0)}"

            bbox = (
                ElementBoundingBox(**raw["bounding_box"])
                if raw.get("bounding_box")
                else None
            )

            elements.append(
                ActionableElement(
                    tag=tag,
                    element_type=raw.get("element_type"),
                    role=raw.get("role"),
                    accessible_name=name,
                    associated_label=label,
                    test_id=raw.get("test_id"),
                    dom_id=raw.get("dom_id"),
                    name_attr=raw.get("name_attr"),
                    href=raw.get("href"),
                    placeholder=raw.get("placeholder"),
                    value=raw.get("value"),
                    is_visible=raw.get("is_visible", True),
                    is_enabled=raw.get("is_enabled", True),
                    is_checked=raw.get("is_checked"),
                    is_required=raw.get("is_required", False),
                    bounding_box=bbox,
                    stable_identity=stable_id,
                    selector_candidates=candidates,
                    attributes=raw.get("attributes", {}),
                )
            )

        return ElementInventory(
            elements=elements,
            total_count=len(elements),
            by_tag=by_tag,
        )
