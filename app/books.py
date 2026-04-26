"""
Book catalog: load, search, stock updates.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.utils import data_path, load_json, save_json

BOOKS_FILE = data_path("books.json")


def _books_list(raw: dict[str, Any]) -> list[dict[str, Any]]:
    books = raw.get("books", [])
    return books if isinstance(books, list) else []


def get_books() -> list[dict[str, Any]]:
    """Return all books from catalog."""
    raw = load_json(BOOKS_FILE, default={"books": []})
    return _books_list(raw)


def _save_books(books: list[dict[str, Any]]) -> None:
    save_json(BOOKS_FILE, {"books": books})


def get_book_by_id(book_id: str) -> dict[str, Any] | None:
    for b in get_books():
        if str(b.get("book_id")) == str(book_id):
            return b
    return None


def get_book_by_title_fuzzy(title: str) -> tuple[dict[str, Any] | None, float]:
    """Find best matching book by title (case-insensitive, fuzzy)."""
    t = title.strip().lower()
    if not t:
        return None, 0.0
    best: dict[str, Any] | None = None
    best_score = 0.0
    for b in get_books():
        bt = str(b.get("title", "")).lower()
        ratio = SequenceMatcher(None, t, bt).ratio()
        # Substring boost
        if t in bt or bt in t:
            ratio = max(ratio, 0.85)
        if ratio > best_score:
            best_score = ratio
            best = b
    return best, best_score


def search_books(
    query: str | None = None,
    *,
    genre: str | None = None,
    author: str | None = None,
    title: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool = True,
) -> list[dict[str, Any]]:
    """
    Filter books by optional text query (title/author/genre) and structured filters.
    """
    books = get_books()
    out: list[dict[str, Any]] = []

    q_norm = (query or "").strip().lower()
    genre_l = (genre or "").strip().lower()
    author_l = (author or "").strip().lower()
    title_l = (title or "").strip().lower()

    for b in books:
        if in_stock_only and int(b.get("stock_quantity", 0)) <= 0:
            continue
        try:
            price = float(b.get("price", 0))
        except (TypeError, ValueError):
            price = 0.0
        if min_price is not None and price < min_price:
            continue
        if max_price is not None and price > max_price:
            continue
        g = str(b.get("genre", "")).lower()
        a = str(b.get("author", "")).lower()
        t = str(b.get("title", "")).lower()

        if genre_l and genre_l not in g:
            continue
        if author_l and author_l not in a:
            continue
        if title_l and title_l not in t:
            continue

        if q_norm:
            blob = f"{t} {a} {g}"
            tokens = [x for x in re.split(r"\s+", q_norm) if len(x) > 1]
            if q_norm in blob:
                pass
            elif tokens and any(tok in blob for tok in tokens):
                pass
            elif SequenceMatcher(None, q_norm, t).ratio() >= 0.55:
                pass
            else:
                continue

        out.append(b)
    return out


def reduce_stock(book_id: str, quantity: int) -> bool:
    """Subtract quantity; return True if successful."""
    books = get_books()
    for i, b in enumerate(books):
        if str(b.get("book_id")) == str(book_id):
            stock = int(b.get("stock_quantity", 0))
            if stock < quantity:
                return False
            b["stock_quantity"] = stock - quantity
            books[i] = b
            _save_books(books)
            return True
    return False


def restore_stock(book_id: str, quantity: int) -> None:
    """Add quantity back (e.g. after cancel)."""
    books = get_books()
    for i, b in enumerate(books):
        if str(b.get("book_id")) == str(book_id):
            stock = int(b.get("stock_quantity", 0))
            b["stock_quantity"] = stock + quantity
            books[i] = b
            break
    _save_books(books)


def recommend_similar(book: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    """Same genre, exclude same book_id, prefer in-stock."""
    gid = str(book.get("genre", ""))
    bid = str(book.get("book_id", ""))
    candidates = [b for b in get_books() if str(b.get("book_id")) != bid and str(b.get("genre")) == gid]
    candidates = [b for b in candidates if int(b.get("stock_quantity", 0)) > 0]
    return candidates[:limit]


def format_books_table(books: list[dict[str, Any]]) -> str:
    if not books:
        return "No books found matching your criteria."
    lines = [
        "| ID | Title | Author | Genre | Price | Stock |",
        "|---|---|---|---|---:|---:|",
    ]
    for b in books:
        lines.append(
            f"| {b.get('book_id')} | {b.get('title')} | {b.get('author')} | "
            f"{b.get('genre')} | ${float(b.get('price', 0)):.2f} | {b.get('stock_quantity')} |"
        )
    return "\n".join(lines)


def format_books_list(books: list[dict[str, Any]], max_items: int | None = 15) -> str:
    """
    Render a clean list for chat (avoids Markdown pipe-table rendering issues).
    """
    if not books:
        return "No books found matching your criteria."

    if max_items is not None:
        books = books[:max_items]

    out_lines: list[str] = []
    for i, b in enumerate(books, start=1):
        try:
            price = float(b.get("price", 0))
        except (TypeError, ValueError):
            price = 0.0
        out_lines.append(
            f"{i}. {b.get('title')} by {b.get('author')} "
            f"(Genre: {b.get('genre')}) - ${price:.2f} - Stock: {b.get('stock_quantity')}"
        )
    return "\n".join(out_lines)
