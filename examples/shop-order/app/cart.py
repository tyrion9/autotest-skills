"""Giỏ hàng lưu trong session (cookie đã ký) — không cần đăng nhập.

Trong session chỉ lưu dạng tối giản `[{"product_id": 4, "quantity": 2}, ...]`
theo đúng thứ tự người dùng thêm vào; tên/giá/tồn kho luôn đọc lại từ DB khi
hiển thị, nên đổi giá trong DB là giỏ hàng cập nhật theo ngay.
"""

from __future__ import annotations

from flask import session

import db as shop_db

CART_SESSION_KEY = "cart"

# Số DÒNG hàng tối đa trong giỏ (mỗi sản phẩm là 1 dòng, không tính số lượng).
# Đặt thấp có chủ ý: seed chỉ có 8 sản phẩm còn hàng, để mốc này CHẠM TỚI ĐƯỢC
# thì mới test được case biên "giỏ hàng đầy".
MAX_CART_LINES = 5


def parse_quantity(raw: str) -> tuple[int | None, str | None]:
    """'3' -> (3, None); '0' -> (None, 'Số lượng phải lớn hơn 0.')"""
    raw = (raw or "").strip()
    if not raw:
        return None, "Vui lòng nhập số lượng."
    try:
        quantity = int(raw)
    except ValueError:
        return None, "Số lượng phải là số nguyên."
    if quantity < 1:
        return None, "Số lượng phải lớn hơn 0."
    return quantity, None


def read_cart() -> list[dict]:
    """Đọc giỏ từ session, bỏ qua dữ liệu hỏng (cookie cũ/sửa tay)."""
    lines = []
    for entry in session.get(CART_SESSION_KEY, []):
        try:
            product_id = int(entry["product_id"])
            quantity = int(entry["quantity"])
        except (KeyError, TypeError, ValueError):
            continue
        if quantity > 0:
            lines.append({"product_id": product_id, "quantity": quantity})
    return lines


def write_cart(lines: list[dict]) -> None:
    session[CART_SESSION_KEY] = lines
    session.modified = True


def clear() -> None:
    session.pop(CART_SESSION_KEY, None)
    session.modified = True


def add(product_id: int, quantity: int) -> str | None:
    """Thêm vào giỏ; sản phẩm đã có thì CỘNG DỒN số lượng. Trả về lỗi (nếu có)."""
    product = shop_db.get_product(product_id)
    if product is None:
        return "Sản phẩm không tồn tại."
    if product["stock"] <= 0:
        return "Sản phẩm đã hết hàng, không thể thêm vào giỏ."

    lines = read_cart()
    for line in lines:
        if line["product_id"] == product_id:
            new_quantity = line["quantity"] + quantity
            if new_quantity > product["stock"]:
                return (
                    f"Chỉ còn {product['stock']} sản phẩm trong kho"
                    f" (giỏ hàng đang có {line['quantity']})."
                )
            line["quantity"] = new_quantity
            write_cart(lines)
            return None

    if len(lines) >= MAX_CART_LINES:
        return f"Giỏ hàng tối đa {MAX_CART_LINES} sản phẩm khác nhau."
    if quantity > product["stock"]:
        return f"Chỉ còn {product['stock']} sản phẩm trong kho."

    lines.append({"product_id": product_id, "quantity": quantity})
    write_cart(lines)
    return None


def set_quantity(product_id: int, quantity: int) -> str | None:
    """Đặt lại số lượng của 1 dòng (dùng ở màn hình giỏ hàng)."""
    product = shop_db.get_product(product_id)
    if product is None:
        return "Sản phẩm không tồn tại."
    if quantity > product["stock"]:
        return f"Chỉ còn {product['stock']} sản phẩm trong kho."

    lines = read_cart()
    for line in lines:
        if line["product_id"] == product_id:
            line["quantity"] = quantity
            write_cart(lines)
            return None
    return "Sản phẩm không có trong giỏ hàng."


def remove(product_id: int) -> None:
    write_cart([line for line in read_cart() if line["product_id"] != product_id])


def build_lines() -> list[dict]:
    """Ghép giỏ trong session với dữ liệu sản phẩm hiện tại trong DB."""
    lines = read_cart()
    products = shop_db.get_products_by_ids(line["product_id"] for line in lines)

    result = []
    for line in lines:
        product = products.get(line["product_id"])
        if product is None:  # sản phẩm đã bị xoá khỏi DB
            continue
        result.append(
            {
                "product_id": product["id"],
                "name": product["name"],
                "category_name": product["category_name"],
                "image": product["image"],
                "unit_price": product["price"],
                "bulky": bool(product["bulky"]),
                "stock": product["stock"],
                "quantity": line["quantity"],
                "line_total": product["price"] * line["quantity"],
            }
        )
    return result


def item_count() -> int:
    """Tổng SỐ LƯỢNG sản phẩm trong giỏ (dùng cho badge trên header)."""
    return sum(line["quantity"] for line in read_cart())


def check_lines_against_stock(lines: list[dict]) -> list[str]:
    """Kiểm tra lại tồn kho ngay trước khi đặt (kho có thể đã đổi từ lúc thêm)."""
    return [
        f"{line['name']}: chỉ còn {line['stock']} sản phẩm trong kho"
        f" (giỏ hàng đang đặt {line['quantity']})."
        for line in lines
        if line["quantity"] > line["stock"]
    ]
