"""Load and manage engine configuration from engines.json."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "engines.json")


def _load_config(path: Optional[str] = None) -> dict[str, Any]:
    config_path = path or _CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_search_engines(path=None) -> list[dict[str, Any]]:
    return _load_config(path).get("search_engines", [])


def get_news_sources(path=None) -> list[dict[str, Any]]:
    return _load_config(path).get("news_sources", [])


def get_academic_sources(path=None) -> list[dict[str, Any]]:
    return _load_config(path).get("academic_sources", [])


def get_wechat_sources(path=None) -> list[dict[str, Any]]:
    return _load_config(path).get("wechat_sources", [])


def get_social_sources(path=None) -> list[dict[str, Any]]:
    return _load_config(path).get("social_sources", [])


def get_special_engines(path=None) -> list[dict[str, Any]]:
    return _load_config(path).get("special_engines", [])


def get_engine(name: str, path=None):
    config = _load_config(path)
    for cat in ["search_engines", "news_sources", "academic_sources", "wechat_sources", "social_sources", "special_engines"]:
        for e in config.get(cat, []):
            if e["name"].lower() == name.lower():
                return e
    return None


def get_all_sources(path=None) -> list[dict[str, Any]]:
    config = _load_config(path)
    all_s = []
    for cat in ["search_engines", "news_sources", "academic_sources", "wechat_sources", "social_sources", "special_engines"]:
        all_s.extend(config.get(cat, []))
    return all_s


def list_source_categories(path=None) -> dict[str, int]:
    config = _load_config(path)
    cats = ["search_engines", "news_sources", "academic_sources", "wechat_sources", "social_sources", "special_engines"]
    return {c: len(config.get(c, [])) for c in cats}
