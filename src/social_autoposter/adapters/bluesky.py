from __future__ import annotations

import logging
from datetime import datetime, timezone

import requests

from ..models import Content, PostResult
from .base import PlatformAdapter

logger = logging.getLogger(__name__)


class BlueskyAdapter(PlatformAdapter):
    platform = "bluesky"

    def __init__(self, handle: str, app_password: str, *, dry_run: bool = True, session=None):
        self.handle = handle
        self.app_password = app_password
        self.dry_run = dry_run
        self.session = session or requests.Session()

    def post(self, content: Content) -> PostResult:
        if self.dry_run:
            logger.info("dry_run platform=bluesky content_id=%s", content.id)
            return PostResult(self.platform, True, post_id=f"dry-run:{content.id}", dry_run=True)
        try:
            session = self._request_with_retry("POST", "https://bsky.social/xrpc/com.atproto.server.createSession", json={"identifier": self.handle, "password": self.app_password})
            session.raise_for_status()
            access_jwt = session.json()["accessJwt"]
            response = self._request_with_retry(
                "POST", "https://bsky.social/xrpc/com.atproto.repo.createRecord",
                headers={"Authorization": f"Bearer {access_jwt}"},
                json={"repo": self.handle, "collection": "app.bsky.feed.post", "record": {"text": self._text(content), "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}},
            )
            response.raise_for_status()
            uri = response.json().get("uri")
            return PostResult(self.platform, True, post_id=uri)
        except requests.HTTPError as exc:
            message = f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
            logger.error("platform=bluesky error=%s", message)
            return PostResult(self.platform, False, error=message)
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.error("platform=bluesky error=%s", exc)
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
            logger.warning("retry platform=bluesky status=%s delay=%s", response.status_code, delay)
            import time
            time.sleep(delay)
