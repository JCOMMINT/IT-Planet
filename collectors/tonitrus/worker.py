"""Tonitrus worker – scrapes one leaf category (PLPs + PDPs for CTO).
Writes products to Firestore. Last worker triggers merge Cloud Task.
"""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import asyncio
import json
import re
import traceback
from math import ceil

from camoufox.async_api import AsyncCamoufox
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from selectolax.parser import HTMLParser

from shared import config, firestore_client, notifications, tasks
from shared.http_client import camoufox_proxy

ITEMS_PER_PAGE = 50
MAX_RETRIES = 3
BACKOFF_BASE = 5

app = FastAPI()


# ── Camoufox helpers ──────────────────────────────────────────────────────────

async def _goto(page, url: str, attempt: int = 0) -> bool:
    """Navigate a Camoufox page to ``url`` with retry on failure.

    Waits for the ``"domcontentloaded"`` event with a 90-second timeout.
    On exception, retries up to ``MAX_RETRIES`` times using exponential
    back-off based on ``BACKOFF_BASE``.

    Args:
        page: An active Camoufox / Playwright ``Page`` instance.
        url: The URL to navigate to.
        attempt: Current retry attempt number (0-indexed). Used internally
            for recursion; callers should omit this.

    Returns:
        ``True`` if navigation succeeded, ``False`` after all retries are
        exhausted.
    """
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=90_000)
        return True
    except Exception:
        if attempt < MAX_RETRIES:
            await asyncio.sleep(BACKOFF_BASE * (2 ** attempt))
            return await _goto(page, url, attempt + 1)
        return False


def _page_url(cat_url: str, page_num: int) -> str:
    """Build a paginated URL for a Tonitrus category listing page.

    Tonitrus pagination appends ``_s{page}`` to the base path and uses
    ``af`` to control items-per-page (fixed at ``ITEMS_PER_PAGE``).

    Args:
        cat_url: The base category URL (may include a query string, which is
            stripped before constructing the paginated URL).
        page_num: The 1-based page number to request.

    Returns:
        A fully constructed URL of the form
        ``{base}_s{page_num}?lang=eng&af={ITEMS_PER_PAGE}``.
    """
    base = cat_url.split("?")[0].rstrip("/")
    return f"{base}_s{page_num}?lang=eng&af={ITEMS_PER_PAGE}"


# ── PLP parsing ───────────────────────────────────────────────────────────────

def _parse_total(html: str) -> int:
    """Parse the total product count from a Tonitrus PLP page.

    Looks for a ``div.productlist-item-info`` element whose text contains
    a phrase like ``"of 1,234"``.

    Args:
        html: Raw HTML string of the product listing page.

    Returns:
        Total number of products in the category as an integer, or ``0``
        if the count element cannot be found or parsed.
    """
    tree = HTMLParser(html)
    el = tree.css_first("div.productlist-item-info")
    if el:
        m = re.search(r"of\s+([\d,]+)", el.text(strip=True))
        if m:
            return int(m.group(1).replace(",", ""))
    return 0


def _parse_plp_cards(html: str, cat_url: str) -> list[dict]:
    """Parse product cards from a Tonitrus product listing page.

    Iterates over ``div.product-thumbnail``, ``article.product-box``, and
    ``div.cms-listing-col`` elements. Product code is derived from a
    dedicated element or, as a fallback, from the trailing URL slug.

    Args:
        html: Raw HTML string of the product listing page.
        cat_url: The category URL that produced this page, stored on each
            product record as ``input_url``.

    Returns:
        A list of partial product dicts. Fields not available on the PLP
        (e.g. ``description``, ``ean_upc``) are set to empty strings. The
        ``is_cto`` field is ``True`` when a CTO indicator element is found.
    """
    tree = HTMLParser(html)
    products = []
    for card in tree.css("div.product-thumbnail, article.product-box, div.cms-listing-col"):
        a_el = card.css_first("a[href*='/']")
        if not a_el:
            continue
        href = a_el.attributes.get("href", "")
        product_url = href if href.startswith("http") else "https://www.tonitrus.com" + href

        name_el = card.css_first("a.product-name, span.product-name, h2.product-name")
        name = name_el.text(strip=True) if name_el else ""

        code_el = card.css_first("span.product-code, div.product-code, input[name='product-id']")
        product_code = (
            code_el.text(strip=True) if code_el and code_el.tag != "input"
            else code_el.attributes.get("value", "") if code_el
            else ""
        )
        if not product_code:
            # Derive from URL slug
            m = re.search(r"/([^/?#]+)$", product_url)
            product_code = m.group(1) if m else ""

        price_el = card.css_first(".price.h1, span.price, div.product-price")
        price_raw = price_el.text(strip=True) if price_el else ""
        price = _parse_price(price_raw)

        brand_el = card.css_first("span.manufacturer-name, a.product-manufacturer")
        brand = brand_el.text(strip=True) if brand_el else ""

        avail_el = card.css_first("span.delivery-status, div.product-badge")
        availability = avail_el.text(strip=True) if avail_el else ""

        # CTO detection
        is_cto = bool(card.css_first("span.is-cto, div.cto-badge, [data-cto='true']"))

        products.append({
            "product_name": name,
            "product_code": product_code,
            "product_url": product_url,
            "category": "",
            "breadcrumb": "",
            "description": "",
            "ean_upc": "",
            "brand": brand,
            "price": price,
            "condition": "New",
            "stock": None,
            "availability": availability,
            "variants": "[]",
            "input_url": cat_url,
            "is_cto": is_cto,
        })
    return products


def _parse_price(text: str) -> float | None:
    """Parse a price string into a float, handling European number formats.

    Strips non-numeric characters, normalises comma decimal separators, and
    collapses ambiguous multi-dot strings (e.g. ``"1.234.56"`` → ``1234.56``).

    Args:
        text: Raw price text such as ``"€1.234,56"`` or ``"1,099.00"``.

    Returns:
        The parsed price as a float, or ``None`` if the string is empty or
        cannot be converted.
    """
    cleaned = re.sub(r"[^\d.,]", "", text).replace(",", ".")
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


# ── PDP parsing for CTO products ──────────────────────────────────────────────

async def _scrape_cto_pdp(page, product_url: str) -> dict:
    """Scrape CTO product: click each variant swatch, capture price per variant."""
    ok = await _goto(page, product_url)
    if not ok:
        return {"variants": "[]", "status": "failed", "error_message": "pdp_fetch_failed"}

    html = await page.content()
    tree = HTMLParser(html)

    # Static fields from PDP
    ean_el = tree.css_first("span.product-code-content, meta[itemprop='gtin']")
    ean_upc = ean_el.text(strip=True) if ean_el else (ean_el.attributes.get("content", "") if ean_el else "")
    desc_el = tree.css_first("div.product-description p, div.cms-block-text p")
    description = desc_el.text(strip=True)[:500] if desc_el else ""

    variants = []
    swatch_els = await page.query_selector_all("label.variation.swatches-text")

    if swatch_els:
        for swatch in swatch_els:
            try:
                # Get current price before click
                price_el = await page.query_selector(".price.h1")
                prev_price = await price_el.inner_text() if price_el else ""

                await swatch.click()
                # Wait for price to update
                try:
                    await page.wait_for_function(
                        f"document.querySelector('.price.h1')?.innerText !== {json.dumps(prev_price)}",
                        timeout=8_000,
                    )
                except Exception:
                    pass  # Price may not change for this variant

                price_el = await page.query_selector(".price.h1")
                price_text = await price_el.inner_text() if price_el else ""
                price = _parse_price(price_text)

                label_text = await swatch.inner_text()
                variants.append({
                    "variant_name": label_text.strip(),
                    "price": price,
                    "availability": "",
                    "stock": None,
                })
            except Exception:
                continue
    else:
        # Non-CTO: single price from page
        price_el = await page.query_selector(".price.h1")
        price_text = await price_el.inner_text() if price_el else ""
        variants.append({"variant_name": "Standard", "price": _parse_price(price_text)})

    return {
        "ean_upc": ean_upc,
        "description": description,
        "variants": json.dumps(variants),
        "status": "ok",
        "error_message": "",
    }


# ── Main category scrape ──────────────────────────────────────────────────────

async def _scrape_category(cat_url: str, cat_id: str, run_id: str) -> list[dict]:
    """Scrape all products from a single Tonitrus leaf category.

    Opens a headless Camoufox browser, paginates through every PLP page,
    deduplicates by product code or URL, and follows up with a full PDP
    scrape for any CTO-flagged products.

    Args:
        cat_url: The leaf category URL to scrape.
        cat_id: A short identifier for this category (e.g. ``"cat_0003"``),
            used for logging.
        run_id: Unique identifier for the parent scrape run.

    Returns:
        A list of product dicts with all fields populated. CTO products have
        additional ``ean_upc``, ``description``, and ``variants`` data merged
        in from their PDP.
    """
    proxy = camoufox_proxy()
    all_products: list[dict] = []
    seen: set[str] = set()

    async with AsyncCamoufox(headless=True, geoip=True, proxy=proxy) as browser:
        page = await browser.new_page()

        # Get total products from page 1
        ok = await _goto(page, _page_url(cat_url, 1))
        if not ok:
            await page.close()
            return []

        html = await page.content()
        total = _parse_total(html)
        n_pages = ceil(total / ITEMS_PER_PAGE) if total > 0 else 1

        # Scrape PLPs
        for pg in range(1, n_pages + 1):
            if pg > 1:
                ok = await _goto(page, _page_url(cat_url, pg))
                if not ok:
                    break
                html = await page.content()

            cards = _parse_plp_cards(html, cat_url)
            for card in cards:
                key = card["product_code"] or card["product_url"]
                if key not in seen:
                    seen.add(key)
                    all_products.append(card)

        # Fetch PDPs for CTO products
        for idx, product in enumerate(all_products):
            if not product.get("is_cto"):
                continue
            pdp_data = await _scrape_cto_pdp(page, product["product_url"])
            all_products[idx].update(pdp_data)

        await page.close()

    return all_products


# ── FastAPI handler ───────────────────────────────────────────────────────────

@app.post("/")
async def handle(request: Request):
    """Handle a Cloud Tasks invocation to scrape one Tonitrus leaf category.

    Reads ``run_id``, ``cat_url``, and ``cat_id`` from the JSON body, runs
    ``_scrape_category``, writes products to Firestore, and atomically
    increments the completed-category counter. If all expected categories
    are done, enqueues the merge Cloud Task and sends a Slack notification.

    Args:
        request: The incoming FastAPI ``Request`` object whose body must
            contain ``run_id`` (str), ``cat_url`` (str), and ``cat_id`` (str).

    Returns:
        A ``JSONResponse`` with ``{"ok": True, "cat_id": <str>, "products": <int>}``
        on success, or ``{"ok": False, "error": <str>}`` with HTTP 500 on
        failure.
    """
    payload = await request.json()
    run_id: str = payload["run_id"]
    cat_url: str = payload["cat_url"]
    cat_id: str = payload["cat_id"]

    try:
        products = await _scrape_category(cat_url, cat_id, run_id)

        # Ensure all rows have required fields
        for p in products:
            p.setdefault("status", "ok")
            p.setdefault("error_message", "")

        await firestore_client.tonitrus_write_products(run_id, cat_id, products)

        # Atomic increment and check
        completed, expected = await _atomic_increment_and_check(run_id)

        if expected > 0 and completed >= expected:
            # Last worker: enqueue merge task
            await tasks.enqueue(
                url=config.TONITRUS_MERGE_URL,
                payload={"run_id": run_id},
                task_id=f"{run_id}-merge",
            )
            notifications.slack_notify(
                f":bar_chart: *tonitrus* all {expected} categories done – merge triggered\nrun_id: `{run_id}`"
            )

        return JSONResponse({"ok": True, "cat_id": cat_id, "products": len(products)})

    except Exception as exc:
        err_msg = traceback.format_exc()
        notifications.slack_notify(
            f":warning: *tonitrus* worker error\nrun_id: `{run_id}`\ncat: {cat_url}\n```{err_msg[:400]}```"
        )
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def _atomic_increment_and_check(run_id: str) -> tuple[int, int]:
    """Increment the completed-category counter and read the expected total.

    Calls Firestore to atomically increment the completed count for the run,
    then fetches the current completed and expected counts.

    Args:
        run_id: Unique identifier for the scrape run.

    Returns:
        A tuple of ``(completed, expected)`` where ``completed`` is the
        newly incremented count and ``expected`` is the total number of
        categories that need to finish before the merge step is triggered.
    """
    new_count = await firestore_client.tonitrus_increment_completed(run_id)
    _, expected = await firestore_client.tonitrus_get_counts(run_id)
    return new_count, expected


@app.get("/health")
async def health():
    """Return a liveness check payload.

    Returns:
        A dict ``{"ok": True}`` indicating the service is alive.
    """
    return {"ok": True}
