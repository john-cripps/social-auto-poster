#!/usr/bin/env python3
"""Validate configured services without creating a post."""

from __future__ import annotations

import logging

import requests

from social_autoposter.config import ConfigurationError, Settings
from social_autoposter.sheets import SheetClient


def check(name, function):
    try:
        function()
        return name, True, "ok"
    except Exception as exc:
        return name, False, str(exc).replace("\n", " ")[:160]


def verify_google(settings):
    SheetClient(settings.sheet_id, settings.sheet_tab, settings.service_account_info).read_posts()


def verify_bluesky(settings):
    response = requests.post("https://bsky.social/xrpc/com.atproto.server.createSession", json={"identifier": settings.bluesky_handle, "password": settings.bluesky_app_password}, timeout=30)
    response.raise_for_status()


def verify_mastodon(settings):
    if not settings.mastodon_base_url or not settings.mastodon_access_token:
        raise ConfigurationError("MASTODON_BASE_URL or MASTODON_ACCESS_TOKEN is missing")
    response = requests.get(f"{settings.mastodon_base_url}/api/v1/accounts/verify_credentials", headers={"Authorization": f"Bearer {settings.mastodon_access_token}"}, timeout=30)
    response.raise_for_status()


def main() -> int:
    logging.basicConfig(level=logging.WARNING)
    try:
        settings = Settings.from_environment()
    except Exception as exc:
        print(f"Configuration: FAIL — {exc}")
        return 1
    results = [check("Google Sheets", lambda: verify_google(settings)), check("Bluesky", lambda: verify_bluesky(settings)), check("Mastodon", lambda: verify_mastodon(settings))]
    print("Service          Result  Details")
    print("---------------- ------- ----------------")
    for name, passed, detail in results:
        print(f"{name:<16} {'PASS' if passed else 'FAIL':<7} {detail}")
    return 0 if all(passed for _, passed, _ in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
