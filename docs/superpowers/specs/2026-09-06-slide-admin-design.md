# Thiết kế trang quản trị slide `/100/admin`

## Mục tiêu

Tạo một trang quản trị riêng tại `https://khanh.design/100/admin/` để cậu chủ tự sắp xếp, thêm, sửa, ẩn và xóa slide; xem trước trước khi xuất bản; cập nhật trực tiếp bộ trình chiếu công khai tại `/100/`; và hoàn tác lần xuất bản gần nhất khi cần.

## Phạm vi phiên bản đầu

### Quản lý slide hiện có

- Hiển thị danh sách thumbnail, số trang và tiêu đề của toàn bộ slide.
- Kéo thả hoặc dùng nút lên/xuống để đổi thứ tự.
- Ẩn/hiện slide mà không xóa nội dung nguồn.
- Các slide HTML thiết kế riêng hiện có chỉ cho đổi thứ tự, đổi tiêu đề hiển thị và ẩn/hiện; không cung cấp trình sửa HTML tự do để tránh làm hỏng bố cục.

### Slide mới

- Thêm slide theo mẫu nhận diện hiện hành gồm ảnh, nhãn nhỏ, tiêu đề, phần diễn giải dạng đoạn hoặc danh sách và dòng ghi chú cuối.
- Ảnh tải lên được nén về kích thước phù hợp nhưng không làm méo tỷ lệ.
- Cho phép sửa toàn bộ nội dung của slide được tạo từ trang quản trị.
- Cho phép xóa slide mới; thao tác xóa chỉ có hiệu lực sau khi bấm xuất bản.

### Xem trước và xuất bản

- Chế độ xem trước dùng đúng khung `1600 × 900` và thu phóng theo màn hình.
- Có hai trạng thái rõ ràng: **Bản nháp** và **Đã xuất bản**.
- Nút **Lưu bản nháp** lưu dữ liệu trên máy chủ nhưng không thay đổi trang công khai.
- Nút **Lưu và xuất bản** kiểm tra dữ liệu, ghi cấu hình/ảnh vào repo `khanhdesignvn-cloud/khanh.design`, tạo commit và push nhánh `main`.
- Trang quản trị hiển thị trạng thái triển khai GitHub Pages và chỉ báo thành công sau khi production phản ánh đúng phiên bản mới.
- Nút **Hoàn tác lần xuất bản gần nhất** tạo một commit phục hồi an toàn, không dùng force-push.

## Kiến trúc

### Frontend tĩnh

- Đường dẫn: `100/admin/index.html`.
- Giữ bảng màu xanh đậm, đỏ bazan, kem/lúa mì và font SVN Brice của bộ nhận diện.
- Giao diện gồm ba vùng: danh sách slide, khung xem trước, bảng thuộc tính slide.
- Trên điện thoại, ba vùng chuyển thành các màn hình xếp dọc; nút lên/xuống thay cho kéo thả khi thao tác cảm ứng khó chính xác.
- Frontend không chứa mật khẩu quản trị, GitHub token hoặc credential nào.

### Dữ liệu slide

- File công khai `100/slide-config.json` giữ:
  - phiên bản schema;
  - thứ tự các ID slide;
  - danh sách slide ẩn;
  - nội dung các slide mới;
  - tiêu đề hiển thị được ghi đè;
  - mã phiên bản xuất bản.
- Mỗi slide HTML cũ được gắn một `data-slide-id` ổn định, không phụ thuộc số thứ tự.
- `/100/index.html` đọc cấu hình trước khi khởi tạo điều hướng, sau đó sắp xếp DOM, ẩn slide và chèn slide mới.
- Nếu tải cấu hình thất bại hoặc dữ liệu không hợp lệ, bộ trình chiếu quay về thứ tự HTML mặc định và vẫn sử dụng được.

### Backend quản trị

- Chạy thành dịch vụ riêng trên VPS, chỉ lắng nghe localhost; reverse proxy qua HTTPS tại một endpoint ổn định.
- API tối thiểu:
  - `POST /login`;
  - `POST /logout`;
  - `GET /slides`;
  - `PUT /draft`;
  - `POST /images`;
  - `POST /publish`;
  - `POST /rollback`;
  - `GET /deployment/:id`.
- Backend kiểm tra quyền, validate schema, kích thước ảnh, MIME thật và giới hạn dung lượng trước khi ghi file.
- Việc ghi repo được khóa tuần tự để hai lần bấm xuất bản không chạy chồng nhau.
- Mỗi lần xuất bản chỉ stage các file thuộc `/100`; không commit cache, ảnh QA hoặc thay đổi ngoài phạm vi.

## Xác thực và an toàn

- Một tài khoản quản trị duy nhất trong phiên bản đầu.
- Mật khẩu không lưu dạng rõ; backend lưu hash có salt trong file cấu hình riêng ngoài repo.
- Phiên đăng nhập dùng cookie `HttpOnly`, `Secure`, `SameSite` phù hợp với endpoint HTTPS.
- Có CSRF token cho mọi thao tác ghi.
- Giới hạn số lần đăng nhập sai và ghi nhật ký thời gian/IP cho đăng nhập, xuất bản, hoàn tác.
- Không cho nhập HTML hoặc JavaScript tùy ý; mọi nội dung văn bản được escape trước khi render.
- Chỉ chấp nhận JPG, PNG hoặc WebP; kiểm tra chữ ký file và giải mã ảnh trước khi lưu.
- Không trả GitHub token, đường dẫn credential hoặc nội dung log nhạy cảm về frontend.

## Luồng sử dụng

1. Cậu chủ mở `/100/admin/` và đăng nhập.
2. Trang tải bản đã xuất bản cùng bản nháp gần nhất nếu có.
3. Cậu chủ kéo thả, thêm/sửa/ẩn slide và xem trước.
4. **Lưu bản nháp** để tiếp tục sau, hoặc **Lưu và xuất bản** để cập nhật website.
5. Backend validate, ghi file, commit, push và theo dõi GitHub Pages.
6. Frontend báo chính xác một trong bốn trạng thái: đang kiểm tra, đang triển khai, đã xuất bản, hoặc lỗi có thể khôi phục.
7. Khi cần, cậu chủ chọn hoàn tác và xác nhận một lần trước khi backend tạo commit phục hồi.

## Xử lý lỗi

- Mất mạng trước khi lưu: giữ dữ liệu đang sửa trong localStorage để khôi phục giao diện.
- Backend không truy cập được repo hoặc push thất bại: không báo thành công; bản công khai giữ nguyên.
- GitHub Pages build lỗi: giữ commit để chẩn đoán, cung cấp nút hoàn tác.
- Ảnh quá lớn/sai định dạng: từ chối trước khi upload và hiển thị giới hạn cụ thể.
- Cấu hình slide sai: backend từ chối xuất bản; frontend production dùng thứ tự HTML mặc định.

## Kiểm thử và tiêu chí hoàn tất

- TDD cho parser/cấu hình, xác thực, validate upload, sắp xếp, ẩn/hiện, thêm/xóa, xuất bản và hoàn tác.
- Kiểm thử trình duyệt desktop và mobile cho đăng nhập, kéo thả/nút lên xuống, sửa nội dung, xem trước và trạng thái triển khai.
- Kiểm thử stored XSS bằng tiêu đề/nội dung độc hại.
- Kiểm thử ảnh lỗi, ảnh quá lớn và MIME giả.
- Kiểm thử hai yêu cầu xuất bản đồng thời.
- Kiểm thử rollback tạo commit mới và phục hồi đúng cấu hình trước đó.
- Production đạt khi:
  - `/100/admin/` tải qua HTTPS;
  - người chưa đăng nhập không đọc/ghi dữ liệu quản trị;
  - một thay đổi thử nghiệm xuất bản thành công và xuất hiện tại `/100/`;
  - hoàn tác thử nghiệm khôi phục đúng trạng thái;
  - console không có lỗi trên desktop/mobile;
  - không có credential trong repo hoặc HTML công khai.

## Ngoài phạm vi

- Trình chỉnh sửa HTML/CSS tự do cho slide cũ.
- Nhiều tài khoản hoặc phân quyền theo vai trò.
- Đồng biên tập thời gian thực.
- Lịch xuất bản slide.
- Force-push hoặc xóa lịch sử Git.
