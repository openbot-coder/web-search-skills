# Web Search Skills

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A collection of web search tools and skills for AI agents, designed to enhance search capabilities with customizable configurations, multiple search engines support, and intelligent result processing.

## Features

- **Multi-Engine Support** — Built-in support for Google, Bing, DuckDuckGo, and custom search backends
- **Intelligent Result Processing** — Extract, summarize, and rank search results automatically
- **Configurable Filters** — Filter by date, domain, language, region, and content type
- **Async & Concurrent** — Non-blocking requests with concurrent search execution
- **Extensible Architecture** — Plugin-based design for easy integration of new search sources
- **Agent-Ready** — Designed as a CodeBuddy Agent Skill for seamless AI integration

## Getting Started

### Prerequisites

- Python 3.8+
- pip / poetry

### Installation

```bash
git clone https://github.com/openbot-coder/web-search-skills.git
cd web-search-skills
pip install -r requirements.txt
```

### Quick Start

```python
import asyncio
from src.web_search import search_web

results = asyncio.run(search_web("latest AI developments"))
for result in results:
    print(f"- {result.title}: {result.url}")
```

## Project Structure

```
web-search-skills/
├── README.md              # Project documentation
├── LICENSE                # MIT License
├── skill.md               # CodeBuddy Agent Skill definition
├── requirements.txt       # Python dependencies
├── src/                   # Source code
│   └── web_search.py      # Core search implementation
└── examples/              # Usage examples
    └── basic_search.py
```

## Usage

### As a CodeBuddy Agent Skill

This project is designed as a CodeBuddy Agent Skill. To install:

1. Copy `skill.md` to your CodeBuddy skills directory
2. Configure your search engine API keys
3. The skill is now available to your AI agent

### API Reference

```python
# Core class
searcher = WebSearch(config=None)
results = await searcher.search(query, engine="duckduckgo", max_results=10)
content = await searcher.extract_content(url)

# Convenience function
results = await search_web(query, engine="duckduckgo", max_results=10)
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built for the CodeBuddy ecosystem
- Inspired by the need for better web search capabilities in AI agents
