---
name: autotest-run-test
description: Chạy bộ test đã sinh (pytest-bdd + Playwright), tự phân loại và sửa lỗi kịch bản (không tự sửa bug thật của app), tách riêng known-bug đã đánh dấu `xfail` khỏi Fail mới (regression), chọn môi trường UAT/PROD qua `--test-env` (mặc định uat, chạy PROD phải được người dùng xác nhận rõ), hỏi người dùng khi thiếu tham số môi trường, rồi sinh báo cáo — **Allure là định dạng mặc định** (kèm test_summary.md, pytest-html), tự đính kèm bằng chứng + lịch sử truy vết vào Allure: ảnh chụp màn hình PASS/FAIL cho scenario UI, lịch sử mọi lời gọi HTTP (URL + mã response) trong scenario, curl + response thật cho scenario API — luôn CHE thông tin nhạy cảm (x-api-key, password, secret, token, cookie...) trước khi ghi. Hỗ trợ chế độ trình diễn cho tester: chạy có màn hình, chậm từng bước, in chi tiết từng testcase ra console và dừng chờ bấm tiếp sau mỗi testcase. Dùng khi người dùng nói "chạy test", "chạy lại bộ test và cho báo cáo", hoặc sau khi đã có code test từ skill autotest-gen-test.
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

   **Chọn môi trường UAT/PROD** qua cờ `--test-env` (do plugin `autotest_env`
   cung cấp — xem bước 2), mặc định `uat` nếu người dùng không nói gì. **PROD
   là môi trường THẬT** — chỉ chạy `--test-env=prod` khi người dùng nói rõ
   ràng ý định đó (vd "chạy trên PROD", "kiểm thử trên môi trường thật"); nếu
   yêu cầu chỉ mơ hồ "chạy test" mà project có cả UAT và PROD, **mặc định
   dùng UAT và nói rõ đang dùng UAT** — không tự suy đoán ý định chạy PROD.
   Scenario có side-effect thật trên PROD (đặt hàng thật, gửi SMS/email thật
   tới số/địa chỉ thật...) phải được xác nhận riêng trước khi chạy, dù đã
   đồng ý chạy PROD nói chung.

2. **Cài `allure-pytest-bdd` + `pyyaml` (bắt buộc)**: `pip install
   allure-pytest-bdd pyyaml`. Thiếu `allure-pytest-bdd` thì `--alluredir`
   không sinh ra gì và mọi bằng chứng (ảnh chụp, curl/response) ở bước 5 bị
   bỏ qua lặng lẽ — không lỗi, nhưng mất bằng chứng. Thiếu `pyyaml` thì plugin
   `autotest_env` (biến môi trường UAT/PROD, xem dưới) báo lỗi ngay lúc nạp
   conftest — không chạy được test nào cho tới khi cài.

   **Cài 3 plugin dùng chung** (nếu project chưa có): copy
   `assets/autotest_reporting.py`, `assets/autotest_demo.py` và
   `assets/autotest_env.py` (cùng thư mục với SKILL.md này) vào thư mục chứa
   `conftest.py` của project, rồi khai báo trong `conftest.py`:
   ```python
   pytest_plugins = ["autotest_reporting", "autotest_demo", "autotest_env"]

   import autotest_env
   import autotest_reporting

   BASE_URL = autotest_env.global_vars()["base_url"]  # theo đúng --test-env đang chạy
   autotest_reporting.ENVIRONMENT.update({
       "App.URL": BASE_URL,
       "Environment": autotest_env.current_env().upper(),  # để tab Environment của
       "Browser": "Chromium (Playwright)",                 # Allure hiện rõ UAT/PROD
   })

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
   `autotest_env` quản lý biến/tham số môi trường (UAT/PROD): nếu project
   chưa có `testing/env/global.yaml`, copy từ `assets/env.global.example.yaml`
   và điền giá trị thật (không tự bịa URL PROD nếu chưa biết — hỏi người
   dùng). Chi tiết đầy đủ về biến global/local nằm ở SKILL.md của
   `autotest-gen-test` (nơi step definitions được viết ra dùng chúng) — bước
   này chỉ cần đảm bảo file đã có và `--test-env` chọn đúng môi trường.

   `autotest_reporting` sinh `reports/test_summary.md` (truy vết theo MatrixID,
   có cột số lần rerun, và tự tách riêng case đã đánh dấu `pytest.mark.xfail`
   thành "Known bug (xfail)" — không cộng vào Fail, xem bảng phân loại ở bước
   7), `environment.properties` cho Allure, và **tự đính bằng chứng + lịch sử
   truy vết vào Allure**:
   - **Scenario UI**: nếu step definitions dùng 1 fixture đặt tên đúng là
     `page` (function-scope, Playwright `Page`) — đây là convention
     `autotest-gen-test` phải tuân theo khi viết step — plugin tự:
     - chụp và đính ảnh màn hình lúc scenario kết thúc, **cả khi PASS và
       FAIL**, không cần step nào tự gọi thêm gì;
     - **ghi lại LỊCH SỬ mọi request `document`/`xhr`/`fetch`** trang gọi
       trong lúc chạy (thứ tự gọi, method, URL, mã response HTTP) thành 1
       attachment `HTTP calls (network log)` — để trace lại đúng những gì đã
       xảy ra khi xem báo cáo, không phụ thuộc step có tự log hay không.
   - **Scenario API** (gọi trực tiếp bằng `requests`... không qua `page`):
     step phải tự gọi `autotest_reporting.attach_api_call(method, url,
     request_headers=..., request_body=..., status=..., response_headers=...,
     response_body=...)` ngay sau khi thực hiện request thật, để đính kèm
     curl tái hiện request + response thật vào Allure. Nếu bộ test đang chạy
     thiếu bằng chứng này ở scenario API, đó là lỗi kịch bản cần bổ sung,
     không phải điều bình thường bỏ qua.
   - **Che thông tin nhạy cảm tự động, không cần step làm gì**: mọi
     header/field/query-param có tên chứa (không phân biệt hoa/thường)
     `key`, `password`, `secret`, `token`, `authorization`, `cookie` —
     bao gồm `x-api-key` — bị thay bằng `***` trước khi ghi vào network log
     lẫn `attach_api_call`, ở cả URL, header và body (JSON lồng nhau). Nếu
     project có tên field nhạy cảm khác không khớp các từ khoá này, phải sửa
     `_SENSITIVE_KEY_RE` trong bản copy `autotest_reporting.py` của project
     đó trước khi chạy, không đợi lộ dữ liệu rồi mới sửa.

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

5. **Chạy toàn bộ bộ test**, ví dụ (mặc định `--test-env=uat` nếu không
   truyền — xem quy tắc chọn môi trường ở bước 1):
   ```bash
   pytest <thư mục test> --test-env=uat \
     --html=reports/report.html --self-contained-html \
     --alluredir=reports/allure-results --clean-alluredir \
     --reruns 1 --reruns-delay 1
   allure generate reports/allure-results --output reports/allure-report --clean
   ```
   Nếu project đã có script gói sẵn các tham số này (vd `scripts/run_tests.sh`
   **của project đang test**, không phải của thư mục skill), ưu tiên dùng nó.

   `--alluredir` **luôn chạy** (không phải tuỳ chọn) — `reports/allure-results/`
   là nơi chứa bằng chứng thật (ảnh chụp màn hình, curl+response) do
   `autotest_reporting` đính vào, đủ để mở bằng `allure serve reports/allure-results`
   dù máy này chưa có Allure Commandline. `allure generate` (build ra HTML tĩnh
   ở `reports/allure-report/`) là bước RIÊNG, chỉ cần Allure Commandline — nếu
   máy không có CLI, bỏ qua đúng lệnh này và nêu rõ với người dùng, KHÔNG bỏ
   qua cả `--alluredir`.

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
   | Bug thật của app | Request/response hợp lý theo kịch bản nhưng kết quả nghiệp vụ sai (vd tổng tiền tính sai) | **KHÔNG tự sửa code app.** Báo cáo là bug kèm bằng chứng — lấy từ attachment Allure đã có sẵn (ảnh chụp màn hình PASS/FAIL, `HTTP calls (network log)` để trỏ đúng request nào gây ra kết quả sai, hoặc curl+response thật do `attach_api_call` đính vào) — + MatrixID để tái hiện; nếu scenario liên quan thiếu attachment này, đó là lỗi kịch bản cần bổ sung trước, không phải chỉ nêu miệng |
   | Lỗi kịch bản/selector | `TimeoutError` do selector không khớp, step thiếu, sai thứ tự thao tác | Tự sửa test code, chạy lại (tối đa 3 lần) |
   | Nghi flaky | Fail không nhất quán, pass sau rerun, lỗi timing/network | Xem cột "Lần chạy lại" trong `test_summary.md`; báo rõ là flaky và đề xuất nguyên nhân — KHÔNG im lặng cho qua vì "chạy lại thì pass" |
   | Known bug đã xác nhận, đang chờ fix | Scenario được đánh dấu `@pytest.mark.xfail(reason=...)` ngay trên hàm test do `@scenario(...)` sinh ra — **chỉ đánh dấu khi người dùng/PO đã xác nhận rõ đây là bug đã biết**, không tự ý gắn để che 1 fail mới | Không phải hành động sửa — `test_summary.md` tự tách case này vào cột "Known bug (xfail)", không tính vào Fail. Nếu case xfail này **bất ngờ PASS** (bug đã được fix nhưng quên gỡ tag) → báo cho người dùng để gỡ `xfail`, không âm thầm để vậy |

8. **Tổng kết cho người dùng**: số scenario pass/fail/flaky, việc gì đã tự
   sửa (kèm diff ngắn), việc gì là bug thật cần người review (kèm MatrixID),
   và đường dẫn report để mở.

## Definition of done
- Có kết quả chạy thật cuối cùng, mọi fail đã được phân loại rõ (không kết
  luận "chắc là do X" mà chưa xác minh bằng bằng chứng).
- `reports/test_summary.md` + `reports/report.html` + `reports/allure-results/`
  luôn được sinh ra (Allure là mặc định, không tuỳ chọn); thêm
  `reports/allure-report/` (HTML build) nếu máy có Allure Commandline — không
  có thì nêu rõ, KHÔNG coi là thiếu `allure-results`.
- Bằng chứng có thật trong Allure: scenario UI có ảnh chụp màn hình
  PASS/FAIL + attachment `HTTP calls (network log)` (lịch sử URL + mã
  response, trace được đúng thứ tự đã gọi), scenario API có curl+response —
  nếu thiếu (vd step chưa dùng fixture `page`/chưa gọi `attach_api_call`),
  phải nêu rõ và bổ sung, không báo xong với báo cáo thiếu bằng chứng.
- Đã kiểm tra (mở thử vài attachment trong `reports/allure-results/` hoặc
  `allure serve`) rằng KHÔNG có `x-api-key`/`password`/`secret`/`token`/giá
  trị header, body, hay query-param nhạy cảm nào lộ ra dạng plaintext — phải
  hiện `***`. Nếu project dùng tên field nhạy cảm khác không khớp
  `_SENSITIVE_KEY_RE`, phải bổ sung trước khi báo xong, không đợi phát hiện
  rồi mới sửa.
- Không có sửa đổi nào vào code ứng dụng (app) trong bước này.
- Nếu có case đánh dấu `xfail` (known bug), `test_summary.md` đã hiện đúng ở
  cột "Known bug (xfail)" tách khỏi Fail; case xfail nào bất ngờ PASS đã được
  báo cho người dùng để xem xét gỡ tag.
- `conftest.py` của project đã khai báo `autotest_demo` và fixture `browser`
  đọc `demo_mode` → `pytest --demo` chạy được thật (có cửa sổ trình duyệt,
  chậm, dừng từng case). Nếu người dùng yêu cầu chạy trình diễn mà thiếu phần
  này, phải bổ sung rồi mới báo xong.
- Đã chạy đúng môi trường người dùng muốn (`--test-env=uat` mặc định, hoặc
  `prod` nếu đã xác nhận rõ) — tab Environment của Allure hiện đúng tên môi
  trường (`Environment: UAT`/`PROD`) để tester mở report không nhầm lẫn.

## Khi nào KHÔNG tự quyết
- Thiếu tham số môi trường bắt buộc (URL, tài khoản test, secret) → hỏi.
- Chạy test trên PROD (`--test-env=prod`) mà người dùng chỉ yêu cầu mơ hồ
  "chạy test" → **KHÔNG tự chạy PROD**, mặc định UAT và nói rõ đang dùng UAT;
  chỉ chạy PROD khi người dùng nói rõ ràng. Scenario PROD có side-effect thật
  (đặt hàng, gửi SMS/email thật...) → xác nhận riêng trước khi chạy dù đã
  đồng ý chạy PROD nói chung.
- Không chắc 1 fail là bug thật hay lỗi kịch bản sau khi đã xem
  request/response → nêu rõ nghi vấn kèm bằng chứng, để người dùng quyết định.
- Muốn "sửa" 1 fail bằng cách nới lỏng assertion, bỏ bớt điều kiện check,
  hoặc tăng `--reruns` cho tới khi pass → **KHÔNG được làm**: đó là che giấu
  lỗi, không phải sửa lỗi.
