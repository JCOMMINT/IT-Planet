"""Unit tests for collectors/jacob/scraper.py.

All tests are pure - no network, no GCS, no Firestore.
"""

from __future__ import annotations

import pytest

from collectors.jacob.scraper import (
    _artnr_from_url,
    _extract_jsonld,
    _is_empty,
    _normalize_condition,
    _parse_pdp,
    _parse_product_urls,
    _plp_url,
)

# ── _plp_url ──────────────────────────────────────────────────────────────────


class TestPlpUrl:
    def test_no_price_filter(self):
        url = _plp_url("https://www.jacob.de/notebooks", 1)
        assert "sortBy=preis_up" in url
        assert "page=1" in url
        assert "price-min" not in url

    def test_with_price_filter(self):
        url = _plp_url("https://www.jacob.de/notebooks", 3, pmin=100.0, pmax=500.0)
        assert "price-min=100" in url
        assert "price-max=500" in url
        assert "page=3" in url

    def test_zero_min_included(self):
        url = _plp_url("https://www.jacob.de/notebooks", 1, pmin=0.0, pmax=200.0)
        assert "price-min=0" in url


# ── _is_empty ─────────────────────────────────────────────────────────────────


class TestIsEmpty:
    def test_empty_page(self, jacob_plp_empty_html):
        assert _is_empty(jacob_plp_empty_html) is True

    def test_non_empty_page(self, jacob_plp_html):
        assert _is_empty(jacob_plp_html) is False

    def test_minimal_html_with_product(self):
        html = '<a href="/produkte/item-123">Item</a>'
        assert _is_empty(html) is False

    def test_html_without_products(self):
        html = "<html><body><p>Nothing here</p></body></html>"
        assert _is_empty(html) is True


# ── _parse_product_urls ───────────────────────────────────────────────────────


class TestParseProductUrls:
    def test_extracts_full_urls(self, jacob_plp_html):
        urls = _parse_product_urls(jacob_plp_html)
        assert any("produkte/laptop-abc-12345" in u for u in urls)
        assert any("produkte/keyboard-xyz-99999" in u for u in urls)

    def test_excludes_non_product_links(self, jacob_plp_html):
        urls = _parse_product_urls(jacob_plp_html)
        assert not any("/other/" in u for u in urls)

    def test_returns_set_like_deduplication(self):
        html = """
        <a href="/produkte/item-1">A</a>
        <a href="/produkte/item-1">A duplicate</a>
        """
        urls = _parse_product_urls(html)
        # Strip query param dedup — each unique path should appear once
        assert len(urls) == 1

    def test_relative_urls_prefixed(self):
        html = '<a href="/produkte/test-item-42">Test</a>'
        urls = _parse_product_urls(html)
        assert all(u.startswith("https://www.jacob.de") for u in urls)

    def test_absolute_urls_kept(self):
        html = '<a href="https://www.jacob.de/produkte/test-item-42">Test</a>'
        urls = _parse_product_urls(html)
        assert all(u.startswith("https://www.jacob.de") for u in urls)


# ── _artnr_from_url ───────────────────────────────────────────────────────────


class TestArtnrFromUrl:
    def test_standard_url(self):
        assert _artnr_from_url("https://www.jacob.de/produkte/laptop-abc-12345") == "12345"

    def test_url_with_query_string(self):
        assert _artnr_from_url("https://www.jacob.de/produkte/item-999?page=1") == "999"

    def test_url_without_artnr(self):
        assert _artnr_from_url("https://www.jacob.de/notebooks") == ""

    def test_multi_digit_artnr(self):
        assert _artnr_from_url("https://www.jacob.de/produkte/server-model-1234567") == "1234567"


# ── _normalize_condition ──────────────────────────────────────────────────────


class TestNormalizeCondition:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("https://schema.org/NewCondition", "New"),
            ("NewCondition", "New"),
            ("neu", "New"),
            ("brand new item", "New"),
            ("RefurbishedCondition", "Refurbished"),
            ("renewed", "Refurbished"),
            ("B-Ware", "Open Box"),
            ("bware", "Open Box"),
            ("Geöffnet", "Open Box"),
            ("Used", "Used"),
            ("gebraucht", "Used"),
            ("SomeUnknownCondition", "SomeUnknownCondition"),
            ("", ""),
        ],
    )
    def test_condition_mapping(self, raw, expected):
        assert _normalize_condition(raw) == expected


# ── _extract_jsonld ───────────────────────────────────────────────────────────


class TestExtractJsonld:
    def test_single_offer(self):
        data = {
            "name": "Laptop X",
            "sku": "SKU001",
            "mpn": "MPN001",
            "gtin13": "1234567890123",
            "description": "Nice laptop",
            "brand": {"name": "BrandA"},
            "offers": {
                "price": "999.00",
                "priceCurrency": "EUR",
                "itemCondition": "NewCondition",
                "availability": "InStock",
            },
        }
        result = _extract_jsonld(data)
        assert result["name"] == "Laptop X"
        assert result["price"] == 999.0
        assert result["price_min"] == 999.0
        assert result["price_max"] == 999.0
        assert result["currency"] == "EUR"
        assert result["condition"] == "New"
        assert result["brand"] == "BrandA"
        assert result["ean"] == "1234567890123"

    def test_multiple_offers_price_range(self):
        data = {
            "name": "Server",
            "brand": "HPE",
            "offers": [
                {"price": "500.00", "priceCurrency": "EUR", "itemCondition": "NewCondition"},
                {
                    "price": "350.00",
                    "priceCurrency": "EUR",
                    "itemCondition": "RefurbishedCondition",
                },
            ],
        }
        result = _extract_jsonld(data)
        assert result["price_min"] == 350.0
        assert result["price_max"] == 500.0
        assert result["jsonld_offer_count"] == 2

    def test_missing_optional_fields(self):
        data = {"name": "Item", "offers": {}}
        result = _extract_jsonld(data)
        assert result["name"] == "Item"
        assert result["ean"] == ""
        assert result["brand"] == ""

    def test_brand_as_string(self):
        data = {"name": "Item", "brand": "Dell", "offers": {}}
        result = _extract_jsonld(data)
        assert result["brand"] == "Dell"


# ── _parse_pdp ────────────────────────────────────────────────────────────────


class TestParsePdp:
    def test_parses_single_offer(self, jacob_pdp_html):
        result = _parse_pdp(jacob_pdp_html)
        assert result is not None
        assert result["name"] == "Laptop ABC"
        assert result["price"] == 999.0
        assert result["condition"] == "New"

    def test_parses_multi_offer(self, jacob_pdp_multi_html):
        result = _parse_pdp(jacob_pdp_multi_html)
        assert result is not None
        assert result["jsonld_offer_count"] == 2
        assert result["price_min"] == 350.0
        assert result["price_max"] == 500.0

    def test_returns_none_when_no_jsonld(self):
        html = "<html><body><p>No structured data</p></body></html>"
        assert _parse_pdp(html) is None

    def test_handles_malformed_json(self):
        html = '<script type="application/ld+json">{not valid json}</script>'
        assert _parse_pdp(html) is None

    def test_handles_graph_structure(self):
        html = """
        <script type="application/ld+json">
        {"@graph": [
          {"@type": "WebPage", "name": "Page"},
          {"@type": "Product", "name": "Item", "brand": "X",
           "offers": {"price": "10", "priceCurrency": "EUR", "itemCondition": "New"}}
        ]}
        </script>
        """
        result = _parse_pdp(html)
        assert result is not None
        assert result["name"] == "Item"


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def jacob_plp_empty_html():
    return "<html><body><p>No results found.</p></body></html>"
