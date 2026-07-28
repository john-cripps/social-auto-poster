from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from .models import Content, SheetPost

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
COLUMNS = ["id", "stream", "body", "image_url", "link", "platforms", "publish_at", "status", "posted_at", "error"]


def _parse_datetime(value: str) -> datetime | None:
    if not value.strip():
        return None
    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("publish_at must include a timezone and be ISO 8601 UTC")
    return parsed.astimezone(timezone.utc)


class SheetClient:
    def __init__(self, sheet_id: str, sheet_tab: str, service_account_info: dict[str, Any], service=None):
        self.sheet_id = sheet_id
        self.sheet_tab = sheet_tab
        self.service = service or build(
            "sheets", "v4", credentials=Credentials.from_service_account_info(service_account_info, scopes=SCOPES)
        )

    def read_posts(self) -> list[SheetPost]:
        result = self.service.spreadsheets().values().get(
            spreadsheetId=self.sheet_id, range=f"{self.sheet_tab}!A:J"
        ).execute()
        rows = result.get("values", [])
        if not rows:
            return []
        header = [str(value).strip() for value in rows[0]]
        missing = [column for column in COLUMNS if column not in header]
        if missing:
            raise ValueError(f"Sheet is missing required columns: {', '.join(missing)}")
        posts: list[SheetPost] = []
        for row_number, values in enumerate(rows[1:], start=2):
            data = {column: (values[header.index(column)] if header.index(column) < len(values) else "") for column in COLUMNS}
            if not data["id"]:
                continue
            posts.append(SheetPost(
                content=Content(data["id"], data["stream"], data["body"], data["image_url"] or None, data["link"] or None),
                platforms=[part.strip().lower() for part in data["platforms"].split(",") if part.strip()] or ["all"],
                publish_at=_parse_datetime(data["publish_at"]),
                status=data["status"].strip().lower(), posted_at=data["posted_at"] or None,
                error=data["error"] or None, row_number=row_number,
            ))
        return posts

    def update_result(self, row_number: int, *, posted_at: str | None = None, error: str | None = None) -> None:
        updates = []
        if posted_at is not None:
            updates.append((f"{self.sheet_tab}!I{row_number}", [[posted_at]]))
        if error is not None:
            updates.append((f"{self.sheet_tab}!J{row_number}", [[error]]))
        if updates:
            body = {"valueInputOption": "RAW", "data": [{"range": cell_range, "values": values} for cell_range, values in updates]}
            self.service.spreadsheets().values().batchUpdate(spreadsheetId=self.sheet_id, body=body).execute()
