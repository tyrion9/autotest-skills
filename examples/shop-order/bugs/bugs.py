#!/usr/bin/env python3
"""Chèn/gỡ các lỗi cố ý vào app demo — phục vụ mutation testing cho bộ autotest-skills.

Mục đích: sau khi dùng skill sinh ra bộ test, bật lỗi lên rồi chạy test để xem
bộ test có THẬT SỰ bắt được lỗi không. Test xanh khi app đã sai = test vô dụng.

Dùng:
    python bugs/bugs.py status            # lỗi nào đang bật
    python bugs/bugs.py apply             # bật tất cả
    python bugs/bugs.py apply --only 1,4  # chỉ bật lỗi số 1 và 4
    python bugs/bugs.py revert            # gỡ sạch, app về đúng

Mỗi lỗi là 1 phép thay chuỗi có thể đảo ngược. Script tự kiểm tra: nếu không
tìm thấy đoạn cần thay (hoặc đã ở trạng thái đích) thì báo rõ, không sửa mù.

⚠️ Đáp án (lỗi nằm ở đâu, test nào bắt được) ở `bugs/README.md` — đừng đọc
file đó, và đừng để skill đọc thư mục `bugs/`, trước khi sinh xong bộ test.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent.parent / "app"

BUGS = [
    {
        "id": 1,
        "title": "Freeship dùng > thay vì >= (sai đúng tại mốc 500.000)",
        "file": "pricing.py",
        "good": "    if subtotal >= FREESHIP_THRESHOLD:",
        "bad": "    if subtotal > FREESHIP_THRESHOLD:",
    },
    {
        "id": 2,
        "title": "Phụ phí cồng kềnh chỉ tính 1 lần, không nhân theo số dòng",
        "file": "pricing.py",
        "good": "    shipping_fee = base_shipping + BULKY_SURCHARGE * bulky_lines",
        "bad": "    shipping_fee = base_shipping + (BULKY_SURCHARGE if bulky_lines else 0)",
    },
    {
        "id": 3,
        "title": "Phí thu hộ COD bị tính cho cả đơn chuyển khoản",
        "file": "pricing.py",
        "good": '    cod_fee = COD_FEE if payment_method == "cod" and subtotal < COD_FEE_THRESHOLD else 0',
        "bad": "    cod_fee = COD_FEE if subtotal < COD_FEE_THRESHOLD else 0",
    },
    {
        "id": 4,
        "title": "Validate SĐT không bắt buộc bắt đầu bằng 0",
        "file": "app.py",
        "good": 'PHONE_RE = re.compile(r"^0\\d{9}$")',
        "bad": 'PHONE_RE = re.compile(r"^\\d{10}$")',
    },
    {
        "id": 5,
        "title": "Thêm trùng sản phẩm vào giỏ không kiểm lại tồn kho",
        "file": "cart.py",
        "good": """            new_quantity = line["quantity"] + quantity
            if new_quantity > product["stock"]:
                return (
                    f"Chỉ còn {product['stock']} sản phẩm trong kho"
                    f" (giỏ hàng đang có {line['quantity']})."
                )
            line["quantity"] = new_quantity""",
        "bad": """            new_quantity = line["quantity"] + quantity
            line["quantity"] = new_quantity""",
    },
    {
        "id": 6,
        "title": "Đơn lưu item_count = số dòng hàng thay vì tổng số lượng",
        "file": "app.py",
        "good": '            "item_count": sum(line["quantity"] for line in lines),',
        "bad": '            "item_count": len(lines),',
    },
]


def state(bug) -> str:
    text = (APP / bug["file"]).read_text(encoding="utf-8")
    if bug["bad"] in text:
        return "BẬT"
    if bug["good"] in text:
        return "tắt"
    return "?? (code đã đổi, không khớp cả 2 trạng thái)"


def switch(bug, on: bool) -> bool:
    path = APP / bug["file"]
    text = path.read_text(encoding="utf-8")
    src, dst = (bug["good"], bug["bad"]) if on else (bug["bad"], bug["good"])
    if src not in text:
        return False
    path.write_text(text.replace(src, dst, 1), encoding="utf-8")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["status", "apply", "revert"])
    ap.add_argument("--only", default="", help="Danh sách id lỗi, vd: 1,3,5")
    args = ap.parse_args()

    only = {int(x) for x in args.only.split(",") if x.strip()} if args.only else None
    targets = [b for b in BUGS if only is None or b["id"] in only]
    if only and len(targets) != len(only):
        print(f"Không có lỗi với id: {sorted(only - {b['id'] for b in targets})}", file=sys.stderr)
        return 1

    if args.command == "status":
        for bug in BUGS:
            print(f"  [{state(bug):>3}] #{bug['id']} {bug['title']}  ({bug['file']})")
        return 0

    on = args.command == "apply"
    changed = skipped = 0
    for bug in targets:
        if switch(bug, on):
            changed += 1
            print(f"  {'BẬT ' if on else 'gỡ  '} #{bug['id']} {bug['title']}")
        else:
            skipped += 1
            print(f"  bỏ qua #{bug['id']} — đã ở trạng thái đích (hoặc code đã đổi)")

    print(f"\n{'Đã bật' if on else 'Đã gỡ'} {changed} lỗi, bỏ qua {skipped}.")
    if on:
        print("Nhớ `python bugs/bugs.py revert` khi thử xong — đừng commit app đang có lỗi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
