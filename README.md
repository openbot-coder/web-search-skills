# Web Search Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Multi-source web search toolkit for AI agents. Integrates **16+ search engines**, **financial news**, **academic papers**, and **WeChat articles** into a unified search interface.

## Features

- **🔍 16+ Search Engines** — Google, DuckDuckGo, Baidu, Bing, 360, Sogou, Yahoo, Startpage, Brave, Ecosia, Qwant, Shenma + WolframAlpha
- **📰 Financial News** — 财联社 (cls.cn) & 华尔街见闻 (wallstreetcn.com)
- **🎓 Academic Papers** — ArXiv (all scientific categories via official API)
- **💬 WeChat Articles** — 搜狗微信搜索 (wx.sogou.com)
- **🌐 Async & Concurrent** — Non-blocking requests with httpx
- **🔧 Config-Driven** — Add/modify engines via `config/engines.json`
- **🔗 URL Generation** — Get search URLs for browser/web_fetch usage
- **📚 Advanced Operators** — site:, filetype:, intitle:, time filters, privacy search

## Quick Start

```bash
git clone https://github.com/openbot-coder/web-search-skills.git
cd web-search-skills
pip install -r requirements.txt
```

### Python API

```python
import asyncio
from scripts.unified_search import UnifiedSearch

async def main():
    async with UnifiedSearch() as searcher:
        # Search all sources
        results = await searcher.search("AI 大模型")
        for r in results:
            print(f"[{r.source}] {r.title}")

        # Search by category
        news = await searcher.search_news("A股")
        papers = await searcher.search_academic("transformer")
        wechat = await searcher.search_wechat("Python教程")

        # Get search URLs (for browser / web_fetch)
        urls = await searcher.get_search_urls("machine learning")
        print(urls["Google"])

asyncio.run(main())
```

### URL-Based Search

```javascript
web_fetch({"url": "https://www.google.com/search?q=AI+news"})
web_fetch({"url": "https://duckduckgo.com/html/?q=privacy+tools"})
web_fetch({"url": "https://www.baidu.com/s?wd=人工智能"})
```

## Project Structure

```
web-search-skills/
├── SKILL.md                       # CodeBuddy Agent Skill definition
├── README.md                      # This file
├── LICENSE                        # MIT License
├── requirements.txt               # Python dependencies
├── config/
│   └── engines.json               # All engine/source definitions
├── scripts/
│   ├── __init__.py
│   ├── unified_search.py          # Unified search entry point
│   ├── core/
│   │   ├── base.py                # Abstract base + SearchResult
│   │   └── config_loader.py       # Engine config loader
│   ├── engines/
│   │   ├── url_engine.py          # Generic URL-based engine
│   │   └── parser_engines.py      # DuckDuckGo result parser
│   ├── news/
│   │   ├── cls.py                 # 财联社
│   │   └── wallstreetcn.py        # 华尔街见闻
│   ├── academic/
│   │   └── arxiv.py               # ArXiv
│   └── wechat/
│       └── sogou_weixin.py        # 搜狗微信
├── references/
│   └── search-operators.md        # Advanced search operators guide
└── examples/
    └── multi_source_search.py     # Usage examples
```

## Available Sources

| Category | Sources | Count |
|----------|---------|:-----:|
| **Web Engines** | Baidu, Google, DuckDuckGo, Bing CN/INT, 360, Sogou, Yahoo, Startpage, Brave, Ecosia, Qwant, Shenma | 14 |
| **News** | 财联社, 华尔街见闻 | 2 |
| **Academic** | ArXiv | 1 |
| **WeChat** | 搜狗微信 | 1 |
| **Special** | WolframAlpha | 1 |
| **Total** | | **19** |

## API Reference

### UnifiedSearch

```python
class UnifiedSearch:
    async def search(query, sources=["all"], max_results=10, force_refresh=False) -> list[SearchResult]
    async def search_engines(query, region=None, max_results=10) -> list[SearchResult]
    async def search_news(query, max_results=10) -> list[SearchResult]
    async def search_academic(query, max_results=10, field="all") -> list[SearchResult]
    async def search_wechat(query, max_results=10) -> list[SearchResult]
    async def get_search_urls(query, sources=None) -> dict[str, str]
```

### SearchResult

| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Result title |
| `url` | str | Result URL |
| `snippet` | str | Summary/description |
| `source` | str | Engine/source name |
| `rank` | int | Rank position |
| `category` | str | web, news, academic, wechat |
| `extra` | dict | Additional metadata |

## Contributing

Contributions welcome! Add new engines to `config/engines.json`, create new source modules in `scripts/`, and submit a PR.

## License

MIT License — see [LICENSE](LICENSE).
