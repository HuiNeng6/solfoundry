"""Reputation history and scoring models.

This module defines the data models for the reputation system including
database models (ORM) and API models (Pydantic schemas).

Reputation Score Calculation:
- Base score: 0
- Completed bounties: +10 per bounty
- Success rate bonus: up to +50 (based on completed/(completed+cancelled))
- Code quality bonus: up to +30 (based on avg review scores)
- Timely delivery bonus: up to +20 (based on on-time completion rate)
- Tier multipliers: T1 x1, T2 x1.5, T3 x2
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ReputationChangeSource(str, Enum):
    """Source of reputation change."""
    BOUNTY_COMPLETED = "bounty_completed"
    BOUNTY_CANCELLED = "bounty_cancelled"
    CODE_REVIEW = "code_review"
    TIMELY_DELIVERY = "timely_delivery"
    MANUAL_ADJUSTMENT = "manual_adjustment"
    BONUS = "bonus"


class ReputationHistoryDB(Base):
    """Database model for tracking reputation changes over time."""
    __tablename__ = "reputation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contributor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    score_before = Column(Integer, nullable=False, default=0)
    score_after = Column(Integer, nullable=False, default=0)
    change = Column(Integer, nullable=False, default=0)
    source = Column(String(50), nullable=False)
    bounty_id = Column(UUID(as_uuid=True), nullable=True)
    description = Column(Text, nullable=True)
    extra_data = Column(String(500), nullable=True)  # JSON string for extra data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index('ix_reputation_history_contributor_created', contributor_id, created_at),
        Index('ix_reputation_history_source', source),
    )


class ReputationBreakdown(BaseModel):
    """Detailed breakdown of reputation score components."""
    base_score: int = 0
    bounty_completion_score: int = Field(default=0, description="Points from completed bounties")
    success_rate_score: int = Field(default=0, ge=0, le=50, description="Success rate bonus (0-50)")
    code_quality_score: int = Field(default=0, ge=0, le=30, description="Code quality bonus (0-30)")
    timely_delivery_score: int = Field(default=0, ge=0, le=20, description="Timely delivery bonus (0-20)")
    tier_multipliers: dict[str, float] = Field(default_factory=dict, description="Tier breakdown with multipliers")
    total_score: int = Field(default=0, description="Final calculated reputation score")


class ReputationStats(BaseModel):
    """Statistics used for reputation calculation."""
    total_bounties_claimed: int = 0
    bounties_completed: int = 0
    bounties_cancelled: int = 0
    success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="completed/(completed+cancelled)")
    avg_review_score: float = Field(default=0.0, ge=0.0, le=5.0, description="Average code review score (0-5)")
    on_time_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="On-time completion rate")
    tier_breakdown: dict[str, int] = Field(default_factory=lambda: {"tier1": 0, "tier2": 0, "tier3": 0})


class ReputationChangeEntry(BaseModel):
    """Single reputation change history entry."""
    id: str
    score_before: int
    score_after: int
    change: int
    source: str
    bounty_id: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReputationHistoryResponse(BaseModel):
    """Paginated reputation history response."""
    contributor_id: str
    current_score: int
    breakdown: ReputationBreakdown
    stats: ReputationStats
    history: List[ReputationChangeEntry]
    total_history: int
    skip: int
    limit: int


class ReputationRankResponse(BaseModel):
    """User's rank in various leaderboards."""
    global_rank: int
    global_total: int
    category_ranks: dict[str, int] = Field(default_factory=dict, description="Rank by skill category")
    tier_ranks: dict[str, int] = Field(default_factory=dict, description="Rank by bounty tier")
    percentile: float = Field(default=0.0, description="Top X% globally")


class LeaderboardTypeEnum(str, Enum):
    """Types of leaderboards available."""
    GLOBAL = "global"
    BY_SKILL = "by_skill"
    BY_TIER = "by_tier"
    BY_PERIOD = "by_period"


class SkillLeaderboardEntry(BaseModel):
    """Leaderboard entry for a specific skill."""
    rank: int
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    skill_score: int = Field(default=0, description="Points earned in this skill")
    bounties_in_skill: int = Field(default=0)
    reputation_score: int = Field(default=0)

    model_config = {"from_attributes": True}


class SkillLeaderboardResponse(BaseModel):
    """Leaderboard for a specific skill."""
    skill: str
    period: str
    total: int
    entries: List[SkillLeaderboardEntry]


class TierLeaderboardEntry(BaseModel):
    """Leaderboard entry for a specific bounty tier."""
    rank: int
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    tier_bounties: int = Field(default=0, description="Bounties completed in this tier")
    tier_earnings: float = Field(default=0.0, description="Total earnings from this tier")
    reputation_score: int = Field(default=0)

    model_config = {"from_attributes": True}


class TierLeaderboardResponse(BaseModel):
    """Leaderboard for a specific bounty tier."""
    tier: int
    period: str
    total: int
    entries: List[TierLeaderboardEntry]


class PeriodLeaderboardEntry(BaseModel):
    """Leaderboard entry for a specific time period."""
    rank: int
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    period_earnings: float = Field(default=0.0, description="Earnings in this period")
    period_bounties: int = Field(default=0, description="Bounties completed in this period")
    reputation_change: int = Field(default=0, description="Reputation gained in this period")
    total_reputation: int = Field(default=0)

    model_config = {"from_attributes": True}


class PeriodLeaderboardResponse(BaseModel):
    """Leaderboard for a specific time period."""
    period: str
    start_date: datetime
    end_date: datetime
    total: int
    entries: List[PeriodLeaderboardEntry]


class GlobalLeaderboardEntry(BaseModel):
    """Entry in the global reputation leaderboard."""
    rank: int
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    reputation_score: int = 0
    total_earnings: float = 0.0
    bounties_completed: int = 0
    success_rate: float = 0.0
    badges: List[str] = []
    skills: List[str] = []

    model_config = {"from_attributes": True}


class GlobalLeaderboardResponse(BaseModel):
    """Full global reputation leaderboard."""
    period: str
    total: int
    offset: int
    limit: int
    top3: List[GlobalLeaderboardEntry] = []
    entries: List[GlobalLeaderboardEntry] = []