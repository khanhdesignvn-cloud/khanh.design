# Bàn giao website quản lý dự án thiết kế

## Thông tin

- Website: https://khe-sanh-design-map.nitia-gpt-pr-6208.chatgpt.site
- Giao diện: Google Sans Flex, chế độ tối mặc định, có chuyển sáng/tối
- Chế độ xem: Sơ đồ, Sản phẩm, Showcase, Slide tổng
- Dữ liệu: Cloudflare D1; ảnh và PDF: Cloudflare R2
- Quản trị: đăng nhập nội bộ hoặc tài khoản ChatGPT được cho phép

## Chức năng chính

- Tạo, sửa, xóa và sắp xếp dự án, danh mục, sản phẩm
- Kéo thả hạng mục giữa các danh mục
- Zoom bằng con lăn chuột hoặc chụm hai ngón; kéo nền để di chuyển
- Ba trạng thái: Đang triển khai, Đợi duyệt, Hoàn thành
- Tải ảnh/PDF, xem trước tài liệu và gắn liên kết Google Drive
- Slide tổng gồm bìa, mục lục, tiến độ và báo cáo từng nhóm
- Người xem chỉ đọc; mọi API ghi dữ liệu đều kiểm tra quyền quản trị phía máy chủ

## Chạy thử

Yêu cầu Node.js 22.13 trở lên.

```bash
npm ci
npm run dev
```

## Biến môi trường khi triển khai

- `ADMIN_EMAILS`: danh sách email ChatGPT quản trị, phân cách bằng dấu phẩy
- `ADMIN_PASSWORD_HASH`: chuỗi PBKDF2 theo dạng `iterations:salt:hash`
- `ADMIN_SESSION_SECRET`: chuỗi ngẫu nhiên tối thiểu 32 ký tự để ký phiên đăng nhập

Giá trị thật không nằm trong gói bàn giao. Khi đổi mật khẩu, tạo hash PBKDF2-SHA256 mới và cập nhật biến môi trường trên nền tảng triển khai.

## Lưu trữ

Tệp `.openai/hosting.json` khai báo hai binding:

- `DB`: cơ sở dữ liệu D1
- `BUCKET`: kho ảnh và PDF R2

Các migration cơ sở dữ liệu nằm trong thư mục `drizzle/` và được áp dụng khi triển khai.

## Lưu ý bảo mật

- Không lưu mật khẩu gốc, token hoặc khóa truy cập vào Git hay file cấu hình.
- Phiên quản trị dùng cookie `HttpOnly`, `Secure`, `SameSite=Strict` và hết hạn sau 8 giờ.
- Đăng nhập sai bị giới hạn số lần thử trong 15 phút.
- Nên đổi mật khẩu bàn giao sau khi đơn vị tiếp nhận đăng nhập thành công.

## Cấu trúc quan trọng

- `app/workspace.tsx`: giao diện quản lý chính
- `app/use-map-navigation.ts`: zoom, pinch và pan
- `app/api/`: API dữ liệu, upload và đăng nhập
- `app/password-auth.ts`: xác thực mật khẩu và phiên
- `db/schema.ts`, `drizzle/`: schema và migration
- `worker/index.ts`: điểm vào Cloudflare Worker

