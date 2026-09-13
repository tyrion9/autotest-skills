# Ví dụ: App "Shop đặt hàng online" (Flask + SQLite)

App demo **chạy được**, dùng làm đối tượng để thử bộ skill `autotest-*`.
Khác với `examples/cafe-checkout/` (chỉ chứa artifact output của quy trình),
thư mục này **chỉ có app, chưa có test nào** — test sẽ do bạn sinh ra bằng
skill.

## Tính năng

1. **Xem hàng hoá theo category** (`/`) — 9 sản phẩm thuộc 3 danh mục
   (Điện tử / Gia dụng / Sách), mỗi sản phẩm có ảnh bìa, lọc bằng
   `?category=<slug>`.
2. **Xem chi tiết + thêm vào giỏ** (`/product/<id>`) — mô tả, giá, tồn kho,
   form chọn số lượng.
3. **Quản lý giỏ hàng** (`/cart`) — sửa số lượng từng dòng, xoá 1 dòng, xoá
   toàn bộ giỏ; badge số lượng hiển thị trên header mọi trang. Giỏ lưu trong
   session (cookie đã ký), không cần đăng nhập.
4. **Màn hình đặt hàng riêng** (`/checkout`) — bảng chi tiết hàng (đơn giá ×
   số lượng = thành tiền, tạm tính) + form thông tin nhận hàng.
5. **Lưu đơn hàng** (`POST /order` → `/order/<mã đơn>`) — validate, tính tiền,
   ghi `orders` + `order_items` trong 1 transaction, xoá giỏ, hiện trang xác
   nhận đầy đủ chi tiết hàng.

```
/  ──xem──>  /product/<id>  ──thêm──>  /cart  ──>  /checkout  ──đặt──>  /order/<mã>
             (chọn số lượng)          (sửa/xoá)   (chi tiết hàng
                                                   + thông tin liên hệ)
```

## Chạy

```bash
cd examples/shop-order
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python db/seed_data.py      # tạo db/shop.sqlite3 với dữ liệu cố định
cd app && ../.venv/bin/python app.py  # http://127.0.0.1:5001
```

`db/seed_data.py` ghi đè toàn bộ DB (bảng `orders`/`order_items` về rỗng) —
chạy lại trước mỗi phiên test để có trạng thái sạch. Trỏ sang DB khác bằng
biến môi trường `SHOP_DB=/đường/dẫn/khác.sqlite3`.

## Cấu trúc

| File | Nội dung |
|---|---|
| `app/app.py` | Route + validate form thông tin nhận hàng |
| `app/cart.py` | Giỏ hàng trong session: thêm/sửa/xoá, giới hạn, kiểm tồn kho |
| `app/pricing.py` | Công thức tính tiền (phí ship, freeship, phụ phí cồng kềnh, phí COD) |
| `app/db.py` | Truy cập SQLite (mỏng, không ORM) |
| `app/templates/` | `index` · `product` · `cart` · `checkout` · `order` |
| `app/static/images/` | Ảnh bìa `product-<id>.jpg` + `placeholder.svg`; nguồn/giấy phép ghi trong `CREDITS.md` |
| `db/schema.sql` | `categories`, `products`, `orders`, `order_items` + ràng buộc CHECK |
| `db/seed_data.py` | Dữ liệu cố định, không random |

## Quy tắc nghiệp vụ (nguồn cho bước factor-analysis)

**Tính tiền** (`app/pricing.py`) — giỏ hàng nhiều dòng:

```
subtotal     = tổng (đơn giá × số lượng) của mọi dòng
phí ship cơ bản = 15.000 (nội thành) | 30.000 (tỉnh khác)
                  → = 0 nếu subtotal >= 500.000 (freeship)
phụ phí cồng kềnh = 20.000 × SỐ DÒNG hàng có bulky=1 (KHÔNG được freeship miễn)
phí COD      = 10.000 nếu thanh toán COD và subtotal < 200.000
tổng cộng    = subtotal + phí ship + phí COD
```

Các mốc trên tương tác với nhau (freeship × số dòng cồng kềnh × ngưỡng COD ×
khu vực) — chỗ này đáng sinh ma trận pairwise.

**Giỏ hàng** (`app/cart.py`):

| Quy tắc | Chi tiết |
|---|---|
| Thêm sản phẩm đã có trong giỏ | Cộng dồn số lượng, không tạo dòng mới |
| Số lượng mỗi dòng | Số nguyên ≥ 1 và ≤ tồn kho (tính cả phần đã có trong giỏ) |
| Sản phẩm hết hàng | Không thêm được; nút "Thêm vào giỏ" bị `disabled` |
| Số dòng tối đa | 5 sản phẩm khác nhau (`MAX_CART_LINES`) |
| Vào `/checkout` khi giỏ trống | Chuyển về `/cart` kèm thông báo |
| Tồn kho đổi sau khi đã thêm | Kiểm tra lại lúc submit `/order` → lỗi `error-cart` |

**Validate thông tin nhận hàng** (`app/app.py`):

| Field | Ràng buộc |
|---|---|
| Họ tên | Bắt buộc, 2–80 ký tự |
| Số điện thoại | Bắt buộc, đúng 10 chữ số, bắt đầu bằng `0` |
| Email | Không bắt buộc; đã nhập thì phải đúng định dạng |
| Địa chỉ | Bắt buộc, ≥ 5 ký tự |
| Khu vực | Bắt buộc, thuộc `noi_thanh` / `ngoai_thanh` |
| Thanh toán | Bắt buộc, thuộc `cod` / `bank_transfer` |
| Ghi chú | Không bắt buộc, ≤ 200 ký tự |

Mọi field được kiểm tra cùng lúc (1 lần submit thấy hết lỗi), không dừng ở lỗi
đầu tiên; submit lỗi thì **giỏ hàng được giữ nguyên**.

## Thuận lợi cho việc viết test

- **Mọi phần tử thao tác đều có `data-testid` ổn định**. Các nhóm chính:
  - Danh sách: `category-<slug>`, `product-link-<id>`, `product-price-<id>`
  - Chi tiết: `input-quantity`, `btn-add-to-cart`, `out-of-stock`, `error-quantity`
  - Giỏ hàng: `cart-line-<id>`, `cart-qty-<id>`, `btn-update-<id>`,
    `btn-remove-<id>`, `cart-line-total-<id>`, `cart-subtotal`,
    `error-quantity-<id>`, `btn-clear-cart`, `btn-go-checkout`, `cart-empty`
  - Đặt hàng: `checkout-line-<id>`, `checkout-subtotal`, `input-name`,
    `input-phone`, `input-address`, `select-region`, `select-payment`,
    `btn-place-order`, `error-<field>`, `error-cart`
  - Xác nhận: `order-code`, `order-line-<id>`, `order-subtotal`,
    `order-shipping-fee`, `order-cod-fee`, `order-total`
  - Ảnh: `product-image-<id>` (danh sách), `product-image` (chi tiết),
    `cart-item-image-<id>`, `checkout-item-image-<id>`, `order-item-image-<id>`
  - Chung: `cart-badge` (header), `flash-message`
- **Mọi số tiền/số lượng hiển thị kèm `data-value`** chứa số nguyên thô — test
  đọc `data-value` thay vì parse chuỗi `"1.610.000 ₫"`.
- **API JSON để kiểm tra state**: `GET /api/cart` (giỏ hiện tại) và
  `GET /api/orders/<code>` (đơn đã lưu, kèm `items`).
- Dữ liệu seed cố định, có sẵn 2 sản phẩm cồng kềnh (id 4, 5) và 1 sản phẩm
  hết hàng (id 9) để làm case biên.

⚠️ Khi viết oracle: **đọc `price`/`bulky` thô từ `db/shop.sqlite3` rồi tự viết
lại công thức trong code test**, đừng `import pricing` của app — xem quy tắc
oracle trong skill `autotest-gen-test`.

## Bộ test E2E — sinh bằng autotest-skills, KHÔNG commit

Repo này chỉ chứa **app**. Toàn bộ artifact của pipeline kiểm thử
(`testing/`, `reports/`, `pytest.ini`) nằm trong `.gitignore` vì chúng sinh
lại được bất cứ lúc nào — đó cũng chính là điều đang muốn chứng minh: cùng 1
requirement thì chạy lại 4 skill phải ra cùng 1 bộ test.

Sinh lại từ đầu:

```bash
.venv/bin/pip install pytest pytest-bdd playwright pytest-html openpyxl
.venv/bin/playwright install chromium
cd app && ../.venv/bin/python app.py &      # app phải đang chạy
```

rồi chạy 4 skill theo thứ tự (xem `PROMPTS.md` ở gốc repo):
`autotest-factor-analysis` → `autotest-testcase-pairwise` → `autotest-gen-test`
→ `autotest-run-test`. Requirement lấy từ mục "Quy tắc nghiệp vụ" bên trên.

Lần chạy tham chiếu đã thực hiện: 5 factor (CartPreset × Region ×
PaymentMethod × Email × CoGhiChu) → 14 dòng pairwise + 10 case biên = 24
scenario, app đúng cho **24/24 PASS**.

Chạy trình diễn để xem bằng mắt: `pytest testing --demo` (Enter = case tiếp
theo · `s` = chạy hết · `q` = dừng).

## Giới hạn có chủ ý

- **Không trừ tồn kho khi đặt hàng** — `stock` chỉ dùng để chặn số lượng đặt.
  Nhờ vậy chạy bao nhiêu scenario cũng không làm cạn kho giữa chừng (tránh
  flaky giả), đổi lại app không mô phỏng quản lý kho thật.
- **Giỏ tối đa 5 dòng** — đặt thấp để mốc này chạm tới được với 8 sản phẩm còn
  hàng trong seed, nhờ vậy case biên "giỏ hàng đầy" mới test được.
- Màn hình `/checkout` chỉ hiện **tạm tính**; phí ship/COD phụ thuộc khu vực và
  phương thức thanh toán nên chỉ chốt ở trang xác nhận (app không dùng JS).
- Không đăng nhập, không thanh toán thật, không quản lý đơn sau khi đặt.
- Chạy `debug=True`, bind `127.0.0.1`, `secret_key` hard-code — chỉ để chạy cục bộ.

## Ảnh bìa sản phẩm

Ảnh lấy từ Wikimedia Commons, chỉ chọn file có giấy phép cho phép dùng lại
(CC0 / Public domain / CC BY / CC BY-SA), đã thu nhỏ về ≤ 640px và nén (tổng
~400 KB). Bảng ghi công đầy đủ: `app/static/images/CREDITS.md` — giữ nguyên
bảng đó khi dùng lại ảnh CC BY / CC BY-SA.

Sản phẩm trong seed là hư cấu, không liên quan tới thương hiệu xuất hiện trong
ảnh. Cột `products.image` giữ tên file; để rỗng thì trang tự dùng
`placeholder.svg`.
