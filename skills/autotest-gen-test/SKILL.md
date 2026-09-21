---
name: autotest-gen-test
description: Sinh code test Python (Gherkin .feature + pytest-bdd step definitions dùng Playwright) từ 1 trong 3 nguồn — prompt mô tả nghiệp vụ của người dùng, 1 file testcase có sẵn (xlsx/csv/markdown/text), hoặc 1 file .feature đã viết sẵn — và TỰ VERIFY (collect + chạy thử + mutation check) trước khi báo hoàn thành. Dùng khi người dùng nói "viết test cho tính năng...", "sinh test từ file testcase này", "viết step definitions cho file .feature này", hoặc bất cứ khi nào cần code test E2E chạy được ngay từ 1 trong 3 nguồn trên.
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
  thao tác, báo cho người dùng — không tự đoán selector CSS mong manh).
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

## Khi nào KHÔNG tự quyết
- UI thiếu `data-testid` cho phần tử cần thao tác → hỏi có nên thêm
  `data-testid` vào code app hay dùng selector khác, không tự chọn selector
  mong manh rồi âm thầm chấp nhận rủi ro flaky.
- Không rõ giá trị kỳ vọng đúng của 1 step Then (không có công thức/nguồn rõ
  ràng) → hỏi người dùng/PO, không tự đặt một số "có vẻ hợp lý".
- Nguồn = file testcase có sẵn nhưng file thiếu thông tin (cột kỳ vọng, mô tả
  case mơ hồ) → hỏi người dùng cách hiểu đúng, không tự suy diễn rồi âm thầm
  bỏ case hoặc gộp sai case.
