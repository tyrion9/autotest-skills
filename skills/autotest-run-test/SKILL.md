---
name: autotest-run-test
description: Chạy bộ test đã sinh (pytest-bdd + Playwright), tự phân loại và sửa lỗi kịch bản (không tự sửa bug thật của app), hỏi người dùng khi thiếu tham số môi trường, rồi sinh báo cáo (test_summary.md, pytest-html, Allure). Hỗ trợ chế độ trình diễn cho tester: chạy có màn hình, chậm từng bước, in chi tiết từng testcase ra console và dừng chờ bấm tiếp sau mỗi testcase. Dùng khi người dùng nói "chạy test", "chạy lại bộ test và cho báo cáo", hoặc sau khi đã có code test từ skill autotest-gen-test.
---

# Autotest: Run Test (chạy, tự sửa/hỏi tham số, gen báo cáo)

## Mục tiêu
Chạy bộ test tới cùng, phân biệt rõ 3 loại lỗi (bug thật / lỗi kịch bản /
flaky), chỉ tự sửa loại mình được phép sửa, và luôn kết thúc bằng báo cáo có
thể đọc lại được, truy vết được về MatrixID.

## Các bước

1. **Xác định tham số chạy**: base URL của app, cách seed dữ liệu test, biến
   môi trường cần thiết, headless/headed, có chạy song song không. Nếu **suy
   luận được từ code có sẵn** (project đã có script chạy test, `conftest.py`
   định nghĩa base URL...) thì dùng thẳng, không hỏi lại. Nếu **thiếu** →
   hỏi người dùng, không tự bịa URL/credentials/cổng.

2. **Cài 2 plugin dùng chung** (nếu project chưa có): copy
   `assets/autotest_reporting.py` và `assets/autotest_demo.py` (cùng thư mục
   với SKILL.md này) vào thư mục chứa `conftest.py` của project, rồi khai báo
   trong `conftest.py`:
   ```python
   pytest_plugins = ["autotest_reporting", "autotest_demo"]

   import autotest_reporting
   autotest_reporting.ENVIRONMENT.update({"App.URL": BASE_URL, "Browser": "Chromium (Playwright)"})

   # Fixture browser PHẢI đọc demo_mode, nếu không cờ --demo sẽ không có tác dụng
   # (vẫn chạy ẩn, vẫn nhanh) — tester không kiểm chứng bằng mắt được.
   @pytest.fixture(scope="session")
   def browser(demo_mode):
       with sync_playwright() as p:
           browser = p.chromium.launch(
               headless=not demo_mode.headed,   # --demo -> hiện cửa sổ trình duyệt
               slow_mo=demo_mode.slow_mo,       # --demo -> chậm lại từng thao tác (ms)
           )
           yield browser
           browser.close()
   ```
   `autotest_reporting` sinh `reports/test_summary.md` (truy vết theo MatrixID,
   có cột số lần rerun) và `environment.properties` cho Allure.
   `autotest_demo` là chế độ trình diễn ở bước 6. **Không tự viết lại hook báo
   cáo hay hook trình diễn cho từng project** — dùng plugin dùng chung để mọi
   project ra cùng 1 định dạng.

3. **Bật cơ chế rerun ở tầng pytest** (khuyến nghị cho CI):
   `pip install pytest-rerunfailures` rồi chạy với `--reruns 1 --reruns-delay 1`.
   Mục đích: flaky được xử lý bằng CƠ CHẾ chạy được trong CI, không phụ thuộc
   việc người/AI nhớ chạy lại tay. Case pass sau rerun sẽ bị đánh dấu "nghi
   flaky" trong `test_summary.md` — KHÔNG coi là pass sạch.

4. **Seed dữ liệu test** bằng script seed sẵn có của project (không tự viết
   script seed mới nếu đã có).

5. **Chạy toàn bộ bộ test**, ví dụ:
   ```bash
   pytest <thư mục test> \
     --html=reports/report.html --self-contained-html \
     --alluredir=reports/allure-results --clean-alluredir \
     --reruns 1 --reruns-delay 1
   allure generate reports/allure-results --output reports/allure-report --clean
   ```
   Nếu project đã có script gói sẵn các tham số này (vd `scripts/run_tests.sh`
   **của project đang test**, không phải của thư mục skill), ưu tiên dùng nó.

6. **Chế độ trình diễn — chạy có màn hình, chậm, dừng từng testcase**
   (dùng khi tester muốn tự kiểm chứng bằng mắt, hoặc khi người dùng yêu cầu
   "chạy cho tôi xem", "demo test", "chạy chậm lại"):
   ```bash
   pytest <thư mục test> --demo                    # dừng chờ Enter sau mỗi testcase
   pytest <thư mục test> --demo --demo-pause=3     # tự chạy tiếp sau 3 giây
   pytest <thư mục test> --demo --demo-pause=none  # không dừng, chỉ chậm + in chi tiết
   pytest <thư mục test> --demo --demo-slowmo=800 --demo-step-delay=1
   pytest <thư mục test> --demo -k "TC-4F2A91"     # trình diễn đúng 1 testcase
   ```
   Chế độ này (do `autotest_demo.py` cung cấp):
   - **Trình duyệt hiện hình** (`headless=False`) và **chậm lại** từng thao tác
     (`slow_mo`, mặc định 500ms) — cần fixture `browser` ở bước 2 đọc `demo_mode`.
   - **In từng testcase ra console trước khi chạy**: số thứ tự/tổng số,
     **MatrixID**, tên scenario, mô tả, feature + đường dẫn file, **toàn bộ dữ
     liệu của dòng Examples** (mỗi factor 1 dòng) và **các bước Gherkin đã thay
     giá trị thật**. Mỗi step được in lại ngay lúc nó chạy (`→ When ...`), step
     lỗi in kèm exception.
   - **Chạy tuần tự từng testcase, dừng chờ tester bấm tiếp**: `Enter` = case
     tiếp theo · `s` = thôi dừng, chạy hết · `q` = dừng phiên. Tự ép tắt
     `pytest-xdist` (không chạy song song) vì song song thì không xem được.
   - Cuối mỗi case in `Kết quả: PASS/FAIL/SKIP`.

   Quy tắc khi dùng:
   - **Không lấy kết quả lần chạy demo làm kết quả chính thức** — vẫn phải có
     1 lần chạy headless ở bước 5 để sinh báo cáo; demo chỉ để kiểm chứng mắt
     thường. Nếu demo và headless cho kết quả khác nhau, đó là dấu hiệu test
     phụ thuộc timing → điều tra, không bỏ qua.
   - **Không bật `--demo` trong CI**: cần trình duyệt có màn hình và stdin là
     terminal. Plugin tự bỏ qua bước dừng khi stdin không phải terminal, nhưng
     phần headed/slow_mo vẫn làm CI chậm và dễ treo.
   - Bộ test quá lớn thì đề xuất tester dùng `-k` để chọn nhóm testcase muốn
     xem, thay vì ngồi bấm Enter vài chục lần.

7. **Có fail → phân loại TRƯỚC khi hành động**:
   | Loại | Dấu hiệu | Hành động |
   |---|---|---|
   | Bug thật của app | Request/response hợp lý theo kịch bản nhưng kết quả nghiệp vụ sai (vd tổng tiền tính sai) | **KHÔNG tự sửa code app.** Báo cáo là bug kèm bằng chứng (request/response JSON, ảnh chụp màn hình từ attachment Allure) + MatrixID để tái hiện |
   | Lỗi kịch bản/selector | `TimeoutError` do selector không khớp, step thiếu, sai thứ tự thao tác | Tự sửa test code, chạy lại (tối đa 3 lần) |
   | Nghi flaky | Fail không nhất quán, pass sau rerun, lỗi timing/network | Xem cột "Lần chạy lại" trong `test_summary.md`; báo rõ là flaky và đề xuất nguyên nhân — KHÔNG im lặng cho qua vì "chạy lại thì pass" |

8. **Tổng kết cho người dùng**: số scenario pass/fail/flaky, việc gì đã tự
   sửa (kèm diff ngắn), việc gì là bug thật cần người review (kèm MatrixID),
   và đường dẫn report để mở.

## Definition of done
- Có kết quả chạy thật cuối cùng, mọi fail đã được phân loại rõ (không kết
  luận "chắc là do X" mà chưa xác minh bằng bằng chứng).
- `reports/test_summary.md` + `reports/report.html` được sinh ra; thêm
  `reports/allure-report/` nếu máy có Allure CLI (không có thì nêu rõ).
- Không có sửa đổi nào vào code ứng dụng (app) trong bước này.
- `conftest.py` của project đã khai báo `autotest_demo` và fixture `browser`
  đọc `demo_mode` → `pytest --demo` chạy được thật (có cửa sổ trình duyệt,
  chậm, dừng từng case). Nếu người dùng yêu cầu chạy trình diễn mà thiếu phần
  này, phải bổ sung rồi mới báo xong.

## Khi nào KHÔNG tự quyết
- Thiếu tham số môi trường bắt buộc (URL, tài khoản test, secret) → hỏi.
- Không chắc 1 fail là bug thật hay lỗi kịch bản sau khi đã xem
  request/response → nêu rõ nghi vấn kèm bằng chứng, để người dùng quyết định.
- Muốn "sửa" 1 fail bằng cách nới lỏng assertion, bỏ bớt điều kiện check,
  hoặc tăng `--reruns` cho tới khi pass → **KHÔNG được làm**: đó là che giấu
  lỗi, không phải sửa lỗi.
