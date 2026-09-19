# RETRACE Demo Application Laboratory

> **Controlled Versioned Application Laboratory & Ground-Truth Benchmark**

The **RETRACE Demo Application Laboratory** provides an isolated testbed with two independently runnable application versions (Version A and Version B), deterministic test data, intentionally seeded regressions across multiple categories, intentional non-regression changes, and an automated ground-truth benchmark validator.

---

## 🏗️ Laboratory Structure

```text
lab/
├── applications/
│   └── commerce/
│       ├── v1/                       # Version A (Baseline: Known-Good Application)
│       │   ├── app.py                # FastAPI REST Server (Default Port: 3001)
│       │   └── static/               # HTML5/JS/Tailwind Client
│       ├── v2/                       # Version B (Target: 6 Seeded Regressions + 3 Non-Regressions)
│       │   ├── app.py                # FastAPI REST Server (Default Port: 3002)
│       │   └── static/               # HTML5/JS/Tailwind Client
│       └── seed/                     # Deterministic Seed Data & Repeatable Reset Engine
├── benchmark/
│   ├── ground_truth.json             # Machine-readable ground truth specification
│   ├── validator.py                  # Automated benchmark validation engine
│   └── test_laboratory.py            # Laboratory Pytest test suite
└── README.md
```

---

## 🎯 Seeded Defect Taxonomy

The laboratory incorporates 6 deterministic seeded regressions:

| Defect ID | Category | Affected Flow | Description |
|---|---|---|---|
| `DEF-001` | **API Contract / Functional** | Checkout -> Coupon Application | Backend requires `couponCode` instead of `code`, returning 422/400 validation failure on valid coupons. |
| `DEF-002` | **Navigation / Route** | Cart -> Proceed to Checkout | Checkout button href points to broken route `/checkout-v2.html` (404 Not Found), blocking order placement. |
| `DEF-003` | **State Persistence** | Cart -> Quantity State Hydration | Client hydration hardcodes rendered quantity to `Qty: 1` regardless of actual cart quantity. |
| `DEF-004` | **Calculation / Accuracy** | Cart -> Tax & Total Summary | Tax is calculated as `$1.00` per item count rather than `10%` of taxable subtotal, causing inaccurate billing. |
| `DEF-005` | **Accessibility & Form Validation** | Checkout -> Shipping Address Form | Input fields stripped of `<label for>` associations and `aria-required="true"` / `required` validation attributes. |
| `DEF-006` | **Performance / Latency** | Catalog -> Product Search | Artificial synchronous blocking loop in query handler injects > 2000ms latency on search requests. |

---

## 🎨 Intentional Non-Regression Changes

Version B contains intentional modifications that are **NOT** regressions:

1. `NONREG-001` (**Visual Styling**): Brand header refreshed with purple gradient and emoji `RETRACE Store 🛍️ (v2.0.0)`.
2. `NONREG-002` (**Copywriting**): Product badge copy updated from `"Best Seller"` to `"Popular Choice"`.
3. `NONREG-003` (**Optional Feature Addition**): Added optional `"Gift Wrapping (+$5.00)"` toggle checkbox in checkout.

---

## 🚀 Running the Laboratory

### 1. Run Version A (Baseline - Port 3001)
```powershell
.\.venv\Scripts\python.exe -m uvicorn lab.applications.commerce.v1.app:app --host 0.0.0.0 --port 3001 --reload
```
*URL: [http://localhost:3001](http://localhost:3001)*

### 2. Run Version B (Target - Port 3002)
```powershell
.\.venv\Scripts\python.exe -m uvicorn lab.applications.commerce.v2.app:app --host 0.0.0.0 --port 3002 --reload
```
*URL: [http://localhost:3002](http://localhost:3002)*

### 3. Reset Laboratory State Deterministically
```powershell
# Via CLI
.\.venv\Scripts\python.exe lab/applications/commerce/seed/reset_engine.py

# Or via HTTP POST to either version
curl -X POST http://localhost:3001/api/reset
curl -X POST http://localhost:3002/api/reset
```

### 4. Execute Benchmark Ground-Truth Validator
```powershell
.\.venv\Scripts\python.exe lab/benchmark/validator.py
```

### 5. Run Laboratory Test Suite
```powershell
.\.venv\Scripts\python.exe -m pytest -v lab/benchmark/test_laboratory.py
```
