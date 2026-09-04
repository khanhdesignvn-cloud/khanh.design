# Thiết kế cổng học viên và quản lý bài tập khóa AI

Ngày: 04/09/2026  
Trạng thái: Đã được cậu chủ duyệt triển khai trong hội thoại

## Phạm vi bản đầu

Cohort tối đa 15 học viên, sáu tuần. Mỗi tuần tạo một sản phẩm nối tiếp thành bài tốt nghiệp. Hệ thống không thay thế LMS, không lưu video, không xử lý thanh toán và không tự chấm chất lượng đầu ra.

## Kiến trúc

- GitHub Pages phục vụ hai giao diện tĩnh:
  - `/hoc-vien/`: đăng nhập, xem sáu tuần, nộp bài, xem lịch sử và phản hồi.
  - `/quan-ly/`: dashboard riêng của giảng viên, lọc tiến độ và chấm bài.
- API Python hiện có trên `127.0.0.1:8092`, công khai qua đúng Cloudflare tunnel hiện tại.
- Dữ liệu riêng nằm trong `/var/lib/khanh-course/`, quyền `0700/0600`; không commit GitHub.
- CORS chỉ cho ba origin đã duyệt. Mọi mutation dùng JSON, body limit, validation, rate limit và ghi file nguyên tử.

## Xác thực

- Học viên đăng nhập bằng `application_id` đã nhận khi đăng ký và số điện thoại đã nộp.
- Chỉ hồ sơ có tên trong registry kích hoạt mới đăng nhập được. Registry chỉ lưu tên hiển thị và hash số điện thoại có salt; không sao chép số điện thoại dạng rõ.
- Đăng nhập thành công trả session token HMAC có hạn dùng 12 giờ. Frontend giữ token trong `sessionStorage`, không `localStorage`.
- Admin dùng khóa riêng do VPS quản lý. Khóa không nằm trong source, URL, log hay response. Đăng nhập trả session token HMAC role admin có hạn dùng 4 giờ.

## Dữ liệu

### Student registry

`students.json`: `id`, `display_name`, `phone_salt`, `phone_hash`, `active`, `cohort`, `activated_at`.

### Submission ledger

`submissions.json`: `id`, `student_id`, `week`, `version`, `artifact_url`, `note`, `self_scores`, `submitted_at`, `review_status`, `instructor_score`, `instructor_feedback`, `reviewed_at`.

Không sửa hoặc xóa bản nộp cũ; nộp lại tạo version tăng dần. Chỉ admin được thêm đánh giá vào phiên bản cụ thể.

## API

- `GET /course/portal/weeks`: cấu trúc sáu tuần, đầu ra và rubric công khai.
- `POST /course/portal/login`: xác thực học viên.
- `GET /course/portal/me`: hồ sơ tối thiểu và tiến độ của chính học viên.
- `GET /course/portal/submissions`: lịch sử của chính học viên.
- `POST /course/portal/submissions`: tạo phiên bản bài nộp mới.
- `POST /course/admin/login`: xác thực giảng viên.
- `GET /course/admin/dashboard`: danh sách tiến độ tối thiểu của cohort.
- `PATCH /course/admin/submissions/{id}`: trạng thái, điểm và nhận xét.

Response không echo số điện thoại, hash, salt hay secret.

## Giao diện

Visual tiếp tục dùng Google Sans Flex và hệ Horus: nền trắng, khối đen bo góc, nhãn tuần, bảng/card có hierarchy rõ. Cổng học viên ưu tiên một hành động chính là “Nộp sản phẩm tuần này”. Dashboard ưu tiên học viên cần xử lý và bài “Đã nộp/Cần sửa”. Desktop và mobile không tràn ngang; có focus state, label thật, aria-live và reduced motion.

## Tiêu chí hoàn tất

- Test API chứng minh auth/authorization, validation, versioning, isolation giữa học viên, admin review, CORS và atomic storage.
- Test HTML/JS chứng minh không có secret, đủ sáu tuần, dùng `textContent`, không dùng `innerHTML` với dữ liệu API.
- Service cài đúng artifact, health local/public đạt và dữ liệu thử chỉ chạy trong temporary store.
- GitHub Pages deploy thành công; portal render desktop/mobile không lỗi console, network, ảnh hoặc overflow.
- Không gửi submission giả vào production.
