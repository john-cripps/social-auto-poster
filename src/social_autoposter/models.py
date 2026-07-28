from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Content:
    id: str
    stream: str
    body: str
    image_url: str | None = None
    link: str | None = None


@dataclass
class SheetPost:
    content: Content
    platforms: list[str]
    publish_at: datetime | None
    status: str
    posted_at: str | None
    error: str | None
    row_number: int

    @property
    def is_due(self) -> bool:
        return self.publish_at is None or self.publish_at <= datetime.now(timezone.utc)


@dataclass(frozen=True)
class PostResult:
    platform: str
    success: bool
    post_id: str | None = None
    error: str | None = None
    dry_run: bool = False


@dataclass
class RunSummary:
    results: list[PostResult] = field(default_factory=list)

    @property
    def failures(self) -> list[PostResult]:
        return [result for result in self.results if not result.success]
