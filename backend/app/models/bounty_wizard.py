"""Bounty Creation Wizard models."""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, String, DateTime, Integer, Float, JSON, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class WizardStep(str, Enum):
    """Wizard steps."""
    BASICS = "basics"           # Title, description, category
    REWARD = "reward"          # Token, amount, tier
    REQUIREMENTS = "requirements"  # Skills, deadline
    REVIEW = "review"          # Final review
    COMPLETE = "complete"      # Done


class BountyDraftDB(Base):
    """Bounty draft for wizard."""
    __tablename__ = "bounty_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)
    current_step = Column(String(20), default="basics")
    
    # Step 1: Basics
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)
    
    # Step 2: Reward
    reward_token = Column(String(20), default="FNDRY")
    reward_amount = Column(Float, nullable=True)
    tier = Column(Integer, nullable=True)
    
    # Step 3: Requirements
    skills = Column(JSON, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)
    github_issue_url = Column(String(500), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# Pydantic models for wizard

class BasicsStep(BaseModel):
    """Step 1: Basic info."""
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    category: str = Field(...)

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        valid = {"frontend", "backend", "smart_contract", "documentation", "testing", "infrastructure", "other"}
        if v not in valid:
            raise ValueError(f"Invalid category. Must be one of: {valid}")
        return v


class RewardStep(BaseModel):
    """Step 2: Reward info."""
    reward_token: str = Field(default="FNDRY")
    reward_amount: float = Field(..., gt=0)
    tier: int = Field(..., ge=1, le=3)

    @field_validator('tier')
    @classmethod
    def validate_tier(cls, v):
        if v not in [1, 2, 3]:
            raise ValueError("Tier must be 1, 2, or 3")
        return v


class RequirementsStep(BaseModel):
    """Step 3: Requirements."""
    skills: List[str] = Field(default_factory=list)
    deadline: Optional[datetime] = None
    github_issue_url: Optional[str] = None


class WizardDraftResponse(BaseModel):
    """Draft response."""
    id: str
    user_id: str
    current_step: str
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    reward_token: Optional[str] = None
    reward_amount: Optional[float] = None
    tier: Optional[int] = None
    skills: Optional[List[str]] = None
    deadline: Optional[datetime] = None
    github_issue_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CreateDraftRequest(BaseModel):
    """Create draft request."""
    user_id: str


class UpdateBasicsRequest(BasicsStep):
    """Update basics step."""
    pass


class UpdateRewardRequest(RewardStep):
    """Update reward step."""
    pass


class UpdateRequirementsRequest(RequirementsStep):
    """Update requirements step."""
    pass


class FinalizeRequest(BaseModel):
    """Finalize and create bounty."""
    confirm: bool = Field(..., description="Must be true to finalize")