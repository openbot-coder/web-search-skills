"""
Core data types and base classes for search engines.

Provides:
- SearchResult: Standard result dataclass used across all engines
- SearchEngine: Abstract base class for all search engine implementations
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str = ""
    url: str = ""
    snippet: str = ""
    source: str = ""
    rank: int = 0
    category: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class SearchEngine(ABC):
    """Abstract base class for search engines."""

    def __init__(self, name: str, config: Optional[dict[str, Any]] = None):
        self.name = name
        self.config = config or {}

    @abstractmethod
    async def search(
        self, query: str, max_results: int = 10, **kwargs
    ) -> list[SearchResult]:
        """Execute a search and return results."""
        ...

    def build_url(self, query: str, **kwargs) -> str:
        """Build a search URL for this engine (optional)."""
        return ""

    async def close(self):
        """Clean up resources."""
        pass
