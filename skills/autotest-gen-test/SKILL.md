---
name: autotest-gen-test
description: Sinh code test Python (Gherkin .feature + pytest-bdd step definitions dùng Playwright) từ 1 trong 3 nguồn — prompt mô tả nghiệp vụ của người dùng, 1 file testcase có sẵn (xlsx/csv/markdown/text), hoặc 1 file .feature đã viết sẵn. Nếu app đích chạy được, ưu tiên rà soát trang thật bằng skill/extension `claude-in-chrome` (đi qua luồng, kiểm tra data-testid, xem network/console thật) TRƯỚC KHI viết code, rồi TỰ VERIFY (collect + chạy thử + mutation check) trước khi báo hoàn thành. Biến/tham số phụ thuộc môi trường (URL, path, số điện thoại, data test) đọc qua plugin `autotest_env` — tách biến global (dùng chung mọi feature) và biến local (riêng 1 feature), theo môi trường UAT/PROD, ghi trong file YAML tester sửa tay được — không hard-code trong step. Dùng khi người dùng nói "viết test cho tính năng...", "sinh test từ file testcase này", "viết step definitions cho file .feature này", hoặc bất cứ khi nào cần code test E2E chạy được ngay từ 1 trong 3 nguồn trên.
---

# Autotest: Gen Test (prompt / file testcase / .feature có sẵn → code test, tự verify)

## Mục tiêu
Từ 1 trong 3 nguồn đầu vào bên dưới, tạo ra `.feature` + step definitions
Python (pytest-bdd + Playwright) **chạy thử thành công** trước khi báo cáo
hoàn thành — không giao code chưa kiểm chứng.

## Xác định nguồn đầu vào

Hỏi lại người dùng nếu không rõ đang ở nguồn nào (chỉ 1 câu, không suy đoán
khi ảnh hưởng tới toàn bộ cách làm việc bên dưới):

1. **Prompt mô tả nghiệp vụ** (chưa có file testcase/.feature nào) — người
   dùng mô tả bằng lời 1 tính năng/luồng cần test (vd "viết test cho luồng
   đặt hàng: chọn hàng, thêm giỏ, checkout, xem lại đơn").
2. **File testcase có sẵn** (xlsx/csv/markdown table/text — bất kỳ định dạng
   nào người dùng đang có sẵn, không bắt buộc theo 1 schema cột cố định).
3. **File `.feature` có sẵn** (Gherkin đã viết, có thể chưa có step definitions
   hoặc đã có 1 phần).

Cả 3 nguồn đều dẫn tới cùng 1 bộ bước 2-5 bên dưới; khác nhau ở bước 1.

## Các bước

### 0. Rà soát trang web thật bằng Claude in Chrome (ưu tiên, làm trước bước 1)

Nếu app đích đang chạy được (có URL truy cập được, kể cả localhost) thì **ưu
tiên dùng skill `claude-in-chrome` mở trình duyệt thật và tự tay đi qua luồng
liên quan** trước khi đọc mã nguồn hoặc viết bất kỳ dòng Gherkin/step nào:
- Điều hướng qua đúng luồng được mô tả (từ prompt/file testcase/`.feature`)
  trên UI thật: bấm, điền form, submit, xem kết quả — không chỉ đọc code rồi
  suy diễn hành vi.
- Dùng `read_page`/`get_page_text`/`find` để xác nhận `data-testid` thật có
  tồn tại trên đúng phần tử cần thao tác (dùng lại ở bước 3) — không đoán
  selector từ tên biến trong code khi chưa thấy DOM thật.
- Dùng `read_network_requests`/`read_console_messages` khi cần thấy
  request/response thật (field trả về, mã lỗi validate thật) — đỡ phải đoán
  từ đọc handler.
- Việc rà soát này giúp thiết kế case biên/negative đúng với hành vi UI thật
  (thông báo lỗi hiển thị thế nào, field nào bị disable khi nào...) thay vì
  chỉ suy từ đọc mã nguồn.

Nếu app **không chạy được / không có URL truy cập được** (chỉ có mã nguồn
tĩnh), nêu rõ điều này với người dùng rồi làm theo cách cũ ở bước 1: đọc mã
nguồn thật — không tự bịa hành vi UI khi chưa xác nhận được bằng trình duyệt
thật lẫn source.

Rà soát ở bước này **không thay thế** verify bắt buộc ở bước 4 (chạy test
thật bằng Playwright) — bước 0 là để hiểu đúng UI/luồng trước khi viết code,
bước 4 là verify chính code test đã viết ra chạy đúng.

### 1. Dựng/đọc nội dung Gherkin theo đúng nguồn

- **Nguồn = Prompt**: đọc requirement + mã nguồn thật liên quan (form UI,
  route/handler, model/DB, config) — không suy diễn business rule nếu thiếu
  thông tin, **hỏi người dùng** trước khi tự chọn dữ liệu test. Tự thiết kế
  Scenario/Scenario Outline đủ để phủ luồng chính + case biên hợp lý (giá trị
  min/max/rỗng, ràng buộc giữa các input nếu có) — không cần máy móc theo
  pairwise, nhưng nếu tổ hợp input đủ lớn để đáng làm ma trận, có thể tự viết
  1 bảng `Examples` thủ công (dữ liệu do AI chọn, ghi rõ vì sao chọn mỗi dòng
  trong docstring/comment, không cần công cụ sinh tổ hợp riêng). Viết ra
  `.feature` mới tại `testing/features/<feature>.feature`.
- **Nguồn = File testcase có sẵn**: đọc TOÀN BỘ file (mọi dòng/mọi sheet liên
  quan) trước khi viết bất kỳ dòng Gherkin nào. File này là **nguồn chân lý
  cho danh sách case** — không tự thêm case người dùng không liệt kê, không
  tự bỏ bớt case đã liệt kê, không tự đổi dữ liệu input/kỳ vọng đã ghi trong
  file. Nếu file thiếu cột/mục quan trọng (vd không có cột kỳ vọng, mô tả case
  không rõ input nào) → hỏi người dùng, không tự đoán. Mỗi dòng/case trong
  file → 1 hàng `Examples` (nếu các case cùng luồng, dùng chung 1 `Scenario
  Outline`) hoặc 1 `Scenario` riêng (nếu case đó có luồng thao tác khác hẳn,
  không gộp được vào cùng 1 outline). Ghi ra `testing/features/<feature>.feature`.
- **Nguồn = File `.feature` có sẵn**: **không viết lại/không sửa nội dung
  Gherkin đã có** (trừ khi người dùng yêu cầu sửa case cụ thể) — chỉ dùng nó
  để xác định các step definitions còn thiếu ở bước 3-4.

- **Mỗi Scenario/mỗi hàng Examples mang 1 ID ổn định** dạng `[TC-xxx]`
  (case thường) hoặc `[BC-xxx]` (case biên/negative), đặt ngay đầu tên
  Scenario — dùng để truy vết report/bug ngược lại case cụ thể (xem
  `autotest-run-test`). Khi **thêm case mới vào 1 `.feature` đã có ID**, giữ
  nguyên ID cũ của các case cũ, chỉ cấp ID mới cho case mới thêm — không đánh
  số lại toàn bộ (báo cáo bug cũ trỏ theo ID sẽ sai nếu ID bị xáo trộn).

### 2. Rà soát step definitions hiện có trước khi viết mới
`grep` các hàm `@given/@when/@then` trong `testing/steps/*.py`, tái dùng step
đã có (khớp đúng text) — chỉ viết step mới cho phần thật sự chưa có.

### 3. Viết step mới (nếu cần) theo convention đã dùng trong project
- Dùng `data-testid` ổn định trên UI (không dùng text hiển thị làm selector
  nếu UI đã có `data-testid`; nếu UI CHƯA có `data-testid` cho phần tử cần
  thao tác — đã xác nhận qua rà soát thật ở bước 0, không chỉ đọc code — báo
  cho người dùng, không tự đoán selector CSS mong manh).
- **Fixture `browser` phải nhận tham số chế độ trình diễn ngay từ đầu**, để
  bước `autotest-run-test` chạy được `pytest --demo` (có màn hình, chậm, dừng
  từng testcase) mà không phải sửa lại conftest:
  ```python
  @pytest.fixture(scope="session")
  def browser(demo_mode):          # demo_mode do plugin autotest_demo cung cấp
      with sync_playwright() as p:
          browser = p.chromium.launch(
              headless=not demo_mode.headed,
              slow_mo=demo_mode.slow_mo,
          )
          yield browser
          browser.close()
  ```
  Mặc định (không có cờ `--demo`) `demo_mode.headed=False`, `slow_mo=0` → vẫn
  chạy headless, nhanh, hợp CI.
- **Biến & tham số môi trường (UAT/PROD) — không hard-code URL/path/số điện
  thoại/data test thẳng trong step.** Plugin dùng chung `autotest_env.py`
  (asset của `autotest-run-test`, copy như `autotest_reporting`/`autotest_demo`)
  tách 2 loại biến, cả 2 đều có sẵn cho môi trường `uat` và `prod`:
  - **Biến global** (`testing/env/global.yaml`) — dùng chung mọi feature, vd
    `base_url`, `api_url`. Đọc bằng `autotest_env.global_vars()["base_url"]`.
  - **Biến local** (`testing/env/local/<feature>.yaml`, tên file khớp tên
    feature) — riêng cho feature đang viết: path, số điện thoại/tài khoản
    cần tra cứu, data test cụ thể... Đọc bằng
    `autotest_env.local_vars("<feature>")["phone_number"]`.
  ```python
  from autotest_env import global_vars, local_vars
  base_url = global_vars()["base_url"]
  phone = local_vars("tra_cuu_don_hang")["phone_number"]
  ```
  **Lần đầu viết 1 feature còn thiếu file biến** → tạo file theo mẫu
  `env.global.example.yaml`/`env.local.example.yaml` (asset của
  `autotest-run-test`), rồi **hỏi người dùng giá trị THẬT cho cả UAT và
  PROD** (URL, số điện thoại, path...) — không tự bịa, vì 2 môi trường
  thường có data khác nhau và bịa sai sẽ khiến test PROD vô tình chạy nhầm
  data UAT hoặc ngược lại.
- **Bằng chứng + lịch sử truy vết cho Allure (bắt buộc, `autotest-run-test`
  chạy xong sẽ kiểm lại phần này)**:
  - Scenario UI: mọi step dùng chung 1 fixture **đặt tên đúng là `page`**
    (function-scope, `browser.new_page()`) — plugin `autotest_reporting` tự
    nhận diện đúng tên này để: (a) tự chụp và đính ảnh màn hình PASS/FAIL vào
    Allure, (b) tự ghi lại **lịch sử mọi lời gọi HTTP** (`document`/`xhr`/
    `fetch`: method, URL, mã response) phát sinh trong lúc chạy thành 1
    attachment `HTTP calls (network log)` — không cần step tự gọi gì thêm.
    Đặt tên fixture khác `page` thì mất cả 2 phần tự động này.
  - Scenario API: step thực hiện request thật (`requests`/Playwright
    `APIRequestContext`...) phải gọi ngay
    `autotest_reporting.attach_api_call(method, url, request_headers=...,
    request_body=..., status=..., response_headers=..., response_body=...)`
    ngay sau khi có response, để đính kèm curl tái hiện request + response
    thật vào Allure — không tự bịa lại request/response từ code app.
  - **Không tự che/lọc thông tin nhạy cảm trong step** — plugin
    `autotest_reporting` đã tự che `x-api-key`/`password`/`secret`/`token`/
    `authorization`/`cookie` (không phân biệt hoa/thường, cả trong URL,
    header, body lồng nhau) trước khi ghi vào Allure. Nếu project có field
    nhạy cảm với tên khác không khớp danh sách trên, phải báo cho người dùng
    để cập nhật `_SENSITIVE_KEY_RE` trong bản copy `autotest_reporting.py`
    của project đó — không tự ý truyền dữ liệu nhạy cảm ra ngoài phạm vi che
    này (vd không tự in ra console/log riêng để "debug").
- **Viết docstring 1 dòng cho step/scenario khi có thể** — chế độ trình diễn
  in docstring này ra console làm phần "Mô tả" của testcase.
- **Oracle (giá trị kỳ vọng) PHẢI ĐỘC LẬP với code của app.** Đây là quy tắc
  quan trọng nhất của bước này:
  - ✅ ĐÚNG: đọc **dữ liệu thô** từ DB/API/config (giá gốc, phụ phí, thuế
    suất...) rồi **tự viết lại công thức** trong code test.
  - ❌ SAI: `from app.pricing import calc_total` rồi dùng chính hàm đó làm kỳ
    vọng. App tính sai kiểu gì test cũng pass (oracle tự khớp chính nó).
  - ❌ SAI: hard-code số liệu kỳ vọng khi lẽ ra tính được từ dữ liệu thô (vỡ
    ngay khi đổi dữ liệu seed). Nếu nguồn là file testcase/`.feature` đã ghi
    sẵn số kỳ vọng cụ thể, dùng đúng số đó làm assertion, nhưng ưu tiên viết
    step Then dưới dạng công thức khi có thể thay vì chỉ so khớp số cố định.
  Việc trùng lặp công thức giữa app và test ở đây là **cố ý** — đó chính là
  cái giúp test phát hiện khi công thức app bị sửa sai.
- Case biên/negative: viết cụ thể Given/When/Then theo mô tả + kỳ vọng đã có
  (từ prompt, file testcase, hoặc `.feature`) — không để lại `# TODO` chưa
  viết xong mà không báo cho người dùng.

### 4. Tự verify (bắt buộc, không bỏ qua)
a. **Collect**: `pytest <thư mục test> --collect-only -q` — phải sạch, không
   lỗi "step chưa định nghĩa"/lỗi import. Số test collect được phải khớp số
   Scenario/Example đã viết (đếm lại bằng tay để đối chiếu, vì không còn
   script tự động so khớp).
b. **Chạy thật (headless)**: toàn bộ nếu ít scenario, hoặc tối thiểu 1
   scenario đại diện cho mỗi luồng/step mới nếu bộ test đã lớn (`-k`).
c. **Mutation check — test có "răng" không**: tiêm 1 lỗi nhỏ vào logic nghiệp
   vụ của app (vd cộng thêm 1000 vào đơn giá, đảo 1 điều kiện), chạy lại vài
   scenario, xác nhận chúng **FAIL**, rồi **gỡ lỗi đã tiêm ngay** và chạy lại
   cho pass. Test xanh mà không fail khi app sai là test vô dụng. Bước này
   bắt buộc khi vừa viết step `Then` kiểm tra giá trị tính toán.
d. Có lỗi → phân loại: lỗi code test tự sửa (selector sai, thiếu import, sai
   kiểu dữ liệu, timing) → sửa → lặp lại (a)-(b), tối đa 3 lần. Lỗi do thiếu
   thông tin nghiệp vụ (không biết kỳ vọng đúng là gì) → DỪNG, hỏi người
   dùng, không đoán đại một giá trị kỳ vọng.

**Không được báo "đã xong" khi chưa chạy đủ (a)+(b)+(c).** Nếu vì lý do môi
trường không chạy được (chưa cài browser, app không khởi động được), phải nói
rõ bước nào chưa verify được và vì sao, thay vì im lặng bỏ qua. Nếu có tiêm
lỗi để mutation check thì **phải xác nhận đã gỡ sạch** (diff sạch) trước khi
báo xong.

Lỗi hay gặp khi viết step Playwright: `wait_for_selector` mặc định chờ
`state="visible"` — muốn chờ phần tử BỊ ẨN phải truyền `state="hidden"`, nếu
không sẽ treo tới hết timeout (30s) rồi báo lỗi khó hiểu.

## Definition of done
- Nếu app đích chạy được: đã rà soát trang thật bằng `claude-in-chrome` (bước
  0) trước khi thiết kế case/viết step — nếu bỏ qua vì app không chạy được,
  đã nói rõ lý do với người dùng thay vì im lặng bỏ qua.
- `pytest --collect-only` sạch, số test khớp số case đã thiết kế/đã có trong
  nguồn đầu vào (không thiếu, không tự bịa thêm case ngoài nguồn — riêng
  nguồn = Prompt thì AI được chủ động chọn case, miễn có ghi rõ lý do).
- Oracle độc lập với code app (không import hàm tính toán của app làm kỳ
  vọng), và đã chứng minh bằng mutation check là test FAIL khi app sai.
- Đã chạy thử thật ít nhất 1 lần và pass (hoặc đã sửa tới khi pass, hoặc đã
  dừng lại báo cáo rõ lý do nếu không tự sửa được).
- Không còn case nào thiếu Given/When/Then cụ thể mà chưa báo rõ với người
  dùng phần nào còn thiếu và vì sao.
- Mỗi Scenario/hàng Examples có ID `[TC-xxx]`/`[BC-xxx]` ổn định; case cũ giữ
  nguyên ID khi thêm case mới.
- Fixture `browser` đã nhận `demo_mode` (sẵn sàng cho `pytest --demo` ở bước
  chạy test), và mặc định không có cờ thì vẫn headless/nhanh.
- Bằng chứng Allure đã được nối đúng convention: scenario UI dùng fixture tên
  `page` (có cả ảnh chụp màn hình lẫn lịch sử `HTTP calls` tự động); scenario
  API gọi `attach_api_call(...)` ngay sau khi có response thật — để
  `autotest-run-test` có bằng chứng + truy vết đầy đủ, không phải báo cáo
  trống bằng chứng.
- Không hard-code URL/path/số điện thoại/data test phụ thuộc môi trường
  thẳng trong step — đọc qua `autotest_env.global_vars()`/`local_vars(...)`.
  Feature mới có data riêng đã có `testing/env/local/<feature>.yaml` với giá
  trị THẬT cho cả `uat` và `prod` (không phải placeholder từ file mẫu), trừ
  khi đã hỏi và người dùng chưa cung cấp — thì phải nêu rõ đang thiếu, không
  âm thầm để giá trị mẫu.

## Khi nào KHÔNG tự quyết
- UI thiếu `data-testid` cho phần tử cần thao tác → hỏi có nên thêm
  `data-testid` vào code app hay dùng selector khác, không tự chọn selector
  mong manh rồi âm thầm chấp nhận rủi ro flaky.
- Không rõ giá trị kỳ vọng đúng của 1 step Then (không có công thức/nguồn rõ
  ràng) → hỏi người dùng/PO, không tự đặt một số "có vẻ hợp lý".
- Nguồn = file testcase có sẵn nhưng file thiếu thông tin (cột kỳ vọng, mô tả
  case mơ hồ) → hỏi người dùng cách hiểu đúng, không tự suy diễn rồi âm thầm
  bỏ case hoặc gộp sai case.
- Test FAIL do app có bug thật (không phải lỗi kịch bản) → báo bug, KHÔNG tự
  gắn `@pytest.mark.xfail` để che fail đi. Chỉ gắn `xfail` khi người dùng/PO
  đã xác nhận rõ đây là bug đã biết, đang chờ fix ở release khác (xem quy ước
  "Known bug (xfail)" ở `autotest-run-test`) — tự quyết định thay người dùng
  việc nào là "known, chấp nhận được" là sai phạm vi.
- Chưa biết giá trị THẬT của 1 biến môi trường (URL PROD, số điện thoại test,
  path...) cho `testing/env/global.yaml`/`local/<feature>.yaml` → hỏi người
  dùng, không tự bịa hoặc copy nguyên giá trị mẫu từ `*.example.yaml` rồi coi
  như xong — data UAT/PROD sai sẽ làm test PROD chạy nhầm data giả.
