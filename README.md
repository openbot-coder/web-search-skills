# Web Search Skills

Multi-source web search CLI tool — search across 20+ engines from your terminal.

## Quick Start

```bash
cd web-search-skills
uv tool install -e .

web-search wechat 蒙面财经
web-search news "AI" -n 5
web-search search "量子计算" -o results.json
```

Or run directly:
```bash
python ws.py wechat 蒙面财经
```

## Commands

| Command | Description |
|---------|-------------|
| `search` | Search all sources |
| `web` | Web search engines |
| `news` | News (财联社, 华尔街见闻, RSS) |
| `wechat` | WeChat public account articles |
| `academic` | Academic papers (ArXiv) |
| `social` | Social media (Twitter/X) |
| `rss` | RSS news feeds |
| `sources` | List all available sources |
| `urls` | Generate search URLs without executing |

Options: `-n N`, `-j` (JSON), `-o FILE`, `-s NAME`, `-r cn/global`, `-v`

## Project Structure

```
web-search-skills/
├── scripts/
│   ├── cli.py
│   ├── unified_search.py
│   ├── core/ (base.py, config_loader.py)
│   ├── engines/ (url_engine.py, parser_engines.py)
│   ├── news/ (cls.py, wallstreetcn.py, rss.py)
│   ├── academic/ (arxiv.py)
│   ├── wechat/ (sogou_weixin.py)
│   └── social/ (twitter.py)
├── config/engines.json
├── ws.py
├── pyproject.toml
├── SKILL.md
├── LICENSE
└── README.md
```

## License

MIT
