"""IT-Resell.com scraper — Shopware 6, curl_cffi + selectolax.

Scrapes a single subcategory URL (input_url). Fetches all PLP pages in
parallel, then fetches each PDP. Phase 2b derives the alternate condition URL
(.1 ↔ .2 suffix) and augments the primary row's prices dict and sku field.
POR products (no price meta) skip Phase 2b entirely.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from urllib.parse import urlparse

from curl_cffi.requests import AsyncSession
from selectolax.parser import HTMLParser

logger = logging.getLogger(__name__)

BASE_URL        = "https://www.it-resell.com"
MAX_RETRIES     = 3
PLP_CONCURRENCY = 20
PDP_CONCURRENCY = int(os.getenv("SCRAPER_CONCURRENCY", "5"))

CONDITION_MAP = {
    "neu":         "NEW",
    "new":         "NEW",         # Google Translate fallback
    "refurbished": "REFURBISHED",
}

CSV_FIELDS = [
    "product_url", "product_name", "brand", "model", "mpn",
    "sku", "ean", "breadcrumb", "prices",
    "input_url", "nav_page_url", "status", "error_message",
]


# ── URL helpers ───────────────────────────────────────────────────────────────

def _plp_url(base: str, page: int) -> str:
    return f"{base.rstrip('/')}/?p={page}"


def _build_breadcrumb_prefix(input_url: str) -> str:
    path = urlparse(input_url).path
    skip = {"collection", ""}
    parts = [
        p.replace("-", " ").title()
        for p in path.split("/")
        if p.lower() not in skip
    ]
    return " > ".join(parts)


# ── PLP parsers ───────────────────────────────────────────────────────────────

def _parse_last_page(html: str) -> int:
    tree = HTMLParser(html)
    last = 1
    for a in tree.css("a[href]"):
        href = a.attributes.get("href", "")
        m = re.search(r"[?&]p=(\d+)", href)
        if m:
            last = max(last, int(m.group(1)))
    return last


def _parse_plp_cards(html: str, nav_url: str) -> list[dict]:
    tree = HTMLParser(html)
    seen: set[str] = set()
    cards: list[dict] = []
    for a in tree.css("a[href]"):
        href = a.attributes.get("href", "")
        if "/product/" not in href:
            continue
        url = href if href.startswith("http") else BASE_URL + href
        url = url.split("?")[0].split("#")[0]
        if url not in seen:
            seen.add(url)
            cards.append({"product_url": url, "nav_page_url": nav_url})
    return cards


# ── PDP parser ────────────────────────────────────────────────────────────────

def _parse_price(text: str) -> float | None:
    cleaned = text.strip().replace(".", "").replace(",", ".")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


def _derive_alt_url(current_url: str) -> str | None:
    m = re.match(r'^(https://www\.it-resell\.com/product/.+)\.([12])$', current_url)
    if m:
        alt_suffix = "1" if m.group(2) == "2" else "2"
        return f"{m.group(1)}.{alt_suffix}"
    return None


def _parse_pdp(html: str, product_url: str, nav_page_url: str, input_url: str) -> dict:
    tree = HTMLParser(html)

    h1 = tree.css_first("h1.product-detail-name")
    product_name = h1.text(strip=True) if h1 else ""

    brand_inp = tree.css_first("input[name='brand-name']")
    brand = brand_inp.attributes.get("value", "").strip() if brand_inp else ""
    if not brand:
        mfr_link = tree.css_first("span.product-detail-manufacturer-name a")
        brand = mfr_link.text(strip=True) if mfr_link else ""

    model_el = tree.css_first("span.product-detail-manufacturer-number")
    model = model_el.text(strip=True) if model_el else ""

    mpn_meta = tree.css_first("meta[itemprop='mpn']")
    mpn = mpn_meta.attributes.get("content", "").strip() if mpn_meta else model

    sku_el = tree.css_first("span.product-detail-ordernumber[itemprop='sku']")
    sku = sku_el.text(strip=True) if sku_el else ""

    ean_meta = tree.css_first("meta[itemprop='gtin13']")
    ean = ean_meta.attributes.get("content", "").strip() if ean_meta else ""
    # Normalize: strip float representation (.0) if HTML returns it
    if ean and "." in ean:
        try:
            ean = str(int(float(ean)))
        except ValueError:
            pass

    condition = ""
    checked_radio = tree.css_first(
        "input.product-detail-configurator-option-input[checked]"
    )
    if checked_radio:
        radio_id = checked_radio.attributes.get("id", "")
        label = tree.css_first(f"label[for='{radio_id}']")
        if label:
            raw = label.attributes.get("title", label.text(strip=True)).lower().strip()
            condition = CONDITION_MAP.get(raw, raw.upper())

    price_meta = tree.css_first("meta[itemprop='price']")
    price_raw  = price_meta.attributes.get("content", "") if price_meta else ""
    price_val: float | None = None
    if price_raw:
        try:
            price_val = float(price_raw)
        except ValueError:
            price_val = _parse_price(price_raw)

    prices: dict[str, float] = {}
    if condition and price_val and price_val > 0:
        prices[condition] = price_val

    alt_url: str | None = None
    if prices:
        for inp in tree.css("input.product-detail-configurator-option-input"):
            if inp.attributes.get("checked"):
                continue
            cls = inp.attributes.get("class", "")
            if "not-combinable" not in cls:
                alt_url = _derive_alt_url(product_url)
            break

    prefix = _build_breadcrumb_prefix(input_url)
    breadcrumb = f"{prefix} > {product_name}" if prefix else product_name

    return {
        "product_url":   product_url,
        "product_name":  product_name,
        "brand":         brand,
        "model":         model,
        "mpn":           mpn,
        "sku":           sku,
        "ean":           ean,
        "breadcrumb":    breadcrumb,
        "prices":        prices if prices else "POR",
        "input_url":     input_url,
        "nav_page_url":  nav_page_url,
        "status":        "ok",
        "error_message": "",
        "_alt_url":      alt_url,
    }


# ── Fetch + PDP scraper ───────────────────────────────────────────────────────

async def _fetch(session: AsyncSession, url: str, attempt: int = 0) -> str | None:
    import random
    try:
        r = await session.get(url, timeout=30)
        if r.status_code == 200:
            return r.text
        if r.status_code in (429, 403, 503) and attempt < MAX_RETRIES:
            delay = attempt * 4 + random.uniform(1.0, 3.0)
            logger.warning("HTTP %d on %s — retry %d in %.1fs", r.status_code, url, attempt + 1, delay)
            await asyncio.sleep(delay)
            return await _fetch(session, url, attempt + 1)
        logger.error("HTTP %d on %s — giving up", r.status_code, url)
        return None
    except Exception as exc:
        if attempt < MAX_RETRIES:
            delay = attempt * 4 + random.uniform(1.0, 3.0)
            logger.warning("Exception on %s: %s — retry %d", url, exc, attempt + 1)
            await asyncio.sleep(delay)
            return await _fetch(session, url, attempt + 1)
        logger.error("Exception on %s after %d attempts: %s", url, MAX_RETRIES, exc)
        return None


def _failed_row(product_url: str, nav_page_url: str, input_url: str, reason: str) -> dict:
    return {
        "product_url":   product_url,
        "product_name":  "", "brand": "", "model": "",
        "mpn": "", "sku": "", "ean": "", "breadcrumb": "",
        "prices":        {},
        "input_url":     input_url,
        "nav_page_url":  nav_page_url,
        "status":        "failed",
        "error_message": reason,
        "_alt_url":      None,
    }


async def _scrape_pdp(
    session: AsyncSession,
    sem: asyncio.Semaphore,
    product_url: str,
    nav_page_url: str,
    input_url: str,
) -> dict:
    async with sem:
        try:
            html = await _fetch(session, product_url)
            if not html:
                return _failed_row(product_url, nav_page_url, input_url, "fetch_failed")
            return _parse_pdp(html, product_url, nav_page_url, input_url)
        except Exception as exc:
            return _failed_row(product_url, nav_page_url, input_url,
                               f"{type(exc).__name__}: {exc}")


async def _fetch_plp_page(
    session: AsyncSession,
    sem: asyncio.Semaphore,
    page: int,
    input_url: str,
) -> tuple[str | None, str]:
    nav_url = _plp_url(input_url, page)
    async with sem:
        html = await _fetch(session, nav_url)
    return html, nav_url


# ── Entry point ───────────────────────────────────────────────────────────────

async def run(input_url: str, run_id: str) -> list[dict]:
    """Scrape one subcategory URL. Returns list of 13-column row dicts.

    Phase 1  — PLP: page 1 sequential, pages 2..N parallel (plp_sem=20)
    Phase 2a — PDP primary: all PLP-collected URLs → one row each
    Phase 2b — PDP secondary: fetch alt condition URL, augment existing row
               (prices dict updated, sku appended). No new rows.
    """
    from shared.http_client import make_dc_proxy, make_curl_session

    logger.info("run started run_id=%s input_url=%s", run_id, input_url)

    proxy   = make_dc_proxy()
    pdp_sem = asyncio.Semaphore(PDP_CONCURRENCY)
    plp_sem = asyncio.Semaphore(PLP_CONCURRENCY)

    async with make_curl_session(proxy) as session:

        # ── Phase 1: PLP ──────────────────────────────────────────────────────
        logger.info("[PLP] page 1 url=%s", input_url)
        html_p1 = await _fetch(session, _plp_url(input_url, 1))
        if not html_p1:
            raise RuntimeError(f"Failed to fetch PLP page 1 for {input_url}")

        last_page = _parse_last_page(html_p1)
        logger.info("[PLP] last_page=%d", last_page)

        all_cards: list[dict] = []
        seen_urls: set[str]   = set()

        def _add_cards(html: str, nav_url: str) -> None:
            for c in _parse_plp_cards(html, nav_url):
                if c["product_url"] not in seen_urls:
                    seen_urls.add(c["product_url"])
                    all_cards.append(c)

        _add_cards(html_p1, _plp_url(input_url, 1))

        if last_page > 1:
            logger.info("[PLP] pages 2..%d parallel concurrency=%d", last_page, PLP_CONCURRENCY)
            page_results = await asyncio.gather(
                *[_fetch_plp_page(session, plp_sem, p, input_url)
                  for p in range(2, last_page + 1)],
                return_exceptions=True,
            )
            for res in page_results:
                if isinstance(res, Exception):
                    logger.warning("[PLP] exception: %s", res)
                    continue
                html, nav_url = res
                if html:
                    _add_cards(html, nav_url)

        logger.info("[PLP] product URLs collected: %d", len(all_cards))

        # ── Phase 2a: PDP primary ──────────────────────────────────────────────
        logger.info("[PDP-2a] %d requests concurrency=%d", len(all_cards), PDP_CONCURRENCY)
        results_2a = await asyncio.gather(
            *[_scrape_pdp(session, pdp_sem, c["product_url"], c["nav_page_url"], input_url)
              for c in all_cards],
            return_exceptions=True,
        )

        plp_url_set: set[str] = {c["product_url"] for c in all_cards}
        rows: list[dict]      = []

        for i, r in enumerate(results_2a):
            if isinstance(r, Exception):
                card = all_cards[i]
                rows.append(_failed_row(card["product_url"], card["nav_page_url"],
                                        input_url, f"{type(r).__name__}: {r}"))
            else:
                rows.append(r)

        # ── Phase 2b: alt condition fetch — augments existing row ──────────────
        alt_to_idx: dict[str, int] = {}
        sec_seen:   set[str]       = set()
        secondary:  list[str]      = []

        for idx, row in enumerate(rows):
            alt = row.get("_alt_url")
            if alt and alt not in plp_url_set and alt not in sec_seen:
                sec_seen.add(alt)
                alt_to_idx[alt] = idx
                secondary.append(alt)

        if secondary:
            logger.info("[PDP-2b] %d alt-condition fetches", len(secondary))
            nav_url_for = {alt: rows[alt_to_idx[alt]]["nav_page_url"] for alt in secondary}
            results_2b = await asyncio.gather(
                *[_scrape_pdp(session, pdp_sem, alt, nav_url_for[alt], input_url)
                  for alt in secondary],
                return_exceptions=True,
            )
            for j, r in enumerate(results_2b):
                if isinstance(r, Exception):
                    logger.warning("[PDP-2b] failed %s: %s", secondary[j], r)
                    continue
                alt_prices = r.get("prices", {})
                alt_sku    = r.get("sku", "")
                primary    = rows[alt_to_idx[secondary[j]]]
                if isinstance(alt_prices, dict) and alt_prices:
                    primary["prices"].update(alt_prices)
                if alt_sku and alt_sku not in primary["sku"]:
                    primary["sku"] = f"{primary['sku']} / {alt_sku}"
        else:
            logger.info("[PDP-2b] skipped — PLP already listed both conditions")

    # ── Finalise ──────────────────────────────────────────────────────────────
    for row in rows:
        row.pop("_alt_url", None)
        row["prices"] = json.dumps(row["prices"]) if isinstance(row["prices"], dict) else row["prices"]

    ok_count = sum(1 for r in rows if r.get("status") == "ok")
    logger.info("[DONE] run_id=%s total=%d ok=%d failed=%d",
                run_id, len(rows), ok_count, len(rows) - ok_count)
    return rows
