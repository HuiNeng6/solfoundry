"""Contributor Profile database and Pydantic models."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ContributorTier(str, Enum):
    """Contributor reputation tiers."""
    BRONZE = "bronze"      # 0-99 points
    SILVER = "silver"      # 100-499 points
    GOLD = "gold"          # 500-1999 points
    PLATINUM = "platinum"   # 2000+ points
    LEGENDARY = "legendary" # 10000+ points


class ContributorDB(Base):
    """
    Contributor profile database model.
    
    Stores contributor statistics, achievements, and profile information.
    """
    __tablename__ = "contributors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_username = Column(String(100), nullable=False, unique=True, index=True)
    github_id = Column(Integer, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(String(500), nullable=True)
    
    # Statistics
    total_prs = Column(Integer, default=0, nullable=False)
    merged_prs = Column(Integer, default=0, nullable=False)
    total_issues = Column(Integer, default=0, nullable=False)
    closed_issues = Column(Integer, default=0, nullable=False)
    total_commits = Column(Integer, default=0, nullable=False)
    lines_added = Column(Integer, default=0, nullable=False)
    lines_removed = Column(Integer, default=0, nullable=False)
    
    # Points and tier
    points = Column(Integer, default=0, nullable=False)
    tier = Column(String(20), default="bronze", nullable=False)
    
    # Achievements (JSON array)
    achievements = Column(JSON, default=list, nullable=False)
    
    # Stats by category
    category_stats = Column(JSON, nullable=True)  # {backend: 10, frontend: 5, ...}
    
    # Timestamps
    first_contribution = Column(DateTime(timezone=True), nullable=True)
    last_contribution = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index('ix_contributors_tier', tier),
        Index('ix_contributors_points', points),
    )


# Pydantic models

class ContributorStats(BaseModel):
    """Contributor statistics."""
    total_prs: int = 0
    merged_prs: int = 0
    total_issues: int = 0
    closed_issues: int = 0
    total_commits: int = 0
    lines_added: int = 0
    lines_removed: int = 0


class Achievement(BaseModel):
    """Single achievement."""
    id: str
    name: str
    description: str
    icon: str
    earned_at: datetime


class ContributorProfile(BaseModel):
    """Full contributor profile."""
    id: str
    github_username: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    stats: ContributorStats
    points: int
    tier: str
    achievements: List[Achievement] = []
    category_stats: Optional[dict] = None
    first_contribution: Optional[datetime] = None
    last_contribution: Optional[datetime] = None
    rank: Optional[int] = None  # Global rank
    model_config = {"from_attributes": True}


class ContributorListItem(BaseModel):
    """Brief contributor info for leaderboards."""
    id: str
    github_username: str
    avatar_url: Optional[str] = None
    points: int
    tier: str
    merged_prs: int = 0
    model_config = {"from_attributes": True}


class LeaderboardResponse(BaseModel):
    """Paginated leaderboard response."""
    items: List[ContributorListItem]
    total: int
    skip: int
    limit: int


class ContributorUpdate(BaseModel):
    """Schema for updating contributor profile."""
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = None