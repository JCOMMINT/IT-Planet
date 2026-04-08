"""Jacob.de scraper - curl_cffi + price-range splitting.

This module implements an async scraper for jacob.de product listings.
It discovers all product URLs from category pages (PLPs), splitting the
catalogue by price range when a category exceeds the per-range page limit,
then fetches and parses each product detail page (PDP) via JSON-LD.
"""

from __future__ import annotations

import asyncio
import json
import re

from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser

BASE_URL = "https://www.jacob.de"
MAX_PAGE = 500
MAX_RETRIES = 3
SEMAPHORE_LIMIT = 5

CSV_FIELDS = [
    "artnr",
    "name",
    "url",
    "sku",
    "mpn",
    "ean",
    "description",
    "brand",
    "category_path",
    "breadcrumbs",
    "price",
    "currency",
    "price_min",
    "price_max",
    "condition",
    "availability",
    "stock",
    "delivery_time",
    "raw_condition",
    "jsonld_offer_count",
    "jsonld_price_min",
    "jsonld_price_max",
    "status",
    "error_message",
]


# ── URL helpers ───────────────────────────────────────────────────────────────


def _plp_url(cat_url: str, page: int, pmin: float | None = None, pmax: float | None = None) -> str:
    """Build a paginated product listing page URL with optional price filters.

    Args:
        cat_url: Base category URL on jacob.de.
        page: 1-based page number to request.
        pmin: Optional minimum price filter (inclusive, truncated to int).
        pmax: Optional maximum price filter (inclusive, truncated to int).

    Returns:
        Fully formed PLP URL string with query parameters appended.
    """
    url = f"{cat_url}?sortBy=preis_up"
    if pmin is not None:
        url += f"&price-min={int(pmin)}"
    if pmax is not None:
        url += f"&price-max={int(pmax)}"
    url += f"&page={page}"
    return url


# ── Fetch with retry ──────────────────────────────────────────────────────────


async def _fetch(
    session: AsyncSession, url: str, sem: asyncio.Semaphore, attempt: int = 0
) -> str | None:
    """Fetch a URL with exponential-backoff retry on rate-limit or network errors.

    The semaphore is released between attempts so retries do not deadlock
    when all semaphore slots are held by the same coroutine chain.

    Args:
        session: An active curl_cffi AsyncSession to issue the request with.
        url: The URL to retrieve.
        sem: Semaphore used to cap concurrent in-flight requests.
        attempt: Current retry attempt index, starting at 0. Used internally
            for recursion; callers should omit this.

    Returns:
        Response body as a string, or None if all retries are exhausted or
        a non-retryable HTTP status code is returned.
    """
    for attempt in range(MAX_RETRIES + 1):
        async with sem:
            try:
                r = await session.get(url, timeout=45)
            except Exception:
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1.5 * (2**attempt))
                    continue
                return None
        if r.status_code == 200:
            return r.text
        if r.status_code in (429, 403, 503) and attempt < MAX_RETRIES:
            await asyncio.sleep(1.5 * (2**attempt))
            continue
        return None
    return None


# ── Pagination ────────────────────────────────────────────────────────────────


def _is_empty(html: str) -> bool:
    """Determine whether a PLP response contains any product links.

    Args:
        html: Raw HTML string of a category listing page.

    Returns:
        True if no product anchor tags are found, False otherwise.
    """
    return not HTMLParser(html).css("a[href*='/produkte/']")


async def _last_page(
    session: AsyncSession,
    cat_url: str,
    sem: asyncio.Semaphore,
    pmin: float | None = None,
    pmax: float | None = None,
) -> int:
    """Find the last non-empty page for a category via binary search.

    Args:
        session: An active curl_cffi AsyncSession.
        cat_url: Base category URL on jacob.de.
        sem: Semaphore used to cap concurrent requests.
        pmin: Optional minimum price filter applied to each probed page.
        pmax: Optional maximum price filter applied to each probed page.

    Returns:
        1-based index of the last page that contains at least one product link.
    """
    lo, hi = 1, MAX_PAGE
    while lo < hi:
        mid = (lo + hi + 1) // 2
        html = await _fetch(session, _plp_url(cat_url, mid, pmin, pmax), sem)
        if html and not _is_empty(html):
            lo = mid
        else:
            hi = mid - 1
    return lo


async def _split_ranges(
    session: AsyncSession,
    cat_url: str,
    sem: asyncio.Semaphore,
    pmin: float,
    pmax: float,
) -> list[tuple[float, float]]:
    """Recursively split a price range until every sub-range fits within MAX_PAGE.

    Probes the last page for the given price band. If the band still spans
    MAX_PAGE pages or more the midpoint is computed and both halves are split
    independently until every leaf range is safely under the page cap.

    Args:
        session: An active curl_cffi AsyncSession.
        cat_url: Base category URL on jacob.de.
        sem: Semaphore used to cap concurrent requests.
        pmin: Lower bound of the price range to probe.
        pmax: Upper bound of the price range to probe.

    Returns:
        List of (pmin, pmax) tuples, each guaranteed to contain fewer than
        MAX_PAGE pages of results.
    """
    last_p = await _last_page(session, cat_url, sem, pmin, pmax)
    if last_p < MAX_PAGE:
        return [(pmin, pmax)]
    mid = (pmin + pmax) / 2
    left = await _split_ranges(session, cat_url, sem, pmin, mid)
    right = await _split_ranges(session, cat_url, sem, mid, pmax)
    return left + right


async def _get_price_ranges(
    session: AsyncSession,
    cat_url: str,
    sem: asyncio.Semaphore,
) -> list[tuple[float | None, float | None]]:
    """Determine the set of price ranges needed to cover an entire category.

    If the category fits within MAX_PAGE pages without any price filter,
    returns a single ``(None, None)`` sentinel meaning "no filter needed".
    Otherwise probes the page for the maximum available price from the filter
    facet and delegates to ``_split_ranges`` to produce a safe partition.

    Args:
        session: An active curl_cffi AsyncSession.
        cat_url: Base category URL on jacob.de.
        sem: Semaphore used to cap concurrent requests.

    Returns:
        List of (pmin, pmax) tuples. A single ``(None, None)`` entry means the
        whole category can be scraped without a price filter.
    """
    last_p = await _last_page(session, cat_url, sem)
    if last_p < MAX_PAGE:
        return [(None, None)]

    # Fetch page 1 to probe max price from filter facet
    html = await _fetch(session, _plp_url(cat_url, 1), sem)
    max_price: float = 50000.0
    if html:
        tree = HTMLParser(html)
        for inp in tree.css("input[data-price-max]"):
            try:
                max_price = float(inp.attributes.get("data-price-max", "50000"))
                break
            except (ValueError, TypeError):
                pass
        # fallback: look for price-to slider value
        if max_price == 50000.0:
            for inp in tree.css("input#price-to, input[name='price-to']"):
                try:
                    max_price = float(inp.attributes.get("value", "50000"))
                    break
                except (ValueError, TypeError):
                    pass

    return await _split_ranges(session, cat_url, sem, 0.0, max_price)


# ── PLP parsing ───────────────────────────────────────────────────────────────


def _parse_product_urls(html: str) -> set[str]:
    """Extract and deduplicate absolute product URLs from a PLP HTML page.

    Query parameters are stripped from each URL so that the same product
    appearing in multiple filter facets is not counted twice.

    Args:
        html: Raw HTML string of a category listing page.

    Returns:
        Set of absolute product URL strings with query parameters removed.
    """
    urls = set()
    for a in HTMLParser(html).css("a[href*='/produkte/']"):
        href = a.attributes.get("href", "")
        if href:
            full = href if href.startswith("http") else BASE_URL + href
            urls.add(full.split("?")[0])  # strip query params for dedup
    return urls


async def _scrape_plp_range(
    session: AsyncSession,
    cat_url: str,
    sem: asyncio.Semaphore,
    pmin: float | None,
    pmax: float | None,
) -> set[str]:
    """Fetch every page of a price-filtered category range and collect product URLs.

    All pages within the range are fetched concurrently (bounded by ``sem``) and
    their product links are merged into a single deduplicated set.

    Args:
        session: An active curl_cffi AsyncSession.
        cat_url: Base category URL on jacob.de.
        sem: Semaphore used to cap concurrent requests.
        pmin: Lower price bound passed to the PLP URL builder, or None.
        pmax: Upper price bound passed to the PLP URL builder, or None.

    Returns:
        Set of absolute product URLs found across all pages in this range.
    """
    last_p = await _last_page(session, cat_url, sem, pmin, pmax)
    tasks = [_fetch(session, _plp_url(cat_url, p, pmin, pmax), sem) for p in range(1, last_p + 1)]
    results = await asyncio.gather(*tasks)
    urls: set[str] = set()
    for html in results:
        if html:
            urls.update(_parse_product_urls(html))
    return urls


# ── PDP parsing ───────────────────────────────────────────────────────────────


def _normalize_condition(raw: str) -> str:
    """Map a raw item-condition string to a canonical label.

    Performs case-insensitive keyword matching against known condition
    vocabularies in both English and German.

    Args:
        raw: Raw condition string, typically sourced from a JSON-LD offer's
            ``itemCondition`` field.

    Returns:
        One of ``"New"``, ``"Refurbished"``, ``"Open Box"``, ``"Used"``,
        or the original ``raw`` value if no keyword matches.
    """
    r = raw.lower()
    if any(x in r for x in ["refurb", "renewed", "erneuer"]):
        return "Refurbished"
    if any(x in r for x in ["new", "neu", "brand"]):
        return "New"
    if any(x in r for x in ["bware", "b-ware", "geöffnet", "opened", "b_ware"]):
        return "Open Box"
    if any(x in r for x in ["used", "gebraucht"]):
        return "Used"
    return raw


def _extract_jsonld(data: dict) -> dict:
    """Extract structured product fields from a JSON-LD Product schema dict.

    Handles both single-offer and multi-offer ``offers`` values. Prices are
    gathered from ``price``, ``lowPrice``, and ``highPrice`` keys. Condition
    strings are normalised via ``_normalize_condition``.

    Args:
        data: Parsed JSON-LD dictionary whose ``@type`` is ``"Product"``.

    Returns:
        Dictionary containing keys: ``name``, ``sku``, ``mpn``, ``ean``,
        ``description``, ``brand``, ``price``, ``currency``, ``price_min``,
        ``price_max``, ``condition``, ``raw_condition``, ``availability``,
        ``stock``, ``delivery_time``, ``jsonld_offer_count``,
        ``jsonld_price_min``, ``jsonld_price_max``.
    """
    raw_offer = data.get("offers", {})
    offers = raw_offer if isinstance(raw_offer, list) else [raw_offer]

    prices = []
    conditions = []
    raw_conditions = []
    currency = "EUR"
    availability = ""

    for o in offers:
        for price_key in ("price", "lowPrice", "highPrice"):
            try:
                prices.append(float(o.get(price_key) or 0))
            except (ValueError, TypeError):
                pass
        raw_cond = o.get("itemCondition", "")
        raw_conditions.append(raw_cond)
        conditions.append(_normalize_condition(raw_cond))
        currency = o.get("priceCurrency", currency)
        availability = o.get("availability", availability)

    price_min = min((p for p in prices if p > 0), default=None)
    price_max = max((p for p in prices if p > 0), default=None)

    brand = data.get("brand")
    brand_name = brand.get("name", "") if isinstance(brand, dict) else (brand or "")

    return {
        "name": data.get("name", ""),
        "sku": data.get("sku", ""),
        "mpn": data.get("mpn", ""),
        "ean": data.get("gtin13") or data.get("gtin14") or data.get("gtin", ""),
        "description": (data.get("description") or "")[:500],
        "brand": brand_name,
        "price": price_min,
        "currency": currency,
        "price_min": price_min,
        "price_max": price_max,
        "condition": conditions[0] if conditions else "",
        "raw_condition": raw_conditions[0] if raw_conditions else "",
        "availability": availability,
        "stock": "",
        "delivery_time": "",
        "jsonld_offer_count": len(offers),
        "jsonld_price_min": price_min,
        "jsonld_price_max": price_max,
    }


def _parse_pdp(html: str) -> dict | None:
    """Parse a product detail page HTML and return structured product data.

    Scans all ``<script type="application/ld+json">`` blocks looking for a
    node whose ``@type`` is ``"Product"``, including nodes nested inside an
    ``@graph`` array.

    Args:
        html: Raw HTML string of a jacob.de product detail page.

    Returns:
        Dictionary of product fields from ``_extract_jsonld``, or None if no
        valid Product JSON-LD block is found.
    """
    tree = HTMLParser(html)
    for script in tree.css("script[type='application/ld+json']"):
        try:
            raw = script.text()
            if not raw:
                continue
            data = json.loads(raw)
            if isinstance(data, dict):
                if data.get("@type") == "Product":
                    return _extract_jsonld(data)
                if "@graph" in data:
                    for item in data["@graph"]:
                        if isinstance(item, dict) and item.get("@type") == "Product":
                            return _extract_jsonld(item)
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


def _artnr_from_url(url: str) -> str:
    """Extract the numeric article number from a jacob.de product URL.

    Expects a URL path segment matching the pattern
    ``/produkte/<slug>-<artnr>``.

    Args:
        url: Absolute product URL string.

    Returns:
        Article number as a string, or an empty string if the pattern is not
        matched.
    """
    m = re.search(r"/produkte/[^/?#]+-(\d+)(?:[/?#]|$)", url)
    return m.group(1) if m else ""


async def _scrape_pdp(session: AsyncSession, url: str, sem: asyncio.Semaphore) -> dict:
    """Fetch and parse a single product detail page, returning a data row.

    Always returns a dictionary with at least the ``artnr``, ``url``,
    ``category_path``, ``breadcrumbs``, ``status``, and ``error_message``
    keys so that failed rows can still be written to the output CSV.

    Args:
        session: An active curl_cffi AsyncSession.
        url: Absolute URL of the product detail page to scrape.
        sem: Semaphore used to cap concurrent requests.

    Returns:
        Dictionary of product fields on success (``status`` is ``"ok"``), or a
        partial dictionary with ``status`` set to ``"failed"`` and an
        ``error_message`` describing the failure reason.
    """
    artnr = _artnr_from_url(url)
    base = {"artnr": artnr, "url": url, "category_path": "", "breadcrumbs": ""}

    html = await _fetch(session, url, sem)
    if not html:
        return {**base, "status": "failed", "error_message": "fetch_failed"}

    parsed = _parse_pdp(html)
    if not parsed:
        return {**base, "status": "failed", "error_message": "parse_failed"}

    return {**base, **parsed, "status": "ok", "error_message": ""}


# ── Entry point ───────────────────────────────────────────────────────────────


async def run(input_url: str, run_id: str) -> list[dict]:
    """Scrape all products from a jacob.de category URL.

    Orchestrates the full pipeline: price-range discovery, concurrent PLP
    scraping across all ranges, concurrent PDP scraping, and deduplication
    by article number.

    Args:
        input_url: Full URL of the jacob.de category page to scrape.
        run_id: Unique identifier for this scrape run (used for logging /
            tracing upstream).

    Returns:
        List of product row dictionaries, deduplicated by ``artnr``. Each
        row contains the fields defined in ``CSV_FIELDS``.
    """
    from shared.http_client import make_curl_session, make_dc_proxy

    proxy = make_dc_proxy(sticky=True)
    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)

    async with make_curl_session(proxy) as session:
        ranges = await _get_price_ranges(session, input_url, sem)

        all_urls: set[str] = set()
        for pmin, pmax in ranges:
            urls = await _scrape_plp_range(session, input_url, sem, pmin, pmax)
            all_urls.update(urls)

        pdp_tasks = [_scrape_pdp(session, url, sem) for url in all_urls]
        rows = await asyncio.gather(*pdp_tasks)

    # Dedup on artnr, keeping first occurrence
    seen: set[str] = set()
    deduped: list[dict] = []
    for row in rows:
        key = row.get("artnr") or row.get("url", "")
        if key not in seen:
            seen.add(key)
            deduped.append(row)

    return deduped
