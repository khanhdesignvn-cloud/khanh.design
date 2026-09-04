# Template — Tiêu chí đánh giá đầu ra

> **An toàn dữ liệu:** Chỉ dùng dữ liệu giả hoặc dữ liệu đã được phép và đã ẩn danh. Không điền mật khẩu, token, mã xác thực, khóa API, link có quyền riêng, thông tin thanh toán hoặc dữ liệu khách hàng thật. Khi chưa chắc quyền sử dụng, hãy để trống và hỏi người phụ trách dữ liệu.

## Định nghĩa nhiệm vụ

Người dùng đầu ra: __________. Quyết định/hành động tiếp theo: __________. Hậu quả nếu sai: __________. Người duyệt cuối: __________.

## Rubric quan sát được

| Tiêu chí | Đạt khi | Cần sửa khi | Bằng chứng | Trọng yếu? |
|---|---|---|---|---|
| Đúng sự thật | Mọi dữ kiện truy về nguồn | Có câu không nguồn hoặc suy diễn |  | Có |
| Đúng yêu cầu | Đủ định dạng, độ dài, CTA | Thiếu phần bắt buộc |  |  |
| Đúng thương hiệu | Đạt quy tắc giọng | Dùng từ/cấu trúc bị cấm |  |  |
| An toàn | Không lộ dữ liệu, không vượt quyền | Chứa dữ liệu nhạy cảm hoặc tự quyết |  | Có |
| Dùng được | Người nhận hiểu bước tiếp | Mơ hồ, cần viết lại nhiều |  |  |

## Bộ test

- Ca chuẩn: đầu vào __________; kết quả mong đợi __________.
- Ca thiếu dữ liệu: thiếu __________; hệ thống phải hỏi/để trống __________.
- Ca mâu thuẫn: nguồn A nói __________, nguồn B nói __________; phải chuyển __________.
- Ca rủi ro: __________; phải dừng trước __________.

## Nhật ký phiên bản

| Phiên bản | Ngày | Thay đổi đầu vào/prompt | Kết quả rubric | Người duyệt |
|---|---|---|---|---|
| v1 |  |  |  |  |
| v2 |  |  |  |  |
| v3 |  |  |  |  |

## Quyết định

[ ] Đạt — có đủ bằng chứng cho mọi tiêu chí trọng yếu.  
[ ] Cần sửa — ghi đúng một thay đổi nhỏ tiếp theo: ____________________.  
[ ] Dừng/chuyển cấp — lý do: ________________________________________.
