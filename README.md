# khanh.design — AI Vận Hành Doanh Nghiệp

Repo chính thức cho website và bộ tài sản khóa học **AI VẬN HÀNH DOANH NGHIỆP — Xây bộ máy trợ lý AI với Claude trong 6 tuần**.

## Phạm vi

- `index.html`: chuyển khách truy cập từ `khanh.design` tới website khóa học.
- `ai-learning/`: landing page, countdown đóng đăng ký lúc 23:59 ngày 15/09/2026, form và tài sản tự host.
- `course/curriculum/`: giáo án giảng viên và lộ trình 6 tuần.
- `course/workbook/`: workbook học viên và biểu mẫu thực hành.
- `course/workshop/`: nội dung workshop mở bán.
- `course/launch/`: kế hoạch nội dung, bài viết, video demo và case study.
- `course/onboarding/`: intake, quyền riêng tư và đặc tả đăng ký.
- `course/dist/` và `dist/`: PDF/PPTX đã xuất và kiểm tra.
- `backend/`: API đăng ký riêng tư cùng cấu hình systemd.
- `docs/superpowers/specs/`: đề án và quy hoạch khóa học.
- `tests/`: kiểm thử website, form, API, giáo án và tài liệu.

## Chạy local

```bash
python3 -m http.server 8100
```

Mở `http://127.0.0.1:8100/ai-learning/`.

## Kiểm thử

```bash
uv run --with pytest --with reportlab --with pypdf --with python-pptx pytest tests -q
node --check ai-learning/app.js
python3 -m py_compile backend/*.py course/scripts/*.py
git diff --check
```

## Triển khai

GitHub Pages phát trực tiếp từ branch `main`, thư mục gốc. `CNAME` cấu hình `khanh.design`; `www` trỏ về GitHub Pages và chuyển về apex. Subdomain `hkm.khanh.design` được giữ độc lập, không thuộc phạm vi repo này.

Landing page tĩnh chạy trên GitHub Pages. API form chạy tách biệt trên VPS, chỉ bind loopback và được đưa ra HTTPS qua tunnel; frontend luôn giữ email fallback nếu API tạm lỗi.

## Nguyên tắc dữ liệu

Form chỉ thu họ tên, số điện thoại, ngành nghề, mong muốn khi tham gia và xác nhận đồng ý xử lý dữ liệu. Không lưu mật khẩu, OTP, hợp đồng hoặc dữ liệu khách hàng; phản hồi API không trả lại PII.
