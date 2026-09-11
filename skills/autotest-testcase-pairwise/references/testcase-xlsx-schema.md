# Schema `testcase-pairwise.xlsx`

Sheet duy nhất tên `testcase-pairwise`, dòng 1 là header (bold, freeze pane).

| Cột | Ý nghĩa |
|---|---|
| `MatrixID` | Số thứ tự dòng — dùng để truy vết 1-1 sang `.feature` (Scenario Outline dùng `[<MatrixID>]` trong tên) và sang báo cáo (`test_summary.md`, Allure parameters). |
| `<mỗi Factor trong factor.md>` | 1 cột / factor, đúng tên đã đặt trong PICT model (PascalCase, không dấu). Trống ở các dòng `Boundary` (case biên không nằm trong không gian factor pairwise). |
| `Loai` | `Pairwise` (sinh bởi pict-cli) hoặc `Boundary` (case biên/negative, chép từ mục 4 của factor.md). |
| `Gherkin` | Với dòng `Pairwise`: text Gherkin ĐÃ ĐIỀN giá trị cụ thể (nhiều dòng, 1 dòng/step When-And), render từ `--gherkin-template` — dùng để người không đọc code vẫn hình dung được kịch bản, và để bước `autotest-gen-test` đối chiếu khi sinh `.feature`. Với dòng `Boundary`: mô tả case + input (cần viết Gherkin/step tay ở bước gen-test vì không có template chung). |
| `KetQuaMongDoi` | Kết quả mong đợi ngắn gọn. Dòng Pairwise thường để trống (kết quả mong đợi là công thức chung, viết trong step Then của `.feature`, không lặp lại từng dòng); dòng Boundary lấy từ factor.md. |
| `GhiChu` | Ghi chú tự do (vd "Viết Gherkin/step tay ở bước gen-test" cho dòng Boundary). |

## Quy ước
- `MatrixID` liên tục 1..N, dòng Pairwise trước, dòng Boundary sau.
- Không sửa tay số liệu ở cột factor của dòng Pairwise sau khi sinh — nếu cần
  đổi, sửa `factor.md`/model PICT rồi chạy lại `pict_to_xlsx.py` (giữ nguồn dữ
  liệu là code sinh ra, không phải xlsx chỉnh tay, để tái sinh được).
- Được phép sửa tay cột `Gherkin`/`KetQuaMongDoi`/`GhiChu` của dòng `Boundary`
  sau khi sinh (đây là phần cần con người viết), không cần chạy lại script.
