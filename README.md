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

GitHub Pages phát trực tiếp từ branch `main`, thư mục gốc. Tệp `CNAME` cấu hình custom domain apex là `khanh.design`.

Để trỏ DNS cho GitHub Pages, tạo bốn bản ghi `A` cho `@` tới `185.199.108.153`, `185.199.109.153`, `185.199.110.153` và `185.199.111.153`; tạo `CNAME` cho `www` tới `khanhdesignvn-cloud.github.io`. Không thay đổi bản ghi `hkm`, để `hkm.khanh.design` tiếp tục chạy trên máy chủ hiện tại. Xem hướng dẫn GitHub Pages chính thức trước khi thay DNS.[1]

## Form production

Bản đầu dùng email client, không gửi dữ liệu đến dịch vụ bên thứ ba và không chứa credential phía client. Khi trỏ domain có thể thay bằng endpoint server-side để lưu Drive/gửi thông báo Zalo.

## References

[1]: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site "Managing a custom domain for your GitHub Pages site"
