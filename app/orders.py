"""
Order creation, lookup, cancellation with stock reconciliation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app import books as books_mod
from app.utils import data_path, load_json, save_json

ORDERS_FILE = data_path("orders.json")


def _ensure_orders_structure(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {"next_order_id": 10001, "orders": []}
    if "orders" not in raw:
        raw["orders"] = []
    if "next_order_id" not in raw:
        raw["next_order_id"] = 10001
    return raw


def load_orders_data() -> dict[str, Any]:
    raw = load_json(ORDERS_FILE, default={"next_order_id": 10001, "orders": []})
    return _ensure_orders_structure(raw)


def save_orders_data(data: dict[str, Any]) -> None:
    save_json(ORDERS_FILE, data)


def get_order_by_id(order_id: int) -> dict[str, Any] | None:
    data = load_orders_data()
    for o in data.get("orders", []):
        if int(o.get("order_id", -1)) == int(order_id):
            return o
    return None


def create_order(
    customer_name: str,
    book_id: str,
    quantity: int,
) -> tuple[bool, str, dict[str, Any] | None]:
    """
    Validate stock, decrement stock, append order. Returns (ok, message, order_dict).
    """
    book = books_mod.get_book_by_id(book_id)
    if not book:
        return False, "Book not found.", None

    stock = int(book.get("stock_quantity", 0))
    if quantity < 1:
        return False, "Quantity must be at least 1.", None
    if stock < quantity:
        return (
            False,
            f"Not enough stock for '{book.get('title')}'. Available: {stock}.",
            None,
        )

    if not books_mod.reduce_stock(book_id, quantity):
        return False, "Could not update stock. Please try again.", None

    data = load_orders_data()
    oid = int(data.get("next_order_id", 10001))
    try:
        unit_price = float(book.get("price", 0))
    except (TypeError, ValueError):
        unit_price = 0.0
    total = round(unit_price * quantity, 2)

    order = {
        "order_id": oid,
        "customer_name": customer_name.strip() or "Guest",
        "book_id": str(book_id),
        "book_title": str(book.get("title", "")),
        "quantity": quantity,
        "total_price": total,
        "status": "Placed",
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    orders = data.get("orders", [])
    orders.append(order)
    data["orders"] = orders
    data["next_order_id"] = oid + 1
    save_orders_data(data)

    return (
        True,
        f"Order placed successfully. Your order ID is **{oid}**. Total: **${total:.2f}**.",
        order,
    )


def get_order_status(order_id: int) -> tuple[bool, str]:
    o = get_order_by_id(order_id)
    if not o:
        return False, f"No order found with ID {order_id}."
    msg = (
        f"Order **{order_id}**: {o.get('book_title')} × {o.get('quantity')} — "
        f"Status: **{o.get('status')}** — Total: ${float(o.get('total_price', 0)):.2f}"
    )
    return True, msg


def cancel_order(order_id: int) -> tuple[bool, str]:
    data = load_orders_data()
    orders = data.get("orders", [])
    for i, o in enumerate(orders):
        if int(o.get("order_id", -1)) != int(order_id):
            continue
        status = str(o.get("status", ""))
        if status == "Cancelled":
            return False, f"Order {order_id} is already cancelled."
        if status == "Delivered":
            return False, f"Order {order_id} has already been delivered and cannot be cancelled."

        book_id = str(o.get("book_id", ""))
        qty = int(o.get("quantity", 0))
        o["status"] = "Cancelled"
        orders[i] = o
        data["orders"] = orders
        save_orders_data(data)

        books_mod.restore_stock(book_id, qty)
        return True, f"Order **{order_id}** has been cancelled and stock restored."

    return False, f"No order found with ID {order_id}."
