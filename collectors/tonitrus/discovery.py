"""Tonitrus discovery job - scrapes category tree live via camoufox.

Writes leaf category URLs to Firestore, enqueues one Cloud Task per leaf.
"""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from camoufox.async_api import AsyncCamoufox
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from shared import config, firestore_client, notifications, tasks
from shared.http_client import camoufox_proxy

BASE_URL = "https://www.tonitrus.com"
NAV_URL = f"{BASE_URL}/?lang=eng"
MAX_RETRIES = 3
BACKOFF_BASE = 5  # seconds

app = FastAPI()

# ── Camoufox helpers ──────────────────────────────────────────────────────────


async def _goto(page: object, url: str, attempt: int = 0) -> bool:
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
            import asyncio

            await asyncio.sleep(BACKOFF_BASE * (2**attempt))
            return await _goto(page, url, attempt + 1)
        return False


async def _discover_leaf_categories(run_id: str, start_url: str) -> list[str]:
    """Return all leaf category URLs by walking the site's navigation tree.

    Opens a headless Camoufox browser and performs a breadth-first traversal
    starting from ``start_url``. A URL is considered a leaf when
    ``_extract_child_cat_urls`` returns no children for it.

    Args:
        run_id: Unique identifier for the current discovery run. Reserved for
            future logging or tracing use.
        start_url: URL to begin BFS traversal from. Defaults to NAV_URL if
            the caller passes the base domain.

    Returns:
        A list of fully qualified leaf category URLs with ``lang=eng``
        appended, in discovery order.
    """
    from selectolax.parser import HTMLParser

    proxy = camoufox_proxy()
    leaf_urls: list[str] = []
    visited: set[str] = set()
    # Ensure lang=eng on start URL
    if "lang=eng" not in start_url:
        start_url += ("&" if "?" in start_url else "?") + "lang=eng"

    logger.info("BFS discovery starting from %s", start_url)

    async with AsyncCamoufox(headless=True, geoip=True, proxy=proxy) as browser:
        page = await browser.new_page()

        # ── Fast-path: if start_url is already a leaf PLP, skip BFS ──────────
        ok = await _goto(page, start_url)
        if not ok:
            logger.warning("Failed to load start_url %s", start_url)
            return leaf_urls
        first_html = await page.content()
        if HTMLParser(first_html).css_first("div[itemprop='itemListElement']"):
            logger.info("start_url is a leaf PLP — skipping BFS: %s", start_url)
            await page.close()
            return [start_url]

        # ── Full BFS from homepage / category root ────────────────────────────
        queue: list[str] = [start_url]
        visited.add(start_url)
        child_urls = _extract_child_cat_urls(first_html, start_url)
        if child_urls:
            queue = child_urls
        else:
            leaf_urls.append(start_url)

        while queue:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            logger.info("BFS visiting %s (queue=%d visited=%d)", url, len(queue), len(visited))
            ok = await _goto(page, url)
            if not ok:
                logger.warning("Failed to load %s, skipping", url)
                continue

            html = await page.content()
            children = _extract_child_cat_urls(html, url)

            if not children:
                logger.info("Leaf found: %s", url)
                leaf_urls.append(url)
            else:
                logger.info("%d children found at %s", len(children), url)
                for child in children:
                    if child not in visited:
                        queue.append(child)

        await page.close()

    logger.info("BFS complete: %d leaf categories found", len(leaf_urls))
    return leaf_urls


def _extract_child_cat_urls(html: str, current_url: str) -> list[str]:
    """Extract child category links from the current page's nav or flyout HTML.

    Tries a prioritised list of CSS selectors (nav flyout, cms-navigation,
    category tree, etc.) and returns links from the first selector that
    yields results. Internal links that look like product pages (containing
    ``/product`` or ``.html``) are excluded. A ``lang=eng`` parameter is
    appended to every URL if not already present.

    Args:
        html: Raw HTML string of the current category page.
        current_url: The URL of the current page, used to skip self-referential
            links.

    Returns:
        A deduplicated list of absolute child category URLs.
    """
    from selectolax.parser import HTMLParser

    tree = HTMLParser(html)
    children: list[str] = []

    # a.categories-recursive-link are the PLP category links in the Tonitrus nav
    # (e.g. "Rack Server", "Switch", "HPE Storage"). The broader lpxcollapse
    # selector was returning 1000+ individual product model pages — wrong level.
    selectors = [
        "a.categories-recursive-link[href]",
    ]
    _skip = {
        "leistungen", "unternehmen", "kontakt", "Konfigurator",
        "impressum", "datenschutz", "sitemap", "newsletter",
        "remarketing", "logistik", "nachhaltigkeit", "standorte",
        "Configurator",
    }
    for sel in selectors:
        for a in tree.css(sel):
            href = a.attributes.get("href", "")
            if not href or href == "#" or href == current_url:
                continue
            if any(f in href for f in _skip):
                continue
            # Only follow internal category links (not product pages)
            if "tonitrus.com" in href or href.startswith("/"):
                if "/product" not in href and ".html" not in href:
                    full = href if href.startswith("http") else BASE_URL + href
                    if "lang=eng" not in full:
                        full += ("&" if "?" in full else "?") + "lang=eng"
                    children.append(full)
        if children:
            break

    return list(dict.fromkeys(children))


# ── FastAPI handler ───────────────────────────────────────────────────────────


@app.post("/")
async def handle(request: Request) -> JSONResponse:
    """Handle a Cloud Tasks invocation to discover Tonitrus leaf categories.

    Reads ``run_id`` and optional ``input_url`` from the JSON body, runs
    ``_discover_leaf_categories``, stores the expected worker count in
    Firestore, and enqueues one Cloud Task per leaf category URL. Sends
    Slack notifications on completion and error.

    Args:
        request: The incoming FastAPI ``Request`` object whose body must
            contain ``run_id`` (str) and optionally ``input_url`` (str,
            defaults to ``NAV_URL``).

    Returns:
        A ``JSONResponse`` with ``{"ok": True, "leaf_count": <int>}`` on
        success, or ``{"ok": False, "error": <str>}`` with HTTP 500 on
        failure.

    Raises:
        RuntimeError: If discovery returns zero leaf categories.
    """
    payload = await request.json()
    run_id: str = payload["run_id"]
    input_url: str = payload.get("input_url", NAV_URL)

    logger.info("Discovery started run_id=%s input_url=%s", run_id, input_url)
    await firestore_client.update_job(run_id, status="discovering")
    notifications.notify_start("tonitrus", run_id, input_url)

    try:
        leaf_urls = await _discover_leaf_categories(run_id, input_url)
        if not leaf_urls:
            raise RuntimeError("Discovery returned 0 leaf categories")

        expected_count = len(leaf_urls)
        logger.info("Discovery found %d leaf categories run_id=%s", expected_count, run_id)
        await firestore_client.tonitrus_set_expected(run_id, expected_count)
        await firestore_client.update_job(run_id, status="running")

        # Enqueue one Cloud Task per leaf category
        worker_url = config.TONITRUS_WORKER_URL
        for idx, cat_url in enumerate(leaf_urls):
            cat_id = f"cat_{idx:04d}"
            logger.info("Enqueuing task %s for %s", cat_id, cat_url)
            await tasks.enqueue(
                url=worker_url,
                payload={
                    "run_id": run_id,
                    "cat_url": cat_url,
                    "cat_id": cat_id,
                },
                task_id=f"{run_id}-{cat_id}",
            )

        notifications.slack_notify(
            f":mag: *tonitrus* discovery complete - {expected_count} categories queued"
            f"\nrun_id: `{run_id}`"
        )
        return JSONResponse({"ok": True, "leaf_count": expected_count})

    except Exception as exc:
        err_msg = traceback.format_exc()
        await firestore_client.update_job(run_id, status="failed", error=str(exc))
        notifications.notify_error("tonitrus", run_id, err_msg)
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get("/health")
async def health() -> dict:
    """Return a liveness check payload.

    Returns:
        A dict ``{"ok": True}`` indicating the service is alive.
    """
    return {"ok": True}
