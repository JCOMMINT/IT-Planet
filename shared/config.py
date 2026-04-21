"""Centralised configuration loaded from environment variables.

All settings are resolved at import time. Required variables (those accessed
via ``os.environ[...]``) will raise ``KeyError`` on startup if missing, giving
fast-fail behaviour before any worker logic runs.

Sections:
    - Proxy: Bright Data superproxy credentials and ports.
    - GCS: Google Cloud Storage target bucket.
    - Firestore: Project identifier for the Firestore database.
    - Notifications: Slack webhook and SMTP credentials.
    - Auth: API key used to authenticate incoming requests.
    - Cloud Tasks: Queue configuration for async job dispatch.
    - Worker URLs: Cloud Run service endpoints for each collector.
"""

import os

# ── Proxy ────────────────────────────────────────────────────────────────────
PROXY_HOST = os.environ.get("PROXY_HOST", "brd.superproxy.io")
PROXY_USER = os.environ["PROXY_USER"]
PROXY_PASS = os.environ["PROXY_PASS"]
PROXY_PORT_DC = int(os.getenv("PROXY_PORT_DC", "22225"))
PROXY_PORT_RESIDENTIAL = int(os.getenv("PROXY_PORT_RESIDENTIAL", "33335"))

# ── GCS ──────────────────────────────────────────────────────────────────────
GCS_BUCKET = os.environ["GCS_BUCKET"]

# ── Firestore ─────────────────────────────────────────────────────────────────
FIRESTORE_PROJECT = os.environ.get("FIRESTORE_PROJECT", os.environ.get("GOOGLE_CLOUD_PROJECT", ""))

# ── Notifications ─────────────────────────────────────────────────────────────
SLACK_WEBHOOK_URL = os.environ["SLACK_WEBHOOK_URL"]
SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
SMTP_FROM = os.environ["SMTP_FROM"]
NOTIFICATION_EMAIL = os.environ["NOTIFICATION_EMAIL"]

# ── Auth ──────────────────────────────────────────────────────────────────────
API_KEY = os.environ["API_KEY"]

# ── Cloud Tasks ───────────────────────────────────────────────────────────────
CLOUD_TASKS_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
CLOUD_TASKS_LOCATION = os.getenv("CLOUD_TASKS_LOCATION", "europe-west1")
CLOUD_TASKS_QUEUE = os.environ["CLOUD_TASKS_QUEUE"]
CLOUD_TASKS_SA_EMAIL = os.getenv("CLOUD_TASKS_SA_EMAIL", "")

# ── Worker URLs (set after deploy) ────────────────────────────────────────────
JACOB_WORKER_URL = os.getenv("JACOB_WORKER_URL", "")
IT_RESELL_WORKER_URL = os.getenv("IT_RESELL_WORKER_URL", "")
IT_MARKET_WORKER_URL = os.getenv("IT_MARKET_WORKER_URL", "")
TONITRUS_DISCOVERY_URL = os.getenv("TONITRUS_DISCOVERY_URL", "")
TONITRUS_WORKER_URL = os.getenv("TONITRUS_WORKER_URL", "")
TONITRUS_MERGE_URL = os.getenv("TONITRUS_MERGE_URL", "")

COLLECTOR_WORKER_URLS = {
    "jacob": JACOB_WORKER_URL,
    "it_resell": IT_RESELL_WORKER_URL,
    "it_market": IT_MARKET_WORKER_URL,
    "tonitrus": TONITRUS_DISCOVERY_URL,
}

# ── Tonitrus output schema ─────────────────────────────────────────────────────
TONITRUS_CSV_FIELDS = [
    "product_url",
    "product_name",
    "brand",
    "model",
    "mpn",
    "sku",
    "breadcrumb",
    "prices",
    "input_url",
    "nav_page_url",
    "status",
    "error_message",
]
