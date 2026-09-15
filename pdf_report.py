from io import BytesIO
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# Use a portable Unicode font instead of a fixed C:\Windows path.
_FONT_CANDIDATES = [
    Path(__file__).with_name("DejaVuSans.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]
_FONT_NAME = "Helvetica"
for _font_path in _FONT_CANDIDATES:
    if _font_path.exists():
        try:
            pdfmetrics.registerFont(TTFont("GreekFont", str(_font_path)))
            _FONT_NAME = "GreekFont"
            break
        except Exception:
            pass


def dataframe_table(df: pd.DataFrame):
    if df is None or df.empty:
        return Paragraph("Δεν υπάρχουν δεδομένα.", ParagraphStyle("empty", fontName=_FONT_NAME))

    data = [[str(v) for v in df.columns]] + [[str(v) for v in row] for row in df.fillna("").values.tolist()]
    table = Table(data, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, -1), _FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return table


def create_project_pdf(elements_df, project_order_df, summary_df, technical_drawings=None, input_df=None, calculation_df=None):
    """Create the project report, optionally including one technical PNG per element."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=24,
        leftMargin=24,
        topMargin=24,
        bottomMargin=24,
        title="Αναφορά έργου GUNITE",
        author="GUNITE",
    )

    styles = getSampleStyleSheet()
    for style_name in ("Title", "Heading2", "BodyText"):
        styles[style_name].fontName = _FONT_NAME
    styles["Title"].fontSize = 18
    styles["Heading2"].fontSize = 12
    styles["BodyText"].fontSize = 9

    story = [
        Paragraph("ΑΝΑΦΟΡΑ ΕΡΓΟΥ GUNITE", styles["Title"]),
        Spacer(1, 12),
        Paragraph("Στοιχεία έργου", styles["Heading2"]),
        dataframe_table(elements_df),
        Spacer(1, 10),
        *( [Paragraph("Είσοδοι", styles["Heading2"]), dataframe_table(input_df), Spacer(1, 10)] if input_df is not None and not input_df.empty else [] ),
        *( [Paragraph("Υπολογισμοί", styles["Heading2"]), dataframe_table(calculation_df), Spacer(1, 10)] if calculation_df is not None and not calculation_df.empty else [] ),
        Paragraph("Συγκεντρωτική παραγγελία", styles["Heading2"]),
        dataframe_table(summary_df),
        Spacer(1, 14),
        Paragraph("Αναλυτική παραγγελία", styles["Heading2"]),
        dataframe_table(project_order_df),
    ]

    if technical_drawings:
        story.append(PageBreak())
        story.append(Paragraph("Τεχνικά σχέδια", styles["Heading2"]))
        story.append(Spacer(1, 8))
        for index, image_bytes in enumerate(technical_drawings, start=1):
            if not image_bytes:
                continue
            image_stream = BytesIO(image_bytes)
            img = Image(image_stream, width=550, height=390, kind="proportional")
            story.append(img)
            if index < len(technical_drawings):
                story.append(PageBreak())

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
