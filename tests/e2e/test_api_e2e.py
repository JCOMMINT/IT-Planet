"""End-to-end tests for the CRS public API.

Uses FastAPI's TestClient (synchronous) against the real app with all
external dependencies (Firestore, Cloud Tasks, worker calls) mocked out.
Tests the full request-response cycle including auth, job creation, and
status polling.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.e2e

VALID_KEY = "test-api-key"
INVALID_KEY = "wrong-key"
TEST_JOB_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"


@pytest.fixture()
def client():
    """Return a TestClient for the CRS FastAPI app."""
    from crs.main import app
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _mock_externals():
    """Patch all external I/O for every e2e test."""
    with patch("crs.main.firestore_client.create_job", new=AsyncMock()), \
         patch("crs.main.tasks.enqueue", new=AsyncMock()):
        yield


# ── POST /scrape ──────────────────────────────────────────────────────────────

class TestPostScrape:
    def test_returns_202_with_job_id(self, client):
        resp = client.post(
            "/scrape",
            json={"collector": "jacob", "input_url": "https://www.jacob.de/notebooks"},
            headers={"X-Api-Key": VALID_KEY},
        )
        assert resp.status_code == 202
        body = resp.json()
        assert "job_id" in body
        assert body["status"] == "queued"

    def test_returns_401_on_missing_key(self, client):
        resp = client.post(
            "/scrape",
            json={"collector": "jacob", "input_url": "https://www.jacob.de/notebooks"},
        )
        assert resp.status_code == 422  # Header required by FastAPI

    def test_returns_401_on_wrong_key(self, client):
        resp = client.post(
            "/scrape",
            json={"collector": "jacob", "input_url": "https://www.jacob.de/notebooks"},
            headers={"X-Api-Key": INVALID_KEY},
        )
        assert resp.status_code == 401

    def test_returns_422_on_invalid_collector(self, client):
        resp = client.post(
            "/scrape",
            json={"collector": "unknown_collector", "input_url": "https://example.com"},
            headers={"X-Api-Key": VALID_KEY},
        )
        assert resp.status_code == 422

    def test_returns_422_on_invalid_url(self, client):
        resp = client.post(
            "/scrape",
            json={"collector": "jacob", "input_url": "not-a-url"},
            headers={"X-Api-Key": VALID_KEY},
        )
        assert resp.status_code == 422

    @pytest.mark.parametrize("collector", ["jacob", "it_resell", "it_market", "tonitrus"])
    def test_all_collectors_accepted(self, client, collector):
        resp = client.post(
            "/scrape",
            json={"collector": collector, "input_url": "https://example.com/category"},
            headers={"X-Api-Key": VALID_KEY},
        )
        assert resp.status_code == 202

    def test_job_id_is_uuid_format(self, client):
        import re
        resp = client.post(
            "/scrape",
            json={"collector": "it_resell", "input_url": "https://www.it-resell.com/en/collections/all"},
            headers={"X-Api-Key": VALID_KEY},
        )
        job_id = resp.json()["job_id"]
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        assert uuid_pattern.match(job_id)


# ── GET /jobs/{job_id} ────────────────────────────────────────────────────────

class TestGetJob:
    def test_returns_queued_status(self, client):
        job_doc = {
            "job_id": TEST_JOB_ID,
            "collector": "jacob",
            "status": "queued",
            "output_url": None,
            "error": None,
        }
        with patch("crs.main.firestore_client.get_job", new=AsyncMock(return_value=job_doc)):
            resp = client.get(
                f"/jobs/{TEST_JOB_ID}",
                headers={"X-Api-Key": VALID_KEY},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "queued"
        assert body["output_url"] is None

    def test_returns_complete_with_output_url(self, client):
        job_doc = {
            "job_id": TEST_JOB_ID,
            "collector": "it_resell",
            "status": "complete",
            "output_url": "gs://bucket/it_resell/2026-04-07/run.csv",
            "error": None,
        }
        with patch("crs.main.firestore_client.get_job", new=AsyncMock(return_value=job_doc)):
            resp = client.get(
                f"/jobs/{TEST_JOB_ID}",
                headers={"X-Api-Key": VALID_KEY},
            )
        assert resp.status_code == 200
        assert resp.json()["output_url"] == "gs://bucket/it_resell/2026-04-07/run.csv"

    def test_returns_failed_with_error(self, client):
        job_doc = {
            "job_id": TEST_JOB_ID,
            "collector": "tonitrus",
            "status": "failed",
            "output_url": None,
            "error": "Proxy exhausted after 3 retries",
        }
        with patch("crs.main.firestore_client.get_job", new=AsyncMock(return_value=job_doc)):
            resp = client.get(
                f"/jobs/{TEST_JOB_ID}",
                headers={"X-Api-Key": VALID_KEY},
            )
        assert resp.status_code == 200
        assert resp.json()["status"] == "failed"
        assert "retries" in resp.json()["error"]

    def test_returns_404_for_unknown_job(self, client):
        with patch("crs.main.firestore_client.get_job", new=AsyncMock(return_value=None)):
            resp = client.get(
                "/jobs/nonexistent-id",
                headers={"X-Api-Key": VALID_KEY},
            )
        assert resp.status_code == 404

    def test_returns_401_on_wrong_key(self, client):
        with patch("crs.main.firestore_client.get_job", new=AsyncMock(return_value=None)):
            resp = client.get(
                f"/jobs/{TEST_JOB_ID}",
                headers={"X-Api-Key": INVALID_KEY},
            )
        assert resp.status_code == 401


# ── GET /health ───────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_check_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}

    def test_health_check_no_auth_required(self, client):
        """Health endpoint must be reachable without an API key (liveness probe)."""
        resp = client.get("/health")
        assert resp.status_code == 200
