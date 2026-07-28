from __future__ import annotations

import logging

import requests

from .models import RunSummary

logger = logging.getLogger(__name__)


def notify_discord(webhook_url: str, summary: RunSummary, *, notify_all_runs: bool = True) -> bool:
    """Send a compact run summary. A notification failure never aborts posting."""
    # A scheduler heartbeat with no due rows is intentionally silent.
    if not webhook_url:
        logger.warning("discord_notification_skipped reason=webhook_not_configured")
        return True
    if not summary.results:
        return True
    succeeded = sum(1 for result in summary.results if result.success)
    failed = len(summary.failures)
    lines = [f"Social auto-poster: post event — {succeeded} succeeded, {failed} failed."]
    for result in summary.results:
        status = "OK" if result.success else "FAIL"
        detail = result.post_id or result.error or "no details"
        lines.append(f"- {status} {result.platform}: {detail}")
    try:
        response = requests.post(webhook_url, json={"content": "\n".join(lines)[:1900]}, timeout=15)
        response.raise_for_status()
        logger.info("discord_notification_sent failures=%s", len(summary.failures))
        return True
    except requests.RequestException as exc:
        logger.error("discord_notification_failed error=%s", exc)
        return False
