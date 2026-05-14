"""RSS news aggregation engine. Fetches and parses RSS/Atom feeds."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

import httpx

from scripts.core.base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "BBC World": {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "category": "news", "lang": "en"},
    "BBC Top Stories": {"url": "https://feeds.bbci.co.uk/news/rss.xml", "category": "news", "lang": "en"},
    "BBC Business": {"url": "https://feeds.bbci.co.uk/news/business/rss.xml", "category": "business", "lang": "en"},
    "BBC Technology": {"url": "https://feeds.bbci.co.uk/news/technology/rss.xml", "category": "technology", "lang": "en"},
    "Reuters": {"url": "https://www.reutersagency.com/feed/?best-regions=world&post_type=best", "category": "news", "lang": "en"},
    "NPR": {"url": "https://feeds.npr.org/1001/rss.xml", "category": "news", "lang": "en"},
    "Al Jazeera": {"url": "https://www.aljazeera.com/xml/rss/all.xml", "category": "news", "lang": "en"},
}


class RSSNewsEngine(SearchEngine):
    """RSS-based news aggregation engine."""

    def __init__(self, config: Optional[dict] = None):
        super().__init__("RSS News", config)
        self._client = httpx.AsyncClient(timeout=30,
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/rss+xml, application/xml, text/xml"},
            follow_redirects=True)

    def build_url(self, query: str, **kwargs) -> str:
        feed_name = kwargs.get("feed", "BBC World")
        return RSS_FEEDS.get(feed_name, RSS_FEEDS["BBC World"])["url"]

    async def search(self, query: str = "", max_results: int = 10, **kwargs) -> list[SearchResult]:
        feeds_to_query = self._select_feeds(kwargs.get("feeds", "all"), kwargs.get("category"))
        results = []
        for feed_name, feed_info in feeds_to_query.items():
            try:
                response = await self._client.get(feed_info["url"])
                response.raise_for_status()
                parsed = self._parse_feed(response.text, feed_name, feed_info)
                for article in parsed:
                    if query:
                        q = query.lower()
                        if q in article.title.lower() or q in article.snippet.lower():
                            results.append(article)
                    else:
                        results.append(article)
            except httpx.HTTPError as e:
                logger.warning(f"RSS '{feed_name}' failed: {e}")
        hours = kwargs.get("hours")
        if hours:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=int(hours))
            results = [r for r in results if r.extra.get("parsed_date", datetime.max.replace(tzinfo=timezone.utc)) >= cutoff]
        results.sort(key=lambda r: r.extra.get("parsed_date", datetime.min.replace(tzinfo=timezone.utc)), reverse=True)
        return results[:max_results * max(1, len(feeds_to_query))]

    def _select_feeds(self, feed_names="all", category=None):
        if feed_names != "all":
            names = [feed_names] if isinstance(feed_names, str) else feed_names
            return {k: v for k, v in RSS_FEEDS.items() if k in names}
        if category:
            return {k: v for k, v in RSS_FEEDS.items() if v.get("category") == category}
        return RSS_FEEDS

    def _parse_feed(self, xml_text: str, feed_name: str, feed_info: dict) -> list[SearchResult]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.error(f"Parse error {feed_name}: {e}")
            return []
        if root.tag == "rss":
            return self._parse_rss(root, feed_name, feed_info)
        elif "feed" in root.tag:
            return self._parse_atom(root, feed_name, feed_info)
        return []

    def _parse_rss(self, root, feed_name, feed_info):
        results = []
        for i, item in enumerate(root.findall(".//item")):
            title = item.findtext("title", "")
            link = item.findtext("link", "")
            desc = item.findtext("description", "")
            pub = item.findtext("pubDate", "")
            snippet = re.sub(r"<[^>]+>", "", desc).strip()[:300]
            if len(snippet) == 300: snippet += "..."
            results.append(SearchResult(title=title, url=link, snippet=snippet,
                source=feed_name, rank=i+1, category=feed_info.get("category", "news"),
                extra={"feed_name": feed_name, "published": pub, "parsed_date": self._parse_date(pub)}))
        return results

    def _parse_atom(self, root, feed_name, feed_info):
        results = []
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for i, entry in enumerate(root.findall("a:entry", ns)):
            title = entry.findtext("a:title", "", ns)
            link_el = entry.find("a:link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            summary = entry.findtext("a:summary", "", ns) or entry.findtext("a:content", "", ns)
            published = entry.findtext("a:published", "", ns) or entry.findtext("a:updated", "", ns)
            snippet = re.sub(r"<[^>]+>", "", summary).strip()[:300]
            if len(snippet) == 300: snippet += "..."
            results.append(SearchResult(title=title, url=link, snippet=snippet,
                source=feed_name, rank=i+1, category=feed_info.get("category", "news"),
                extra={"feed_name": feed_name, "published": published, "parsed_date": self._parse_date(published)}))
        return results

    def _parse_date(self, date_str: str) -> datetime:
        if not date_str:
            return datetime.min.replace(tzinfo=timezone.utc)
        for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z",
                     "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"]:
            try:
                return datetime.strptime(date_str.strip(), fmt).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                continue
        return datetime.min.replace(tzinfo=timezone.utc)

    async def close(self):
        await self._client.aclose()
