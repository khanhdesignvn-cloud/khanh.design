#!/usr/bin/env python3
"""Kết xuất workbook học viên thành PDF Unicode có vùng thực hành."""
from __future__ import annotations

import argparse
import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "_course" / "workbook"
OUTPUT = ROOT / "_course" / "dist" / "04-09-2026-Workbook-AI-Van-hanh-doanh-nghiep.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
REGULAR = FONT_DIR / "DejaVuSans.ttf"
BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"

GOLD = colors.HexColor("#B08D57")
INK = colors.HexColor("#171717")
MUTED = colors.HexColor("#5B5B5B")
IVORY = colors.HexColor("#F7F2E8")
LINE = colors.HexColor("#D8D0C2")


def register_fonts() -> None:
    if not REGULAR.exists() or not BOLD.exists():
        raise FileNotFoundError("Cần font DejaVuSans.ttf và DejaVuSans-Bold.ttf")
    pdfmetrics.registerFont(TTFont("DejaVu", str(REGULAR)))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(BOLD)))
    pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")


def styles():
    sheet = getSampleStyleSheet()
    return {
        "CoverTitle": ParagraphStyle("CoverTitle", fontName="DejaVu-Bold", fontSize=25, leading=32, textColor=INK, alignment=TA_CENTER, spaceAfter=10 * mm),
        "CoverSub": ParagraphStyle("CoverSub", fontName="DejaVu", fontSize=12, leading=19, textColor=MUTED, alignment=TA_CENTER),
        "Heading1": ParagraphStyle("Heading1", fontName="DejaVu-Bold", fontSize=18, leading=24, textColor=INK, spaceBefore=5 * mm, spaceAfter=3 * mm, keepWithNext=True),
        "Heading2": ParagraphStyle("Heading2", fontName="DejaVu-Bold", fontSize=13, leading=18, textColor=GOLD, spaceBefore=4 * mm, spaceAfter=2 * mm, keepWithNext=True),
        "Heading3": ParagraphStyle("Heading3", fontName="DejaVu-Bold", fontSize=10.5, leading=15, textColor=INK, spaceBefore=3 * mm, spaceAfter=1.5 * mm, keepWithNext=True),
        "Body": ParagraphStyle("Body", fontName="DejaVu", fontSize=9.2, leading=14, textColor=INK, alignment=TA_LEFT, spaceAfter=2.2 * mm),
        "Bullet": ParagraphStyle("Bullet", fontName="DejaVu", fontSize=9.2, leading=14, leftIndent=5 * mm, firstLineIndent=-3 * mm, bulletIndent=1 * mm, textColor=INK, spaceAfter=1.4 * mm),
        "Quote": ParagraphStyle("Quote", fontName="DejaVu", fontSize=8.8, leading=13, leftIndent=6 * mm, rightIndent=4 * mm, borderColor=GOLD, borderWidth=1, borderPadding=5, textColor=MUTED, backColor=IVORY, spaceAfter=3 * mm),
        "Table": ParagraphStyle("Table", fontName="DejaVu", fontSize=7.4, leading=10, textColor=INK),
        "TOCHeading": ParagraphStyle("TOCHeading", fontName="DejaVu-Bold", fontSize=12, leading=18, leftIndent=0, textColor=INK, spaceBefore=2 * mm),
        "TOCSub": ParagraphStyle("TOCSub", fontName="DejaVu", fontSize=9, leading=14, leftIndent=7 * mm, textColor=MUTED),
    }


def inline(text: str) -> str:
    text = escape(text.strip())
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='DejaVu'>\1</font>", text)
    return text


def table_flow(rows: list[list[str]], st: dict) -> Table:
    count = max(len(row) for row in rows)
    normalized = [row + [""] * (count - len(row)) for row in rows]
    data = [[Paragraph(inline(cell), st["Table"]) for cell in row] for row in normalized]
    available = A4[0] - 36 * mm
    weights = []
    for col in range(count):
        longest = max(len(row[col]) for row in normalized)
        weights.append(max(1.0, min(4.0, longest / 20)))
    widths = [available * w / sum(weights) for w in weights]
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVu-Bold"),
        ("BACKGROUND", (0, 1), (-1, -1), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return table


def markdown_flows(text: str, st: dict, skip_first_h1: bool = False) -> list:
    flows: list = []
    lines = text.splitlines()
    i = 0
    first_h1_seen = False
    while i < len(lines):
        raw = lines[i].rstrip()
        line = raw.strip()
        if not line:
            i += 1
            continue
        if line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?[\s:|-]+\|?$", lines[i + 1].strip()):
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[\s:|-]+", cell or " ") for cell in cells):
                    rows.append(cells)
                i += 1
            flows.extend([table_flow(rows, st), Spacer(1, 3 * mm)])
            continue
        match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if match:
            level = len(match.group(1))
            title = match.group(2)
            if level == 1 and skip_first_h1 and not first_h1_seen:
                first_h1_seen = True
            else:
                flows.append(Paragraph(inline(title), st[f"Heading{level}"]))
                first_h1_seen = first_h1_seen or level == 1
            i += 1
            continue
        if line.startswith("> "):
            flows.append(Paragraph(inline(line[2:]), st["Quote"]))
            i += 1
            continue
        bullet = re.match(r"^[-*]\s+(.+)$", line)
        numbered = re.match(r"^(\d+)\.\s+(.+)$", line)
        if bullet:
            flows.append(Paragraph("• " + inline(bullet.group(1)), st["Bullet"]))
            i += 1
            continue
        if numbered:
            flows.append(Paragraph(numbered.group(1) + ". " + inline(numbered.group(2)), st["Bullet"]))
            i += 1
            continue
        paragraph = [line]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt or nxt.startswith(("#", "|", "> ", "- ", "* ")) or re.match(r"^\d+\.\s+", nxt):
                break
            paragraph.append(nxt)
            i += 1
        flows.append(Paragraph(inline(" ".join(paragraph)), st["Body"]))
    return flows


class WorkbookDoc(BaseDocTemplate):
    def __init__(self, filename: str, st: dict):
        super().__init__(filename, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=17 * mm, title="Workbook AI Vận Hành Doanh Nghiệp", author="khanh.design")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="body")
        self.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=self.draw_page))
        self._outline_seq = 0
        self.st = st

    def beforeDocument(self):
        # multiBuild renders several passes; bookmark keys must be stable.
        self._outline_seq = 0
        super().beforeDocument()

    def draw_page(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.line(18 * mm, 14 * mm, A4[0] - 18 * mm, 14 * mm)
        canvas.setFont("DejaVu", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(18 * mm, 9 * mm, "AI VẬN HÀNH DOANH NGHIỆP · Workbook học viên")
        canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f"Trang {doc.page}")
        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name in ("Heading1", "Heading2"):
            level = 0 if flowable.style.name == "Heading1" else 1
            title = flowable.getPlainText()
            key = f"h{self._outline_seq}"
            self._outline_seq += 1
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=level, closed=level == 0)
            self.notify("TOCEntry", (level, title, self.page, key))


def build(output: Path = OUTPUT) -> Path:
    register_fonts()
    st = styles()
    output.parent.mkdir(parents=True, exist_ok=True)
    toc = TableOfContents()
    toc.levelStyles = [st["TOCHeading"], st["TOCSub"]]
    story = [
        Spacer(1, 45 * mm),
        Paragraph("WORKBOOK HỌC VIÊN", st["CoverTitle"]),
        Paragraph("AI VẬN HÀNH DOANH NGHIỆP", st["CoverTitle"]),
        Paragraph("Xây bộ máy trợ lý AI với Claude trong 6 tuần", st["CoverSub"]),
        Spacer(1, 12 * mm),
        Paragraph("Cohort sáng lập · khanh.design · 04-09-2026", st["CoverSub"]),
        PageBreak(),
        Paragraph("MỤC LỤC", st["Heading1"]),
        Spacer(1, 4 * mm),
        toc,
        PageBreak(),
    ]
    sources = [SOURCE / "workbook-source.md"] + sorted((SOURCE / "templates").glob("*.md"))
    for idx, path in enumerate(sources):
        if idx:
            story.append(PageBreak())
            story.append(Paragraph("PHIẾU THỰC HÀNH", st["Heading3"]))
        flows = markdown_flows(path.read_text(encoding="utf-8"), st)
        expanded = []
        for flow in flows:
            expanded.append(flow)
            if isinstance(flow, Paragraph) and (
                "____" in flow.getPlainText() or flow.style.name == "Heading2"
            ):
                expanded.append(Spacer(1, 3 * mm))
        story.extend(expanded)
    story.extend([
        PageBreak(),
        Paragraph("GHI CHÚ VÀ QUYẾT ĐỊNH SAU KHÓA HỌC", st["Heading1"]),
        Paragraph("Ghi lại quyết định, giả định cần kiểm tra, người chịu trách nhiệm và ngày rà soát. Không ghi dữ liệu khách hàng thật, mật khẩu hoặc token.", st["Body"]),
        Spacer(1, 8 * mm),
        Paragraph("Quyết định 1: ________________________________________________________________", st["Body"]),
        Spacer(1, 12 * mm),
        Paragraph("Quyết định 2: ________________________________________________________________", st["Body"]),
        Spacer(1, 12 * mm),
        Paragraph("Rủi ro cần theo dõi: _________________________________________________________", st["Body"]),
        Spacer(1, 12 * mm),
        Paragraph("Người phụ trách: ________________________  Ngày rà soát: ________________________", st["Body"]),
        Spacer(1, 12 * mm),
        Paragraph("Bằng chứng cần thu thêm: _____________________________________________________", st["Body"]),
    ])
    doc = WorkbookDoc(str(output), st)
    doc.multiBuild(story)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = build(args.output)
    print(result)
