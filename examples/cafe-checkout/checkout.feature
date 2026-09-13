Feature: Chọn đồ uống và thanh toán tại quán cà phê
  Là khách hàng, tôi muốn chọn đồ uống, tuỳ chỉnh (size/đường/đá/topping),
  số lượng và phương thức thanh toán để xem tổng tiền cần thanh toán chính xác.

  # Khối Scenario Outline + Examples bên dưới do xlsx_to_feature.py sinh từ
  # testcase-pairwise.xlsx — KHÔNG sửa tay (CI có bước --check sẽ bắt lỗi lệch).
  # MatrixID (TC-xxxxxx) ổn định theo nội dung dòng: thêm/bớt testcase khác
  # không làm đổi ID của các dòng còn lại.

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
      | TC-DBB3BE | TraDao | S | 100 | 30 | Thach | 5 | Cash |
      | TC-19617E | MatchaLatte | M | 30 | 0 | TranChau | 20 | EWallet |
      | TC-93F169 | TraDao | L | 30 | 100 | None | 1 | Card |
      | TC-F948DA | CaPheSua | S | 30 | 50 | TranChau | 2 | Cash |
      | TC-023DD2 | BacXiu | M | 100 | 0 | None | 2 | Card |
      | TC-9F3D75 | BacXiu | S | 50 | 0 | Thach | 1 | EWallet |
      | TC-C50F33 | BacXiu | L | 0 | 0 | None | 20 | Cash |
      | TC-A2A2EE | BacXiu | L | 70 | 0 | TranChau | 5 | Card |
      | TC-7A8312 | TraDao | M | 70 | 100 | Thach | 2 | EWallet |
      | TC-069421 | CaPheDen | L | 100 | 50 | None | 20 | EWallet |
      | TC-51857F | CaPheDen | M | 70 | 30 | TranChau | 1 | Cash |
      | TC-937E6B | CaPheSua | S | 70 | 50 | Thach | 20 | Card |
      | TC-7BCD80 | MatchaLatte | S | 0 | 30 | None | 5 | Card |
      | TC-705C64 | MatchaLatte | L | 100 | 100 | Thach | 1 | Cash |
      | TC-551083 | MatchaLatte | M | 70 | 50 | None | 5 | EWallet |
      | TC-1E1936 | TraDao | L | 0 | 100 | TranChau | 2 | EWallet |
      | TC-9B888D | BacXiu | L | 30 | 0 | Thach | 5 | EWallet |
      | TC-1A5F4E | MatchaLatte | L | 50 | 30 | TranChau | 2 | Card |
      | TC-976DF2 | TraDao | M | 50 | 50 | None | 1 | Cash |
      | TC-03DF7F | CaPheSua | M | 0 | 0 | None | 1 | EWallet |
      | TC-FA8F48 | TraDao | M | 50 | 0 | Thach | 20 | Cash |
      | TC-22FE3B | CaPheDen | S | 50 | 100 | Thach | 5 | Card |
      | TC-F9B181 | CaPheDen | M | 0 | 50 | Thach | 2 | EWallet |
      | TC-4AEF08 | CaPheSua | L | 100 | 100 | TranChau | 5 | Cash |
      | TC-FCF54B | CaPheDen | L | 30 | 0 | Thach | 2 | Cash |
      | TC-477219 | CaPheSua | M | 50 | 100 | TranChau | 20 | Cash |
      | TC-86CA9E | CaPheSua | S | 30 | 30 | Thach | 20 | EWallet |

  Rule: Kiểm tra dữ liệu biên / không hợp lệ (từ factor.md mục 4, KHÔNG thuộc bảng pairwise)

    Scenario: [BC-ED1511] Số lượng = 0 không được thêm vào giỏ
      When khách chọn đồ uống "CaPheDen"
      And khách chọn size "S", đường "50", đá "50", topping "None"
      And khách nhập số lượng 0 và thêm vào giỏ hàng
      Then hệ thống báo lỗi số lượng không hợp lệ và không thêm vào giỏ

    Scenario: [BC-9EAB4A] Không thể thanh toán khi giỏ hàng trống
      When khách chọn phương thức thanh toán "Cash"
      And khách nhấn nút thanh toán
      Then hệ thống báo lỗi giỏ hàng trống và không tạo đơn hàng
