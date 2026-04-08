"""Tonitrus merge job - reads all products from Firestore, writes CSV to GCS."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import traceback

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from shared import firestore_client, gcs_client, notifications

app = FastAPI()

CSV_FIELDS = [
    "product_name",
    "product_code",
    "product_url",
    "category",
    "breadcrumb",
    "description",
    "ean_upc",
    "brand",
    "price",
    "condition",
    "stock",
    "availability",
    "variants",
    "input_url",
    "is_cto",
    "status",
    "error_message",
]


@app.post("/")
async def handle(request: Request) -> JSONResponse:
    """Handle a Cloud Tasks invocation to merge and export Tonitrus products.

    Reads all per-category product documents from Firestore, performs a
    final deduplication pass keyed on ``product_code`` (falling back to
    ``product_url``), uploads the result as a CSV to GCS, and updates the
    Firestore job record to ``"complete"``. Sends a Slack notification via
    ``notifications.notify_complete`` on success and
    ``notifications.notify_error`` on failure.

    Args:
        request: The incoming FastAPI ``Request`` object whose body must
            contain ``run_id`` (str).

    Returns:
        A ``JSONResponse`` with ``{"ok": True, "rows": <int>}`` on success,
        or ``{"ok": False, "error": <str>}`` with HTTP 500 on failure.
    """
    payload = await request.json()
    run_id: str = payload["run_id"]

    try:
        products = await firestore_client.tonitrus_read_all_products(run_id)

        # Final dedup pass on product_code
        seen: set[str] = set()
        deduped: list[dict] = []
        for p in products:
            key = p.get("product_code") or p.get("product_url", "")
            if key not in seen:
                seen.add(key)
                deduped.append(p)

        gcs_uri = gcs_client.upload_csv(run_id, "tonitrus", deduped, CSV_FIELDS)
        await firestore_client.update_job(run_id, status="complete", output_url=gcs_uri)

        error_count = sum(1 for p in deduped if p.get("status") == "failed")
        notifications.notify_complete("tonitrus", run_id, gcs_uri, len(deduped), error_count)

        return JSONResponse({"ok": True, "rows": len(deduped)})

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
