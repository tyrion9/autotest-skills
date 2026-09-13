"""Truy cập SQLite — mỏng, không ORM, để test đọc thẳng DB làm oracle dễ dàng."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "db" / "shop.sqlite3"


def db_path() -> Path:
    """Cho phép trỏ sang DB khác qua biến môi trường SHOP_DB (tiện chạy test)."""
    return Path(os.environ.get("SHOP_DB", DEFAULT_DB_PATH))


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def list_categories() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute("SELECT slug, name FROM categories ORDER BY sort_order").fetchall()


def list_products(category_slug: str | None = None) -> list[sqlite3.Row]:
    sql = (
        "SELECT p.*, c.name AS category_name FROM products p"
        " JOIN categories c ON c.slug = p.category_slug"
    )
    params: tuple = ()
    if category_slug:
        sql += " WHERE p.category_slug = ?"
        params = (category_slug,)
    sql += " ORDER BY c.sort_order, p.id"
    with get_connection() as conn:
        return conn.execute(sql, params).fetchall()


def get_product(product_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT p.*, c.name AS category_name FROM products p"
            " JOIN categories c ON c.slug = p.category_slug WHERE p.id = ?",
            (product_id,),
        ).fetchone()


def get_products_by_ids(product_ids) -> dict[int, sqlite3.Row]:
    """Trả về {id: row} cho các id còn tồn tại (id không có sẽ vắng mặt)."""
    ids = list(dict.fromkeys(int(pid) for pid in product_ids))
    if not ids:
        return {}
    placeholders = ", ".join("?" for _ in ids)
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT p.*, c.name AS category_name FROM products p"
            f" JOIN categories c ON c.slug = p.category_slug WHERE p.id IN ({placeholders})",
            ids,
        ).fetchall()
    return {row["id"]: row for row in rows}


def get_order_by_code(code: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute("SELECT * FROM orders WHERE code = ?", (code,)).fetchone()


def get_order_items(order_id: int) -> list[sqlite3.Row]:
    with get_connection() as conn:
        # LEFT JOIN products chỉ để lấy ảnh hiển thị; mọi số liệu của đơn đều
        # đọc từ order_items (đã chốt tại thời điểm đặt).
        return conn.execute(
            "SELECT oi.*, p.image AS image FROM order_items oi"
            " LEFT JOIN products p ON p.id = oi.product_id"
            " WHERE oi.order_id = ? ORDER BY oi.id",
            (order_id,),
        ).fetchall()


def insert_order(order: dict, items: list[dict]) -> int:
    """Ghi đơn + các dòng hàng trong CÙNG 1 transaction. Trả về order id."""
    columns = ", ".join(order)
    placeholders = ", ".join(f":{key}" for key in order)
    conn = get_connection()
    try:
        cursor = conn.execute(f"INSERT INTO orders ({columns}) VALUES ({placeholders})", order)
        order_id = cursor.lastrowid
        conn.executemany(
            "INSERT INTO order_items"
            " (order_id, product_id, product_name, unit_price, bulky, quantity, line_total)"
            " VALUES (:order_id, :product_id, :product_name, :unit_price, :bulky, :quantity, :line_total)",
            [dict(item, order_id=order_id) for item in items],
        )
        conn.commit()
        return order_id
    finally:
        conn.close()
