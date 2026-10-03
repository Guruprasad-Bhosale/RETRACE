"""Visual Smoke Test for RETRACE Command Center Angular UI."""

import pytest
from playwright.async_api import async_playwright


@pytest.mark.asyncio
async def test_ui_routes_and_tabs_render():
    """Verify Angular Command Center routes and investigation workstation tabs."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1440, "height": 900})
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # 1. Dashboard Route
        await page.goto("http://localhost:4200/dashboard")
        await page.wait_for_selector("h1")
        page_text = await page.inner_text("body")
        assert "RETRACE" in page_text

        # 2. Case Files List Route
        await page.goto("http://localhost:4200/investigations")
        await page.wait_for_selector("table")
        rows = await page.locator("tbody tr").count()
        assert rows >= 1

        # 3. Investigation Detail Route (Real Backend Data: inv_comm_cart_01)
        await page.goto("http://localhost:4200/investigations/inv_comm_cart_01")
        await page.wait_for_selector("h1")
        assert "COMMERCE CART" in (await page.inner_text("h1")).upper()

        # 4. Verify Causal Trajectory Banner
        await page.wait_for_selector(".bento-card")
        detail_text = await page.inner_text("body")
        assert "Causal Regression Trajectory" in detail_text or "VERSION A" in detail_text

        # 5. Verify Core Forensic Workstation Tabs & Dynamic Panel Switching
        # Default Tab: Evidence Graph
        await page.wait_for_selector("app-evidence-graph-view")

        # Tab: Hypotheses & Falsification
        await page.locator('button:has-text("Hypotheses")').click()
        await page.wait_for_selector("app-hypotheses-view", timeout=5000)

        # Tab: Root Cause & Diff
        await page.locator('button:has-text("Root Cause")').click()
        await page.wait_for_selector("app-source-diff-view", timeout=5000)

        # Tab: Reproduction & Test
        await page.locator('button:has-text("Reproduction")').click()
        await page.wait_for_selector("app-reproduction-timeline", timeout=5000)

        # Tab: Replay & Verification
        await page.locator('button:has-text("Replay")').click()
        await page.wait_for_selector("app-investigation-replay-comparison", timeout=5000)

        # Tab: Artifacts
        await page.locator('button:has-text("Artifacts")').click()
        await page.wait_for_selector("app-artifact-viewer", timeout=5000)

        # Return to Evidence Graph Tab
        await page.locator('button:has-text("Evidence Graph")').click()
        await page.wait_for_selector("app-evidence-graph-view", timeout=5000)

        await browser.close()
