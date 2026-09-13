# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repo này là gì

Đây **không phải một ứng dụng**, mà là một bộ 5 **Claude Code Skill** (`skills/*/SKILL.md`)
đóng gói quy trình kiểm thử: requirement → `factor.md` → `testcase-pairwise.xlsx` →
`.feature` + step defs → chạy test + báo cáo. "Sản phẩm" của repo là văn bản SKILL.md
và 2 script Python đi kèm; `tests/` chỉ kiểm thử 2 script đó.

Khi sửa repo này, phân biệt rõ 2 ngữ cảnh đường dẫn:
- **Của repo skill** (ở đây): `skills/…/scripts/*.py`, `tests/`, `examples/`.
- **Của project sẽ được test** (nơi skill chạy khi cài đi chỗ khác): `testing/factor/…`,
  `testing/features/…`, `reports/…`. SKILL.md nhắc tới các đường dẫn đó là nói về project
  đích, đừng tạo chúng trong repo này.

## Lệnh thường dùng

```bash
.venv/bin/pytest tests -q                    # 32 unit test cho 2 script sinh testcase
.venv/bin/pytest tests/test_pict_to_xlsx.py::test_ten_test -q   # chạy 1 test
.venv/bin/python scripts/validate_skills.py            # lint frontmatter + file tham chiếu của mọi SKILL.md
```

Repo không còn giữ 1 artifact cố định để `--check` (đã bỏ `examples/cafe-checkout/` —
xem mục "`examples/shop-order/`" bên dưới): 32 unit test ở trên là nơi duy nhất kiểm
thử 2 script `pict_to_xlsx.py`/`xlsx_to_feature.py`. Muốn tự tay thử `--check`, chạy
`autotest-testcase-pairwise` + `autotest-gen-test` lên `examples/shop-order/` (sinh
`testing/` tại đó, bị gitignore) rồi chạy lại đúng 2 lệnh đó lần nữa với `--check`.

Máy này **không có `python` trên PATH** — dùng `.venv/bin/python` (hoặc `python3`).

Phụ thuộc: Python 3.10+ với `pytest` + `openpyxl`; **Node.js 22 hoặc 24** (pict-cli@0.2 khai
`engines: ^22 || ^24`) để `pict_to_xlsx.py` gọi được `npx pict-cli`.

## Kiến trúc

### Nguyên tắc chi phối toàn bộ thiết kế

**AI chỉ làm phần cần phán đoán ngôn ngữ/nghiệp vụ; mọi phép tính tổ hợp và ghép chuỗi
đều do script xác định làm.** Cụ thể: AI đọc requirement ra factor, đặt tên, viết **một**
file `gherkin-template.txt` cho cả feature; `pict-cli` tính tổ hợp; `pict_to_xlsx.py` và
`xlsx_to_feature.py` render từng dòng. AI không bao giờ tự viết ra một dòng testcase.
Mọi thay đổi ở repo này phải giữ ranh giới đó.

### Luồng dữ liệu và 2 script

```
factor.md ──(người/AI viết model + gherkin-template)──> model.txt + gherkin-template.txt
     └────────────┐                                              │
                  ▼                                              ▼
        pict_to_xlsx.py  ──(gọi npx pict-cli, + mục 4 factor.md)──> testcase-pairwise.xlsx
                                                                       │
                                        xlsx_to_feature.py ────────────┴──> .feature
```

- `skills/autotest-testcase-pairwise/scripts/pict_to_xlsx.py` (~450 dòng) — gọi `pict-cli`
  (pin `pict-cli@0.2`, `-o order`, `-r seed`), render cột `Gherkin` từ template, đọc bảng
  "Case biên" (mục 4 của `factor.md`) thành dòng `Loai=Boundary`, ghi 2 sheet
  (`testcase-pairwise` + `meta`).
- `skills/autotest-gen-test/scripts/xlsx_to_feature.py` (~240 dòng) — đọc xlsx, dựng
  `Scenario Outline` + bảng `Examples` (tự escape `|`, làm phẳng newline), để lại `# TODO`
  cho dòng Boundary.

`gherkin-template.txt` được **tái dùng nguyên vẹn** ở cả 2 script — đó là lý do khối
`Scenario Outline` không phải viết lại lần hai.

### Các bất biến không được phá

Đây là những quyết định thiết kế đã có chủ đích; sửa script mà làm hỏng chúng là hồi quy:

- **`MatrixID` hash theo nội dung tổ hợp** (`TC-xxxxxx`/`BC-xxxxxx`, sha1 rút gọn, kéo dài
  khi đụng độ), không theo vị trí dòng — để bug report cũ vẫn trỏ đúng tổ hợp sau khi
  regenerate. `STT` chỉ để đọc. `MatrixID` xuyên suốt tên Scenario → Allure → `test_summary.md`.
- **Cả 2 script có `--check`**: không ghi file, so với file trên đĩa, exit 1 khi lệch. Đây là
  cơ chế chống drift duy nhất; CI của repo và của project đích đều dựa vào nó.
- **Thà báo lỗi dừng hẳn còn hơn im lặng trả rỗng**: placeholder `<...>` không khớp tên factor
  → lỗi (thoát bằng `--allow-unknown-placeholders`); bảng case biên không nhận ra cột mô tả →
  lỗi. Tên cột nhận nhiều biến thể qua `DESC_ALIASES`/`INPUT_ALIASES`/`EXPECTED_ALIASES`.
- **Seed mặc định 42, order mặc định 2**: đổi seed là đổi toàn bộ ma trận và mọi `MatrixID`
  pairwise. Sheet `meta` ghi model/seed/order/sha1/`pict_stats` để audit lại được.

### Quy tắc nghiệp vụ nằm trong SKILL.md (không có trong code)

Khi sửa nội dung skill, giữ các ràng buộc sau — chúng là lý do bộ skill này đáng dùng:

- `autotest-gen-test`: **oracle phải độc lập với code app** (đọc dữ liệu thô từ DB/API rồi
  tự viết lại công thức trong test; cấm `import` hàm tính toán của app, cấm hard-code số).
  Verify bắt buộc 4 lớp: `--check` → `--collect-only` → chạy thật → **mutation check** (tiêm
  lỗi vào app, xác nhận test FAIL, gỡ sạch).
- `autotest-run-test`: chỉ tự sửa lỗi kịch bản/selector; **không sửa code app**, không nới
  assertion hay tăng `--reruns` cho tới khi pass. Pass-sau-rerun bị đánh dấu "nghi flaky".
- `autotest-pipeline`: các điểm dừng bắt buộc hỏi người dùng (câu hỏi mở trong `factor.md`,
  tham số môi trường trước khi chạy test).
- SKILL.md phải trỏ script bằng "thư mục chứa SKILL.md đang đọc", **không hardcode
  `.claude/skills/...`** — skill có thể cài global ở `~/.claude/skills/`.

### Ràng buộc do `scripts/validate_skills.py` áp

- `name:` trong frontmatter phải **khớp chính xác tên thư mục** (lệch → Claude nạp sai skill).
- `description` ≥ 60 ký tự và phải nói rõ KHI NÀO dùng skill.
- Mọi đường dẫn trong backtick dạng `references/…`, `scripts/…`, `assets/…` phải tồn tại —
  trừ khi skill không có thư mục top-level đó (khi ấy hiểu là đường dẫn của project đích).

## `examples/shop-order/`

App demo **chạy được** (Flask + SQLite, `.venv` riêng, `pip install -r requirements.txt`)
— dùng làm đối tượng để thử bộ skill từ bước 1. **Chỉ app được commit**: artifact của
pipeline (`testing/`, `reports/`, `pytest.ini`) nằm trong `examples/shop-order/.gitignore`
vì sinh lại được bằng 4 skill — đừng bỏ ignore để commit chúng.

Luồng: danh sách → chi tiết → giỏ hàng (session) → `/checkout` → `/order/<mã>`. Mọi
phần tử UI có `data-testid`, mọi số tiền có `data-value` thô, `db/seed_data.py` reset DB
về trạng thái sạch, `GET /api/cart` + `/api/orders/<code>` đọc state dạng JSON. Business
rule nằm ở `app/pricing.py` (công thức tiền), `app/cart.py` (quy tắc giỏ) và `app/app.py`
(validate form) — chi tiết trong README của nó.

### `shop-order/bugs/` — lỗi cố ý cho mutation testing

`bugs/bugs.py apply|revert|status` bật/tắt 6 lỗi nghiệp vụ đã gieo sẵn vào app, để kiểm tra
bộ test sinh ra có thật sự "có răng". Quy tắc khi làm việc ở đây:

- **`examples/shop-order/README.md` là spec đúng**, kể cả khi code đang bị gieo lỗi — khi
  chạy `autotest-factor-analysis` cho app này, lấy requirement từ README, đừng suy spec ra
  từ `app/pricing.py` hay `app/app.py`.
- **Đừng đọc `bugs/README.md`** (đáp án: lỗi ở đâu, test nào bắt được) trong lúc đang sinh
  testcase hoặc code test — đọc trước là làm hỏng phép thử.
- App có lỗi đang bật là trạng thái tạm; `revert` trước khi commit.

## Ngôn ngữ

Toàn bộ tài liệu, docstring, comment và message lỗi viết bằng tiếng Việt — giữ nguyên quy ước
này khi thêm nội dung mới.
