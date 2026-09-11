# autotest-skills

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
| `autotest-run-test` | Chạy test, phân loại bug thật (không tự sửa app) / lỗi kịch bản (tự sửa) / flaky, sinh báo cáo |

Xem chi tiết từng bước trong `skills/<tên-skill>/SKILL.md`.

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
- Node.js 18+ (`npx pict-cli@0.2`)
- Python 3.10+, `openpyxl` (2 script sinh/đọc `.xlsx`)
- `pytest`, `pytest-bdd`, `playwright` (Python) — engine chạy test thật
- (Tuỳ chọn) [Allure Commandline](https://allurereport.org/docs/install/) để
  xem báo cáo HTML chi tiết (request/response, ảnh chụp màn hình, tham số
  theo scenario)

## Cách dùng — prompt từng bước

Xem **[`PROMPTS.md`](./PROMPTS.md)**: prompt mẫu (kèm bản đã điền theo ví dụ
cafe-checkout) cho từng bước 1→4, cách kiểm tra kết quả sau mỗi bước, prompt
gộp dùng `autotest-pipeline`, và cách chạy lại 1 phần khi tính năng đổi nhỏ.

## Ví dụ đã validate

`examples/cafe-checkout/` — artifact thật sinh ra khi áp dụng bộ skill này
vào tính năng "chọn đồ uống & thanh toán" của 1 app demo (Flask + SQLite):
`checkout.factor.md` → `checkout.model.txt` +
`checkout.gherkin-template.txt` → `testcase-pairwise.xlsx` (27 dòng Pairwise
+ 2 Boundary) → `checkout.feature`. Đã chạy lại toàn bộ quy trình này trong 1
thư mục clean-room (không có sẵn file nào ở trên) và xác nhận: 27 dòng
Pairwise khớp 100% từng ký tự với bộ ở đây; bộ test Python sinh ra chạy thật
bằng Playwright cho kết quả **29/29 PASS**.

## Playwright: MCP vs thư viện Python

`autotest-gen-test` sinh step definitions dùng **thư viện `playwright`
(Python)** — engine chạy test thật, lặp lại được, phù hợp CI. `@playwright/mcp`
(MCP server) là công cụ KHÁC, dùng khi AI assistant cần tương tác trực tiếp
với trình duyệt thật để THIẾT KẾ/GỠ LỖI test (xem DOM thật, tự sửa selector
hỏng) — không dùng để chạy bộ test tự động.

## License

MIT
