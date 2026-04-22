"""Tonitrus worker — PLP phase + PDP phase (curl_cffi, no browser for PDPs).

Two routes on the same service:
  POST /     — PLP: Camoufox paginates category, writes stubs, enqueues PDP tasks
  POST /pdp  — PDP: curl_cffi + session cookies, parse, update Firestore
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import asyncio
import json
import logging
import re
import traceback
from math import ceil

from camoufox.async_api import AsyncCamoufox
from curl_cffi.requests import AsyncSession
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from selectolax.parser import HTMLParser

from shared import config, firestore_client, notifications, tasks
from shared.http_client import camoufox_proxy, make_residential_proxy

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 50
MAX_RETRIES    = 3
BACKOFF_BASE   = 5

app = FastAPI()


# ── Camoufox navigation helper (PLP only) ────────────────────────────────────


async def _goto(page: object, url: str, attempt: int = 0) -> bool:
    logger.debug("_goto  attempt=%d  navigating  url=%s", attempt, url)
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=90_000)
        logger.debug("_goto  OK  url=%s", url)
        return True
    except Exception as exc:
        err_str = type(exc).__name__ + ": " + str(exc)[:120]
        logger.warning("_goto  attempt=%d  url=%s  err=%s", attempt, url, err_str)
        if "TargetClosedError" in type(exc).__name__ or "Target page" in str(exc):
            logger.warning("_goto  browser dead  url=%s", url)
            return False
        if attempt < MAX_RETRIES:
            await asyncio.sleep(BACKOFF_BASE * (2 ** attempt))
            return await _goto(page, url, attempt + 1)
        return False


def _page_url(cat_url: str, page_num: int) -> str:
    base = cat_url.split("?")[0].rstrip("/")
    return f"{base}_s{page_num}?lang=eng&af={ITEMS_PER_PAGE}"


# ── PLP parsing ───────────────────────────────────────────────────────────────


def _parse_total(html: str) -> int:
    tree = HTMLParser(html)
    el = tree.css_first("div.productlist-item-info")
    if el:
        m = re.search(r"(?:of|von)\s+([\d.,]+)", el.text(strip=True))
        if m:
            return int(m.group(1).replace(".", "").replace(",", ""))
    return 0


def _parse_plp_cards(html: str, cat_url: str) -> list[dict]:
    tree = HTMLParser(html)
    products = []
    for card in tree.css("div[itemprop='itemListElement']"):
        a_el = card.css_first("a[href]")
        if not a_el:
            continue
        href = a_el.attributes.get("href", "")
        product_url = href if href.startswith("http") else "https://www.tonitrus.com" + href
        m = re.search(r"/([^/?#]+)$", product_url)
        slug = m.group(1) if m else ""
        products.append({
            "product_code": slug,
            "product_url":  product_url,
            "input_url":    cat_url,
        })
    return products


def _parse_price(text: str) -> float | None:
    cleaned = re.sub(r"[^\d.,]", "", text).replace(",", ".")
    parts = cleaned.split(".")
    if len(parts) > 2:
        cleaned = "".join(parts[:-1]) + "." + parts[-1]
    try:
        return float(cleaned) if cleaned else None
    except ValueError:
        return None


# ── PDP HTML parsing (shared logic, browser-agnostic) ────────────────────────


def _parse_pdp_html(html: str, product_url: str) -> dict:
    tree = HTMLParser(html)

    h1_el = tree.css_first("h1.product-title, h1[itemprop='name'], h1")
    product_name = h1_el.text(strip=True) if h1_el else ""

    parts = [p.strip() for p in product_name.split(" - ")]
    brand = parts[0] if len(parts) > 0 else ""

    sku_el = tree.css_first("li.product-sku span[itemprop='sku']")
    sku    = sku_el.text(strip=True) if sku_el else ""

    crumbs: list[tuple[int, str]] = []
    for li in tree.css("li.breadcrumb-item[itemprop='itemListElement']"):
        pos_el  = li.css_first("meta[itemprop='position']")
        name_el = li.css_first("span[itemprop='name']")
        if not name_el:
            continue
        pos = int(pos_el.attributes.get("content", "99")) if pos_el else 99
        crumbs.append((pos, name_el.text(strip=True)))
    crumbs.sort(key=lambda x: x[0])
    model       = crumbs[-1][1] if crumbs else ""
    subcategory = " > ".join(c[1] for c in crumbs[1:-1])

    prices: dict[str, dict] = {}
    for row in tree.css("div.lpxBorderVar"):
        radio = row.css_first("input[type='radio']")
        if not radio:
            continue
        label_raw = radio.attributes.get("aria-label", "").upper()
        if label_raw in ("NEU", "NEW") or "NEW" in label_raw:
            cond = "NEW"
        elif "GENERAL" in label_raw or "REFURB" in label_raw:
            cond = "REFURBISHED"
        else:
            continue

        small_el    = row.css_first("small")
        var_sku     = small_el.text(strip=True).split(":")[-1].strip() if small_el else ""
        is_oos      = bool(row.css_first("span.badge-not-available, label[data-stock='out-of-stock']"))
        price_gross_el = row.css_first("span.lpxPDetailsPreis")
        price_gross    = price_gross_el.text(strip=True) if price_gross_el else None
        if price_gross and _parse_price(price_gross) == 0.0:
            price_gross = None
        price_net = None
        for small in row.css("small"):
            t = small.text(strip=True)
            if t.startswith("Net:"):
                price_net = t[4:].strip()
                break
        stock_el  = row.css_first("span.status")
        stock_raw = stock_el.text(strip=True) if stock_el else ""
        stock     = int(re.sub(r"[^\d]", "", stock_raw) or "0")
        prices[cond] = {
            "sku":         var_sku,
            "price_gross": price_gross,
            "price_net":   price_net,
            "stock":       stock,
            "status":      "OOS" if (is_oos or not price_gross) else "InStock",
        }

    def _is_live(p: dict) -> bool:
        return p.get("status") == "InStock" and p.get("price_gross") is not None

    primary_cond = next(
        (c for c in ("NEW", "REFURBISHED") if c in prices and _is_live(prices[c])),
        next(iter(prices), None),
    )
    primary = prices.get(primary_cond, {}) if primary_cond else {}

    logger.debug(
        "_parse_pdp_html  url=%s  h1=%s  lpx_rows=%d  prices=%s",
        product_url, product_name[:60], len(tree.css("div.lpxBorderVar")), list(prices.keys()),
    )

    return {
        "product_name":  product_name,
        "brand":         brand,
        "model":         model,
        "mpn":           "",
        "sku":           sku,
        "breadcrumb":    subcategory,
        "prices":        prices,
        "status":        "ok",
        "error_message": "",
    }


# ── HTTP PDP fetch (curl_cffi, no browser) ────────────────────────────────────


async def _scrape_pdp_http(product_url: str, cookie_str: str, ua: str, _attempt: int = 0) -> dict:
    pdp_url = product_url if "lang=" in product_url else product_url + "?lang=eng"
    proxy   = make_residential_proxy(sticky=False)  # fresh rotating IP each attempt
    headers = {
        "User-Agent":      ua,
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Cookie":          cookie_str,
        "Referer":         "https://www.tonitrus.com/",
    }
    try:
        async with AsyncSession(impersonate="firefox120", proxies=proxy) as s:
            r = await s.get(pdp_url, headers=headers, timeout=30)
        logger.debug(
            "_scrape_pdp_http  status=%d  size=%d  url=%s",
            r.status_code, len(r.text), pdp_url,
        )
        if r.status_code == 403 and _attempt < 2:
            logger.info("_scrape_pdp_http  403 retry %d  url=%s", _attempt + 1, pdp_url)
            await asyncio.sleep(1 + _attempt)
            return await _scrape_pdp_http(product_url, cookie_str, ua, _attempt + 1)
        if r.status_code != 200:
            return {"status": "failed", "error_message": f"http_{r.status_code}", "variants": "{}"}
        return _parse_pdp_html(r.text, pdp_url)
    except Exception as exc:
        err = type(exc).__name__ + ": " + str(exc)[:120]
        logger.warning("_scrape_pdp_http  FAILED  url=%s  err=%s", pdp_url, err)
        if _attempt < 2:
            await asyncio.sleep(2 ** _attempt)
            return await _scrape_pdp_http(product_url, cookie_str, ua, _attempt + 1)
        return {"status": "failed", "error_message": err, "variants": "{}"}


# ── PLP phase ─────────────────────────────────────────────────────────────────


async def _scrape_category_plp(cat_url: str) -> tuple[list[dict], str, str]:
    """Paginate PLP with Camoufox. Returns (products, cookie_str, ua)."""
    proxy = camoufox_proxy()
    all_products: list[dict] = []
    seen: set[str] = set()

    async with AsyncCamoufox(headless=True, geoip=True, proxy=proxy) as browser:
        page = await browser.new_page()

        # Visit base URL first to establish a proper session before paginating
        base_url = cat_url.split("?")[0] + "?lang=eng"
        logger.info("_scrape_category  cat=%s  warming up session", cat_url)
        await _goto(page, base_url)

        logger.info("_scrape_category  cat=%s  fetching page 1", cat_url)
        ok = await _goto(page, _page_url(cat_url, 1))
        if not ok:
            logger.warning("_scrape_category  cat=%s  page 1 nav failed", cat_url)
            await page.close()
            return [], "", ""

        html    = await page.content()
        total   = _parse_total(html)
        n_pages = ceil(total / ITEMS_PER_PAGE) if total > 0 else 1
        logger.info("_scrape_category  cat=%s  total=%d  pages=%d", cat_url, total, n_pages)

        total_raw = 0
        for pg in range(1, n_pages + 1):
            if pg > 1:
                logger.info("_scrape_category  cat=%s  fetching page %d/%d", cat_url, pg, n_pages)
                ok = await _goto(page, _page_url(cat_url, pg))
                if not ok:
                    logger.warning("_scrape_category  cat=%s  page %d nav failed — stopping", cat_url, pg)
                    break
                html = await page.content()
            cards = _parse_plp_cards(html, cat_url)
            total_raw += len(cards)
            added = 0
            nav_page_url = f"{cat_url.split('?')[0]}_s{pg}"
            for card in cards:
                key = card["product_url"]
                if key not in seen:
                    seen.add(key)
                    all_products.append({**card, "nav_page_url": nav_page_url})
                    added += 1
            logger.info(
                "_scrape_category  page=%d  cards=%d  added=%d  deduped=%d  running_total=%d",
                pg, len(cards), added, len(cards) - added, len(all_products),
            )

        # Capture session cookies + UA for curl_cffi PDP requests
        cookies    = await page.context.cookies()
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
        ua         = await page.evaluate("navigator.userAgent")
        await page.close()

    logger.info(
        "_scrape_category  PLP done  raw=%d  unique=%d  deduped=%d  cat=%s",
        total_raw, len(all_products), total_raw - len(all_products), cat_url,
    )
    return all_products, cookie_str, ua


# ── FastAPI handlers ──────────────────────────────────────────────────────────


@app.post("/")
async def handle(request: Request) -> JSONResponse:
    """PLP phase: paginate category, write stubs, enqueue one PDP task per product."""
    payload = await request.json()
    run_id  = payload["run_id"]
    cat_url = payload["cat_url"]
    cat_id  = payload["cat_id"]

    logger.info("Worker started  run_id=%s  cat_id=%s  cat_url=%s", run_id, cat_id, cat_url)

    # Idempotency gate: if PLP already completed for this cat_id, skip re-scrape.
    # This handles Cloud Tasks retries where PDP tasks are already running.
    existing = await firestore_client.tonitrus_get_pdp_counter(run_id, cat_id)
    if existing and existing.get("plp_done"):
        logger.info("PLP already done for cat_id=%s run_id=%s — skipping re-scrape", cat_id, run_id)
        return JSONResponse({"ok": True, "cat_id": cat_id, "skipped": True})

    # Phase 1: scrape + write stubs — safe to 500 here, nothing committed yet
    try:
        products, cookie_str, ua = await _scrape_category_plp(cat_url)
        if not products:
            raise RuntimeError("PLP returned 0 products")

        stubs = [{**p, "status": "pending", "error_message": ""} for p in products]
        await firestore_client.tonitrus_write_products(run_id, cat_id, stubs)
        logger.info("Stubs written  n=%d  cat_id=%s", len(stubs), cat_id)

    except Exception as exc:
        err_msg = traceback.format_exc()
        logger.error("PLP scrape/write failed  run_id=%s  cat_id=%s  err=%s", run_id, cat_id, err_msg)
        notifications.slack_notify(
            f":warning: *tonitrus* worker error (PLP)\nrun_id: `{run_id}`\n"
            f"cat: {cat_url}\n```{err_msg[:400]}```"
        )
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Phase 2: enqueue + counter + mark done — stubs already written; never return 500
    # A 500 here causes Cloud Tasks to retry PLP, forcing a full 25-page re-scrape.

    # Fix 3: enqueue first so we know the actual count before setting expected.
    pdp_url = config.TONITRUS_WORKER_URL.rstrip("/") + "/pdp"
    enqueued_count = len(products)  # optimistic default
    try:
        results = await asyncio.gather(*[
            tasks.enqueue(
                url=pdp_url,
                payload={
                    "run_id":       run_id,
                    "cat_id":       cat_id,
                    "product_url":  product["product_url"],
                    "product_code": product["product_code"],
                    "cookie_str":   cookie_str,
                    "ua":           ua,
                },
                task_id=f"{run_id}-{cat_id}-pdp-{i}",
                oidc_audience=config.TONITRUS_WORKER_URL,
            )
            for i, product in enumerate(products)
        ], return_exceptions=True)
        failures = [r for r in results if isinstance(r, Exception)]
        enqueued_count = len(products) - len(failures)
        if failures:
            logger.error("enqueue partial failures  n=%d/%d  run_id=%s  cat_id=%s  first=%s",
                         len(failures), len(products), run_id, cat_id, failures[0])
        logger.info("PDP tasks enqueued  n=%d  failures=%d  cat_id=%s  run_id=%s",
                    enqueued_count, len(failures), cat_id, run_id)
    except Exception as exc:
        logger.error("enqueue failed  run_id=%s  cat_id=%s  err=%s", run_id, cat_id, exc)

    # Fix 3: init counter with actual enqueued count, not total scraped.
    try:
        await firestore_client.tonitrus_init_pdp_counter(run_id, cat_id, enqueued_count)
    except Exception as exc:
        logger.error("init_pdp_counter failed  run_id=%s  cat_id=%s  err=%s", run_id, cat_id, exc)

    # Fix 6: retry mark_plp_done — failure leaves plp_done=False, causing unnecessary PLP re-scrape.
    for attempt in range(3):
        try:
            await firestore_client.tonitrus_mark_plp_done(run_id, cat_id)
            break
        except Exception as exc:
            if attempt == 2:
                logger.error("mark_plp_done failed after 3 attempts  run_id=%s  cat_id=%s  err=%s",
                             run_id, cat_id, exc)
            else:
                await asyncio.sleep(1)

    return JSONResponse({"ok": True, "cat_id": cat_id, "pdp_tasks": enqueued_count})


_PDP_MAX_ATTEMPTS = 5  # must match queue --max-attempts


async def _increment_and_maybe_merge(run_id: str, cat_id: str, product_url: str) -> None:
    """Increment PDP counter and trigger merge if all categories are done.

    Extracted so both the success path and the exhausted-retry path share the
    same logic without duplication.
    """
    pdp_done, pdp_expected = await firestore_client.tonitrus_increment_pdp_completed(run_id, cat_id)
    logger.info("PDP progress  cat_id=%s  %d/%d", cat_id, pdp_done, pdp_expected)

    if pdp_done >= pdp_expected:
        logger.info("Category PDP complete  cat_id=%s", cat_id)
        # Fix 5: increment + read expected in one atomic transaction.
        cats_done, cats_expected = await firestore_client.tonitrus_increment_completed(run_id)
        logger.info("Categories  %d/%d  run_id=%s", cats_done, cats_expected, run_id)

        if cats_expected > 0 and cats_done >= cats_expected:
            logger.info("All categories done — triggering merge  run_id=%s", run_id)
            await tasks.enqueue(
                url=config.TONITRUS_MERGE_URL,
                payload={"run_id": run_id},
                task_id=f"{run_id}-merge",
            )
            notifications.slack_notify(
                f":bar_chart: *tonitrus* all {cats_expected} categories done — merge triggered"
                f"\nrun_id: `{run_id}`"
            )


@app.post("/pdp")
async def handle_pdp(request: Request) -> JSONResponse:
    """PDP phase: curl_cffi fetch, parse, update Firestore, check completion."""
    payload      = await request.json()
    run_id       = payload["run_id"]
    cat_id       = payload["cat_id"]
    product_url  = payload["product_url"]
    product_code = payload["product_code"]
    cookie_str   = payload["cookie_str"]
    ua           = payload["ua"]

    # Fix 1+2: detect final attempt via Cloud Tasks retry header.
    # On exhaustion we mark the product as error, increment the counter, and
    # return 200 so the task does not retry again — "failed tasks count as done".
    retry_count = int(request.headers.get("X-CloudTasks-TaskRetryCount", "0"))
    is_final_attempt = retry_count >= _PDP_MAX_ATTEMPTS - 1

    logger.debug(
        "PDP task  run_id=%s  cat_id=%s  url=%s  retry=%d",
        run_id, cat_id, product_url.split("/")[-1], retry_count,
    )

    try:
        pdp = await _scrape_pdp_http(product_url, cookie_str, ua)

        pdp.setdefault("prices", {})

        await firestore_client.tonitrus_update_product(run_id, cat_id, product_code, pdp)
        logger.info(
            "PDP done  run_id=%s  cat_id=%s  url=%s  status=%s",
            run_id, cat_id, product_url.split("/")[-1], pdp.get("status"),
        )

        # Product data saved — counter is best-effort (must not 500, see comment below).
        try:
            await _increment_and_maybe_merge(run_id, cat_id, product_url)
        except Exception as counter_exc:
            logger.error(
                "PDP counter update failed (product saved — returning 200)  "
                "cat_id=%s  url=%s  err=%s",
                cat_id, product_url.split("/")[-1], counter_exc,
            )

        return JSONResponse({"ok": True})

    except Exception as exc:
        err_msg = traceback.format_exc()

        if is_final_attempt:
            # Fix 1+2: task exhausted retries — mark as error and count as done
            # so the run is not permanently stuck waiting for this product.
            logger.error(
                "PDP task EXHAUSTED retries  url=%s  retry=%d  err=%s",
                product_url, retry_count, err_msg[:300],
            )
            try:
                await firestore_client.tonitrus_update_product(
                    run_id, cat_id, product_code,
                    {"status": "error", "error_message": str(exc)[:500]},
                )
            except Exception:
                pass
            try:
                await _increment_and_maybe_merge(run_id, cat_id, product_url)
            except Exception as counter_exc:
                logger.error(
                    "counter update failed on exhausted PDP  url=%s  err=%s",
                    product_url, counter_exc,
                )
            return JSONResponse({"ok": False, "exhausted": True})

        logger.error("PDP task FAILED  url=%s  retry=%d  err=%s", product_url, retry_count, err_msg[:300])
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get("/health")
async def health() -> dict:
    return {"ok": True}
