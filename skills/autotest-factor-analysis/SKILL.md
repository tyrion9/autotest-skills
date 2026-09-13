---
name: autotest-factor-analysis
description: Phân tích requirement/mô tả màn hình/tham số đầu vào của một tính năng thành factor.md (bảng Factor & Levels, ràng buộc, case biên) làm đầu vào cho sinh testcase pairwise. Dùng khi người dùng nói "phân tích factor cho...", "liệt kê factor/tham số kiểm thử cho màn hình...", "chuẩn bị đầu vào cho pairwise testing", hoặc bước 1 của autotest-pipeline. KHÔNG dùng để tự sinh testcase/matrix (đó là autotest-testcase-pairwise) hay để viết code test.
---

# Autotest: Factor Analysis (Requirement → factor.md)

## Mục tiêu
Biến 1 requirement/mô tả màn hình/tham số API thành danh sách **Factor** (biến
đầu vào có ảnh hưởng tới hành vi cần test) + **Levels** (giá trị đại diện,
gồm cả giá trị biên) + **Constraint** (ràng buộc giữa các factor) — đủ chi
tiết, chính xác để bước sau sinh pairwise mà không cần đoán thêm.

**Nguyên tắc quan trọng nhất: Factor/Level/Constraint phải bắt nguồn từ
requirement + MÃ NGUỒN THẬT của tính năng đang test (form UI, route
validation, schema DB, config), không suy diễn/bịa.** Nếu thiếu thông tin
nghiệp vụ quan trọng, hỏi người dùng — đừng tự giả định rồi ghi vào factor.md
như thể đã xác nhận.

## Các bước

1. **Xác định phạm vi**: 1 màn hình/luồng/API cụ thể (không phân tích cả hệ
   thống trong 1 lần). Xác định mục tiêu test: GUI E2E, API, hay cả hai.

2. **Thu thập nguồn**:
   - Đọc requirement/mô tả người dùng cung cấp.
   - Đọc code thật liên quan: template/form UI (field nào, kiểu dữ liệu, giá
     trị mặc định), route/handler xử lý (validation, business rule), model/DB
     schema (cột, kiểu, ràng buộc NOT NULL/FK/CHECK), config liên quan.
   - Nếu có sẵn ví dụ tham khảo trong repo (như `app/templates/index.html`,
     `app/app.py`, `db/schema.sql` của ví dụ cà phê), dùng làm mẫu về mức độ
     chi tiết cần đạt, KHÔNG copy nội dung của ví dụ đó sang tính năng khác.

3. **Liệt kê Factor**: mỗi input/control/tham số ảnh hưởng tới kết quả là 1
   Factor. Với mỗi Factor, liệt kê **Levels**:
   - Giá trị hợp lệ đại diện (không cần liệt kê hết nếu là dải liên tục — chọn
     đại diện biên trong/ngoài khoảng).
   - Giá trị biên (min, max, rỗng, 0, giá trị đặc biệt theo business rule).
   Đánh dấu Factor nào **có tương tác cặp với factor khác** (đưa vào pairwise)
   và Factor nào chỉ có ý nghĩa test đơn lẻ (đưa vào "Case biên").

4. **Liệt kê Constraint**: ràng buộc giữa các factor, đối chiếu với code
   validation thật (vd "nếu Drink=hot_only thì Ice bắt buộc = 0" lấy từ cột
   `hot_only` + logic check trong `app.py`, không phải suy đoán).

5. **Case biên/negative**: liệt kê riêng các trường hợp không có tương tác
   cặp (input rỗng, giá trị = 0, vượt giới hạn, thiếu field bắt buộc) — các
   case này sẽ thành `Scenario` viết tay ở bước sau, không đưa vào ma trận
   pairwise (đưa vào sẽ làm nổ số dòng không cần thiết).

6. **Câu hỏi mở/giả định**: bất cứ điều gì không rõ ràng từ requirement/code
   (vd business rule không có trong code, giá trị mặc định không tài liệu
   hoá) — ghi thành câu hỏi, và **hỏi người dùng trước khi chốt factor.md**
   nếu nó ảnh hưởng tới việc chọn factor/level/constraint.

7. Ghi ra `factor.md` theo đúng cấu trúc trong
   `references/factor-md-template.md`, đặt tại
   `testing/factor/<ten-tinh-nang>.factor.md` (tạo thư mục nếu chưa có).

   **Bảng mục 4 (Case biên) sẽ được script ở bước sau đọc tự động**, nên phải
   giữ đúng dạng bảng markdown với cột mô tả (`Mô tả case`/`Description`),
   cột input (`Input`/`Đầu vào`), cột kỳ vọng (`Kết quả mong đợi`/`Expected`).
   Script chấp nhận vài biến thể tên cột nhưng sẽ **báo lỗi dừng hẳn** nếu
   không nhận ra cột mô tả — đừng tự đổi cấu trúc bảng này.

8. **Tự review**: đọc lại factor.md, đối chiếu từng dòng với requirement gốc
   — không thiếu field quan trọng, không có factor không có căn cứ.

9. **Rà lại quyết định "pairwise hay case biên"** cho từng factor: factor bị
   xếp nhầm vào mục 4 sẽ KHÔNG bao giờ được test tổ hợp với factor khác, và
   không có cơ chế nào cảnh báo điều đó về sau. Nếu phân vân, mặc định đưa
   vào pairwise (an toàn hơn), hoặc hỏi người dùng.

## Definition of done
- `factor.md` tồn tại, đủ 5 mục (Nguồn, Factor & Levels, Constraints, Case
  biên, Câu hỏi mở/giả định).
- Mọi Factor/Constraint đều trích dẫn được nguồn (đoạn requirement hoặc
  file:dòng code cụ thể).
- Không còn câu hỏi mở nào **quan trọng** (ảnh hưởng factor/constraint) mà
  chưa hỏi người dùng.

## Khi nào KHÔNG tự quyết
- Business rule mơ hồ, không có trong code lẫn requirement → hỏi.
- Không chắc 1 field có nên đưa vào pairwise hay chỉ cần test đơn lẻ → nêu rõ
  trong factor.md phần giả định, hỏi nếu ảnh hưởng lớn tới số lượng testcase.
