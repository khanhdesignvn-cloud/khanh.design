# Thiết kế trang chủ khanh.design theo Horus Workspace

Ngày: 2026-09-07

## Mục tiêu

Thay trang chủ trống `khanh.design/` bằng một bản triển khai tĩnh bám sát giao diện và tương tác của site tham chiếu `khe-sanh-design-map.nitia-gpt-pr-6208.chatgpt.site`, đồng thời giữ nguyên toàn bộ đường dẫn hiện hữu như `/100/`, `/khesanhfarm/`, `/quan-ly/` và các dịch vụ phía sau.

Trang phục vụ một người dùng chính là Khánh quản lý các hạng mục thiết kế theo dự án. Không có đăng nhập hoặc dữ liệu dùng chung giữa thiết bị.

## Phạm vi

### Có

- Sidebar Horus, tiêu đề workspace, bộ chọn dự án và thống kê nhanh.
- Thanh dự án với mã, mô tả và tỷ lệ hoàn thành.
- Ba chế độ `Sơ đồ`, `Bảng`, `Showcase`.
- Tìm kiếm hạng mục và lọc theo trạng thái.
- Sơ đồ nhóm/hạng mục có kéo khung nhìn, thu nhỏ, phóng to và vừa màn hình.
- Tạo, sửa, xóa dự án, nhóm và hạng mục qua hộp thoại.
- Đổi trạng thái: Chưa bắt đầu, Đang thiết kế, Chờ duyệt, Cần chỉnh sửa, Hoàn thành.
- Thêm ảnh showcase từ máy; lưu ảnh trong IndexedDB, dữ liệu cấu trúc trong localStorage.
- Responsive desktop/mobile; hỗ trợ bàn phím, focus rõ và reduced motion.
- Dữ liệu mẫu ban đầu đúng dự án `100 năm cà phê Khe Sanh` với 4 nhóm và 13 hạng mục như site tham chiếu.

### Không có

- Đăng nhập, backend, đồng bộ giữa thiết bị hoặc nhiều người dùng.
- Thay đổi các trang con hiện hữu.
- Ghi dữ liệu lên Google Drive/GitHub từ trình duyệt.

## Kiến trúc

Trang chủ là ứng dụng tĩnh không framework:

- `index.html`: cấu trúc semantic, hộp thoại và template.
- `assets/home.css`: token màu, typography, layout, responsive và trạng thái.
- `assets/home.js`: state, CRUD, tìm kiếm/lọc, các chế độ xem, pan/zoom và UI.
- `assets/home-db.js`: wrapper IndexedDB cho ảnh showcase.

State có version schema. Khi chưa có dữ liệu, ứng dụng seed dự án mẫu. Mỗi thay đổi cấu trúc được serialize vào localStorage. Ảnh được lưu theo ID trong IndexedDB để tránh vượt giới hạn localStorage. Nếu storage lỗi hoặc đầy, UI báo rõ và không làm mất state trước đó.

## Ngôn ngữ thị giác

Bám sát bản tham chiếu: nền xanh đen sâu, sidebar tối, panel kem sáng, điểm nhấn xanh chanh, type display serif lớn và sans-serif cho UI. Cấu trúc desktop gồm sidebar cố định và canvas nội dung; mobile chuyển thành header gọn, thanh điều khiển cuộn ngang và các card một cột.

Không sao chép bundle/minified code của site nguồn. Giao diện được dựng lại từ quan sát trực tiếp để mã nguồn dễ bảo trì và không phụ thuộc hostname tham chiếu.

## Luồng dữ liệu

1. Load schema từ localStorage và ảnh từ IndexedDB.
2. Nếu chưa có, seed dữ liệu Khe Sanh.
3. Mọi thao tác CRUD cập nhật state bất biến, validate, persist rồi render lại.
4. Search/filter chỉ tạo derived view, không sửa dữ liệu gốc.
5. Showcase đọc thumbnail từ IndexedDB bằng object URL và thu hồi URL khi unmount/render lại.

## An toàn và lỗi

- Nội dung người dùng render bằng `textContent`, không đưa trực tiếp vào `innerHTML`.
- File ảnh giới hạn MIME ảnh và kích thước hợp lý; URL object được thu hồi.
- Xóa dữ liệu cần xác nhận và chỉ tác động storage trong trình duyệt hiện tại.
- Có nút khôi phục dữ liệu mẫu nhưng yêu cầu xác nhận.
- Không nhúng token, mật khẩu hoặc API key.

## Kiểm thử và nghiệm thu

- Syntax check JavaScript và kiểm tra HTML.
- Playwright desktop 1440×1000 và mobile 390×844.
- E2E: seed dữ liệu; chuyển 3 view; tìm kiếm/lọc; tạo/sửa/xóa nhóm và hạng mục; đổi trạng thái; upload ảnh; reload và xác nhận persistence; pan/zoom; reset dữ liệu.
- Không có console error, ảnh hỏng, tràn ngang ngoài vùng điều khiển chủ ý hoặc liên kết trang con bị đổi.
- So sánh screenshot với site tham chiếu ở desktop và mobile.
- Commit/push riêng các file trang chủ; chờ GitHub Pages thành công và kiểm tra production `https://khanh.design/`.
