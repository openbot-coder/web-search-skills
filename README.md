# Web Search Skills

Multi-source web search CLI tool — search across **28 engines** from your terminal: web search, news, WeChat articles, academic papers, social media, RSS feeds, and AI-powered Baidu search.

## Quick Start

```bash
# Option 1: pip install (recommended for CodeBuddy Agent use)
cd web-search-skills
pip install -e .

# Option 2: uv tool install (alternative)
uv tool install -e .

# Now use globally from anywhere
web-search wechat 蒙面财经
web-search news "AI" -n 5
web-search search "量子计算" -o results.json
```

Or run directly without install:
```bash
python ws.py wechat 蒙面财经
```

> Requires Python 3.8+. After `pip install -e .`, the `web-search` command is available globally.

## Usage

```bash
web-search <command> <query> [options]
```

| Command    | Description                                         |
|------------|-----------------------------------------------------|
| `search`   | Search 28 sources in parallel (default)             |
| `web`      | Web search engines (Google, Baidu, DDG, Yahoo…)     |
| `news`     | News (Hacker News, GitHub Trending, 36氪, RSS…)     |
| `baidu`    | AI-powered Baidu search (site/recency filters)      |
| `wechat`   | WeChat public account articles (via Sogou)          |
| `academic` | Academic papers (ArXiv)                             |
| `social`   | Social media (Twitter/X)                            |
| `rss`      | RSS feeds (AI newsletters, essays, podcasts…)       |
| `health`   | Test connectivity of all 28 engines (concurrent)    |
| `sources`  | List all available search sources                   |
| `urls`     | Generate search URLs without executing              |

### Options

| Flag              | Description                                  |
|-------------------|----------------------------------------------|
| `-n N`            | Max results per source (default: 10)         |
| `-j`              | JSON output                                  |
| `-o FILE`         | Save to JSON file (path restricted to current directory) |
| `-s NAME [...]`   | Specific source(s) — engine names or categories (e.g. `-s "Hacker News" V2EX`, `-s web news`) |
| `-r cn/global`    | Region filter (web search)                   |
| `--site SITE`     | Restrict to site (baidu command only)        |
| `--recency RECENCY` | Time filter: day/week/month/semiyear/year  |
| `-v`              | Verbose/debug logs                           |

### Examples

```bash
# Search specific engines concurrently (new!)
web-search search "technology" -s "Hacker News" "V2EX" "GitHub Trending" -n 3

# Search two categories concurrently (new!)
web-search search "AI" -s web news -n 3

# Baidu with site & recency filters
web-search baidu "中美元首会晤" --site mp.weixin.qq.com --recency week

# Quick search
web-search news "人工智能" -n 5
web-search wechat 蒙面财经
web-search academic "quantum computing"
web-search search "latest AI news" -o results.json

# Check engine health (concurrent, ~14s for 28 engines)
web-search health
```

## Sources (28 engines)

| Category | Sources | Count |
|----------|---------|-------|
| **Web** | Baidu, Bing CN, Bing INT, 360, Sogou, Shenma, Google, Google HK, DuckDuckGo, Yahoo, Startpage, Brave, Ecosia, Qwant | 14 |
| **News (CN)** | 财联社, 华尔街见闻, 36氪, 微博热搜, V2EX, 腾讯新闻 | 6 |
| **News (Global)** | Hacker News, GitHub Trending | 2 |
| **RSS** | Reuters, AP, BBC, FT, CNN, Al Jazeera + AI newsletters (Latent Space, ChinAI, KDnuggets…), essays (Paul Graham, James Clear…), podcasts (Lex Fridman…) | 18 |
| **Academic** | ArXiv | 1 |
| **WeChat** | Sogou WeChat | 1 |
| **Social** | Twitter, Twitter Latest | 2 |
| **API** | Baidu Qianfan (AI search with site/recency) | 1 |
| **Special** | WolframAlpha | 1 |

## Project Structure

```
web-search-skills/
├── scripts/
│   ├── cli.py                   # CLI entry point
│   ├── unified_search.py        # Unified search orchestrator (async + concurrent)
│   ├── core/
│   │   ├── base.py              # SearchResult & SearchEngine base class
│   │   ├── config_loader.py     # Load engine config from JSON
│   │   └── thread_utils.py      # Shared thread pool for HTML parsing
│   ├── engines/
│   │   ├── url_engine.py        # URL-template search engines
│   │   ├── parser_engines.py    # HTML-parsed search (DuckDuckGo)
│   │   └── baidu_qianfan.py     # Baidu Qianfan AI Search API
│   ├── news/
│   │   ├── cls.py               # 财联社
│   │   ├── wallstreetcn.py      # 华尔街见闻
│   │   ├── rss.py               # RSS feeds (18 sources)
│   │   └── tech_news.py         # Tech news engines (Hacker News, GitHub Trending, 36氪, etc.)
│   ├── academic/
│   │   └── arxiv.py             # ArXiv papers
│   ├── wechat/
│   │   └── sogou_weixin.py      # Sogou WeChat search
│   └── social/
│       └── twitter.py           # Twitter/X search
├── config/
│   └── engines.json             # Search engine definitions
├── ws.py                        # Direct run entry point
├── pyproject.toml               # Package config
├── SKILL.md                     # CodeBuddy skill definition
├── LICENSE
└── README.md
```

## Python API

```python
from scripts.unified_search import UnifiedSearch

async def main():
    us = UnifiedSearch()
    # Search specific sources concurrently
    results = await us.search("quantum computing",
                              sources=["Hacker News", "ArXiv"],
                              max_results=5)
    for r in results:
        print(f"[{r.rank}] {r.title}: {r.url}")
    await us.close()
```

## Performance

- **Concurrent engine execution**: All 28 engines run in parallel via `asyncio.gather`, with `Semaphore(5)` for gentle concurrency
- **Health check**: 28 engines checked in ~14 seconds (vs ~84s without concurrency)
- **Thread pool**: HTML parsing offloaded to `ThreadPoolExecutor` via `scripts/core/thread_utils.py`, preventing event loop blocking
- **Timeout**: 15s per engine timeout prevents hanging

## Notes

- Sogou WeChat has anti-scraping limits, may return empty results
- 财联社 and 华尔街见闻 require JavaScript rendering; `UnifiedSearch` returns search page links for these
- RSS feeds require stable network connectivity
- Baidu Qianfan requires `BAIDU_API_KEY` environment variable

## License

MIT
