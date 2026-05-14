"""Core data types and base classes for search engines."""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class SearchResult:
    title: str = ""
    url: str = ""
    snippet: str = ""
    source: str = ""
    rank: int = 0
    category: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

class SearchEngine(ABC):
    def __init__(self, name: str, config: Optional[dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
    @abstractmethod
    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        ...
    def build_url(self, query: str, **kwargs) -> str:
        return ""
    async def close(self):
        pass
