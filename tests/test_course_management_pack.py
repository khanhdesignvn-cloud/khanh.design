from html import unescape
from pathlib import Path
from zipfile import ZipFile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "course" / "dist"
PREFIX = "04-09-2026"

OPS_DOCX = DIST / f"{PREFIX}-So-tay-van-hanh-khoa-hoc-AI.docx"
OPS_PDF = DIST / f"{PREFIX}-So-tay-van-hanh-khoa-hoc-AI.pdf"
SHARE_DOCX = DIST / f"{PREFIX}-Chuong-trinh-hoc-AI-Van-hanh-doanh-nghiep.docx"
SHARE_PDF = DIST / f"{PREFIX}-Chuong-trinh-hoc-AI-Van-hanh-doanh-nghiep.pdf"
TRACKER = DIST / f"{PREFIX}-Lich-hoc-va-quan-ly-cohort-AI.xlsx"


def package_text(path: Path) -> str:
    with ZipFile(path) as archive:
        assert archive.testzip() is None
        return unescape("\n".join(
            archive.read(name).decode("utf-8", "ignore")
            for name in archive.namelist()
            if name.endswith(".xml")
        ))


def pdf_text(path: Path) -> tuple[int, str]:
    reader = PdfReader(str(path))
    return len(reader.pages), "\n".join(page.extract_text() or "" for page in reader.pages)


def test_management_pack_files_exist_and_office_packages_are_healthy():
    for path in [OPS_DOCX, OPS_PDF, SHARE_DOCX, SHARE_PDF, TRACKER]:
        assert path.exists()
        assert path.stat().st_size > 10_000
    for path in [OPS_DOCX, SHARE_DOCX, TRACKER]:
        assert package_text(path)


def test_internal_handbook_covers_end_to_end_course_operations():
    pages, text = pdf_text(OPS_PDF)
    assert pages >= 4
    for phrase in [
        "Quy trình xử lý học viên mới",
        "Lịch cohort dự kiến",
        "Chương trình và sản phẩm từng tuần",
        "Trạng thái quản lý chuẩn",
        "Sự cố và phương án dự phòng",
        "AI Clinic tốt nghiệp",
    ]:
        assert phrase in text


def test_shareable_program_contains_schedule_curriculum_and_policies():
    pages, text = pdf_text(SHARE_PDF)
    assert pages >= 3
    for phrase in [
        "CHƯƠNG TRÌNH HỌC 6 TUẦN",
        "26/09/2026",
        "Tự động hóa và bàn giao hệ thống",
        "3.900.000",
        "4.900.000",
        "Nộp hồ sơ không bảo đảm nhận lớp",
    ]:
        assert phrase in text


def test_tracker_has_all_management_sheets_and_no_prefilled_student_pii():
    xml = package_text(TRACKER)
    for sheet in [
        "Dashboard",
        "Học viên",
        "Lịch học",
        "Tiến độ",
        "Công việc vận hành",
        "Chương trình 6 tuần",
        "Chỉ mục tài liệu",
    ]:
        assert sheet in xml
    assert "DỰ KIẾN" in xml
    assert "SẴN SÀNG" in xml
    assert "ĐÃ THANH TOÁN" in xml
    assert "0912 345 678" not in xml
    assert "Nguyễn Văn An" not in xml
