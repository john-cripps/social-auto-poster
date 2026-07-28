from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Content, PostResult


class PlatformAdapter(ABC):
    platform: str

    @abstractmethod
    def post(self, content: Content) -> PostResult:
        """Publish content and return a result; adapters must not raise for API failures."""
