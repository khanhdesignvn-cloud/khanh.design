from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT / "course"
CURRICULUM = COURSE / "curriculum"
WORKBOOK = COURSE / "workbook"
DIST = COURSE / "dist"
CURRICULUM_PDF = DIST / "04-09-2026-Giao-an-chi-tiet-Horus-AI-Van-hanh-doanh-nghiep.pdf"
CURRICULUM_DOCX = DIST / "04-09-2026-Giao-an-chi-tiet-Horus-AI-Van-hanh-doanh-nghiep.docx"
WORKBOOK_PDF = DIST / "04-09-2026-Workbook-AI-Van-hanh-doanh-nghiep.pdf"

REQUIRED_WEEK_SECTIONS = (
    "Mục tiêu đo được",
    "Agenda 150 phút",
    "Dữ liệu mẫu cho demo",
    "Kịch bản demo",
    "Thực hành có hướng dẫn",
    "Rubric đánh giá",
    "Bài tập về nhà",
    "Quyền riêng tư và bảo mật",
    "Lỗi thường gặp",
)

TEMPLATE_NAMES = {
    "ban-do-co-hoi-ai.md",
    "ho-so-doanh-nghiep.md",
    "tieu-chi-danh-gia-dau-ra.md",
    "lich-noi-dung-da-kenh.md",
    "kich-ban-ban-hang.md",
    "faq-chuyen-cap.md",
    "sop.md",
    "workflow-ban-giao.md",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def agenda_total(text: str) -> int:
    block_match = re.search(
        r"## Agenda 150 phút(?P<body>.*?)(?=\n## )", text, flags=re.DOTALL
    )
    assert block_match, "Thiếu mục agenda"
    minutes = re.findall(r"^\|\s*\d+\s*\|[^|]+\|\s*(\d+)\s*\|", block_match["body"], re.MULTILINE)
    assert len(minutes) >= 5, "Agenda phải có ít nhất 5 chặng"
    return sum(map(int, minutes))


def pdf_reader(path: Path):
    pypdf = pytest.importorskip("pypdf")
    assert path.exists(), f"Chưa tạo PDF: {path}"
    return pypdf.PdfReader(str(path))


def extracted_text(reader) -> str:
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def embedded_base_fonts(reader) -> set[str]:
    fonts: set[str] = set()
    for page in reader.pages:
        resources = page.get("/Resources") or {}
        for font_ref in (resources.get("/Font") or {}).values():
            font = font_ref.get_object()
            descriptor_ref = font.get("/FontDescriptor")
            if descriptor_ref:
                descriptor = descriptor_ref.get_object()
                if any(key in descriptor for key in ("/FontFile", "/FontFile2", "/FontFile3")):
                    fonts.add(str(font.get("/BaseFont", "")))
    return fonts


def test_six_complete_week_guides_have_required_sections_and_150_minutes():
    week_files = sorted(CURRICULUM.glob("week-*.md"))
    assert [path.name for path in week_files] == [f"week-{n:02d}.md" for n in range(1, 7)]

    for number, path in enumerate(week_files, start=1):
        text = read(path)
        assert f"# Tuần {number}" in text
        for heading in REQUIRED_WEEK_SECTIONS:
            assert f"## {heading}" in text, f"{path.name} thiếu {heading}"
        assert agenda_total(text) == 150, f"{path.name} không đủ đúng 150 phút"
        assert len(text) >= 6_000, f"{path.name} quá ngắn, có dấu hiệu là placeholder"
        assert not re.search(r"\b(TODO|TBD|placeholder|lorem ipsum)\b", text, re.IGNORECASE)
        assert "Đạt" in text and "Cần sửa" in text


def test_facilitator_guide_is_actionable_and_covers_all_weeks():
    text = read(CURRICULUM / "facilitator-guide.md")
    for phrase in (
        "Trước khóa học",
        "Nhịp điều phối 150 phút",
        "AI Clinic",
        "Xử lý dữ liệu nhạy cảm",
        "Phản hồi theo rubric",
        "Kế hoạch dự phòng",
    ):
        assert phrase in text
    for number in range(1, 7):
        assert f"Tuần {number}" in text
    assert len(text) >= 7_000


def test_workbook_has_all_templates_and_safe_fillable_prompts():
    source = read(WORKBOOK / "workbook-source.md")
    actual_templates = {path.name for path in (WORKBOOK / "templates").glob("*.md")}
    assert actual_templates == TEMPLATE_NAMES
    assert len(source) >= 15_000
    for number in range(1, 7):
        assert f"Tuần {number}" in source
    for path in (WORKBOOK / "templates").glob("*.md"):
        text = read(path)
        assert len(text) >= 1_000, f"{path.name} chưa đủ hữu dụng"
        assert "Không điền" in text or "không điền" in text
    combined = source + "\n" + "\n".join(read(path) for path in (WORKBOOK / "templates").glob("*.md"))
    assert "mật khẩu" in combined.lower()
    assert "token" in combined.lower()
    assert "dữ liệu khách hàng thật" in combined.lower()


def test_renderers_explicitly_use_embedded_unicode_fonts():
    workbook = read(COURSE / "scripts" / "render_workbook.py")
    assert "DejaVuSans.ttf" in workbook
    assert "DejaVuSans-Bold.ttf" in workbook
    assert "TTFont" in workbook

    curriculum = read(COURSE / "scripts" / "render_curriculum_horus.py")
    for font in ("GoogleSansFlex-400.ttf", "GoogleSansFlex-500.ttf", "GoogleSansFlex-700.ttf"):
        assert font in curriculum
        assert (COURSE / "assets" / font).exists()
    assert "TTFont" in curriculum


def test_renderers_complete_without_unresolved_toc_entries(tmp_path):
    pytest.importorskip("reportlab")
    output = tmp_path / "workbook.pdf"
    result = subprocess.run(
        [sys.executable, str(COURSE / "scripts" / "render_workbook.py"), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stderr
    assert output.exists() and output.stat().st_size > 10_000


def test_horus_curriculum_renderer_completes_with_pdf_and_docx(tmp_path):
    pytest.importorskip("reportlab")
    pytest.importorskip("docx")
    pdf = tmp_path / "curriculum.pdf"
    docx = tmp_path / "curriculum.docx"
    result = subprocess.run(
        [sys.executable, str(COURSE / "scripts" / "render_curriculum_horus.py"), "--pdf", str(pdf), "--docx", str(docx)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert pdf.exists() and pdf.stat().st_size > 100_000
    assert docx.exists() and docx.stat().st_size > 40_000


def test_curriculum_pdf_has_vietnamese_text_toc_pages_and_embedded_font():
    reader = pdf_reader(CURRICULUM_PDF)
    text = extracted_text(reader)
    assert len(reader.pages) >= 30
    for phrase in ("MỤC LỤC", "Tuần 1", "Tuần 6", "Quyền riêng tư", "Bài tập về nhà", "TÀI LIỆU DÙNG KHI ĐỨNG LỚP"):
        assert phrase.lower() in text.lower()
    assert "AI VẬN HÀNH DOANH NGHIỆP" in text
    assert len(text) >= 70_000
    assert any("GoogleSansFlex" in name for name in embedded_base_fonts(reader))
    assert CURRICULUM_DOCX.exists() and CURRICULUM_DOCX.stat().st_size > 40_000


def test_workbook_pdf_has_vietnamese_text_room_to_write_and_embedded_font():
    reader = pdf_reader(WORKBOOK_PDF)
    text = extracted_text(reader)
    assert len(reader.pages) >= 28
    for phrase in (
        "WORKBOOK HỌC VIÊN",
        "Bản đồ cơ hội AI",
        "Hồ sơ doanh nghiệp",
        "Lịch nội dung đa kênh",
        "Kịch bản bán hàng",
        "Sơ đồ workflow",
        "Checklist bàn giao",
    ):
        assert phrase in text
    assert len(text) >= 20_000
    assert any("DejaVu" in name for name in embedded_base_fonts(reader))
