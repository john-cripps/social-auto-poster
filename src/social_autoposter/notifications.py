from __future__ import annotations

import logging

import requests

from .models import RunSummary

logger = logging.getLogger(__name__)


def notify_discord(webhook_url: str, summary: RunSummary) -> bool:
    """Send a compact failure alert. A notification failure never aborts posting."""
    if not webhook_url or not summary.failures:
        return True
    lines = [f"Social auto-poster failure: {len(summary.failures)} platform failure(s)"]
    for result in summary.failures:
        lines.append(f"- {result.platform}: {result.error or 'unknown error'}")
    try:
        response = requests.post(webhook_url, json={"content": "\n".join(lines)[:1900]}, timeout=15)
        response.raise_for_status()
        logger.info("discord_notification_sent failures=%s", len(summary.failures))
        return True
    except requests.RequestException as exc:
        logger.error("discord_notification_failed error=%s", exc)
        return False
