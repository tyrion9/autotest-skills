# Schema `testcase-pairwise.xlsx`

File có **2 sheet**:

## Sheet `testcase-pairwise` (dữ liệu chính)

Dòng 1 là header (bold, freeze pane).

| Cột | Ý nghĩa |
|---|---|
| `STT` | Số thứ tự cho dễ đọc. **KHÔNG dùng để truy vết** — sẽ xô lệch mỗi lần sinh lại. |
| `MatrixID` | **ID ổn định**, hash theo nội dung tổ hợp: `TC-xxxxxx` (dòng pairwise) / `BC-xxxxxx` (case biên). Cùng 1 tổ hợp giá trị luôn ra cùng 1 ID dù đổi vị trí dòng hay sinh lại file → bug report/comment cũ trích MatrixID vẫn trỏ đúng tổ hợp. Đây là ID dùng trong tên Scenario, Allure parameters và `test_summary.md`. |
| `<mỗi Factor>` | 1 cột / factor, đúng tên trong PICT model (PascalCase, không dấu). Trống ở dòng `Boundary`. |
| `Loai` | `Pairwise` (sinh bởi pict-cli) hoặc `Boundary` (case biên, chép từ mục 4 của factor.md). |
| `Gherkin` | Dòng `Pairwise`: text Gherkin ĐÃ ĐIỀN giá trị cụ thể (nhiều dòng, 1 dòng/step), render từ `--gherkin-template`. Dòng `Boundary`: mô tả case + input (Gherkin/step viết tay ở bước gen-test). |
| `KetQuaMongDoi` | Kết quả mong đợi. Dòng Pairwise thường để trống (kỳ vọng là công thức chung, viết trong step `Then`); dòng Boundary lấy từ factor.md. |
| `GhiChu` | Ghi chú tự do. |

## Sheet `meta` (provenance — phục vụ audit)

Cặp `key | value`, ghi lại chính xác thứ đã sinh ra file:

| key | Ý nghĩa |
|---|---|
| `generated_at` | Thời điểm sinh |
| `model_file`, `model_sha1` | Model PICT và hash nội dung của nó |
| `pict_cli` | Phiên bản pict-cli được ghim (vd `pict-cli@0.2`) |
| `order`, `seed` | Bậc phủ (2 = pairwise) và seed — quyết định tính tái lập |
| `pict_stats` | Thống kê từ `pict-cli -s` (số combination cần phủ / số test sinh ra) |
| `factors` | Danh sách factor |
| `rows_pairwise`, `rows_boundary` | Số dòng từng loại |
| `gherkin_template`, `gherkin_template_sha1` | Template Gherkin và hash |
| `factor_file`, `factor_sha1` | factor.md và hash |

Nhờ các hash này, khi cầm 1 file xlsx cũ vẫn biết được nó sinh từ model/template
nào — cần khi điều tra "vì sao testcase này lại có tổ hợp đó".

## Quy ước

- **Không sửa tay** cột factor của dòng `Pairwise`. Muốn đổi → sửa
  `factor.md`/model rồi chạy lại script. CI nên chạy `pict_to_xlsx.py ... --check`
  để bắt trường hợp file bị sửa tay hoặc model đã đổi mà chưa regenerate.
- **Được phép sửa tay** `Gherkin`/`KetQuaMongDoi`/`GhiChu` của dòng `Boundary`
  (đây là phần con người viết) — nhưng nhớ cập nhật lại `factor.md` mục 4 cho
  khớp, nếu không lần regenerate sau sẽ ghi đè mất.
- `MatrixID` của dòng Boundary hash từ (mô tả case + input) → đổi mô tả trong
  factor.md sẽ đổi ID; giữ mô tả ổn định nếu muốn giữ traceability.
