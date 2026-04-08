"""Slack webhook + SMTP email notifications."""
import smtplib
import ssl
from email.mime.text import MIMEText

import httpx

from . import config


# ── Slack ─────────────────────────────────────────────────────────────────────

def slack_notify(message: str) -> None:
    """Send a plain-text message to the configured Slack webhook.

    Failures are silently suppressed so that a Slack outage never interrupts
    a running collector.

    Args:
        message: The text payload to post to the Slack incoming webhook.
    """
    try:
        httpx.post(config.SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
    except Exception:
        pass  # Never let notification failure kill the worker


# ── SMTP Email ────────────────────────────────────────────────────────────────

def email_notify(subject: str, body: str) -> None:
    """Send a plain-text notification email via SMTP with STARTTLS.

    Connects to the configured SMTP host, upgrades to TLS, authenticates, and
    sends the message to :data:`config.NOTIFICATION_EMAIL`. Failures are
    silently suppressed so that an SMTP outage never interrupts a worker.

    Args:
        subject: Email subject line.
        body: Plain-text body of the email.
    """
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = config.SMTP_FROM
        msg["To"] = config.NOTIFICATION_EMAIL
        ctx = ssl.create_default_context()
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as s:
            s.starttls(context=ctx)
            s.login(config.SMTP_USER, config.SMTP_PASS)
            s.sendmail(config.SMTP_FROM, [config.NOTIFICATION_EMAIL], msg.as_string())
    except Exception:
        pass


# ── Structured events ─────────────────────────────────────────────────────────

def notify_start(collector: str, run_id: str, input_url: str) -> None:
    """Send a Slack notification indicating that a collector job has started.

    Args:
        collector: Name of the collector that was triggered (e.g. ``"jacob"``).
        run_id: Unique identifier for this scrape run.
        input_url: The URL being scraped in this job.
    """
    slack_notify(f":rocket: *{collector}* job started\nrun_id: `{run_id}`\nurl: {input_url}")


def notify_complete(
    collector: str,
    run_id: str,
    gcs_uri: str,
    total_rows: int,
    error_count: int,
) -> None:
    """Send Slack and email notifications for a successfully completed scrape.

    Args:
        collector: Name of the collector that finished (e.g. ``"jacob"``).
        run_id: Unique identifier for this scrape run.
        gcs_uri: The ``gs://`` URI of the output CSV uploaded to GCS.
        total_rows: Total number of product rows written to the output file.
        error_count: Number of rows that encountered errors during scraping.
    """
    slack_notify(
        f":white_check_mark: *{collector}* complete\n"
        f"run_id: `{run_id}`\n"
        f"rows: {total_rows} ({error_count} errors)\n"
        f"output: `{gcs_uri}`"
    )
    email_notify(
        subject=f"[IT Planet] {collector} scrape complete – {run_id}",
        body=(
            f"Collector: {collector}\n"
            f"Run ID: {run_id}\n"
            f"Total rows: {total_rows}\n"
            f"Error rows: {error_count}\n"
            f"Output: {gcs_uri}\n"
        ),
    )


def notify_error(collector: str, run_id: str, error: str) -> None:
    """Send Slack and email notifications for a failed scrape run.

    Args:
        collector: Name of the collector that failed (e.g. ``"jacob"``).
        run_id: Unique identifier for this scrape run.
        error: Human-readable description or traceback of the failure.
    """
    slack_notify(f":x: *{collector}* failed\nrun_id: `{run_id}`\nerror: {error}")
    email_notify(
        subject=f"[IT Planet] {collector} scrape FAILED – {run_id}",
        body=f"Collector: {collector}\nRun ID: {run_id}\nError: {error}\n",
    )


def notify_rate_limited(collector: str, run_id: str, url: str) -> None:
    """Send a Slack warning when a collector is rate-limited after all retries.

    Args:
        collector: Name of the collector that was rate-limited.
        run_id: Unique identifier for the affected scrape run.
        url: The specific URL that triggered the rate-limit response.
    """
    slack_notify(
        f":warning: *{collector}* rate-limited after retries\n"
        f"run_id: `{run_id}`\nurl: {url}"
    )
