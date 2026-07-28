from __future__ import annotations

import logging
import time

import requests

from ..models import Content, PostResult
from .base import PlatformAdapter

logger = logging.getLogger(__name__)


class LinkedInAdapter(PlatformAdapter):
    platform = "linkedin"

    def __init__(self, *, client_id: str = "", client_secret: str = "", access_token: str = "", refresh_token: str = "", access_token_expires_at: int = 0, author_urn: str = "", version: str = "202607", dry_run: bool = True, session=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.access_token_expires_at = access_token_expires_at
        self.author_urn = author_urn
        self.version = version
        self.dry_run = dry_run
        self.session = session or requests.Session()

    def post(self, content: Content) -> PostResult:
        if self.dry_run:
            logger.info("dry_run platform=linkedin content_id=%s", content.id)
            return PostResult(self.platform, True, post_id=f"dry-run:{content.id}", dry_run=True)
        missing = [name for name, value in {
            "LINKEDIN_CLIENT_ID": self.client_id,
            "LINKEDIN_CLIENT_SECRET": self.client_secret,
            "LINKEDIN_ACCESS_TOKEN": self.access_token,
            "LINKEDIN_REFRESH_TOKEN": self.refresh_token,
            "LINKEDIN_AUTHOR_URN": self.author_urn,
        }.items() if not value]
        if missing:
            return PostResult(self.platform, False, error=f"Missing LinkedIn configuration: {', '.join(missing)}")
        try:
            token = self._get_valid_token()
            response = self._post(token, content)
            if response.status_code == 401:
                token = self._refresh_access_token()
                response = self._post(token, content)
            response.raise_for_status()
            return PostResult(self.platform, True, post_id=response.headers.get("x-restli-id"))
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else "unknown"
            detail = exc.response.text[:300] if exc.response is not None else str(exc)
            message = f"HTTP {status}: {detail}"
            logger.error("platform=linkedin error=%s", message)
            return PostResult(self.platform, False, error=message)
        except (requests.RequestException, KeyError, ValueError) as exc:
            logger.error("platform=linkedin error=%s", exc)
            return PostResult(self.platform, False, error=str(exc))

    def _post(self, token: str, content: Content):
        commentary = f"{content.body}\n\n{content.link}" if content.link else content.body
        return self._request_with_retry(
            "POST", "https://api.linkedin.com/rest/posts",
            headers={"Authorization": f"Bearer {token}", "LinkedIn-Version": self.version, "X-Restli-Protocol-Version": "2.0.0", "Content-Type": "application/json"},
            json={"author": self.author_urn, "commentary": commentary, "visibility": "PUBLIC", "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []}, "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False},
        )

    def _get_valid_token(self) -> str:
        if self.access_token_expires_at and self.access_token_expires_at <= int(time.time()):
            return self._refresh_access_token()
        return self.access_token

    def _refresh_access_token(self) -> str:
        response = self._request_with_retry(
            "POST", "https://www.linkedin.com/oauth/v2/accessToken",
            data={"grant_type": "refresh_token", "refresh_token": self.refresh_token, "client_id": self.client_id, "client_secret": self.client_secret},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code >= 400:
            raise RuntimeError("LinkedIn access-token refresh failed; reauthorize the LinkedIn app")
        payload = response.json()
        self.access_token = payload["access_token"]
        self.access_token_expires_at = int(time.time()) + int(payload.get("expires_in", 0))
        if payload.get("refresh_token"):
            self.refresh_token = payload["refresh_token"]
        logger.info("linkedin_access_token_refreshed")
        return self.access_token

    def _request_with_retry(self, method: str, url: str, **kwargs):
        for attempt in range(3):
            response = self.session.request(method, url, timeout=30, **kwargs)
            if response.status_code not in (429, 500, 502, 503, 504) or attempt == 2:
                return response
            delay = 2**attempt
            logger.warning("retry platform=linkedin status=%s delay=%s", response.status_code, delay)
            time.sleep(delay)
