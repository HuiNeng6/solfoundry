"""PR Status database and Pydantic models."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, JSON, Integer, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class PRStage(str, Enum):
    SUBMITTED = "submitted"
    CI_RUNNING = "ci_running"
    AI_REVIEW = "ai_review"
    HUMAN_REVIEW = "human_review"
    APPROVED = "approved"
    DENIED = "denied"
    PAYOUT = "payout"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


# Database Model
class PRStatusDB(Base):
    __tablename__ = "pr_status"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pr_number = Column(Integer, nullable=False, unique=True, index=True)
    pr_title = Column(String(500), nullable=False)
    pr_url = Column(String(1000), nullable=False)
    author = Column(String(100), nullable=False)
    bounty_id = Column(String(100), nullable=True, index=True)
    bounty_title = Column(String(500), nullable=True)
    current_stage = Column(SQLEnum(PRStage), nullable=False, default=PRStage.SUBMITTED)
    stages_data = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# Pydantic Models
class AIReviewScore(BaseModel):
    quality: float = Field(..., ge=0, le=10)
    correctness: float = Field(..., ge=0, le=10)
    security: float = Field(..., ge=0, le=10)
    completeness: float = Field(..., ge=0, le=10)
    tests: float = Field(..., ge=0, le=10)
    overall: float = Field(..., ge=0, le=10)


class StageDetails(BaseModel):
    status: StageStatus = StageStatus.PENDING
    timestamp: Optional[str] = None
    duration: Optional[int] = None  # in seconds
    message: Optional[str] = None
    # AI Review specific
    scores: Optional[AIReviewScore] = None
    # Payout specific
    tx_hash: Optional[str] = None
    solscan_url: Optional[str] = None
    amount: Optional[int] = None


class PRStatusBase(BaseModel):
    pr_number: int
    pr_title: str
    pr_url: str
    author: str
    bounty_id: Optional[str] = None
    bounty_title: Optional[str] = None
    current_stage: PRStage = PRStage.SUBMITTED
    stages: Dict[PRStage, StageDetails] = Field(default_factory=lambda: {
        PRStage.SUBMITTED: StageDetails(status=StageStatus.PASSED, timestamp=datetime.now(timezone.utc).isoformat()),
        PRStage.CI_RUNNING: StageDetails(),
        PRStage.AI_REVIEW: StageDetails(),
        PRStage.HUMAN_REVIEW: StageDetails(),
        PRStage.APPROVED: StageDetails(),
        PRStage.DENIED: StageDetails(),
        PRStage.PAYOUT: StageDetails(),
    })


class PRStatusCreate(BaseModel):
    pr_number: int = Field(..., gt=0)
    pr_title: str = Field(..., min_length=1, max_length=500)
    pr_url: str = Field(..., max_length=1000)
    author: str = Field(..., min_length=1, max_length=100)
    bounty_id: Optional[str] = Field(None, max_length=100)
    bounty_title: Optional[str] = Field(None, max_length=500)


class PRStatusUpdate(BaseModel):
    current_stage: Optional[PRStage] = None
    stages: Optional[Dict[str, StageDetails]] = None


class PRStatusResponse(PRStatusBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PRStatusListItem(BaseModel):
    pr_number: int
    pr_title: str
    author: str
    current_stage: PRStage
    bounty_id: Optional[str] = None
    updated_at: datetime
    model_config = {"from_attributes": True}


class PRStatusListResponse(BaseModel):
    items: list[PRStatusListItem]
    total: int
    skip: int
    limit: int


# Helper functions
def get_default_stages() -> Dict[str, Dict[str, Any]]:
    """Get default stages configuration."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        PRStage.SUBMITTED.value: {
            "status": StageStatus.PASSED.value,
            "timestamp": now,
            "duration": None,
            "message": "PR submitted successfully"
        },
        PRStage.CI_RUNNING.value: {
            "status": StageStatus.PENDING.value,
            "timestamp": None,
            "duration": None,
            "message": None
        },
        PRStage.AI_REVIEW.value: {
            "status": StageStatus.PENDING.value,
            "timestamp": None,
            "duration": None,
            "message": None,
            "scores": None
        },
        PRStage.HUMAN_REVIEW.value: {
            "status": StageStatus.PENDING.value,
            "timestamp": None,
            "duration": None,
            "message": None
        },
        PRStage.APPROVED.value: {
            "status": StageStatus.PENDING.value,
            "timestamp": None,
            "duration": None,
            "message": None
        },
        PRStage.DENIED.value: {
            "status": StageStatus.PENDING.value,
            "timestamp": None,
            "duration": None,
            "message": None
        },
        PRStage.PAYOUT.value: {
            "status": StageStatus.PENDING.value,
            "timestamp": None,
            "duration": None,
            "message": None,
            "tx_hash": None,
            "solscan_url": None,
            "amount": None
        }
    }