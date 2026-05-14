#!/usr/bin/env python3
"""
Web Search Skills CLI — search across 20+ sources from the command line.

Usage:
    web-search <command> <query> [options]

Commands:
    search       Search all sources (default)
    web          Search web search engines (Google, Baidu, DuckDuckGo, etc.)
    baidu        Search via Baidu Qianfan AI Search API (需配置 BAIDU_API_KEY)
    news         Search news (财联社, 华尔街见闻, RSS)
    wechat       Search WeChat public account articles (via Sougou)
    academic     Search academic papers (ArXiv)
    social       Search social media (Twitter/X)
    rss          Search RSS news feeds
    health       Test engine connectivity
    sources      List all available sources
    urls         Get search URLs without executing

Options:
    -n, --max-results N    Max results per source (default: 10)
    -j, --json             Output as JSON
    -o, --output FILE      Save results to file
    -s, --source NAME      Specific source name(s)
    -r, --region REGION    Region filter (cn/global)
    --site SITE            Restrict to specific site (baidu command only, e.g. mp.weixin.qq.com)
    --recency RECENCY      Time filter: day, week, month, semiyear, year (baidu command only)
    -v, --verbose          Show debug logs
    -h, --help             Show this help

Examples:
    web-search wechat 蒙面财经
    web-search baidu 今日新闻 --recency week
    web-search baidu "央视新闻 中美元首会晤" --site mp.weixin.qq.com --recency week
    web-search news "人工智能" -n 5
    web-search web "Python async" -r global -j
    web-search search "量子计算" -o results.json
    web-search health
    web-search sources
    web-search urls "机器学习"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any

# Ensure scripts package is importable
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("cli")


# ---------------------------------------------------------------------------
# Lazy engine imports (import on demand to keep startup fast)
# ---------------------------------------------------------------------------

def _get_unified():
    from scripts.unified_search import UnifiedSearch
    return UnifiedSearch


def _get_sogou():
    from scripts.wechat.sogou_weixin import SogouWeChatEngine
    return SogouWeChatEngine


def _get_rss():
    from scripts.news.rss import RSSNewsEngine
    return RSSNewsEngine


def _get_twitter():
    from scripts.social.twitter import TwitterSearchEngine
    return TwitterSearchEngine


def _get_ddg():
    from scripts.engines.parser_engines import DuckDuckGoEngine
    return DuckDuckGoEngine


def _get_config_loader():
    from scripts.core.config_loader import (
        get_search_engines,
        get_news_sources,
        get_academic_sources,
        get_wechat_sources,
        get_social_sources,
        get_special_engines,
        get_all_sources,
        list_source_categories,
    )
    return {
        "get_search_engines": get_search_engines,
        "get_news_sources": get_news_sources,
        "get_academic_sources": get_academic_sources,
        "get_wechat_sources": get_wechat_sources,
        "get_social_sources": get_social_sources,
        "get_special_engines": get_special_engines,
        "get_all_sources": get_all_sources,
        "list_source_categories": list_source_categories,
    }


# ---------------------------------------------------------------------------
# Result formatting
# ---------------------------------------------------------------------------

def _format_result(r, fmt: str = "text") -> str:
    """Format a single SearchResult."""
    if fmt == "json":
        return json.dumps({
            "rank": r.rank,
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet[:300],
            "source": r.source,
            "category": r.category,
            "extra": dict(r.extra) if r.extra else {},
        }, ensure_ascii=False, indent=2)

    lines = [f"[{r.rank}] {r.title}"]
    lines.append(f"    URL: {r.url}")
    if r.snippet:
        lines.append(f"    {r.snippet[:200]}")
    if r.extra:
        extra_parts = []
        for k, v in r.extra.items():
            if k == "account" and v:
                extra_parts.append(f"公众号: {v}")
            elif k == "time" and v:
                extra_parts.append(f"时间: {v}")
            elif k == "search_url":
                continue
            elif v and k not in ("parsed_date", "note", "feed_url"):
                extra_parts.append(f"{k}: {v}")
        if extra_parts:
            lines.append(f"    ({'; '.join(extra_parts)})")
    return "\n".join(lines)


def _print_results(results, fmt: str = "text"):
    """Print search results."""
    if not results:
        print("  未找到结果")
        return

    if fmt == "json":
        output = json.dumps(
            [{
                "rank": r.rank,
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet[:300],
                "source": r.source,
                "category": r.category,
                "extra": dict(r.extra) if r.extra else {},
            } for r in results],
            ensure_ascii=False,
            indent=2,
        )
        print(output)
    else:
        for r in results:
            print(_format_result(r))
            print()


# ---------------------------------------------------------------------------
# Async searchers
# ---------------------------------------------------------------------------

async def _search_all(query: str, max_results: int, **kwargs) -> list[Any]:
    us = _get_unified()()
    try:
        return await us.search(query, max_results=max_results, **kwargs)
    finally:
        await us.close()


async def _search_web(query: str, max_results: int, region: str = None, **kwargs) -> list[Any]:
    us = _get_unified()()
    try:
        return await us.search_engines(query, region=region, max_results=max_results)
    finally:
        await us.close()


async def _search_news(query: str, max_results: int, **kwargs) -> list[Any]:
    us = _get_unified()()
    try:
        return await us.search_news(query, max_results=max_results, **kwargs)
    finally:
        await us.close()


async def _search_wechat(query: str, max_results: int) -> list[Any]:
    engine = _get_sogou()()
    try:
        return await engine.search(query, max_results=max_results)
    finally:
        await engine.close()


async def _search_academic(query: str, max_results: int) -> list[Any]:
    us = _get_unified()()
    try:
        return await us.search_academic(query, max_results=max_results)
    finally:
        await us.close()


async def _search_social(query: str, max_results: int, **kwargs) -> list[Any]:
    us = _get_unified()()
    try:
        return await us.search_social(query, max_results=max_results, **kwargs)
    finally:
        await us.close()


async def _search_baidu(query: str, max_results: int, **kwargs) -> list[Any]:
    from scripts.engines.baidu_qianfan import BaiduQianFanEngine
    engine = BaiduQianFanEngine({"api_key": os.getenv("BAIDU_API_KEY", "")})
    try:
        return await engine.search(query, max_results=max_results, **kwargs)
    finally:
        await engine.close()


async def _search_rss(query: str, max_results: int, **kwargs) -> list[Any]:
    us = _get_unified()()
    try:
        return await us.search_rss(query, max_results=max_results, **kwargs)
    finally:
        await us.close()


async def _get_urls(query: str, sources: list[str] = None) -> dict[str, str]:
    us = _get_unified()()
    try:
        return await us.get_search_urls(query, sources=sources)
    finally:
        await us.close()


# ---------------------------------------------------------------------------
# CLI actions
# ---------------------------------------------------------------------------

def cmd_sources(args):
    """List all available search sources."""
    cl = _get_config_loader()
    categories = cl["list_source_categories"]()

    print("可用搜索源:\n")
    for cat_key, cat_name in [
        ("search_engines", "Web 搜索引擎"),
        ("news_sources", "新闻源"),
        ("academic_sources", "学术源"),
        ("wechat_sources", "微信源"),
        ("social_sources", "社交源"),
        ("api_engines", "API 引擎"),
        ("special_engines", "特殊源"),
    ]:
        count = categories.get(cat_key, 0)
        if count == 0:
            continue
        print(f"  {cat_name} ({count} 个)")

    print(f"\n总计: {cl['get_all_sources']().__len__()} 个源")
    print("\n详细列表:")
    for s in cl["get_all_sources"]():
        print(f"  - {s['name']:20s}  ({s.get('region', '?')})  [{s.get('type', 'url')}]")


def cmd_urls(args):
    """Get search URLs without executing."""
    urls = asyncio.run(_get_urls(args.query, sources=args.source))
    for name, url in urls.items():
        print(f"{name}:")
        print(f"    {url}")
        print()


async def cmd_health(args):
    """Test all engine connectivity."""
    us = _get_unified()()
    try:
        print("正在检测各引擎连通性...\n")
        statuses = await us.search_health()
        ok_count = sum(1 for s in statuses if s["status"] == "ok")
        for s in statuses:
            if s["status"] == "ok":
                print(f"  [OK]  {s['name']}")
            elif s["status"] == "timeout":
                print(f"  [TIMEOUT]  {s['name']}")
            else:
                detail = s.get("detail", "")
                print(f"  [FAIL]  {s['name']}  {detail}")
        print(f"\n总计: {len(statuses)} 个引擎, {ok_count} 个可用")
    finally:
        await us.close()


async def _run_search(args):
    """Route search to the right engine(s)."""
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    method_map = {
        "search": _search_all,
        "web": _search_web,
        "baidu": _search_baidu,
        "news": _search_news,
        "wechat": _search_wechat,
        "academic": _search_academic,
        "social": _search_social,
        "rss": _search_rss,
    }

    search_fn = method_map.get(args.command, _search_all)

    kwargs = {}
    if args.command == "web" and args.region:
        kwargs["region"] = args.region
    if args.command == "baidu":
        if args.site:
            kwargs["site"] = args.site
        if args.recency:
            kwargs["recency"] = args.recency

    try:
        results = await search_fn(
            args.query,
            max_results=args.max_results,
            **kwargs,
        )
    except Exception as e:
        print(f"搜索失败: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Print header
    cmd_names = {
        "search": "全源搜索",
        "web": "网页搜索",
        "baidu": "百度千帆 AI 搜索",
        "news": "新闻搜索",
        "wechat": "微信公众号搜索",
        "academic": "学术搜索",
        "social": "社交搜索",
        "rss": "RSS 新闻搜索",
    }
    header = cmd_names.get(args.command, "搜索")
    print(f"{header}: {args.query}")
    print(f"共 {len(results)} 条结果\n")

    _print_results(results, fmt="json" if args.json else "text")

    # Save to file if requested
    if args.output:
        output_data = json.dumps(
            [{
                "query": args.query,
                "command": args.command,
                "timestamp": datetime.now().isoformat(),
                "total": len(results),
                "results": [
                    {
                        "rank": r.rank,
                        "title": r.title,
                        "url": r.url,
                        "snippet": r.snippet[:500],
                        "source": r.source,
                        "category": r.category,
                        "extra": dict(r.extra) if r.extra else {},
                    }
                    for r in results
                ],
            }],
            ensure_ascii=False,
            indent=2,
        )
        output_path = os.path.abspath(args.output)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_data)
        print(f"\n结果已保存至: {output_path}")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="web-search",
        description="Web Search Skills CLI — multi-source search tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="search",
        choices=["search", "web", "baidu", "news", "wechat", "academic",
                 "social", "rss", "health", "sources", "urls"],
        help="Search type (default: search)",
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="",
        help="Search keyword",
    )
    parser.add_argument(
        "-n", "--max-results",
        type=int,
        default=10,
        help="Max results per source (default: 10)",
    )
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Save results to JSON file",
    )
    parser.add_argument(
        "-s", "--source",
        type=str,
        nargs="*",
        help="Specific source name(s)",
    )
    parser.add_argument(
        "-r", "--region",
        type=str,
        choices=["cn", "global"],
        help="Region filter (web search only)",
    )
    parser.add_argument(
        "--site",
        type=str,
        help="Restrict to specific site (baidu command only, e.g. mp.weixin.qq.com)",
    )
    parser.add_argument(
        "--recency",
        type=str,
        choices=["day", "week", "month", "semiyear", "year"],
        default=None,
        help="Time filter (baidu command only, default: year)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show debug logs",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # sources, urls, health don't need a query
    if args.command == "sources":
        cmd_sources(args)
        return

    if args.command == "health":
        asyncio.run(cmd_health(args))
        return

    if args.command == "urls":
        if not args.query:
            print("错误: urls 命令需要提供搜索关键词", file=sys.stderr)
            sys.exit(1)
        cmd_urls(args)
        return

    # Other commands need a query
    if not args.query:
        print(f"错误: {args.command} 命令需要提供搜索关键词", file=sys.stderr)
        sys.exit(1)

    asyncio.run(_run_search(args))


if __name__ == "__main__":
    main()
