# autotest-skills

[![CI](https://github.com/tyrion9/autotest-skills/actions/workflows/ci.yml/badge.svg)](https://github.com/tyrion9/autotest-skills/actions/workflows/ci.yml)

Bộ 2 [Claude Code Skill](https://docs.claude.com/en/docs/claude-code/skills)
biến quy trình kiểm thử **(prompt / file testcase / .feature có sẵn) → code
test → chạy + báo cáo** thành các bước lặp lại được, dùng cho bất kỳ màn
hình/API nào — không gắn cứng vào 1 app cụ thể.

```
Prompt mô tả nghiệp vụ  ─┐
File testcase có sẵn     ├──  autotest-gen-test  ──> .feature + step definitions
File .feature có sẵn    ─┘    (tự verify: collect     Python (pytest-bdd + Playwright),
                               + chạy thật + mutation   đã chạy thử OK
                               check)
                                        │
                                        ▼
                               autotest-run-test
                                        │
                                        ▼
                    Kết quả test + report.html + allure-report/ + test_summary.md
```

Triết lý: `autotest-gen-test` nhận đúng nguồn người dùng đang có — không bắt
buộc phải đi qua 1 bước sinh ma trận riêng trước — nhưng vẫn giữ kỷ luật chất
lượng bất kể nguồn nào: ID case ổn định để truy vết report, oracle độc lập
với code app, và **tự verify bằng chạy thật + mutation check** trước khi báo
xong, không giao code test chưa kiểm chứng.

## 2 skill

| Skill | Input → Output |
|---|---|
| `autotest-gen-test` | Prompt mô tả nghiệp vụ **hoặc** file testcase có sẵn (xlsx/csv/markdown/text) **hoặc** file `.feature` có sẵn → `.feature` + step defs, **tự verify** (collect + chạy thật + mutation check) trước khi báo xong |
| `autotest-run-test` | Chạy test, phân loại bug thật (không tự sửa app) / lỗi kịch bản (tự sửa) / flaky, sinh báo cáo. Có **chế độ trình diễn** `--demo`: trình duyệt hiện hình, chậm từng bước, in chi tiết từng testcase, dừng chờ tester bấm tiếp |

Xem chi tiết từng skill trong `skills/<tên-skill>/SKILL.md`.

## Đặc tính production

| Vấn đề thường gặp khi tự động sinh test | Cách bộ skill này xử lý |
|---|---|
| ID testcase xô lệch khi thêm case mới → bug report cũ trỏ sai | Mỗi Scenario/hàng Examples có ID ổn định (`[TC-xxx]`/`[BC-xxx]`); case cũ giữ nguyên ID khi thêm case mới |
| Test xanh mà không thật sự kiểm tra được gì | Bắt buộc mutation check: tiêm lỗi vào app, xác nhận test FAIL, gỡ lỗi ngay sau đó |
| Oracle tự khớp chính app (app sai kiểu gì test cũng pass) | Cấm `import` hàm tính toán của app làm kỳ vọng — bắt đọc dữ liệu thô rồi tự viết lại công thức |
| Nguồn testcase có sẵn bị AI tự "biên tập" (thêm/bớt/đổi case) | SKILL.md quy định rõ: file testcase là nguồn chân lý, không tự thêm/bớt case |
| Flaky bị "chạy lại cho tới khi pass" | Hỗ trợ `pytest-rerunfailures`; case pass-sau-rerun bị đánh dấu **nghi flaky** trong báo cáo |
| Known bug đã báo cáo bị lẫn vào Fail mới, gây báo động giả mỗi lần chạy | Case đánh dấu `@pytest.mark.xfail(reason=...)` (chỉ khi PO xác nhận là bug đã biết) được tách riêng cột "Known bug (xfail)" trong `test_summary.md`, không cộng vào Fail; xfail bất ngờ PASS được báo để gỡ tag |
| Mỗi project tự viết lại hook báo cáo | Plugin dùng chung `autotest_reporting.py` (test_summary.md + Allure environment); **Allure là báo cáo mặc định**, tự đính ảnh chụp màn hình PASS/FAIL (UI), lịch sử mọi lời gọi HTTP (URL + mã response) và curl+response thật (API) làm bằng chứng truy vết cho từng scenario |
| Báo cáo lộ thông tin nhạy cảm (API key, password, token...) | `autotest_reporting.py` tự che (`***`) mọi header/field/query-param có tên khớp `key`/`password`/`secret`/`token`/`authorization`/`cookie` trước khi đính vào Allure — cả URL, header, và body JSON lồng nhau |
| URL/path/số điện thoại/data test hard-code thẳng trong step, đổi môi trường phải sửa code | Plugin `autotest_env.py`: biến global (`testing/env/global.yaml`) + biến local theo feature (`testing/env/local/<feature>.yaml`), mỗi file có mục riêng cho UAT/PROD, chọn qua `--test-env` — file YAML tester sửa tay được, không đụng code test |
| Tester không tin bộ test vì chỉ thấy dòng `29 passed` | Plugin `autotest_demo.py`: `--demo` chạy có màn hình, chậm lại, in ID case + dữ liệu + từng step Gherkin, dừng chờ bấm Enter từng testcase |
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

**Yêu cầu hệ thống** (cho project sẽ được test, không phải cho bản thân bộ
skill):
- Python 3.10+, `pytest`, `pytest-bdd`, `playwright` (Python) — engine chạy
  test thật
- `allure-pytest-bdd` (**bắt buộc** — Allure là báo cáo mặc định của bộ
  skill, không phải phần tuỳ chọn; thiếu package này thì mất bằng chứng ảnh
  chụp màn hình + curl/response trong báo cáo)
- `pyyaml` (**bắt buộc** — plugin `autotest_env.py` đọc file biến môi trường
  `testing/env/*.yaml`; thiếu package này thì mọi test dừng ngay lúc nạp
  conftest, không chạy được)
- Khuyến nghị `pytest-rerunfailures` — xử lý flaky ở tầng CI thay vì chạy lại
  tay
- (Tuỳ chọn) [Allure Commandline](https://allurereport.org/docs/install/) chỉ
  cần khi muốn build sẵn báo cáo HTML tĩnh (`allure generate`) tại máy này —
  không có CLI thì vẫn có `reports/allure-results/` (mở bằng `allure serve`
  hoặc build ở máy khác)
- Nếu nguồn đầu vào là file testcase `.xlsx`: `openpyxl` (chỉ cần khi tự mở
  file để đối chiếu bằng tay; `autotest-gen-test` tự đọc nội dung file, không
  gọi thư viện ngoài nào của repo này)

## Phát triển / kiểm thử chính bộ skill

```bash
pip install pytest
pytest tests -q                   # unit test cho scripts/validate_skills.py
python scripts/validate_skills.py # kiểm tra frontmatter + file tham chiếu của mọi SKILL.md
```
CI (`.github/workflows/ci.yml`) chạy 2 lệnh trên.

## Cách dùng — prompt từng bước

Xem **[`PROMPTS.md`](./PROMPTS.md)**: prompt mẫu (kèm bản đã điền theo ví dụ
`examples/shop-order`) cho từng nguồn đầu vào của `autotest-gen-test`, cách
kiểm tra kết quả trước khi chạy `autotest-run-test`, cách chạy lại 1 phần khi
tính năng đổi nhỏ, và **hướng dẫn riêng để săn 6 lỗi cố ý trong shop-order
rồi báo cáo**.

## Ví dụ: `examples/shop-order/`

App demo **chạy được** (Flask + SQLite) — xem hàng hoá theo category, giỏ
hàng, màn hình đặt hàng riêng, lưu đơn + thông tin liên hệ. Dùng làm đối
tượng để tự chạy lại cả 2 bước từ đầu. **Chỉ app được commit** — artifact
sinh test (`testing/`, `reports/`) bị ignore vì sinh lại được bằng skill.

Kèm `bugs/bugs.py`: bật/tắt **6 lỗi nghiệp vụ gieo sẵn** (mặc định tắt, app
chạy đúng) để tự đo bộ test sinh ra có "răng" hay không — mutation testing.
Xem mô tả app + lỗi cố ý trong `examples/shop-order/README.md`, và prompt
từng bước để tự săn bug trong `PROMPTS.md`.

## Playwright: MCP vs thư viện Python

`autotest-gen-test` sinh step definitions dùng **thư viện `playwright`
(Python)** — engine chạy test thật, lặp lại được, phù hợp CI. `@playwright/mcp`
(MCP server) là công cụ KHÁC, dùng khi AI assistant cần tương tác trực tiếp
với trình duyệt thật để THIẾT KẾ/GỠ LỖI test (xem DOM thật, tự sửa selector
hỏng) — không dùng để chạy bộ test tự động.

## License

MIT
