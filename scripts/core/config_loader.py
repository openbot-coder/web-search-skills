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


def get_special_engines(path: Optional[str] = None) -> list[dict[str, Any]]:
    return _load_config(path).get("special_engines", [])


def get_engine(name: str, path: Optional[str] = None):
    config = _load_config(path)
    for category in ["search_engines", "news_sources", "academic_sources", "wechat_sources", "special_engines"]:
        for engine in config.get(category, []):
            if engine["name"].lower() == name.lower():
                return engine
    return None


def get_all_sources(path: Optional[str] = None) -> list[dict[str, Any]]:
    config = _load_config(path)
    all_sources = []
    for category in ["search_engines", "news_sources", "academic_sources", "wechat_sources", "special_engines"]:
        all_sources.extend(config.get(category, []))
    return all_sources
