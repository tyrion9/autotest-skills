# Hướng dẫn prompt từng bước — dùng `autotest-skills` cho 1 tính năng bất kỳ

Copy từng prompt bên dưới, gõ vào Claude Code (đã cài skill — xem README mục
Cài đặt), **đọc/kiểm tra artifact sinh ra trước khi sang bước kế tiếp**. Mỗi
prompt có 1 bản mẫu tổng quát (điền `<...>` theo project của bạn) và 1 bản đã
điền sẵn theo ví dụ `examples/shop-order/` trong repo này (app Flask + SQLite
"shop đặt hàng online" — xem `examples/shop-order/README.md`) để bạn hình
dung.

Repo còn có mục riêng ở cuối file này — **["Săn bug trong shop-order"](#săn-bug-trong-shop-order-dùng-skill-để-tìm-lỗi-cố-ý)**
— dùng chính app đó (đang có 6 lỗi nghiệp vụ gieo sẵn, tắt được/bật được) để
tự đo xem `autotest-gen-test` + `autotest-run-test` có thật sự phát hiện ra
bug hay không, và cách viết báo cáo bug từ kết quả chạy test.

## Bước 0 — Chuẩn bị (làm 1 lần)

1. Mở Claude Code **tại thư mục gốc project cần test** (không phải thư mục
   chứa bộ skill này). Muốn thử ngay không cần project riêng thì mở tại
   `examples/shop-order/` của repo này.
2. Cài skill (nếu chưa cài — xem README mục Cài đặt):
   ```bash
   gh skill install tyrion9/autotest-skills
   ```
   Khởi động lại Claude Code sau khi cài để skill được nạp.
3. Đảm bảo project có Python 3.10+ và cài
   `pip install pytest pytest-bdd playwright pytest-html` +
   `python -m playwright install chromium` trong venv của project (thêm
   `openpyxl` nếu nguồn testcase của bạn là file `.xlsx` và bạn muốn tự mở
   file đó bằng script riêng — bản thân `autotest-gen-test` không cần).
   Với `examples/shop-order/`:
   ```bash
   cd examples/shop-order
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt pytest pytest-bdd playwright pytest-html
   .venv/bin/playwright install chromium
   .venv/bin/python db/seed_data.py       # tạo db/shop.sqlite3, dữ liệu cố định
   cd app && ../.venv/bin/python app.py   # http://127.0.0.1:5001, để chạy song song
   ```

## Prompt 1 — Gen test

`autotest-gen-test` nhận 1 trong 3 nguồn. Chọn đúng mẫu khớp với thứ bạn
đang có.

### 1a. Nguồn = prompt mô tả nghiệp vụ (chưa có file testcase/.feature nào)

**Mẫu tổng quát:**
```
Dùng skill autotest-gen-test để viết test cho tính năng "<tên tính
năng/màn hình>" của project này. Requirement lấy từ <đường dẫn requirement/
README>, đọc thêm <đường dẫn file UI>, <đường dẫn file xử lý/validation>,
<đường dẫn schema DB nếu có> để lấy đúng field/giá trị hợp lệ/ràng buộc thật
— không suy đoán nếu thiếu thông tin, hãy hỏi tôi. Ghi ra
testing/features/<ten-tinh-nang>.feature + step definitions. Oracle (giá trị
kỳ vọng) phải đọc dữ liệu thô rồi tự viết lại công thức, không import hàm
tính toán của app. Tự verify bằng collect-only + chạy thử thật + mutation
check trước khi báo hoàn thành.
```

**Ví dụ đã điền** (theo `examples/shop-order/`):
```
Dùng skill autotest-gen-test để viết test cho luồng "thêm hàng vào giỏ và
đặt hàng" của app trong examples/shop-order/. Requirement lấy từ
examples/shop-order/README.md mục "Quy tắc nghiệp vụ" — README là spec đúng,
không suy spec từ app/pricing.py, app/app.py hay app/cart.py. App chạy tại
http://127.0.0.1:5001. Oracle (giá trị kỳ vọng về tiền) phải đọc dữ liệu thô
từ db/shop.sqlite3 rồi tự viết lại công thức theo README — không import
app/pricing.py. Ghi ra testing/features/dat-hang.feature + step definitions.
Tự verify bằng collect + chạy thử trước khi báo hoàn thành.
```

> Vì sao chỉ định rõ nguồn = README chứ không phải code? Đây là điểm mấu
> chốt để bài tập "săn bug" ở cuối file này có ý nghĩa: nếu requirement được
> lấy từ chính `app/pricing.py`/`app/app.py`, testcase sẽ **kỳ vọng đúng
> theo cái code đang (có thể) sai** — bài test tự triệt tiêu chính nó.

### 1b. Nguồn = file testcase có sẵn (xlsx/csv/markdown/text)

**Mẫu tổng quát:**
```
Dùng skill autotest-gen-test để sinh testing/features/<ten-tinh-nang>.feature
và step definitions Python (pytest-bdd + Playwright) từ file testcase
<đường dẫn file>. File này là nguồn chân lý cho danh sách case — không tự
thêm/bớt case, không tự đổi input/kỳ vọng đã ghi trong file. Nếu file thiếu
thông tin (cột kỳ vọng, mô tả case không rõ) thì hỏi tôi. Tự verify bằng
collect-only + chạy thử thật + mutation check trước khi báo hoàn thành.
```

**Ví dụ đã điền:**
```
Dùng skill autotest-gen-test để sinh testing/features/dat-hang.feature và
step definitions từ file testing/testcase/dat-hang.xlsx. File này là nguồn
chân lý cho danh sách case. App chạy tại http://127.0.0.1:5001. Oracle (giá
trị kỳ vọng về tiền) phải đọc dữ liệu thô từ db/shop.sqlite3 rồi tự viết lại
công thức theo README — không import app/pricing.py.
```

### 1c. Nguồn = file `.feature` đã viết sẵn (chỉ thiếu step definitions)

**Mẫu tổng quát:**
```
Dùng skill autotest-gen-test để viết step definitions Python (pytest-bdd +
Playwright) cho file <đường dẫn>.feature đã có sẵn. Không sửa nội dung
Gherkin đã viết, chỉ bổ sung step definitions còn thiếu. Tự verify bằng
collect-only + chạy thử thật + mutation check trước khi báo hoàn thành.
```

**Kiểm tra chung cho cả 3 nguồn**:
```bash
pytest testing --collect-only -q
```
Phải hiện đúng số test = số case bạn mong đợi (đếm lại bằng tay theo nguồn
đầu vào — không có lỗi "step chưa định nghĩa"/lỗi cú pháp).

## Prompt 2 — Run test

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

### Prompt 2b — Chạy trình diễn để tester kiểm chứng bằng mắt

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

## Khi tính năng thay đổi (chạy lại 1 phần, không phải từ đầu)

- Đổi input/case cần test (thêm case mới, sửa case cũ) → chạy lại **Prompt 1**
  với đúng nguồn bạn đang dùng (prompt/file testcase/`.feature`), giữ nguyên
  ID case cũ, chỉ thêm ID mới cho case mới.
- Chỉ đổi UI (đổi `data-testid`, thêm field mới không đổi logic) → chạy lại
  **Prompt 1** chỉ để sửa step definitions bị ảnh hưởng (nguồn `.feature`
  không đổi).
- Chỉ muốn chạy lại test đã có (không đổi gì) → chỉ cần **Prompt 2**.

## Săn bug trong shop-order: dùng skill để tìm lỗi cố ý

`examples/shop-order/bugs/` chứa **6 lỗi nghiệp vụ gieo sẵn**, bật/tắt được
bằng 1 lệnh, mặc định đang **tắt** (app chạy đúng). Đây là bài tập tự đo xem
`autotest-gen-test` + `autotest-run-test` có thật sự "có răng" hay không —
và cách viết báo cáo bug từ kết quả chạy test, giống việc test 1 tính năng
thật rồi báo QA/dev.

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

### Bước 2 — Gen test rồi chạy test

Nếu chưa có `testing/features/dat-hang.feature` từ trước, chạy **Prompt 1a**
(nguồn = prompt, requirement lấy từ README) rồi **Prompt 2** ở trên. Nếu đã
chạy 1 lần với app đúng rồi, không cần làm lại Prompt 1 — `.feature` không
phụ thuộc vào app đang đúng hay sai (nó bắt nguồn từ README, không phải từ
code). Chỉ cần chạy lại **Prompt 2**:

```
Dùng skill autotest-run-test để chạy lại toàn bộ bộ test dat-hang, seed lại
dữ liệu test, và xuất báo cáo đầy đủ.
```

**Nhắc lại 2 điều bắt buộc** (đã nói ở Prompt 1a, nhấn mạnh lại vì đây là chỗ
dễ làm hỏng bài tập nếu bỏ qua):
- Nguồn spec là `README.md`, không phải code app.
- Oracle tự viết lại công thức từ dữ liệu thô, không `import` module tính
  toán của app.

### Bước 3 — Đọc kết quả

Kỳ vọng: **có FAIL**. Nếu 6 lỗi đều bật mà toàn bộ test PASS, đó tự nó là
một phát hiện quan trọng — nghĩa là bộ test vừa sinh không đủ "răng" (thường
do oracle lấy kỳ vọng từ chính app, hoặc thiếu case biên/tổ hợp đúng chỗ);
xem lại Prompt 1a trước khi kết luận "app không có bug".

```bash
cat reports/test_summary.md     # bảng ID case | scenario | PASS/FAIL | lỗi
open reports/report.html        # chi tiết từng case, lọc theo Failed
```

### Bước 4 — Prompt yêu cầu báo cáo bug

```
Đọc reports/test_summary.md và reports/report.html của lần chạy vừa rồi.
Với mỗi testcase FAIL, viết 1 mục báo cáo bug gồm: ID case, tên scenario,
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
