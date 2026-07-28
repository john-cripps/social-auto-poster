from __future__ import annotations

import json
import os
from dataclasses import dataclass

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    pass


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ConfigurationError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class Settings:
    sheet_id: str
    sheet_tab: str
    service_account_info: dict
    bluesky_handle: str
    bluesky_app_password: str
    mastodon_base_url: str
    mastodon_access_token: str
    linkedin_client_id: str
    linkedin_client_secret: str
    linkedin_access_token: str
    linkedin_refresh_token: str
    linkedin_access_token_expires_at: int
    linkedin_author_urn: str
    linkedin_version: str
    discord_webhook_url: str

    @classmethod
    def from_environment(cls) -> "Settings":
        load_dotenv()
        raw_json = required("GOOGLE_SERVICE_ACCOUNT_JSON")
        try:
            service_account_info = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ConfigurationError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc
        return cls(
            sheet_id=required("GOOGLE_SHEET_ID"),
            sheet_tab=os.getenv("GOOGLE_SHEET_TAB", "Posts").strip() or "Posts",
            service_account_info=service_account_info,
            bluesky_handle=required("BLUESKY_HANDLE"),
            bluesky_app_password=required("BLUESKY_APP_PASSWORD"),
            mastodon_base_url=os.getenv("MASTODON_BASE_URL", "").strip().rstrip("/"),
            mastodon_access_token=os.getenv("MASTODON_ACCESS_TOKEN", "").strip(),
            linkedin_client_id=os.getenv("LINKEDIN_CLIENT_ID", "").strip(),
            linkedin_client_secret=os.getenv("LINKEDIN_CLIENT_SECRET", "").strip(),
            linkedin_access_token=os.getenv("LINKEDIN_ACCESS_TOKEN", "").strip(),
            linkedin_refresh_token=os.getenv("LINKEDIN_REFRESH_TOKEN", "").strip(),
            linkedin_access_token_expires_at=int(os.getenv("LINKEDIN_ACCESS_TOKEN_EXPIRES_AT", "0") or 0),
            linkedin_author_urn=os.getenv("LINKEDIN_AUTHOR_URN", "").strip(),
            linkedin_version=os.getenv("LINKEDIN_VERSION", "202607").strip() or "202607",
            discord_webhook_url=os.getenv("DISCORD_WEBHOOK_URL", "").strip(),
        )
