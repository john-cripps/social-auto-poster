# Social Auto-Poster

The current milestone contains the platform-independent Python runner, Google Sheets reader, shared adapter interface, Bluesky and Mastodon adapters, Discord failure alerts, and GitHub Actions workflows.

## Safety defaults

Running `social-auto-poster` is a dry run by default. It reads queued, due rows from the sheet and logs what would be posted. Use `--live` only after reviewing the dry-run output.

Post content belongs in Google Sheets, not this repository. Credentials are supplied through environment variables only.

## Sheet setup

Create a tab named `Posts` with this exact header row:

```text
id | stream | body | image_url | link | platforms | publish_at | status | posted_at | error
```

Share the sheet with the Google service account email. `publish_at` should be ISO 8601 UTC, for example `2026-07-28T16:30:00Z`.

## Local dry run

```bash
cd /Users/john/codex-html/social-auto-poster
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
set -a; source .env; set +a
social-auto-poster --dry-run
```

The command also loads `.env` automatically; the explicit `source` lines are useful when running other local commands that need the same variables.

LinkedIn and Meta adapters are deferred until the required accounts are available. Discord notification is still deferred.

See [`SETUP.md`](SETUP.md) for credential verification and the later Mac Mini migration checklist.

## GitHub Actions

The scheduled workflow intentionally calls the entrypoint with the explicit `--live` flag because scheduled automation is meant to publish. Store every value from `.env` as a GitHub Actions repository secret before enabling it. The repository must be public to use standard GitHub-hosted runners free of charge.
