"""IT-Resell.com scraper – curl_cffi, handle-based dedup.

This module implements an async scraper for the IT-Resell.com Shopify storefront.
It pages through the full product collection, parses each product card on
category listing pages, deduplicates results by variant ID or product handle,
and returns structured rows ready for CSV export.
"""
from __future__ import annotations

import asyncio
import random
import re

from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser

BASE_URL = "https://www.it-resell.com"
COLLECTION_PATH = "/en/collections/all"
MAX_RETRIES = 3
WORKER_COUNT = 4

CSV_FIELDS = [
    "handle", "name", "product_url", "variant_id", "sku",
    "price_min", "price_max", "availability",
    "description", "ean", "brand", "mpn", "manufacturer",
    "price_zero_flag", "source_url",
    "status", "error_message",
]


def _collection_url(page: int) -> str:
    """Build the URL for a specific page of the IT-Resell full product collection.

    Results are sorted by ascending price so that pagination is stable across
    multiple requests.

    Args:
        page: 1-based page number to request.

    Returns:
        Absolute URL string for the requested collection page.
    """
    return f"{BASE_URL}{COLLECTION_PATH}?sort_by=price-ascending&page={page}"


# ── Fetch with retry ──────────────────────────────────────────────────────────

async def _fetch(session: AsyncSession, url: str, attempt: int = 0) -> str | None:
    """Fetch a URL with randomised exponential-backoff retry on errors.

    Retries on HTTP 429, 403, 503 responses and on any exception, up to
    ``MAX_RETRIES`` times. Delay between retries grows with attempt index and
    includes a small random jitter.

    Args:
        session: An active curl_cffi AsyncSession to issue the request with.
        url: The URL to retrieve.
        attempt: Current retry attempt index, starting at 0.

    Returns:
        Response body as a string, or None if all retries are exhausted or
        a non-retryable HTTP status code is returned.
    """
    try:
        r = await session.get(url, timeout=30)
        if r.status_code == 200:
            return r.text
        if r.status_code in (429, 403, 503) and attempt < MAX_RETRIES:
            delay = (attempt) * 4 + random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
            return await _fetch(session, url, attempt + 1)
        return None
    except Exception:
        if attempt < MAX_RETRIES:
            delay = (attempt) * 4 + random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
            return await _fetch(session, url, attempt + 1)
        return None


# ── Pagination ────────────────────────────────────────────────────────────────

def _get_last_page(html: str) -> int:
    """Determine the total number of pages from pagination links in a collection page.

    Scans ``<a href>`` elements inside ``li.pagination_el`` and extracts the
    highest ``page=N`` query parameter found.

    Args:
        html: Raw HTML string of any collection listing page.

    Returns:
        Highest page number found in the pagination links, or 1 if none are
        present (i.e. the collection fits on a single page).
    """
    tree = HTMLParser(html)
    last = 1
    for a in tree.css("li.pagination_el a[href]"):
        href = a.attributes.get("href", "")
        m = re.search(r"page=(\d+)", href)
        if m:
            last = max(last, int(m.group(1)))
    return last


# ── PLP parsing ───────────────────────────────────────────────────────────────

def _parse_money(text: str) -> float | None:
    """Parse a price string into a float value.

    Strips thousands-separator commas before matching a numeric pattern, so
    both ``"1,299.99"`` and ``"1299.99"`` are handled correctly.

    Args:
        text: Raw price text, e.g. ``"€1,299.99"`` or ``"1299.99 EUR"``.

    Returns:
        Price as a float, or None if no numeric value can be extracted.
    """
    m = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    return float(m.group()) if m else None


def _parse_plp(html: str) -> list[dict]:
    """Parse product cards from a collection listing page into structured dicts.

    Iterates over ``div.product_item`` cards and extracts name, URL, handle,
    price range, variant ID, SKU, and availability from each card's markup.
    Cards that contain neither a handle nor a name are skipped.

    Args:
        html: Raw HTML string of an IT-Resell collection listing page.

    Returns:
        List of product dictionaries, one per valid card, containing the
        fields defined in ``CSV_FIELDS`` (description, EAN, brand, MPN, and
        manufacturer are left empty for later enrichment).
    """
    tree = HTMLParser(html)
    products = []
    for card in tree.css("div.product_item"):
        name_el = card.css_first("a.product-name")
        name = name_el.text(strip=True) if name_el else ""

        link_el = card.css_first("a[href*='/products/']") or card.css_first("a.product-name")
        product_url = ""
        handle = ""
        if link_el:
            href = link_el.attributes.get("href", "")
            product_url = href if href.startswith("http") else BASE_URL + href
            m = re.search(r"/products/([^/?#]+)", href)
            handle = m.group(1) if m else ""

        # Price range
        prices = []
        for span in card.css("span.money"):
            p = _parse_money(span.text(strip=True))
            if p is not None:
                prices.append(p)
        price_min = min(prices) if prices else None
        price_max = max(prices) if prices else None
        price_zero_flag = price_min == 0 if price_min is not None else False

        # Variant ID from hidden input
        variant_id = ""
        inp = card.css_first("input[name='id']")
        if inp:
            variant_id = inp.attributes.get("value", "")

        # SKU
        sku_el = card.css_first("div.single_product__sku")
        sku = sku_el.text(strip=True) if sku_el else ""

        # Availability via class name heuristic
        avail_el = card.css_first("span.availability, div.availability")
        availability = avail_el.text(strip=True) if avail_el else ""

        if not handle and not name:
            continue

        products.append({
            "handle": handle,
            "name": name,
            "product_url": product_url,
            "variant_id": variant_id,
            "sku": sku,
            "price_min": price_min,
            "price_max": price_max,
            "availability": availability,
            "description": "",
            "ean": "",
            "brand": "",
            "mpn": "",
            "manufacturer": "",
            "price_zero_flag": price_zero_flag,
            "source_url": _collection_url(1),
            "status": "ok",
            "error_message": "",
        })
    return products


# ── Worker coroutine ──────────────────────────────────────────────────────────

async def _scrape_pages(session: AsyncSession, pages: range) -> list[dict]:
    """Sequentially fetch and parse a contiguous range of collection pages.

    On a fetch failure the page is recorded as a single error row rather than
    raising an exception, so partial results from other workers are still
    usable.

    Args:
        session: An active curl_cffi AsyncSession to use for all requests.
        pages: Range of 1-based page numbers to fetch in order.

    Returns:
        List of product dictionaries parsed from the requested pages.
        Failed pages contribute one error row each with ``status`` set to
        ``"failed"``.
    """
    products = []
    for page in pages:
        html = await _fetch(session, _collection_url(page))
        if not html:
            products.append({
                "handle": "", "name": "", "product_url": "", "variant_id": "",
                "sku": "", "price_min": None, "price_max": None, "availability": "",
                "description": "", "ean": "", "brand": "", "mpn": "", "manufacturer": "",
                "price_zero_flag": False,
                "source_url": _collection_url(page),
                "status": "failed", "error_message": f"fetch_failed_page_{page}",
            })
            continue
        products.extend(_parse_plp(html))
    return products


# ── Entry point ───────────────────────────────────────────────────────────────

async def run(input_url: str, run_id: str) -> list[dict]:
    """Scrape all products from the IT-Resell full collection.

    Discovers the last collection page, divides the page range across
    ``WORKER_COUNT`` concurrent workers each using their own residential
    proxy session, then deduplicates the combined results by variant ID
    (falling back to product handle).

    Args:
        input_url: Unused URL parameter kept for interface parity with other
            collector ``run`` functions.
        run_id: Unique identifier for this scrape run (used for logging /
            tracing upstream).

    Returns:
        List of deduplicated product row dictionaries. Each row contains the
        fields defined in ``CSV_FIELDS``.

    Raises:
        RuntimeError: If the first collection page cannot be fetched.
    """
    from shared.http_client import make_residential_proxy, make_curl_session

    proxy = make_residential_proxy()
    async with make_curl_session(proxy) as session:
        # Discover last page
        html_p1 = await _fetch(session, _collection_url(1))
        if not html_p1:
            raise RuntimeError("Failed to fetch collection page 1")
        last_page = _get_last_page(html_p1)

    # Split pages across workers
    chunks: list[range] = []
    chunk_size = max(1, (last_page + WORKER_COUNT - 1) // WORKER_COUNT)
    for i in range(WORKER_COUNT):
        start = i * chunk_size + 1
        end = min(start + chunk_size - 1, last_page)
        if start <= end:
            chunks.append(range(start, end + 1))

    # Scrape all chunks concurrently, each with own session
    async def _worker(pages: range) -> list[dict]:
        """Scrape an assigned page range using a dedicated proxy session.

        Creates a fresh residential proxy and curl session for each worker so
        that concurrent workers do not share connection state.

        Args:
            pages: Range of 1-based page numbers assigned to this worker.

        Returns:
            List of product dictionaries scraped from the assigned pages.
        """
        p = make_residential_proxy()
        async with make_curl_session(p) as s:
            return await _scrape_pages(s, pages)

    results = await asyncio.gather(*[_worker(c) for c in chunks])
    all_rows: list[dict] = []
    for chunk_rows in results:
        all_rows.extend(chunk_rows)

    # Dedup on variant_id (fallback to handle)
    seen: set[str] = set()
    deduped: list[dict] = []
    for row in all_rows:
        key = row.get("variant_id") or row.get("handle") or ""
        if not key:
            deduped.append(row)
            continue
        if key not in seen:
            seen.add(key)
            deduped.append(row)

    return deduped
