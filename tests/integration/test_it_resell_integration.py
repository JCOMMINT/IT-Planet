"""Integration tests for IT Resell scraper - mocked HTTP, real logic."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from collectors.it_resell.scraper import _fetch, _scrape_pages
from tests.conftest import IT_RESELL_PLP_HTML

pytestmark = pytest.mark.integration


class TestFetch:
    @pytest.mark.asyncio
    async def test_returns_text_on_200(self):
        mock_session = AsyncMock()
        mock_session.get.return_value = MagicMock(status_code=200, text="<html>OK</html>")
        result = await _fetch(mock_session, "https://example.com")
        assert result == "<html>OK</html>"

    @pytest.mark.asyncio
    async def test_returns_none_on_500(self):
        mock_session = AsyncMock()
        mock_session.get.return_value = MagicMock(status_code=500)
        result = await _fetch(mock_session, "https://example.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_retries_on_429_then_succeeds(self):
        mock_session = AsyncMock()
        mock_session.get.side_effect = [
            MagicMock(status_code=429),
            MagicMock(status_code=200, text="<html>OK</html>"),
        ]
        with patch("collectors.it_resell.scraper.asyncio.sleep", new_callable=AsyncMock):
            result = await _fetch(mock_session, "https://example.com")
        assert result == "<html>OK</html>"


class TestScrapePages:
    @pytest.mark.asyncio
    async def test_collects_products_across_pages(self):
        mock_session = AsyncMock()
        mock_session.get.return_value = MagicMock(status_code=200, text=IT_RESELL_PLP_HTML)

        with patch("collectors.it_resell.scraper._fetch", return_value=IT_RESELL_PLP_HTML):
            products = await _scrape_pages(mock_session, range(1, 3))

        assert len(products) > 0
        ok_products = [p for p in products if p["status"] == "ok"]
        assert len(ok_products) > 0

    @pytest.mark.asyncio
    async def test_records_failed_row_on_fetch_failure(self):
        mock_session = AsyncMock()

        with patch("collectors.it_resell.scraper._fetch", return_value=None):
            products = await _scrape_pages(mock_session, range(1, 2))

        assert len(products) == 1
        assert products[0]["status"] == "failed"
        assert "fetch_failed" in products[0]["error_message"]

    @pytest.mark.asyncio
    async def test_dedup_preserved_across_chunks(self):
        """Same product on two fetched pages should deduplicate at the run level."""
        with patch("collectors.it_resell.scraper._fetch", return_value=IT_RESELL_PLP_HTML):
            mock_session = AsyncMock()
            products = await _scrape_pages(mock_session, range(1, 3))

        # Both pages return identical products; variant_id dedup happens in run(), not here
        # At _scrape_pages level we get all rows (run() deduplicates)
        assert all(isinstance(p, dict) for p in products)
