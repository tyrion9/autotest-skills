Feature: Chọn đồ uống và thanh toán tại quán cà phê
  Là khách hàng, tôi muốn chọn đồ uống, tuỳ chỉnh (size/đường/đá/topping),
  số lượng và phương thức thanh toán để xem tổng tiền cần thanh toán chính xác.

  # Bảng Examples bên dưới được sinh từ pict-cli (thay PictMCP đã archived,
  # xem README mục "Về PictMCP") với model testing/pict/checkout.model.txt,
  # phủ pairwise (mọi cặp giá trị của 7 tham số) chỉ với 27 dòng thay vì
  # 5*3*5*4*3*4*3 = 10800 tổ hợp đầy đủ.
  # Cột MatrixID dùng để truy vết 1-1 sang reports/test_summary.md.

  Background:
    Given khách mở trang menu quán cà phê

  @pairwise
  Scenario Outline: [<MatrixID>] Thêm đồ uống theo tuỳ chọn và thanh toán ra đúng tổng tiền
    When khách chọn đồ uống "<Drink>"
    And khách chọn size "<Size>", đường "<Sugar>", đá "<Ice>", topping "<Topping>"
    And khách nhập số lượng <Quantity> và thêm vào giỏ hàng
    And khách chọn phương thức thanh toán "<PaymentMethod>"
    And khách nhấn nút thanh toán
    Then hệ thống hiển thị tổng tiền cần thanh toán đúng với công thức tính giá
    And đơn hàng được lưu vào cơ sở dữ liệu với đúng tổng tiền

    Examples:
      | MatrixID | Drink | Size | Sugar | Ice | Topping | Quantity | PaymentMethod |
      | 1 | TraDao | S | 100 | 30 | Thach | 5 | Cash |
      | 2 | MatchaLatte | M | 30 | 0 | TranChau | 20 | EWallet |
      | 3 | TraDao | L | 30 | 100 | None | 1 | Card |
      | 4 | CaPheSua | S | 30 | 50 | TranChau | 2 | Cash |
      | 5 | BacXiu | M | 100 | 0 | None | 2 | Card |
      | 6 | BacXiu | S | 50 | 0 | Thach | 1 | EWallet |
      | 7 | BacXiu | L | 0 | 0 | None | 20 | Cash |
      | 8 | BacXiu | L | 70 | 0 | TranChau | 5 | Card |
      | 9 | TraDao | M | 70 | 100 | Thach | 2 | EWallet |
      | 10 | CaPheDen | L | 100 | 50 | None | 20 | EWallet |
      | 11 | CaPheDen | M | 70 | 30 | TranChau | 1 | Cash |
      | 12 | CaPheSua | S | 70 | 50 | Thach | 20 | Card |
      | 13 | MatchaLatte | S | 0 | 30 | None | 5 | Card |
      | 14 | MatchaLatte | L | 100 | 100 | Thach | 1 | Cash |
      | 15 | MatchaLatte | M | 70 | 50 | None | 5 | EWallet |
      | 16 | TraDao | L | 0 | 100 | TranChau | 2 | EWallet |
      | 17 | BacXiu | L | 30 | 0 | Thach | 5 | EWallet |
      | 18 | MatchaLatte | L | 50 | 30 | TranChau | 2 | Card |
      | 19 | TraDao | M | 50 | 50 | None | 1 | Cash |
      | 20 | CaPheSua | M | 0 | 0 | None | 1 | EWallet |
      | 21 | TraDao | M | 50 | 0 | Thach | 20 | Cash |
      | 22 | CaPheDen | S | 50 | 100 | Thach | 5 | Card |
      | 23 | CaPheDen | M | 0 | 50 | Thach | 2 | EWallet |
      | 24 | CaPheSua | L | 100 | 100 | TranChau | 5 | Cash |
      | 25 | CaPheDen | L | 30 | 0 | Thach | 2 | Cash |
      | 26 | CaPheSua | M | 50 | 100 | TranChau | 20 | Cash |
      | 27 | CaPheSua | S | 30 | 30 | Thach | 20 | EWallet |

  Rule: Kiểm tra dữ liệu biên / không hợp lệ (viết tay, không thuộc bảng pairwise)

    Scenario: Số lượng 0 không được thêm vào giỏ hàng
      When khách chọn đồ uống "CaPheDen"
      And khách chọn size "S", đường "50", đá "50", topping "None"
      And khách nhập số lượng 0 và thêm vào giỏ hàng
      Then hệ thống báo lỗi số lượng không hợp lệ và không thêm vào giỏ

    Scenario: Không thể thanh toán khi giỏ hàng đang trống
      When khách chọn phương thức thanh toán "Cash"
      And khách nhấn nút thanh toán
      Then hệ thống báo lỗi giỏ hàng trống và không tạo đơn hàng
