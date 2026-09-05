# Hướng dẫn giảng viên — AI VẬN HÀNH DOANH NGHIỆP

**Phiên bản cohort sáng lập — 04-09-2026**  
Tài liệu này giúp giảng viên đứng lớp nhất quán trong sáu buổi 150 phút và sáu phiên AI Clinic 60 phút. Trọng tâm là làm ra sản phẩm vận hành được, không trình diễn công cụ. Claude là công cụ trung tâm; Canva, Google Workspace và Make/n8n chỉ hỗ trợ nơi cần thiết.

## Nguyên tắc điều phối

1. Bắt đầu từ kết quả, dữ liệu, tiêu chí và người duyệt trước khi viết prompt.
2. Mỗi phần giải thích phải dẫn đến một thao tác của học viên; không giảng liên tục quá 20 phút.
3. Dùng dữ liệu mẫu mặc định. Dữ liệu thật chỉ xuất hiện khi học viên có quyền sử dụng và đã làm sạch.
4. Đầu ra trôi chảy không đồng nghĩa đúng. Luôn yêu cầu nguồn, test case và rubric.
5. Mọi nội dung ra ngoài doanh nghiệp ở trạng thái nháp/chờ duyệt trong cohort đầu.
6. Chấm **Đạt/Cần sửa** dựa trên bằng chứng, không dựa trên kinh nghiệm dùng công cụ.

## Trước khóa học

### Hai tuần trước khai giảng

- Gửi khảo sát ngành, vai trò, quy trình muốn cải tiến, mức độ sử dụng Claude và nhu cầu hỗ trợ tiếp cận.
- Gửi thông báo dữ liệu: mục đích thu thập, người được xem, thời hạn lưu và cách yêu cầu xóa.
- Cấp workbook, thư mục nộp bài riêng và bộ dữ liệu hư cấu Mộc Nhiên. Không tạo thư mục lớp cho phép học viên xem file riêng của nhau.
- Hướng dẫn tạo tài khoản nhưng không yêu cầu gửi mật khẩu, mã xác thực, token hay ảnh màn hình billing.
- Yêu cầu đo thời gian hiện tại của một công việc cụ thể; đây là mốc học tập, không phải cam kết tăng hiệu suất.

### 24 giờ trước mỗi buổi

- Kiểm tra link Meet, quyền phòng, phụ đề, breakout và bản ghi. Chỉ ghi phần chung sau khi thông báo.
- Chạy lại demo bằng tài khoản thử; chụp ảnh từng mốc và xuất đầu ra mẫu để dự phòng thay đổi giao diện.
- Rà dữ liệu demo: không có tên, email, điện thoại, địa chỉ, ID thật, chữ ký, số tài khoản hoặc bí mật kinh doanh.
- Mở tài liệu tuần, rubric, bảng theo dõi tiến độ và đồng hồ. Chuẩn bị một đầu ra đạt, một đầu ra cần sửa.

## Nhịp điều phối 150 phút

| Chặng | Phút | Kết quả bắt buộc |
|---|---:|---|
| Kiểm tra tuần trước | 10 | Nêu sản phẩm, bằng chứng, một điểm cần sửa |
| Tư duy và nguyên tắc | 20 | Học viên giải thích lại bằng ví dụ của mình |
| Demo | 25 | Có dữ liệu mẫu, tiêu chí, phiên bản lỗi và bản sửa |
| Thực hành | 65 | Mỗi người tạo đầu ra và tự chấm rubric |
| Nhận xét | 20 | Hai bài được sửa công khai bằng dữ liệu an toàn |
| Giao bài | 10 | Biết file phải nộp, tiêu chí và hạn |

Giảng viên dùng timebox thật. Nếu phần demo lỗi, không lấy thời gian của thực hành: chuyển sang ảnh dự phòng, để lớp phân tích quyết định. Phút 120 là điểm đóng phạm vi; không thêm tính năng sau mốc này.

## Vai trò trong lớp

- **Giảng viên chính:** giữ mục tiêu, demo, phản hồi theo rubric và quyết định điểm dừng an toàn.
- **Trợ giảng:** theo dõi breakout, đánh dấu xanh/vàng/đỏ, hỗ trợ kỹ thuật nhưng không nhận credential.
- **Timekeeper luân phiên:** nhắc mốc, giúp lớp hình thành kỷ luật vận hành.
- **Học viên:** chịu trách nhiệm dữ liệu đưa vào, kiểm tra đầu ra và quyết định sử dụng.

## Phản hồi theo rubric

Dùng ba câu: “Tôi thấy bằng chứng…”, “Rủi ro còn lại là…”, “Hãy thử một thay đổi…”. Không nói “prompt chưa hay” chung chung. Chỉ ra tiêu chí cụ thể và yêu cầu học viên tự sửa. Với sản phẩm Cần sửa, ghi một hành động có thể hoàn tất trong 48 giờ; không giao lại toàn bộ bài.

Khi hai reviewer bất đồng, họ phải trích bằng chứng và định nghĩa tiêu chí. Giảng viên quyết định dựa trên ranh giới an toàn và mục tiêu đã công bố, đồng thời ghi chú để hiệu chỉnh rubric sau cohort.

## Xử lý dữ liệu nhạy cảm

Dừng ngay việc chia sẻ khi thấy dữ liệu nhận diện, credential, thông tin thanh toán, hồ sơ sức khỏe hoặc tài liệu không rõ quyền. Yêu cầu đóng file, không chụp lại màn hình, chuyển sang dữ liệu mẫu. Sau buổi, nhắc người học kiểm tra lịch sử chia sẻ và quyền truy cập. Không yêu cầu gửi bản gốc cho giảng viên để “xem giúp”.

Nếu nghi ngờ lộ dữ liệu: ghi nhận tối thiểu thời điểm và loại dữ liệu, không sao chép thêm; báo chủ sở hữu hệ thống theo quy trình của doanh nghiệp; thu hồi link/quyền khi được phép; đổi credential qua kênh chính thức do chính học viên thực hiện. Lớp học không thay thế quy trình ứng phó sự cố của doanh nghiệp.

## AI Clinic 60 phút

AI Clinic không giảng bài mới. Cấu trúc: 5 phút nhắc ranh giới, 10 phút thu ca và chọn thứ tự, 35 phút xử lý tối đa ba ca, 5 phút ghi hành động, 5 phút tổng kết. Mỗi ca trình bày bằng dữ liệu giả hoặc màn hình đã làm sạch: mục tiêu, đầu vào, triệu chứng, điều đã thử và tiêu chí đạt.

Phần chung có thể ghi hình sau khi cả lớp được thông báo. Khi đi vào dữ liệu riêng, dừng bản ghi hoặc chuyển phòng riêng. Không biến Clinic thành nơi giảng viên vận hành hệ thống hộ học viên; kết thúc mỗi ca bằng test nhỏ mà học viên tự chạy.

## Kế hoạch dự phòng

- **Claude gián đoạn:** dùng transcript demo, cho học viên viết brief và chấm hai đầu ra tĩnh.
- **Google Meet lỗi:** chuyển link dự phòng đã thông báo; không gửi link mới qua kênh công khai.
- **Make/n8n thay giao diện:** dạy sơ đồ trạng thái, dùng ảnh chụp và workflow JSON đã kiểm tra; không chạy gửi thật.
- **Học viên thiếu tài khoản trả phí:** ghép cặp quan sát và làm toàn bộ worksheet; sản phẩm không phụ thuộc tính năng trả phí.
- **Vắng trợ giảng:** giảm số bài nhận xét, giữ nguyên 65 phút thực hành và điểm kiểm tra an toàn.

## Theo dõi tiến độ

Bảng lớp chỉ lưu mã học viên, trạng thái nộp, Đạt/Cần sửa, hành động tiếp và ngày kiểm tra. Không lưu nội dung khách hàng hoặc credential. Mỗi tuần giảng viên xem ba tín hiệu: ai chưa tạo được sản phẩm tối thiểu, tiêu chí nào bị trượt nhiều, phần nào tiêu tốn quá thời gian. Điều chỉnh ví dụ và hướng dẫn, không âm thầm hạ rubric.

## Hướng dẫn từng tuần

### Tuần 1 — Làm chủ Claude và tư duy giao việc
Giữ trọng tâm ở lựa chọn việc phù hợp và năm thành phần giao việc. Can thiệp nếu học viên chọn tuyển dụng, thanh toán hoặc quyết định pháp lý làm bài đầu. Kết thúc bằng ba quy trình ưu tiên có lý do.

### Tuần 2 — Xây trợ lý hiểu doanh nghiệp
Không để lớp biến thành buổi tải hàng loạt tài liệu. Mỗi nguồn phải có chủ sở hữu, ngày hiệu lực và mức tin cậy. Demo xung đột chính sách để tạo thói quen hỏi lại.

### Tuần 3 — Hệ thống nội dung marketing
Dừng ngay claim không có nguồn. Chấm khả năng truy vết trước văn phong. Mỗi kênh phải có người đọc, mục tiêu, cấu trúc và CTA riêng.

### Tuần 4 — Trợ lý bán hàng
Phân biệt hỗ trợ soạn nháp với tự quyết định giá, chiết khấu hay gửi tin. Bắt buộc nhánh dừng theo dõi và bước người duyệt.

### Tuần 5 — Chăm sóc khách hàng và vận hành
Dạy ngưỡng chuyển cấp rõ, đặc biệt tình huống pháp lý, an toàn, khiếu nại công khai hoặc bồi hoàn. SOP phải có bằng chứng hoàn tất, không chỉ danh sách bước.

### Tuần 6 — Tự động hóa và bàn giao
Chỉ dùng tài khoản thử, tắt lịch, dừng trước gửi. Kiểm thử ca chuẩn, dữ liệu thiếu và chạy trùng. Bài tốt nghiệp cần runbook tắt hệ thống và chủ sở hữu sau khóa.

## Đánh giá bài tốt nghiệp

Bài tốt nghiệp Đạt khi chứng minh: bài toán có phạm vi rõ; dữ liệu hợp lệ; workflow chạy bằng dữ liệu mẫu; có validation, chống trùng, nhánh lỗi và log; đầu ra chờ duyệt; rubric có bằng chứng; runbook và bàn giao xác định người chịu trách nhiệm. Không thưởng điểm cho số lượng công cụ.

## Sau mỗi buổi và sau cohort

Trong 24 giờ, gửi recap không chứa dữ liệu riêng, hạn bài, rubric và link tài nguyên. Xóa bản tải tạm không cần thiết. Ghi thay đổi giáo trình bằng changelog. Sau sáu tuần, tổng hợp tỷ lệ tham dự, tỷ lệ Đạt, thời gian tự đo và phản hồi; chỉ dùng case study khi có sự đồng ý riêng về nội dung được công bố.
