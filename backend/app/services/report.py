"""
REPORT GENERATION SERVICE — builds the assessment PDF (ReportLab).

POST-NCCF ARCHITECTURE:
  Reports now show NCCF-aligned grading breakdown:
    - Grade A count + %
    - Grade-URS count + %
    - Non-Qualifying count + %
    - Per-defect breakdown
    - Specification applied
    - Manual inspection flags

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


def format_defect_name(defect_name: str) -> str:
    """Convert raw defect class name to a clear human-readable string."""
    mapping = {
        "cut_crack": "Cut / Crack",
        "rotten": "Rotten",
        "damaged": "Damaged",
        "sprouted": "Sprouted",
        "smut": "Smut",
        "discoloured": "Discoloured",
        "fresh_roots": "Fresh Roots",
        "mechanical_injury": "Mechanical Injury",
        "slimy_soft_rot": "Soft Rot",
        "rot_rotting_fungal": "Fungal Rot",
        "double_misshape": "Misshaped",
    }
    return mapping.get(defect_name.lower(), defect_name.replace("_", " ").title())


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
    manual_style = ParagraphStyle(
        "MAN", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#92400E"),
    )

    doc = SimpleDocTemplate(str(pdf_path), pagesize=A4, topMargin=18 * mm)
    story: list = []

    story.append(Paragraph("Onion Quality Assessment Report", title_style))
    story.append(Paragraph(f"Report {report_code}", styles["Heading4"]))
    
    if assessment.is_demo:
        story.append(Paragraph("DEMO DATA — NOT REAL AI OUTPUT — NOT FOR OFFICIAL USE", demo_style))
        
    if assessment.avg_confidence < 0.70:
        story.append(Paragraph("⚠ LOW CONFIDENCE ASSESSMENT — Please recapture image", warning_style))

    meta = Table(
        [
            ["Batch", batch_code],
            ["Batch name", assessment.batch.name or "-"],
            ["Assessment ID", str(assessment.id)],
            ["Generated at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Model / pipeline", assessment.model_version or "unknown"],
            ["NCCF Specification", assessment.specification_id or "N/A"],
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
                            "onion": (0, 255, 0),       # Green (Healthy)
                            "damaged": (0, 255, 255),    # Yellow
                            "rotten": (0, 0, 255),       # Red
                            "sprouted": (255, 0, 0),     # Blue
                            "cut_crack": (0, 165, 255),  # Orange
                            "smut": (128, 0, 128),       # Purple
                            "discoloured": (255, 255, 0),# Cyan
                            "fresh_roots": (0, 128, 128),# Teal
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

    # --- NCCF Grading Breakdown (primary) ---
    total = assessment.total_onions
    grade_a_pct = (assessment.grade_a_count / total * 100) if total > 0 else 0
    grade_urs_pct = (assessment.grade_urs_count / total * 100) if total > 0 else 0
    non_qual_pct = (assessment.non_qualifying_count / total * 100) if total > 0 else 0

    story.append(Paragraph("NCCF Grade Breakdown", styles["Heading3"]))
    nccf_rows = [
        ["NCCF Grade", "Count", "Percentage"],
        ["Grade A", str(assessment.grade_a_count), f"{grade_a_pct:.1f}%"],
        ["Grade URS", str(assessment.grade_urs_count), f"{grade_urs_pct:.1f}%"],
        ["Non-Qualifying", str(assessment.non_qualifying_count), f"{non_qual_pct:.1f}%"],
        ["Total Onions", str(total), "100.0%"],
    ]
    nccf_table = Table(nccf_rows, colWidths=[70 * mm, 42 * mm, 43 * mm])
    nccf_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ])
    )
    story += [nccf_table, Spacer(1, 6 * mm)]

    # --- Defect Breakdown ---
    defect_breakdown = dict(assessment.defect_breakdown or {})
    if defect_breakdown:
        story.append(Paragraph("Defect Type Breakdown", styles["Heading3"]))
        defect_rows = [["Defect Type", "Count", "Percentage"]]
        for defect, count in sorted(defect_breakdown.items(), key=lambda x: -x[1]):
            pct = count / total * 100 if total > 0 else 0
            defect_rows.append([format_defect_name(defect), str(count), f"{pct:.1f}%"])
        d_table = Table(defect_rows, colWidths=[70 * mm, 42 * mm, 43 * mm])
        d_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#374151")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ])
        )
        story += [d_table, Spacer(1, 6 * mm)]

    # --- Per-Onion Analysis & URS Disqualification Reasons ---
    onion_grades = list(assessment.onion_grades or [])
    if onion_grades:
        story.append(Paragraph("Per-Onion Analysis & URS Specification Details", styles["Heading3"]))
        cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=10)
        grade_a_cell = ParagraphStyle("GA", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#16A34A"), fontName="Helvetica-Bold")
        grade_urs_cell = ParagraphStyle("GURS", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#D97706"), fontName="Helvetica-Bold")
        non_qual_cell = ParagraphStyle("NQ", parent=styles["Normal"], fontSize=8, leading=10, textColor=colors.HexColor("#DC2626"), fontName="Helvetica-Bold")

        po_rows = [["Onion #", "Diameter", "Grade", "Defects", "URS Evaluation Details / Reasons"]]
        for i, item in enumerate(onion_grades):
            o_id = f"#{item.get('onion_id', i+1)}"
            dia_val = item.get("diameter_mm")
            dia_str = f"{dia_val:.1f} mm" if dia_val is not None else "N/A"
            grade_val = item.get("grade", "NON_QUALIFYING")
            
            if grade_val == "GRADE_A":
                g_p = Paragraph("GRADE A", grade_a_cell)
            elif grade_val == "GRADE_URS":
                g_p = Paragraph("GRADE URS", grade_urs_cell)
            else:
                g_p = Paragraph("NON-QUALIFYING", non_qual_cell)
            
            defects = item.get("defects", [])
            def_str = ", ".join(format_defect_name(d) for d in defects) if defects else "None (Healthy)"

            reasons_list = item.get("reasons", [])
            if reasons_list:
                reason_str = "; ".join(reasons_list)
            else:
                if grade_val == "GRADE_A":
                    reason_str = "Meets Grade A standards (35–70mm size, dry skins, zero defects)"
                elif grade_val == "GRADE_URS":
                    reason_str = "Qualifies under Relaxed Specifications (Grade URS)"
                else:
                    reason_str = "Non-qualifying per specification limits"

            po_rows.append([
                Paragraph(o_id, cell_style),
                Paragraph(dia_str, cell_style),
                g_p,
                Paragraph(def_str, cell_style),
                Paragraph(reason_str, cell_style),
            ])

        po_table = Table(po_rows, colWidths=[18 * mm, 24 * mm, 30 * mm, 28 * mm, 65 * mm])
        po_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ])
        )
        story += [po_table, Spacer(1, 6 * mm)]

    # --- Overall Metrics ---
    story.append(Paragraph("Overall Quality Metrics", styles["Heading3"]))
    metrics_rows = [
        ["Metric", "Value"],
        ["Total onions", str(total)],
        ["NCCF Batch Grade", assessment.nccf_grade or "N/A"],
        ["Grade A %", f"{grade_a_pct:.1f}%"],
        ["Grade URS %", f"{grade_urs_pct:.1f}%"],
        ["Non-Qualifying %", f"{non_qual_pct:.1f}%"],
        ["Avg AI Confidence", f"{assessment.avg_confidence * 100:.1f}%"],
        ["Specification", assessment.specification_id or "N/A"],
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
    story.append(Paragraph("Grading Summary", styles["Heading3"]))
    for reason in reasons or ["No details recorded."]:
        story.append(Paragraph(f"•  {reason}", styles["Normal"]))

    story += [
        Spacer(1, 8 * mm),
        Paragraph(
            "AI-based visual pre-grading per NCCF 2026 procurement specifications "
            f"({assessment.specification_id or 'unspecified'}). "
            "This report is NOT an official government certification.",
            note_style,
        ),
    ]

    try:
        doc.build(story)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

    return pdf_path
