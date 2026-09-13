"""App demo "Shop đặt hàng online" — Flask + SQLite.

Luồng chính:
  1. Xem hàng hoá, lọc theo category              -> GET  /
  2. Xem chi tiết sản phẩm, thêm vào giỏ           -> GET  /product/<id>, POST /cart/add
  3. Quản lý giỏ hàng (sửa số lượng/xoá/xoá hết)   -> GET  /cart, POST /cart/update|remove|clear
  4. Màn hình đặt hàng: chi tiết hàng + liên hệ    -> GET  /checkout
  5. Đặt hàng: validate, tính tiền, lưu DB         -> POST /order, GET /order/<code>

Mọi phần tử UI cần thao tác đều có `data-testid` ổn định, và mọi số tiền hiển
thị đều kèm `data-value` (giá trị số nguyên thô) để test không phải parse
chuỗi đã format.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

import cart as shop_cart
import db as shop_db
import pricing

app = Flask(__name__)
# App demo chạy cục bộ — khoá cố định để session giỏ hàng không mất khi reload.
app.secret_key = "shop-order-demo-secret-key"

PHONE_RE = re.compile(r"^0\d{9}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

MAX_NAME_LEN = 80
MIN_NAME_LEN = 2
MIN_ADDRESS_LEN = 5
MAX_NOTE_LEN = 200


@app.template_filter("vnd")
def format_vnd(value: int) -> str:
    """123456 -> '123.456 ₫' (chỉ để hiển thị; test nên đọc data-value)."""
    return f"{int(value):,}".replace(",", ".") + " ₫"


@app.context_processor
def inject_cart_count():
    """Badge số lượng trên header của mọi trang."""
    return {"cart_count": shop_cart.item_count()}


def new_order_code() -> str:
    return "DH" + uuid.uuid4().hex[:6].upper()


def form_int(field: str) -> int:
    try:
        return int(request.form.get(field, ""))
    except ValueError:
        abort(400, f"{field} không hợp lệ")


def render_product(product, errors: dict, status: int = 200):
    return render_template("product.html", product=product, errors=errors, form=request.form), status


def render_cart(errors: dict, status: int = 200):
    lines = shop_cart.build_lines()
    return render_template(
        "cart.html",
        lines=lines,
        subtotal=pricing.calc_subtotal(lines),
        errors=errors,
        max_lines=shop_cart.MAX_CART_LINES,
    ), status


def validate_contact_form(form) -> tuple[dict, dict]:
    """Trả về (dữ liệu đã làm sạch, lỗi theo từng field).

    Mọi field đều được kiểm tra để người dùng thấy hết lỗi trong 1 lần submit
    (không dừng ở lỗi đầu tiên).
    """
    data = {
        "customer_name": form.get("customer_name", "").strip(),
        "phone": form.get("phone", "").strip(),
        "email": form.get("email", "").strip(),
        "address": form.get("address", "").strip(),
        "region": form.get("region", "").strip(),
        "payment_method": form.get("payment_method", "").strip(),
        "note": form.get("note", "").strip(),
    }
    errors: dict[str, str] = {}

    if not data["customer_name"]:
        errors["customer_name"] = "Vui lòng nhập họ tên người nhận."
    elif len(data["customer_name"]) < MIN_NAME_LEN:
        errors["customer_name"] = f"Họ tên phải có ít nhất {MIN_NAME_LEN} ký tự."
    elif len(data["customer_name"]) > MAX_NAME_LEN:
        errors["customer_name"] = f"Họ tên không được quá {MAX_NAME_LEN} ký tự."

    if not data["phone"]:
        errors["phone"] = "Vui lòng nhập số điện thoại."
    elif not PHONE_RE.match(data["phone"]):
        errors["phone"] = "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0."

    # Email không bắt buộc, nhưng đã nhập thì phải đúng định dạng.
    if data["email"] and not EMAIL_RE.match(data["email"]):
        errors["email"] = "Email không đúng định dạng."

    if not data["address"]:
        errors["address"] = "Vui lòng nhập địa chỉ nhận hàng."
    elif len(data["address"]) < MIN_ADDRESS_LEN:
        errors["address"] = f"Địa chỉ phải có ít nhất {MIN_ADDRESS_LEN} ký tự."

    if data["region"] not in pricing.REGIONS:
        errors["region"] = "Vui lòng chọn khu vực giao hàng."

    if data["payment_method"] not in pricing.PAYMENT_METHODS:
        errors["payment_method"] = "Vui lòng chọn phương thức thanh toán."

    if len(data["note"]) > MAX_NOTE_LEN:
        errors["note"] = f"Ghi chú không được quá {MAX_NOTE_LEN} ký tự."

    return data, errors


# --------------------------------------------------------------------- catalog


@app.route("/")
def index():
    selected = request.args.get("category") or None
    categories = shop_db.list_categories()
    if selected and selected not in {row["slug"] for row in categories}:
        abort(404)
    return render_template(
        "index.html",
        categories=categories,
        products=shop_db.list_products(selected),
        selected_category=selected,
    )


@app.route("/product/<int:product_id>")
def product_detail(product_id: int):
    product = shop_db.get_product(product_id)
    if product is None:
        abort(404)
    return render_template("product.html", product=product, form={}, errors={})


# ------------------------------------------------------------------------ cart


@app.route("/cart")
def cart_view():
    return render_cart(errors={})


@app.route("/cart/add", methods=["POST"])
def cart_add():
    product = shop_db.get_product(form_int("product_id"))
    if product is None:
        abort(404)

    quantity, error = shop_cart.parse_quantity(request.form.get("quantity", ""))
    if error:
        return render_product(product, {"quantity": error}, status=400)

    error = shop_cart.add(product["id"], quantity)
    if error:
        return render_product(product, {"quantity": error}, status=400)

    flash(f"Đã thêm “{product['name']}” vào giỏ hàng.")
    return redirect(url_for("cart_view"))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    product_id = form_int("product_id")
    quantity, error = shop_cart.parse_quantity(request.form.get("quantity", ""))
    if error is None:
        error = shop_cart.set_quantity(product_id, quantity)
    if error:
        return render_cart({f"quantity-{product_id}": error}, status=400)

    flash("Đã cập nhật số lượng.")
    return redirect(url_for("cart_view"))


@app.route("/cart/remove", methods=["POST"])
def cart_remove():
    shop_cart.remove(form_int("product_id"))
    flash("Đã xoá sản phẩm khỏi giỏ hàng.")
    return redirect(url_for("cart_view"))


@app.route("/cart/clear", methods=["POST"])
def cart_clear():
    shop_cart.clear()
    flash("Đã xoá toàn bộ giỏ hàng.")
    return redirect(url_for("cart_view"))


# -------------------------------------------------------------------- checkout


@app.route("/checkout")
def checkout():
    lines = shop_cart.build_lines()
    if not lines:
        flash("Giỏ hàng đang trống, chưa thể đặt hàng.")
        return redirect(url_for("cart_view"))
    return render_template(
        "checkout.html",
        lines=lines,
        subtotal=pricing.calc_subtotal(lines),
        regions=pricing.REGIONS,
        payment_methods=pricing.PAYMENT_METHODS,
        form={},
        errors={},
    )


@app.route("/order", methods=["POST"])
def create_order():
    lines = shop_cart.build_lines()
    if not lines:
        flash("Giỏ hàng đang trống, chưa thể đặt hàng.")
        return redirect(url_for("cart_view"))

    data, errors = validate_contact_form(request.form)

    # Kiểm tra lại tồn kho ngay trước khi ghi đơn (kho có thể đã đổi).
    stock_errors = shop_cart.check_lines_against_stock(lines)
    if stock_errors:
        errors["cart"] = " ".join(stock_errors)

    if errors:
        return render_template(
            "checkout.html",
            lines=lines,
            subtotal=pricing.calc_subtotal(lines),
            regions=pricing.REGIONS,
            payment_methods=pricing.PAYMENT_METHODS,
            form=request.form,
            errors=errors,
        ), 400

    money = pricing.calc_order(lines, region=data["region"], payment_method=data["payment_method"])
    code = new_order_code()
    shop_db.insert_order(
        {
            "code": code,
            "item_count": sum(line["quantity"] for line in lines),
            "subtotal": money["subtotal"],
            "shipping_fee": money["shipping_fee"],
            "cod_fee": money["cod_fee"],
            "total": money["total"],
            "customer_name": data["customer_name"],
            "phone": data["phone"],
            "email": data["email"],
            "address": data["address"],
            "region": data["region"],
            "payment_method": data["payment_method"],
            "note": data["note"],
            "created_at": datetime.now().isoformat(timespec="seconds"),
        },
        [
            {
                "product_id": line["product_id"],
                "product_name": line["name"],
                "unit_price": line["unit_price"],
                "bulky": int(line["bulky"]),
                "quantity": line["quantity"],
                "line_total": line["line_total"],
            }
            for line in lines
        ],
    )
    shop_cart.clear()
    return redirect(url_for("order_detail", code=code))


@app.route("/order/<code>")
def order_detail(code: str):
    order = shop_db.get_order_by_code(code)
    if order is None:
        abort(404)
    return render_template(
        "order.html",
        order=order,
        items=shop_db.get_order_items(order["id"]),
        region_label=pricing.REGIONS[order["region"]],
        payment_label=pricing.PAYMENT_METHODS[order["payment_method"]],
    )


# ------------------------------------------------------------------------- api


@app.route("/api/cart")
def api_cart():
    """Giỏ hàng hiện tại dưới dạng JSON — tiện kiểm tra state của session."""
    lines = shop_cart.build_lines()
    return jsonify(
        {
            "lines": lines,
            "item_count": shop_cart.item_count(),
            "subtotal": pricing.calc_subtotal(lines),
        }
    )


@app.route("/api/orders/<code>")
def api_order(code: str):
    """Đọc lại đơn dưới dạng JSON — tiện kiểm tra dữ liệu đã lưu."""
    order = shop_db.get_order_by_code(code)
    if order is None:
        return jsonify({"error": "not found"}), 404
    payload = dict(order)
    payload["items"] = [dict(item) for item in shop_db.get_order_items(order["id"])]
    return jsonify(payload)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
