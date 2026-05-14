#!/usr/bin/env python3
"""
Web Search Skills CLI.

Usage:
    web-search <command> <query> [options]

Commands:
    search       Search all sources (default)
    web          Web search engines
    news         News (CLS, WallStreetCN, RSS)
    wechat       WeChat public account articles
    academic     Academic papers (ArXiv)
    social       Social media (Twitter/X)
    rss          RSS news feeds
    sources      List all available sources
    urls         Get search URLs without executing
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

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_SCRIPT_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("cli")

def _get_unified():
    from scripts.unified_search import UnifiedSearch
    return UnifiedSearch

def _get_sogou():
    from scripts.wechat.sogou_weixin import SogouWeChatEngine
    return SogouWeChatEngine

def _get_config_loader():
    from scripts.core.config_loader import get_search_engines, get_news_sources, get_academic_sources, get_wechat_sources, get_social_sources, get_special_engines, get_all_sources, list_source_categories
    return {"get_search_engines": get_search_engines, "get_news_sources": get_news_sources, "get_academic_sources": get_academic_sources, "get_wechat_sources": get_wechat_sources, "get_social_sources": get_social_sources, "get_special_engines": get_special_engines, "get_all_sources": get_all_sources, "list_source_categories": list_source_categories}

def _format_result(r):
    lines = [f"[{r.rank}] {r.title}", f"    URL: {r.url}"]
    if r.snippet:
        lines.append(f"    {r.snippet[:200]}")
    if r.extra:
        parts = []
        for k, v in r.extra.items():
            if k == "account" and v: parts.append(f"公众号: {v}")
            elif k == "time" and v: parts.append(f"时间: {v}")
            elif k == "search_url" or k in ("parsed_date", "note", "feed_url"): continue
            elif v: parts.append(f"{k}: {v}")
        if parts: lines.append(f"    ({'; '.join(parts)})")
    return "\n".join(lines)

def _print_results(results):
    if not results:
        print("  未找到结果"); return
    for r in results:
        print(_format_result(r)); print()

async def _search_all(query, max_results=10, **kw):
    us = _get_unified()()
    try: return await us.search(query, max_results=max_results, **kw)
    finally: await us.close()

async def _search_web(query, max_results=10, region=None):
    us = _get_unified()()
    try: return await us.search_engines(query, region=region, max_results=max_results)
    finally: await us.close()

async def _search_news(query, max_results=10, **kw):
    us = _get_unified()()
    try: return await us.search_news(query, max_results=max_results, **kw)
    finally: await us.close()

async def _search_wechat(query, max_results=10):
    engine = _get_sogou()()
    try: return await engine.search(query, max_results=max_results)
    finally: await engine.close()

async def _search_academic(query, max_results=10):
    us = _get_unified()();
    try: return await us.search_academic(query, max_results=max_results)
    finally: await us.close()

async def _search_social(query, max_results=10, **kw):
    us = _get_unified()();
    try: return await us.search_social(query, max_results=max_results, **kw)
    finally: await us.close()

async def _search_rss(query, max_results=10, **kw):
    us = _get_unified()();
    try: return await us.search_rss(query, max_results=max_results, **kw)
    finally: await us.close()

async def _get_urls(query, sources=None):
    us = _get_unified()()
    try: return await us.get_search_urls(query, sources=sources)
    finally: await us.close()

def cmd_sources(args):
    cl = _get_config_loader()
    cats = cl["list_source_categories"]()
    print("可用搜索源:\n")
    for k, n in [("search_engines","Web 搜索引擎"),("news_sources","新闻源"),("academic_sources","学术源"),("wechat_sources","微信源"),("social_sources","社交源"),("special_engines","特殊源")]:
        c = cats.get(k,0)
        if c: print(f"  {n} ({c} 个)")
    print(f"\n总计: {len(cl['get_all_sources']())} 个源\n")
    for s in cl["get_all_sources"]():
        print(f"  - {s['name']:20s}  ({s.get('region','?')})  [{s.get('type','url')}]")

def cmd_urls(args):
    urls = asyncio.run(_get_urls(args.query, sources=args.source))
    for name, url in urls.items():
        print(f"{name}:\n    {url}\n")

async def _run_search(args):
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    fn = {"search":_search_all,"web":_search_web,"news":_search_news,"wechat":_search_wechat,"academic":_search_academic,"social":_search_social,"rss":_search_rss}.get(args.command,_search_all)
    kw = {}
    if args.command == "web" and args.region: kw["region"] = args.region
    try:
        results = await fn(args.query, max_results=args.max_results, **kw)
    except Exception as e:
        print(f"搜索失败: {e}", file=sys.stderr); sys.exit(1)
    names = {"search":"全源搜索","web":"网页搜索","news":"新闻搜索","wechat":"微信公众号搜索","academic":"学术搜索","social":"社交搜索","rss":"RSS 新闻搜索"}
    print(f"{names.get(args.command,'搜索')}: {args.query}")
    print(f"共 {len(results)} 条结果\n")
    if args.json:
        print(json.dumps([{"rank":r.rank,"title":r.title,"url":r.url,"snippet":r.snippet[:300],"source":r.source,"category":r.category,"extra":dict(r.extra) if r.extra else {}} for r in results], ensure_ascii=False, indent=2))
    else:
        _print_results(results)
    if args.output:
        data = json.dumps([{"query":args.query,"command":args.command,"timestamp":datetime.now().isoformat(),"total":len(results),"results":[{"rank":r.rank,"title":r.title,"url":r.url,"snippet":r.snippet[:500],"source":r.source,"category":r.category,"extra":dict(r.extra) if r.extra else {}} for r in results]}], ensure_ascii=False, indent=2)
        with open(os.path.abspath(args.output),"w",encoding="utf-8") as f: f.write(data)
        print(f"\n结果已保存至: {os.path.abspath(args.output)}")

def build_parser():
    p = argparse.ArgumentParser(prog="web-search", description="Web Search Skills CLI", formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("command", nargs="?", default="search", choices=["search","web","news","wechat","academic","social","rss","sources","urls"], help="Search type")
    p.add_argument("query", nargs="?", default="", help="Search keyword")
    p.add_argument("-n","--max-results", type=int, default=10, help="Max results per source")
    p.add_argument("-j","--json", action="store_true", help="JSON output")
    p.add_argument("-o","--output", type=str, help="Save to JSON file")
    p.add_argument("-s","--source", type=str, nargs="*", help="Specific source name(s)")
    p.add_argument("-r","--region", type=str, choices=["cn","global"], help="Region filter")
    p.add_argument("-v","--verbose", action="store_true", help="Debug logs")
    return p

def main():
    args = build_parser().parse_args()
    if args.command == "sources": cmd_sources(args); return
    if args.command == "urls":
        if not args.query: print("错误: urls 需要搜索关键词", file=sys.stderr); sys.exit(1)
        cmd_urls(args); return
    if not args.query: print(f"错误: {args.command} 需要搜索关键词", file=sys.stderr); sys.exit(1)
    asyncio.run(_run_search(args))

if __name__ == "__main__":
    main()
