"""IT-Market.com scraper – 5-sort strategy, product_code dedup."""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re

import os

from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser

log = logging.getLogger(__name__)

BASE_URL = "https://it-market.com"
MAX_PAGE_CAP = 415
MAX_RETRIES = 3
SORTS = ["name-asc", "name-desc", "price-asc", "price-desc", "topseller"]
CONCURRENCY = int(os.getenv("SCRAPER_CONCURRENCY", "5"))  # max simultaneous HTTP requests

CSV_FIELDS = [
    "product_url", "product_name", "brand", "model", "mpn", "sku",
    "breadcrumb", "prices", "input_url", "nav_page_url",
    "status", "error_message",
]


# ── URL helpers ───────────────────────────────────────────────────────────────

def _sort_url(subcat_url: str, sort: str, page: int) -> str:
    """Build a paginated, sorted URL for a subcategory listing page.

    Args:
        subcat_url: The base subcategory URL without query parameters.
        sort: The sort identifier (e.g. ``"name-asc"``, ``"price-desc"``).
        page: The 1-based page number to request.

    Returns:
        A fully constructed URL with ``order`` and ``p`` query parameters.
    """
    base = subcat_url.rstrip("/")
    return f"{base}?order={sort}&p={page}"


# ── Fetch with retry ──────────────────────────────────────────────────────────

async def _fetch(session: AsyncSession, url: str, attempt: int = 0, _sem: asyncio.Semaphore | None = None) -> str | None:
    """Fetch a URL with automatic retry on rate-limit and transient errors.

    Rotates to a fresh proxy exit node on every attempt. Retries up to
    ``MAX_RETRIES`` times. Timeout/connection errors retry fast; rate-limit
    responses back off slowly.

    Args:
        session: An active ``curl_cffi`` async HTTP session.
        url: The URL to retrieve.
        attempt: Current retry attempt number (0-indexed). Used internally
            for recursion; callers should omit this.

    Returns:
        The response body as a string on HTTP 200, or ``None`` if the request
        ultimately fails after all retries.
    """
    from shared.http_client import make_dc_proxy

    if _sem is not None:
        async with _sem:
            return await _fetch(session, url, attempt, _sem=None)

    try:
        proxy = make_dc_proxy()   # fresh exit node every attempt
        r = await session.get(
            url,
            proxies=proxy,
            timeout=20,
            headers={
                "accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.9",
                "referer":         "https://www.google.com/",
            },
        )
        log.debug("  GET %s → %d", url, r.status_code)
        if r.status_code == 200:
            return r.text
        if r.status_code in (429, 403, 503) and attempt < MAX_RETRIES:
            wait = (attempt + 1) * 5 + random.uniform(1, 3)
            log.warning("  HTTP %d — retry %d/%d in %.1fs — %s", r.status_code, attempt + 1, MAX_RETRIES, wait, url)
            await asyncio.sleep(wait)
            return await _fetch(session, url, attempt + 1)
        log.error("  HTTP %d — giving up — %s", r.status_code, url)
        return None
    except Exception as e:
        err = str(e).lower()
        is_timeout = any(k in err for k in ("timed out", "timeout", "operation timed", "28,"))
        is_conn    = any(k in err for k in ("connection", "proxy", "ssl", "eof", "reset"))
        if (is_timeout or is_conn) and attempt < MAX_RETRIES:
            wait = random.uniform(0.3, 1.0)
            kind = "TIMEOUT" if is_timeout else "CONN_ERR"
            log.warning("  %s [%d/%d] — retry in %.1fs — %s", kind, attempt + 1, MAX_RETRIES, wait, url)
            await asyncio.sleep(wait)
            return await _fetch(session, url, attempt + 1)
        log.error("  FATAL %s — %s", url, e)
        return None


# ── Category discovery ────────────────────────────────────────────────────────

def _extract_top_cats(html: str) -> list[str]:
    """Extract top-level category URLs from the main navigation bar.

    Args:
        html: Raw HTML string of the site's home or any page that
            contains the primary navigation element.

    Returns:
        A deduplicated, order-preserving list of absolute category URLs
        that contain ``/en/`` in their path.
    """
    tree = HTMLParser(html)
    urls = []
    for a in tree.css("nav.main-navigation a[href*='/en/']"):
        href = a.attributes.get("href", "")
        if href and "/en/" in href:
            full = href if href.startswith("http") else BASE_URL + href
            urls.append(full)
    return list(dict.fromkeys(urls))  # preserve order, dedup


def _extract_subcats(html: str, base_cat_url: str) -> list[str]:
    """Extract subcategory URLs from the navigation flyout or sidebar.

    Searches multiple CSS selectors that IT Market uses for flyout menus
    and category sidebars, returning only internal ``/en/`` URLs.

    Args:
        html: Raw HTML string of a top-level category page.
        base_cat_url: The URL of the page that was fetched, used for
            context (currently unused but kept for future filtering).

    Returns:
        A deduplicated, order-preserving list of absolute subcategory URLs.
    """
    tree = HTMLParser(html)
    subcats = []
    for a in tree.css("div.navigation-flyout a[href], div.category-sidebar a[href], ul.cms-navigation-link a[href]"):
        href = a.attributes.get("href", "")
        if href and "/en/" in href:
            full = href if href.startswith("http") else BASE_URL + href
            subcats.append(full)
    return list(dict.fromkeys(subcats))


async def _get_last_page(session: AsyncSession, subcat_url: str, sort: str = "name-asc", sem: asyncio.Semaphore | None = None) -> int:
    """Determine the highest pagination page number for a subcategory.

    Fetches the first page of the listing and inspects ``[data-page]``
    attributes and ``div.pagination`` anchor ``href`` values to find the
    maximum page number. The result is capped at ``MAX_PAGE_CAP``.

    Args:
        session: An active ``curl_cffi`` async HTTP session.
        subcat_url: The base subcategory URL (without query parameters).
        sort: Sort order string used when building the request URL.

    Returns:
        The last (maximum) available page number, capped at ``MAX_PAGE_CAP``.
    """
    html = await _fetch(session, _sort_url(subcat_url, sort, 1), _sem=sem)
    if not html:
        return 1
    tree = HTMLParser(html)
    last = 1
    # Try data-page attribute on pagination elements
    for el in tree.css("[data-page]"):
        try:
            last = max(last, int(el.attributes.get("data-page", "1")))
        except (ValueError, TypeError):
            pass
    # Fallback: hrefs with p= param
    if last == 1:
        for a in tree.css("div.pagination a[href]"):
            m = re.search(r"[?&]p=(\d+)", a.attributes.get("href", ""))
            if m:
                last = max(last, int(m.group(1)))
    return min(last, MAX_PAGE_CAP)


async def _probe_subcat(session: AsyncSession, subcat_url: str) -> tuple[int, int]:
    """Fetch total product count and last pagination page for a subcategory.

    Args:
        session: An active ``curl_cffi`` async HTTP session.
        subcat_url: The base subcategory URL to probe.

    Returns:
        A tuple of ``(total_products, last_page)``. Both values are ``0``
        if the page cannot be fetched.
    """
    html = await _fetch(session, _sort_url(subcat_url, "name-asc", 1))
    if not html:
        return 0, 0
    tree = HTMLParser(html)
    total = 0
    total_el = tree.css_first("span.total-count, p.cms-listing-result-count")
    if total_el:
        m = re.search(r"(\d[\d,.]*)", total_el.text(strip=True).replace(".", "").replace(",", ""))
        if m:
            total = int(m.group(1))
    last = await _get_last_page(session, subcat_url)
    return total, last


# ── PLP parsing ───────────────────────────────────────────────────────────────

def _parse_money(text: str) -> float | None:
    """Parse a price string into a float, handling European number formats.

    Strips non-numeric characters, normalises comma decimal separators, and
    collapses ambiguous multi-dot strings (e.g. ``"1.234.56"`` → ``1234.56``).

    Args:
        text: Raw price text such as ``"€1.234,56"`` or ``"1,099.00"``.

    Returns:
        The parsed price as a float, or ``None`` if parsing fails.
    """
    cleaned = re.sub(r"[^\d.,]", "", text).replace(",", ".")
    # Handle "1.234.56" → "1234.56"
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_plp(html: str, input_url: str, nav_page_url: str = "") -> list[dict]:
    """Parse product listing page HTML into a list of product dicts.

    Iterates over every ``div.product-box`` card, extracting product identity
    fields, descriptive metadata, and variant information. Falls back to a
    single synthetic variant when no explicit variant options are present.
    Cards with neither a product code nor a product name are skipped.

    Args:
        html: Raw HTML string of the product listing page.
        input_url: The subcategory URL that produced this page, stored on
            each product record for traceability.
        nav_page_url: The paginated URL where this product was found.

    Returns:
        A list of product dicts whose keys match ``CSV_FIELDS``.
    """
    tree = HTMLParser(html)
    products = []
    for card in tree.css("div.product-box"):
        # Product URL + name
        a_el = card.css_first("a.product-name")
        name = a_el.text(strip=True) if a_el else ""
        href = a_el.attributes.get("href", "") if a_el else ""
        product_url = (href if href.startswith("http") else BASE_URL + href) if href else ""

        # IDs
        id_inp = card.css_first("input[name='product-id']")
        product_id = id_inp.attributes.get("value", "") if id_inp else ""

        # Brand + model from product name ("Fortinet FortiGate-40F" → "Fortinet", "FortiGate-40F")
        name_parts = name.split(" ", 1)
        brand = name_parts[0] if name_parts else ""
        model = name_parts[1] if len(name_parts) > 1 else ""

        # Breadcrumb from URL path (category > subcategory > subcategory2)
        category = subcategory = subcategory2 = ""
        if product_url:
            parts = product_url.rstrip("/").split("/")
            try:
                rel = parts[parts.index("en") + 1:]  # everything after /en/
                category     = rel[0] if len(rel) > 0 else ""
                subcategory  = rel[1] if len(rel) > 1 else ""
                subcategory2 = rel[2] if len(rel) > 2 else ""
            except (ValueError, IndexError):
                pass

        # EAN
        ean_el = card.css_first("span.product-ean")
        ean_upc = ean_el.text(strip=True) if ean_el else ""

        # Variants
        variants = []
        for opt in card.css("div.product-detail-configurator-option"):
            variant_id = opt.attributes.get("data-product-id", "")

            # Condition: text node in div BEFORE the span child.
            # selectolax.text() concatenates nodes without spaces, so we read
            # the raw HTML and split on <span to get only the direct text.
            text_div   = opt.css_first("div.maxia-variants-list-text")
            avail_span = text_div.css_first("span") if text_div else None
            span_text  = avail_span.text(strip=True) if avail_span else ""
            condition  = ""
            if text_div:
                div_html    = text_div.html or ""
                before_span = re.split(r"<span", div_html, maxsplit=1)[0]
                before_span = re.sub(r"^<[^>]+>", "", before_span)  # strip opening div tag
                before_span = re.sub(r"<[^>]+>", "", before_span)   # strip <br> and any other tags
                condition   = " ".join(before_span.split())          # collapse whitespace/newlines

            # Availability from span class name
            if avail_span:
                cls = avail_span.attributes.get("class", "")
                if "inStock" in cls:
                    availability = "In Stock"
                elif "withDelivery" in cls:
                    availability = "With Delivery"
                else:
                    availability = span_text
            else:
                availability = ""

            # Price: p.product-price inside the variant option
            price_el   = opt.css_first("p.product-price")
            price_text = price_el.text(strip=True) if price_el else ""
            price      = _parse_money(price_text)
            if price is None and "request" in price_text.lower():
                price = "on_request"

            # Stock: "23 available" → 23
            stock_el = opt.css_first("div.product-variant-stock")
            stock = None
            if stock_el:
                m = re.search(r"\d+", stock_el.text(strip=True))
                stock = int(m.group()) if m else None

            variants.append({
                "variant_id": variant_id,
                "condition": condition,
                "price": price,
                "stock": stock,
                "availability": availability,
            })

        # Fallback single variant when no configurator options present
        if not variants:
            price_el   = card.css_first("p.product-price")
            price_text = price_el.text(strip=True) if price_el else ""
            price      = _parse_money(price_text)
            if price is None and "request" in price_text.lower():
                price = "on_request"
            variants.append({
                "variant_id": product_id,
                "condition": "New",
                "price": price,
                "stock": None,
                "availability": "",
            })

        if not product_id and not name:
            continue

        crumb_parts = [p for p in [category, subcategory, subcategory2] if p]
        breadcrumb = " > ".join(p.replace("-", " ").title() for p in crumb_parts)

        prices = {
            f"{v['condition']} ({v['availability']})": v["price"]
            for v in variants
            if v.get("price") is not None
        }

        products.append({
            "product_url": product_url,
            "product_name": name,
            "brand": brand,
            "model": model,
            "mpn": "",
            "sku": product_id,
            "breadcrumb": breadcrumb,
            "prices": json.dumps(prices, ensure_ascii=False),
            "input_url": input_url,
            "nav_page_url": nav_page_url,
            "status": "ok",
            "error_message": "",
        })
    return products


# ── Paginate one subcategory ──────────────────────────────────────────────────

async def _scrape_subcat(
    session: AsyncSession,
    subcat_url: str,
    seen: set[str],
    sem: asyncio.Semaphore | None = None,
) -> list[dict]:
    """Paginate a single subcategory URL and return unseen products.

    Fetches page 1 to determine last page, then fetches all pages in parallel,
    deduplicating on sku or product_url via the shared seen set.

    Args:
        session: An active ``curl_cffi`` async HTTP session.
        subcat_url: The base subcategory URL to scrape.
        seen: A mutable set of already-collected product keys shared across
            all subcategory calls for the same run, updated in place.

    Returns:
        A list of new (not yet seen) product dicts discovered during this
        subcategory scrape.
    """
    new_products: list[dict] = []
    last_page = await _get_last_page(session, subcat_url, sem=sem)
    log.info("  subcat %s — %d pages", subcat_url, last_page)

    page_urls = [f"{subcat_url.rstrip('/')}?p={page}" for page in range(1, last_page + 1)]
    html_results = await asyncio.gather(
        *[_fetch(session, url, _sem=sem) for url in page_urls],
        return_exceptions=True,
    )
    for url, html in zip(page_urls, html_results):
        if not isinstance(html, str):
            log.warning("  page FAILED — skipping: %s", url)
            continue
        for p in _parse_plp(html, subcat_url, nav_page_url=url):
            key = p["sku"] or p["product_url"]  # sku is now UUID from product-id
            if key and key not in seen:
                seen.add(key)
                new_products.append(p)

    log.info("  subcat done — %d new products (total seen: %d)", len(new_products), len(seen))
    return new_products


# ── Entry point ───────────────────────────────────────────────────────────────

async def run(input_url: str, run_id: str) -> list[dict]:
    """Orchestrate an IT-Market scrape and return all discovered products.

    If ``input_url`` is a specific subcategory URL, scrapes only that URL
    (no discovery). If ``input_url`` is the site base URL, performs full
    category discovery first.

    Args:
        input_url: Specific subcategory URL, or base URL for full discovery.
        run_id: Unique identifier for this scrape run.

    Returns:
        A list of product dicts with all ``CSV_FIELDS`` populated.

    Raises:
        RuntimeError: If a required page cannot be fetched.
    """
    from shared.http_client import make_dc_proxy, make_curl_session

    proxy = make_dc_proxy(sticky=True)
    seen: set[str] = set()
    all_products: list[dict] = []
    sem = asyncio.Semaphore(CONCURRENCY)

    async with make_curl_session(proxy) as session:
        # Direct URL — skip discovery entirely
        if input_url and input_url.rstrip("/") != BASE_URL.rstrip("/"):
            log.info("[%s] direct URL — skipping discovery: %s", run_id, input_url)
            subcats = [input_url]
        else:
            # Full discovery from home page
            log.info("[%s] base URL — running full discovery", run_id)
            html_home = await _fetch(session, BASE_URL + "/en/", _sem=sem)
            if not html_home:
                raise RuntimeError("Failed to fetch IT Market home page")
            top_cats = _extract_top_cats(html_home)
            cat_htmls = await asyncio.gather(
                *[_fetch(session, cat_url, _sem=sem) for cat_url in top_cats],
                return_exceptions=True,
            )
            subcats: list[str] = []
            for cat_url, cat_html in zip(top_cats, cat_htmls):
                if isinstance(cat_html, str):
                    subcats.extend(_extract_subcats(cat_html, cat_url))
            subcats = list(dict.fromkeys(subcats))
            log.info("[%s] discovery found %d subcategories", run_id, len(subcats))

        subcat_results = await asyncio.gather(
            *[_scrape_subcat(session, url, seen, sem=sem) for url in subcats],
            return_exceptions=True,
        )
        for result in subcat_results:
            if isinstance(result, list):
                all_products.extend(result)

    return all_products
