#!/usr/bin/env python3
"""Sinh testcase-pairwise.xlsx từ 1 PICT model (+ tuỳ chọn factor.md + gherkin-template).

Triết lý: phần TÍNH TOÁN tổ hợp (pict-cli) và GHÉP CHUỖI (string template) đều
là code xác định — không để AI tự bịa dòng nào. Phần cần phán đoán ngôn ngữ tự
nhiên (chọn cách diễn đạt Gherkin cho tính năng cụ thể) do Claude làm 1 LẦN khi
viết ra file --gherkin-template, không phải làm lại cho từng dòng.

Cách dùng:
    python pict_to_xlsx.py MODEL.txt \
        --gherkin-template TEMPLATE.txt \
        [--factor FACTOR.md] \
        [--order 2] [--seed 42] \
        [-o testcase-pairwise.xlsx]

MODEL.txt        : file model PICT (xem skill design-pairwise-tests).
TEMPLATE.txt      : mỗi dòng là 1 step Gherkin ĐÃ CÓ từ khoá (When/And...),
                    placeholder dùng ĐÚNG cú pháp Gherkin Scenario Outline
                    <TenFactor> (khớp chính xác tên cột PICT model, phân biệt
                    hoa/thường) — vd: `When khách chọn đồ uống "<Drink>"`.
                    Dùng chung cú pháp <...> để file này TÁI DÙNG NGUYÊN VẸN
                    ở bước autotest-gen-test (xlsx_to_feature.py) khi dựng
                    khối Scenario Outline, không phải viết 2 bản. Không
                    truyền --gherkin-template thì cột Gherkin để trống.
FACTOR.md         : nếu có, đọc mục "## 4. Case biên / Negative" (bảng markdown)
                    để thêm các dòng Loai=Boundary vào cuối (không qua pict-cli).

Output: .xlsx với cột MatrixID | <factor...> | Loai | Gherkin | KetQuaMongDoi | GhiChu
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
except ImportError:
    print("Cần cài openpyxl trước: pip install openpyxl", file=sys.stderr)
    raise


def run_pict(model_path: Path, order: int, seed: int) -> list[dict]:
    if not shutil.which("npx"):
        raise RuntimeError("Không tìm thấy 'npx' trong PATH — cần Node.js để chạy pict-cli")
    cmd = ["npx", "-y", "pict-cli@0.2", str(model_path), "-o", str(order), "-r", str(seed)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError(f"pict-cli không trả ra dòng nào. stderr: {result.stderr}")
    header = lines[0].split("\t")
    rows = [dict(zip(header, line.split("\t"))) for line in lines[1:]]
    return rows


_PLACEHOLDER_RE = re.compile(r"<([A-Za-z0-9_]+)>")


def render_gherkin(template_lines: list[str], row: dict) -> str:
    """Thay <TenFactor> bằng giá trị thật của dòng. Cùng cú pháp <...> này được
    xlsx_to_feature.py tái dùng nguyên vẹn cho khối Scenario Outline (không thay)."""
    rendered = []
    for line in template_lines:
        def _sub(m: re.Match) -> str:
            name = m.group(1)
            if name not in row:
                raise KeyError(
                    f"<{name}> nhưng PICT model không có cột này. Các cột hiện có: {list(row)}"
                )
            return row[name]

        rendered.append(_PLACEHOLDER_RE.sub(_sub, line))
    return "\n".join(rendered)


def parse_boundary_rows(factor_md_path: Path) -> list[dict]:
    """Đọc bảng markdown trong mục '## 4. Case biên' của factor.md -> list dict theo cột."""
    text = factor_md_path.read_text(encoding="utf-8")
    match = re.search(r"##\s*4\..*?\n(.*?)(\n##\s|\Z)", text, re.S)
    if not match:
        return []
    table_lines = [line for line in match.group(1).splitlines() if line.strip().startswith("|")]
    if len(table_lines) < 2:
        return []
    headers = [c.strip() for c in table_lines[0].strip("|").split("|")]
    rows = []
    for line in table_lines[2:]:  # bỏ header + dòng phân cách "---"
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) != len(headers):
            continue
        rows.append(dict(zip(headers, cells)))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model", type=Path, help="File model PICT")
    ap.add_argument("--gherkin-template", type=Path, default=None)
    ap.add_argument("--factor", type=Path, default=None, help="factor.md để lấy case biên")
    ap.add_argument("--order", type=int, default=2, help="Bậc phủ (2=pairwise). Mặc định 2")
    ap.add_argument("--seed", type=int, default=42, help="Seed cho pict-cli -r (tái lập được)")
    ap.add_argument("-o", "--output", type=Path, default=Path("testcase-pairwise.xlsx"))
    args = ap.parse_args()

    pict_rows = run_pict(args.model, args.order, args.seed)
    factor_names = list(pict_rows[0].keys()) if pict_rows else []

    template_lines: list[str] = []
    if args.gherkin_template:
        template_lines = [
            line for line in args.gherkin_template.read_text(encoding="utf-8").splitlines() if line.strip()
        ]

    boundary_rows: list[dict] = []
    if args.factor:
        boundary_rows = parse_boundary_rows(args.factor)

    wb = Workbook()
    ws = wb.active
    ws.title = "testcase-pairwise"
    header = ["MatrixID", *factor_names, "Loai", "Gherkin", "KetQuaMongDoi", "GhiChu"]
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for i, row in enumerate(pict_rows, start=1):
        gherkin = render_gherkin(template_lines, row) if template_lines else ""
        ws.append([i, *[row[f] for f in factor_names], "Pairwise", gherkin, "", ""])

    offset = len(pict_rows)
    for j, brow in enumerate(boundary_rows, start=1):
        desc = brow.get("Mô tả case") or next(iter(brow.values()), "")
        input_val = brow.get("Input", "")
        expected = brow.get("Kết quả mong đợi", "")
        blank_factors = ["" for _ in factor_names]
        gherkin_note = f"{desc}\nInput: {input_val}" if input_val else desc
        ws.append([offset + j, *blank_factors, "Boundary", gherkin_note, expected, "Viết Gherkin/step tay ở bước gen-test"])

    # Bọc chữ cho cột Gherkin/KetQuaMongDoi/GhiChu, tự co giãn độ rộng cột còn lại
    gherkin_col_idx = header.index("Gherkin") + 1
    for row_cells in ws.iter_rows(min_row=2):
        row_cells[gherkin_col_idx - 1].alignment = Alignment(wrap_text=True, vertical="top")
    for col_cells in ws.columns:
        header_name = col_cells[0].value
        if header_name == "Gherkin":
            ws.column_dimensions[col_cells[0].column_letter].width = 60
            continue
        length = max((len(str(c.value)) for c in col_cells if c.value is not None), default=10)
        ws.column_dimensions[col_cells[0].column_letter].width = min(max(length + 2, 10), 40)
    ws.freeze_panes = "A2"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wb.save(args.output)

    total = len(pict_rows) + len(boundary_rows)
    print(
        f"Đã ghi {args.output} — {len(pict_rows)} dòng Pairwise + {len(boundary_rows)} dòng Boundary "
        f"= {total} dòng, {len(factor_names)} factor ({', '.join(factor_names)})"
    )


if __name__ == "__main__":
    main()
