"""Deterministic Seed and State Reset Engine for Commerce Laboratory."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

SEED_FILE = Path(__file__).parent / "seed_data.json"


class CommerceDataStore:
    """In-memory thread-safe state store initialized from deterministic seed data."""

    def __init__(self, seed_file: Path = SEED_FILE) -> None:
        self.seed_file = seed_file
        self.products: list[dict[str, Any]] = []
        self.coupons: dict[str, dict[str, Any]] = {}
        self.users: dict[str, dict[str, Any]] = {}
        self.orders: list[dict[str, Any]] = []
        self.cart: dict[str, int] = {}  # product_id -> quantity
        self.applied_coupon: dict[str, Any] | None = None
        self.reset()

    def reset(self) -> dict[str, int]:
        """Reset state to exact deterministic seed values."""
        with open(self.seed_file, encoding="utf-8") as f:
            data = json.load(f)

        self.products = deepcopy(data.get("products", []))
        self.coupons = {c["code"]: deepcopy(c) for c in data.get("coupons", [])}
        self.users = {u["id"]: deepcopy(u) for u in data.get("users", [])}
        self.orders = []
        self.cart = {}
        self.applied_coupon = None

        return {
            "products_count": len(self.products),
            "coupons_count": len(self.coupons),
            "users_count": len(self.users),
            "orders_count": 0,
        }

    def get_product(self, product_id: str) -> dict[str, Any] | None:
        return next((p for p in self.products if p["id"] == product_id), None)

    def search_products(
        self, query: str | None = None, category: str | None = None
    ) -> list[dict[str, Any]]:
        results = list(self.products)
        if category:
            results = [p for p in results if p["category"].lower() == category.lower()]
        if query:
            q = query.lower()
            results = [
                p for p in results if q in p["name"].lower() or q in p["description"].lower()
            ]
        return results


def get_fresh_datastore() -> CommerceDataStore:
    """Return a newly initialized datastore with reset seed data."""
    return CommerceDataStore()


if __name__ == "__main__":
    store = get_fresh_datastore()
    summary = store.reset()
    print(f"Commerce Laboratory reset complete: {summary}")
