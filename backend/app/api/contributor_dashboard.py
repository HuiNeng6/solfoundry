"""Contributor Dashboard API router."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.contributor import ContributorDB
from app.models.bounty import BountyDB


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


# Pydantic models

class BountyHistoryItem(BaseModel):
    """Bounty participation history item."""
    id: str
    title: str
    status: str
    tier: int
    reward_amount: float
    reward_token: str
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    model_config = {"from_attributes": True}


class EarningsStats(BaseModel):
    """Earnings statistics."""
    total_earned: float = 0.0
    total_bounties: int = 0
    average_reward: float = 0.0
    this_month_earned: float = 0.0
    last_month_earned: float = 0.0
    by_token: dict = {}
    
    model_config = {"from_attributes": True}


class ReputationChange(BaseModel):
    """Reputation score change."""
    date: datetime
    change: int
    reason: str
    new_total: int
    
    model_config = {"from_attributes": True}


class ReputationStats(BaseModel):
    """Reputation statistics."""
    current_score: int = 0
    total_changes: int = 0
    recent_changes: List[ReputationChange] = []
    
    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    """Dashboard summary data."""
    contributor_id: str
    username: str
    display_name: str
    avatar_url: Optional[str] = None
    wallet_address: Optional[str] = None
    earnings: EarningsStats
    reputation: ReputationStats
    active_bounties: int = 0
    completed_bounties: List[BountyHistoryItem] = []
    claimed_bounties: List[BountyHistoryItem] = []
    
    model_config = {"from_attributes": True}


class DashboardResponse(BaseModel):
    """Full dashboard response."""
    summary: DashboardSummary
    bounty_history: List[BountyHistoryItem]
    earnings_chart: List[dict]
    reputation_history: List[dict]
    
    model_config = {"from_attributes": True}


@router.get("/{contributor_id}", response_model=DashboardResponse)
async def get_contributor_dashboard(
    contributor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard data for a contributor."""
    
    try:
        contributor_uuid = UUID(contributor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid contributor ID format")
    
    # Fetch contributor
    result = await db.execute(
        select(ContributorDB).where(ContributorDB.id == contributor_uuid)
    )
    contributor = result.scalar_one_or_none()
    
    if not contributor:
        raise HTTPException(status_code=404, detail="Contributor not found")
    
    # Fetch completed bounties
    completed_result = await db.execute(
        select(BountyDB)
        .where(BountyDB.winner_id == contributor_uuid)
        .where(BountyDB.status == "completed")
        .order_by(BountyDB.updated_at.desc())
        .limit(10)
    )
    completed_bounties = completed_result.scalars().all()
    
    # Fetch claimed bounties
    claimed_result = await db.execute(
        select(BountyDB)
        .where(BountyDB.claimant_id == contributor_uuid)
        .where(BountyDB.status == "claimed")
        .order_by(BountyDB.updated_at.desc())
        .limit(10)
    )
    claimed_bounties = claimed_result.scalars().all()
    
    # Calculate earnings statistics
    now = datetime.now(timezone.utc)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    # Get all completed bounties for earnings calculation
    all_completed_result = await db.execute(
        select(BountyDB)
        .where(BountyDB.winner_id == contributor_uuid)
        .where(BountyDB.status == "completed")
    )
    all_completed = all_completed_result.scalars().all()
    
    total_earned = sum(b.reward_amount for b in all_completed)
    this_month_earned = sum(
        b.reward_amount for b in all_completed 
        if b.updated_at and b.updated_at >= this_month_start
    )
    last_month_earned = sum(
        b.reward_amount for b in all_completed 
        if b.updated_at and last_month_start <= b.updated_at < this_month_start
    )
    
    # Calculate earnings by token
    by_token = {}
    for b in all_completed:
        token = b.reward_token or "FNDRY"
        by_token[token] = by_token.get(token, 0) + b.reward_amount
    
    # Generate earnings chart data (last 6 months)
    earnings_chart = []
    for i in range(5, -1, -1):
        month_start = (now - timedelta(days=30*i)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        month_earned = sum(
            b.reward_amount for b in all_completed
            if b.updated_at and month_start <= b.updated_at <= month_end
        )
        earnings_chart.append({
            "month": month_start.strftime("%Y-%m"),
            "earned": month_earned
        })
    
    # Generate reputation history
    reputation_history = []
    base_reputation = max(0, contributor.reputation_score - 50)
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30*i)
        change = min(10, contributor.reputation_score // 6)
        reputation_history.append({
            "month": month_date.strftime("%Y-%m"),
            "score": base_reputation + change * (6 - i)
        })
    
    # Build response
    earnings_stats = EarningsStats(
        total_earned=total_earned,
        total_bounties=len(all_completed),
        average_reward=total_earned / len(all_completed) if all_completed else 0.0,
        this_month_earned=this_month_earned,
        last_month_earned=last_month_earned,
        by_token=by_token
    )
    
    # Build recent reputation changes
    recent_changes = []
    if completed_bounties:
        for i, bounty in enumerate(completed_bounties[:5]):
            recent_changes.append(
                ReputationChange(
                    date=bounty.updated_at or bounty.created_at,
                    change=bounty.tier * 5,
                    reason=f"Completed bounty: {bounty.title[:30]}...",
                    new_total=contributor.reputation_score - (5 - i) * bounty.tier * 5
                )
            )
    
    reputation_stats = ReputationStats(
        current_score=contributor.reputation_score,
        total_changes=len(all_completed),
        recent_changes=recent_changes
    )
    
    # Build bounty history
    bounty_history = []
    for bounty in list(completed_bounties) + list(claimed_bounties):
        bounty_history.append(
            BountyHistoryItem(
                id=str(bounty.id),
                title=bounty.title,
                status=bounty.status,
                tier=bounty.tier,
                reward_amount=bounty.reward_amount,
                reward_token=bounty.reward_token,
                completed_at=bounty.updated_at if bounty.status == "completed" else None,
                created_at=bounty.created_at
            )
        )
    
    # Build summary
    summary = DashboardSummary(
        contributor_id=str(contributor.id),
        username=contributor.username,
        display_name=contributor.display_name,
        avatar_url=contributor.avatar_url,
        wallet_address=None,
        earnings=earnings_stats,
        reputation=reputation_stats,
        active_bounties=len(claimed_bounties),
        completed_bounties=[
            BountyHistoryItem(
                id=str(b.id),
                title=b.title,
                status=b.status,
                tier=b.tier,
                reward_amount=b.reward_amount,
                reward_token=b.reward_token,
                completed_at=b.updated_at,
                created_at=b.created_at
            ) for b in completed_bounties[:5]
        ],
        claimed_bounties=[
            BountyHistoryItem(
                id=str(b.id),
                title=b.title,
                status=b.status,
                tier=b.tier,
                reward_amount=b.reward_amount,
                reward_token=b.reward_token,
                completed_at=None,
                created_at=b.created_at
            ) for b in claimed_bounties[:5]
        ]
    )
    
    return DashboardResponse(
        summary=summary,
        bounty_history=bounty_history,
        earnings_chart=earnings_chart,
        reputation_history=reputation_history
    )


@router.get("/{contributor_id}/earnings", response_model=EarningsStats)
async def get_contributor_earnings(
    contributor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed earnings statistics for a contributor."""
    
    try:
        contributor_uuid = UUID(contributor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid contributor ID format")
    
    result = await db.execute(
        select(ContributorDB).where(ContributorDB.id == contributor_uuid)
    )
    contributor = result.scalar_one_or_none()
    
    if not contributor:
        raise HTTPException(status_code=404, detail="Contributor not found")
    
    bounties_result = await db.execute(
        select(BountyDB)
        .where(BountyDB.winner_id == contributor_uuid)
        .where(BountyDB.status == "completed")
    )
    bounties = bounties_result.scalars().all()
    
    now = datetime.now(timezone.utc)
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
    
    total_earned = sum(b.reward_amount for b in bounties)
    this_month_earned = sum(
        b.reward_amount for b in bounties 
        if b.updated_at and b.updated_at >= this_month_start
    )
    last_month_earned = sum(
        b.reward_amount for b in bounties 
        if b.updated_at and last_month_start <= b.updated_at < this_month_start
    )
    
    by_token = {}
    for b in bounties:
        token = b.reward_token or "FNDRY"
        by_token[token] = by_token.get(token, 0) + b.reward_amount
    
    return EarningsStats(
        total_earned=total_earned,
        total_bounties=len(bounties),
        average_reward=total_earned / len(bounties) if bounties else 0.0,
        this_month_earned=this_month_earned,
        last_month_earned=last_month_earned,
        by_token=by_token
    )


@router.get("/{contributor_id}/reputation", response_model=ReputationStats)
async def get_contributor_reputation(
    contributor_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get detailed reputation statistics for a contributor."""
    
    try:
        contributor_uuid = UUID(contributor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid contributor ID format")
    
    result = await db.execute(
        select(ContributorDB).where(ContributorDB.id == contributor_uuid)
    )
    contributor = result.scalar_one_or_none()
    
    if not contributor:
        raise HTTPException(status_code=404, detail="Contributor not found")
    
    bounties_result = await db.execute(
        select(BountyDB)
        .where(BountyDB.winner_id == contributor_uuid)
        .where(BountyDB.status == "completed")
        .order_by(BountyDB.updated_at.desc())
        .limit(10)
    )
    bounties = bounties_result.scalars().all()
    
    recent_changes = []
    for i, bounty in enumerate(bounties[:5]):
        recent_changes.append(
            ReputationChange(
                date=bounty.updated_at or bounty.created_at,
                change=bounty.tier * 5,
                reason=f"Completed bounty: {bounty.title[:30]}...",
                new_total=contributor.reputation_score - (len(bounties[:5]) - i - 1) * bounty.tier * 5
            )
        )
    
    return ReputationStats(
        current_score=contributor.reputation_score,
        total_changes=len(bounties),
        recent_changes=recent_changes
    )


@router.get("/{contributor_id}/bounty-history", response_model=List[BountyHistoryItem])
async def get_bounty_history(
    contributor_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Get bounty participation history for a contributor."""
    
    try:
        contributor_uuid = UUID(contributor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid contributor ID format")
    
    query = select(BountyDB).where(
        or_(
            BountyDB.claimant_id == contributor_uuid,
            BountyDB.winner_id == contributor_uuid
        )
    )
    
    if status:
        query = query.where(BountyDB.status == status)
    
    query = query.order_by(BountyDB.updated_at.desc()).offset(offset).limit(limit)
    
    result = await db.execute(query)
    bounties = result.scalars().all()
    
    return [
        BountyHistoryItem(
            id=str(b.id),
            title=b.title,
            status=b.status,
            tier=b.tier,
            reward_amount=b.reward_amount,
            reward_token=b.reward_token,
            completed_at=b.updated_at if b.status == "completed" else None,
            created_at=b.created_at
        ) for b in bounties
    ]