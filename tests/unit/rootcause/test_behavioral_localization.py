"""Unit tests for category-specific behavioral localization rules."""

from apps.worker.regression.models import (
    ClassificationEvidence,
    ClassificationStatus,
    RegressionCategory,
    RegressionClassification,
)
from apps.worker.rootcause.ast.parser import MultiLanguageASTParser
from apps.worker.rootcause.git.diff import DiffParser
from apps.worker.rootcause.localization.behavioral import BehavioralLocalizer
from apps.worker.rootcause.models import AttributionRelationshipType, LanguageType

APP_V1 = """
@app.post("/api/coupons/apply")
async def apply_coupon(payload: dict):
    code = payload.get("code")
    return {"discount": 20.0}

def calculate_tax(subtotal: float) -> float:
    return subtotal * 0.10
"""

APP_V2 = """
@app.post("/api/coupons/apply")
async def apply_coupon(payload: dict):
    code = payload.get("couponCode")
    return {"discount": 20.0}

def calculate_tax(subtotal: float) -> float:
    return 2.00
"""


def test_localize_api_contract_regression():
    """Verify localization of API contract schema mismatch."""
    diff_text = """--- a/app.py
+++ b/app.py
@@ -3,2 +3,2 @@
-    code = payload.get("code")
+    code = payload.get("couponCode")
"""
    diffs = DiffParser.parse_unified_diff(diff_text)
    idx_v2 = MultiLanguageASTParser.parse_file_content("app.py", APP_V2, LanguageType.PYTHON)
    indices = {"app.py": idx_v2}

    classification = RegressionClassification(
        classification_id="class-api-01",
        difference_id="diff-api-01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.API_CONTRACT,
        rule_id="RULE-API-400",
        reason="API returned 400 Bad Request",
        evidence=ClassificationEvidence(
            difference_id="diff-api-01",
            canonical_subject="/api/coupons/apply",
            details={"endpoint": "/api/coupons/apply", "key": "code"},
        ),
    )

    localizer = BehavioralLocalizer()
    candidates = localizer.localize(classification, None, diffs, indices)

    assert len(candidates) >= 1
    top = candidates[0]
    assert top.source_location.file_path == "app.py"
    assert top.relationship_type in (
        AttributionRelationshipType.DIRECTLY_CHANGED,
        AttributionRelationshipType.AFFECTED_ROUTE,
    )


def test_localize_calculation_regression():
    """Verify localization of calculation mismatch."""
    diff_text = """--- a/app.py
+++ b/app.py
@@ -6,2 +6,2 @@
-    return subtotal * 0.10
+    return 2.00
"""
    diffs = DiffParser.parse_unified_diff(diff_text)
    idx_v2 = MultiLanguageASTParser.parse_file_content("app.py", APP_V2, LanguageType.PYTHON)
    indices = {"app.py": idx_v2}

    classification = RegressionClassification(
        classification_id="class-calc-01",
        difference_id="diff-calc-01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.CALCULATION,
        rule_id="RULE-CALC-TAX",
        reason="Tax calculation formula mismatch",
        evidence=ClassificationEvidence(
            difference_id="diff-calc-01",
            canonical_subject="tax",
            details={"subject": "tax"},
        ),
    )

    localizer = BehavioralLocalizer()
    candidates = localizer.localize(classification, None, diffs, indices)

    assert len(candidates) >= 1
    top = candidates[0]
    assert top.source_location.file_path == "app.py"
    assert top.relationship_type in (
        AttributionRelationshipType.DIRECTLY_CHANGED,
        AttributionRelationshipType.AFFECTED_SYMBOL,
    )


def test_localize_navigation_regression():
    """Verify localization of broken navigation route."""
    html_diff = """--- a/cart.html
+++ b/cart.html
@@ -10,1 +10,1 @@
-<a href="/checkout.html">Checkout</a>
+<a href="/checkout-v2.html">Checkout</a>
"""
    diffs = DiffParser.parse_unified_diff(html_diff)
    idx_v2 = MultiLanguageASTParser.parse_file_content(
        "cart.html", '<a href="/checkout-v2.html">Checkout</a>', LanguageType.HTML
    )
    indices = {"cart.html": idx_v2}

    classification = RegressionClassification(
        classification_id="class-nav-01",
        difference_id="diff-nav-01",
        status=ClassificationStatus.REGRESSION_CANDIDATE,
        category=RegressionCategory.NAVIGATION,
        rule_id="RULE-NAV-404",
        reason="Target route resulted in 404",
        evidence=ClassificationEvidence(
            difference_id="diff-nav-01",
            canonical_subject="/checkout-v2.html",
            details={"route": "/checkout-v2.html"},
        ),
    )

    localizer = BehavioralLocalizer()
    candidates = localizer.localize(classification, None, diffs, indices)

    assert len(candidates) >= 1
    top = candidates[0]
    assert top.source_location.file_path == "cart.html"
    assert top.relationship_type in (
        AttributionRelationshipType.AFFECTED_ROUTE,
        AttributionRelationshipType.DIRECTLY_CHANGED,
    )
