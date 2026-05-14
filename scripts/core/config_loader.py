"""Load and manage engine configuration from engines.json."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "config", "engines.json",
)


def _load_config(path: Optional[str] = None) -> dict[str, Any]:
    config_path = path or _CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_search_engines(path: Optional[str] = None) -> list[dict[str, Any]]:
    return _load_config(path).get("search_engines", [])


def get_news_sources(path: Optional[str] = None) -> list[dict[str, Any]]:
    return _load_config(path).get("news_sources", [])


def get_academic_sources(path: Optional[str] = None) -> list[dict[str, Any]]:
    return _load_config(path).get("academic_sources", [])


def get_wechat_sources(path: Optional[str] = None) -> list[dict[str, Any]]:
    return _load_config(path).get("wechat_sources", [])


def get_social_sources(path: Optional[str] = None) -> list[dict[str, Any]]:
    return _load_config(path).get("social_sources", [])


def get_api_engines(path: Optional[str] = None) -> list[dict[str, Any]]:
    """Get API-based search engines (Baidu Qianfan, etc.)."""
    return _load_config(path).get("api_engines", [])


def get_special_engines(path: Optional[str] = None) -> list[dict[str, Any]]:
    return _load_config(path).get("special_engines", [])


def get_engine(name: str, path: Optional[str] = None):
    config = _load_config(path)
    for category in ["search_engines", "news_sources", "academic_sources",
                      "wechat_sources", "social_sources", "api_engines",
                      "special_engines"]:
        for engine in config.get(category, []):
            if engine["name"].lower() == name.lower():
                return engine
    return None


def get_all_sources(path: Optional[str] = None) -> list[dict[str, Any]]:
    config = _load_config(path)
    all_sources = []
    for category in ["search_engines", "news_sources", "academic_sources",
                      "wechat_sources", "social_sources", "api_engines",
                      "special_engines"]:
        all_sources.extend(config.get(category, []))
    return all_sources

def list_source_categories(path: Optional[str] = None) -> dict[str, int]:
    """Return a dict mapping category name to count of sources."""
    config = _load_config(path)
    categories = [
        "search_engines", "news_sources", "academic_sources",
        "wechat_sources", "social_sources", "api_engines",
        "special_engines",
    ]
    return {cat: len(config.get(cat, [])) for cat in categories}
