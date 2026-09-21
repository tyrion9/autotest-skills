# Đáp án bộ lỗi cố ý (seeded bugs)

> ⛔ **Đừng đọc file này — và đừng để skill đọc thư mục `bugs/`** — trước khi
> đã sinh xong bộ test. Đây là đáp án; đọc trước là tự làm hỏng phép thử.
>
> Khi chạy `autotest-gen-test`, hãy chỉ rõ nguồn requirement là
> `examples/shop-order/README.md` (mục "Quy tắc nghiệp vụ") — **README luôn mô
> tả hành vi ĐÚNG**, kể cả khi code đang bị chèn lỗi.

## Cách dùng

```bash
python bugs/bugs.py status       # lỗi nào đang bật
python bugs/bugs.py apply        # bật tất cả
python bugs/bugs.py apply --only 1,4
python bugs/bugs.py revert       # gỡ sạch
```

Quy trình đánh giá bộ test:

1. `revert` → app đúng → chạy bộ test → **phải PASS hết**.
2. `apply --only <n>` → chạy lại → bộ test **phải có ít nhất 1 case FAIL**.
   Nếu vẫn xanh: bộ test không đủ "răng" ở vùng đó — thường là do oracle đang
   lấy kỳ vọng từ chính code app, hoặc thiếu case biên.
3. `revert` trước khi commit.

## Danh sách lỗi

| # | File | Lỗi | Cách lộ ra | Loại test cần có để bắt |
|---|---|---|---|---|
| 1 | `app/pricing.py` | Freeship dùng `>` thay vì `>=` | Giỏ đúng **500.000** (bình giữ nhiệt 250.000 × 2) vẫn bị tính phí ship | Case **biên** đúng tại mốc freeship. Test chỉ chạy 490k/510k sẽ không bắt được |
| 2 | `app/pricing.py` | Phụ phí cồng kềnh tính 1 lần, không nhân theo số dòng | Giỏ có **2 dòng cồng kềnh** (nồi chiên + bộ nồi): ship 20.000 thay vì 40.000 | Test giỏ **nhiều dòng**, ít nhất 2 dòng `bulky`. Giỏ 1 sản phẩm không bao giờ bắt được |
| 3 | `app/pricing.py` | Phí COD tính cho cả đơn **chuyển khoản** | Đơn nhỏ trả bằng chuyển khoản vẫn bị +10.000 | Pairwise có tổ hợp (PaymentMethod=bank_transfer × subtotal nhỏ) |
| 4 | `app/app.py` | Regex SĐT bỏ ràng buộc bắt đầu bằng `0` | SĐT `1912345678` được chấp nhận, đơn tạo thành công | Case **negative** cho SĐT sai định dạng (không chỉ test chuỗi quá ngắn) |
| 5 | `app/cart.py` | Thêm trùng sản phẩm không kiểm lại tồn kho | Nồi chiên còn 8: thêm 5 rồi thêm 5 nữa → giỏ có 10 | Test **thao tác lặp** trên giỏ, không chỉ thêm 1 lần |
| 6 | `app/app.py` | `item_count` lưu số **dòng** thay vì tổng số lượng | Giỏ 2 dòng tổng 5 món → trang xác nhận hiện "Tổng số lượng 2" | Assert `order-item-count` khớp tổng số lượng đã đặt |

## Ghi chú thiết kế

- Cả 6 lỗi đều **không làm app crash** — app vẫn chạy, chỉ trả kết quả sai.
  Đúng kiểu bug lọt qua smoke test.
- Lỗi 1–3 nằm trong công thức tính tiền: nếu bộ test sinh ra `import pricing`
  của app để lấy kỳ vọng thì **cả 3 sẽ không bị bắt** — đây chính là quy tắc
  "oracle độc lập với code app" trong skill `autotest-gen-test`.
- Lỗi 2 và 5 chỉ lộ khi test dùng **giỏ nhiều dòng / nhiều bước**; bộ test chỉ
  đi đường thẳng "1 sản phẩm → đặt hàng" sẽ bỏ sót.
- Lỗi 1 chỉ lộ **đúng tại biên**; đây là phép thử cho mục "Case biên" của
  `factor.md`.
