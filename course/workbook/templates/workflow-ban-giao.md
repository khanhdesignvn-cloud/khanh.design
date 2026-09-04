# Template — Sơ đồ workflow và Checklist bàn giao

> **An toàn dữ liệu:** Chỉ dùng dữ liệu giả hoặc dữ liệu đã được phép và đã ẩn danh. Không điền mật khẩu, token, mã xác thực, khóa API, link có quyền riêng, thông tin thanh toán hoặc dữ liệu khách hàng thật. Khi chưa chắc quyền sử dụng, hãy để trống và hỏi người phụ trách dữ liệu.

## Sơ đồ workflow

Trigger: __________ → Kiểm tra đầu vào: __________ → Xử lý AI: __________ → **WAITING_APPROVAL** → Người duyệt: __________ → Đầu ra: __________.

Nhánh lỗi: __________ → ghi log tối thiểu __________ → thông báo __________ → thử lại tối đa ____ lần. Khóa chống chạy trùng: __________. ID công việc: __________.

## Bảng trạng thái

| Trạng thái | Điều kiện vào | Hành động cho phép | Điều kiện ra | Người chịu trách nhiệm |
|---|---|---|---|---|
| NEW |  | Kiểm tra |  |  |
| PROCESSING |  | Tạo nháp |  |  |
| WAITING_APPROVAL |  | Duyệt/từ chối |  |  |
| DONE |  | Không chạy lại |  |  |
| ERROR |  | Điều tra an toàn |  |  |

## Test bắt buộc

[ ] Ca chuẩn tạo đúng một bản nháp.  
[ ] Thiếu trường thì dừng và báo rõ.  
[ ] Cùng request_id không tạo bản thứ hai.  
[ ] AI lỗi thì không gửi nội dung rỗng/sai.  
[ ] Chưa có approved_by thì không chuyển READY.  
[ ] Log không chứa bí mật hoặc dữ liệu đầy đủ không cần thiết.

## Checklist bàn giao

[ ] Chủ sở hữu kinh doanh và kỹ thuật.  
[ ] Danh sách quyền tối thiểu, ngày rà soát và cách thu hồi.  
[ ] Nơi lưu prompt/template cùng phiên bản.  
[ ] Dashboard/log và người nhận cảnh báo.  
[ ] Runbook tắt, khởi động lại và xử lý lỗi.  
[ ] Sao lưu, khôi phục và thời hạn lưu dữ liệu.  
[ ] Danh sách giới hạn, hành động cấm và bước người duyệt.  
[ ] Ba bằng chứng chạy thử và ngày tái kiểm tra.

Người bàn giao: ____ Người nhận: ____ Ngày: ____ Phiên bản: ____ Vấn đề còn mở: ____________________.
