"""Unit tests for collectors/it_resell/scraper.py."""

from __future__ import annotations

import pytest

from collectors.it_resell.scraper import (
    _collection_url,
    _get_last_page,
    _parse_money,
    _parse_plp,
)

# ── _collection_url ───────────────────────────────────────────────────────────


class TestCollectionUrl:
    def test_page_1(self):
        url = _collection_url(1)
        assert "page=1" in url
        assert "sort_by=price-ascending" in url

    def test_page_100(self):
        url = _collection_url(100)
        assert "page=100" in url


# ── _parse_money ──────────────────────────────────────────────────────────────


class TestParseMoney:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("€ 450.00", 450.0),
            ("1,200.50", 1200.5),
            ("€1200", 1200.0),
            ("0.00", 0.0),
            ("", None),
            ("N/A", None),
            ("Price on request", None),
        ],
    )
    def test_parse_various_formats(self, text, expected):
        assert _parse_money(text) == expected


# ── _get_last_page ────────────────────────────────────────────────────────────


class TestGetLastPage:
    def test_extracts_last_page(self, it_resell_pagination_html):
        assert _get_last_page(it_resell_pagination_html) == 740

    def test_returns_1_when_no_pagination(self):
        assert _get_last_page("<html><body></body></html>") == 1

    def test_returns_1_for_single_page(self):
        html = '<li class="pagination_el"><a href="?page=1">1</a></li>'
        assert _get_last_page(html) == 1

    def test_handles_multiple_page_links(self):
        html = """
        <li class="pagination_el"><a href="?page=1">1</a></li>
        <li class="pagination_el"><a href="?page=5">5</a></li>
        <li class="pagination_el"><a href="?page=10">10</a></li>
        """
        assert _get_last_page(html) == 10


# ── _parse_plp ────────────────────────────────────────────────────────────────


class TestParsePlp:
    def test_extracts_two_products(self, it_resell_plp_html):
        products = _parse_plp(it_resell_plp_html)
        assert len(products) == 2

    def test_product_fields_present(self, it_resell_plp_html):
        products = _parse_plp(it_resell_plp_html)
        first = products[0]
        assert first["name"] == "ThinkPad T490"
        assert first["handle"] == "thinkpad-t490"
        assert first["variant_id"] == "var-001"
        assert first["sku"] == "ABC123"

    def test_price_range_extracted(self, it_resell_plp_html):
        products = _parse_plp(it_resell_plp_html)
        first = products[0]
        assert first["price_min"] == 450.0
        assert first["price_max"] == 520.0

    def test_product_url_is_absolute(self, it_resell_plp_html):
        products = _parse_plp(it_resell_plp_html)
        assert all(p["product_url"].startswith("http") for p in products)

    def test_price_zero_flag(self):
        html = """
        <div class="product_item">
          <a class="product-name" href="/en/products/item-a">Item A</a>
          <span class="money main_price">€ 0.00</span>
          <input name="id" value="var-zero" />
        </div>
        """
        products = _parse_plp(html)
        assert len(products) == 1
        assert products[0]["price_zero_flag"] is True

    def test_empty_html_returns_empty_list(self):
        assert _parse_plp("<html><body></body></html>") == []

    def test_status_ok_on_all_rows(self, it_resell_plp_html):
        products = _parse_plp(it_resell_plp_html)
        assert all(p["status"] == "ok" for p in products)
