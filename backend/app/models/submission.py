"""Bounty submission database and Pydantic models."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class SubmissionStatus(str, Enum):
    PENDING = "pending"
    MATCHED = "matched"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"
    DISPUTED = "disputed"


class MatchConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SubmissionDB(Base):
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contributor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    contributor_wallet = Column(String(64), nullable=False, index=True)
    pr_url = Column(String(500), nullable=False)
    pr_number = Column(Integer, nullable=True)
    pr_repo = Column(String(255), nullable=True)
    pr_status = Column(String(50), nullable=True)
    pr_merged_at = Column(DateTime(timezone=True), nullable=True)
    bounty_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    match_confidence = Column(String(20), nullable=True)
    match_score = Column(Float, nullable=True)
    match_reasons = Column(JSON, default=list, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    review_notes = Column(Text, nullable=True)
    reviewer_id = Column(UUID(as_uuid=True), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    reward_amount = Column(Float, nullable=True)
    reward_token = Column(String(20), nullable=True)
    payout_tx_hash = Column(String(128), nullable=True)
    payout_at = Column(DateTime(timezone=True), nullable=True)
    description = Column(Text, nullable=True)
    evidence = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_submissions_contributor_status', contributor_id, status),
        Index('ix_submissions_bounty_status', bounty_id, status),
        Index('ix_submissions_status_created', status, created_at),
        Index('ix_submissions_wallet_status', contributor_wallet, status),
    )


class SubmissionBase(BaseModel):
    pr_url: str = Field(..., min_length=10, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    evidence: List[str] = Field(default_factory=list)

    @field_validator('pr_url')
    @classmethod
    def validate_pr_url(cls, v: str) -> str:
        if not v.startswith(('https://github.com/', 'http://github.com/')):
            raise ValueError('PR URL must be a valid GitHub URL')
        if '/pull/' not in v:
            raise ValueError('URL must be a pull request URL')
        return v


class SubmissionCreate(SubmissionBase):
    bounty_id: Optional[str] = Field(None)
    contributor_wallet: str = Field(..., min_length=32, max_length=64)


class SubmissionUpdate(BaseModel):
    status: Optional[str] = None
    review_notes: Optional[str] = None
    bounty_id: Optional[str] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        valid_statuses = {s.value for s in SubmissionStatus}
        if v is not None and v not in valid_statuses:
            raise ValueError(f"Invalid status: {v}")
        return v


class MatchResult(BaseModel):
    bounty_id: str
    bounty_title: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    confidence: str
    reasons: List[str]
    github_issue_url: Optional[str] = None


class SubmissionResponse(SubmissionBase):
    id: str
    contributor_id: str
    contributor_wallet: str
    pr_number: Optional[int] = None
    pr_repo: Optional[str] = None
    pr_status: Optional[str] = None
    pr_merged_at: Optional[datetime] = None
    bounty_id: Optional[str] = None
    match_confidence: Optional[str] = None
    match_score: Optional[float] = None
    match_reasons: List[str] = Field(default_factory=list)
    status: str
    review_notes: Optional[str] = None
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reward_amount: Optional[float] = None
    reward_token: Optional[str] = None
    payout_tx_hash: Optional[str] = None
    payout_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class SubmissionListItem(BaseModel):
    id: str
    contributor_wallet: str
    pr_url: str
    pr_number: Optional[int] = None
    pr_repo: Optional[str] = None
    bounty_id: Optional[str] = None
    match_confidence: Optional[str] = None
    status: str
    reward_amount: Optional[float] = None
    reward_token: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class SubmissionListResponse(BaseModel):
    items: List[SubmissionListItem]
    total: int
    skip: int
    limit: int


class SubmissionSearchParams(BaseModel):
    contributor_id: Optional[str] = None
    bounty_id: Optional[str] = None
    status: Optional[str] = None
    wallet: Optional[str] = None
    sort: str = Field("newest", pattern="^(newest|oldest|status|reward)$")
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class SubmissionStats(BaseModel):
    total_submissions: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    paid: int = 0
    total_earnings: float = 0.0
    approval_rate: float = 0.0
