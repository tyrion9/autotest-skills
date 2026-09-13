# Hướng dẫn prompt từng bước — dùng `autotest-skills` cho 1 tính năng bất kỳ

Copy từng prompt bên dưới, gõ vào Claude Code (đã cài skill — xem README mục
Cài đặt), **chạy tuần tự từng bước, đọc/kiểm tra artifact sinh ra trước khi
sang bước kế tiếp**. Mỗi prompt có 1 bản mẫu tổng quát (điền `<...>` theo
project của bạn) và 1 bản đã điền sẵn theo ví dụ `examples/shop-order/`
trong repo này (app Flask + SQLite "shop đặt hàng online" — xem
`examples/shop-order/README.md`) để bạn hình dung.

Repo còn có mục riêng ở cuối file này — **["Săn bug trong shop-order"](#săn-bug-trong-shop-order-dùng-skill-để-tìm-lỗi-cố-ý)**
— dùng chính app đó (đang có 6 lỗi nghiệp vụ gieo sẵn, tắt được/bật được) để
tự đo xem quy trình 4 bước có thật sự phát hiện ra bug hay không, và cách
viết báo cáo bug từ kết quả chạy test.

## Bước 0 — Chuẩn bị (làm 1 lần)

1. Mở Claude Code **tại thư mục gốc project cần test** (không phải thư mục
   chứa bộ skill này). Muốn thử ngay không cần project riêng thì mở tại
   `examples/shop-order/` của repo này.
2. Cài skill (nếu chưa cài — xem README mục Cài đặt):
   ```bash
   gh skill install tyrion9/autotest-skills
   gh skill install takeyaqa/tester-skills   # bắt buộc, dùng ở bước 2
   ```
   Khởi động lại Claude Code sau khi cài để skill được nạp.
3. Đảm bảo project có: Node.js (`npx`), Python 3.10+, và cài
   `pip install openpyxl pytest pytest-bdd playwright pytest-html` +
   `python -m playwright install chromium` trong venv của project.
   Với `examples/shop-order/`:
   ```bash
   cd examples/shop-order
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt pytest pytest-bdd playwright pytest-html openpyxl
   .venv/bin/playwright install chromium
   .venv/bin/python db/seed_data.py       # tạo db/shop.sqlite3, dữ liệu cố định
   cd app && ../.venv/bin/python app.py   # http://127.0.0.1:5001, để chạy song song
   ```

## Prompt 1 — Factor analysis

**Mẫu tổng quát:**
```
Dùng skill autotest-factor-analysis để phân tích factor cho tính năng
"<tên tính năng/màn hình>" trong project này. Đọc kỹ <đường dẫn file UI>,
<đường dẫn file xử lý/validation>, <đường dẫn schema DB nếu có> để lấy đúng
field, giá trị hợp lệ, và ràng buộc thật — không suy đoán nếu thiếu thông
tin, hãy hỏi tôi. Ghi kết quả vào testing/factor/<ten-tinh-nang>.factor.md.
```

**Ví dụ đã điền** (theo `examples/shop-order/`):
```
Dùng skill autotest-factor-analysis để phân tích factor cho luồng "thêm hàng
vào giỏ và đặt hàng" của app trong examples/shop-order/. Requirement lấy từ
examples/shop-order/README.md mục "Quy tắc nghiệp vụ" — README là spec đúng,
không suy spec từ app/pricing.py, app/app.py hay app/cart.py. Ghi kết quả
vào testing/factor/dat-hang.factor.md.
```

**Kiểm tra**: mở file `.factor.md` vừa tạo — mỗi Factor/Constraint/Case biên
phải có cột "Nguồn" trỏ tới requirement hoặc `file:dòng` cụ thể, không có
mục nào ghi chung chung không kiểm chứng được. Nếu có mục "Câu hỏi mở" quan
trọng, trả lời trước khi sang Prompt 2.

> Vì sao chỉ định rõ nguồn = README chứ không phải code? Đây là điểm mấu
> chốt để bài tập "săn bug" ở cuối file này có ý nghĩa: nếu factor.md được
> suy ra từ chính `app/pricing.py`/`app/app.py`, testcase sẽ **kỳ vọng đúng
> theo cái code đang (có thể) sai** — bài test tự triệt tiêu chính nó.

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
testing/factor/dat-hang.factor.md. Dựng model PICT và file gherkin-template
cần thiết, chạy pict-cli qua skill design-pairwise-tests, xuất ra
testing/testcase-pairwise.xlsx.
```

**Kiểm tra**: script tự in ra số dòng Pairwise/Boundary — đối chiếu với ước
lượng thô (số tổ hợp đầy đủ = tích số level các factor) để thấy pairwise
thực sự giảm đáng kể số dòng. Mở `.xlsx`, đọc vài dòng cột **Gherkin** xem
có đọc hiểu được ngay không (không cần mở code); xem sheet `meta` để biết
model/seed/thống kê đã dùng. Cột `MatrixID` phải có dạng `TC-xxxxxx`/`BC-xxxxxx`
(ID ổn định theo nội dung, không phải số thứ tự).

> Lưu ý đặt tên factor: tên factor **không được trùng** các cột dành riêng
> của xlsx (`STT`, `MatrixID`, `Loai`, `Gherkin`, `KetQuaMongDoi`, `GhiChu`)
> — script sẽ báo lỗi dừng hẳn nếu trùng, kèm gợi ý đổi tên (vd đổi
> `GhiChu` → `CoGhiChu`), thay vì âm thầm sinh ra header 2 cột cùng tên và
> làm mất dữ liệu factor đó.

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
Dùng skill autotest-gen-test để sinh testing/features/dat-hang.feature và
step definitions Python (pytest-bdd + Playwright) từ
testing/testcase-pairwise.xlsx. App chạy tại http://127.0.0.1:5001. Oracle
(giá trị kỳ vọng về tiền) phải đọc dữ liệu thô từ db/shop.sqlite3 rồi tự viết
lại công thức theo README — không import app/pricing.py. Tự verify bằng
collect + chạy thử trước khi báo hoàn thành.
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
Dùng skill autotest-run-test để chạy toàn bộ bộ test dat-hang vừa sinh, seed
lại dữ liệu test (db/seed_data.py), và xuất báo cáo đầy đủ.
```

**Kiểm tra**: đọc phần tổng kết Claude đưa ra (bao nhiêu pass/fail, cái gì tự
sửa, cái gì cần review) — mở `reports/allure-report/index.html` (nếu có) để
xem chi tiết request/response từng scenario.

### Prompt 4b — Chạy trình diễn để tester kiểm chứng bằng mắt

```
Dùng skill autotest-run-test, chạy bộ test ở chế độ trình diễn: mở trình duyệt
có màn hình, chậm lại từng thao tác, in chi tiết từng testcase ra console và
dừng chờ tôi bấm Enter sau mỗi testcase.
```

Claude sẽ chạy `pytest <thư mục test> --demo`. Khi đang dừng: `Enter` = case
tiếp theo · `s` = thôi dừng, chạy hết · `q` = dừng phiên. Muốn tự chạy tiếp
thay vì bấm tay thì thêm `--demo-pause=3` (giây); muốn xem chậm hơn nữa thì
`--demo-slowmo=1000 --demo-step-delay=1.5`; muốn xem đúng 1 testcase thì
`-k "TC-4F2A91"`.

**Lưu ý**: kết quả chính thức + báo cáo vẫn lấy từ lần chạy headless bình
thường; `--demo` chỉ để nhìn bằng mắt, đừng bật trong CI.

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

## Săn bug trong shop-order: dùng skill để tìm lỗi cố ý

`examples/shop-order/bugs/` chứa **6 lỗi nghiệp vụ gieo sẵn**, bật/tắt được
bằng 1 lệnh, mặc định đang **tắt** (app chạy đúng). Đây là bài tập tự đo
xem quy trình 4 bước có thật sự "có răng" hay không — và cách viết báo cáo
bug từ kết quả chạy test, giống việc test 1 tính năng thật rồi báo QA/dev.

Đáp án (lỗi nằm ở đâu, cách nó lộ ra, test nào bắt được) nằm ở
`examples/shop-order/bugs/README.md` — **đừng mở file đó trước khi làm xong
bước 4 bên dưới**, mở trước là tự lộ đề, làm hỏng bài tập.

### Bước 1 — Bật lỗi rồi khởi động app

```bash
cd examples/shop-order
.venv/bin/python bugs/bugs.py apply     # bật cả 6 lỗi; --only 1,4 nếu chỉ muốn bật vài lỗi
.venv/bin/python bugs/bugs.py status    # xác nhận đang BẬT
.venv/bin/python db/seed_data.py        # về trạng thái sạch
cd app && ../.venv/bin/python app.py &  # http://127.0.0.1:5001
```

### Bước 2 — Chạy đủ 4 bước (hoặc dùng `autotest-pipeline`)

Nếu chưa có `testing/factor/dat-hang.factor.md` từ trước, chạy tuần tự
**Prompt 1 → 2 → 3 → 4** ở trên (hoặc gộp bằng `autotest-pipeline`). Nếu đã
chạy 1 lần với app đúng rồi, không cần làm lại Prompt 1–3 — `factor.md`,
`testcase-pairwise.xlsx`, `.feature` không phụ thuộc vào app đang đúng hay
sai (chúng bắt nguồn từ README, không phải từ code). Chỉ cần chạy lại
**Prompt 4**:

```
Dùng skill autotest-run-test để chạy lại toàn bộ bộ test dat-hang, seed lại
dữ liệu test, và xuất báo cáo đầy đủ.
```

**Nhắc lại 2 điều bắt buộc** (đã nói ở Prompt 1 và Prompt 3, nhấn mạnh lại
vì đây là chỗ dễ làm hỏng bài tập nếu bỏ qua):
- Nguồn spec là `README.md`, không phải code app.
- Oracle tự viết lại công thức từ dữ liệu thô, không `import` module tính
  toán của app.

### Bước 3 — Đọc kết quả

Kỳ vọng: **có FAIL**. Nếu 6 lỗi đều bật mà toàn bộ test PASS, đó tự nó là
một phát hiện quan trọng — nghĩa là bộ test vừa sinh không đủ "răng" (thường
do oracle lấy kỳ vọng từ chính app, hoặc thiếu case biên/pairwise đúng chỗ);
xem lại Prompt 1–3 trước khi kết luận "app không có bug".

```bash
cat reports/test_summary.md     # bảng MatrixID | scenario | PASS/FAIL | lỗi
open reports/report.html        # chi tiết từng case, lọc theo Failed
```

### Bước 4 — Prompt yêu cầu báo cáo bug

```
Đọc reports/test_summary.md và reports/report.html của lần chạy vừa rồi.
Với mỗi testcase FAIL, viết 1 mục báo cáo bug gồm: MatrixID, tên scenario,
input dùng để tái hiện, kết quả mong đợi (theo README) vs kết quả thực tế
(app trả về), và nghi vấn nó là bug thật hay lỗi kịch bản. Không tự sửa code
app. Gộp các FAIL cùng nguyên nhân gốc thành 1 bug (đừng liệt kê trùng lặp).
```

Đây đúng là việc `autotest-run-test` đã làm khi phân loại fail (xem
"Definition of done" của skill: không sửa code app, chỉ báo cáo kèm bằng
chứng) — prompt trên chỉ yêu cầu trình bày lại thành báo cáo gọn để gửi đi.

### Bước 5 — So đáp án

Bây giờ mở `examples/shop-order/bugs/README.md`, đối chiếu từng bug trong
báo cáo vừa viết với bảng "Danh sách lỗi": có bắt đủ cả 6 không, mô tả có
đúng nguyên nhân gốc không (vd lỗi #2 "phụ phí cồng kềnh tính 1 lần" chỉ lộ
ra khi giỏ có ≥ 2 dòng cồng kềnh — nếu báo cáo mô tả sai thành "tính phí
cồng kềnh sai" chung chung mà không chỉ đúng điều kiện, nghĩa là chưa hiểu
đúng gốc lỗi).

### Bước 6 — Dọn dẹp

```bash
.venv/bin/python bugs/bugs.py revert   # gỡ sạch lỗi, app về đúng — làm TRƯỚC khi commit bất cứ gì
```

`testing/`, `reports/` không commit được (đã ignore) nên không lo dính vào
git, nhưng **luôn `revert` trước khi rời máy** — để lần sau (hoặc người
khác) mở app lên không nhầm tưởng đang gặp bug thật.
