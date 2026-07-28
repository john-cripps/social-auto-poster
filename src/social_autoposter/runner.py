from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from .adapters.base import PlatformAdapter
from .models import PostResult, RunSummary

logger = logging.getLogger(__name__)
KNOWN_PLATFORMS = {"bluesky", "mastodon", "linkedin", "facebook", "instagram", "threads"}


def run(sheet_client, adapters: dict[str, PlatformAdapter], *, live: bool = False) -> RunSummary:
    summary = RunSummary()
    for post in sheet_client.read_posts():
        if post.posted_at or post.status != "queued" or not post.is_due:
            continue
        requested = KNOWN_PLATFORMS if "all" in post.platforms else set(post.platforms)
        row_results: list[PostResult] = []
        for platform in sorted(requested):
            adapter = adapters.get(platform)
            if adapter is None:
                result = PostResult(platform, False, error="Adapter is not implemented yet")
            else:
                try:
                    result = adapter.post(post.content)
                except Exception as exc:  # one adapter must never abort other platforms
                    logger.exception("platform=%s unexpected_error", platform)
                    result = PostResult(platform, False, error=str(exc))
            summary.results.append(result)
            row_results.append(result)
        if live:
            errors = {result.platform: result.error for result in row_results if not result.success}
            if not errors and row_results:
                # The row-level posted_at is written only once every requested platform succeeds.
                sheet_client.update_result(post.row_number, posted_at=datetime.now(timezone.utc).isoformat())
            elif errors:
                sheet_client.update_result(post.row_number, error=json.dumps(errors, sort_keys=True))
        logger.info("content_id=%s results=%s", post.content.id, len(requested))
    return summary
