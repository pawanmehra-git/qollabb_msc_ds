"""
FAQ loading, keyword scoring, and optional LLM fallback.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.utils import data_path, load_json, save_json

FAQ_FILE = data_path("faq.json")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def load_faqs() -> list[dict[str, Any]]:
    raw = load_json(FAQ_FILE, default={"faqs": []})
    faqs = raw.get("faqs", [])
    return faqs if isinstance(faqs, list) else []


def score_faq_match(user_query: str, faq: dict[str, Any]) -> float:
    """Combine keyword overlap and fuzzy similarity to question text."""
    u = _normalize(user_query)
    q = _normalize(str(faq.get("question", "")))
    keywords = faq.get("keywords") or []
    if not isinstance(keywords, list):
        keywords = []

    score = 0.0
    utoks = _tokenize(u)

    # Keyword hits
    for kw in keywords:
        kw_s = str(kw).lower()
        if kw_s and kw_s in u:
            score += 2.0
        elif kw_s:
            kt = _tokenize(kw_s)
            if kt and kt & utoks:
                score += 1.0

    # Question similarity
    score += SequenceMatcher(None, u, q).ratio() * 3.0

    return score


def search_faq(user_query: str, top_k: int = 3) -> list[tuple[float, dict[str, Any]]]:
    """Return ranked FAQ entries (score, faq dict)."""
    faqs = load_faqs()
    ranked: list[tuple[float, dict[str, Any]]] = []
    for f in faqs:
        s = score_faq_match(user_query, f)
        ranked.append((s, f))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return ranked[:top_k]


def best_faq_answer(user_query: str, threshold: float = 1.5) -> tuple[str | None, float]:
    """
    Return (answer, score) for the best FAQ match, or (None, best_score) if below threshold.
    """
    ranked = search_faq(user_query, top_k=1)
    if not ranked:
        return None, 0.0
    score, faq = ranked[0]
    if score < threshold:
        return None, score
    ans = faq.get("answer")
    if not ans:
        return None, score
    return str(ans), score


def faq_context_block(user_query: str, max_items: int = 2) -> str:
    """Build a short context string of top FAQ Q&A for LLM RAG."""
    ranked = search_faq(user_query, top_k=max_items)
    lines: list[str] = []
    for s, faq in ranked:
        if s < 0.8:
            continue
        lines.append(f"Q: {faq.get('question','')}\nA: {faq.get('answer','')}")
    return "\n\n".join(lines)


def persist_faq_snapshot(faqs: list[dict[str, Any]]) -> None:
    """Optional admin: write FAQs back to disk."""
    save_json(FAQ_FILE, {"faqs": faqs})
