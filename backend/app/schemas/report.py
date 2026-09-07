"""Report schemas (Backend <-> Mobile contract)."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReportOut(BaseModel):
    report_id: int
    report_code: str = Field(examples=["RPT-0001-20260907-101500"])
    assessment_id: int
    batch_id: str = Field(description="Batch code, e.g. ON-0001")
    format: str = "pdf"
    is_demo: bool = Field(description="True => report generated from DEMO data")
    generated_at: datetime
    download_url: str = Field(description="Relative URL: /api/reports/{id}/download")
