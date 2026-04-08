"""Unit tests for Tonitrus worker and discovery parsing logic."""
from __future__ import annotations

import pytest

from collectors.tonitrus.worker import (
    _page_url,
    _parse_price,
    _parse_plp_cards,
    _parse_total,
)
from collectors.tonitrus.discovery import _extract_child_cat_urls


# ── _page_url ─────────────────────────────────────────────────────────────────

class TestPageUrl:
    def test_page_1(self):
        url = _page_url("https://www.tonitrus.com/servers?lang=eng", 1)
        assert "_s1?" in url
        assert "lang=eng" in url
        assert "af=50" in url

    def test_page_3(self):
        url = _page_url("https://www.tonitrus.com/servers?lang=eng", 3)
        assert "_s3?" in url

    def test_strips_existing_query(self):
        url = _page_url("https://www.tonitrus.com/servers?lang=eng&af=50", 2)
        # Should not double-add lang/af
        assert url.count("af=") == 1

    def test_base_url_without_query(self):
        url = _page_url("https://www.tonitrus.com/servers", 1)
        assert "_s1?" in url
        assert "lang=eng" in url


# ── _parse_total ──────────────────────────────────────────────────────────────

class TestParseTotal:
    def test_parses_standard_format(self, tonitrus_plp_html):
        assert _parse_total(tonitrus_plp_html) == 127

    def test_parses_with_comma_thousands(self):
        html = "<div class='productlist-item-info'>Showing 1-50 of 1,234 products</div>"
        assert _parse_total(html) == 1234

    def test_returns_zero_when_missing(self):
        assert _parse_total("<html><body></body></html>") == 0

    def test_returns_zero_on_malformed(self):
        html = "<div class='productlist-item-info'>No products</div>"
        assert _parse_total(html) == 0


# ── _parse_price ──────────────────────────────────────────────────────────────

class TestParsePrice:
    @pytest.mark.parametrize("text,expected", [
        ("€ 4,500.00", 4500.0),
        ("3200", 3200.0),
        ("1.234,56", 1234.56),
        ("", None),
        ("N/A", None),
        ("0.00", 0.0),
    ])
    def test_various_formats(self, text, expected):
        result = _parse_price(text)
        if expected is None:
            assert result is None
        else:
            assert abs(result - expected) < 0.01


# ── _parse_plp_cards ──────────────────────────────────────────────────────────

class TestParsePlpCards:
    def test_extracts_products(self, tonitrus_plp_html):
        cards = _parse_plp_cards(tonitrus_plp_html, "https://www.tonitrus.com/servers")
        assert len(cards) == 2

    def test_product_fields(self, tonitrus_plp_html):
        cards = _parse_plp_cards(tonitrus_plp_html, "https://www.tonitrus.com/servers")
        first = cards[0]
        assert first["product_name"] == "Dell PowerEdge R750"
        assert first["brand"] == "Dell"
        assert first["price"] == 4500.0

    def test_product_url_absolute(self, tonitrus_plp_html):
        cards = _parse_plp_cards(tonitrus_plp_html, "https://www.tonitrus.com/servers")
        assert all(c["product_url"].startswith("http") for c in cards)

    def test_product_code_derived_from_url(self, tonitrus_plp_html):
        cards = _parse_plp_cards(tonitrus_plp_html, "https://www.tonitrus.com/servers")
        assert cards[0]["product_code"] != ""

    def test_input_url_stored(self, tonitrus_plp_html):
        cat = "https://www.tonitrus.com/servers"
        cards = _parse_plp_cards(tonitrus_plp_html, cat)
        assert all(c["input_url"] == cat for c in cards)

    def test_empty_html_returns_empty(self):
        assert _parse_plp_cards("<html><body></body></html>", "") == []

    def test_cto_false_by_default(self, tonitrus_plp_html):
        cards = _parse_plp_cards(tonitrus_plp_html, "https://www.tonitrus.com/servers")
        assert all(c["is_cto"] is False for c in cards)


# ── _extract_child_cat_urls ───────────────────────────────────────────────────

class TestExtractChildCatUrls:
    def test_finds_nav_links(self):
        html = """
        <ul class="cms-navigation-link">
          <a href="/servers/dell">Dell Servers</a>
          <a href="/servers/hpe">HPE Servers</a>
        </ul>
        """
        urls = _extract_child_cat_urls(html, "https://www.tonitrus.com/servers")
        assert len(urls) == 2

    def test_excludes_product_links(self):
        html = """
        <ul class="cms-navigation-link">
          <a href="/product/dell-r750">Dell R750</a>
          <a href="/servers/dell">Dell Servers</a>
        </ul>
        """
        urls = _extract_child_cat_urls(html, "https://www.tonitrus.com/servers")
        assert not any("/product/" in u for u in urls)

    def test_deduplicates(self):
        html = """
        <ul class="cms-navigation-link">
          <a href="/servers/dell">Dell</a>
          <a href="/servers/dell">Dell duplicate</a>
        </ul>
        """
        urls = _extract_child_cat_urls(html, "https://www.tonitrus.com/servers")
        dell_urls = [u for u in urls if "/servers/dell" in u]
        assert len(dell_urls) == 1

    def test_appends_lang_param(self):
        html = '<ul class="cms-navigation-link"><a href="/servers/dell">Dell</a></ul>'
        urls = _extract_child_cat_urls(html, "https://www.tonitrus.com/servers")
        assert all("lang=eng" in u for u in urls)
