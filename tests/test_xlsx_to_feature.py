"""Unit test cho skills/autotest-gen-test/scripts/xlsx_to_feature.py."""

from __future__ import annotations

import argparse

import pytest
from openpyxl import Workbook

HEADER = ["STT", "MatrixID", "Drink", "Size", "Loai", "Gherkin", "KetQuaMongDoi", "GhiChu"]


def _make_xlsx(path, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = "testcase-pairwise"
    ws.append(HEADER)
    for r in rows:
        ws.append(r)
    wb.save(path)
    return path


def _sample_xlsx(tmp_path):
    return _make_xlsx(
        tmp_path / "tc.xlsx",
        [
            [1, "TC-AAA111", "TraDao", "S", "Pairwise", 'When chọn "TraDao"', "", ""],
            [2, "TC-BBB222", "CaPheDen", "L", "Pairwise", 'When chọn "CaPheDen"', "", ""],
            [3, "BC-CCC333", "", "", "Boundary", "Số lượng = 0\nInput: Qty=0", "Báo lỗi", "viết tay"],
        ],
    )


def _args(tmp_path, **overrides):
    template = tmp_path / "tpl.txt"
    template.write_text('When khách chọn đồ uống "<Drink>"\nAnd size "<Size>"\n', encoding="utf-8")
    then = tmp_path / "then.txt"
    then.write_text("Then tổng tiền đúng\n", encoding="utf-8")
    bg = tmp_path / "bg.txt"
    bg.write_text("Given khách mở trang menu\n", encoding="utf-8")

    args = argparse.Namespace(
        gherkin_template=template,
        then_steps=then,
        background=bg,
        feature_name="Demo feature",
        scenario_title="Thanh toán đúng tổng tiền",
        tag="pairwise",
    )
    for k, v in overrides.items():
        setattr(args, k, v)
    return args


# --------------------------------------------------------------------------- đọc xlsx


def test_factor_columns_bo_qua_stt(xlsx_to_feature):
    assert xlsx_to_feature.factor_columns(HEADER) == ["Drink", "Size"]


def test_factor_columns_bao_loi_khi_thieu_cot_bat_buoc(xlsx_to_feature):
    with pytest.raises(xlsx_to_feature.XlsxToFeatureError) as exc:
        xlsx_to_feature.factor_columns(["A", "B", "C"])
    assert "MatrixID" in str(exc.value)


def test_read_rows(xlsx_to_feature, tmp_path):
    path = _sample_xlsx(tmp_path)
    header, rows = xlsx_to_feature.read_rows(path)
    assert header == HEADER
    assert len(rows) == 3
    assert rows[0]["MatrixID"] == "TC-AAA111"


# --------------------------------------------------------------------------- escape


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("a|b", r"a\|b"),
        ("dòng1\ndòng2", "dòng1 dòng2"),
        ("  trim  ", "trim"),
        (None, ""),
        (5, "5"),
    ],
)
def test_escape_cell(xlsx_to_feature, raw, expected):
    """Ô chứa '|' hoặc xuống dòng sẽ làm vỡ bảng Examples nếu không escape."""
    assert xlsx_to_feature.escape_cell(raw) == expected


def test_examples_table_khong_vo_khi_gia_tri_co_pipe(xlsx_to_feature):
    rows = [{"MatrixID": "TC-1", "Drink": "a|b"}]
    lines = xlsx_to_feature.build_examples_table(["Drink"], rows)
    data_line = lines[-1]
    # escape rồi thì mỗi dòng chỉ còn đúng 3 dấu '|' không bị escape (2 biên + 1 ngăn cột)
    unescaped = data_line.replace(r"\|", "")
    assert unescaped.count("|") == 3


# --------------------------------------------------------------------------- build feature


def test_build_feature_day_du_cac_phan(xlsx_to_feature, tmp_path):
    path = _sample_xlsx(tmp_path)
    header, rows = xlsx_to_feature.read_rows(path)
    factors = xlsx_to_feature.factor_columns(header)
    pairwise = [r for r in rows if r["Loai"] == "Pairwise"]
    boundary = [r for r in rows if r["Loai"] == "Boundary"]

    lines, outline_steps, examples = xlsx_to_feature.build_feature(
        _args(tmp_path), factors, pairwise, boundary
    )
    text = "\n".join(lines)

    assert "Feature: Demo feature" in text
    assert "Given khách mở trang menu" in text
    assert "Scenario Outline: [<MatrixID>] Thanh toán đúng tổng tiền" in text
    assert 'When khách chọn đồ uống "<Drink>"' in text
    assert "Then tổng tiền đúng" in text
    assert "| MatrixID | Drink | Size |" in text
    assert "| TC-AAA111 | TraDao | S |" in text
    # case biên: giữ MatrixID ổn định + có TODO cho người viết tiếp
    assert "Scenario: [BC-CCC333] Số lượng = 0" in text
    assert "# TODO" in text
    assert "Kỳ vọng: Báo lỗi" in text
    assert len(examples) == 1 + 1 + len(pairwise)  # "Examples:" + header + data


def test_build_feature_canh_bao_khi_thieu_ket_qua_mong_doi(xlsx_to_feature, tmp_path):
    path = _make_xlsx(
        tmp_path / "tc2.xlsx",
        [
            [1, "TC-AAA111", "TraDao", "S", "Pairwise", "When x", "", ""],
            [2, "BC-DDD444", "", "", "Boundary", "Case chưa có kỳ vọng", "", ""],
        ],
    )
    header, rows = xlsx_to_feature.read_rows(path)
    lines, _, _ = xlsx_to_feature.build_feature(
        _args(tmp_path),
        xlsx_to_feature.factor_columns(header),
        [r for r in rows if r["Loai"] == "Pairwise"],
        [r for r in rows if r["Loai"] == "Boundary"],
    )
    assert "[cảnh báo] Chưa có 'Kết quả mong đợi'" in "\n".join(lines)


# --------------------------------------------------------------------------- check mode


def _generated_feature(xlsx_to_feature, tmp_path):
    path = _sample_xlsx(tmp_path)
    header, rows = xlsx_to_feature.read_rows(path)
    return xlsx_to_feature.build_feature(
        _args(tmp_path),
        xlsx_to_feature.factor_columns(header),
        [r for r in rows if r["Loai"] == "Pairwise"],
        [r for r in rows if r["Loai"] == "Boundary"],
    )


def test_check_pass_khi_feature_dong_bo(xlsx_to_feature, tmp_path):
    lines, outline_steps, examples = _generated_feature(xlsx_to_feature, tmp_path)
    feature_file = tmp_path / "checkout.feature"
    feature_file.write_text("\n".join(lines), encoding="utf-8")
    assert xlsx_to_feature.check_feature(feature_file, outline_steps, examples) == 0


def test_check_fail_khi_examples_bi_sua_tay(xlsx_to_feature, tmp_path, capsys):
    lines, outline_steps, examples = _generated_feature(xlsx_to_feature, tmp_path)
    tampered = "\n".join(lines).replace("| TC-AAA111 | TraDao | S |", "| TC-AAA111 | TraDao | M |")
    feature_file = tmp_path / "checkout.feature"
    feature_file.write_text(tampered, encoding="utf-8")

    assert xlsx_to_feature.check_feature(feature_file, outline_steps, examples) == 1
    assert "KHÔNG đồng bộ" in capsys.readouterr().err


def test_check_fail_khi_thieu_step(xlsx_to_feature, tmp_path, capsys):
    lines, outline_steps, examples = _generated_feature(xlsx_to_feature, tmp_path)
    tampered = "\n".join(line for line in lines if "Then tổng tiền đúng" not in line)
    feature_file = tmp_path / "checkout.feature"
    feature_file.write_text(tampered, encoding="utf-8")

    assert xlsx_to_feature.check_feature(feature_file, outline_steps, examples) == 1
    assert "Thiếu step" in capsys.readouterr().err


def test_check_bao_thieu_file(xlsx_to_feature, tmp_path, capsys):
    _, outline_steps, examples = _generated_feature(xlsx_to_feature, tmp_path)
    assert xlsx_to_feature.check_feature(tmp_path / "khong-co.feature", outline_steps, examples) == 1
    assert "THIẾU FILE" in capsys.readouterr().err
