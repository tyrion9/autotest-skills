# Factor Analysis — Chọn đồ uống và thanh toán (checkout)

> File này được sinh áp dụng skill `autotest-factor-analysis` NGƯỢC LẠI vào
> tính năng checkout ĐÃ CÓ trong repo, dùng để validate bộ `autotest-skills`
> (xem `.claude/skills/autotest-*`). Nội dung phải khớp với
> `testing/features/checkout.feature` đang có.

## 1. Nguồn
- Requirement: màn hình menu quán cà phê — chọn đồ uống, tuỳ chỉnh, số
  lượng, thanh toán, hệ thống hiển thị đúng tổng tiền cần thanh toán.
- Mã nguồn đã đọc:
  - `app/templates/index.html` — các control trên UI (size/sugar/ice/topping/
    quantity/payment-method), toàn bộ có `data-testid`.
  - `app/app.py:29-31` — `VALID_SUGAR`, `VALID_ICE`, `VALID_PAYMENT`.
  - `app/app.py:60-61` — chặn checkout khi giỏ hàng trống.
  - `app/app.py:77` — chặn số lượng ≤ 0.
  - `app/app.py:81-82` — ràng buộc `hot_only` → đá phải 0%.
  - `db/seed_data.py` (`PRODUCTS`, `SIZES`, `TOPPINGS`) — danh sách giá trị
    thật của Drink/Size/Topping và cờ `hot_only` (Bạc xỉu = 1).
- Phạm vi test: GUI E2E — luồng "thêm 1 món vào giỏ → thanh toán → xem tổng
  tiền", tương ứng `testing/features/checkout.feature`.

## 2. Bảng Factor & Levels

| Factor | Levels (giá trị đại diện + biên) | Đưa vào pairwise? | Nguồn |
|---|---|---|---|
| Drink | CaPheDen, CaPheSua, BacXiu, TraDao, MatchaLatte | Có | `db/seed_data.py:PRODUCTS` |
| Size | S, M, L | Có | `db/seed_data.py:SIZES` |
| Sugar | 0, 30, 50, 70, 100 | Có | `app/app.py:29` |
| Ice | 0, 30, 50, 100 | Có | `app/app.py:30` |
| Topping | None, TranChau, Thach | Có | `db/seed_data.py:TOPPINGS` |
| Quantity | 1, 2, 5, 20 (đại diện; biên xem mục 4) | Có | Không giới hạn cứng giá trị hợp lệ trong code — chọn đại diện nhỏ/thường/lớn |
| PaymentMethod | Cash, Card, EWallet | Có | `app/app.py:31` |

## 3. Constraints (ràng buộc giữa các factor)

| # | Điều kiện (ngôn ngữ tự nhiên) | Nguồn | Ghi chú cú pháp PICT nháp |
|---|---|---|---|
| 1 | Nếu Drink = BacXiu (chỉ phục vụ nóng) thì Ice phải = 0 | `app/app.py:81-82`, `db/seed_data.py` (`hot_only=1` cho BacXiu) | `IF [Drink] = "BacXiu" THEN [Ice] = 0;` |

## 4. Case biên / Negative (KHÔNG đưa vào ma trận pairwise)

| # | Mô tả case | Input | Kết quả mong đợi | Nguồn |
|---|---|---|---|---|
| 1 | Số lượng = 0 không được thêm vào giỏ | Quantity = 0, các factor khác bất kỳ (vd CaPheDen/S/50/50/None) | Hiển thị lỗi số lượng không hợp lệ; giỏ hàng vẫn trống | `app/app.py:77` + xử lý phía client `app/static/app.js` |
| 2 | Không thể thanh toán khi giỏ hàng trống | Giỏ hàng rỗng, bấm "Thanh toán" | Hiển thị lỗi giỏ hàng trống; không tạo đơn hàng | `app/app.py:60-61` |

## 5. Câu hỏi mở / Giả định
- Không có câu hỏi mở — toàn bộ factor/constraint/case biên đều trích được từ
  code thật đang chạy, không có giả định nào cần xác nhận thêm.
