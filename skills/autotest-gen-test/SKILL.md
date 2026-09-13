---
name: autotest-gen-test
description: Sinh code test Python (Gherkin .feature + pytest-bdd step definitions dùng Playwright) từ 1 file testcase-pairwise.xlsx đã có, và TỰ VERIFY (collect + chạy thử) trước khi báo hoàn thành. Dùng khi người dùng nói "sinh test từ testcase-pairwise.xlsx", "viết code test cho các testcase đã có", hoặc bước 3 của autotest-pipeline. Yêu cầu đã có testcase-pairwise.xlsx (nếu chưa, dùng skill autotest-testcase-pairwise trước).
---

# Autotest: Gen Test (testcase-pairwise.xlsx → code test, tự verify)

## Mục tiêu
Biến `testcase-pairwise.xlsx` (nguồn chân lý) thành `.feature` + step
definitions Python (pytest-bdd + Playwright) **chạy thử thành công** trước
khi báo cáo hoàn thành — không giao code chưa kiểm chứng.

## Các bước

1. **Đọc `testing/testcase-pairwise.xlsx`** — coi đây là nguồn chân lý duy
   nhất cho Examples + case biên (KHÔNG tự thêm/bớt dòng khi sinh feature).

2. **Sinh khối Gherkin** bằng script `xlsx_to_feature.py` (nằm trong
   `scripts/` cùng cấp với `SKILL.md` này — skill có thể cài project-scoped
   hoặc global `~/.claude/skills/...`, dùng đúng đường dẫn tuyệt đối tới thư
   mục chứa SKILL.md đang đọc, không hardcode `.claude/skills/...`):
   ```bash
   python <thư_mục_chứa_SKILL.md_này>/scripts/xlsx_to_feature.py \
     testing/testcase-pairwise.xlsx \
     --gherkin-template <feature>.gherkin-template.txt \
     --feature-name "<Tên feature>" \
     --scenario-title "<Tên Scenario Outline>" \
     --background background.txt --then-steps then.txt \
     -o /tmp/generated.feature
   ```
   - Nếu `.feature` CHƯA tồn tại: dùng thẳng output làm file mới tại
     `testing/features/<feature>.feature`.
   - Nếu `.feature` ĐÃ tồn tại (đang cập nhật): so sánh khối `Scenario
     Outline` + `Examples` sinh ra với khối hiện có, chỉ thay phần đó, GIỮ
     NGUYÊN các `Scenario`/`Rule` khác đã có mà không phải do script quản lý.
   - Tên Scenario mang sẵn `MatrixID` ổn định (`[TC-xxxxxx]`, `[BC-xxxxxx]`)
     lấy từ xlsx — **không đổi/không bỏ tiền tố này**, vì báo cáo và truy vết
     ngược về testcase dựa vào nó.
   - Script tự escape ký tự `|` và làm phẳng xuống dòng trong ô Examples —
     không cần xử lý tay, nhưng cũng đừng sửa tay bảng này.

3. **Rà soát step definitions hiện có trước khi viết mới**: `grep` các hàm
   `@given/@when/@then` trong `testing/steps/*.py`, tái dùng step đã có (khớp
   đúng text) — chỉ viết step mới cho phần thật sự chưa có.

4. **Viết step mới** (nếu cần) theo convention đã dùng trong project:
   - Dùng `data-testid` ổn định trên UI (không dùng text hiển thị làm selector
     nếu UI đã có `data-testid`; nếu UI CHƯA có `data-testid` cho phần tử cần
     thao tác, báo cho người dùng — không tự đoán selector CSS mong manh).
   - Với step Then cần biết "kết quả đúng", tính lại giá trị kỳ vọng bằng
     logic nghiệp vụ THẬT của app (module dùng chung với backend nếu có, như
     `app/pricing.py` trong ví dụ cà phê) — không hard-code số liệu kỳ vọng.
   - Với case Boundary do script để lại dạng `# TODO`: viết cụ thể
     Given/When/Then theo mô tả + kỳ vọng đã ghi trong comment.

5. **Tự verify (bắt buộc, không bỏ qua — 3 lớp)**:
   a. **Đồng bộ dữ liệu**: chạy lại script với `--check <file>.feature` —
      xác nhận `.feature` khớp 100% với xlsx (bắt trường hợp sửa tay bảng
      Examples hoặc quên cập nhật sau khi đổi factor).
   b. **Collect**: `pytest <thư mục test> --collect-only -q` — phải sạch,
      không lỗi "step chưa định nghĩa"/lỗi import. Số test collect được phải
      bằng số dòng trong xlsx.
   c. **Chạy thật (headless)**: toàn bộ nếu ít scenario, hoặc tối thiểu 1
      scenario đại diện cho mỗi factor/step mới nếu bộ test đã lớn (`-k`).
   d. Có lỗi → phân loại: lỗi code test tự sửa (selector sai, thiếu import,
      sai kiểu dữ liệu, timing) → sửa → lặp lại (a)-(c), tối đa 3 lần. Lỗi do
      thiếu thông tin nghiệp vụ (không biết kỳ vọng đúng là gì) → DỪNG, hỏi
      người dùng, không đoán đại một giá trị kỳ vọng.

   **Không được báo "đã xong" khi chưa chạy đủ (a)+(b)+(c).** Nếu vì lý do môi
   trường không chạy được (chưa cài browser, app không khởi động được), phải
   nói rõ bước nào chưa verify được và vì sao, thay vì im lặng bỏ qua.

## Definition of done
- `xlsx_to_feature.py --check <file>.feature` cho exit code 0.
- `pytest --collect-only` sạch, số test = số dòng trong xlsx.
- Đã chạy thử thật ít nhất 1 lần và pass (hoặc đã sửa tới khi pass, hoặc đã
  dừng lại báo cáo rõ lý do nếu không tự sửa được).
- Không còn `# TODO` nào trong case Boundary mà chưa viết Given/When/Then cụ
  thể (hoặc đã báo rõ với người dùng phần nào còn để TODO và vì sao).
- Đề xuất cho người dùng thêm 2 lệnh `--check` (xlsx + feature) vào CI của
  project để bảo vệ tính đồng bộ về lâu dài.

## Khi nào KHÔNG tự quyết
- UI thiếu `data-testid` cho phần tử cần thao tác → hỏi có nên thêm
  `data-testid` vào code app hay dùng selector khác, không tự chọn selector
  mong manh rồi âm thầm chấp nhận rủi ro flaky.
- Không rõ giá trị kỳ vọng đúng của 1 step Then (không có công thức/nguồn rõ
  ràng) → hỏi người dùng/PO, không tự đặt một số "có vẻ hợp lý".
