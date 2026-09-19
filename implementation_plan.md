# Implementation Plan: Phase 2 — Demo Application Laboratory & Ground-Truth Benchmark

## Executive Summary & Objectives
Phase 2 builds the **RETRACE Demo Application Laboratory**: an isolated, controlled, two-version e-commerce application (`RETRACE Commerce Lab`) with deterministic data, 6 intentionally seeded regressions across varied categories, 3 intentional non-regression changes, canonical reproduction flows, and an automated ground-truth benchmark validator.

---

## Architecture & Isolation Boundary

```
lab/
├── applications/
│   └── commerce/
│       ├── v1/                       # Version A (Baseline: Known-good state)
│       │   ├── backend/              # FastAPI REST backend on Port 3001
│       │   └── frontend/             # Complete accessible HTML5/JS/Tailwind frontend
│       ├── v2/                       # Version B (Target release with 6 seeded defects + 3 non-regressions)
│       │   ├── backend/              # FastAPI REST backend on Port 3002
│       │   └── frontend/             # Updated frontend reflecting v2 changes
│       └── seed/
│           ├── seed_data.json        # Deterministic seed data (products, users, coupons)
│           └── reset_engine.py       # Repeatable database/state reset mechanism
├── benchmark/
│   ├── ground_truth.json             # Machine-readable ground truth specification
│   ├── validator.py                  # Automated benchmark validation engine
│   └── test_laboratory.py            # Pytest test suite for lab applications & ground truth
└── README.md                         # Complete laboratory documentation and execution guide
```

---

## Seeded Defect Taxonomy (Version A vs. Version B)

| Defect ID | Category | Affected Flow | Version A (Expected) | Version B (Defect) | Introducing Change |
|---|---|---|---|---|---|
| `DEF-001` | **API Contract / Functional** | Checkout -> Coupon Application | `POST /api/coupons/apply` with `{"code": "SAVE20"}` succeeds -> 20% discount ($20 off). | Backend expects `{"couponCode": "..."}`, frontend sends `{"code": "..."}` -> 400 Bad Request, discount rejected. | Commit `8f31c2` (coupon schema refactor) |
| `DEF-002` | **Navigation / Route** | Cart -> Proceed to Checkout | Button navigates to `/checkout.html` with cart items intact. | Button points to broken route `/checkout-v2.html` (404), blocking user from checking out. | Commit `4b82e1` (router path typo) |
| `DEF-003` | **State Persistence** | Cart -> Page Reload | Cart item quantity preserved after browser refresh (e.g. quantity = 3). | Cart quantity resets to default 1 on page refresh due to state deserialization bug. | Commit `9d14f3` (cart hydration bug) |
| `DEF-004` | **Calculation / Logic** | Cart -> Total & Tax Summary | Tax calculated as 10% of subtotal ($10.00 on $100 -> Total $110.00). | Tax incorrectly calculated per item count ($2.00 on $100 -> Total $102.00). | Commit `2e7a9c` (tax formula error) |
| `DEF-005` | **Accessibility & Form Validation** | Checkout Form Submission | Shipping inputs have `<label for>` and `aria-required="true"`, preventing empty submission. | Address fields stripped of labels and required attributes, allowing empty invalid submits. | Commit `6c381d` (accessibility degradation) |
| `DEF-006` | **Performance / Latency** | Catalog Search | Search for "laptop" responds in < 80ms. | Query endpoint executes blocking sync delay loop, responding in > 2000ms. | Commit `5a92b4` (blocking query loop) |

---

## Intentional Non-Regression Changes (Version B)

| Non-Reg ID | Type | Change in Version B | Expected RETRACE Evaluation |
|---|---|---|---|
| `NONREG-001` | **Visual / Aesthetic** | Header brand styling updated with modern gradient and emoji `RETRACE Store 🛍️`. | **Not a Regression** (visual cosmetic enhancement). |
| `NONREG-002` | **Copywriting** | Badge copy changed from `"Best Seller"` to `"Popular Choice"`. | **Not a Regression** (copy update, identical behavior). |
| `NONREG-003` | **Feature Addition** | Added optional `"Gift Wrapping (+$5.00)"` toggle checkbox in checkout. | **Not a Regression** (new non-breaking optional feature). |

---

## User Review Required

> [!IMPORTANT]
> - Laboratory applications run completely independently on separate ports (Version A on `http://localhost:3001` and Version B on `http://localhost:3002`), or can be tested headlessly via ASGI transports in test suites.
> - Zero contamination: Ground-truth files are stored in `lab/benchmark/` and are never imported or referenced by RETRACE's runtime packages (`packages/`, `apps/`).
> - Reset engine (`POST /api/reset` or `reset_engine.py`) provides 100% deterministic repeatable state.

---

## Verification Plan

### Automated Laboratory & Benchmark Tests
1. **Lab API & Frontend Unit Tests:** `pytest -v lab/benchmark/test_laboratory.py`
   - Validates Version A known-good flows (catalog, cart, coupon `SAVE20`, tax calculation, accessibility attributes, search speed).
   - Validates Version B seeded defects (coupon 400 schema error, broken checkout route, cart quantity reload bug, tax mismatch, accessibility label loss, search latency).
   - Validates Version B non-regression changes.
   - Validates deterministic reset repeatability.
2. **Benchmark Validator Script:** `python lab/benchmark/validator.py`
   - Executes full ground-truth validation against both versions and asserts 100% benchmark consistency.
3. **Phase 0 & Phase 1 Regression Protection:**
   - `python -m ruff check .`
   - `python -m pytest -v tests/` (all 25 existing tests pass)
   - `cd apps/frontend && npm test -- --watch=false`
   - `cd apps/frontend && npm run build`
