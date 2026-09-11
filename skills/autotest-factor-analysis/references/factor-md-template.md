# Template `factor.md`

Copy cấu trúc dưới đây khi tạo `testing/factor/<ten-tinh-nang>.factor.md`.
Phần trong `{...}` là chỗ cần điền; phần còn lại giữ nguyên tiêu đề mục.

```markdown
# Factor Analysis — <Tên tính năng/màn hình>

## 1. Nguồn
- Requirement: {tóm tắt hoặc link tới requirement gốc}
- Mã nguồn đã đọc: {đường dẫn file:dòng, vd app/app.py:60-95, app/templates/index.html, db/schema.sql}
- Phạm vi test: {GUI E2E / API / cả hai} — {mô tả ngắn luồng cụ thể đang test}

## 2. Bảng Factor & Levels

| Factor | Levels (giá trị đại diện + biên) | Đưa vào pairwise? | Nguồn |
|---|---|---|---|
| {TênFactor1} | {giá trị 1, giá trị 2, ...} | Có | {file:dòng hoặc đoạn requirement} |
| {TênFactor2} | {...} | Có | {...} |
| {TênFactorN} | {...} | Không (xem mục 4) | {...} |

Quy ước đặt tên Factor: viết liền không dấu, PascalCase (vd `PaymentMethod`,
`Quantity`) — sẽ dùng trực tiếp làm tên tham số PICT và tên cột trong xlsx.

## 3. Constraints (ràng buộc giữa các factor)

| # | Điều kiện (ngôn ngữ tự nhiên) | Nguồn | Ghi chú cú pháp PICT nháp |
|---|---|---|---|
| 1 | {Nếu Factor A = X thì Factor B phải = Y} | {file:dòng} | `IF [A] = "X" THEN [B] = Y;` |

## 4. Case biên / Negative (KHÔNG đưa vào ma trận pairwise)

| # | Mô tả case | Input | Kết quả mong đợi | Nguồn |
|---|---|---|---|---|
| 1 | {vd: số lượng = 0} | {...} | {hệ thống báo lỗi gì, không tạo gì} | {file:dòng} |

## 5. Câu hỏi mở / Giả định
- [ ] {Câu hỏi cần xác nhận với người dùng/PO trước khi chốt, nếu có}
- Giả định: {giả định đã tự đưa ra vì requirement không nói rõ, nêu rõ để người review biết đây là suy đoán}
```

## Ghi chú khi điền
- Mỗi hàng trong bảng Factor & Levels và Constraints PHẢI có cột "Nguồn" trỏ
  tới requirement hoặc code thật — không để trống trừ khi đó là giả định đã
  ghi rõ ở mục 5.
- Factor đưa vào pairwise nên có tương tác thực sự với ít nhất 1 factor khác
  (ảnh hưởng lẫn nhau tới kết quả); nếu 1 factor chỉ cần test độc lập, đưa vào
  mục 4 thay vì pairwise để tránh nổ số dòng không cần thiết.
