"""Integration tests for Jacob scraper - mocked HTTP, real logic."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from collectors.jacob.scraper import (
    MAX_PAGE,
    _fetch,
    _get_price_ranges,
    _last_page,
    _scrape_plp_range,
)
from tests.conftest import (
    JACOB_PLP_EMPTY_HTML,
    JACOB_PLP_HTML,
)

pytestmark = pytest.mark.integration


# ── _fetch ────────────────────────────────────────────────────────────────────


class TestFetch:
    @pytest.mark.asyncio
    async def test_returns_text_on_200(self):
        mock_session = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>OK</html>"
        mock_session.get.return_value = mock_response

        sem = asyncio.Semaphore(1)
        result = await _fetch(mock_session, "https://example.com", sem)
        assert result == "<html>OK</html>"

    @pytest.mark.asyncio
    async def test_returns_none_on_404(self):
        mock_session = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.get.return_value = mock_response

        sem = asyncio.Semaphore(1)
        result = await _fetch(mock_session, "https://example.com", sem)
        assert result is None

    @pytest.mark.asyncio
    async def test_retries_on_429(self):
        mock_session = AsyncMock()
        rate_limited = MagicMock(status_code=429)
        ok_response = MagicMock(status_code=200, text="<html>OK</html>")
        mock_session.get.side_effect = [rate_limited, ok_response]

        sem = asyncio.Semaphore(1)
        with patch("collectors.jacob.scraper.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch(mock_session, "https://example.com", sem)
        assert result == "<html>OK</html>"

    @pytest.mark.asyncio
    async def test_returns_none_after_max_retries(self):
        mock_session = AsyncMock()
        rate_limited = MagicMock(status_code=429)
        mock_session.get.return_value = rate_limited

        sem = asyncio.Semaphore(1)
        with patch("collectors.jacob.scraper.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch(mock_session, "https://example.com", sem)
        assert result is None

    @pytest.mark.asyncio
    async def test_retries_on_exception(self):
        mock_session = AsyncMock()
        mock_session.get.side_effect = [
            ConnectionError("timeout"),
            MagicMock(status_code=200, text="<html>OK</html>"),
        ]
        sem = asyncio.Semaphore(1)
        with patch("collectors.jacob.scraper.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch(mock_session, "https://example.com", sem)
        assert result == "<html>OK</html>"


# ── _last_page ────────────────────────────────────────────────────────────────


class TestLastPage:
    @pytest.mark.asyncio
    async def test_finds_last_nonempty_page(self):
        """Binary search stops at last page with products."""
        call_count = [0]

        async def fake_fetch(session, url, sem, attempt=0):
            call_count[0] += 1
            # Pages 1-3 have content, page 4+ are empty
            page = int(url.split("page=")[-1]) if "page=" in url else 1
            return JACOB_PLP_HTML if page <= 3 else JACOB_PLP_EMPTY_HTML

        sem = asyncio.Semaphore(5)
        with patch("collectors.jacob.scraper._fetch", side_effect=fake_fetch):
            result = await _last_page(MagicMock(), "https://jacob.de/cat", sem)
        assert result == 3

    @pytest.mark.asyncio
    async def test_caps_at_max_page(self):
        """Binary search respects MAX_PAGE ceiling."""

        async def always_has_products(session, url, sem, attempt=0):
            return JACOB_PLP_HTML

        sem = asyncio.Semaphore(5)
        with patch("collectors.jacob.scraper._fetch", side_effect=always_has_products):
            result = await _last_page(MagicMock(), "https://jacob.de/cat", sem)
        assert result == MAX_PAGE


# ── _get_price_ranges ─────────────────────────────────────────────────────────


class TestGetPriceRanges:
    @pytest.mark.asyncio
    async def test_returns_no_filter_when_under_cap(self):
        """When last_page < MAX_PAGE, no splitting needed."""

        async def fake_last_page(session, cat_url, sem, pmin=None, pmax=None):
            return 10  # Well under MAX_PAGE

        sem = asyncio.Semaphore(5)
        with patch("collectors.jacob.scraper._last_page", side_effect=fake_last_page):
            ranges = await _get_price_ranges(MagicMock(), "https://jacob.de/cat", sem)
        assert ranges == [(None, None)]

    @pytest.mark.asyncio
    async def test_splits_when_at_cap(self):
        """When first range hits MAX_PAGE, should return multiple ranges."""
        call_count = [0]

        async def fake_last_page(session, cat_url, sem, pmin=None, pmax=None):
            call_count[0] += 1
            if pmin is None:
                return MAX_PAGE  # Trigger split
            if pmax is not None and (pmax - (pmin or 0)) <= 1000:
                return 5  # Sub-range fits
            return MAX_PAGE  # Keep splitting

        # _fetch needed to get max_price from page
        async def fake_fetch(session, url, sem, attempt=0):
            return '<html><input data-price-max="10000" /></html>'

        sem = asyncio.Semaphore(5)
        with (
            patch("collectors.jacob.scraper._last_page", side_effect=fake_last_page),
            patch("collectors.jacob.scraper._fetch", side_effect=fake_fetch),
        ):
            ranges = await _get_price_ranges(MagicMock(), "https://jacob.de/cat", sem)

        assert len(ranges) > 1
        assert all(r != (None, None) for r in ranges)


# ── _scrape_plp_range ─────────────────────────────────────────────────────────


class TestScrapePlpRange:
    @pytest.mark.asyncio
    async def test_collects_urls_from_pages(self):
        async def fake_last_page(session, cat_url, sem, pmin=None, pmax=None):
            return 2

        async def fake_fetch(session, url, sem, attempt=0):
            return JACOB_PLP_HTML

        sem = asyncio.Semaphore(5)
        with (
            patch("collectors.jacob.scraper._last_page", side_effect=fake_last_page),
            patch("collectors.jacob.scraper._fetch", side_effect=fake_fetch),
        ):
            urls = await _scrape_plp_range(MagicMock(), "https://jacob.de/cat", sem, None, None)

        assert len(urls) > 0
        assert all("produkte" in u for u in urls)

    @pytest.mark.asyncio
    async def test_deduplicates_across_pages(self):
        """Same URL on two pages should appear only once."""

        async def fake_last_page(session, cat_url, sem, pmin=None, pmax=None):
            return 2

        async def fake_fetch(session, url, sem, attempt=0):
            return JACOB_PLP_HTML  # Both pages return same products

        sem = asyncio.Semaphore(5)
        with (
            patch("collectors.jacob.scraper._last_page", side_effect=fake_last_page),
            patch("collectors.jacob.scraper._fetch", side_effect=fake_fetch),
        ):
            urls = await _scrape_plp_range(MagicMock(), "https://jacob.de/cat", sem, None, None)

        assert len(urls) == len(set(urls))
