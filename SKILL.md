---
name: web-search-skills
description: "Multi-source web search CLI & library, covering web, news, WeChat, academic, social, and RSS feeds across 28 engines. Use when the user asks to search the web, find WeChat articles, look up news, search academic papers, or check social media."
version: 2.2.0
license: MIT
compatibility: Requires Python 3.8+, httpx, beautifulsoup4, lxml
metadata:
  author: openbot-coder
  category: development
  tags: [search, web, wechat, news, academic, social, rss, cli, concurrent]
---

# Web Search Skills

## Overview

A CLI (`web-search`) and Python library that queries **28 search engines** concurrently via `asyncio.gather`. Supports web search, news (Hacker News, GitHub Trending, 36氪, 微博热搜, V2EX, RSS feeds), WeChat articles, ArXiv papers, Twitter/X, and Baidu Qianfan AI search.

All engines run in parallel with `Semaphore(5)` concurrency control and 15s per-engine timeout.

## Triggers

When the user says any of these, use this skill:

| Intent | Example user phrases |
|--------|---------------------|
| Web search | "搜索一下 xxx", "search the web for xxx" |
| WeChat articles | "搜微信公众号 xxx", "search WeChat for xxx" |
| News | "查一下新闻", "搜索最新的科技新闻", "search news about xxx" |
| Academic | "搜论文 xxx", "search papers about xxx", "查学术资料" |
| Social media | "看看 Twitter 上关于", "check Twitter for xxx" |
| Specific source | "看看 Hacker News 上关于", "what's trending on GitHub" |
| Hot topics | "查一下微博热搜", "check Weibo trending" |

## Agent Decision Tree

Use this flow to pick the right command:

```
用户说了什么？
│
├─ "微信公众号" / "WeChat" / 公众号名称
│   → web-search wechat <query>
│
├─ "学术" / "论文" / "paper" / "ArXiv"
│   → web-search academic <query>
│
├─ "Twitter" / "X" / "社交" / "social"
│   → web-search social <query> [-n 5]
│
├─ "新闻" / "news" / 明确指定 RSS/博文/播客
│   → web-search news <query> [-n 5]
│
├─ 明确指定了特定源名称
│   → web-search search <query> -s "源名1" "源名2" [-n 5]
│
├─ 需要多类源对比（如"新闻+社交上关于伊朗的看法"）
│   → web-search search <query> -s news social [-n 10]
│
├─ 需要百度搜索 + 站点/时间过滤
│   → web-search baidu <query> [--site xxx] [--recency week]
│
├─ "健康检查" / "health" / "测试引擎"
│   → web-search health
│
├─ "列出源" / "sources" / "有哪些搜索引擎"
│   → web-search sources
│
├─ 其余通用查询
│   → web-search search <query> [-s 源1 源2...] [-n 10]
│
└─ 不确定 / 没特别要求
    → web-search search <query> -n 10
```

## Quick Command Reference

| Command | Speed | Best for |
|---------|-------|----------|
| `search` | 并发 28 源 | 通用搜索、多源对比 |
| `web` | 14 网页引擎 | 普通网页搜索 |
| `baidu` | 单引擎 | 需 site/recency 过滤 |
| `news` | ~10+ 新闻源 | 科技/财经/博客/播客 |
| `wechat` | 单引擎 | 微信公众号独家内容 |
| `academic` | 单引擎 | 学术论文 |
| `social` | 2 源 (Twitter) | 社交媒体动态 |
| `rss` | 18 订阅源 | AI 周报/深度文章/播客 |
| `health` | 28 源并发 (~14s) | 检测连通性 |

**通用选项：** `-n N`（每源结果数）, `-j`（JSON）, `-o FILE`（存文件）, `-s NAME...`（指定源）, `-v`（调试日志）

## Result Field Reference

Each `SearchResult` returned has these fields:

| Field | Type | Description |
|-------|------|-------------|
| `rank` | int | Position in results (1-based) |
| `title` | str | Article/title text |
| `url` | str | Direct URL to source |
| `snippet` | str | Summary text (first ~300 chars) |
| `source` | str | Engine name (e.g. "Hacker News") |
| `category` | str | "web", "news", "academic", "social", etc. |
| `extra` | dict | Engine-specific metadata (see below) |

### `extra` fields by source

| Source | extra fields |
|--------|-------------|
| Hacker News | `points`, `author`, `time` (ISO date) |
| GitHub Trending | `language`, `stars today` (heat) |
| WeChat | `account` (公众号名), `time` |
| Twitter | `time`, `account`, `search_type` |
| RSS feeds | `time`, `feed_url` |
| Cls / WallStreetCN | `search_url` (JS-rendered fallback) |
| Baidu Qianfan | `site`, `recency` (if filtered) |

## Error Handling

| Symptom | Likely cause | Action |
|---------|-------------|--------|
| Empty results from Hacker News/GitHub | Network issue or no matches | Retry with different query |
| Baidu Qianfan returns nothing | Missing `BAIDU_API_KEY` env | Check env var is set |
| DuckDuckGo times out (15s) | Anti-scraping / rate limit | Note to user, skip |
| WeChat empty results | Sogou anti-scraping | Inform user it may be limited |
| `web-search health` shows [TIMEOUT] | Engine unreachable from this region | Not critical, skip that engine |
| GBK encode error on Windows | Non-ASCII char in output | Already auto-fixed by `_sanitize_for_console` |

**General rule:** If a specific source fails, note it but don't fail the whole search — other sources continue concurrently.

## Usage Examples

```bash
# Full search (all 28 sources, concurrent)
web-search search "quantum computing" -n 10

# Specific sources only
web-search search "technology" -s "Hacker News" "V2EX" "GitHub Trending" -n 3

# Multiple categories
web-search search "Iran nuclear" -s web news social -n 5

# Baidu with site filter
web-search baidu "中美元首会晤" --site mp.weixin.qq.com --recency week

# All web engines
web-search web "Python async" -r global -j

# Quick searches
web-search news "人工智能" -n 5
web-search wechat 蒙面财经
web-search academic "machine learning"
web-search social "AI regulation" -n 5

# Concurrent health check (~14s for 28 engines)
web-search health
```

## Python API (for programmatic use)

> **Tip:** For Agent use, prefer invoking the `web-search` CLI command directly (see examples above).
> The API import below only works when running from the project root directory.

```python
from scripts.unified_search import UnifiedSearch

async def main():
    us = UnifiedSearch()
    results = await us.search(
        "quantum computing",
        sources=["Hacker News", "ArXiv"],
        max_results=5,
    )
    for r in results:
        print(f"[{r.rank}] {r.title} ({r.source})")
        if r.extra:
            print(f"    extra: {r.extra}")
    await us.close()
```

## Important Notes

### Installation
The `web-search` CLI must be installed first before use:
```bash
cd web-search-skills
pip install -e .
```
This registers `web-search` as a global command. Requires Python 3.8+.

### Known Limitations

- **WeChat** via Sogou has anti-scraping limits, may return empty
- **财联社 / 华尔街见闻** need JS rendering → returns search page URL, not parsed results
- **Baidu Qianfan** requires `BAIDU_API_KEY` env var
- **RSS feeds** need stable internet
- **Windows GBK** terminals: special chars auto-replaced by `_sanitize_for_console()`

> Full user-facing documentation (detailed command reference, project structure, config guide, architecture) is in `README.md`.
