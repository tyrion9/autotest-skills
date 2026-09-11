#!/usr/bin/env python3
"""Sinh khối Gherkin (.feature) từ testcase-pairwise.xlsx.

testcase-pairwise.xlsx là NGUỒN CHÂN LÝ cho Examples (dòng Loai=Pairwise) và
danh sách case biên (dòng Loai=Boundary). File --gherkin-template (cùng file
đã dùng ở bước autotest-testcase-pairwise, cú pháp <TenFactor>) được tái dùng
NGUYÊN VẸN làm thân bài Scenario Outline — không viết lại, đảm bảo Gherkin
sinh ra khớp 100% với dữ liệu đã render trong cột "Gherkin" của xlsx.

Cách dùng:
    python xlsx_to_feature.py testcase-pairwise.xlsx \
        --gherkin-template <feature>.gherkin-template.txt \
        --feature-name "Tên feature" \
        --scenario-title "Tên Scenario Outline" \
        [--background background.txt] [--then-steps then.txt] \
        [--tag pairwise] [-o out.feature]

Không truyền -o thì in ra stdout để người dùng/Claude tự chèn/so sánh với
.feature hiện có (khuyến nghị khi cập nhật 1 feature đã tồn tại, tránh ghi đè
các Scenario khác không do script này quản lý).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from openpyxl import load_workbook


def read_rows(xlsx_path: Path) -> tuple[list[str], list[dict]]:
    wb = load_workbook(xlsx_path, read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    header = list(next(rows_iter))
    rows = [dict(zip(header, r)) for r in rows_iter if any(v is not None for v in r)]
    return header, rows


def factor_columns(header: list[str]) -> list[str]:
    start = header.index("MatrixID") + 1
    end = header.index("Loai")
    return header[start:end]


def build_examples_table(factors: list[str], pairwise_rows: list[dict]) -> str:
    cols = ["MatrixID", *factors]
    lines = ["    Examples:", "      | " + " | ".join(cols) + " |"]
    for row in pairwise_rows:
        values = [str(row.get(c, "")) for c in cols]
        lines.append("      | " + " | ".join(values) + " |")
    return "\n".join(lines)


def indent(lines: list[str], n: int) -> list[str]:
    pad = " " * n
    return [f"{pad}{line}" if line.strip() else line for line in lines]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("xlsx", type=Path)
    ap.add_argument("--gherkin-template", type=Path, required=True)
    ap.add_argument("--feature-name", required=True)
    ap.add_argument("--scenario-title", required=True)
    ap.add_argument("--background", type=Path, default=None, help="File chứa step Given (Background), tuỳ chọn")
    ap.add_argument("--then-steps", type=Path, default=None, help="File chứa step Then/And nối sau template, tuỳ chọn")
    ap.add_argument("--tag", default="pairwise", help="Tag gắn trên Scenario Outline, mặc định 'pairwise'")
    ap.add_argument("-o", "--output", type=Path, default=None, help="Ghi ra file thay vì in stdout")
    args = ap.parse_args()

    header, rows = read_rows(args.xlsx)
    factors = factor_columns(header)
    pairwise_rows = [r for r in rows if r.get("Loai") == "Pairwise"]
    boundary_rows = [r for r in rows if r.get("Loai") == "Boundary"]

    template_lines = [
        line for line in args.gherkin_template.read_text(encoding="utf-8").splitlines() if line.strip()
    ]

    out: list[str] = [f"Feature: {args.feature_name}", ""]

    if args.background:
        out += ["  Background:"]
        out += indent(
            [line for line in args.background.read_text(encoding="utf-8").splitlines() if line.strip()], 4
        )
        out.append("")

    out += [f"  @{args.tag}"]
    out += [f"  Scenario Outline: [<MatrixID>] {args.scenario_title}"]
    out += indent(template_lines, 4)
    if args.then_steps:
        out += indent(
            [line for line in args.then_steps.read_text(encoding="utf-8").splitlines() if line.strip()], 4
        )
    out.append("")
    out += indent([build_examples_table(factors, pairwise_rows)], 0)
    out.append("")

    if boundary_rows:
        out += ["  Rule: Kiểm tra dữ liệu biên / không hợp lệ (từ factor.md mục 4, KHÔNG thuộc bảng pairwise)", ""]
        for row in boundary_rows:
            note = str(row.get("Gherkin", "")).strip() or "(chưa có mô tả)"
            expected = str(row.get("KetQuaMongDoi", "")).strip()
            first_line = note.splitlines()[0]
            out += [f"    Scenario: [Boundary #{row.get('MatrixID')}] {first_line}"]
            out += ["      # TODO: viết cụ thể Given/When/Then cho case này. Tham khảo:"]
            for note_line in note.splitlines():
                out.append(f"      #   {note_line}")
            if expected:
                out.append(f"      #   Kỳ vọng: {expected}")
            out.append("")

    text = "\n".join(out).rstrip() + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Đã ghi {args.output} ({len(pairwise_rows)} dòng pairwise, {len(boundary_rows)} case biên)")
    else:
        print(text)


if __name__ == "__main__":
    main()
