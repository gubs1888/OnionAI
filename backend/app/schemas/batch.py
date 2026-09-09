"""Batch-related schemas (Backend <-> Mobile contract)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64, examples=["demo"])
    password: str = Field(min_length=1, max_length=128, examples=["demo123"])


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token lifetime in seconds")
    user: UserOut


class BatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120, examples=["Lot A — Nashik farm"])
    variety: str | None = Field(default=None, max_length=64, examples=["Nashik Red"])
    source: str | None = Field(default=None, max_length=120, examples=["Lasalgaon Mandi"])
    notes: str | None = Field(default=None, max_length=2000)


class BatchUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    variety: str | None = Field(default=None, max_length=64)
    source: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None, pattern="^(created|analyzing|analyzed|failed|closed)$")


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_code: str = Field(description="Human-friendly code, e.g. ON-0001")
    name: str
    variety: str | None = None
    source: str | None = None
    notes: str | None = None
    status: str = Field(description="created | analyzing | analyzed | failed")
    created_by: int | None = None
    image_count: int = 0
    created_at: datetime
