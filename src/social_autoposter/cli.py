from __future__ import annotations

import argparse
import logging

from .adapters.bluesky import BlueskyAdapter
from .adapters.mastodon import MastodonAdapter
from .adapters.linkedin import LinkedInAdapter
from .config import Settings
from .runner import run
from .sheets import SheetClient
from .notifications import notify_discord


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish queued social posts from Google Sheets")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Preview posts without publishing (default)")
    mode.add_argument("--live", action="store_true", help="Publish to real accounts")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = Settings.from_environment()
    dry_run = not args.live
    sheet = SheetClient(settings.sheet_id, settings.sheet_tab, settings.service_account_info)
    adapters = {"bluesky": BlueskyAdapter(settings.bluesky_handle, settings.bluesky_app_password, dry_run=dry_run)}
    adapters["mastodon"] = MastodonAdapter(settings.mastodon_base_url, settings.mastodon_access_token, dry_run=dry_run)
    adapters["linkedin"] = LinkedInAdapter(client_id=settings.linkedin_client_id, client_secret=settings.linkedin_client_secret, access_token=settings.linkedin_access_token, refresh_token=settings.linkedin_refresh_token, access_token_expires_at=settings.linkedin_access_token_expires_at, author_urn=settings.linkedin_author_urn, version=settings.linkedin_version, dry_run=dry_run)
    summary = run(sheet, adapters, live=args.live)
    notify_discord(settings.discord_webhook_url, summary, notify_all_runs=settings.discord_notify_all_runs)
    logging.info("run_complete total=%s failures=%s", len(summary.results), len(summary.failures))
    return 1 if summary.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
