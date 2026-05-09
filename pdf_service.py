"""
PDF Generation Service
Builds professional PDFs from AI-generated content
"""
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Image, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from io import BytesIO
import os

# ── Color Palette ──
DARK     = colors.HexColor("#0f0f1a")
ACCENT   = colors.HexColor("#6c2eff")
ACCENT2  = colors.HexColor("#00e5b0")
LIGHT_BG = colors.HexColor("#f8f8fc")
MID_GRAY = colors.HexColor("#6b6b80")
WHITE    = colors.white

def build_ebook_pdf(data: dict) -> bytes:
    """Build a professional ebook PDF"""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        rightMargin=1*inch, leftMargin=1*inch,
        topMargin=1*inch, bottomMargin=0.75*inch,
        title=data.get("title","Ebook"),
        author=data.get("author","ProductAI")
    )

    styles = getSampleStyleSheet()

    # Custom styles
    cover_title = ParagraphStyle("CoverTitle", parent=styles["Title"],
        fontSize=36, textColor=WHITE, alignment=TA_CENTER,
        fontName="Helvetica-Bold", spaceAfter=16, leading=44)
    cover_sub = ParagraphStyle("CoverSub", parent=styles["Normal"],
        fontSize=16, textColor=ACCENT2, alignment=TA_CENTER, spaceAfter=8)
    chapter_head = ParagraphStyle("ChapterHead", parent=styles["Heading1"],
        fontSize=22, textColor=ACCENT, fontName="Helvetica-Bold",
        spaceAfter=12, spaceBefore=24, borderPad=4)
    body_text = ParagraphStyle("Body", parent=styles["Normal"],
        fontSize=11, leading=18, textColor=DARK, alignment=TA_JUSTIFY, spaceAfter=10)
    toc_item = ParagraphStyle("TOC", parent=styles["Normal"],
        fontSize=11, leading=18, textColor=DARK)

    story = []

    # ── COVER PAGE ──
    # Background rectangle via canvas callback not possible in platypus directly,
    # so we use a colored table as cover
    cover_data = [[Paragraph(data.get("title","Untitled"), cover_title)]]
    cover_table = Table(cover_data, colWidths=[6.5*inch], rowHeights=[3*inch])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), DARK),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("ROUNDEDCORNERS", [10]),
        ("TOPPADDING", (0,0), (-1,-1), 40),
        ("BOTTOMPADDING", (0,0), (-1,-1), 40),
    ]))
    story.append(Spacer(1, 1*inch))
    story.append(cover_table)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(data.get("subtitle",""), cover_sub))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"By {data.get('author','ProductAI')}", ParagraphStyle("auth",
        parent=styles["Normal"], fontSize=12, textColor=MID_GRAY, alignment=TA_CENTER)))
    story.append(PageBreak())

    # ── TABLE OF CONTENTS ──
    story.append(Paragraph("Table of Contents", chapter_head))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=16))
    for ch in data.get("chapters", []):
        toc_row = [[
            Paragraph(f"Chapter {ch['number']}: {ch['title']}", toc_item),
            Paragraph(str(ch['number'] * 3 + 2), ParagraphStyle("pg",
                parent=styles["Normal"], fontSize=11, alignment=1))
        ]]
        t = Table(toc_row, colWidths=[5.5*inch, 1*inch])
        t.setStyle(TableStyle([
            ("LINEBELOW", (0,0), (-1,-1), 0.5, colors.HexColor("#e0e0e8")),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ]))
        story.append(t)
    story.append(PageBreak())

    # ── CHAPTERS ──
    for ch in data.get("chapters", []):
        story.append(Paragraph(f"Chapter {ch['number']}", ParagraphStyle("chnum",
            parent=styles["Normal"], fontSize=11, textColor=ACCENT2,
            fontName="Helvetica", spaceAfter=4)))
        story.append(Paragraph(ch["title"], chapter_head))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=16))

        content = ch.get("content", ch.get("summary", ""))
        for para in content.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), body_text))

        if ch.get("key_takeaways"):
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("Key Takeaways", ParagraphStyle("kth",
                parent=styles["Normal"], fontSize=13, textColor=ACCENT,
                fontName="Helvetica-Bold", spaceAfter=8)))
            items = [ListItem(Paragraph(t, body_text)) for t in ch["key_takeaways"]]
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=20))

        story.append(PageBreak())

    # ── RESOURCES ──
    if data.get("resources"):
        story.append(Paragraph("Resources & References", chapter_head))
        story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=16))
        for i, r in enumerate(data["resources"], 1):
            story.append(Paragraph(f"{i}. {r}", body_text))

    doc.build(story)
    return buf.getvalue()


def build_audiobook_pdf(data: dict) -> bytes:
    """Build a publisher-grade audiobook PDF with full template"""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=1.1*inch, leftMargin=1.1*inch,
        topMargin=1*inch, bottomMargin=0.9*inch
    )

    styles = getSampleStyleSheet()
    title_s = ParagraphStyle("ABTitle", fontSize=28, textColor=DARK,
        fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=8, leading=34)
    sub_s = ParagraphStyle("ABSub", fontSize=14, textColor=MID_GRAY,
        alignment=TA_CENTER, spaceAfter=6, fontName="Helvetica-Oblique")
    ch_s = ParagraphStyle("ABChapter", fontSize=18, textColor=ACCENT,
        fontName="Helvetica-Bold", spaceAfter=10, spaceBefore=20)
    body_s = ParagraphStyle("ABBody", fontSize=10.5, leading=17,
        textColor=DARK, alignment=TA_JUSTIFY, spaceAfter=8)
    footnote_s = ParagraphStyle("Footnote", fontSize=8, textColor=MID_GRAY,
        fontName="Helvetica-Oblique", spaceAfter=4)

    story = []

    # Cover
    story.append(Spacer(1, 1.2*inch))
    story.append(Paragraph(data.get("title","Audiobook"), title_s))
    story.append(Paragraph(data.get("subtitle",""), sub_s))
    story.append(Spacer(1, 0.2*inch))
    story.append(HRFlowable(width="60%", thickness=2, color=ACCENT, hAlign="CENTER"))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("ProductAI Publisher · First Edition", ParagraphStyle("edition",
        fontSize=10, textColor=MID_GRAY, alignment=TA_CENTER)))
    story.append(Paragraph(f"Estimated Runtime: {data.get('total_runtime_estimate','—')}", ParagraphStyle("rt",
        fontSize=10, textColor=ACCENT2, alignment=TA_CENTER, spaceBefore=6)))
    story.append(PageBreak())

    # TOC
    story.append(Paragraph("Table of Contents", ch_s))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=12))
    story.append(Paragraph("Introduction", ParagraphStyle("toci",
        fontSize=11, leading=20, textColor=DARK)))
    for ch in data.get("chapters",[]):
        story.append(Paragraph(
            f"Chapter {ch['number']}: {ch['title']}  ·  {ch.get('runtime_estimate','')}",
            ParagraphStyle("tocch", fontSize=11, leading=20, textColor=DARK, leftIndent=12)
        ))
    story.append(Paragraph("Bibliography & Resources", ParagraphStyle("tocbi",
        fontSize=11, leading=20, textColor=DARK)))
    story.append(PageBreak())

    # Introduction
    if data.get("introduction"):
        story.append(Paragraph("Introduction", ch_s))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT2, spaceAfter=10))
        story.append(Paragraph(data["introduction"], body_s))
        story.append(PageBreak())

    # Chapters
    for ch in data.get("chapters",[]):
        story.append(Paragraph(f"Chapter {ch['number']}", ParagraphStyle("chnum2",
            fontSize=10, textColor=ACCENT2, spaceAfter=2)))
        story.append(Paragraph(ch["title"], ch_s))
        if ch.get("runtime_estimate"):
            story.append(Paragraph(f"⏱ Estimated runtime: {ch['runtime_estimate']}",
                ParagraphStyle("rt2", fontSize=9, textColor=MID_GRAY, spaceAfter=6,
                    fontName="Helvetica-Oblique")))
        if ch.get("narrator_notes"):
            note_data = [[Paragraph(f"🎙 Narrator: {ch['narrator_notes']}", ParagraphStyle("nn",
                fontSize=9, textColor=ACCENT2, fontName="Helvetica-Oblique"))]]
            nt = Table(note_data, colWidths=[5.8*inch])
            nt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#f0f8ff")),
                ("BOX",(0,0),(-1,-1),0.5,ACCENT2), ("TOPPADDING",(0,0),(-1,-1),6),
                ("BOTTOMPADDING",(0,0),(-1,-1),6), ("LEFTPADDING",(0,0),(-1,-1),10)]))
            story.append(nt)
            story.append(Spacer(1, 0.1*inch))

        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e8"), spaceAfter=10))
        content = ch.get("content","")
        for para in content.split("\n\n"):
            if para.strip():
                story.append(Paragraph(para.strip(), body_s))

        if ch.get("key_takeaways"):
            story.append(Spacer(1, 0.15*inch))
            kd = [[Paragraph("Key Takeaways", ParagraphStyle("kh",
                fontSize=11, fontName="Helvetica-Bold", textColor=WHITE))]]
            kt_head = Table(kd, colWidths=[5.8*inch])
            kt_head.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),ACCENT),
                ("TOPPADDING",(0,0),(-1,-1),8), ("BOTTOMPADDING",(0,0),(-1,-1),8),
                ("LEFTPADDING",(0,0),(-1,-1),12)]))
            story.append(kt_head)
            for takeaway in ch["key_takeaways"]:
                story.append(Paragraph(f"• {takeaway}", ParagraphStyle("kt2",
                    fontSize=10, leading=16, textColor=DARK, leftIndent=12, spaceAfter=4)))
        story.append(PageBreak())

    # Conclusion
    if data.get("conclusion"):
        story.append(Paragraph("Conclusion", ch_s))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=10))
        story.append(Paragraph(data["conclusion"], body_s))
        story.append(PageBreak())

    # Bibliography
    if data.get("bibliography"):
        story.append(Paragraph("Bibliography & Resources", ch_s))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=10))
        for i, ref in enumerate(data["bibliography"], 1):
            story.append(Paragraph(f"{i}. {ref}", footnote_s))

    doc.build(story)
    return buf.getvalue()
