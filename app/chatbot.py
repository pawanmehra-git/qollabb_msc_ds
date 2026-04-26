"""
Intent detection, entity extraction, and response routing for Ansira.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app import books as books_mod
from app import faq as faq_mod
from app import logger as log_mod
from app import orders as orders_mod
from app.llm import extract_entities_llm, generate_response


class Intent(str, Enum):
    FAQ = "faq"
    BOOK_SEARCH = "book_search"
    ORDER_PLACEMENT = "order_placement"
    ORDER_STATUS = "order_status"
    CANCEL_ORDER = "cancel_order"
    GENERAL = "general"


@dataclass
class Entities:
    book_title: str | None = None
    author: str | None = None
    quantity: int = 1
    order_id: int | None = None
    customer_name: str | None = None
    genre: str | None = None
    min_price: float | None = None
    max_price: float | None = None


@dataclass
class BotReply:
    text: str
    intent: Intent
    used_llm: bool = False
    meta: dict[str, Any] = field(default_factory=dict)


# --- Rule-based intent cues ---

FAQ_HINTS = (
    "hours", "open", "close", "shipping", "return", "refund", "payment", "pay",
    "loyalty", "ebook", "e-book", "delivery", "secure", "gift", "wrap", "reserve",
    "location", "address", "price match", "contact", "support", "phone", "email",
    "policy", "track", "faq", "help with account",
)

BOOK_BROWSE_HINTS = (
    "show book",
    "list book",
    "list of books",
    "book list",
    "browse",
    "catalog",
    "available book",
    "available books",
    "what book",
    "fiction", "non-fiction", "genre", "recommend", "suggest", "books in",
    "books by", "author", "cheap", "under $",
)

ORDER_STATUS_HINTS = (
    "order status",
    "check my order",
    "check order",
    "track order",
    "where is my order",
    "status of order",
)
CANCEL_HINTS = ("cancel", "void order")


def _lower(s: str) -> str:
    return s.lower().strip()


def detect_intent(user_message: str) -> Intent:
    t = _lower(user_message)

    if any(h in t for h in CANCEL_HINTS) and re.search(r"\b(order|#\s?)?\d{4,6}\b", t):
        return Intent.CANCEL_ORDER
    if any(h in t for h in CANCEL_HINTS) and "order" in t:
        return Intent.CANCEL_ORDER

    if any(h in t for h in ORDER_STATUS_HINTS) or (re.search(r"\b(check|track)\b.*\border\b", t) and re.search(r"\d{4,6}", t)):
        return Intent.ORDER_STATUS
    if "order" in t and re.search(r"\b\d{4,6}\b", t) and any(x in t for x in ("status", "check", "track")):
        return Intent.ORDER_STATUS

    # Placement: explicit "copies of" / quantity patterns — avoid matching generic "buy books"
    if "copies of" in t or "copy of" in t:
        return Intent.ORDER_PLACEMENT
    if re.search(r"\b(?:buy|purchase|order)\s+\d{1,2}\s+(?:copies?|copies)\s+of\b", t):
        return Intent.ORDER_PLACEMENT
    # e.g. "buy 2 Atomic Habits" (without the word "copies")
    if re.search(r"\b(?:buy|purchase|order)\s+\d{1,2}\s+\S", t):
        return Intent.ORDER_PLACEMENT
    if re.search(r"\b(?:want|need)\s+to\s+(?:buy|purchase|order)\s+\d+", t):
        return Intent.ORDER_PLACEMENT
    if re.search(r"\b(?:add to cart|get me)\b", t) and "book" in t:
        return Intent.ORDER_PLACEMENT

    if any(h in t for h in BOOK_BROWSE_HINTS) or re.search(r"\bbooks?\s+(in|by)\b", t):
        return Intent.BOOK_SEARCH
    if "book" in t and any(x in t for x in ("show", "list", "browse", "find", "search")):
        return Intent.BOOK_SEARCH

    if any(h in t for h in FAQ_HINTS):
        return Intent.FAQ

    ranked = faq_mod.search_faq(user_message, top_k=1)
    if ranked and ranked[0][0] >= 2.0:
        return Intent.FAQ

    return Intent.GENERAL


def extract_order_id(text: str) -> int | None:
    m = re.search(r"\b(?:order\s*#?\s*|#)?(\d{4,6})\b", text, re.I)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


def extract_quantity(text: str) -> int:
    m = re.search(r"\b(\d{1,2})\s*(?:cop(?:y|ies)|x\b)", text, re.I)
    if m:
        return max(1, int(m.group(1)))
    m2 = re.search(r"\b(?:buy|purchase|order)\s+(\d{1,2})\b", text, re.I)
    if m2:
        return max(1, int(m2.group(1)))
    return 1


def extract_title_from_purchase(text: str) -> str | None:
    """Patterns: 'copies of X', 'buy 2 X', 'order X' (title may follow)."""
    t = text.strip()
    patterns = [
        r"(?:copies? of|copy of)\s+['\"]?([^'\"\n]+?)['\"]?(?:\s*$|\s*(?:for|at)\s)",
        r"\b(?:buy|purchase|order)\s+\d{1,2}\s+['\"]?([^'\"\n]+?)['\"]?(?:\s*$)",
        r"(?:buy|purchase|get)\s+(\d+\s+)?(?:copies of|copy of)?\s*['\"]?([^'\"\n]+?)['\"]?(?:\s*$|\s+for\s)",
        r"(?:order|want)\s+['\"]?([^'\"\n]+?)['\"]?(?:\s*$)",
    ]
    for p in patterns:
        m = re.search(p, t, re.I)
        if m:
            grp = m.groups()[-1].strip()
            if len(grp) > 2:
                return grp.rstrip(".,!?")
    return None


def extract_author_phrase(text: str) -> str | None:
    m = re.search(r"\b(?:by|author)\s+([A-Za-z][A-Za-z\s.'-]{2,40})", text, re.I)
    if m:
        return m.group(1).strip()
    m2 = re.search(r"\bbooks?\s+by\s+([A-Za-z][A-Za-z\s.'-]{2,40})", text, re.I)
    if m2:
        return m2.group(1).strip()
    return None


def extract_genre_phrase(text: str) -> str | None:
    m = re.search(
        r"\b(?:books?\s+)?(?:in|genre)\s+(?:the\s+)?([a-z][a-z\s-]{2,30})\b",
        text,
        re.I,
    )
    if m:
        g = m.group(1).strip()
        g = re.sub(r"\s+category\s*$", "", g, flags=re.I)
        return g
    m2 = re.search(
        r"\b(fiction|non-fiction|fantasy|sci-fi|science fiction|thriller|memoir|history|classic|self-help|business)\b",
        text,
        re.I,
    )
    if m2:
        return m2.group(1).strip()
    return None


def extract_price_range(text: str) -> tuple[float | None, float | None]:
    t = _lower(text)
    min_p = max_p = None
    m = re.search(r"under\s*\$?\s*(\d+(?:\.\d+)?)", t)
    if m:
        max_p = float(m.group(1))
    m2 = re.search(r"between\s*\$?\s*(\d+)\s*and\s*\$?\s*(\d+)", t)
    if m2:
        min_p, max_p = float(m2.group(1)), float(m2.group(2))
    return min_p, max_p


def extract_entities(user_message: str, intent: Intent) -> Entities:
    e = Entities()
    e.quantity = extract_quantity(user_message)
    e.order_id = extract_order_id(user_message)
    e.author = extract_author_phrase(user_message)
    e.genre = extract_genre_phrase(user_message)
    mn, mx = extract_price_range(user_message)
    e.min_price, e.max_price = mn, mx

    if intent == Intent.ORDER_PLACEMENT:
        title = extract_title_from_purchase(user_message)
        if title:
            e.book_title = title
        # Optional LLM assist for messy phrasing
        if not e.book_title or len(e.book_title) < 3:
            raw = extract_entities_llm(
                user_message,
                'book_title (string), quantity (number), customer_name (string or null)',
            )
            try:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start >= 0 and end > start:
                    obj = json.loads(raw[start:end])
                    if obj.get("book_title"):
                        e.book_title = str(obj["book_title"])
                    if obj.get("quantity"):
                        e.quantity = max(1, int(obj["quantity"]))
                    if obj.get("customer_name"):
                        e.customer_name = str(obj["customer_name"])
            except (json.JSONDecodeError, TypeError, ValueError):
                pass

    return e


def build_conversation_context(history: list[dict[str, str]], max_turns: int = 6) -> str:
    """Recent chat turns for LLM context."""
    chunk = history[-max_turns:]
    lines = []
    for h in chunk:
        role = h.get("role", "user")
        content = h.get("content", "")
        lines.append(f"{role.upper()}: {content}")
    return "\n".join(lines)


def process_message(
    user_message: str,
    conversation_history: list[dict[str, str]] | None = None,
    session_customer_name: str | None = None,
) -> BotReply:
    """
    Main router: detect intent, extract entities, call FAQ/books/orders or LLM.
    """
    conversation_history = conversation_history or []
    intent = detect_intent(user_message)
    entities = extract_entities(user_message, intent)

    ctx = build_conversation_context(conversation_history)
    meta: dict[str, Any] = {"intent": intent.value}

    # --- FAQ ---
    if intent == Intent.FAQ:
        ans, score = faq_mod.best_faq_answer(user_message, threshold=1.5)
        if ans:
            return BotReply(text=ans, intent=intent, used_llm=False, meta=meta)

        rag = faq_mod.faq_context_block(user_message)
        prompt = user_message
        llm_ctx = (ctx + "\n\n" + rag).strip() if (ctx or rag) else rag
        out = generate_response(prompt, context=llm_ctx or ctx)
        return BotReply(text=out, intent=intent, used_llm=True, meta=meta)

    # --- Book search ---
    if intent == Intent.BOOK_SEARCH:
        log_mod.bump_analytics("book_searches", 1)
        genre = entities.genre
        author = entities.author
        q = user_message
        # Refine genre from common phrases if not extracted
        if not genre:
            tl = _lower(user_message)
            if "science fiction" in tl or "sci-fi" in tl:
                genre = "science fiction"
            else:
                for key in (
                    "fiction",
                    "fantasy",
                    "thriller",
                    "memoir",
                    "history",
                    "classic",
                    "self-help",
                    "business",
                    "technology",
                ):
                    if re.search(rf"\b{re.escape(key)}\b", tl):
                        genre = key
                        break

        results = books_mod.search_books(
            query=q,
            genre=genre,
            author=author,
            min_price=entities.min_price,
            max_price=entities.max_price,
        )
        table = books_mod.format_books_table(results[:15])
        extra = ""
        if results:
            recs = books_mod.recommend_similar(results[0], limit=2)
            if recs:
                titles = ", ".join(str(r.get("title")) for r in recs)
                extra = f"\n\n**You may also like:** {titles}"

        text = f"Here are books that match your request:\n\n{table}{extra}"
        if not results:
            # Fallback to LLM with catalog summary
            all_b = books_mod.get_books()[:8]
            brief = "\n".join(f"- {b.get('title')} ({b.get('genre')})" for b in all_b)
            out = generate_response(
                user_message,
                context=ctx + "\nSample catalog:\n" + brief,
            )
            return BotReply(text=out, intent=intent, used_llm=True, meta=meta)

        return BotReply(text=text, intent=intent, used_llm=False, meta=meta)

    # --- Order placement ---
    if intent == Intent.ORDER_PLACEMENT:
        title_guess = entities.book_title
        if not title_guess:
            return BotReply(
                text="Please specify which book you want (e.g. *I want to buy 2 copies of Atomic Habits*).",
                intent=intent,
                meta=meta,
            )

        book, conf = books_mod.get_book_by_title_fuzzy(title_guess)
        if not book or conf < 0.4:
            return BotReply(
                text=(
                    f"I could not find a book matching **{title_guess}**. "
                    "Try browsing with *Show me fiction books* or check the exact title."
                ),
                intent=intent,
                meta=meta,
            )

        cust = session_customer_name or entities.customer_name or "Guest"
        ok, msg, order = orders_mod.create_order(
            customer_name=cust,
            book_id=str(book.get("book_id")),
            quantity=entities.quantity,
        )
        if ok:
            log_mod.bump_analytics("orders_placed", 1)
        return BotReply(text=msg, intent=intent, meta={**meta, "order": order})

    # --- Order status ---
    if intent == Intent.ORDER_STATUS:
        oid = entities.order_id
        if oid is None:
            return BotReply(
                text="Please provide your order number (e.g. *Check my order 10002*).",
                intent=intent,
                meta=meta,
            )
        ok, msg = orders_mod.get_order_status(oid)
        return BotReply(text=msg, intent=intent, meta=meta)

    # --- Cancel order ---
    if intent == Intent.CANCEL_ORDER:
        oid = entities.order_id
        if oid is None:
            return BotReply(
                text="Please provide the order ID to cancel (e.g. *Cancel my order 10002*).",
                intent=intent,
                meta=meta,
            )
        ok, msg = orders_mod.cancel_order(oid)
        return BotReply(text=msg, intent=intent, meta=meta)

    # --- General ---
    catalog_snip = "\n".join(
        f"- {b.get('title')} by {b.get('author')}" for b in books_mod.get_books()[:12]
    )
    out = generate_response(
        user_message,
        context=ctx + "\n\nSome books we carry:\n" + catalog_snip,
    )
    return BotReply(text=out, intent=Intent.GENERAL, used_llm=True, meta=meta)
