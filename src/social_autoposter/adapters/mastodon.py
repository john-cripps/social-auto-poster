from __future__ import annotations

import logging
import time

import requests

from ..models import Content, PostResult
from .base import PlatformAdapter

logger = logging.getLogger(__name__)


class MastodonAdapter(PlatformAdapter):
    platform = "mastodon"

    def __init__(self, base_url: str, access_token: str, *, dry_run: bool = True, session=None):
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self.dry_run = dry_run
        self.session = session or requests.Session()

    def post(self, content: Content) -> PostResult:
        if self.dry_run:
            logger.info("dry_run platform=mastodon content_id=%s", content.id)
            return PostResult(self.platform, True, post_id=f"dry-run:{content.id}", dry_run=True)
        if not self.base_url or not self.access_token:
            return PostResult(self.platform, False, error="MASTODON_BASE_URL and MASTODON_ACCESS_TOKEN are required for live posting")
        try:
            response = self._request_with_retry(
                "POST", f"{self.base_url}/api/v1/statuses",
                headers={"Authorization": f"Bearer {self.access_token}"},
                data={"status": self._text(content)},
            )
            response.raise_for_status()
            return PostResult(self.platform, True, post_id=response.json().get("id"))
        except requests.HTTPError as exc:
            message = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            logger.error("platform=mastodon error=%s", message)
            return PostResult(self.platform, False, error=message)
        except (requests.RequestException, ValueError) as exc:
            logger.error("platform=mastodon error=%s", exc)
            return PostResult(self.platform, False, error=str(exc))

    @staticmethod
    def _text(content: Content) -> str:
        return f"{content.body}\n\n{content.link}" if content.link else content.body

    def _request_with_retry(self, method: str, url: str, **kwargs):
        for attempt in range(3):
            response = self.session.request(method, url, timeout=30, **kwargs)
            if response.status_code not in (429, 500, 502, 503, 504) or attempt == 2:
                return response
            delay = 2**attempt
            logger.warning("retry platform=mastodon status=%s delay=%s", response.status_code, delay)
            time.sleep(delay)
