"""Unit tests for conservative DOM normalization and hashing."""

from apps.worker.browser.dom import DOMObserver


def test_dom_normalization_sorts_attributes():
    html_a = '<button id="btn" class="primary" data-testid="submit-btn" disabled>Submit</button>'
    html_b = '<button data-testid="submit-btn" disabled class="primary" id="btn">Submit</button>'

    norm_a = DOMObserver.normalize_html(html_a)
    norm_b = DOMObserver.normalize_html(html_b)

    assert norm_a == norm_b
    assert DOMObserver.compute_hash(norm_a) == DOMObserver.compute_hash(norm_b)


def test_dom_normalization_preserves_text_and_values():
    html = """
    <div>
        <h1>Header Title</h1>
        <input type="text" name="email" value="user@example.com" required />
        <textarea>Detailed notes</textarea>
    </div>
    """
    norm = DOMObserver.normalize_html(html)
    assert "<h1>Header Title</h1>" in norm
    assert 'value="user@example.com"' in norm
    assert "<textarea>Detailed notes</textarea>" in norm


def test_dom_hash_differs_on_content_change():
    html_1 = '<div><span class="count">1</span></div>'
    html_2 = '<div><span class="count">2</span></div>'

    norm_1 = DOMObserver.normalize_html(html_1)
    norm_2 = DOMObserver.normalize_html(html_2)

    assert DOMObserver.compute_hash(norm_1) != DOMObserver.compute_hash(norm_2)
