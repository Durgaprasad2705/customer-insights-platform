from typing import Any
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import TableStyle

# ─── Colour palette ──────────────────────────────────────────────────────────
C_INDIGO  = colors.HexColor("#6366F1")
C_VIOLET  = colors.HexColor("#A855F7")
C_GREEN   = colors.HexColor("#10B981")
C_AMBER   = colors.HexColor("#F59E0B")
C_DARK    = colors.HexColor("#0F172A")
C_NAVY    = colors.HexColor("#1E293B")
C_TEXT    = colors.HexColor("#334155")
C_MUTED   = colors.HexColor("#64748B")
C_BG      = colors.HexColor("#F8FAFC")
C_BG2     = colors.HexColor("#F1F5F9")
C_BORDER  = colors.HexColor("#E2E8F0")
C_WHITE   = colors.white

# ─── Shared Table Style ───────────────────────────────────────────────────────
def get_table_style(header_color: Any, alt: bool = True) -> TableStyle:
    cmds = [
        ("BACKGROUND",    (0, 0), (-1, 0),  header_color),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  C_WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
        ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -1), 8.5),
        ("TEXTCOLOR",     (0, 1), (-1, -1), C_TEXT),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_BG, C_BG2] if alt else [C_BG]),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    return TableStyle(cmds)

def get_pdf_styles():
    styles = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "RPTitle", parent=styles["Heading1"],
            fontName="Helvetica-Bold", fontSize=26,
            textColor=C_INDIGO, leading=30, spaceAfter=6,
        ),
        "cov_sub": ParagraphStyle(
            "CovSub", parent=styles["Normal"],
            fontName="Helvetica", fontSize=12,
            textColor=C_MUTED, spaceAfter=6,
        ),
        "sec": ParagraphStyle(
            "RPSec", parent=styles["Heading2"],
            fontName="Helvetica-Bold", fontSize=13,
            textColor=C_INDIGO, spaceBefore=16, spaceAfter=8,
        ),
        "sub_sec": ParagraphStyle(
            "RPSubSec", parent=styles["Heading3"],
            fontName="Helvetica-Bold", fontSize=10,
            textColor=C_NAVY, spaceBefore=10, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "RPBody", parent=styles["Normal"],
            fontName="Helvetica", fontSize=9,
            textColor=C_TEXT, leading=13,
        ),
        "caption": ParagraphStyle(
            "RPCaption", parent=styles["Normal"],
            fontName="Helvetica-Oblique", fontSize=8,
            textColor=C_MUTED, spaceAfter=6, alignment=1,  # centred
        ),
        "kpi_val": ParagraphStyle(
            "KPIVal", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=16,
            textColor=C_INDIGO, leading=20,
        ),
        "kpi_lbl": ParagraphStyle(
            "KPILbl", parent=styles["Normal"],
            fontName="Helvetica", fontSize=8,
            textColor=C_MUTED,
        ),
        "footer": ParagraphStyle(
            "Footer", parent=styles["Normal"],
            fontName="Helvetica-Oblique", fontSize=8,
            textColor=C_MUTED, alignment=1
        ),
        "banner": ParagraphStyle(
            "Ban", parent=styles["Normal"],
            fontName="Helvetica-Bold", fontSize=28,
            textColor=C_INDIGO, leading=34
        )
    }

def hex_color(c: Any) -> str:
    """Return 6-char hex string from a ReportLab colour (no leading #)."""
    try:
        r, g, b = int(c.red * 255), int(c.green * 255), int(c.blue * 255)
        return f"{r:02X}{g:02X}{b:02X}"
    except Exception:
        return "334155"
