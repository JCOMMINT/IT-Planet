"""Jacob.de scraper - curl_cffi + price-range splitting.

This module implements an async scraper for jacob.de product listings.
It discovers all product URLs from category pages (PLPs), splitting the
catalogue by price range when a category exceeds the per-range page limit,
then fetches and parses each product detail page (PDP) via JSON-LD.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

import os

from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser

logger = logging.getLogger(__name__)

BASE_URL = "https://www.jacob.de"
MAX_PAGE = 500
MAX_RETRIES = 3
SEMAPHORE_LIMIT = int(os.getenv("SCRAPER_CONCURRENCY", "5"))

CSV_FIELDS = [
    "product_url", "product_name", "brand", "model", "mpn", "sku",
    "breadcrumb", "prices", "input_url", "nav_page_url",
    "status", "error_message",
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
    left, right = await asyncio.gather(
        _split_ranges(session, cat_url, sem, pmin, mid),
        _split_ranges(session, cat_url, sem, mid, pmax),
    )
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
) -> dict[str, str]:
    """Fetch every page of a price-filtered category range and collect product URLs.

    All pages within the range are fetched concurrently (bounded by ``sem``) and
    their product links are merged. Returns a mapping of product URL → nav_page_url
    (the PLP page where the product was first seen).

    Args:
        session: An active curl_cffi AsyncSession.
        cat_url: Base category URL on jacob.de.
        sem: Semaphore used to cap concurrent requests.
        pmin: Lower price bound passed to the PLP URL builder, or None.
        pmax: Upper price bound passed to the PLP URL builder, or None.

    Returns:
        Dict mapping absolute product URL → nav_page_url (first PLP page seen on).
    """
    last_p = await _last_page(session, cat_url, sem, pmin, pmax)
    page_urls = [_plp_url(cat_url, p, pmin, pmax) for p in range(1, last_p + 1)]
    results = await asyncio.gather(*[_fetch(session, pu, sem) for pu in page_urls])
    url_to_nav: dict[str, str] = {}
    for page_url, html in zip(page_urls, results):
        if html:
            for prod_url in _parse_product_urls(html):
                url_to_nav.setdefault(prod_url, page_url)  # keep first page seen
    return url_to_nav


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

    Handles both single-offer and multi-offer ``offers`` values. Builds a
    ``prices`` dict keyed by normalized condition label.

    Args:
        data: Parsed JSON-LD dictionary whose ``@type`` is ``"Product"``.

    Returns:
        Dictionary containing keys: ``product_name``, ``sku``, ``mpn``,
        ``brand``, ``prices``.
    """
    raw_offer = data.get("offers", {})
    offers = raw_offer if isinstance(raw_offer, list) else [raw_offer]

    brand = data.get("brand")
    brand_name = brand.get("name", "") if isinstance(brand, dict) else (brand or "")

    prices: dict[str, float] = {}
    for o in offers:
        cond = _normalize_condition(o.get("itemCondition", ""))
        for price_key in ("price", "lowPrice"):
            try:
                v = float(o.get(price_key) or 0)
                if v > 0:
                    prices[cond] = v
                    break
            except (ValueError, TypeError):
                pass

    return {
        "product_name": data.get("name", ""),
        "sku": data.get("sku", ""),
        "mpn": data.get("mpn", ""),
        "brand": brand_name,
        "prices": json.dumps(prices, ensure_ascii=False),
    }


def _parse_pdp(html: str) -> dict | None:
    """Parse a product detail page HTML and return structured product data.

    Scans all ``<script type="application/ld+json">`` blocks for a Product
    node and an optional BreadcrumbList node (both at root and inside @graph).
    Breadcrumb is built by joining item names[1:-1] (skip home + product).

    Args:
        html: Raw HTML string of a jacob.de product detail page.

    Returns:
        Dictionary of product fields including ``breadcrumb``, or None if no
        valid Product JSON-LD block is found.
    """
    tree = HTMLParser(html)
    product_data: dict | None = None
    breadcrumb_items: list = []

    for script in tree.css("script[type='application/ld+json']"):
        try:
            raw = script.text()
            if not raw:
                continue
            data = json.loads(raw)
            if not isinstance(data, dict):
                continue
            nodes = data.get("@graph", [data])
            for item in nodes:
                if not isinstance(item, dict):
                    continue
                t = item.get("@type")
                if t == "Product" and product_data is None:
                    product_data = _extract_jsonld(item)
                elif t == "BreadcrumbList" and not breadcrumb_items:
                    breadcrumb_items = item.get("itemListElement", [])
        except (json.JSONDecodeError, AttributeError):
            continue

    if product_data is None:
        return None

    if breadcrumb_items:
        sorted_items = sorted(breadcrumb_items, key=lambda x: x.get("position", 0))
        names = [
            (i.get("name") or (i.get("item") or {}).get("name", ""))
            for i in sorted_items
        ]
        names = [n for n in names if n]
        product_data["breadcrumb"] = " > ".join(names[1:-1])
    else:
        product_data["breadcrumb"] = ""

    return product_data


def _breadcrumb_from_url(url: str) -> str:
    """Derive a breadcrumb string from a jacob.de category URL.

    Parses the URL path, drops the ``kategorie`` prefix if present, drops
    file extensions, title-cases each segment, and joins with `` > ``.
    Single-segment URLs (e.g. ``/racks/``) return that segment alone.
    """
    from urllib.parse import urlparse
    path = urlparse(url).path
    parts = [p for p in path.split("/") if p]
    # Drop known structural prefix
    if parts and parts[0] == "kategorie":
        parts = parts[1:]
    # Drop last segment if it looks like a product slug (contains a dot, e.g. .html)
    if len(parts) > 1 and "." in parts[-1]:
        parts = parts[:-1]
    # Title-case and replace hyphens with spaces for readability
    parts = [p.replace("-", " ").title() for p in parts]
    return " > ".join(parts)


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


async def _scrape_pdp(
    session: AsyncSession,
    url: str,
    sem: asyncio.Semaphore,
    nav_page_url: str = "",
    input_url: str = "",
) -> dict:
    """Fetch and parse a single product detail page, returning a data row.

    Always returns a dictionary with at least ``product_url``, ``nav_page_url``,
    ``input_url``, ``status``, and ``error_message`` so failed rows are still
    written to the output CSV.

    Args:
        session: An active curl_cffi AsyncSession.
        url: Absolute URL of the product detail page to scrape.
        sem: Semaphore used to cap concurrent requests.
        nav_page_url: PLP page URL where this product was discovered.
        input_url: Category URL that seeded this scrape run.

    Returns:
        Dictionary of product fields on success (``status`` is ``"ok"``), or a
        partial dictionary with ``status`` set to ``"failed"``.
    """
    base = {"product_url": url, "nav_page_url": nav_page_url, "input_url": input_url}

    html = await _fetch(session, url, sem)
    if not html:
        return {**base, "status": "failed", "error_message": "fetch_failed"}

    parsed = _parse_pdp(html)
    if not parsed:
        return {**base, "status": "failed", "error_message": "parse_failed"}

    return {**base, **parsed, "status": "ok", "error_message": ""}


# ── Per-range scrape with its own sticky session ──────────────────────────────


async def _scrape_range(
    input_url: str,
    sem: asyncio.Semaphore,
    pmin: float | None,
    pmax: float | None,
    slot: int,
) -> dict[str, str]:
    """Scrape one price-filtered range using a dedicated sticky proxy session.

    Each parallel range gets its own exit IP (slot-based sticky proxy) so
    concurrent ranges don't share the same datacenter node.

    Args:
        input_url: Base category URL on jacob.de.
        sem: Shared semaphore capping concurrent in-flight requests.
        pmin: Lower price bound, or None for no filter.
        pmax: Upper price bound, or None for no filter.
        slot: Deterministic slot index used to select a distinct exit node.

    Returns:
        Dict mapping product URL → nav_page_url for all products in this range.
    """
    from shared.http_client import make_curl_session, make_dc_proxy

    proxy = make_dc_proxy(sticky=True, slot=slot)
    async with make_curl_session(proxy) as sess:
        return await _scrape_plp_range(sess, input_url, sem, pmin, pmax)


# ── Entry point ───────────────────────────────────────────────────────────────


async def run(input_url: str, run_id: str) -> list[dict]:
    """Scrape all products from a jacob.de category URL.

    Orchestrates the full pipeline: price-range discovery, concurrent PLP
    scraping across all ranges, concurrent PDP scraping, and deduplication
    by product URL.

    Args:
        input_url: Full URL of the jacob.de category page to scrape.
        run_id: Unique identifier for this scrape run (used for logging /
            tracing upstream).

    Returns:
        List of product row dictionaries, deduplicated by ``product_url``.
        Each row contains the fields defined in ``CSV_FIELDS``.
    """
    from shared.http_client import make_curl_session, make_dc_proxy

    logger.info("run started run_id=%s input_url=%s", run_id, input_url)
    proxy = make_dc_proxy(sticky=True)
    sem = asyncio.Semaphore(SEMAPHORE_LIMIT)

    async with make_curl_session(proxy) as session:
        ranges = await _get_price_ranges(session, input_url, sem)
        logger.info("Price ranges found: %d", len(ranges))

        url_to_nav: dict[str, str] = {}
        range_batches = await asyncio.gather(
            *[_scrape_range(input_url, sem, pmin, pmax, slot=i)
              for i, (pmin, pmax) in enumerate(ranges)],
            return_exceptions=True,
        )
        for i, batch in enumerate(range_batches):
            if isinstance(batch, Exception):
                logger.warning("PLP range %d failed: %s", i, batch)
                continue
            for prod_url, nav in batch.items():
                url_to_nav.setdefault(prod_url, nav)
        logger.info("PLP done — %d unique product URLs", len(url_to_nav))

        logger.info("Fetching %d PDPs", len(url_to_nav))
        pdp_tasks = [
            _scrape_pdp(session, url, sem, nav_page_url=nav, input_url=input_url)
            for url, nav in url_to_nav.items()
        ]
        results = await asyncio.gather(*pdp_tasks, return_exceptions=True)

    # Breadcrumb derived from input_url — used as fallback when JSON-LD is absent
    url_breadcrumb = _breadcrumb_from_url(input_url)

    # Resolve exceptions → failed rows; compute model; dedup by product_url
    seen: set[str] = set()
    deduped: list[dict] = []
    for url, result in zip(url_to_nav, results):
        if isinstance(result, Exception):
            logger.warning("PDP exception url=%s error=%s", url, result)
            result = {
                "product_url": url,
                "nav_page_url": url_to_nav[url],
                "input_url": input_url,
                "status": "failed",
                "error_message": str(result),
            }
        key = result.get("product_url", "")
        if key and key not in seen:
            seen.add(key)
            # Derive model: product_name minus leading brand prefix
            name = result.get("product_name", "")
            brand = result.get("brand", "")
            if brand and name.startswith(brand):
                result["model"] = name[len(brand):].strip()
            else:
                result["model"] = name.split(" ", 1)[1] if " " in name else ""
            # Fill breadcrumb from input_url when JSON-LD didn't provide one
            if not result.get("breadcrumb"):
                result["breadcrumb"] = url_breadcrumb
            deduped.append(result)

    logger.info("run complete run_id=%s total=%d deduped=%d", run_id, len(results), len(deduped))
    return deduped
