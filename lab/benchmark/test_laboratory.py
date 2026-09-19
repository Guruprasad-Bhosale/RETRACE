"""Pytest test suite for RETRACE Demo Application Laboratory."""

import pytest
from httpx import ASGITransport, AsyncClient

from lab.applications.commerce.seed.reset_engine import get_fresh_datastore
from lab.applications.commerce.v1.app import app as app_v1
from lab.applications.commerce.v2.app import app as app_v2
from lab.benchmark.validator import BenchmarkValidator


@pytest.fixture
async def v1_client():
    transport = ASGITransport(app=app_v1)
    async with AsyncClient(transport=transport, base_url="http://v1.test") as client:
        yield client


@pytest.fixture
async def v2_client():
    transport = ASGITransport(app=app_v2)
    async with AsyncClient(transport=transport, base_url="http://v2.test") as client:
        yield client


@pytest.mark.asyncio
async def test_reset_engine_deterministic():
    store = get_fresh_datastore()
    summary = store.reset()
    assert summary["products_count"] == 8
    assert summary["coupons_count"] == 4
    assert summary["users_count"] == 2
    assert summary["orders_count"] == 0

    # Mutate state
    store.cart["P101"] = 5
    store.orders.append({"order_id": "test"})
    assert len(store.orders) == 1

    # Reset again and verify exact restoration
    summary_2 = store.reset()
    assert summary_2["orders_count"] == 0
    assert len(store.cart) == 0
    assert len(store.orders) == 0


@pytest.mark.asyncio
async def test_version_a_checkout_flow(v1_client: AsyncClient):
    await v1_client.post("/api/reset")

    # 1. Search products
    res = await v1_client.get("/api/products?query=Headphones")
    assert res.status_code == 200
    products = res.json()
    assert len(products) == 1
    assert products[0]["id"] == "P102"

    # 2. Add to Cart
    add_res = await v1_client.post("/api/cart", json={"product_id": "P102", "quantity": 1})
    assert add_res.status_code == 200
    cart = add_res.json()
    assert cart["subtotal"] == 349.99

    # 3. Apply Coupon SAVE20 (Valid in v1)
    coupon_res = await v1_client.post("/api/coupons/apply", json={"code": "SAVE20"})
    assert coupon_res.status_code == 200
    applied_cart = coupon_res.json()["cart"]
    assert applied_cart["discount_amount"] == 70.00  # 20% of 349.99

    # 4. Place Order
    checkout_payload = {
        "customer_name": "Alex Chen",
        "customer_email": "alex@example.com",
        "shipping_address": "123 Tech Way",
        "payment_method": "credit_card",
    }
    order_res = await v1_client.post("/api/checkout", json=checkout_payload)
    assert order_res.status_code == 200
    order = order_res.json()["order"]
    assert order["order_id"].startswith("ORD-")
    assert order["discount_amount"] == 70.00


@pytest.mark.asyncio
async def test_benchmark_validator_runner():
    validator = BenchmarkValidator()
    results = await validator.run_all_checks()
    assert results["all_passed"] is True
    assert len(results["defects_validated"]) == 6
    assert len(results["non_regressions_validated"]) == 3
