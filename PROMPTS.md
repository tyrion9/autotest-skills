# Hướng dẫn prompt từng bước — dùng `autotest-skills` cho 1 tính năng bất kỳ

Copy từng prompt bên dưới, gõ vào Claude Code (đã cài skill — xem README mục
Cài đặt), **chạy tuần tự từng bước, đọc/kiểm tra artifact sinh ra trước khi
sang bước kế tiếp**. Mỗi prompt có 1 bản mẫu tổng quát (điền `<...>` theo
project của bạn) và 1 bản đã điền sẵn theo ví dụ `examples/cafe-checkout/`
trong repo này để bạn hình dung.

## Bước 0 — Chuẩn bị (làm 1 lần)

1. Mở Claude Code **tại thư mục gốc project cần test** (không phải thư mục
   chứa bộ skill này).
2. Cài skill (nếu chưa cài — xem README mục Cài đặt):
   ```bash
   gh skill install tyrion9/autotest-skills
   gh skill install takeyaqa/tester-skills   # bắt buộc, dùng ở bước 2
   ```
   Khởi động lại Claude Code sau khi cài để skill được nạp.
3. Đảm bảo project có: Node.js (`npx`), Python 3.10+, và cài
   `pip install openpyxl pytest pytest-bdd playwright pytest-html` +
   `python -m playwright install chromium` trong venv của project.

## Prompt 1 — Factor analysis

**Mẫu tổng quát:**
```
Dùng skill autotest-factor-analysis để phân tích factor cho tính năng
"<tên tính năng/màn hình>" trong project này. Đọc kỹ <đường dẫn file UI>,
<đường dẫn file xử lý/validation>, <đường dẫn schema DB nếu có> để lấy đúng
field, giá trị hợp lệ, và ràng buộc thật — không suy đoán nếu thiếu thông
tin, hãy hỏi tôi. Ghi kết quả vào testing/factor/<ten-tinh-nang>.factor.md.
```

**Ví dụ đã điền** (theo `examples/cafe-checkout/`):
```
Dùng skill autotest-factor-analysis để phân tích factor cho tính năng
"chọn đồ uống và thanh toán" trong project này. Đọc kỹ app/app.py,
app/templates/index.html, app/static/app.js, db/seed_data.py để lấy đúng
field, giá trị hợp lệ, và ràng buộc thật. Ghi kết quả vào
testing/factor/checkout.factor.md.
```

**Kiểm tra**: mở file `.factor.md` vừa tạo — mỗi Factor/Constraint/Case biên
phải có cột "Nguồn" trỏ tới requirement hoặc `file:dòng` cụ thể, không có
mục nào ghi chung chung không kiểm chứng được. Nếu có mục "Câu hỏi mở" quan
trọng, trả lời trước khi sang Prompt 2.

## Prompt 2 — Testcase pairwise

**Mẫu tổng quát:**
```
Dùng skill autotest-testcase-pairwise để sinh testcase-pairwise.xlsx từ
testing/factor/<ten-tinh-nang>.factor.md. Dựng model PICT và file
gherkin-template cần thiết, chạy pict-cli qua skill design-pairwise-tests,
xuất ra testing/testcase-pairwise.xlsx.
```

**Ví dụ đã điền:**
```
Dùng skill autotest-testcase-pairwise để sinh testcase-pairwise.xlsx từ
testing/factor/checkout.factor.md. Dựng model PICT và file gherkin-template
cần thiết, chạy pict-cli qua skill design-pairwise-tests, xuất ra
testing/testcase-pairwise.xlsx.
```

**Kiểm tra**: script tự in ra số dòng Pairwise/Boundary — đối chiếu với ước
lượng thô (số tổ hợp đầy đủ = tích số level các factor) để thấy pairwise
thực sự giảm đáng kể số dòng. Mở `.xlsx`, đọc vài dòng cột **Gherkin** xem
có đọc hiểu được ngay không (không cần mở code); xem sheet `meta` để biết
model/seed/thống kê đã dùng. Cột `MatrixID` phải có dạng `TC-xxxxxx`/`BC-xxxxxx`
(ID ổn định theo nội dung, không phải số thứ tự).

## Prompt 3 — Gen test

**Mẫu tổng quát:**
```
Dùng skill autotest-gen-test để sinh testing/features/<ten-tinh-nang>.feature
và step definitions Python (pytest-bdd + Playwright) từ
testing/testcase-pairwise.xlsx. Nhớ tự verify: `pytest --collect-only` rồi
chạy thử thật (headless) trước khi báo hoàn thành; lỗi thì tự sửa rồi chạy
lại, tối đa 3 lần; nếu không tự sửa được (thiếu nghiệp vụ) thì dừng lại hỏi
tôi.
```

**Ví dụ đã điền:**
```
Dùng skill autotest-gen-test để sinh testing/features/checkout.feature và
step definitions Python (pytest-bdd + Playwright) từ
testing/testcase-pairwise.xlsx. Tự verify bằng collect + chạy thử trước khi
báo hoàn thành.
```

**Kiểm tra**:
```bash
pytest testing --collect-only -q
```
Phải hiện đúng số test = số dòng trong xlsx, không có lỗi "step chưa định
nghĩa"/lỗi cú pháp.

## Prompt 4 — Run test

**Mẫu tổng quát:**
```
Dùng skill autotest-run-test để chạy toàn bộ bộ test vừa sinh cho
"<ten-tinh-nang>", seed dữ liệu test cần thiết, phân loại rõ bug thật vs lỗi
kịch bản nếu có fail, và xuất báo cáo (report.html, allure-report nếu có cài
Allure CLI, test_summary.md).
```

**Ví dụ đã điền:**
```
Dùng skill autotest-run-test để chạy toàn bộ bộ test checkout vừa sinh, seed
dữ liệu test, và xuất báo cáo đầy đủ.
```

**Kiểm tra**: đọc phần tổng kết Claude đưa ra (bao nhiêu pass/fail, cái gì tự
sửa, cái gì cần review) — mở `reports/allure-report/index.html` (nếu có) để
xem chi tiết request/response từng scenario.

## Cách gộp 4 bước thành 1 prompt (dùng `autotest-pipeline`)

```
Dùng autotest-pipeline để tự động hoá kiểm thử pairwise cho tính năng
"<tên tính năng>" của project này, từ đọc code tới báo cáo test. Dừng lại
hỏi tôi nếu có điểm không rõ ràng (factor/constraint mơ hồ, thiếu tham số
môi trường, hoặc gặp lỗi không tự sửa được).
```

## Prompt 5 (làm 1 lần cho mỗi project) — gắn chống drift vào CI

```
Thêm vào CI của project 2 bước kiểm tra chống drift của autotest-skills:
chạy pict_to_xlsx.py ... --check và xlsx_to_feature.py ... --check để CI fail
nếu testcase-pairwise.xlsx hoặc .feature bị sửa tay / lệch khỏi factor.md.
Dùng Node 22 hoặc 24 (yêu cầu của pict-cli).
```

Không có bước này, sau vài tháng `.xlsx`/`.feature` sẽ lệch khỏi `factor.md`
mà không ai phát hiện — testcase trong Excel nói một đằng, test chạy một nẻo.

## Khi tính năng thay đổi (chạy lại 1 phần, không phải từ đầu)

- Chỉ đổi giá trị/factor → sửa lại `testing/factor/<feature>.factor.md`,
  chạy lại **Prompt 2 → 3 → 4**.
- Chỉ đổi UI (đổi `data-testid`, thêm field mới không đổi logic) → chạy lại
  **Prompt 3 → 4** (không cần phân tích factor lại).
- Chỉ muốn chạy lại test đã có (không đổi gì) → chỉ cần **Prompt 4**.
