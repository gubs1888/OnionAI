"""
REPORT GENERATION SERVICE — builds the assessment PDF (ReportLab).

Rules:
  * Reports generated from DEMO assessments carry a prominent
    "DEMO DATA — NOT FOR OFFICIAL USE" banner.
  * ReportLab is imported lazily so the API can start even without it
    (endpoint returns 501 in that case instead of crashing).
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm.session import Session

from app.config import settings, BACKEND_ROOT
from app.models.image import Image
from app.models.detection import Detection


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
        from reportlab.platypus import Image as RLImage
        from reportlab.lib.utils import ImageReader
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
    warning_style = ParagraphStyle(
        "WARN", parent=styles["Heading3"], textColor=colors.black,
        backColor=colors.HexColor("#FBBF24"), alignment=1, spaceBefore=6, spaceAfter=10,
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
        
    if assessment.avg_confidence < 0.70:
        story.append(Paragraph("⚠ LOW CONFIDENCE ASSESSMENT — Please recapture image or verify manually", warning_style))

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
    story += [meta, Spacer(1, 6 * mm)]

    # --- Draw Bounding Boxes ---
    tmp_path = None
    try:
        db = Session.object_session(assessment)
        if db and assessment.image_id:
            img_row = db.get(Image, assessment.image_id)
            if img_row:
                detections = db.query(Detection).filter(Detection.image_id == img_row.id).all()
                img_path = str(BACKEND_ROOT / img_row.file_path)
                if os.path.exists(img_path):
                    import cv2
                    img_array = cv2.imread(img_path)
                    if img_array is not None:
                        color_map = {
                            "onion": (0, 255, 0),     # Green (Healthy)
                            "damaged": (0, 255, 255), # Yellow
                            "rotten": (0, 0, 255),    # Red
                            "sprouted": (255, 0, 0),  # Blue
                        }
                        for det in detections:
                            color = color_map.get(det.class_name, (255, 255, 255))
                            if det.bbox and len(det.bbox) == 4:
                                x1, y1, x2, y2 = map(int, det.bbox)
                                cv2.rectangle(img_array, (x1, y1), (x2, y2), color, 3)
                                label = f"{det.class_name} {det.confidence:.2f}"
                                cv2.putText(img_array, label, (x1, max(y1 - 10, 0)), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)
                        
                        fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
                        os.close(fd)
                        cv2.imwrite(tmp_path, img_array)
                        
                        img_reader = ImageReader(tmp_path)
                        img_w, img_h = img_reader.getSize()
                        aspect = img_h / float(img_w)
                        display_width = 150 * mm
                        display_height = display_width * aspect
                        if display_height > 90 * mm:  # Constrain height so it fits on page 1 easily
                            display_height = 90 * mm
                            display_width = display_height / aspect
                        
                        story.append(RLImage(tmp_path, width=display_width, height=display_height))
                        story.append(Spacer(1, 6 * mm))
    except Exception as e:
        print(f"Failed to generate annotated image: {e}")
        pass

    # --- Calculations ---
    total = assessment.total_onions
    grade_a_pct = (assessment.healthy / total * 100) if total > 0 else 0
    damaged_pct = (assessment.damaged / total * 100) if total > 0 else 0
    rotten_pct = (assessment.rotten / total * 100) if total > 0 else 0
    sprouted_pct = (assessment.sprouted / total * 100) if total > 0 else 0
    undersized_pct = (assessment.undersized / total * 100) if total > 0 else 0

    # --- Breakdown Table ---
    story.append(Paragraph("Quality Category Breakdown", styles["Heading3"]))
    breakdown_rows = [
        ["Quality Category", "Count", "Percentage"],
        ["Grade A (Healthy)", str(assessment.healthy), f"{grade_a_pct:.1f}%"],
        ["Damaged", str(assessment.damaged), f"{damaged_pct:.1f}%"],
        ["Rotten", str(assessment.rotten), f"{rotten_pct:.1f}%"],
        ["Sprouted", str(assessment.sprouted), f"{sprouted_pct:.1f}%"],
        ["Undersized / URS", str(assessment.undersized), f"{undersized_pct:.1f}%"],
    ]
    b_table = Table(breakdown_rows, colWidths=[70 * mm, 42 * mm, 43 * mm])
    b_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ])
    )
    story += [b_table, Spacer(1, 6 * mm)]

    # --- Overall Metrics ---
    story.append(Paragraph("Overall Quality Metrics", styles["Heading3"]))
    metrics_rows = [
        ["Metric", "Value"],
        ["Total onions", str(total)],
        ["Grade A %", f"{grade_a_pct:.1f}%"],
        ["URS %", f"{assessment.urs_percentage:.1f}%"],
        ["Avg AI Confidence", f"{assessment.avg_confidence * 100:.1f}%"],
    ]
    m_table = Table(metrics_rows, colWidths=[75 * mm, 80 * mm])
    m_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16A34A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("FONTSTYLE", (0, 1), (0, -1), "Bold"),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ])
    )
    story += [m_table, Spacer(1, 6 * mm)]

    # --- Reasons ---
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

    try:
        doc.build(story)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return pdf_path
