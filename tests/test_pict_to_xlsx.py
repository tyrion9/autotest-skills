"""Unit test cho skills/autotest-testcase-pairwise/scripts/pict_to_xlsx.py."""

from __future__ import annotations

import argparse
import shutil

import pytest

FACTOR_MD_VI = """# Factor Analysis — Demo

## 3. Constraints

| # | Điều kiện | Nguồn |
|---|---|---|
| 1 | không có | - |

## 4. Case biên / Negative

| # | Mô tả case | Input | Kết quả mong đợi | Nguồn |
|---|---|---|---|---|
| 1 | Số lượng = 0 | Quantity = 0 | Báo lỗi, không thêm vào giỏ | app.py:77 |
| 2 | Giỏ trống | Không có item | Báo lỗi giỏ trống | app.py:60 |

## 5. Câu hỏi mở
- không
"""

FACTOR_MD_EN = """# Factor Analysis

## 4. Boundary cases

| # | Description | Input | Expected | Source |
|---|---|---|---|---|
| 1 | Empty name | name="" | Validation error | api.py:12 |
"""

FACTOR_MD_BAD_HEADERS = """# Factor Analysis

## 4. Case biên

| # | Ghi chú gì đó | Cột lạ |
|---|---|---|
| 1 | abc | xyz |
"""


# --------------------------------------------------------------------------- stable_id


def test_stable_id_deterministic(pict_to_xlsx):
    a = pict_to_xlsx.stable_id("TC", "Drink=CaPheDen|Size=S", set())
    b = pict_to_xlsx.stable_id("TC", "Drink=CaPheDen|Size=S", set())
    assert a == b
    assert a.startswith("TC-") and len(a) == 9


def test_stable_id_khac_nhau_theo_noi_dung(pict_to_xlsx):
    taken: set[str] = set()
    a = pict_to_xlsx.stable_id("TC", "Drink=CaPheDen", taken)
    b = pict_to_xlsx.stable_id("TC", "Drink=TraDao", taken)
    assert a != b


def test_stable_id_xu_ly_dung_do(pict_to_xlsx):
    payload = "same-payload"
    taken: set[str] = set()
    first = pict_to_xlsx.stable_id("TC", payload, taken)
    second = pict_to_xlsx.stable_id("TC", payload, taken)  # ép đụng độ
    assert first != second
    assert len(second) > len(first)


def test_matrix_id_on_dinh_khi_them_dong_khac(pict_to_xlsx):
    """Điểm mấu chốt: thêm dòng mới KHÔNG làm đổi ID của dòng cũ."""
    rows_v1 = [{"A": "1", "B": "x"}, {"A": "2", "B": "y"}]
    rows_v2 = [{"A": "0", "B": "z"}] + rows_v1  # chèn thêm 1 dòng lên đầu

    def ids(rows):
        taken: set[str] = set()
        return [pict_to_xlsx.stable_id("TC", pict_to_xlsx.pairwise_payload(r), taken) for r in rows]

    assert ids(rows_v1) == ids(rows_v2)[1:]


# --------------------------------------------------------------------------- render_gherkin


def test_render_gherkin_thay_placeholder(pict_to_xlsx):
    out = pict_to_xlsx.render_gherkin(
        ['When khách chọn đồ uống "<Drink>"', "And số lượng <Qty>"],
        {"Drink": "TraDao", "Qty": "5"},
    )
    assert out == 'When khách chọn đồ uống "TraDao"\nAnd số lượng 5'


def test_render_gherkin_bao_loi_khi_sai_ten_factor(pict_to_xlsx):
    with pytest.raises(pict_to_xlsx.PictToXlsxError) as exc:
        pict_to_xlsx.render_gherkin(['When chọn "<Drinkk>"'], {"Drink": "TraDao"})
    assert "Drinkk" in str(exc.value)
    assert "Drink" in str(exc.value)  # có gợi ý cột đang có


def test_render_gherkin_allow_unknown_giu_nguyen(pict_to_xlsx):
    out = pict_to_xlsx.render_gherkin(
        ["Then thấy <b>đậm</b> và <Drink>"], {"Drink": "TraDao"}, allow_unknown=True
    )
    assert out == "Then thấy <b>đậm</b> và TraDao"


# --------------------------------------------------------------------------- parse_boundary_rows


def test_parse_boundary_rows_tieng_viet(pict_to_xlsx, tmp_path):
    factor = tmp_path / "f.factor.md"
    factor.write_text(FACTOR_MD_VI, encoding="utf-8")
    rows = pict_to_xlsx.parse_boundary_rows(factor)
    assert len(rows) == 2
    assert rows[0]["desc"] == "Số lượng = 0"
    assert rows[0]["input"] == "Quantity = 0"
    assert rows[0]["expected"] == "Báo lỗi, không thêm vào giỏ"


def test_parse_boundary_rows_tieng_anh(pict_to_xlsx, tmp_path):
    factor = tmp_path / "f.factor.md"
    factor.write_text(FACTOR_MD_EN, encoding="utf-8")
    rows = pict_to_xlsx.parse_boundary_rows(factor)
    assert len(rows) == 1
    assert rows[0]["desc"] == "Empty name"
    assert rows[0]["expected"] == "Validation error"


def test_parse_boundary_rows_fail_loud_khi_sai_ten_cot(pict_to_xlsx, tmp_path):
    """Hồi quy: trước đây trả rỗng âm thầm -> case biên mất mà không ai biết."""
    factor = tmp_path / "f.factor.md"
    factor.write_text(FACTOR_MD_BAD_HEADERS, encoding="utf-8")
    with pytest.raises(pict_to_xlsx.PictToXlsxError) as exc:
        pict_to_xlsx.parse_boundary_rows(factor)
    assert "cột mô tả case" in str(exc.value)


def test_parse_boundary_rows_khong_co_muc_4(pict_to_xlsx, tmp_path, capsys):
    factor = tmp_path / "f.factor.md"
    factor.write_text("# Factor\n\n## 2. Bảng Factor\n\n| a |\n|---|\n| b |\n", encoding="utf-8")
    rows = pict_to_xlsx.parse_boundary_rows(factor)
    assert rows == []
    assert "cảnh báo" in capsys.readouterr().err


# --------------------------------------------------------------------------- workbook I/O


def _fake_args(tmp_path, **overrides):
    args = argparse.Namespace(
        model=tmp_path / "m.txt",
        gherkin_template=None,
        factor=None,
        order=2,
        seed=42,
        output=tmp_path / "out.xlsx",
        allow_unknown_placeholders=False,
        check=False,
    )
    for k, v in overrides.items():
        setattr(args, k, v)
    return args


def test_write_va_doc_lai_workbook(pict_to_xlsx, tmp_path):
    header = ["STT", "MatrixID", "A", "Loai", "Gherkin", "KetQuaMongDoi", "GhiChu"]
    data = [[1, "TC-ABC123", "x", "Pairwise", "When a", "", ""]]
    meta = [["generated_at", "2026-01-01T00:00:00"], ["seed", "42"]]
    out = tmp_path / "t.xlsx"

    pict_to_xlsx.write_workbook(out, header, data, meta)
    assert out.exists()

    read_header, read_data = pict_to_xlsx.read_workbook_data(out)
    assert read_header == header
    # openpyxl đọc ô rỗng thành None -> chuẩn hoá giống check_against_existing
    norm = lambda row: ["" if c is None else str(c) for c in row]  # noqa: E731
    assert norm(read_data[0]) == norm(data[0])


def test_check_phat_hien_lech_du_lieu(pict_to_xlsx, tmp_path, capsys):
    header = ["STT", "MatrixID", "A", "Loai", "Gherkin", "KetQuaMongDoi", "GhiChu"]
    data = [[1, "TC-ABC123", "x", "Pairwise", "When a", "", ""]]
    out = tmp_path / "t.xlsx"
    pict_to_xlsx.write_workbook(out, header, data, [])

    assert pict_to_xlsx.check_against_existing(out, header, data) == 0

    changed = [[1, "TC-ABC123", "y", "Pairwise", "When a", "", ""]]
    assert pict_to_xlsx.check_against_existing(out, header, changed) == 1
    assert "KHÔNG khớp" in capsys.readouterr().err


def test_check_bao_thieu_file(pict_to_xlsx, tmp_path, capsys):
    assert pict_to_xlsx.check_against_existing(tmp_path / "chua-co.xlsx", ["A"], []) == 1
    assert "THIẾU FILE" in capsys.readouterr().err


# --------------------------------------------------------------------------- integration (cần Node/npx)


@pytest.mark.skipif(shutil.which("npx") is None, reason="Cần Node.js/npx để chạy pict-cli")
def test_integration_sinh_matrix_that(pict_to_xlsx, tmp_path):
    model = tmp_path / "m.txt"
    # Lưu ý cú pháp PICT: giá trị CHUỖI phải bọc ngoặc kép trong constraint,
    # giá trị SỐ thì không — dùng giá trị chuỗi cho rõ ràng.
    model.write_text('A: a1, a2\nB: x, y\nC: p, q\n\nIF [A] = "a1" THEN [B] = "x";\n', encoding="utf-8")
    rows = pict_to_xlsx.run_pict(model, order=2, seed=42)
    assert rows, "pict-cli phải sinh ít nhất 1 dòng"
    assert set(rows[0].keys()) == {"A", "B", "C"}
    # constraint phải được tôn trọng
    assert all(r["B"] == "x" for r in rows if r["A"] == "a1")


@pytest.mark.skipif(shutil.which("npx") is None, reason="Cần Node.js/npx để chạy pict-cli")
def test_integration_pict_loi_model_sai_cu_phap(pict_to_xlsx, tmp_path):
    model = tmp_path / "bad.txt"
    model.write_text('A: 1, 2\nIF [A] = "1" THEN [KhongTonTai] = 9;\n', encoding="utf-8")
    with pytest.raises(pict_to_xlsx.PictToXlsxError) as exc:
        pict_to_xlsx.run_pict(model, order=2, seed=42)
    assert "pict-cli lỗi" in str(exc.value)


def test_bao_loi_khi_factor_trung_ten_cot_danh_rieng(pict_to_xlsx, tmp_path, monkeypatch):
    """Factor tên 'GhiChu' trùng cột dành riêng -> phải DỪNG, không ghi file hỏng.

    Nếu để lọt, header xlsx có 2 cột 'GhiChu' và xlsx_to_feature.py đọc theo tên
    cột sẽ lấy nhầm cột rỗng -> Examples mất sạch giá trị factor mà không báo gì.
    """
    monkeypatch.setattr(
        pict_to_xlsx,
        "run_pict",
        lambda model, order, seed: [{"Region": "noi_thanh", "GhiChu": "co"}],
    )
    args = argparse.Namespace(
        model=tmp_path / "model.txt",
        gherkin_template=None,
        factor=None,
        order=2,
        seed=42,
        allow_unknown_placeholders=False,
    )
    with pytest.raises(pict_to_xlsx.PictToXlsxError) as err:
        pict_to_xlsx.build_rows(args)
    assert "GhiChu" in str(err.value)
    assert "CoGhiChu" in str(err.value)  # có gợi ý cách sửa
