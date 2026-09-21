# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo này là gì

Đây **không phải một ứng dụng**, mà là một bộ 2 **Claude Code Skill** (`skills/*/SKILL.md`)
đóng gói quy trình kiểm thử: (prompt mô tả nghiệp vụ | file testcase có sẵn | file `.feature`
có sẵn) → `.feature` + step defs → chạy test + báo cáo. "Sản phẩm" của repo là văn bản
SKILL.md; script Python duy nhất còn lại (`scripts/validate_skills.py`) chỉ lint frontmatter
của các SKILL.md, không tham gia vào quy trình sinh test — `autotest-gen-test` không còn
phụ thuộc script nào, AI đọc trực tiếp nguồn đầu vào và tự viết Gherkin.

Khi sửa repo này, phân biệt rõ 2 ngữ cảnh đường dẫn:
- **Của repo skill** (ở đây): `scripts/validate_skills.py`, `tests/`, `examples/`.
- **Của project sẽ được test** (nơi skill chạy khi cài đi chỗ khác): `testing/features/…`,
  `testing/steps/…`, `reports/…`. SKILL.md nhắc tới các đường dẫn đó là nói về project đích,
  đừng tạo chúng trong repo này.

## Lệnh thường dùng

```bash
.venv/bin/pytest tests -q                              # unit test cho validate_skills.py
.venv/bin/python scripts/validate_skills.py             # lint frontmatter + file tham chiếu của mọi SKILL.md
```

Máy này **không có `python` trên PATH** — dùng `.venv/bin/python` (hoặc `python3`).

Phụ thuộc của bản thân bộ skill: chỉ Python 3.10+ với `pytest` (cho `tests/`). Không cần
Node.js/`npx` — dependency đó (pict-cli) thuộc về skill `autotest-testcase-pairwise` đã bị
xoá; xem mục "Lịch sử tái cấu trúc" bên dưới.

## Kiến trúc

### Nguyên tắc chi phối `autotest-gen-test`

`autotest-gen-test` nhận 1 trong 3 nguồn đầu vào và tự viết `.feature` + step definitions,
**tự verify bằng cách chạy thật** trước khi báo hoàn thành:

1. **Prompt mô tả nghiệp vụ** — chưa có file testcase/`.feature` nào; AI đọc requirement +
   mã nguồn thật, tự thiết kế Scenario/Scenario Outline (được chủ động chọn case, nhưng phải
   hỏi người dùng khi thiếu business rule quan trọng, không tự bịa).
2. **File testcase có sẵn** (xlsx/csv/markdown/text bất kỳ định dạng) — file này là nguồn
   chân lý cho danh sách case; AI đọc trực tiếp (không qua script), không tự thêm/bớt/sửa
   case đã liệt kê.
3. **File `.feature` có sẵn** — chỉ viết step definitions còn thiếu, không sửa Gherkin đã có.

Khác với thiết kế cũ (xem lịch sử bên dưới), **không còn ranh giới "AI chỉ viết template, script
tính tổ hợp"** — vì không còn công đoạn sinh ma trận pairwise xác định trong repo này. Bù lại,
`autotest-gen-test` giữ nguyên các yêu cầu chất lượng độc lập với nguồn đầu vào: mỗi
Scenario/hàng Examples có ID ổn định (`[TC-xxx]`/`[BC-xxx]`, giữ nguyên khi thêm case mới),
oracle độc lập với code app, và bắt buộc verify 3 lớp (collect → chạy thật → mutation check).

### Quy tắc nghiệp vụ nằm trong SKILL.md (không có trong code)

Khi sửa nội dung skill, giữ các ràng buộc sau — chúng là lý do bộ skill này đáng dùng:

- `autotest-gen-test`: **oracle phải độc lập với code app** (đọc dữ liệu thô từ DB/API rồi
  tự viết lại công thức trong test; cấm `import` hàm tính toán của app, cấm hard-code số khi
  tính được từ dữ liệu thô). Verify bắt buộc 3 lớp: `--collect-only` → chạy thật →
  **mutation check** (tiêm lỗi vào app, xác nhận test FAIL, gỡ sạch). Không tự thêm/bớt case
  khi nguồn là file testcase có sẵn.
- `autotest-run-test`: chỉ tự sửa lỗi kịch bản/selector; **không sửa code app**, không nới
  assertion hay tăng `--reruns` cho tới khi pass. Pass-sau-rerun bị đánh dấu "nghi flaky".
- SKILL.md phải trỏ script/asset bằng "thư mục chứa SKILL.md đang đọc", **không hardcode
  `.claude/skills/...`** — skill có thể cài global ở `~/.claude/skills/`.

### Ràng buộc do `scripts/validate_skills.py` áp

- `name:` trong frontmatter phải **khớp chính xác tên thư mục** (lệch → Claude nạp sai skill).
- `description` ≥ 60 ký tự và phải nói rõ KHI NÀO dùng skill.
- Mọi đường dẫn trong backtick dạng `references/…`, `scripts/…`, `assets/…` phải tồn tại —
  trừ khi skill không có thư mục top-level đó (khi ấy hiểu là đường dẫn của project đích).

## `examples/shop-order/`

App demo **chạy được** (Flask + SQLite, `.venv` riêng, `pip install -r requirements.txt`)
— dùng làm đối tượng để thử `autotest-gen-test` (nguồn = prompt, đọc `README.md` làm
requirement) rồi `autotest-run-test`. **Chỉ app được commit**: artifact sinh test
(`testing/`, `reports/`, `pytest.ini`) nằm trong `examples/shop-order/.gitignore` vì sinh
lại được bằng 2 skill — đừng bỏ ignore để commit chúng.

Luồng: danh sách → chi tiết → giỏ hàng (session) → `/checkout` → `/order/<mã>`. Mọi
phần tử UI có `data-testid`, mọi số tiền có `data-value` thô, `db/seed_data.py` reset DB
về trạng thái sạch, `GET /api/cart` + `/api/orders/<code>` đọc state dạng JSON. Business
rule nằm ở `app/pricing.py` (công thức tiền), `app/cart.py` (quy tắc giỏ) và `app/app.py`
(validate form) — chi tiết trong README của nó.

### `shop-order/bugs/` — lỗi cố ý cho mutation testing

`bugs/bugs.py apply|revert|status` bật/tắt 6 lỗi nghiệp vụ đã gieo sẵn vào app, để kiểm tra
bộ test sinh ra có thật sự "có răng". Quy tắc khi làm việc ở đây:

- **`examples/shop-order/README.md` là spec đúng**, kể cả khi code đang bị gieo lỗi — khi
  dùng `autotest-gen-test` cho app này, lấy requirement từ README, đừng suy spec ra từ
  `app/pricing.py` hay `app/app.py`.
- **Đừng đọc `bugs/README.md`** (đáp án: lỗi ở đâu, test nào bắt được) trong lúc đang sinh
  code test — đọc trước là làm hỏng phép thử.
- App có lỗi đang bật là trạng thái tạm; `revert` trước khi commit.

## Lịch sử tái cấu trúc

Repo trước đây có 5 skill: `autotest-factor-analysis` → `autotest-testcase-pairwise`
(sinh `testcase-pairwise.xlsx` bằng `pict-cli`, có `MatrixID` hash sha1 theo tổ hợp,
cơ chế `--check` chống drift) → `autotest-gen-test` (dựng `.feature` từ đúng xlsx đó bằng
script `xlsx_to_feature.py`) → `autotest-run-test`, điều phối bởi `autotest-pipeline`. Hai
skill đầu và skill điều phối đã bị **xoá**: `autotest-gen-test` giờ là điểm vào trực tiếp,
nhận prompt/file testcase/`.feature` có sẵn thay vì chỉ nhận `testcase-pairwise.xlsx`. Nếu
gặp tài liệu/commit cũ nhắc tới `factor.md`, `testcase-pairwise.xlsx`, `pict_to_xlsx.py`,
hay `autotest-pipeline`, hiểu đó là thiết kế cũ đã bỏ, không phải lỗi thiếu file.

## Ngôn ngữ

Toàn bộ tài liệu, docstring, comment và message lỗi viết bằng tiếng Việt — giữ nguyên quy ước
này khi thêm nội dung mới.
