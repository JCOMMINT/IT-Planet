"""Cloud Run Service - public API gateway."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import uuid
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, HttpUrl

from shared import config, firestore_client, tasks

app = FastAPI(title="IT Planet API")

COLLECTORS = Literal["jacob", "it_resell", "it_market", "tonitrus"]


# ── Auth ──────────────────────────────────────────────────────────────────────


def _require_api_key(x_api_key: str = Header(...)) -> None:
    """Validate the ``X-Api-Key`` request header against the configured secret.

    Intended for use as an inline guard at the top of each route handler.

    Args:
        x_api_key: Value of the ``X-Api-Key`` HTTP header supplied by the
            caller.

    Raises:
        HTTPException: With status 401 if the provided key does not match
            :data:`config.API_KEY`.
    """
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


# ── Models ────────────────────────────────────────────────────────────────────


class ScrapeRequest(BaseModel):
    """Request body for the ``POST /scrape`` endpoint.

    Attributes:
        collector: Name of the collector to invoke. Must be one of the
            literals defined by the ``COLLECTORS`` type alias.
        input_url: URL of the page or listing to be scraped by the selected
            collector.
    """

    collector: COLLECTORS
    input_url: HttpUrl


class ScrapeResponse(BaseModel):
    """Response body returned by the ``POST /scrape`` endpoint.

    Attributes:
        job_id: UUID assigned to the newly created job.
        status: Initial job status string, always ``"queued"`` on creation.
    """

    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    """Response body returned by the ``GET /jobs/{job_id}`` endpoint.

    Attributes:
        job_id: Unique identifier of the queried job.
        collector: Name of the collector assigned to this job.
        status: Current job status (e.g. ``"queued"``, ``"running"``,
            ``"complete"``, or ``"failed"``).
        output_url: The ``gs://`` URI of the output CSV once the job completes,
            or ``None`` if the job has not finished.
        error: Human-readable error message if the job failed, otherwise
            ``None``.
    """

    job_id: str
    collector: str
    status: str
    output_url: str | None = None
    error: str | None = None


# ── Routes ────────────────────────────────────────────────────────────────────


@app.post("/scrape", response_model=ScrapeResponse, status_code=202)
async def scrape(body: ScrapeRequest, x_api_key: str = Header(...)) -> ScrapeResponse:
    """Enqueue a new scrape job for the specified collector.

    Validates the API key, creates a Firestore job document with status
    ``"queued"``, and dispatches a Cloud Tasks HTTP task to the appropriate
    collector worker URL.

    Args:
        body: JSON request body containing ``collector`` and ``input_url``.
        x_api_key: Value of the ``X-Api-Key`` header used for authentication.

    Returns:
        A :class:`ScrapeResponse` with the new ``job_id`` and status
        ``"queued"``.

    Raises:
        HTTPException: With status 401 if the API key is invalid.
        HTTPException: With status 500 if no worker URL is configured for the
            requested collector.
    """
    _require_api_key(x_api_key)

    worker_url = config.COLLECTOR_WORKER_URLS.get(body.collector)
    if not worker_url:
        raise HTTPException(
            status_code=500, detail=f"Worker URL not configured for {body.collector}"
        )

    job_id = str(uuid.uuid4())
    input_url = str(body.input_url)

    await firestore_client.create_job(job_id, body.collector, input_url)
    await tasks.enqueue(
        url=worker_url,
        payload={"run_id": job_id, "input_url": input_url},
        task_id=job_id,
    )

    return ScrapeResponse(job_id=job_id, status="queued")


@app.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job(job_id: str, x_api_key: str = Header(...)) -> JobStatusResponse:
    """Retrieve the current status of a scrape job by its ID.

    Args:
        job_id: The UUID of the job to look up, taken from the URL path.
        x_api_key: Value of the ``X-Api-Key`` header used for authentication.

    Returns:
        A :class:`JobStatusResponse` with the job's current state, output URL,
        and error message (if any).

    Raises:
        HTTPException: With status 401 if the API key is invalid.
        HTTPException: With status 404 if no job exists with the given ID.
    """
    _require_api_key(x_api_key)

    job = await firestore_client.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(
        job_id=job_id,
        collector=job.get("collector", ""),
        status=job.get("status", "unknown"),
        output_url=job.get("output_url"),
        error=job.get("error"),
    )


@app.get("/health")
async def health() -> dict:
    """Health-check endpoint for Cloud Run liveness probes.

    Returns:
        A JSON object ``{"ok": true}`` with an implicit 200 status code.
    """
    return {"ok": True}
