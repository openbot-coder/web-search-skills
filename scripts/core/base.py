"""Abstract base classes and data models for search engines."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Unified search result model for all sources."""
    title: str
    url: str
    snippet: str = ""
    source: str = ""
    rank: int = 0
    category: str = "web"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "rank": self.rank,
            "category": self.category,
        }


class SearchEngine(ABC):
    """Abstract base class for all search engines/sources."""

    def __init__(self, name: str, config: Optional[dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        ...

    @abstractmethod
    def build_url(self, query: str, **kwargs) -> str:
        ...

    async def close(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()
