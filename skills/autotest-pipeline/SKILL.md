---
name: autotest-pipeline
description: Điều phối toàn bộ quy trình autotest 4 bước (factor -> pairwise -> gen-test -> run-test) cho một màn hình/API/luồng nghiệp vụ. Dùng khi người dùng yêu cầu "chạy autotest cho...", "tự động hoá kiểm thử cho...", hoặc muốn thực hiện trọn vẹn từ requirement tới báo cáo test mà không nêu rõ đang ở bước nào. Nếu người dùng chỉ định rõ 1 bước cụ thể (vd "chỉ phân tích factor", "chỉ sinh lại testcase-pairwise"), dùng thẳng skill con tương ứng thay vì skill điều phối này.
---

# Autotest Pipeline (điều phối)

Quy trình 4 bước, mỗi bước là 1 skill riêng, nối nhau bằng file/artifact cụ
thể (không truyền ngữ cảnh ngầm) để mỗi bước có thể dừng lại, review, và chạy
lại độc lập:

```
Requirement / mô tả màn hình / mã nguồn thật
        │  autotest-factor-analysis
        ▼
factor.md  (Factor & Levels, Constraints, Case biên, câu hỏi mở)
        │  autotest-testcase-pairwise  (dùng design-pairwise-tests + pict-cli)
        ▼
testcase-pairwise.xlsx  (MatrixID, factor..., Loại, Gherkin, Kết quả mong đợi)
        │  autotest-gen-test
        ▼
.feature + step definitions (Python, đã pytest --collect-only + chạy thử OK)
        │  autotest-run-test
        ▼
Kết quả test + report.html + allure-report/ + test_summary.md
```

## Cách điều phối

1. Chạy từng skill theo đúng thứ tự trên. **Không gộp tắt** (vd nhảy thẳng từ
   requirement sang code test) — mỗi artifact trung gian (`factor.md`,
   `testcase-pairwise.xlsx`) là điểm con người có thể đọc lại/sửa tay trước
   khi bước sau dùng nó làm input.
2. **Điểm dừng bắt buộc hỏi người dùng** (không tự đoán rồi đi tiếp):
   - Sau `factor.md`: nếu có mục "Câu hỏi mở/giả định" chưa được xác nhận và
     ảnh hưởng tới việc chọn Factor/Constraint, hỏi trước khi sinh pairwise.
   - Trước `autotest-run-test`: nếu thiếu tham số môi trường bắt buộc (base
     URL, tài khoản test, biến môi trường) mà không suy luận được từ code có
     sẵn trong project.
3. Nếu 1 bước lỗi và không tự sửa được trong phạm vi skill đó, DỪNG lại ở đó,
   báo cáo rõ đang kẹt ở bước nào và vì sao — không chuyển sang bước kế tiếp
   với dữ liệu chưa xác nhận.
4. Khi chạy lại pipeline cho 1 thay đổi nhỏ (vd thêm 1 factor), chỉ cần chạy
   lại từ bước bị ảnh hưởng trở đi (không nhất thiết làm lại từ đầu) — nhờ
   các artifact trung gian đã lưu thành file.
5. **Kết thúc pipeline lần đầu cho 1 project, luôn đề xuất gắn 2 lệnh
   `--check` vào CI của project** (xem mục "Bảo vệ khỏi drift" bên dưới) —
   nếu không, `.xlsx`/`.feature` sẽ dần lệch khỏi `factor.md` mà không ai
   phát hiện.

## Yêu cầu môi trường

- **Node.js 22 hoặc 24** (pict-cli khai `engines: ^22 || ^24`; Node 18/20 trên
  nhiều CI runner sẽ không chạy được) + `npx`.
- Python 3.10+ với `openpyxl`; `pytest`, `pytest-bdd`, `playwright` cho bộ test;
  khuyến nghị `pytest-rerunfailures` (xử lý flaky ở tầng CI) và Allure CLI.

## Quy ước thư mục artifact (mặc định, có thể điều chỉnh theo project)

```
testing/factor/<feature>.factor.md
testing/factor/<feature>.model.txt              (model PICT)
testing/factor/<feature>.gherkin-template.txt   (step Gherkin + <TenFactor>)
testing/testcase-pairwise.xlsx        (hoặc testing/<feature>/testcase-pairwise.xlsx nếu nhiều luồng)
testing/features/<feature>.feature
testing/steps/test_<feature>_steps.py
testing/autotest_reporting.py         (plugin báo cáo, copy từ skill autotest-run-test)
reports/{test_summary.md, report.html, allure-report/}
```

## Bảo vệ khỏi drift (bắt buộc cho dùng lâu dài)

Hai lệnh sau nên chạy trong CI của project mỗi PR — chúng phát hiện khi
`.xlsx`/`.feature` bị sửa tay hoặc `factor.md`/model đã đổi mà chưa regenerate:

```bash
python <skill autotest-testcase-pairwise>/scripts/pict_to_xlsx.py \
  testing/factor/<feature>.model.txt \
  --gherkin-template testing/factor/<feature>.gherkin-template.txt \
  --factor testing/factor/<feature>.factor.md \
  -o testing/testcase-pairwise.xlsx --check

python <skill autotest-gen-test>/scripts/xlsx_to_feature.py \
  testing/testcase-pairwise.xlsx \
  --gherkin-template testing/factor/<feature>.gherkin-template.txt \
  --feature-name "..." --scenario-title "..." \
  --background ... --then-steps ... \
  --check testing/features/<feature>.feature
```

Xem chi tiết từng bước ở skill con: `autotest-factor-analysis`,
`autotest-testcase-pairwise`, `autotest-gen-test`, `autotest-run-test`.
