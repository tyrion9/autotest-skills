# autotest-skills

[![CI](https://github.com/tyrion9/autotest-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/tyrion9/autotest-skills/actions/workflows/ci.yml)

Bộ 5 [Claude Code Skill](https://docs.claude.com/en/docs/claude-code/skills)
biến quy trình kiểm thử **requirement → pairwise → code test → chạy + báo
cáo** thành các bước lặp lại được, dùng cho bất kỳ màn hình/API nào — không
gắn cứng vào 1 app cụ thể.

```
Requirement / mô tả màn hình / mã nguồn thật
        │  autotest-factor-analysis
        ▼
factor.md            (Factor & Levels, Constraints, Case biên, câu hỏi mở)
        │  autotest-testcase-pairwise   (dùng pict-cli qua skill design-pairwise-tests)
        ▼
testcase-pairwise.xlsx   (MatrixID, factor..., Loại, Gherkin, Kết quả mong đợi)
        │  autotest-gen-test
        ▼
.feature + step definitions Python (đã pytest --collect-only + chạy thử OK)
        │  autotest-run-test
        ▼
Kết quả test + report.html + allure-report/ + test_summary.md
```

Triết lý: **AI chỉ làm phần cần phán đoán ngôn ngữ/nghiệp vụ (đọc requirement
ra factor, đặt tên, viết 1 template Gherkin)**; mọi phép **tính tổ hợp**
(pairwise) và **ghép chuỗi dữ liệu → Gherkin/Excel** đều giao cho script xác
định (`pict-cli`, 2 script Python trong repo này) — không để AI tự bịa dòng
testcase nào.

## 5 skill

| Skill | Input → Output |
|---|---|
| `autotest-pipeline` | Điều phối 4 bước dưới, quy định rõ điểm nào phải dừng hỏi người dùng thay vì tự đoán |
| `autotest-factor-analysis` | Requirement + code thật → `factor.md` |
| `autotest-testcase-pairwise` | `factor.md` → `testcase-pairwise.xlsx` (script `pict_to_xlsx.py`) |
| `autotest-gen-test` | `testcase-pairwise.xlsx` → `.feature` + step defs, **tự verify** trước khi báo xong (script `xlsx_to_feature.py`) |
| `autotest-run-test` | Chạy test, phân loại bug thật (không tự sửa app) / lỗi kịch bản (tự sửa) / flaky, sinh báo cáo. Có **chế độ trình diễn** `--demo`: trình duyệt hiện hình, chậm từng bước, in chi tiết từng testcase, dừng chờ tester bấm tiếp |

Xem chi tiết từng bước trong `skills/<tên-skill>/SKILL.md`.

## Đặc tính production

| Vấn đề thường gặp khi tự động sinh test | Cách bộ skill này xử lý |
|---|---|
| ID testcase xô lệch mỗi lần regenerate → bug report cũ trỏ sai | `MatrixID` **hash theo nội dung tổ hợp** (`TC-xxxxxx`): cùng 1 tổ hợp luôn cùng 1 ID, kể cả khi đổi vị trí dòng |
| File Excel/`.feature` bị sửa tay rồi lệch khỏi nguồn | Cả 2 script có `--check` → exit 1 khi lệch, gắn vào CI là chặn được |
| Không biết file testcase cũ sinh ra từ đâu | Sheet `meta` trong xlsx ghi model/seed/order/hash/thống kê pict |
| Sai tên factor trong template → dữ liệu hỏng âm thầm | Placeholder lạ → **báo lỗi dừng hẳn** (có `--allow-unknown-placeholders` khi thật sự cần) |
| Bảng "case biên" viết khác tên cột → mất case mà không ai biết | Nhận nhiều biến thể tên cột, không khớp thì **báo lỗi**, không im lặng trả rỗng |
| Giá trị chứa `\|` hoặc xuống dòng làm vỡ bảng Gherkin | Tự escape khi sinh Examples |
| Flaky bị "chạy lại cho tới khi pass" | Hỗ trợ `pytest-rerunfailures`; case pass-sau-rerun bị đánh dấu **nghi flaky** trong báo cáo |
| Mỗi project tự viết lại hook báo cáo | Plugin dùng chung `autotest_reporting.py` (test_summary.md + Allure environment) |
| Tester không tin bộ test vì chỉ thấy dòng `29 passed` | Plugin `autotest_demo.py`: `--demo` chạy có màn hình, chậm lại, in MatrixID + dữ liệu + từng step Gherkin, dừng chờ bấm Enter từng testcase |
| Bản thân công cụ không được kiểm thử | 32 unit test cho 2 script sinh testcase, chạy trên Node 22 & 24 |
| Không biết bộ skill có thật sự bắt được bug hay không | `examples/shop-order/` có 6 lỗi nghiệp vụ gieo sẵn, bật/tắt được, để tự đo trước khi tin dùng — xem mục "Ví dụ: shop-order" bên dưới |

## Cài đặt

```bash
# Cài cho project hiện tại (đặt vào .claude/skills/ của project)
gh skill install tyrion9/autotest-skills
# hoặc
npx skills add tyrion9/autotest-skills

# Cài global (dùng được ở mọi project) — copy nội dung skills/*
# vào ~/.claude/skills/, mỗi skill 1 thư mục con.
```

**Phụ thuộc bắt buộc**: `autotest-testcase-pairwise` dùng lại
[`takeyaqa/tester-skills`](https://github.com/takeyaqa/tester-skills)
(skill `design-pairwise-tests`, bọc `pict-cli` — thuật toán PICT gốc của
Microsoft) để sinh tổ hợp pairwise xác định. Cài thêm:
```bash
gh skill install takeyaqa/tester-skills
```

**Yêu cầu hệ thống** (cho project sẽ được test, không phải cho bản thân bộ
skill):
- **Node.js 22 hoặc 24** — `pict-cli@0.2` khai `engines: ^22 || ^24`. Node
  18/20 (mặc định trên nhiều CI runner) hoặc bản quá mới có thể không chạy
  được; CI của repo này test trên cả 22 và 24.
- Python 3.10+, `openpyxl` (2 script sinh/đọc `.xlsx`)
- `pytest`, `pytest-bdd`, `playwright` (Python) — engine chạy test thật
- Khuyến nghị `pytest-rerunfailures` — xử lý flaky ở tầng CI thay vì chạy lại tay
- (Tuỳ chọn) [Allure Commandline](https://allurereport.org/docs/install/) để
  xem báo cáo HTML chi tiết (request/response, ảnh chụp màn hình, tham số
  theo scenario)

## Phát triển / kiểm thử chính bộ skill

```bash
pip install pytest openpyxl
pytest tests -q                  # 32 unit test cho 2 script sinh testcase
python scripts/validate_skills.py # kiểm tra frontmatter + file tham chiếu của mọi SKILL.md
```
CI (`.github/workflows/ci.yml`) chạy 2 lệnh trên, trên cả Node 22 và 24.

## Cách dùng — prompt từng bước

Xem **[`PROMPTS.md`](./PROMPTS.md)**: prompt mẫu (kèm bản đã điền theo ví dụ
`examples/shop-order`) cho từng bước 1→4, cách kiểm tra kết quả sau mỗi bước,
prompt gộp dùng `autotest-pipeline`, cách chạy lại 1 phần khi tính năng đổi
nhỏ, và **hướng dẫn riêng để săn 6 lỗi cố ý trong shop-order rồi báo cáo**.

## Ví dụ: `examples/shop-order/`

App demo **chạy được** (Flask + SQLite) — xem hàng hoá theo category, giỏ
hàng, màn hình đặt hàng riêng, lưu đơn + thông tin liên hệ. Dùng làm đối
tượng để tự chạy lại cả 4 bước từ đầu. **Chỉ app được commit** — artifact
pipeline (`testing/`, `reports/`) bị ignore vì sinh lại được bằng skill.

Kèm `bugs/bugs.py`: bật/tắt **6 lỗi nghiệp vụ gieo sẵn** (mặc định tắt, app
chạy đúng) để tự đo bộ test sinh ra có "răng" hay không — mutation testing.
Lần chạy tham chiếu: 5 factor → 14 dòng pairwise + 10 case biên = 24
scenario; app đúng cho **24/24 PASS**, bật cả 6 lỗi thì **10 FAIL** — bắt đủ
cả 6. Xem mô tả app + lỗi cố ý trong `examples/shop-order/README.md`, và
prompt từng bước để tự săn bug trong `PROMPTS.md`.

## Playwright: MCP vs thư viện Python

`autotest-gen-test` sinh step definitions dùng **thư viện `playwright`
(Python)** — engine chạy test thật, lặp lại được, phù hợp CI. `@playwright/mcp`
(MCP server) là công cụ KHÁC, dùng khi AI assistant cần tương tác trực tiếp
với trình duyệt thật để THIẾT KẾ/GỠ LỖI test (xem DOM thật, tự sửa selector
hỏng) — không dùng để chạy bộ test tự động.

## License

MIT
