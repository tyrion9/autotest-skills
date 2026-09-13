-- Schema cho app demo "shop đặt hàng online".
-- Mọi ràng buộc nghiệp vụ được khai báo ở DB (CHECK/NOT NULL/FK) để bước
-- autotest-factor-analysis trích được Factor/Level/Constraint từ nguồn thật.

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;

CREATE TABLE categories (
    slug       TEXT PRIMARY KEY,
    name       TEXT    NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE products (
    id            INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    category_slug TEXT    NOT NULL REFERENCES categories(slug),
    -- Giá đơn vị, đơn vị VND, luôn là số nguyên (không có xu).
    price         INTEGER NOT NULL CHECK (price > 0),
    -- Tồn kho: chặn đặt quá số lượng. App demo KHÔNG trừ kho khi đặt hàng
    -- (xem README mục "Giới hạn có chủ ý").
    stock         INTEGER NOT NULL CHECK (stock >= 0),
    -- Hàng cồng kềnh -> cộng phụ phí vận chuyển theo DÒNG, xem app/pricing.py
    bulky         INTEGER NOT NULL DEFAULT 0 CHECK (bulky IN (0, 1)),
    description   TEXT    NOT NULL DEFAULT '',
    -- Tên file ảnh bìa trong app/static/images/ (rỗng -> dùng placeholder.svg)
    image         TEXT    NOT NULL DEFAULT ''
);

-- 1 đơn hàng = nhiều dòng hàng (order_items). Phần tiền được chốt tại thời
-- điểm đặt, không tính lại từ products (đổi giá không làm sai đơn cũ).
CREATE TABLE orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    code           TEXT    NOT NULL UNIQUE,
    item_count     INTEGER NOT NULL CHECK (item_count > 0),
    subtotal       INTEGER NOT NULL,
    shipping_fee   INTEGER NOT NULL,
    cod_fee        INTEGER NOT NULL,
    total          INTEGER NOT NULL,
    customer_name  TEXT    NOT NULL,
    phone          TEXT    NOT NULL,
    email          TEXT    NOT NULL DEFAULT '',
    address        TEXT    NOT NULL,
    region         TEXT    NOT NULL CHECK (region IN ('noi_thanh', 'ngoai_thanh')),
    payment_method TEXT    NOT NULL CHECK (payment_method IN ('cod', 'bank_transfer')),
    note           TEXT    NOT NULL DEFAULT '',
    created_at     TEXT    NOT NULL
);

CREATE TABLE order_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id   INTEGER NOT NULL REFERENCES products(id),
    -- Chốt tên + giá + cờ cồng kềnh tại thời điểm đặt.
    product_name TEXT    NOT NULL,
    unit_price   INTEGER NOT NULL,
    bulky        INTEGER NOT NULL DEFAULT 0 CHECK (bulky IN (0, 1)),
    quantity     INTEGER NOT NULL CHECK (quantity > 0),
    line_total   INTEGER NOT NULL
);

CREATE INDEX idx_products_category ON products (category_slug);
CREATE INDEX idx_orders_code ON orders (code);
CREATE INDEX idx_order_items_order ON order_items (order_id);
