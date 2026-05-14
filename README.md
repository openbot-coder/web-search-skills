# Web Search Skills

Multi-source web search CLI tool — search across 20+ engines from your terminal.

## Quick Start

```bash
# Install with uv (recommended)
cd web-search-skills
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

## Usage

```bash
web-search <command> <query> [options]
```

| Command    | Description                              |
|------------|------------------------------------------|
| `search`   | Search all sources (default)             |
| `web`      | Web search engines (Google, Baidu, DDG)  |
| `news`     | News (财联社, 华尔街见闻, RSS)           |
| `wechat`   | WeChat public account articles           |
| `academic` | Academic papers (ArXiv)                  |
| `social`   | Social media (Twitter/X)                 |
| `rss`      | RSS news feeds                           |
| `sources`  | List all available search sources        |
| `urls`     | Generate search URLs without executing   |

Options:

| Flag | Description |
|------|-------------|
| `-n N` | Max results per source (default: 10) |
| `-j` | JSON output |
| `-o FILE` | Save to JSON file |
| `-s NAME` | Specific source name(s) |
| `-r cn/global` | Region filter (web search) |
| `-v` | Verbose/debug logs |

## Project Structure

```
web-search-skills/
├── scripts/
│   ├── cli.py                   # CLI entry point
│   ├── unified_search.py        # Unified search orchestrator
│   ├── core/
│   │   ├── base.py              # SearchResult & SearchEngine base class
│   │   └── config_loader.py     # Load engine config from JSON
│   ├── engines/
│   │   ├── url_engine.py        # URL-template search engines
│   │   └── parser_engines.py    # HTML-parsed search (DuckDuckGo)
│   ├── news/
│   │   ├── cls.py               # 财联社
│   │   ├── wallstreetcn.py      # 华尔街见闻
│   │   └── rss.py               # RSS feeds
│   ├── academic/
│   │   └── arxiv.py             # ArXiv papers
│   ├── wechat/
│   │   └── sogou_weixin.py      # WeChat (via Sogou)
│   └── social/
│       └── twitter.py           # Twitter/X
├── config/
│   └── engines.json             # Search engine definitions
├── ws.py                        # Direct run entry point
├── pyproject.toml               # Package config
├── SKILL.md                     # CodeBuddy skill definition
├── LICENSE
└── README.md
```

## License

MIT
