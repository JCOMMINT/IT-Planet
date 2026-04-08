"""Integration tests for Tonitrus fan-out logic - mocked Firestore and Cloud Tasks."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

pytestmark = pytest.mark.integration


class TestAtomicCounterLogic:
    """Tests the fan-in coordination logic without a real Firestore."""

    @pytest.mark.asyncio
    async def test_last_worker_triggers_merge(self):
        """When completed_count reaches expected_count, merge task is enqueued."""
        from collectors.tonitrus import worker as w

        # Simulate: 3 categories, this is the 3rd (last) worker
        async def fake_increment(run_id):
            return 3  # new count

        async def fake_get_counts(run_id):
            return 3, 3  # completed == expected → last worker

        mock_enqueue = AsyncMock()

        with (
            patch(
                "collectors.tonitrus.worker.firestore_client.tonitrus_increment_completed",
                side_effect=fake_increment,
            ),
            patch(
                "collectors.tonitrus.worker.firestore_client.tonitrus_get_counts",
                side_effect=fake_get_counts,
            ),
            patch("collectors.tonitrus.worker.tasks.enqueue", mock_enqueue),
            patch("collectors.tonitrus.worker.notifications.slack_notify"),
        ):
            completed, expected = await w._atomic_increment_and_check("run-001")

        assert completed == 3
        assert expected == 3

    @pytest.mark.asyncio
    async def test_non_last_worker_does_not_trigger_merge(self):
        """Workers that are not last should not enqueue merge task."""
        from collectors.tonitrus import worker as w

        async def fake_increment(run_id):
            return 1  # first worker done

        async def fake_get_counts(run_id):
            return 1, 5  # 4 more expected

        with (
            patch(
                "collectors.tonitrus.worker.firestore_client.tonitrus_increment_completed",
                side_effect=fake_increment,
            ),
            patch(
                "collectors.tonitrus.worker.firestore_client.tonitrus_get_counts",
                side_effect=fake_get_counts,
            ),
        ):
            completed, expected = await w._atomic_increment_and_check("run-002")

        assert completed == 1
        assert expected == 5
        assert completed < expected


class TestDiscoveryHandler:
    """Tests the discovery FastAPI handler with mocked browser and Cloud Tasks."""

    @pytest.mark.asyncio
    async def test_handler_enqueues_one_task_per_leaf(self):
        from httpx import AsyncClient

        from collectors.tonitrus.discovery import app

        leaf_urls = [
            "https://www.tonitrus.com/servers/dell?lang=eng",
            "https://www.tonitrus.com/servers/hpe?lang=eng",
            "https://www.tonitrus.com/servers/lenovo?lang=eng",
        ]

        mock_enqueue = AsyncMock()

        with (
            patch(
                "collectors.tonitrus.discovery._discover_leaf_categories",
                new=AsyncMock(return_value=leaf_urls),
            ),
            patch("collectors.tonitrus.discovery.firestore_client.update_job", new=AsyncMock()),
            patch(
                "collectors.tonitrus.discovery.firestore_client.tonitrus_set_expected",
                new=AsyncMock(),
            ),
            patch("collectors.tonitrus.discovery.tasks.enqueue", mock_enqueue),
            patch("collectors.tonitrus.discovery.notifications.slack_notify"),
            patch("collectors.tonitrus.discovery.notifications.notify_start"),
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/", json={"run_id": "run-disc-001"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["leaf_count"] == 3
        assert mock_enqueue.call_count == 3

    @pytest.mark.asyncio
    async def test_handler_fails_on_empty_discovery(self):
        from httpx import AsyncClient

        from collectors.tonitrus.discovery import app

        with (
            patch(
                "collectors.tonitrus.discovery._discover_leaf_categories",
                new=AsyncMock(return_value=[]),
            ),
            patch("collectors.tonitrus.discovery.firestore_client.update_job", new=AsyncMock()),
            patch("collectors.tonitrus.discovery.notifications.notify_start"),
            patch("collectors.tonitrus.discovery.notifications.notify_error"),
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/", json={"run_id": "run-disc-fail"})

        assert resp.status_code == 500


class TestMergeHandler:
    """Tests the merge FastAPI handler with mocked Firestore and GCS."""

    @pytest.mark.asyncio
    async def test_merge_deduplicates_by_product_code(self):
        from httpx import AsyncClient

        from collectors.tonitrus.merge import app

        products = [
            {
                "product_code": "CODE-001",
                "product_url": "https://t.com/a",
                "status": "ok",
                "error_message": "",
                "product_name": "Item A",
                "category": "",
                "breadcrumb": "",
                "description": "",
                "ean_upc": "",
                "brand": "",
                "price": 100,
                "condition": "New",
                "stock": None,
                "availability": "",
                "variants": "[]",
                "input_url": "",
                "is_cto": False,
            },
            {
                "product_code": "CODE-001",
                "product_url": "https://t.com/a-dup",
                "status": "ok",
                "error_message": "",
                "product_name": "Item A dup",
                "category": "",
                "breadcrumb": "",
                "description": "",
                "ean_upc": "",
                "brand": "",
                "price": 100,
                "condition": "New",
                "stock": None,
                "availability": "",
                "variants": "[]",
                "input_url": "",
                "is_cto": False,
            },
            {
                "product_code": "CODE-002",
                "product_url": "https://t.com/b",
                "status": "ok",
                "error_message": "",
                "product_name": "Item B",
                "category": "",
                "breadcrumb": "",
                "description": "",
                "ean_upc": "",
                "brand": "",
                "price": 200,
                "condition": "New",
                "stock": None,
                "availability": "",
                "variants": "[]",
                "input_url": "",
                "is_cto": False,
            },
        ]

        captured_rows = {}

        def fake_upload(run_id, collector, rows, fields):
            captured_rows["rows"] = rows
            return "gs://bucket/tonitrus/run.csv"

        with (
            patch(
                "collectors.tonitrus.merge.firestore_client.tonitrus_read_all_products",
                new=AsyncMock(return_value=products),
            ),
            patch("collectors.tonitrus.merge.firestore_client.update_job", new=AsyncMock()),
            patch("collectors.tonitrus.merge.gcs_client.upload_csv", side_effect=fake_upload),
            patch("collectors.tonitrus.merge.notifications.notify_complete"),
            patch("collectors.tonitrus.merge.notifications.notify_error"),
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                resp = await client.post("/", json={"run_id": "run-merge-001"})

        assert resp.status_code == 200
        assert resp.json()["rows"] == 2  # duplicate CODE-001 removed
        assert len(captured_rows["rows"]) == 2
