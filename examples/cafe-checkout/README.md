# Ví dụ: Chọn đồ uống & thanh toán (checkout) tại quán cà phê

Đây là bộ artifact THẬT do bộ skill `autotest-*` sinh ra khi áp dụng vào 1
tính năng cụ thể — "chọn đồ uống, tuỳ chỉnh (size/đường/đá/topping), số
lượng, thanh toán" của 1 app Flask + SQLite demo. Giữ lại ở đây làm ví dụ
tham khảo, không phải hướng dẫn cài đặt.

App demo đầy đủ (Flask + Playwright + Allure) không nằm trong repo skill
này — repo này chỉ chứa các artifact input/output của quy trình.

| File | Sinh bởi bước | Nội dung |
|---|---|---|
| `checkout.factor.md` | `autotest-factor-analysis` | Factor & Levels, Constraint, Case biên — trích từ code thật của app |
| `checkout.model.txt` | `autotest-testcase-pairwise` | Model PICT dựng từ factor.md |
| `checkout.gherkin-template.txt` | `autotest-testcase-pairwise` | Step Gherkin mẫu, placeholder `<TenFactor>` — viết 1 lần, dùng lại cho cả xlsx lẫn `.feature` |
| `checkout.background.txt` / `checkout.then-steps.txt` | `autotest-testcase-pairwise` (chuẩn bị cho gen-test) | Step Given/Then cố định |
| `testcase-pairwise.xlsx` | `autotest-testcase-pairwise` | 27 dòng Pairwise + 2 dòng Boundary, có cột Gherkin đã render |
| `checkout.feature` | `autotest-gen-test` | Gherkin cuối cùng (Scenario Outline + Examples lấy từ xlsx, Rule cho case biên) |

**Đã validate**: chạy lại toàn bộ quy trình này trong 1 thư mục clean-room
(chỉ có code app, không có sẵn các file trên) — 27 dòng Pairwise sinh ra khớp
100% từng ký tự với bộ ở đây; bộ test Python sinh từ `autotest-gen-test` chạy
thật (Playwright) cho kết quả 29/29 PASS.
