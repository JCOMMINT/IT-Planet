"""Firestore state management for all collectors."""
from __future__ import annotations

import datetime
from typing import Any

from google.cloud import firestore

from . import config

_db: firestore.AsyncClient | None = None

JOB_TTL_DAYS = 30
TONITRUS_PRODUCT_TTL_DAYS = 7


def _get_db() -> firestore.AsyncClient:
    """Return the module-level Firestore async client, creating it if needed.

    Uses a module-level singleton so the client is initialised at most once
    per process, avoiding redundant credential lookups.

    Returns:
        The shared :class:`google.cloud.firestore.AsyncClient` instance.
    """
    global _db
    if _db is None:
        _db = firestore.AsyncClient(project=config.FIRESTORE_PROJECT)
    return _db


def _ttl(days: int) -> datetime.datetime:
    """Calculate an absolute expiry timestamp offset from now.

    Args:
        days: Number of days from the current UTC time until expiry.

    Returns:
        A UTC :class:`datetime.datetime` representing the expiry time.
    """
    return datetime.datetime.utcnow() + datetime.timedelta(days=days)


# ── Job CRUD ──────────────────────────────────────────────────────────────────

async def create_job(job_id: str, collector: str, input_url: str) -> None:
    """Create a new job document in the ``jobs`` Firestore collection.

    Initialises the document with ``status="queued"`` and a TTL of
    :data:`JOB_TTL_DAYS` days from creation time.

    Args:
        job_id: Unique identifier for the job (used as the Firestore document
            ID).
        collector: Name of the collector that will process this job (e.g.
            ``"jacob"``).
        input_url: The URL to be scraped by the collector.
    """
    db = _get_db()
    await db.collection("jobs").document(job_id).set({
        "job_id": job_id,
        "collector": collector,
        "input_url": input_url,
        "status": "queued",
        "output_url": None,
        "error": None,
        "created_at": firestore.SERVER_TIMESTAMP,
        "updated_at": firestore.SERVER_TIMESTAMP,
        "expires_at": _ttl(JOB_TTL_DAYS),
    })


async def get_job(job_id: str) -> dict | None:
    """Fetch a job document from Firestore by its ID.

    Args:
        job_id: The Firestore document ID of the job to retrieve.

    Returns:
        A dict containing the job fields if the document exists, or ``None``
        if no document was found with the given ID.
    """
    db = _get_db()
    doc = await db.collection("jobs").document(job_id).get()
    return doc.to_dict() if doc.exists else None


async def update_job(job_id: str, **fields: Any) -> None:
    """Update arbitrary fields on an existing job document.

    Automatically sets ``updated_at`` to the Firestore server timestamp on
    every call.

    Args:
        job_id: The Firestore document ID of the job to update.
        **fields: Keyword arguments representing the field names and values to
            merge into the existing document.
    """
    db = _get_db()
    fields["updated_at"] = firestore.SERVER_TIMESTAMP
    await db.collection("jobs").document(job_id).update(fields)


# ── Tonitrus fan-out ──────────────────────────────────────────────────────────

async def tonitrus_set_expected(run_id: str, expected_count: int) -> None:
    """Initialise the Tonitrus fan-out counters on a job document.

    Sets ``tonitrus_expected_count`` to the given value and resets
    ``tonitrus_completed_count`` to zero. Called once after the discovery
    phase determines how many category workers will be dispatched.

    Args:
        run_id: The Firestore document ID of the Tonitrus job.
        expected_count: Total number of category workers that will report
            back for this run.
    """
    db = _get_db()
    await db.collection("jobs").document(run_id).update({
        "tonitrus_expected_count": expected_count,
        "tonitrus_completed_count": 0,
    })


async def tonitrus_increment_completed(run_id: str) -> int:
    """Atomically increment the completed worker count for a Tonitrus run.

    Uses a Firestore transaction to prevent lost updates when multiple
    category workers report completion concurrently.

    Args:
        run_id: The Firestore document ID of the Tonitrus job.

    Returns:
        The new value of ``tonitrus_completed_count`` after incrementing.
    """
    db = _get_db()
    ref = db.collection("jobs").document(run_id)

    @firestore.async_transactional
    async def _txn(transaction: firestore.AsyncTransaction) -> int:
        """Transactional inner function that reads, increments, and writes.

        Args:
            transaction: The active Firestore async transaction context.

        Returns:
            The incremented completed count value.
        """
        doc = await ref.get(transaction=transaction)
        data = doc.to_dict() or {}
        new_count = data.get("tonitrus_completed_count", 0) + 1
        transaction.update(ref, {"tonitrus_completed_count": new_count})
        return new_count

    return await _txn(db.transaction())


async def tonitrus_get_counts(run_id: str) -> tuple[int, int]:
    """Retrieve the current fan-out progress counters for a Tonitrus run.

    Args:
        run_id: The Firestore document ID of the Tonitrus job.

    Returns:
        A tuple of ``(completed_count, expected_count)``. Both values default
        to ``0`` if the document does not exist or the fields are absent.
    """
    doc = await get_job(run_id)
    if not doc:
        return 0, 0
    return doc.get("tonitrus_completed_count", 0), doc.get("tonitrus_expected_count", 0)


# ── Tonitrus product storage ───────────────────────────────────────────────────

async def tonitrus_write_products(run_id: str, category_id: str, products: list[dict]) -> None:
    """Batch-write scraped product records to Firestore for a Tonitrus run.

    Products are stored under ``tonitrus_products/{run_id}/{category_id}/``
    with a TTL of :data:`TONITRUS_PRODUCT_TTL_DAYS` days. The document ID for
    each product is derived from ``product_code``, the last path segment of
    ``url``, or the first 40 characters of ``name``, in that priority order.

    Args:
        run_id: The Firestore document ID of the parent Tonitrus job.
        category_id: Identifier for the product category sub-collection.
        products: List of product dicts to write. Each dict should contain at
            least one of ``product_code``, ``url``, or ``name`` to form a
            stable document ID.
    """
    db = _get_db()
    expires_at = _ttl(TONITRUS_PRODUCT_TTL_DAYS)
    batch = db.batch()
    col = db.collection("tonitrus_products").document(run_id).collection(category_id)
    for p in products:
        key = p.get("product_code") or p.get("url", "").split("/")[-1] or p.get("name", "")[:40]
        ref = col.document(key[:500])  # Firestore doc ID limit
        batch.set(ref, {**p, "expires_at": expires_at})
    await batch.commit()


async def tonitrus_read_all_products(run_id: str) -> list[dict]:
    """Read all product records for a Tonitrus run across all categories.

    Iterates over every sub-collection (one per category) under
    ``tonitrus_products/{run_id}`` and aggregates their documents.

    Args:
        run_id: The Firestore document ID of the Tonitrus job whose products
            should be retrieved.

    Returns:
        A flat list of product dicts gathered from all category sub-collections.
        Returns an empty list if no products have been written yet.
    """
    db = _get_db()
    run_ref = db.collection("tonitrus_products").document(run_id)
    # List all sub-collections (one per category)
    sub_cols = run_ref.collections()
    products = []
    async for col in sub_cols:
        async for doc in col.stream():
            products.append(doc.to_dict())
    return products
