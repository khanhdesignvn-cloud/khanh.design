# Tuần 4 — Xây trợ lý bán hàng

**Sản phẩm tuần:** Kịch bản khám phá nhu cầu, xử lý từ chối và chuỗi theo dõi ba chạm  
**Kết quả nối tiếp:** bộ kịch bản tư vấn và chuỗi theo dõi có kiểm duyệt.  
**Thông điệp điều phối:** Không đánh giá học viên bằng độ dài prompt; đánh giá bằng chất lượng đầu ra, khả năng truy vết và trách nhiệm của người dùng.

## Mục tiêu đo được

- Phân loại chính xác 4/5 tình huống mẫu theo nhu cầu, mức phù hợp và bước tiếp theo.
- Soạn kịch bản khám phá có ít nhất năm câu hỏi mở, không chẩn đoán thay khách hàng.
- Tạo chuỗi theo dõi ba chạm có điều kiện dừng và bước duyệt trước khi gửi.

Cuối buổi, giảng viên yêu cầu từng học viên chỉ ra bằng chứng cho mỗi mục tiêu trong file làm việc. Nếu chưa có bằng chứng, trạng thái là **Cần sửa**, không dùng điểm cảm tính để “cho qua”.

## Chuẩn bị trước buổi học

### Giảng viên

- Kiểm tra giao diện Claude và đường dẫn tài nguyên trước giờ học; chuẩn bị ảnh chụp dự phòng để nội dung không phụ thuộc nút bấm.
- Tạo bản sao dữ liệu mẫu, một đầu ra đạt và một đầu ra cố ý có lỗi để lớp so sánh.
- Mở đồng hồ đếm ngược, phòng breakout và bảng theo dõi tiến độ 15 học viên.
- Xóa lịch sử chứa dữ liệu thật khỏi màn hình chia sẻ; tắt thông báo hệ thống.

### Học viên

- Mở workbook đúng tuần, Claude Project thử nghiệm và thư mục lưu phiên bản.
- Chuẩn bị dữ liệu giả hoặc dữ liệu đã được phép, đã ẩn danh.
- Ghi thời gian hiện tại của quy trình để có mốc so sánh trước/sau.

## Agenda 150 phút

| STT | Hoạt động | Phút |
|---:|---|---:|
| 1 | Kiểm tra sản phẩm tuần trước và khởi động | 10 |
| 2 | Giải thích tư duy, nguyên tắc và tiêu chí thành công | 20 |
| 3 | Demo trực tiếp với dữ liệu mẫu | 25 |
| 4 | Thực hành có hướng dẫn theo các mốc kiểm tra | 65 |
| 5 | Nhận xét, sửa hai bài tiêu biểu và tự chấm rubric | 20 |
| 6 | Chốt sản phẩm, bài tập và cam kết tuần mới | 10 |
|  | **Tổng** | **150** |

### Dấu mốc điều phối

- Phút 10: mọi người đã mở đúng tài liệu và nêu một vướng mắc cụ thể.
- Phút 55: demo dừng; học viên phải mô tả lại quy trình trước khi tự làm.
- Phút 85: kiểm tra mốc 1, ưu tiên cứu người chưa có đầu ra tối thiểu.
- Phút 120: dừng thêm tính năng, chuyển sang kiểm tra chất lượng và an toàn.
- Phút 140: mỗi người tự xác nhận Đạt/Cần sửa và ghi hành động tiếp theo.

## Dữ liệu mẫu cho demo

Khách giả lập mã LEAD-07 là quản lý hành chính cần 80 hộp quà, ngân sách 650.000 đồng/hộp, giao trước 20/12, cần hóa đơn VAT. Chưa xác nhận hương vị, địa điểm giao và điều khoản thanh toán. Không dùng tên, email hay số điện thoại thật.

**Quy ước dữ liệu:** mọi người dùng cùng bộ mẫu trong demo để có thể so sánh. Các trường chưa có được ghi “chưa xác nhận”; Claude phải hỏi lại hoặc để trống, không tự sáng tác. Giảng viên nói rõ dữ liệu là hư cấu và chỉ phục vụ học tập.

## Kịch bản demo

**Tên demo:** Từ ghi chú cuộc gọi giả lập đến đề xuất và chuỗi theo dõi.

1. Tách ghi chú thành dữ kiện đã biết, chưa biết và giả định cấm dùng.
2. Cho Claude đề xuất câu hỏi khám phá tiếp theo thay vì chốt sản phẩm ngay.
3. Soạn email tóm tắt nhu cầu và hai phương án có điều kiện rõ.
4. Tạo ba tin theo dõi với nhánh có phản hồi, không phản hồi và từ chối; đặt trạng thái nháp.

### Lời dẫn gợi ý

“Trước khi nhấn gửi, chúng ta có thể nói đầu ra đạt là gì không?” Giảng viên ghi tiêu chí lên màn hình, sau đó mới thao tác. Ở mỗi bước, dừng để hỏi: dữ kiện nào đến từ nguồn, câu nào là suy luận, ai chịu trách nhiệm duyệt? Khi Claude trả lời tốt, vẫn tìm một điểm cần xác minh để luyện năng lực phân biệt. Khi đầu ra sai, không sửa bằng lời nhắc ngẫu nhiên; quay lại đúng thành phần của brief hoặc nguồn dữ liệu gây lỗi.

### Bằng chứng cần lưu

- Brief hoặc cấu hình đầu vào trước khi chạy.
- Đầu ra lần một có đánh dấu lỗi.
- Phiên bản sửa và checklist đã chấm.
- Một câu giải thích vì sao thay đổi giúp kết quả tốt hơn.

## Thực hành có hướng dẫn

1. Viết bảng tiêu chí phân loại lead phù hợp, cần thêm thông tin hoặc không phù hợp.
2. Dùng tình huống mẫu để tạo kịch bản khám phá và xử lý hai phản đối.
3. Soạn đề xuất một trang chỉ dùng thông tin đã xác nhận.
4. Đóng vai theo cặp: một người là khách, một người dùng trợ lý; đổi vai và ghi lỗi.

### Nhịp 65 phút

- **0–10 phút — Chọn phạm vi:** viết một câu nêu người dùng, tình huống, đầu ra và giới hạn. Trợ giảng kiểm tra để tránh bài quá rộng.
- **10–25 phút — Chuẩn hóa đầu vào:** học viên đánh dấu dữ kiện đã xác minh, dữ kiện thiếu và dữ liệu phải loại bỏ. Chưa được gọi AI nếu chưa xong.
- **25–40 phút — Tạo phiên bản 1:** chạy trên dữ liệu mẫu hoặc dữ liệu đã làm sạch; lưu nguyên văn, không ghi đè.
- **40–52 phút — Kiểm tra:** dùng rubric, tô câu thiếu nguồn, sai giọng, sai định dạng hoặc vượt thẩm quyền.
- **52–62 phút — Sửa phiên bản 2:** chỉ thay đổi những phần có lý do; so sánh trước/sau.
- **62–65 phút — Chốt bằng chứng:** đặt tên file, ghi phiên bản, người duyệt và câu hỏi còn mở.

### Câu hỏi coaching

- Thành công quan sát được là gì, và ai là người xác nhận?
- Nếu đầu ra sai, hậu quả lớn nhất là gì? Có thể giảm rủi ro bằng dữ liệu giả, trạng thái nháp hay một bước duyệt không?
- Claude đang thiếu dữ kiện nào? Có được phép hỏi hoặc để trống thay vì đoán không?
- Tiêu chí nào trong rubric chưa có bằng chứng?

## Rubric đánh giá

| Tiêu chí | Đạt | Cần sửa |
|---|---|---|
| Kịch bản ưu tiên hiểu nhu cầu trước khi đề xuất. | Có bằng chứng rõ, dùng được ngay và không vi phạm ranh giới an toàn. | Thiếu bằng chứng, còn suy đoán hoặc chưa có bước duyệt. |
| Không tự bịa giá, tồn kho, thời hạn hay chính sách. | Có bằng chứng rõ, dùng được ngay và không vi phạm ranh giới an toàn. | Thiếu bằng chứng, còn suy đoán hoặc chưa có bước duyệt. |
| Mỗi tin theo dõi có mục tiêu, ngữ cảnh và điều kiện dừng. | Có bằng chứng rõ, dùng được ngay và không vi phạm ranh giới an toàn. | Thiếu bằng chứng, còn suy đoán hoặc chưa có bước duyệt. |
| Tất cả nội dung ra ngoài ở trạng thái nháp và có người duyệt. | Có bằng chứng rõ, dùng được ngay và không vi phạm ranh giới an toàn. | Thiếu bằng chứng, còn suy đoán hoặc chưa có bước duyệt. |

**Cách chấm:** sản phẩm chỉ **Đạt** khi tất cả tiêu chí đều đạt. Giảng viên không sửa hộ toàn bộ; phản hồi theo cấu trúc “bằng chứng thấy được — rủi ro — một thay đổi nhỏ cần thử”. Học viên lưu phiên bản đã sửa để chứng minh vòng cải tiến.

## Bài tập về nhà

Tùy chỉnh kịch bản cho một dòng sản phẩm; chạy ba tình huống giả lập; nộp bản trước/sau khi sửa và nhật ký quyết định.

### Tiêu chí hoàn thành

- Nộp đúng sản phẩm, không chỉ nộp ảnh prompt.
- Có dữ liệu đầu vào đã làm sạch, đầu ra trước/sau và rubric tự chấm.
- Có tên người duyệt hoặc vai trò duyệt, ngày cập nhật và một việc sẽ thử tiếp.
- Không chứa dữ liệu cá nhân thật, credential hoặc link cấp quyền riêng.

## Quyền riêng tư và bảo mật

- CRM chỉ xuất trường tối thiểu cần thiết; thay danh tính bằng mã lead.
- Không nhập thông tin sức khỏe, tài chính, lịch sử mua hàng nhạy cảm hoặc nội dung trao đổi riêng tư.
- Không bật tự gửi email/tin nhắn trong bài tập; người học phải đọc và xác nhận người nhận.

### Điểm dừng bắt buộc

Nếu học viên mở tài liệu có dữ liệu nhận diện, giảng viên yêu cầu dừng chia sẻ màn hình, đóng tài liệu và chuyển sang bộ mẫu. Không yêu cầu học viên gửi file thật vào chat lớp. Sự tiện lợi không phải là lý do đủ để bỏ qua quyền truy cập, mục đích sử dụng và thời hạn lưu giữ.

## Lỗi thường gặp

- Dùng AI để ép chốt thay vì hỗ trợ tư vấn phù hợp.
- Gộp dữ kiện và suy đoán thành một đoạn khó kiểm tra.
- Theo dõi vô hạn, không có opt-out hoặc điều kiện dừng.

- Chỉ lưu đầu ra cuối nên không chứng minh được cách kiểm tra và cải tiến.
- Tối ưu câu chữ trước khi xác nhận dữ kiện và tiêu chí thành công.
- Nhầm “AI có thể làm” với “AI được phép tự quyết”.

## Phương án xử lý lớp học

- **Học viên chưa có dữ liệu:** dùng trọn bộ Mộc Nhiên; vẫn hoàn thành kỹ năng, sau lớp mới thay dữ liệu của mình.
- **Học viên đi quá nhanh:** giao vai reviewer, yêu cầu tìm rủi ro và tạo test case biên; không mở thêm công cụ.
- **Claude hoặc mạng lỗi:** dùng ảnh đầu ra dự phòng, chấm rubric và viết bản sửa ngoại tuyến.
- **Chênh lệch ngành:** giữ cấu trúc quy trình chung; ví dụ ngành chỉ thay sau khi tiêu chí và ranh giới đã rõ.

## Chốt buổi và bàn giao sang tuần sau

Mỗi học viên nói trong 30 giây: sản phẩm đã có, trạng thái Đạt/Cần sửa, một rủi ro và bước tiếp theo. Giảng viên ghi người cần hỗ trợ ở AI Clinic, không kéo dài buổi chính. Nhắc lại rằng sản phẩm tuần này sẽ trở thành đầu vào cho các tuần sau; tài liệu phải có phiên bản và nguồn để có thể bàn giao.
