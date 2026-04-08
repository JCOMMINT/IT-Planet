"""Integration tests for IT Market scraper – mocked HTTP, real logic."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from collectors.it_market.scraper import _get_last_page, _scrape_subcat, SORTS, MAX_PAGE_CAP
from tests.conftest import IT_MARKET_PLP_HTML, IT_MARKET_PAGINATION_HTML

pytestmark = pytest.mark.integration


class TestGetLastPage:
    @pytest.mark.asyncio
    async def test_extracts_page_from_data_attr(self):
        mock_session = AsyncMock()
        with patch("collectors.it_market.scraper._fetch", return_value=IT_MARKET_PAGINATION_HTML):
            result = await _get_last_page(mock_session, "https://it-market.com/en/laptops")
        assert result == 50

    @pytest.mark.asyncio
    async def test_returns_1_on_fetch_failure(self):
        mock_session = AsyncMock()
        with patch("collectors.it_market.scraper._fetch", return_value=None):
            result = await _get_last_page(mock_session, "https://it-market.com/en/laptops")
        assert result == 1

    @pytest.mark.asyncio
    async def test_caps_at_max_page_cap(self):
        big_page_html = f"""
        <div class="pagination">
          <a href="?p=999" data-page="999">999</a>
        </div>
        """
        mock_session = AsyncMock()
        with patch("collectors.it_market.scraper._fetch", return_value=big_page_html):
            result = await _get_last_page(mock_session, "https://it-market.com/en/laptops")
        assert result == MAX_PAGE_CAP

    @pytest.mark.asyncio
    async def test_returns_1_when_no_pagination(self):
        mock_session = AsyncMock()
        with patch("collectors.it_market.scraper._fetch", return_value="<html></html>"):
            result = await _get_last_page(mock_session, "https://it-market.com/en/laptops")
        assert result == 1


class TestScrapeSubcat:
    @pytest.mark.asyncio
    async def test_applies_all_sorts(self):
        """Verifies that all 5 sort orders are requested."""
        requested_urls = []

        async def fake_fetch(session, url, attempt=0):
            requested_urls.append(url)
            return IT_MARKET_PLP_HTML

        async def fake_last_page(session, subcat_url, sort="name-asc"):
            return 1

        mock_session = AsyncMock()
        seen: set[str] = set()

        with patch("collectors.it_market.scraper._fetch", side_effect=fake_fetch), \
             patch("collectors.it_market.scraper._get_last_page", side_effect=fake_last_page):
            await _scrape_subcat(mock_session, "https://it-market.com/en/laptops", seen)

        sort_params_seen = {url.split("order=")[1].split("&")[0] for url in requested_urls if "order=" in url}
        assert sort_params_seen == set(SORTS)

    @pytest.mark.asyncio
    async def test_deduplicates_via_seen_set(self):
        """Products found in sort 1 should not appear in results from sort 2."""
        async def fake_fetch(session, url, attempt=0):
            return IT_MARKET_PLP_HTML

        async def fake_last_page(session, subcat_url, sort="name-asc"):
            return 1

        mock_session = AsyncMock()
        seen: set[str] = set()

        with patch("collectors.it_market.scraper._fetch", side_effect=fake_fetch), \
             patch("collectors.it_market.scraper._get_last_page", side_effect=fake_last_page):
            products = await _scrape_subcat(mock_session, "https://it-market.com/en/laptops", seen)

        # Product code LAP-CODE-001 should appear exactly once across all sorts
        codes = [p["product_code"] for p in products]
        assert len(codes) == len(set(codes))

    @pytest.mark.asyncio
    async def test_shared_seen_set_prevents_cross_subcat_dupes(self):
        """Products already seen from a prior subcat call are excluded."""
        async def fake_fetch(session, url, attempt=0):
            return IT_MARKET_PLP_HTML

        async def fake_last_page(session, subcat_url, sort="name-asc"):
            return 1

        mock_session = AsyncMock()
        seen: set[str] = set()

        with patch("collectors.it_market.scraper._fetch", side_effect=fake_fetch), \
             patch("collectors.it_market.scraper._get_last_page", side_effect=fake_last_page):
            first = await _scrape_subcat(mock_session, "https://it-market.com/en/laptops", seen)
            second = await _scrape_subcat(mock_session, "https://it-market.com/en/laptops", seen)

        assert len(second) == 0  # All products already in seen from first call
