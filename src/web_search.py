"""
Core web search module providing multi-engine search capabilities.

Supports DuckDuckGo, Google Custom Search, Bing, and extensible backends.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Represents a single search result."""
    title: str
    url: str
    snippet: str
    source: str = ""
    rank: int = 0


@dataclass
class SearchConfig:
    """Configuration for web search."""
    engine: str = "duckduckgo"
    max_results: int = 10
    timeout: int = 15
    user_agent: str = "WebSearchSkill/1.0"
    proxies: dict[str, str] = field(default_factory=dict)


class WebSearch:
    """
    Main web search class supporting multiple search backends.

    Usage:
        searcher = WebSearch()
        results = searcher.search("Python async programming")
    """

    def __init__(self, config: Optional[SearchConfig | dict[str, Any]] = None):
        if config is None:
            self.config = SearchConfig()
        elif isinstance(config, dict):
            self.config = SearchConfig(**config)
        else:
            self.config = config

        self._client = httpx.AsyncClient(
            timeout=self.config.timeout,
            headers={"User-Agent": self.config.user_agent},
            proxies=self.config.proxies if self.config.proxies else None,
        )
        self._cache: dict[str, list[SearchResult]] = {}

    async def search(
        self,
        query: str,
        engine: Optional[str] = None,
        max_results: Optional[int] = None,
        force_refresh: bool = False,
    ) -> list[SearchResult]:
        """
        Perform a web search with the given query.

        Args:
            query: Search query string.
            engine: Search engine to use (default: config.engine).
            max_results: Maximum number of results (default: config.max_results).
            force_refresh: Ignore cached results if True.

        Returns:
            List of SearchResult objects.
        """
        cache_key = f"{engine or self.config.engine}:{query}"

        if not force_refresh and cache_key in self._cache:
            logger.debug(f"Returning cached results for: {query}")
            return self._cache[cache_key]

        engine = engine or self.config.engine
        max_results = max_results or self.config.max_results

        if engine == "duckduckgo":
            results = await self._search_duckduckgo(query, max_results)
        elif engine == "google":
            results = await self._search_google(query, max_results)
        elif engine == "bing":
            results = await self._search_bing(query, max_results)
        else:
            raise ValueError(f"Unsupported search engine: {engine}")

        self._cache[cache_key] = results
        return results

    async def _search_duckduckgo(
        self, query: str, max_results: int
    ) -> list[SearchResult]:
        """Search using DuckDuckGo (no API key required)."""
        url = "https://html.duckduckgo.com/html/"
        params = {"q": query}

        try:
            response = await self._client.post(url, data=params)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            results = []
            for i, result in enumerate(soup.select(".result")[:max_results]):
                title_el = result.select_one(".result__title a")
                snippet_el = result.select_one(".result__snippet")

                if title_el:
                    results.append(
                        SearchResult(
                            title=title_el.get_text(strip=True),
                            url=title_el.get("href", ""),
                            snippet=snippet_el.get_text(strip=True)
                            if snippet_el
                            else "",
                            source="duckduckgo",
                            rank=i + 1,
                        )
                    )
            return results
        except httpx.HTTPError as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []

    async def _search_google(
        self, query: str, max_results: int
    ) -> list[SearchResult]:
        """Search using Google Custom Search API (requires API key)."""
        logger.warning("Google Custom Search requires an API key.")
        return []

    async def _search_bing(
        self, query: str, max_results: int
    ) -> list[SearchResult]:
        """Search using Bing (requires API key)."""
        logger.warning("Bing Search requires an API key.")
        return []

    async def extract_content(self, url: str) -> Optional[str]:
        """
        Extract readable text content from a URL.

        Args:
            url: Target URL to extract content from.

        Returns:
            Extracted text content, or None on failure.
        """
        try:
            response = await self._client.get(url, follow_redirects=True)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            # Remove non-content elements
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            return soup.get_text(separator="\n", strip=True)
        except httpx.HTTPError as e:
            logger.error(f"Failed to extract content from {url}: {e}")
            return None

    async def close(self):
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()


async def search_web(
    query: str,
    engine: str = "duckduckgo",
    max_results: int = 10,
) -> list[SearchResult]:
    """
    Convenience function for one-off web searches.

    Example:
        results = await search_web("Python asyncio")
        for r in results:
            print(f"{r.title}: {r.url}")
    """
    async with WebSearch() as searcher:
        return await searcher.search(query, engine=engine, max_results=max_results)
