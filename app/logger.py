"""
Chat logging and analytics (JSON-backed).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from app.utils import data_path, load_json, save_json

LOG_FILE = data_path("chat_logs.json")

AnalyticsKey = Literal["total_queries", "book_searches", "orders_placed"]


def _default_log_structure() -> dict[str, Any]:
    return {
        "entries": [],
        "analytics": {
            "total_queries": 0,
            "book_searches": 0,
            "orders_placed": 0,
        },
    }


def load_logs() -> dict[str, Any]:
    raw = load_json(LOG_FILE, default=_default_log_structure())
    if not isinstance(raw, dict):
        return _default_log_structure()
    raw.setdefault("entries", [])
    raw.setdefault("analytics", _default_log_structure()["analytics"])
    for k in ("total_queries", "book_searches", "orders_placed"):
        raw["analytics"].setdefault(k, 0)
    return raw


def save_logs(data: dict[str, Any]) -> None:
    save_json(LOG_FILE, data)


def log_interaction(user_query: str, bot_response: str) -> None:
    """Append one chat turn and bump total_queries."""
    data = load_logs()
    entries = data.get("entries", [])
    entries.append(
        {
            "user_query": user_query,
            "bot_response": bot_response,
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )
    data["entries"] = entries[-500:]  # cap size
    data["analytics"]["total_queries"] = int(data["analytics"].get("total_queries", 0)) + 1
    save_logs(data)


def bump_analytics(key: AnalyticsKey, delta: int = 1) -> None:
    data = load_logs()
    cur = int(data["analytics"].get(key, 0))
    data["analytics"][key] = cur + delta
    save_logs(data)


def get_analytics_summary() -> dict[str, int]:
    data = load_logs()
    return {k: int(data["analytics"].get(k, 0)) for k in ("total_queries", "book_searches", "orders_placed")}
