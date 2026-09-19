"""RETRACE Benchmark Ground-Truth Validator.

Executes standalone programmatic verification of Version A and Version B to ensure:
1. Version A behaves as expected (known-good baseline).
2. Version B exhibits the exact 6 seeded defects (DEF-001 through DEF-006).
3. Version B non-regression changes (NONREG-001 through NONREG-003) are present.
4. Deterministic reset mechanism functions identically on both versions.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path for direct script execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from httpx import ASGITransport, AsyncClient

from lab.applications.commerce.v1.app import app as app_v1
from lab.applications.commerce.v2.app import app as app_v2

GROUND_TRUTH_FILE = Path(__file__).parent / "ground_truth.json"


class BenchmarkValidator:
    """Automated validator ensuring laboratory ground-truth consistency."""

    def __init__(self, ground_truth_path: Path = GROUND_TRUTH_FILE) -> None:
        with open(ground_truth_path, encoding="utf-8") as f:
            self.ground_truth: dict[str, Any] = json.load(f)
        self.results: dict[str, Any] = {
            "defects_validated": [],
            "non_regressions_validated": [],
            "health_checks": {},
            "reset_verified": False,
            "all_passed": False,
        }

    async def run_all_checks(self) -> dict[str, Any]:
        """Execute complete benchmark validation suite."""
        print("=" * 70)
        print("RETRACE LABORATORY GROUND-TRUTH BENCHMARK VALIDATOR")
        print("=" * 70)

        transport_v1 = ASGITransport(app=app_v1)
        transport_v2 = ASGITransport(app=app_v2)

        async with (
            AsyncClient(transport=transport_v1, base_url="http://v1.local") as client_v1,
            AsyncClient(transport=transport_v2, base_url="http://v2.local") as client_v2,
        ):
            # 1. Health & Readiness Checks
            await self._check_health(client_v1, client_v2)

            # 2. Deterministic Reset Verification
            await self._check_reset(client_v1, client_v2)

            # 3. Verify DEF-001: Coupon Schema Mismatch
            await self._verify_def_001_coupon_schema(client_v1, client_v2)

            # 4. Verify DEF-002: Broken Checkout Route
            await self._verify_def_002_broken_route(client_v1, client_v2)

            # 5. Verify DEF-003: Cart Hydration / Quantity State Bug
            await self._verify_def_003_cart_hydration()

            # 6. Verify DEF-004: Tax Calculation Formula
            await self._verify_def_004_tax_calculation(client_v1, client_v2)

            # 7. Verify DEF-005: Form Accessibility Attributes
            await self._verify_def_005_accessibility_attributes()

            # 8. Verify DEF-006: Performance Latency Regression
            await self._verify_def_006_performance_latency(client_v1, client_v2)

            # 9. Verify Non-Regressions (NONREG-001, NONREG-002, NONREG-003)
            await self._verify_non_regressions(client_v1, client_v2)

        all_defects_pass = all(d["status"] == "PASS" for d in self.results["defects_validated"])
        all_nonreg_pass = all(
            n["status"] == "PASS" for n in self.results["non_regressions_validated"]
        )
        self.results["all_passed"] = (
            all_defects_pass and all_nonreg_pass and self.results["reset_verified"]
        )

        print("\n" + "=" * 70)
        print(
            f"BENCHMARK VALIDATION RESULT: {'[PASS]' if self.results['all_passed'] else '[FAIL]'}"
        )
        print(f"Defects Verified: {len(self.results['defects_validated'])}/6")
        print(f"Non-Regressions Verified: {len(self.results['non_regressions_validated'])}/3")
        print("=" * 70)

        return self.results

    async def _check_health(self, v1: AsyncClient, v2: AsyncClient) -> None:
        res_v1 = await v1.get("/health")
        res_v2 = await v2.get("/health")
        assert res_v1.status_code == 200, "Version A health check failed"
        assert res_v2.status_code == 200, "Version B health check failed"
        self.results["health_checks"] = {"v1": "healthy", "v2": "healthy"}
        print("[OK] Health and readiness probes verified on Version A and Version B.")

    async def _check_reset(self, v1: AsyncClient, v2: AsyncClient) -> None:
        res_v1 = await v1.post("/api/reset")
        res_v2 = await v2.post("/api/reset")
        assert res_v1.status_code == 200 and res_v2.status_code == 200
        assert res_v1.json()["summary"]["products_count"] == 8
        assert res_v2.json()["summary"]["products_count"] == 8
        self.results["reset_verified"] = True
        print("[OK] Deterministic reset verified on Version A and Version B.")

    async def _verify_def_001_coupon_schema(self, v1: AsyncClient, v2: AsyncClient) -> None:
        await v1.post("/api/reset")
        await v2.post("/api/reset")

        await v1.post("/api/cart", json={"product_id": "P101", "quantity": 1})
        await v2.post("/api/cart", json={"product_id": "P101", "quantity": 1})

        # Version A sends {"code": "SAVE20"} -> Expect 200 OK & 20% discount ($259.998 off)
        res_v1 = await v1.post("/api/coupons/apply", json={"code": "SAVE20"})
        v1_ok = res_v1.status_code == 200 and res_v1.json()["cart"]["discount_amount"] > 0

        # Version B sends {"code": "SAVE20"} -> Expect 422 Unprocessable Entity because v2 requires 'couponCode'
        res_v2 = await v2.post("/api/coupons/apply", json={"code": "SAVE20"})
        v2_defect = res_v2.status_code in (400, 422)

        status = "PASS" if (v1_ok and v2_defect) else "FAIL"
        self.results["defects_validated"].append(
            {
                "defect_id": "DEF-001",
                "title": "Coupon Schema Mismatch",
                "status": status,
                "v1_status_code": res_v1.status_code,
                "v2_status_code": res_v2.status_code,
            }
        )
        print(
            f"[{status}] DEF-001 (Coupon Schema Mismatch): vA={res_v1.status_code} (OK), vB={res_v2.status_code} (Schema Error)"
        )

    async def _verify_def_002_broken_route(self, v1: AsyncClient, v2: AsyncClient) -> None:
        cart_html_v1 = (
            Path(__file__).parent.parent / "applications/commerce/v1/static/cart.html"
        ).read_text(encoding="utf-8")
        cart_html_v2 = (
            Path(__file__).parent.parent / "applications/commerce/v2/static/cart.html"
        ).read_text(encoding="utf-8")

        v1_has_valid_route = 'href="/checkout.html"' in cart_html_v1
        v2_has_broken_route = 'href="/checkout-v2.html"' in cart_html_v2

        # Check route resolution on server
        res_v1 = await v1.get("/checkout.html")
        res_v2 = await v2.get("/checkout-v2.html")

        v1_resolves = res_v1.status_code == 200
        v2_404 = res_v2.status_code == 404

        status = (
            "PASS"
            if (v1_has_valid_route and v2_has_broken_route and v1_resolves and v2_404)
            else "FAIL"
        )
        self.results["defects_validated"].append(
            {
                "defect_id": "DEF-002",
                "title": "Broken Navigation Target",
                "status": status,
                "v1_checkout_resolves": v1_resolves,
                "v2_broken_route_404": v2_404,
            }
        )
        print(
            f"[{status}] DEF-002 (Broken Navigation Route): vA=/checkout.html (200), vB=/checkout-v2.html (404)"
        )

    async def _verify_def_003_cart_hydration(self) -> None:
        js_v1 = (Path(__file__).parent.parent / "applications/commerce/v1/static/app.js").read_text(
            encoding="utf-8"
        )
        js_v2 = (Path(__file__).parent.parent / "applications/commerce/v2/static/app.js").read_text(
            encoding="utf-8"
        )

        v1_renders_dynamic_qty = "Qty: ${item.quantity}" in js_v1
        v2_hardcodes_qty_one = "Qty: 1" in js_v2

        status = "PASS" if (v1_renders_dynamic_qty and v2_hardcodes_qty_one) else "FAIL"
        self.results["defects_validated"].append(
            {
                "defect_id": "DEF-003",
                "title": "Cart Quantity Hydration Bug",
                "status": status,
            }
        )
        print(
            f"[{status}] DEF-003 (Cart Quantity Hydration Bug): vA=dynamic quantity, vB=hardcoded quantity 1"
        )

    async def _verify_def_004_tax_calculation(self, v1: AsyncClient, v2: AsyncClient) -> None:
        await v1.post("/api/reset")
        await v2.post("/api/reset")

        # Add 1 product of P103 ($149.99)
        await v1.post("/api/cart", json={"product_id": "P103", "quantity": 1})
        await v2.post("/api/cart", json={"product_id": "P103", "quantity": 1})

        cart_v1 = (await v1.get("/api/cart")).json()
        cart_v2 = (await v2.get("/api/cart")).json()

        # v1: 10% of 149.99 = 15.00
        # v2: $1.00 per item = 1.00
        v1_tax = cart_v1["tax_amount"]
        v2_tax = cart_v2["tax_amount"]

        v1_correct = abs(v1_tax - 15.00) < 0.01
        v2_defective = abs(v2_tax - 1.00) < 0.01

        status = "PASS" if (v1_correct and v2_defective) else "FAIL"
        self.results["defects_validated"].append(
            {
                "defect_id": "DEF-004",
                "title": "Tax Calculation Formula Error",
                "status": status,
                "v1_tax": v1_tax,
                "v2_tax": v2_tax,
            }
        )
        print(
            f"[{status}] DEF-004 (Tax Formula Defect): vA=${v1_tax:.2f} (10% tax), vB=${v2_tax:.2f} ($1.00 tax)"
        )

    async def _verify_def_005_accessibility_attributes(self) -> None:
        html_v1 = (
            Path(__file__).parent.parent / "applications/commerce/v1/static/checkout.html"
        ).read_text(encoding="utf-8")
        html_v2 = (
            Path(__file__).parent.parent / "applications/commerce/v2/static/checkout.html"
        ).read_text(encoding="utf-8")

        v1_has_labels = (
            'label for="shipping-address"' in html_v1 and 'aria-required="true"' in html_v1
        )
        v2_missing_labels = (
            'label for="shipping-address"' not in html_v2 and 'aria-required="true"' not in html_v2
        )

        status = "PASS" if (v1_has_labels and v2_missing_labels) else "FAIL"
        self.results["defects_validated"].append(
            {
                "defect_id": "DEF-005",
                "title": "Accessibility Label Removal",
                "status": status,
            }
        )
        print(
            f"[{status}] DEF-005 (Accessibility Degradation): vA=labels & aria-required, vB=missing aria/labels"
        )

    async def _verify_def_006_performance_latency(self, v1: AsyncClient, v2: AsyncClient) -> None:
        # Measure v1 search latency
        t0 = time.perf_counter()
        await v1.get("/api/products?query=laptop")
        latency_v1_ms = (time.perf_counter() - t0) * 1000

        # Measure v2 search latency
        t0 = time.perf_counter()
        await v2.get("/api/products?query=laptop")
        latency_v2_ms = (time.perf_counter() - t0) * 1000

        v1_fast = latency_v1_ms < 300.0
        v2_slow = latency_v2_ms >= 2000.0

        status = "PASS" if (v1_fast and v2_slow) else "FAIL"
        self.results["defects_validated"].append(
            {
                "defect_id": "DEF-006",
                "title": "Search Latency Regression",
                "status": status,
                "v1_latency_ms": round(latency_v1_ms, 2),
                "v2_latency_ms": round(latency_v2_ms, 2),
            }
        )
        print(
            f"[{status}] DEF-006 (Search Latency Regression): vA={latency_v1_ms:.1f}ms, vB={latency_v2_ms:.1f}ms"
        )

    async def _verify_non_regressions(self, v1: AsyncClient, v2: AsyncClient) -> None:
        # NONREG-001: Header redesign & emoji in index.html
        html_v1 = (
            Path(__file__).parent.parent / "applications/commerce/v1/static/index.html"
        ).read_text(encoding="utf-8")
        html_v2 = (
            Path(__file__).parent.parent / "applications/commerce/v2/static/index.html"
        ).read_text(encoding="utf-8")
        nonreg_1_ok = "RETRACE Store (v1.0.0)" in html_v1 and "RETRACE Store 🛍️ (v2.0.0)" in html_v2

        self.results["non_regressions_validated"].append(
            {
                "non_reg_id": "NONREG-001",
                "type": "Visual Styling",
                "status": "PASS" if nonreg_1_ok else "FAIL",
            }
        )
        print(
            f"[{'PASS' if nonreg_1_ok else 'FAIL'}] NONREG-001 (Visual Header Redesign): Present in Version B"
        )

        # NONREG-002: Product badge copy change
        p_v1 = (await v1.get("/api/products/P101")).json()
        p_v2 = (await v2.get("/api/products/P101")).json()
        nonreg_2_ok = p_v1.get("badge") == "Best Seller" and p_v2.get("badge") == "Popular Choice"

        self.results["non_regressions_validated"].append(
            {
                "non_reg_id": "NONREG-002",
                "type": "Copywriting",
                "status": "PASS" if nonreg_2_ok else "FAIL",
            }
        )
        print(
            f"[{'PASS' if nonreg_2_ok else 'FAIL'}] NONREG-002 (Badge Copy Update): vA='Best Seller', vB='Popular Choice'"
        )

        # NONREG-003: Optional gift wrapping checkbox feature in v2 checkout.html
        chk_v1 = (
            Path(__file__).parent.parent / "applications/commerce/v1/static/checkout.html"
        ).read_text(encoding="utf-8")
        chk_v2 = (
            Path(__file__).parent.parent / "applications/commerce/v2/static/checkout.html"
        ).read_text(encoding="utf-8")
        nonreg_3_ok = "gift_wrapping" not in chk_v1 and "gift_wrapping" in chk_v2

        self.results["non_regressions_validated"].append(
            {
                "non_reg_id": "NONREG-003",
                "type": "Optional Feature",
                "status": "PASS" if nonreg_3_ok else "FAIL",
            }
        )
        print(
            f"[{'PASS' if nonreg_3_ok else 'FAIL'}] NONREG-003 (Optional Gift Wrap Feature): Present in Version B"
        )


async def main() -> None:
    validator = BenchmarkValidator()
    results = await validator.run_all_checks()
    if not results["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
