# khanh.design

Trang chủ thương hiệu cá nhân Nguyễn Quốc Khánh, chuyển thể có chọn lọc từ cấu trúc giao diện HKM:

- Một trang duy nhất: hero, giới thiệu, dự án, quy trình, dịch vụ và project brief.
- HTML/CSS/JavaScript thuần, không framework và không dependency build.
- Giao diện editorial bám sát mẫu Manus/HKM: hero tràn màn hình, bảng màu kem–nâu–vàng, vòng cung, project grid lệch tầng và ribbon ngang.
- 11 ảnh WebP thực tế từ kho dự án của Khánh; không dùng ảnh nội thất hoặc asset thương hiệu HKM.
- Responsive tại 390 px; menu bàn phím/Escape; hỗ trợ `prefers-reduced-motion`.
- Form kiểm tra trường bắt buộc, tự lưu nháp bằng `localStorage` và chuẩn bị email gửi tới `hi@nguyenquockhanh.vn`.

## Chạy local

```bash
python3 -m http.server 8100
```

Mở `http://127.0.0.1:8100/`.

## Kiểm thử

```bash
uv run --with pytest pytest tests -q
node --check app.js
git diff --check
```

## Triển khai

GitHub Pages phát trực tiếp từ branch `main`, thư mục gốc. Chưa tạo `CNAME`; chỉ thêm `khanh.design` sau khi DNS được chuyển sang GitHub Pages.

## Form production

Bản đầu dùng email client, không gửi dữ liệu đến dịch vụ bên thứ ba và không chứa credential phía client. Khi trỏ domain có thể thay bằng endpoint server-side để lưu Drive/gửi thông báo Zalo.
