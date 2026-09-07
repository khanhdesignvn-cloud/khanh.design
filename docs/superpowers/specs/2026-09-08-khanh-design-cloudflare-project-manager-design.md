# Thiết kế khởi tạo khanh.design từ gói Project Manager

Ngày: 08/09/2026  
Nguồn bàn giao: `khanh-design-project-manager-handover.zip` trên Google Drive  
Phạm vi đã duyệt: thay trang chủ bằng ứng dụng quản lý mới, giữ nguyên `/100/` và `/khesanhfarm/`, quản trị bằng mật khẩu riêng.

## 1. Mục tiêu

Đưa ứng dụng quản lý dự án trong gói bàn giao lên `https://khanh.design/` với dữ liệu tập trung và phân quyền ghi phía máy chủ. Hai route hiện hữu `https://khanh.design/100/` và `https://khanh.design/khesanhfarm/` phải tiếp tục hoạt động sau chuyển đổi.

Thành công khi:

- Trang chủ tải đúng giao diện Project Manager và các chế độ Sơ đồ, Sản phẩm, Showcase, Slide tổng.
- Người chưa đăng nhập chỉ xem; người quản trị đăng nhập bằng mật khẩu mới có thể ghi dữ liệu và tải tệp.
- Dữ liệu cấu trúc lưu trong Cloudflare D1; ảnh/PDF lưu trong Cloudflare R2.
- `/100/` và `/khesanhfarm/` trả đúng nội dung cũ, không lỗi tài nguyên hay điều hướng.
- Không có mật khẩu, hash thật, khóa phiên, token hoặc credential trong Git.

## 2. Kiến trúc được chọn

Toàn bộ `khanh.design` chuyển từ GitHub Pages sang một Cloudflare Worker/Vinext duy nhất:

- **Ứng dụng động:** source Next/Vinext trong gói bàn giao phục vụ `/` và các API `/api/*`.
- **Dữ liệu:** binding `DB` trỏ tới Cloudflare D1; migration tạo bảng `workspace` và `login_limits`.
- **Media:** binding `BUCKET` trỏ tới Cloudflare R2; API upload/image quản lý ảnh và PDF.
- **Static routes kế thừa:** nội dung hiện hành của `100/` và `khesanhfarm/` được đưa vào cây public/static của cùng deployment, giữ nguyên URL tuyệt đối và đường dẫn tương đối.
- **Tên miền:** sau khi staging đạt toàn bộ kiểm tra, gắn `khanh.design` vào Worker. Không đổi DNS trước khi có bản staging hoạt động.

Không chọn bản static trên GitHub Pages vì phương án đó không thể giữ D1, R2, đăng nhập máy chủ và dữ liệu dùng chung.

## 3. Tổ chức mã nguồn

Gói bàn giao trở thành nền ứng dụng tại repository `khanhdesignvn-cloud/khanh.design`:

- `app/`, `components/`, `db/`, `drizzle/`, `worker/`, `build/`, `lib/`, `hooks/`: giữ theo source bàn giao.
- `public/100/`: bản đang phát hành của route `/100/`, gồm cấu hình slide và toàn bộ asset được tham chiếu.
- `public/khesanhfarm/`: wrapper hiện hành của route `/khesanhfarm/`.
- Các script nguồn, ảnh QA và file chưa được Git theo dõi trong repository cũ không tự động đưa vào deployment.
- Tệp ZIP và bản giải nén tạm không commit vào Git.

Trước khi nhập source phải lập manifest file cũ cần bảo toàn, so sánh checksum sau sao chép và xác nhận không có va chạm đường dẫn với ứng dụng mới.

## 4. Dữ liệu khởi tạo

- Migration D1 được áp dụng trước lần mở production.
- Khi bảng `workspace` chưa có bản ghi `main`, API trả seed `initial` từ `app/model.ts`.
- Lần ghi đầu tiên tạo bản ghi và dùng trường `revision` để chống ghi đè từ nhiều cửa sổ.
- Không tự nhập dữ liệu trình duyệt/localStorage của phiên bản trang chủ cũ vì người dùng đã yêu cầu xóa phiên bản đó và source mới có mô hình dữ liệu riêng.
- Không xóa hoặc sửa dữ liệu Drive, Zalo hay các dự án khác trong quá trình khởi tạo.

## 5. Xác thực và bảo mật

Chỉ bật quản trị bằng mật khẩu riêng:

- Tạo `ADMIN_PASSWORD_HASH` bằng PBKDF2-SHA256; mật khẩu gốc không ghi vào source, log hoặc tin nhắn.
- Tạo `ADMIN_SESSION_SECRET` ngẫu nhiên tối thiểu 32 ký tự và lưu bằng Cloudflare Secret.
- `ADMIN_EMAILS` để trống; đăng nhập ChatGPT không được xem là đường quản trị trong cấu hình production này.
- Cookie quản trị giữ thuộc tính `HttpOnly`, `Secure`, `SameSite=Strict`, tên `__Host-design-admin`, hết hạn sau 8 giờ.
- Mọi API ghi gọi `authorizeWrite`, kiểm tra phiên và chặn origin chéo.
- API đăng nhập giữ giới hạn số lần thử bằng D1.
- Upload phải xác minh MIME, kích thước và ID; không cho người dùng điều khiển trực tiếp key R2.

Nếu source có đường quản trị ChatGPT phụ, UI có thể giữ nhưng production không cấp `ADMIN_EMAILS`; mọi kiểm thử quyền phải chứng minh chỉ mật khẩu hợp lệ mới ghi được.

## 6. Bảo toàn `/100/` và `/khesanhfarm/`

- Sao chép chính xác nội dung đã commit, không lấy các file QA/script chưa theo dõi.
- Kiểm tra toàn bộ asset được tham chiếu trong `/100/`, đặc biệt `slide-config.json`, ảnh, font và SVG.
- `/khesanhfarm/` tiếp tục dùng wrapper hiện hành và iframe tới site catalog nguồn; kiểm tra cả wrapper lẫn origin iframe.
- Worker/static asset routing phải ưu tiên file thực cho hai prefix này, không để Vinext trả HTML fallback của trang chủ.
- Với từng route, xác minh HTTP 200, `Content-Type` đúng, marker nội dung đúng và không có console error.

## 7. Quy trình chuyển đổi an toàn

1. Tạo nhánh/worktree riêng từ `main`; không làm thay đổi các file chưa theo dõi hiện có.
2. Nhập source bàn giao đã kiểm tra path traversal và checksum.
3. Ghép hai route kế thừa vào public/static; tạo test hồi quy.
4. Cài đúng lockfile bằng `npm ci`; chạy lint, test và build theo package scripts.
5. Chạy local với D1/R2 mô phỏng; kiểm thử đăng nhập, CRUD, upload ảnh/PDF, xung đột revision và quyền read-only.
6. Tạo D1, R2, migration và secrets trong môi trường staging Cloudflare.
7. Deploy staging; QA desktop/mobile và kiểm thử trực tiếp API.
8. Chỉ sau khi staging đạt mới commit/push và gắn custom domain.
9. Xác minh production trên `khanh.design`, `/100/`, `/khesanhfarm/`, API, D1, R2 và console.
10. Giữ rollback rõ ràng: cấu hình DNS/route trước chuyển đổi và commit GitHub Pages cuối cùng phải được ghi nhận để có thể phục hồi.

## 8. Kiểm thử bắt buộc

- `npm run lint`.
- `npm test` và `npm run build`.
- Test HTML/component có sẵn trong gói bàn giao.
- Test API: GET công khai; PUT/upload bị từ chối khi chưa đăng nhập; đăng nhập đúng tạo cookie; đăng xuất vô hiệu hóa phiên.
- Test D1 migration và optimistic concurrency trả 409 khi revision cũ.
- Test R2 upload/read ảnh và PDF, kích thước tối đa, MIME không hợp lệ.
- Playwright desktop và mobile cho Sơ đồ, Sản phẩm, Showcase, Slide tổng, đăng nhập và drawer/viewer.
- Regression `/100/` và `/khesanhfarm/`: marker, asset, page overflow và console.
- Production phải kiểm tra bằng cache-busting và đọc lại dữ liệu đã ghi thử; xóa dữ liệu thử trước khi bàn giao.

## 9. Triển khai và rollback

Trước cutover lưu lại:

- bản ghi DNS hiện tại của `khanh.design`;
- trạng thái GitHub Pages và commit production cuối;
- URL staging Worker;
- ID D1/R2 và trạng thái migration, không lưu secrets.

Nếu production lỗi nghiêm trọng, gỡ custom-domain route khỏi Worker và phục hồi DNS/hosting cũ. D1/R2 không bị xóa trong rollback để tránh mất dữ liệu; chỉ ngừng tuyến truy cập.

## 10. Ngoài phạm vi

- Không thay đổi source repository độc lập của Khe Sanh Farm.
- Không sửa nội dung bộ slide `/100/`.
- Không kết nối Zalo, Google Drive hoặc hồ sơ bán hàng vào ứng dụng ở đợt khởi tạo này.
- Không tạo thêm phương thức đăng nhập, phân quyền nhiều vai trò hoặc tài khoản người dùng.
- Không di chuyển/xóa bất kỳ thư mục Google Drive nào.
