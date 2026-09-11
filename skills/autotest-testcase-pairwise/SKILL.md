---
name: autotest-testcase-pairwise
description: Sinh testcase-pairwise.xlsx (kèm cột Gherkin) từ 1 file factor.md đã có. Dùng khi người dùng nói "sinh pairwise testcase từ factor.md", "tạo ma trận test từ factor", "xuất testcase ra excel", hoặc bước 2 của autotest-pipeline. Yêu cầu đã có factor.md (nếu chưa có, dùng skill autotest-factor-analysis trước). Luôn dùng pict-cli (qua skill design-pairwise-tests) để sinh tổ hợp — không tự bịa dòng nào.
---

# Autotest: Testcase Pairwise (factor.md → testcase-pairwise.xlsx)

## Mục tiêu
Từ `factor.md` (bảng Factor & Levels + Constraints + Case biên), sinh ra
`testcase-pairwise.xlsx` — nguồn chân lý duy nhất cho bước sinh code test
(`autotest-gen-test`). Xem schema đầy đủ ở
`references/testcase-xlsx-schema.md`.

## Các bước

1. **Đọc `factor.md`**, trích bảng "Factor & Levels" (chỉ lấy factor có "Đưa
   vào pairwise? = Có") và bảng "Constraints".

2. **Dựng file model PICT** (`<feature>.model.txt`), 1 dòng/factor
   `TenFactor: v1, v2, ...`, rồi các constraint theo cú pháp trong
   `../design-pairwise-tests/references/pict-constraints-grammar.md` (lưu ý:
   giá trị số không bọc dấu ngoặc kép, giá trị chuỗi phải bọc).

3. **Viết `<feature>.gherkin-template.txt`**: mỗi dòng 1 step Gherkin đã có từ
   khoá (When/And...), placeholder dùng đúng cú pháp Scenario Outline
   `<TenFactor>` khớp tên cột model — vd `When khách chọn đồ uống "<Drink>"`.
   Đây là bước CẦN phán đoán ngôn ngữ (đọc UI/feature file có sẵn của tính
   năng, hoặc theo convention project đang dùng) — làm 1 lần cho cả feature,
   không lặp lại cho từng dòng dữ liệu. File này được **tái dùng nguyên vẹn**
   ở bước `autotest-gen-test` để dựng khối `Scenario Outline` (không viết lại
   lần 2). Ví dụ tham khảo cách hành văn: `testing/features/checkout.feature`
   (dự án ví dụ cà phê trong repo này).

4. **Chạy pict-cli qua skill `design-pairwise-tests`** để sinh ma trận (mặc
   định pairwise `-o 2`; hỏi người dùng nếu cần n-wise mạnh hơn) — không tự
   tính tổ hợp bằng tay/bằng suy luận của AI.

5. **Chạy script sinh xlsx** — script `pict_to_xlsx.py` nằm ngay trong thư
   mục `scripts/` CÙNG CẤP với file `SKILL.md` này (skill có thể được cài
   project-scoped tại `<project>/.claude/skills/autotest-testcase-pairwise/`
   hoặc global tại `~/.claude/skills/autotest-testcase-pairwise/` — dùng
   đúng đường dẫn tuyệt đối tới thư mục chứa SKILL.md đang đọc, không hardcode
   `.claude/skills/...` vì skill global không nằm trong project):
   ```bash
   python <thư_mục_chứa_SKILL.md_này>/scripts/pict_to_xlsx.py \
     <feature>.model.txt \
     --gherkin-template <feature>.gherkin-template.txt \
     --factor testing/factor/<feature>.factor.md \
     -o testing/testcase-pairwise.xlsx
   ```
   (Cần `pip install openpyxl` nếu chưa có trong venv của project đang test.)

6. **Tự kiểm**:
   - Số dòng Pairwise + Boundary khớp: dòng in ra ở cuối script khớp số dòng
     mong đợi (đếm factor × level thô để ước lượng, không cần bằng — pairwise
     luôn ít hơn tổ hợp đầy đủ).
   - Mở lại file (đọc bằng `openpyxl` hoặc liệt kê nhanh) xác nhận cột
     `Gherkin` của vài dòng Pairwise có nội dung hợp lý, không lỗi
     `KeyError` (placeholder sai tên cột).
   - Đối chiếu 1-2 dòng với Constraint trong factor.md (vd dòng nào có factor
     bị ràng buộc thì giá trị liên quan phải đúng theo constraint).

## Definition of done
- `testing/testcase-pairwise.xlsx` tồn tại, đúng schema (xem
  `references/testcase-xlsx-schema.md`), mở được không lỗi.
- Mọi Constraint trong factor.md đều được phản ánh đúng trong dữ liệu sinh ra
  (không có dòng nào vi phạm ràng buộc).
- Các case Boundary trong factor.md mục 4 đều có mặt (Loai=Boundary).

## Khi nào KHÔNG tự quyết
- Constraint trong factor.md không dịch được sang cú pháp PICT rõ ràng → hỏi
  người dùng cách diễn giải, không tự đơn giản hoá ràng buộc.
- Số lượng testcase pairwise ra quá lớn (vd hàng trăm dòng) → báo cho người
  dùng, đề xuất giảm bớt factor/level hoặc tách nhỏ phạm vi, không tự ý xoá
  bớt dòng.
