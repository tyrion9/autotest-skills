"""Công thức tính tiền của đơn hàng — toàn bộ business rule về giá nằm ở đây.

⚠️ LƯU Ý CHO NGƯỜI VIẾT TEST: KHÔNG import module này để lấy giá trị kỳ vọng.
Oracle phải độc lập với code app — đọc dữ liệu thô (giá, cờ `bulky`) từ DB rồi
TỰ VIẾT LẠI công thức bên phía test. Dùng chính hàm này làm kỳ vọng thì app
tính sai kiểu gì test cũng pass. Xem skill `autotest-gen-test`.

Công thức (giỏ hàng có thể có nhiều dòng hàng):
    subtotal     = tổng (đơn giá × số lượng) của mọi dòng
    shipping_fee = phí cơ bản theo khu vực (miễn nếu subtotal >= 500.000)
                   + 20.000 × SỐ DÒNG hàng cồng kềnh (không được miễn)
    cod_fee      = 10.000 nếu thanh toán COD và subtotal < 200.000
    total        = subtotal + shipping_fee + cod_fee
"""

from __future__ import annotations

# Phí vận chuyển cơ bản theo khu vực giao hàng (VND).
SHIPPING_FEE_BY_REGION = {
    "noi_thanh": 15_000,
    "ngoai_thanh": 30_000,
}

# Phụ phí hàng cồng kềnh, tính theo TỪNG DÒNG hàng cồng kềnh trong giỏ
# (mua 2 loại hàng cồng kềnh -> 40.000). KHÔNG nằm trong diện miễn phí ship.
BULKY_SURCHARGE = 20_000

# Từ mốc này trở lên được miễn phí ship cơ bản.
FREESHIP_THRESHOLD = 500_000

# Phí thu hộ khi chọn COD cho đơn giá trị nhỏ.
COD_FEE = 10_000
COD_FEE_THRESHOLD = 200_000

REGIONS = {
    "noi_thanh": "Nội thành (Hà Nội / TP.HCM)",
    "ngoai_thanh": "Tỉnh thành khác",
}

PAYMENT_METHODS = {
    "cod": "Thanh toán khi nhận hàng (COD)",
    "bank_transfer": "Chuyển khoản ngân hàng",
}


def calc_subtotal(lines) -> int:
    """lines: iterable các dict có `unit_price` và `quantity`."""
    return sum(int(line["unit_price"]) * int(line["quantity"]) for line in lines)


def calc_order(lines, region: str, payment_method: str) -> dict[str, int]:
    """Trả về chi tiết tiền của 1 đơn hàng. Mọi giá trị là số nguyên VND.

    lines: iterable các dict có `unit_price`, `quantity`, `bulky`.
    """
    lines = list(lines)
    subtotal = calc_subtotal(lines)

    base_shipping = SHIPPING_FEE_BY_REGION[region]
    if subtotal >= FREESHIP_THRESHOLD:
        base_shipping = 0
    bulky_lines = sum(1 for line in lines if line["bulky"])
    shipping_fee = base_shipping + BULKY_SURCHARGE * bulky_lines

    cod_fee = COD_FEE if payment_method == "cod" and subtotal < COD_FEE_THRESHOLD else 0

    return {
        "subtotal": subtotal,
        "shipping_fee": shipping_fee,
        "cod_fee": cod_fee,
        "total": subtotal + shipping_fee + cod_fee,
    }
