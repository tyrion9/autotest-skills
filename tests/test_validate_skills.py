"""Unit test cho scripts/validate_skills.py — script còn lại duy nhất của repo
sau khi bỏ pict_to_xlsx.py/xlsx_to_feature.py (autotest-gen-test giờ không
còn phụ thuộc script, AI đọc trực tiếp nguồn đầu vào)."""

from __future__ import annotations

from pathlib import Path


def make_skill(skills_dir: Path, dirname: str, skill_md_text: str | None) -> Path:
    skill_dir = skills_dir / dirname
    skill_dir.mkdir(parents=True, exist_ok=True)
    if skill_md_text is not None:
        (skill_dir / "SKILL.md").write_text(skill_md_text, encoding="utf-8")
    return skill_dir


VALID_DESCRIPTION = (
    "Mô tả đủ dài để vượt ngưỡng 60 ký tự, nói rõ khi nào Claude nên dùng skill này."
)


def valid_skill_md(name: str, description: str = VALID_DESCRIPTION) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n"


# ---- parse_frontmatter -------------------------------------------------


def test_parse_frontmatter_valid(validate_skills):
    text = valid_skill_md("autotest-gen-test")
    meta = validate_skills.parse_frontmatter(text)
    assert meta == {"name": "autotest-gen-test", "description": VALID_DESCRIPTION}


def test_parse_frontmatter_missing_dashes(validate_skills):
    assert validate_skills.parse_frontmatter("# Không có frontmatter\n") is None


def test_parse_frontmatter_unterminated(validate_skills):
    assert validate_skills.parse_frontmatter("---\nname: x\n") is None


def test_parse_frontmatter_multiline_value_is_concatenated(validate_skills):
    text = "---\nname: x\ndescription: dòng một\n  dòng hai\n---\n"
    meta = validate_skills.parse_frontmatter(text)
    assert meta == {"name": "x", "description": "dòng một dòng hai"}


# ---- main() --------------------------------------------------------------


def test_main_no_skills_dir(validate_skills, tmp_path, capsys):
    validate_skills.SKILLS_DIR = tmp_path / "khong-ton-tai"
    assert validate_skills.main() == 1


def test_main_valid_skill_passes(validate_skills, tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    make_skill(skills_dir, "autotest-gen-test", valid_skill_md("autotest-gen-test"))
    validate_skills.SKILLS_DIR = skills_dir

    assert validate_skills.main() == 0
    assert "✅" in capsys.readouterr().out


def test_main_missing_skill_md(validate_skills, tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    make_skill(skills_dir, "broken-skill", None)
    validate_skills.SKILLS_DIR = skills_dir

    assert validate_skills.main() == 1
    assert "thiếu SKILL.md" in capsys.readouterr().err


def test_main_name_mismatch(validate_skills, tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    make_skill(skills_dir, "autotest-gen-test", valid_skill_md("ten-sai"))
    validate_skills.SKILLS_DIR = skills_dir

    assert validate_skills.main() == 1
    assert "không khớp tên thư mục" in capsys.readouterr().err


def test_main_description_too_short(validate_skills, tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    make_skill(skills_dir, "autotest-gen-test", valid_skill_md("autotest-gen-test", "quá ngắn"))
    validate_skills.SKILLS_DIR = skills_dir

    assert validate_skills.main() == 1
    assert "quá ngắn" in capsys.readouterr().err


def test_main_missing_description(validate_skills, tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    make_skill(skills_dir, "autotest-gen-test", "---\nname: autotest-gen-test\n---\n")
    validate_skills.SKILLS_DIR = skills_dir

    assert validate_skills.main() == 1
    assert "thiếu 'description'" in capsys.readouterr().err


def test_main_referenced_path_missing_when_top_level_dir_exists(validate_skills, tmp_path, capsys):
    skills_dir = tmp_path / "skills"
    skill_dir = make_skill(
        skills_dir,
        "autotest-gen-test",
        valid_skill_md("autotest-gen-test") + "\nDùng `scripts/xlsx_to_feature.py` để...\n",
    )
    (skill_dir / "scripts").mkdir()
    validate_skills.SKILLS_DIR = skills_dir

    assert validate_skills.main() == 1
    assert "scripts/xlsx_to_feature.py" in capsys.readouterr().err


def test_main_referenced_path_skipped_when_no_top_level_dir(validate_skills, tmp_path, capsys):
    """Đường dẫn trong backtick nói về file của PROJECT ĐANG TEST (vd
    `testing/features/...`), không phải tài nguyên của skill, khi skill không
    có thư mục top-level đó — không được báo lỗi."""
    skills_dir = tmp_path / "skills"
    make_skill(
        skills_dir,
        "autotest-gen-test",
        valid_skill_md("autotest-gen-test") + "\nGhi ra `scripts/run_tests.sh` của project.\n",
    )
    validate_skills.SKILLS_DIR = skills_dir

    assert validate_skills.main() == 0
