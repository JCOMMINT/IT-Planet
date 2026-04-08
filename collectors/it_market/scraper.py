"""IT-Market.com scraper – 5-sort strategy, product_code dedup."""
from __future__ import annotations

import asyncio
import json
import random
import re

from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser

BASE_URL = "https://it-market.com"
MAX_PAGE_CAP = 415
MAX_RETRIES = 3
SORTS = ["name-asc", "name-desc", "price-asc", "price-desc", "topseller"]

CSV_FIELDS = [
    "product_name", "product_code", "product_id", "product_url",
    "breadcrumb", "category", "subcategory",
    "model", "description", "ean_upc", "brand",
    "variants",        # JSON string: [{variant_id, condition, price, stock, availability}]
    "input_url", "coverage_pct",
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

async def _fetch(session: AsyncSession, url: str, attempt: int = 0) -> str | None:
    """Fetch a URL with automatic retry on rate-limit and transient errors.

    Retries up to ``MAX_RETRIES`` times with exponential-ish back-off when
    the server responds with 429, 403, or 503, or when a network exception
    is raised.

    Args:
        session: An active ``curl_cffi`` async HTTP session.
        url: The URL to retrieve.
        attempt: Current retry attempt number (0-indexed). Used internally
            for recursion; callers should omit this.

    Returns:
        The response body as a string on HTTP 200, or ``None`` if the request
        ultimately fails after all retries.
    """
    try:
        r = await session.get(url, timeout=30)
        if r.status_code == 200:
            return r.text
        if r.status_code in (429, 403, 503) and attempt < MAX_RETRIES:
            delay = attempt * 4 + random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
            return await _fetch(session, url, attempt + 1)
        return None
    except Exception:
        if attempt < MAX_RETRIES:
            delay = attempt * 4 + random.uniform(0.5, 2.0)
            await asyncio.sleep(delay)
            return await _fetch(session, url, attempt + 1)
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


async def _get_last_page(session: AsyncSession, subcat_url: str, sort: str = "name-asc") -> int:
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
    html = await _fetch(session, _sort_url(subcat_url, sort, 1))
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


def _parse_plp(html: str, input_url: str) -> list[dict]:
    """Parse product listing page HTML into a list of product dicts.

    Iterates over every ``div.product-box`` card, extracting product identity
    fields, descriptive metadata, and variant information. Falls back to a
    single synthetic variant when no explicit variant options are present.
    Cards with neither a product code nor a product name are skipped.

    Args:
        html: Raw HTML string of the product listing page.
        input_url: The subcategory URL that produced this page, stored on
            each product record for traceability.

    Returns:
        A list of product dicts whose keys match ``CSV_FIELDS``. The
        ``variants`` value is a JSON string; ``coverage_pct`` is ``None``
        and should be filled in by the caller.
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
        code_inp = card.css_first("input[name='product-name']")
        product_code = code_inp.attributes.get("value", "") if code_inp else ""
        id_inp = card.css_first("input[name='product-id']")
        product_id = id_inp.attributes.get("value", "") if id_inp else ""

        # Description
        desc_el = card.css_first("div.product-description")
        description = desc_el.text(strip=True) if desc_el else ""

        # Model from meta or name
        model_el = card.css_first("span.product-model, div.product-number")
        model = model_el.text(strip=True) if model_el else ""

        # Brand
        brand_el = card.css_first("span.product-manufacturer-name, a.product-manufacturer")
        brand = brand_el.text(strip=True) if brand_el else ""

        # EAN
        ean_el = card.css_first("span.product-ean")
        ean_upc = ean_el.text(strip=True) if ean_el else ""

        # Variants
        variants = []
        for opt in card.css("div.product-detail-configurator-option"):
            cond_el = opt.css_first("div.maxia-variants-list-text")
            condition = cond_el.text(strip=True).split()[0] if cond_el else ""

            price_el = opt.css_first("div.product-variant-price")
            price = _parse_money(price_el.text(strip=True)) if price_el else None

            stock_el = opt.css_first("div.product-variant-stock")
            try:
                stock = int(re.search(r"\d+", stock_el.text(strip=True)).group()) if stock_el else None
            except (AttributeError, ValueError):
                stock = None

            variant_id = opt.attributes.get("data-product-id", "")

            # Availability via class
            avail_span = opt.css_first("span.product-variant-availability")
            if avail_span:
                cls = " ".join(avail_span.attributes.get("class", "").split())
                if "inStock" in cls:
                    availability = "In Stock"
                elif "withDelivery" in cls:
                    availability = "With Delivery"
                else:
                    availability = avail_span.text(strip=True)
            else:
                availability = ""

            variants.append({
                "variant_id": variant_id,
                "condition": condition,
                "price": price,
                "stock": stock,
                "availability": availability,
            })

        # Fallback single variant from card price
        if not variants:
            price_el = card.css_first("div.product-price span.price-unit-content")
            price = _parse_money(price_el.text(strip=True)) if price_el else None
            stock_el = card.css_first("div.delivery-badge")
            availability = stock_el.text(strip=True) if stock_el else ""
            variants.append({
                "variant_id": product_id,
                "condition": "New",
                "price": price,
                "stock": None,
                "availability": availability,
            })

        if not product_code and not name:
            continue

        products.append({
            "product_name": name,
            "product_code": product_code,
            "product_id": product_id,
            "product_url": product_url,
            "breadcrumb": "",
            "category": "",
            "subcategory": "",
            "model": model,
            "description": description[:500],
            "ean_upc": ean_upc,
            "brand": brand,
            "variants": json.dumps(variants),
            "input_url": input_url,
            "coverage_pct": None,
            "status": "ok",
            "error_message": "",
        })
    return products


# ── Multi-sort scrape ─────────────────────────────────────────────────────────

async def _scrape_subcat(
    session: AsyncSession,
    subcat_url: str,
    seen: set[str],
) -> list[dict]:
    """Scrape all 5 sort orders for one subcategory, deduplicating via a shared seen set.

    Iterates over ``SORTS``, fetches every page for each sort order, parses
    product cards, and adds only previously-unseen products (keyed on
    ``product_code`` or ``product_url``) to the result list.

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

    for sort in SORTS:
        last_page = await _get_last_page(session, subcat_url, sort)
        for page in range(1, last_page + 1):
            html = await _fetch(session, _sort_url(subcat_url, sort, page))
            if not html:
                continue
            for p in _parse_plp(html, subcat_url):
                key = p["product_code"] or p["product_url"]
                if key and key not in seen:
                    seen.add(key)
                    new_products.append(p)

    return new_products


# ── Entry point ───────────────────────────────────────────────────────────────

async def run(input_url: str, run_id: str) -> list[dict]:
    """Orchestrate a full IT-Market scrape and return all discovered products.

    Performs dynamic category discovery from the site's home page, then
    iterates over every subcategory applying the 5-sort deduplication
    strategy via ``_scrape_subcat``. If ``input_url`` is a specific
    subcategory URL it overrides discovery and only that URL is scraped.
    A ``coverage_pct`` of 100.0 is assigned to every product at the end.

    Args:
        input_url: A specific subcategory URL to scope the scrape to, or the
            site's base URL to trigger full discovery.
        run_id: Unique identifier for this scrape run, used for logging and
            upstream job tracking.

    Returns:
        A list of product dicts with all ``CSV_FIELDS`` populated.

    Raises:
        RuntimeError: If the IT Market home page cannot be fetched.
    """
    from shared.http_client import make_dc_proxy, make_curl_session

    proxy = make_dc_proxy(sticky=True)
    seen: set[str] = set()
    all_products: list[dict] = []

    async with make_curl_session(proxy) as session:
        # Dynamic category discovery
        html_home = await _fetch(session, BASE_URL + "/en/")
        if not html_home:
            raise RuntimeError("Failed to fetch IT Market home page")

        top_cats = _extract_top_cats(html_home)

        # Collect all subcategories
        subcats: list[str] = []
        for cat_url in top_cats:
            cat_html = await _fetch(session, cat_url)
            if cat_html:
                subs = _extract_subcats(cat_html, cat_url)
                subcats.extend(subs)

        # Deduplicate subcategory URLs
        subcats = list(dict.fromkeys(subcats))

        # If caller passed a specific subcat URL, use that only
        if input_url and input_url != BASE_URL:
            subcats = [input_url]

        # Probe each subcat and scrape
        for subcat_url in subcats:
            products = await _scrape_subcat(session, subcat_url, seen)
            all_products.extend(products)

    # Add coverage_pct per product (all products found = 100% per sort; approximation)
    total = len(all_products)
    for p in all_products:
        p["coverage_pct"] = 100.0 if total > 0 else 0.0

    return all_products
