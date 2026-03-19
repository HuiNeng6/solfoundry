"""Bounty database and Pydantic models."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, JSON, Float, Integer, Text, Index
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR

from app.database import Base


class BountyTier(int, Enum):
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


class BountyStatus(str, Enum):
    OPEN = "open"
    CLAIMED = "claimed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BountyCategory(str, Enum):
    FRONTEND = "frontend"
    BACKEND = "backend"
    SMART_CONTRACT = "smart_contract"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"
    OTHER = "other"


class BountyDB(Base):
    __tablename__ = "bounties"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    tier = Column(Integer, nullable=False, default=1)
    category = Column(String(50), nullable=False, default="other")
    status = Column(String(20), nullable=False, default="open", index=True)
    reward_amount = Column(Float, nullable=False, default=0.0)
    reward_token = Column(String(20), nullable=False, default="FNDRY")
    deadline = Column(DateTime(timezone=True), nullable=True)
    skills = Column(JSON, default=list, nullable=False)
    github_issue_url = Column(String(500), nullable=True)
    github_issue_number = Column(Integer, nullable=True)
    github_repo = Column(String(255), nullable=True)
    claimant_id = Column(UUID(as_uuid=True), nullable=True)
    winner_id = Column(UUID(as_uuid=True), nullable=True)
    popularity = Column(Integer, default=0, nullable=False)
    search_vector = Column(TSVECTOR, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_bounties_search_vector', search_vector, postgresql_using='gin'),
        Index('ix_bounties_tier_status', tier, status),
        Index('ix_bounties_category_status', category, status),
        Index('ix_bounties_reward', reward_amount),
        Index('ix_bounties_deadline', deadline),
        Index('ix_bounties_popularity', popularity),
    )


# Pydantic models for API
class BountyBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    tier: int = Field(1, ge=1, le=3)
    category: str = Field("other")
    reward_amount: float = Field(0.0, ge=0)
    reward_token: str = Field("FNDRY")
    deadline: Optional[datetime] = None
    skills: list[str] = []


class BountyCreate(BountyBase):
    github_issue_url: Optional[str] = None
    github_issue_number: Optional[int] = None
    github_repo: Optional[str] = None


class BountyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    tier: Optional[int] = Field(None, ge=1, le=3)
    category: Optional[str] = None
    status: Optional[str] = None
    reward_amount: Optional[float] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    skills: Optional[list[str]] = None


class BountyResponse(BountyBase):
    id: str
    status: str
    github_issue_url: Optional[str] = None
    github_issue_number: Optional[int] = None
    github_repo: Optional[str] = None
    claimant_id: Optional[str] = None
    winner_id: Optional[str] = None
    popularity: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class BountyListItem(BaseModel):
    id: str
    title: str
    description: str
    tier: int
    category: str
    status: str
    reward_amount: float
    reward_token: str
    deadline: Optional[datetime] = None
    skills: list[str] = []
    popularity: int = 0
    created_at: datetime
    model_config = {"from_attributes": True}


class BountyListResponse(BaseModel):
    items: list[BountyListItem]
    total: int
    skip: int
    limit: int


class BountySearchParams(BaseModel):
    q: Optional[str] = None
    tier: Optional[int] = None
    category: Optional[str] = None
    status: Optional[str] = None
    reward_min: Optional[float] = None
    reward_max: Optional[float] = None
    skills: Optional[list[str]] = None
    sort: Optional[str] = Field("newest", pattern="^(newest|reward_high|reward_low|deadline|popularity)$")
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)


class AutocompleteSuggestion(BaseModel):
    text: str
    type: str  # 'title' or 'skill'


class AutocompleteResponse(BaseModel):
    suggestions: list[AutocompleteSuggestion]