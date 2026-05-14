"""
ArXiv academic paper search engine.

Uses the ArXiv API (export.arxiv.org/api/query) to search for papers.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus

import httpx

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class ArXivEngine(SearchEngine):
    """ArXiv academic paper search engine via official API."""

    API_URL = "https://export.arxiv.org/api/query"

    def __init__(self, config: Optional[dict] = None):
        super().__init__("ArXiv", config)
        timeout = (config or {}).get("timeout", 30)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": (config or {}).get(
                    "user_agent",
                    "ArXivSearchSkill/1.0",
                ),
                "Accept": "application/atom+xml",
            },
            follow_redirects=True,
        )

    def build_url(self, query: str, max_results: int = 10, **kwargs) -> str:
        search_field = kwargs.get("search_field", "all")
        return (
            f"{self.API_URL}?search_query={search_field}:{quote_plus(query)}"
            f"&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
        )

    async def search(
        self, query: str, max_results: int = 10, **kwargs
    ) -> list[SearchResult]:
        """Search ArXiv papers."""
        url = self.build_url(query, max_results=max_results, **kwargs)
        try:
            response = await self._client.get(url)
            response.raise_for_status()
            return self._parse_response(response.text, max_results)
        except httpx.HTTPError as e:
            logger.error(f"ArXiv search failed: {e}")
            return []

    def _parse_response(self, xml_text: str, max_results: int) -> list[SearchResult]:
        """Parse ArXiv Atom XML response."""
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "arxiv": "http://arxiv.org/schemas/atom",
        }
        results = []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"ArXiv XML parse error: {e}")
            return []

        for i, entry in enumerate(root.findall("atom:entry", ns)[:max_results]):
            title = entry.findtext("atom:title", "", ns)
            summary = entry.findtext("atom:summary", "", ns)
            published = entry.findtext("atom:published", "", ns)
            updated = entry.findtext("atom:updated", "", ns)

            link_el = entry.find("atom:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""

            authors = []
            for author in entry.findall("atom:author", ns):
                name = author.findtext("atom:name", "", ns)
                if name:
                    authors.append(name)

            # Clean title and summary
            title = title.replace("\n", " ").strip()
            snippet = summary.replace("\n", " ").strip()[:300]

            parsed_date = self._parse_date(published) if published else (
                self._parse_date(updated) if updated else
                datetime.min.replace(tzinfo=timezone.utc)
            )

            results.append(
                SearchResult(
                    title=title or f"ArXiv: {summary[:60]}",
                    url=link,
                    snippet=snippet or "No abstract available",
                    source=self.name,
                    rank=i + 1,
                    category="academic",
                    extra={
                        "published": published or "",
                        "updated": updated or "",
                        "authors": ", ".join(authors),
                        "parsed_date": parsed_date,
                    },
                )
            )

        return results

    def _parse_date(self, date_str: str) -> datetime:
        """Parse ArXiv date format."""
        try:
            # ArXiv format: 2024-01-01T00:00:00Z
            return datetime.strptime(
                date_str.strip(), "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return datetime.min.replace(tzinfo=timezone.utc)

    async def close(self):
        await self._client.aclose()
