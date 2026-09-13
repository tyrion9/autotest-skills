#!/usr/bin/env python3
"""Tạo lại database demo từ schema.sql + dữ liệu cố định bên dưới.

Chạy:
    python db/seed_data.py            # tạo/ghi đè db/shop.sqlite3
    python db/seed_data.py --db /tmp/shop-test.sqlite3

Dữ liệu là HẰNG SỐ (không random) để kết quả test tái lập được giữa các lần
chạy. Chạy lại script này trước mỗi phiên test để về trạng thái sạch (bảng
orders rỗng).
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = DB_DIR / "shop.sqlite3"
SCHEMA_PATH = DB_DIR / "schema.sql"

# slug, tên hiển thị, thứ tự
CATEGORIES = [
    ("dien-tu", "Điện tử", 1),
    ("gia-dung", "Gia dụng", 2),
    ("sach", "Sách", 3),
]

# id, tên, category, giá (VND), tồn kho, cồng kềnh, mô tả, ảnh bìa
# Ảnh bìa: xem app/static/images/CREDITS.md (nguồn + giấy phép).
PRODUCTS = [
    (1, "Tai nghe Bluetooth ZX", "dien-tu", 450_000, 25, 0,
     "Tai nghe chụp tai, pin 30 giờ, chống ồn chủ động.",
     "product-1.jpg"),
    (2, "Chuột không dây M1", "dien-tu", 180_000, 40, 0,
     "Chuột quang không dây 2.4GHz, im lặng, pin AA.",
     "product-2.jpg"),
    (3, "Bàn phím cơ K87", "dien-tu", 890_000, 12, 0,
     "Bàn phím cơ 87 phím, switch nâu, led trắng.",
     "product-3.jpg"),
    (4, "Nồi chiên không dầu 5L", "gia-dung", 1_590_000, 8, 1,
     "Nồi chiên không dầu dung tích 5 lít, 8 chế độ nấu.",
     "product-4.jpg"),
    (5, "Bộ nồi inox 3 món", "gia-dung", 720_000, 15, 1,
     "Bộ 3 nồi inox 304 đáy từ, dùng được mọi loại bếp.",
     "product-5.jpg"),
    (6, "Bình giữ nhiệt 500ml", "gia-dung", 250_000, 30, 0,
     "Bình giữ nhiệt inox, giữ nóng 12 giờ.",
     "product-6.jpg"),
    (7, "Nhà giả kim", "sach", 79_000, 100, 0,
     "Tiểu thuyết của Paulo Coelho, bản dịch tiếng Việt.",
     "product-7.jpg"),
    (8, "Clean Code (bản dịch)", "sach", 195_000, 20, 0,
     "Sách kỹ thuật về viết mã sạch, bản dịch tiếng Việt.",
     "product-8.jpg"),
    # Sản phẩm hết hàng — dùng cho case biên "không đặt được khi hết hàng".
    (9, "Đắc nhân tâm", "sach", 88_000, 0, 0,
     "Sách kỹ năng giao tiếp kinh điển. Tạm thời hết hàng.",
     "product-9.jpg"),
]


def seed(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.executemany("INSERT INTO categories (slug, name, sort_order) VALUES (?, ?, ?)", CATEGORIES)
        conn.executemany(
            "INSERT INTO products (id, name, category_slug, price, stock, bulky, description, image)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            PRODUCTS,
        )
        conn.commit()
    finally:
        conn.close()

    print(
        f"✅ Đã tạo lại {db_path}\n"
        f"   {len(CATEGORIES)} category, {len(PRODUCTS)} sản phẩm "
        f"(1 sản phẩm hết hàng: id=9), bảng orders rỗng."
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Đường dẫn file sqlite muốn tạo")
    args = ap.parse_args()
    seed(args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
