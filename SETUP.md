# Setup checklist

## Current runner: GitHub Actions

1. Keep the repository public.
2. Add the seven repository secrets listed in `README.md`.
3. Add queued rows to the private Google Sheet.
4. Use `platforms=bluesky,mastodon` until more adapters are enabled.
5. Use the Actions tab to run `Publish queued social posts` manually when testing.

## Credential verification

```bash
source .venv/bin/activate
python scripts/verify.py
```

This only authenticates and reads account/sheet metadata. It never creates a post.

## Later migration to a Mac Mini

- Install Python 3.12 and create the project virtual environment.
- Copy the project and private `.env` to the Mac Mini.
- Stop using the GitHub Actions posting workflow.
- Either load `com.example.social-auto-poster.plist` with `launchctl` or run `docker compose up -d`.
- Replace `YOUR_USER` in the plist with the Mac Mini username.
- Keep the same environment variable names and Google Sheet; no posting-code rewrite is required.
