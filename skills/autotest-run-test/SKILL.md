---
name: autotest-run-test
description: Chạy bộ test đã sinh (pytest-bdd + Playwright), tự phân loại và sửa lỗi kịch bản (không tự sửa bug thật của app), hỏi người dùng khi thiếu tham số môi trường, rồi sinh báo cáo (test_summary.md, pytest-html, Allure). Dùng khi người dùng nói "chạy test", "chạy lại bộ test và cho báo cáo", hoặc bước 4 (cuối) của autotest-pipeline.
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

2. **Cài plugin báo cáo dùng chung** (nếu project chưa có): copy
   `assets/autotest_reporting.py` (cùng thư mục với SKILL.md này) vào thư mục
   chứa `conftest.py` của project, rồi khai báo trong `conftest.py`:
   ```python
   pytest_plugins = ["autotest_reporting"]

   import autotest_reporting
   autotest_reporting.ENVIRONMENT.update({"App.URL": BASE_URL, "Browser": "Chromium (Playwright)"})
   ```
   Plugin này sinh `reports/test_summary.md` (truy vết theo MatrixID, có cột
   số lần rerun) và `environment.properties` cho Allure. **Không tự viết lại
   hook báo cáo cho từng project** — dùng plugin dùng chung để mọi project
   ra cùng 1 định dạng báo cáo.

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

6. **Có fail → phân loại TRƯỚC khi hành động**:
   | Loại | Dấu hiệu | Hành động |
   |---|---|---|
   | Bug thật của app | Request/response hợp lý theo kịch bản nhưng kết quả nghiệp vụ sai (vd tổng tiền tính sai) | **KHÔNG tự sửa code app.** Báo cáo là bug kèm bằng chứng (request/response JSON, ảnh chụp màn hình từ attachment Allure) + MatrixID để tái hiện |
   | Lỗi kịch bản/selector | `TimeoutError` do selector không khớp, step thiếu, sai thứ tự thao tác | Tự sửa test code, chạy lại (tối đa 3 lần) |
   | Nghi flaky | Fail không nhất quán, pass sau rerun, lỗi timing/network | Xem cột "Lần chạy lại" trong `test_summary.md`; báo rõ là flaky và đề xuất nguyên nhân — KHÔNG im lặng cho qua vì "chạy lại thì pass" |

7. **Tổng kết cho người dùng**: số scenario pass/fail/flaky, việc gì đã tự
   sửa (kèm diff ngắn), việc gì là bug thật cần người review (kèm MatrixID),
   và đường dẫn report để mở.

## Definition of done
- Có kết quả chạy thật cuối cùng, mọi fail đã được phân loại rõ (không kết
  luận "chắc là do X" mà chưa xác minh bằng bằng chứng).
- `reports/test_summary.md` + `reports/report.html` được sinh ra; thêm
  `reports/allure-report/` nếu máy có Allure CLI (không có thì nêu rõ).
- Không có sửa đổi nào vào code ứng dụng (app) trong bước này.

## Khi nào KHÔNG tự quyết
- Thiếu tham số môi trường bắt buộc (URL, tài khoản test, secret) → hỏi.
- Không chắc 1 fail là bug thật hay lỗi kịch bản sau khi đã xem
  request/response → nêu rõ nghi vấn kèm bằng chứng, để người dùng quyết định.
- Muốn "sửa" 1 fail bằng cách nới lỏng assertion, bỏ bớt điều kiện check,
  hoặc tăng `--reruns` cho tới khi pass → **KHÔNG được làm**: đó là che giấu
  lỗi, không phải sửa lỗi.
