"""GCS CSV upload helper."""

import csv
import datetime
import io
import json
from typing import Any

from google.cloud import storage

from . import config

_client: storage.Client | None = None


def _get_client() -> storage.Client:
    """Return the module-level GCS client, creating it if needed.

    Uses a module-level singleton to avoid constructing a new authenticated
    client on every upload call.

    Returns:
        The shared :class:`google.cloud.storage.Client` instance.
    """
    global _client
    if _client is None:
        _client = storage.Client()
    return _client


def _blob_path(collector: str, run_id: str) -> str:
    """Build the GCS object path for a collector run's CSV output.

    The path follows the pattern ``{collector}/{YYYY-MM-DD}/{run_id}.csv``,
    partitioned by UTC date for easy lifecycle management.

    Args:
        collector: Name of the collector (e.g. ``"jacob"``).
        run_id: Unique run identifier used as the filename stem.

    Returns:
        A GCS object path string (no leading slash).
    """
    date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return f"{collector}/{date_str}/{run_id}.csv"


def upload_csv(
    run_id: str, collector: str, rows: list[dict[str, Any]], fieldnames: list[str]
) -> str:
    """Serialise a list of row dicts to CSV and upload the result to GCS.

    Columns are written in the order specified by ``fieldnames``. Missing or
    ``None`` values are written as empty strings. The object is stored at
    ``{collector}/{YYYY-MM-DD}/{run_id}.csv`` inside the configured bucket.

    Args:
        run_id: Unique identifier for the scrape run; used as the CSV filename.
        collector: Name of the collector that produced the data (used as the
            top-level GCS prefix).
        rows: List of dicts where each dict represents one output row.
        fieldnames: Ordered list of column names to include in the CSV header
            and rows.

    Returns:
        The ``gs://`` URI of the uploaded object, e.g.
        ``gs://my-bucket/jacob/2026-04-06/abc123.csv``.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
    def _csv_val(v: Any) -> Any:
        if isinstance(v, (dict, list)):
            return json.dumps(v, ensure_ascii=False)
        return v if v is not None else ""

    writer.writeheader()
    for row in rows:
        writer.writerow({k: _csv_val(row.get(k)) for k in fieldnames})

    client = _get_client()
    bucket = client.bucket(config.GCS_BUCKET)
    path = _blob_path(collector, run_id)
    blob = bucket.blob(path)
    blob.upload_from_string(buf.getvalue(), content_type="text/csv")
    return f"gs://{config.GCS_BUCKET}/{path}"
