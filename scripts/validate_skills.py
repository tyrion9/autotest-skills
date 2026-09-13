#!/usr/bin/env python3
"""Kiểm tra mọi SKILL.md trong skills/ có frontmatter hợp lệ.

Chạy: python scripts/validate_skills.py
Exit 0 nếu tất cả hợp lệ, 1 nếu có lỗi (dùng trong CI).

Quy tắc (theo yêu cầu của Claude Code Skill):
- Có frontmatter YAML mở/đóng bằng '---'
- Có 'name' khớp CHÍNH XÁC tên thư mục (nếu lệch, skill sẽ không được nhận đúng)
- Có 'description' đủ dài để Claude quyết định khi nào dùng skill
- Mọi file/thư mục được SKILL.md nhắc tới theo đường dẫn tương đối phải tồn tại
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
MIN_DESCRIPTION_LEN = 60

# Đường dẫn tương đối tới file đi kèm mà SKILL.md hay trích dẫn trong backtick
REFERENCED_PATH_RE = re.compile(r"`((?:references|scripts|assets)/[A-Za-z0-9_./-]+)`")


def parse_frontmatter(text: str) -> dict[str, str] | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end].strip("\n")
    data: dict[str, str] = {}
    current_key: str | None = None
    for line in block.splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            current_key = match.group(1)
            data[current_key] = match.group(2).strip()
        elif current_key and line.strip():
            data[current_key] += " " + line.strip()
    return data


def main() -> int:
    if not SKILLS_DIR.is_dir():
        print(f"Không tìm thấy thư mục {SKILLS_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    checked = 0

    for skill_dir in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{skill_dir.name}: thiếu SKILL.md")
            continue

        checked += 1
        text = skill_md.read_text(encoding="utf-8")
        meta = parse_frontmatter(text)

        if meta is None:
            errors.append(f"{skill_dir.name}: SKILL.md thiếu frontmatter '---'")
            continue

        name = meta.get("name", "")
        if not name:
            errors.append(f"{skill_dir.name}: frontmatter thiếu 'name'")
        elif name != skill_dir.name:
            errors.append(
                f"{skill_dir.name}: 'name: {name}' không khớp tên thư mục -> Claude sẽ nạp sai skill"
            )

        description = meta.get("description", "")
        if not description:
            errors.append(f"{skill_dir.name}: frontmatter thiếu 'description'")
        elif len(description) < MIN_DESCRIPTION_LEN:
            errors.append(
                f"{skill_dir.name}: description quá ngắn ({len(description)} ký tự) — "
                "cần mô tả rõ KHI NÀO dùng skill để Claude trigger đúng"
            )

        for rel in REFERENCED_PATH_RE.findall(text):
            # Chỉ kiểm tra khi skill THỰC SỰ có thư mục đó — nếu không, đường dẫn
            # trong backtick đang nói về file của PROJECT ĐANG TEST, không phải
            # tài nguyên của skill (vd `scripts/run_tests.sh` của project).
            top_level = skill_dir / rel.split("/", 1)[0]
            if not top_level.is_dir():
                continue
            if not (skill_dir / rel).exists():
                errors.append(f"{skill_dir.name}: SKILL.md trích dẫn `{rel}` nhưng file không tồn tại")

    if errors:
        print(f"❌ {len(errors)} lỗi trong {checked} skill:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print(f"✅ {checked} skill hợp lệ (frontmatter + file tham chiếu đầy đủ).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
