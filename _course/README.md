# AI Vận Hành Doanh Nghiệp

Bộ tài sản triển khai cohort sáng lập của chương trình **AI Vận Hành Doanh Nghiệp — Xây bộ máy trợ lý AI với Claude trong 6 tuần**.

## Cấu trúc

- `curriculum/`: giáo án giảng viên theo tuần.
- `workbook/`: workbook và template dành cho học viên.
- `workshop/`: nội dung và source workshop mở bán.
- `launch/`: kế hoạch nội dung, case study và chuỗi nhắc lịch.
- `onboarding/`: form spec, checklist đầu vào và thông báo quyền riêng tư.
- `scripts/`: script dựng PDF/PPTX.
- `dist/`: tài liệu xuất bản đã kiểm tra.

## Nguyên tắc

- Claude là công cụ AI trung tâm.
- Học qua dự án thật nhưng phải ẩn dữ liệu nhạy cảm.
- Mọi workflow gửi/đăng ra ngoài đều có bước người dùng duyệt.
- Không dùng cam kết x10 doanh thu, tự động hóa 80% hoặc thay thế nhân sự.
- File tiếng Việt giao cho học viên phải ở dạng PDF có font Unicode nhúng.

## Bộ quản lý và chia sẻ

Các file hiện hành trong `dist/`:

- `04-09-2026-So-tay-van-hanh-khoa-hoc-AI.docx/.pdf`: quy trình nội bộ từ đăng ký đến tốt nghiệp.
- `04-09-2026-Lich-hoc-va-quan-ly-cohort-AI.xlsx`: dashboard, hồ sơ, lịch, tiến độ, công việc và chỉ mục tài liệu.
- `04-09-2026-Chuong-trinh-hoc-AI-Van-hanh-doanh-nghiep.docx/.pdf`: bản chia sẻ cho ứng viên/học viên.
- Giáo án chi tiết Horus 6 tuần: `04-09-2026-Giao-an-chi-tiet-Horus-AI-Van-hanh-doanh-nghiep.docx/.pdf`.
- Workbook và workshop đã xuất PDF/PPTX riêng.

Lịch ngày/giờ trong bộ file mới là **dự kiến**; chỉ đổi thành chính thức sau khi chủ chương trình xác nhận.

## Cổng học viên và quản lý bài tập

- `/hoc-vien/`: học viên đăng nhập bằng mã hồ sơ + số điện thoại, xem 6 tuần, nộp link sản phẩm, tự chấm rubric và xem lịch sử phản hồi.
- `/quan-ly/`: dashboard riêng của giảng viên, không liên kết công khai từ landing page; dùng khóa quản trị chỉ lưu trên VPS.
- Dữ liệu portal nằm trong `/var/lib/khanh-course/`, không đưa lên GitHub.
- Sau khi xác nhận phù hợp và hoàn tất thanh toán, kích hoạt học viên bằng:
  `sudo -u khanh-course /usr/local/lib/khanh-course/manage_course_portal.py activate <MÃ_HỒ_SƠ> --cohort 2026-09`
- Đổi khóa quản trị bằng cách chạy `configure-admin`; công cụ đọc khóa từ stdin/terminal và không in lại giá trị.

## Trạng thái biểu mẫu

Landing page gửi hồ sơ tới API riêng tư; API chỉ trả mã hồ sơ, không phản hồi dữ liệu cá nhân. Khi API tạm lỗi, frontend dùng email fallback để người đăng ký tự kiểm tra và xác nhận gửi.

## Kiểm thử

```bash
uv run --with pytest pytest tests -q
node --check ai-learning/app.js
```

## Phát hành

Microsite nằm tại `/ai-learning/` trên branch `course/ai-learning`. Không merge hoặc deploy production nếu chưa có xác nhận riêng của cậu chủ.
