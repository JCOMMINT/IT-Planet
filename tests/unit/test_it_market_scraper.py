"""Unit tests for collectors/it_market/scraper.py."""

from __future__ import annotations

import json

import pytest

from collectors.it_market.scraper import (
    _extract_top_cats,
    _parse_money,
    _parse_plp,
    _sort_url,
)

# ── _sort_url ─────────────────────────────────────────────────────────────────


class TestSortUrl:
    def test_basic_construction(self):
        url = _sort_url("https://it-market.com/en/laptops", "name-asc", 1)
        assert url == "https://it-market.com/en/laptops?order=name-asc&p=1"

    def test_trailing_slash_stripped(self):
        url = _sort_url("https://it-market.com/en/laptops/", "price-desc", 5)
        assert url == "https://it-market.com/en/laptops?order=price-desc&p=5"

    def test_all_sort_keys(self):
        sorts = ["name-asc", "name-desc", "price-asc", "price-desc", "topseller"]
        for sort in sorts:
            url = _sort_url("https://it-market.com/en/laptops", sort, 1)
            assert f"order={sort}" in url


# ── _parse_money ──────────────────────────────────────────────────────────────


class TestParseMoney:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("€ 799.00", 799.0),
            ("1.234,56", 1234.56),  # European format with dot thousands
            ("1,234.56", 1234.56),
            ("500", 500.0),
            ("", None),
            ("Price on Request", None),
        ],
    )
    def test_various_formats(self, text, expected):
        result = _parse_money(text)
        if expected is None:
            assert result is None
        else:
            assert abs(result - expected) < 0.01


# ── _extract_top_cats ─────────────────────────────────────────────────────────


class TestExtractTopCats:
    def test_extracts_nav_links(self):
        html = """
        <nav class="main-navigation">
          <a href="/en/laptops">Laptops</a>
          <a href="/en/servers">Servers</a>
          <a href="https://external.com">External</a>
        </nav>
        """
        urls = _extract_top_cats(html)
        assert any("/en/laptops" in u for u in urls)
        assert any("/en/servers" in u for u in urls)
        assert not any("external.com" in u for u in urls)

    def test_deduplicates_urls(self):
        html = """
        <nav class="main-navigation">
          <a href="/en/laptops">Laptops</a>
          <a href="/en/laptops">Laptops again</a>
        </nav>
        """
        urls = _extract_top_cats(html)
        laptop_urls = [u for u in urls if "/en/laptops" in u]
        assert len(laptop_urls) == 1

    def test_empty_nav_returns_empty(self):
        html = "<html><body></body></html>"
        assert _extract_top_cats(html) == []


# ── _parse_plp ────────────────────────────────────────────────────────────────


class TestParsePlp:
    def test_extracts_product_with_variants(self, it_market_plp_html):
        products = _parse_plp(it_market_plp_html, "https://it-market.com/en/laptops")
        assert len(products) == 1
        product = products[0]
        assert product["product_name"] == "Laptop 123"
        assert product["product_code"] == "LAP-CODE-001"
        assert product["product_id"] == "prod-id-001"

    def test_variant_count(self, it_market_plp_html):
        products = _parse_plp(it_market_plp_html, "https://it-market.com/en/laptops")
        variants = json.loads(products[0]["variants"])
        assert len(variants) == 2

    def test_variant_fields(self, it_market_plp_html):
        products = _parse_plp(it_market_plp_html, "https://it-market.com/en/laptops")
        variants = json.loads(products[0]["variants"])
        first_var = variants[0]
        assert first_var["variant_id"] == "var-A"
        assert first_var["price"] == 799.0
        assert first_var["availability"] == "In Stock"

    def test_second_variant_with_delivery(self, it_market_plp_html):
        products = _parse_plp(it_market_plp_html, "https://it-market.com/en/laptops")
        variants = json.loads(products[0]["variants"])
        second_var = variants[1]
        assert second_var["price"] == 499.0
        assert second_var["availability"] == "With Delivery"

    def test_input_url_stored(self, it_market_plp_html):
        products = _parse_plp(it_market_plp_html, "https://it-market.com/en/laptops")
        assert products[0]["input_url"] == "https://it-market.com/en/laptops"

    def test_empty_html_returns_empty(self):
        assert _parse_plp("<html><body></body></html>", "") == []

    def test_status_ok(self, it_market_plp_html):
        products = _parse_plp(it_market_plp_html, "https://it-market.com/en/laptops")
        assert all(p["status"] == "ok" for p in products)

    def test_product_url_is_absolute(self, it_market_plp_html):
        products = _parse_plp(it_market_plp_html, "https://it-market.com/en/laptops")
        assert all(p["product_url"].startswith("http") for p in products)
