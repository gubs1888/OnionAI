"""
REPORT GENERATION SERVICE — builds the assessment PDF (ReportLab).

Rules:
  * Reports generated from DEMO assessments carry a prominent
    "DEMO DATA — NOT FOR OFFICIAL USE" banner.
  * ReportLab is imported lazily so the API can start even without it
    (endpoint returns 501 in that case instead of crashing).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.config import settings


class ReportGenerationError(RuntimeError):
    """Raised when the PDF cannot be generated."""


def generate_report(assessment, out_dir: Path | None = None) -> Path:
    """
    assessment: app.models.assessment.Assessment (with .batch relationship).
    returns:    Path to the generated PDF file.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:  # pragma: no cover
        raise ReportGenerationError(
            "reportlab is not installed — cannot generate PDF. "
            "pip install -r backend/requirements.txt"
        ) from exc

    out_dir = Path(out_dir or settings.report_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    batch_code = assessment.batch.batch_code
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_code = f"RPT-{assessment.id:04d}-{stamp}"
    pdf_path = out_dir / f"{report_code}.pdf"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("T", parent=styles["Title"], fontSize=18, spaceAfter=4)
    demo_style = ParagraphStyle(
        "DEMO", parent=styles["Heading3"], textColor=colors.white,
        backColor=colors.HexColor("#B91C1C"), alignment=1, spaceBefore=6, spaceAfter=10,
    )
    note_style = ParagraphStyle(
        "N", parent=styles["Italic"], fontSize=8, textColor=colors.HexColor("#555555")
    )

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=18 * mm)
    story: list = []

    story.append(Paragraph("Onion Quality Assessment Report", title_style))
    story.append(Paragraph(f"Report {report_code}", styles["Heading4"]))
    if assessment.is_demo:
        story.append(Paragraph("DEMO DATA — NOT REAL AI OUTPUT — NOT FOR OFFICIAL USE", demo_style))

    meta = Table(
        [
            ["Batch", batch_code],
            ["Batch name", assessment.batch.name or "-"],
            ["Assessment ID", str(assessment.id)],
            ["Generated at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Model / pipeline", assessment.model_version or "unknown"],
        ],
        colWidths=[45 * mm, 110 * mm],
    )
    meta.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.grey)]))
    story += [meta, Spacer(1, 8 * mm)]

    rows = [
        ["Metric", "Value"],
        ["Total onions", str(assessment.total_onions)],
        ["Healthy", str(assessment.healthy)],
        ["Damaged", str(assessment.damaged)],
        ["Rotten", str(assessment.rotten)],
        ["Sprouted", str(assessment.sprouted)],
        ["Undersized", str(assessment.undersized)],
        ["Defect %", f"{assessment.defect_percentage:.2f}"],
        ["Quality score", f"{assessment.quality_score:.1f} / 100"],
        ["Grade (MVP)", assessment.grade],
        ["URS %", f"{assessment.urs_percentage:.1f}"],
        ["Avg confidence", f"{assessment.avg_confidence * 100:.1f}%"],
    ]
    table = Table(rows, colWidths=[70 * mm, 85 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story += [Paragraph("Results", styles["Heading3"]), table, Spacer(1, 6 * mm)]

    reasons = list(assessment.reasons or [])
    story.append(Paragraph("Reasons / deductions", styles["Heading3"]))
    for reason in reasons or ["No deductions recorded."]:
        story.append(Paragraph(f"•  {reason}", styles["Normal"]))

    story += [
        Spacer(1, 8 * mm),
        Paragraph(
            "Grades and URS values are produced by THIS PROJECT'S MVP scoring logic "
            "(backend/config/grading_config.json). They are NOT official AGMARK/FSSAI "
            "grades until thresholds are verified by the team (docs/standards/).",
            note_style,
        ),
    ]

    doc.build(story)
    return pdf_path
