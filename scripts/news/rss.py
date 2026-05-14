"""
RSS news aggregation engine.

Fetches and parses RSS/Atom feeds from trusted news sources.
Inspired by the news-summary skill's RSS-based approach.

Supported sources:
- BBC (World, Business, Technology, Top Stories)
- Reuters (World News)
- NPR (US news)
- Al Jazeera (Global South perspective)
- 财联社 (RSS if available)
- 华尔街见闻 (RSS if available)
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

# RSS feed definitions
# Core sources (general news) + AI newsletters + essays + podcasts
RSS_FEEDS = {
    "BBC World": {
        "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "category": "news",
        "lang": "en",
    },
    "BBC Top Stories": {
        "url": "https://feeds.bbci.co.uk/news/rss.xml",
        "category": "news",
        "lang": "en",
    },
    "BBC Business": {
        "url": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "category": "business",
        "lang": "en",
    },
    "BBC Technology": {
        "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",
        "category": "technology",
        "lang": "en",
    },
    "Reuters": {
        "url": "https://www.reutersagency.com/feed/?best-regions=world&post_type=best",
        "category": "news",
        "lang": "en",
    },
    "NPR": {
        "url": "https://feeds.npr.org/1001/rss.xml",
        "category": "news",
        "lang": "en",
    },
    "Al Jazeera": {
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "category": "news",
        "lang": "en",
    },

    # -----------------------------------------------------------------------
    # AI Newsletters (inspired by news-aggregator-skill)
    # -----------------------------------------------------------------------
    "Latent Space": {
        "url": "https://feeds.transistor.fm/latent-space-podcast",
        "category": "technology",
        "lang": "en",
        "subcategory": "ai_newsletter",
    },
    "ChinAI": {
        "url": "https://chinai.substack.com/feed",
        "category": "technology",
        "lang": "en",
        "subcategory": "ai_newsletter",
    },
    "Memia": {
        "url": "https://memia.substack.com/feed",
        "category": "technology",
        "lang": "en",
        "subcategory": "ai_newsletter",
    },
    "Interconnects": {
        "url": "https://interconnects.substack.com/feed",
        "category": "technology",
        "lang": "en",
        "subcategory": "ai_newsletter",
    },
    "KDnuggets": {
        "url": "https://www.kdnuggets.com/feed",
        "category": "technology",
        "lang": "en",
        "subcategory": "ai_newsletter",
    },

    # -----------------------------------------------------------------------
    # Deep Essays & Thinkers (inspired by news-aggregator-skill)
    # -----------------------------------------------------------------------
    "Paul Graham": {
        "url": "https://paulgraham.com/rss.xml",
        "category": "technology",
        "lang": "en",
        "subcategory": "essay",
    },
    "James Clear": {
        "url": "https://jamesclear.com/feed",
        "category": "news",
        "lang": "en",
        "subcategory": "essay",
    },
    "Wait But Why": {
        "url": "https://waitbutwhy.com/feed",
        "category": "news",
        "lang": "en",
        "subcategory": "essay",
    },
    "Farnam Street": {
        "url": "https://fs.blog/feed/",
        "category": "news",
        "lang": "en",
        "subcategory": "essay",
    },

    # -----------------------------------------------------------------------
    # Podcasts (inspired by news-aggregator-skill)
    # -----------------------------------------------------------------------
    "Lex Fridman Podcast": {
        "url": "https://lexfridman.com/feed/podcast/",
        "category": "technology",
        "lang": "en",
        "subcategory": "podcast",
    },
    "80,000 Hours": {
        "url": "https://80000hours.org/feed/podcast/",
        "category": "news",
        "lang": "en",
        "subcategory": "podcast",
    },
}


class RSSNewsEngine(SearchEngine):
    """
    RSS-based news aggregation engine.

    Fetches and parses RSS/Atom feeds from international news sources.
    Supports filtering by category, keyword, and time range.
    """

    def __init__(self, config: Optional[dict] = None):
        super().__init__("RSS News", config)
        timeout = (config or {}).get("timeout", 30)
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": (config or {}).get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36",
                ),
                "Accept": "application/rss+xml, application/xml, text/xml, */*",
            },
            follow_redirects=True,
        )

    def build_url(self, query: str, **kwargs) -> str:
        """Build search URL - for RSS this is not a search URL but a feed URL."""
        feed_name = kwargs.get("feed", "BBC World")
        feed = RSS_FEEDS.get(feed_name, RSS_FEEDS["BBC World"])
        return feed["url"]

    async def search(self, query: str, max_results: int = 10, **kwargs) -> list[SearchResult]:
        """
        Search news across RSS feeds. If query is empty, returns latest headlines.

        Args:
            query: Search keyword to filter articles (case-insensitive).
                   If empty/blank, returns all headlines.
            max_results: Maximum articles per feed.
            feeds: Specific feeds to query (list of feed names or "all").
            category: Filter by category (news, business, technology).
            hours: Only include articles from the last N hours.

        Returns:
            List of SearchResult objects sorted by date (newest first).
        """
        feeds_to_query = self._select_feeds(
            feed_names=kwargs.get("feeds", "all"),
            category=kwargs.get("category"),
        )

        results = []
        for feed_name, feed_info in feeds_to_query.items():
            try:
                response = await self._client.get(feed_info["url"])
                response.raise_for_status()

                parsed = self._parse_feed(response.text, feed_name, feed_info)
                for article in parsed:
                    # Filter by keyword if query provided
                    if query:
                        q = query.lower()
                        if q in article.title.lower() or q in article.snippet.lower():
                            results.append(article)
                    else:
                        results.append(article)

            except httpx.HTTPError as e:
                logger.warning(f"RSS feed '{feed_name}' failed: {e}")
                continue

        # Apply time filter
        hours = kwargs.get("hours")
        if hours:
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc) - timedelta(hours=int(hours))
            results = [r for r in results if r.extra.get("parsed_date", datetime.max.replace(tzinfo=timezone.utc)) >= cutoff]

        # Sort by date (newest first), limit results
        results.sort(key=lambda r: r.extra.get("parsed_date", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        return results[:max_results * max(1, len(feeds_to_query))]

    def _select_feeds(self, feed_names="all", category=None):
        """Select feeds based on filters."""
        if feed_names != "all":
            if isinstance(feed_names, str):
                feed_names = [feed_names]
            return {k: v for k, v in RSS_FEEDS.items() if k in feed_names}

        if category:
            return {k: v for k, v in RSS_FEEDS.items() if v.get("category") == category}

        return RSS_FEEDS

    def _parse_feed(self, xml_text: str, feed_name: str, feed_info: dict) -> list[SearchResult]:
        """Parse RSS/Atom XML into SearchResult objects."""
        results = []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"Failed to parse RSS from {feed_name}: {e}")
            return []

        # Detect RSS vs Atom format
        if root.tag == "rss":
            return self._parse_rss(root, feed_name, feed_info)
        elif root.tag.endswith("feed"):
            return self._parse_atom(root, feed_name, feed_info)
        else:
            logger.warning(f"Unknown feed format for {feed_name}: {root.tag}")
            return results

    def _parse_rss(self, root: ET.Element, feed_name: str, feed_info: dict) -> list[SearchResult]:
        """Parse RSS 2.0 format."""
        results = []
        namespaces = {"content": "http://purl.org/rss/1.0/modules/content/"}

        for i, item in enumerate(root.findall(".//item")):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            description = item.findtext("description", "")
            pub_date_str = item.findtext("pubDate", "")
            creator = item.findtext("dc:creator", "") or item.findtext("author", "")

            # Clean up description (remove HTML tags)
            import re
            snippet = re.sub(r"<[^>]+>", "", description).strip()
            # Truncate
            snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet

            # Parse date
            parsed_date = self._parse_date(pub_date_str)

            results.append(
                SearchResult(
                    title=title,
                    url=link,
                    snippet=snippet,
                    source=feed_name,
                    rank=i + 1,
                    category=feed_info.get("category", "news"),
                    extra={
                        "feed_name": feed_name,
                        "author": creator,
                        "published": pub_date_str,
                        "parsed_date": parsed_date,
                        "feed_url": feed_info["url"],
                    },
                )
            )

        return results

    def _parse_atom(self, root: ET.Element, feed_name: str, feed_info: dict) -> list[SearchResult]:
        """Parse Atom format."""
        results = []
        ns = {"a": "http://www.w3.org/2005/Atom"}

        feed_title = root.findtext("a:title", "", ns)

        for i, entry in enumerate(root.findall("a:entry", ns)):
            title = entry.findtext("a:title", "", ns)
            link_el = entry.find("a:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            summary = entry.findtext("a:summary", "", ns) or entry.findtext("a:content", "", ns)
            published = entry.findtext("a:published", "", ns) or entry.findtext("a:updated", "", ns)
            author = entry.findtext("a:author/a:name", "", ns)

            import re
            snippet = re.sub(r"<[^>]+>", "", summary).strip()
            snippet = snippet[:300] + "..." if len(snippet) > 300 else snippet

            parsed_date = self._parse_date(published)

            results.append(
                SearchResult(
                    title=title,
                    url=link,
                    snippet=snippet,
                    source=feed_name,
                    rank=i + 1,
                    category=feed_info.get("category", "news"),
                    extra={
                        "feed_name": feed_name,
                        "author": author,
                        "published": published,
                        "parsed_date": parsed_date,
                        "feed_url": feed_info["url"],
                    },
                )
            )

        return results

    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats to datetime."""
        if not date_str:
            return datetime.min.replace(tzinfo=timezone.utc)

        formats = [
            "%a, %d %b %Y %H:%M:%S %z",     # RSS: Sat, 01 Jan 2024 12:00:00 +0000
            "%a, %d %b %Y %H:%M:%S %Z",     # RSS with timezone name
            "%Y-%m-%dT%H:%M:%S%z",          # Atom ISO 8601
            "%Y-%m-%dT%H:%M:%S.%f%z",       # Atom with microseconds
            "%Y-%m-%dT%H:%M:%SZ",           # Atom UTC
            "%Y-%m-%d",                      # Simple date
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue

        return datetime.min.replace(tzinfo=timezone.utc)

    async def close(self):
        await self._client.aclose()
