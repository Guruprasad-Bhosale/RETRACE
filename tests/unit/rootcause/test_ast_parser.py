"""Unit tests for multi-language AST parser across Python, JavaScript, HTML, and CSS."""

from apps.worker.rootcause.ast.parser import MultiLanguageASTParser
from apps.worker.rootcause.models import ASTNodeType, LanguageType

PYTHON_SOURCE = """
from fastapi import FastAPI, HTTPException
app = FastAPI()

class OrderService:
    def process_order(self, order_id: str):
        return {"status": "ok"}

@app.post("/api/coupons/apply")
async def apply_coupon(payload: dict):
    code = payload.get("couponCode")
    if not code:
        raise HTTPException(status_code=400)
    return {"discount": 20.0}

def calculate_tax(subtotal: float) -> float:
    return subtotal * 0.10
"""

JS_SOURCE = """
function initCart() {
    const saved = localStorage.getItem("cart");
    return saved ? JSON.parse(saved) : [];
}

const proceedToCheckout = async (items) => {
    const res = await fetch("/api/checkout", {
        method: "POST",
        body: JSON.stringify(items)
    });
    return res.json();
};
"""

HTML_SOURCE = """
<!DOCTYPE html>
<html>
<body>
    <form action="/submit" method="post">
        <label for="shipping-address">Address</label>
        <input id="shipping-address" name="address" aria-required="true" required />
        <a href="/checkout.html" id="btn-checkout">Checkout</a>
    </form>
</body>
</html>
"""


def test_python_ast_parsing():
    """Verify parsing Python AST extracting classes, methods, functions, and FastAPI route decorators."""
    index = MultiLanguageASTParser.parse_file_content("app.py", PYTHON_SOURCE, LanguageType.PYTHON)
    assert index.is_valid is True
    assert len(index.nodes) >= 4

    names = {n.name: n for n in index.nodes}
    assert "OrderService" in names
    assert names["OrderService"].kind == ASTNodeType.CLASS

    assert "process_order" in names
    assert names["process_order"].kind == ASTNodeType.METHOD
    assert names["process_order"].parent_name == "OrderService"

    assert "apply_coupon" in names
    assert names["apply_coupon"].kind == ASTNodeType.ROUTE_HANDLER
    assert names["apply_coupon"].route_path == "/api/coupons/apply"
    assert names["apply_coupon"].http_methods == ["POST"]

    assert "calculate_tax" in names
    assert names["calculate_tax"].kind == ASTNodeType.FUNCTION
    assert names["calculate_tax"].parameters == ["subtotal"]


def test_javascript_ast_parsing():
    """Verify parsing JavaScript source extracting functions, arrow functions, fetch calls, and storage."""
    index = MultiLanguageASTParser.parse_file_content("cart.js", JS_SOURCE, LanguageType.JAVASCRIPT)
    assert index.is_valid is True

    names = {n.name: n for n in index.nodes}
    assert "initCart" in names
    assert names["initCart"].kind == ASTNodeType.FUNCTION

    assert "proceedToCheckout" in names
    assert names["proceedToCheckout"].kind == ASTNodeType.FUNCTION

    assert "fetch(/api/checkout)" in names
    assert names["fetch(/api/checkout)"].kind == ASTNodeType.API_CALL

    assert "storage:cart" in names
    assert names["storage:cart"].kind == ASTNodeType.STATE_MUTATION


def test_html_parsing():
    """Verify parsing HTML source extracting tags, aria attributes, links, and forms."""
    index = MultiLanguageASTParser.parse_file_content("index.html", HTML_SOURCE, LanguageType.HTML)
    assert index.is_valid is True
    assert len(index.nodes) >= 3

    # Check that route handler link was extracted
    routes = index.find_by_route("/checkout.html")
    assert len(routes) >= 1
    assert routes[0].route_path == "/checkout.html"


def test_unsupported_language_graceful_handling():
    """Verify unsupported languages return clean index without error."""
    index = MultiLanguageASTParser.parse_file_content("code.rs", "fn main() {}", LanguageType.UNSUPPORTED_LANGUAGE)
    assert index.is_valid is True
    assert index.language == LanguageType.UNSUPPORTED_LANGUAGE
    assert len(index.nodes) == 0


def test_malformed_python_syntax_error_tolerance():
    """Verify malformed Python code does not crash the parser."""
    bad_code = "def broken(\n  return 123"
    index = MultiLanguageASTParser.parse_file_content("bad.py", bad_code, LanguageType.PYTHON)
    assert index.is_valid is False
    assert index.error_message is not None
