"""IT Resell worker – Cloud Run Service triggered by Cloud Tasks.

Exposes a FastAPI application with a POST endpoint that receives a Cloud Tasks
payload, invokes the IT-Resell scraper, uploads results to GCS, and updates
the corresponding Firestore job document with status and output location.
"""
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from shared import firestore_client, gcs_client, notifications
from scraper import run, CSV_FIELDS

app = FastAPI()


@app.post("/")
async def handle(request: Request):
    """Handle an inbound Cloud Tasks job request for the IT-Resell scraper.

    Parses the JSON payload, marks the Firestore job as running, executes
    the scraper, uploads the resulting CSV to GCS, and updates the job
    document with the final status and output URI. Sends Slack notifications
    at each lifecycle stage.

    Args:
        request: The incoming FastAPI Request carrying a JSON body with
            ``run_id`` and ``input_url`` fields.

    Returns:
        JSONResponse with ``{"ok": True, "rows": <count>}`` on success, or
        ``{"ok": False, "error": <message>}`` with HTTP 500 on failure.
    """
    payload = await request.json()
    run_id: str = payload["run_id"]
    input_url: str = payload["input_url"]

    logger.info("Job received run_id=%s input_url=%s", run_id, input_url)
    await firestore_client.update_job(run_id, status="running")
    notifications.notify_start("it_resell", run_id, input_url)

    try:
        rows = await run(input_url, run_id)
        logger.info("Scrape complete run_id=%s rows=%d", run_id, len(rows))
        gcs_uri = gcs_client.upload_csv(run_id, "it_resell", rows, CSV_FIELDS)
        logger.info("CSV uploaded run_id=%s uri=%s", run_id, gcs_uri)
        await firestore_client.update_job(run_id, status="complete", output_url=gcs_uri)
        error_count = sum(1 for r in rows if r.get("status") == "failed")
        notifications.notify_complete("it_resell", run_id, gcs_uri, len(rows), error_count)
        return JSONResponse({"ok": True, "rows": len(rows)})

    except Exception as exc:
        err_msg = traceback.format_exc()
        logger.error("Job failed run_id=%s error=%s", run_id, err_msg)
        await firestore_client.update_job(run_id, status="failed", error=str(exc))
        notifications.notify_error("it_resell", run_id, err_msg)
        return JSONResponse(
            {"ok": False, "error": str(exc)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@app.get("/health")
async def health():
    """Return a liveness probe response.

    Returns:
        Dictionary ``{"ok": True}`` indicating the service is running.
    """
    return {"ok": True}
