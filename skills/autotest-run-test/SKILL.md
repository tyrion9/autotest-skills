---
name: autotest-run-test
description: Chạy bộ test đã sinh (pytest-bdd + Playwright), tự phân loại và sửa lỗi kịch bản (không tự sửa bug thật của app), hỏi người dùng khi thiếu tham số môi trường, rồi sinh báo cáo (test_summary.md, pytest-html, Allure). Dùng khi người dùng nói "chạy test", "chạy lại bộ test và cho báo cáo", hoặc bước 4 (cuối) của autotest-pipeline.
---

# Autotest: Run Test (chạy, tự sửa/hỏi tham số, gen báo cáo)

## Mục tiêu
Chạy bộ test tới cùng, phân biệt rõ 3 loại lỗi (bug thật / lỗi kịch bản /
flaky), chỉ tự sửa loại mình được phép sửa, và luôn kết thúc bằng báo cáo có
thể đọc lại được.

## Các bước

1. **Xác định tham số chạy**: base URL của app, cách seed dữ liệu test, biến
   môi trường cần thiết (vd cổng, thư mục DB test), headless/headed, có chạy
   song song không. Nếu **suy luận được từ code có sẵn** (vd project đã có
   `scripts/run_tests.sh`, `conftest.py` định nghĩa base URL) thì dùng thẳng,
   không hỏi lại. Nếu **thiếu** (project mới, chưa có mặc định) → hỏi người
   dùng, không tự bịa URL/credentials/cổng.

2. **Seed dữ liệu test** bằng script seed sẵn có của project (không tự viết
   script seed mới nếu đã có sẵn một cái).

3. **Chạy toàn bộ bộ test** theo đúng pipeline đã thiết lập của project (vd
   `bash scripts/run_tests.sh` trong ví dụ cà phê — script này tự sinh cả 3
   tầng báo cáo và tự phát hiện có Allure CLI hay không).

4. **Có fail → phân loại trước khi hành động**:
   | Loại | Dấu hiệu | Hành động |
   |---|---|---|
   | Bug thật của app | Request/response hợp lý theo kịch bản nhưng kết quả nghiệp vụ sai (vd tổng tiền tính sai) | **KHÔNG tự sửa code app.** Báo cáo là bug, kèm bằng chứng cụ thể (request/response JSON, ảnh chụp màn hình — lấy từ attachment Allure nếu có) |
   | Lỗi kịch bản/selector | `TimeoutError` do selector không khớp, step thiếu, sai thứ tự thao tác | Tự sửa test code, chạy lại (tối đa 3 lần) |
   | Nghi flaky | Fail không nhất quán, lỗi timing/network tạm thời | Chạy lại có kiểm soát 1 lần; còn fail nữa thì coi là lỗi thật (không tự động retry vô hạn để "cho qua") |

5. **Sinh báo cáo** (giữ nguyên 3 tầng đã có trong ví dụ cà phê, áp dụng cho
   mọi project dùng bộ skill này):
   - `reports/test_summary.md` — 1 dòng/scenario, có MatrixID.
   - `reports/report.html` — pytest-html.
   - `reports/allure-report/index.html` — chi tiết nhất, có request/response,
     ảnh chụp màn hình, tham số theo MatrixID (nếu project đã cấu hình Allure
     như hướng dẫn trong README của ví dụ cà phê).

6. **Tổng kết cho người dùng**: số scenario pass/fail, việc gì đã tự sửa
   (kèm diff ngắn gọn), việc gì là bug thật cần người review, và đường dẫn
   report để mở.

## Definition of done
- Có kết quả chạy thật cuối cùng (pass hoặc fail đã phân loại rõ), không kết
  luận "chắc là do X" mà chưa xác minh.
- 3 tầng báo cáo được sinh ra (hoặc nêu rõ tầng nào bị bỏ qua và vì sao, vd
  chưa cài Allure CLI).
- Không có sửa đổi nào vào code ứng dụng (app) trong bước này — mọi bug thật
  chỉ được báo cáo, việc sửa app là quyết định của người dùng/dev.

## Khi nào KHÔNG tự quyết
- Thiếu tham số môi trường bắt buộc (URL, tài khoản test, secret) → hỏi,
  không tự bịa giá trị "tạm".
- Không chắc 1 fail là bug thật hay lỗi kịch bản sau khi đã xem
  request/response → nêu rõ nghi vấn với bằng chứng, để người dùng quyết định
  thay vì tự gắn nhãn.
- Muốn "sửa" 1 fail bằng cách nới lỏng assertion (vd bỏ bớt điều kiện check)
  → KHÔNG được làm — đó là che giấu lỗi chứ không phải sửa lỗi.
