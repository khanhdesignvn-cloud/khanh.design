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

## Trạng thái biểu mẫu

Google credential hiện chỉ có quyền Drive. Landing page dùng fallback chuẩn bị email để người đăng ký tự xác nhận gửi. Chỉ chuyển sang Google Forms sau khi cậu chủ cấp đúng scope cần thiết và form thử nghiệm đã được kiểm tra bằng dữ liệu giả.

## Kiểm thử

```bash
uv run --with pytest pytest tests -q
node --check ai-van-hanh-doanh-nghiep/app.js
```

## Phát hành

Microsite nằm tại `/ai-van-hanh-doanh-nghiep/` trên branch `course/ai-van-hanh-doanh-nghiep`. Không merge hoặc deploy production nếu chưa có xác nhận riêng của cậu chủ.
