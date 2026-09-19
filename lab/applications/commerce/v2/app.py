"""RETRACE Commerce Lab - Version B (Target Release with 6 Seeded Regressions + 3 Non-Regressions)."""

import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from lab.applications.commerce.seed.reset_engine import get_fresh_datastore

app = FastAPI(
    title="RETRACE Commerce Lab - Version B",
    description="Modified e-commerce application under test with intentional seeded regressions",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

datastore = get_fresh_datastore()
STATIC_DIR = Path(__file__).parent / "static"


# ------------------------------------------------------------------------------
# Request & Response Contracts (Version B)
# ------------------------------------------------------------------------------


class AddToCartRequest(BaseModel):
    product_id: str
    quantity: int = Field(default=1, ge=1)


# DEF-001: Backend schema changed from 'code' to 'couponCode'
class ApplyCouponRequestV2(BaseModel):
    couponCode: str = Field(min_length=1, max_length=32)


class CheckoutRequest(BaseModel):
    customer_name: str | None = None
    customer_email: str | None = None
    shipping_address: str | None = None
    payment_method: str = Field(default="credit_card")
    gift_wrapping: bool = Field(default=False)  # NONREG-003: Optional gift wrapping feature


# ------------------------------------------------------------------------------
# System & Health Probes
# ------------------------------------------------------------------------------


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy", "version": "v2.0.0", "app": "commerce-lab"}


@app.get("/ready")
async def readiness_check() -> dict[str, str | bool]:
    return {"status": "ready", "healthy": True, "version": "v2.0.0"}


@app.post("/api/reset")
async def reset_lab_state() -> dict[str, Any]:
    summary = datastore.reset()
    return {"status": "reset_successful", "version": "v2.0.0", "summary": summary}


# ------------------------------------------------------------------------------
# Products & Catalog API
# ------------------------------------------------------------------------------


@app.get("/api/products")
async def list_products(query: str | None = None, category: str | None = None) -> list[dict]:
    # DEF-006: Artificial performance regression (synchronous blocking delay on search)
    if query:
        time.sleep(2.5)  # Injects 2500ms blocking latency

    products = datastore.search_products(query=query, category=category)
    # NONREG-002: Badge copy update from 'Best Seller' to 'Popular Choice'
    modified_products = []
    for p in products:
        p_copy = dict(p)
        if p_copy.get("badge") == "Best Seller":
            p_copy["badge"] = "Popular Choice"
        modified_products.append(p_copy)

    return modified_products


@app.get("/api/products/{product_id}")
async def get_product(product_id: str) -> dict:
    product = datastore.get_product(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    p_copy = dict(product)
    if p_copy.get("badge") == "Best Seller":
        p_copy["badge"] = "Popular Choice"
    return p_copy


# ------------------------------------------------------------------------------
# Cart Management API
# ------------------------------------------------------------------------------


def _calculate_cart_summary() -> dict:
    items = []
    subtotal = 0.0

    for pid, qty in datastore.cart.items():
        prod = datastore.get_product(pid)
        if prod:
            line_total = round(prod["price"] * qty, 2)
            subtotal += line_total
            items.append({
                "product_id": pid,
                "name": prod["name"],
                "price": prod["price"],
                "quantity": qty,
                "line_total": line_total,
            })

    subtotal = round(subtotal, 2)
    discount_amount = 0.0

    if datastore.applied_coupon:
        coupon = datastore.applied_coupon
        if coupon["type"] == "percentage":
            discount_amount = round(subtotal * (coupon["value"] / 100.0), 2)
        elif coupon["type"] == "fixed":
            discount_amount = min(subtotal, float(coupon["value"]))

    taxable_amount = max(0.0, subtotal - discount_amount)
    # DEF-004: Incorrect tax calculation formula ($1.00 per item count instead of 10% of subtotal)
    item_count = sum(datastore.cart.values())
    tax_amount = round(float(item_count) * 1.0, 2)
    total = round(taxable_amount + tax_amount, 2)

    return {
        "items": items,
        "items_count": item_count,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "applied_coupon": datastore.applied_coupon["code"] if datastore.applied_coupon else None,
        "tax_amount": tax_amount,
        "total": total,
    }


@app.get("/api/cart")
async def get_cart() -> dict:
    return _calculate_cart_summary()


@app.post("/api/cart")
async def add_to_cart(req: AddToCartRequest) -> dict:
    product = datastore.get_product(req.product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    datastore.cart[req.product_id] = datastore.cart.get(req.product_id, 0) + req.quantity
    return _calculate_cart_summary()


@app.delete("/api/cart")
async def clear_cart() -> dict:
    datastore.cart.clear()
    datastore.applied_coupon = None
    return _calculate_cart_summary()


# ------------------------------------------------------------------------------
# Coupon Validation API (DEF-001 Schema Mismatch)
# ------------------------------------------------------------------------------


@app.post("/api/coupons/apply")
async def apply_coupon(req: ApplyCouponRequestV2) -> dict:
    """Version B: Requires 'couponCode' instead of 'code', breaking clients sending 'code'."""
    code = req.couponCode.strip().upper()
    coupon = datastore.coupons.get(code)

    if not coupon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Coupon '{code}' is invalid.",
        )
    if not coupon.get("active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=coupon.get("description", "Coupon is inactive or expired."),
        )

    datastore.applied_coupon = coupon
    return {
        "success": True,
        "coupon": coupon,
        "cart": _calculate_cart_summary(),
        "message": f"Coupon {code} applied successfully.",
    }


# ------------------------------------------------------------------------------
# Checkout & Orders API
# ------------------------------------------------------------------------------


@app.post("/api/checkout")
async def place_order(req: CheckoutRequest) -> dict:
    if not datastore.cart:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot checkout an empty cart")

    cart_summary = _calculate_cart_summary()
    order_id = f"ORD-{uuid4().hex[:8].upper()}"

    order = {
        "order_id": order_id,
        "customer_name": req.customer_name or "Anonymous",
        "customer_email": req.customer_email or "unknown@example.com",
        "shipping_address": req.shipping_address or "Not Provided",
        "payment_method": req.payment_method,
        "gift_wrapping": req.gift_wrapping,
        "items": list(cart_summary["items"]),
        "subtotal": cart_summary["subtotal"],
        "discount_amount": cart_summary["discount_amount"],
        "applied_coupon": cart_summary["applied_coupon"],
        "tax_amount": cart_summary["tax_amount"],
        "total": cart_summary["total"],
        "created_at": 0.0,
    }
    datastore.orders.append(order)

    datastore.cart.clear()
    datastore.applied_coupon = None

    return {"success": True, "order": order}


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str) -> dict:
    order = next((o for o in datastore.orders if o["order_id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


# ------------------------------------------------------------------------------
# Static Frontend Mounts
# ------------------------------------------------------------------------------

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/cart.html")
    async def serve_cart():
        return FileResponse(STATIC_DIR / "cart.html")

    @app.get("/checkout.html")
    async def serve_checkout():
        return FileResponse(STATIC_DIR / "checkout.html")

    @app.get("/order_success.html")
    async def serve_order_success():
        return FileResponse(STATIC_DIR / "order_success.html")
