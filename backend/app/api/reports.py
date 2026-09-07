"""Report endpoints: generate (PDF), fetch metadata, download."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.assessment import Assessment
from app.models.report import Report
from app.schemas.report import ReportOut
from app.services.report import ReportGenerationError, generate_report

router = APIRouter(prefix="/reports", tags=["reports"])


def _report_out(report: Report) -> ReportOut:
    return ReportOut(
        report_id=report.id,
        report_code=report.report_code,
        assessment_id=report.assessment_id,
        batch_id=report.assessment.batch.batch_code,
        format=report.format,
        is_demo=report.is_demo,
        generated_at=report.generated_at,
        download_url=f"/api/reports/{report.id}/download",
    )


def _get_report(db: Session, report_ref: str) -> Report:
    ref = (report_ref or "").strip()
    report = None
    if ref.isdigit():
        report = db.get(Report, int(ref))
    if report is None:
        report = db.query(Report).filter(Report.report_code.ilike(ref)).first()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REPORT_NOT_FOUND", "message": f"Report '{report_ref}' not found."},
        )
    return report


@router.post(
    "/{assessment_id}",
    response_model=ReportOut,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a PDF report for an assessment",
    description=(
        "Builds a PDF via ReportLab and stores a `reports` row. "
        "Reports for DEMO assessments are watermarked "
        "'DEMO DATA — NOT FOR OFFICIAL USE'."
    ),
    responses={
        404: {"description": "Assessment not found"},
        501: {"description": "reportlab not installed"},
    },
)
def create_report(assessment_id: int, db: Session = Depends(get_db)) -> ReportOut:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ASSESSMENT_NOT_FOUND",
                "message": f"Assessment {assessment_id} not found.",
            },
        )
    try:
        pdf_path = generate_report(assessment)
    except ReportGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={"code": "REPORT_UNAVAILABLE", "message": str(exc)},
        ) from exc

    report = Report(
        report_code=pdf_path.stem,
        assessment_id=assessment.id,
        file_path=str(pdf_path),
        format="pdf",
        is_demo=assessment.is_demo,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return _report_out(report)


@router.get(
    "/{report_id}",
    response_model=ReportOut,
    summary="Get report metadata",
    description="Accepts the numeric report id or the report code. Use `/download` for the PDF.",
    responses={404: {"description": "Report not found"}},
)
def get_report(report_id: str, db: Session = Depends(get_db)) -> ReportOut:
    return _report_out(_get_report(db, report_id))


@router.get(
    "/{report_id}/download",
    summary="Download the report PDF",
    responses={404: {"description": "Report not found"}, 410: {"description": "PDF file missing"}},
)
def download_report(report_id: str, db: Session = Depends(get_db)) -> FileResponse:
    report = _get_report(db, report_id)
    path = Path(report.file_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail={"code": "FILE_MISSING", "message": "The PDF file is no longer on disk."},
        )
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{report.report_code}.pdf",
    )
