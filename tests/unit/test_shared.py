"""Unit tests for shared utilities (config, http_client, gcs, notifications)."""

from __future__ import annotations

import csv
import io
from unittest.mock import MagicMock, patch

# ── shared.http_client ────────────────────────────────────────────────────────


class TestHttpClient:
    def test_dc_proxy_port(self):
        from shared.http_client import make_dc_proxy

        proxy = make_dc_proxy()
        assert "22225" in proxy["http"]

    def test_residential_proxy_port(self):
        from shared.http_client import make_residential_proxy

        proxy = make_residential_proxy()
        assert "33335" in proxy["http"]

    def test_dc_proxy_with_slot(self):
        from shared.http_client import make_dc_proxy

        proxy = make_dc_proxy(sticky=True, slot=2)
        assert "session-slot2" in proxy["http"]

    def test_dc_proxy_sticky_random(self):
        from shared.http_client import make_dc_proxy

        p1 = make_dc_proxy(sticky=True)
        p2 = make_dc_proxy(sticky=True)
        # Random session tokens should differ (probabilistic)
        assert p1["http"] != p2["http"]

    def test_camoufox_proxy_structure(self):
        from shared.http_client import camoufox_proxy

        proxy = camoufox_proxy()
        assert "server" in proxy
        assert "username" in proxy
        assert "password" in proxy
        assert "bypass" in proxy
        assert proxy["bypass"] == []

    def test_camoufox_proxy_uses_residential_port(self):
        from shared.http_client import camoufox_proxy

        proxy = camoufox_proxy()
        assert "33335" in proxy["server"]


# ── shared.gcs_client ─────────────────────────────────────────────────────────


class TestGcsClient:
    def test_upload_csv_returns_gs_uri(self):
        from shared import gcs_client

        mock_blob = MagicMock()
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client = MagicMock()
        mock_storage_client.bucket.return_value = mock_bucket

        with patch("shared.gcs_client._get_client", return_value=mock_storage_client):
            rows = [{"name": "Item A", "price": 100.0, "status": "ok", "error_message": ""}]
            fields = ["name", "price", "status", "error_message"]
            uri = gcs_client.upload_csv("run-123", "jacob", rows, fields)

        assert uri.startswith("gs://")
        assert "jacob" in uri
        assert "run-123" in uri

    def test_upload_csv_writes_correct_content(self):
        from shared import gcs_client

        captured_content = {}

        def fake_upload(content, content_type):
            captured_content["data"] = content

        mock_blob = MagicMock()
        mock_blob.upload_from_string.side_effect = fake_upload
        mock_bucket = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        mock_storage_client = MagicMock()
        mock_storage_client.bucket.return_value = mock_bucket

        with patch("shared.gcs_client._get_client", return_value=mock_storage_client):
            rows = [{"name": "Test", "price": 42.0, "status": "ok", "error_message": ""}]
            gcs_client.upload_csv(
                "run-abc", "it_resell", rows, ["name", "price", "status", "error_message"]
            )

        csv_data = captured_content["data"]
        reader = csv.DictReader(io.StringIO(csv_data))
        parsed = list(reader)
        assert len(parsed) == 1
        assert parsed[0]["name"] == "Test"

    def test_blob_path_format(self):
        from shared.gcs_client import _blob_path

        path = _blob_path("jacob", "run-xyz")
        parts = path.split("/")
        assert parts[0] == "jacob"
        assert parts[2] == "run-xyz.csv"
        # Middle part is a date string YYYY-MM-DD
        assert len(parts[1]) == 10
        assert parts[1][4] == "-"


# ── shared.notifications ──────────────────────────────────────────────────────


class TestNotifications:
    def test_slack_notify_swallows_exceptions(self):
        """Notification failures must never propagate."""
        from shared import notifications

        with patch("shared.notifications.httpx.post", side_effect=RuntimeError("timeout")):
            notifications.slack_notify("test message")  # Must not raise

    def test_email_notify_swallows_exceptions(self):
        from shared import notifications

        with patch("shared.notifications.smtplib.SMTP", side_effect=ConnectionRefusedError):
            notifications.email_notify("Subject", "Body")  # Must not raise

    def test_notify_complete_calls_both(self):
        from shared import notifications

        with (
            patch("shared.notifications.slack_notify") as mock_slack,
            patch("shared.notifications.email_notify") as mock_email,
        ):
            notifications.notify_complete("jacob", "run-1", "gs://bucket/file.csv", 100, 2)
            mock_slack.assert_called_once()
            mock_email.assert_called_once()

    def test_notify_error_calls_both(self):
        from shared import notifications

        with (
            patch("shared.notifications.slack_notify") as mock_slack,
            patch("shared.notifications.email_notify") as mock_email,
        ):
            notifications.notify_error("jacob", "run-1", "some error")
            mock_slack.assert_called_once()
            mock_email.assert_called_once()

    def test_notify_start_calls_slack_only(self):
        from shared import notifications

        with (
            patch("shared.notifications.slack_notify") as mock_slack,
            patch("shared.notifications.email_notify") as mock_email,
        ):
            notifications.notify_start("jacob", "run-1", "https://jacob.de/category")
            mock_slack.assert_called_once()
            mock_email.assert_not_called()

    def test_notify_complete_message_contains_run_id(self):
        from shared import notifications

        messages = []
        with (
            patch("shared.notifications.slack_notify", side_effect=lambda m: messages.append(m)),
            patch("shared.notifications.email_notify"),
        ):
            notifications.notify_complete("jacob", "run-999", "gs://b/f.csv", 50, 0)
        assert "run-999" in messages[0]
