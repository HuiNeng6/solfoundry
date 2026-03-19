"""Contributor profile API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributor_profile import (
    ContributorProfile,
    LeaderboardResponse,
    ContributorUpdate,
)
from app.services.contributor_service import ContributorService
from app.database import get_db

router = APIRouter(prefix="/contributors", tags=["contributors"])


@router.get("/{username}", response_model=ContributorProfile)
async def get_contributor_profile(
    username: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a contributor's full profile.
    
    - **username**: GitHub username
    
    Returns profile with stats, achievements, and rank.
    """
    service = ContributorService(db)
    profile = await service.get_profile(username)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Contributor not found")
    
    return profile


@router.get("", response_model=LeaderboardResponse)
async def get_leaderboard(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    tier: Optional[str] = Query(None, description="Filter by tier"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the contributor leaderboard.
    
    - **skip**: Pagination offset
    - **limit**: Number of results per page
    - **tier**: Filter by tier (bronze, silver, gold, platinum, legendary)
    
    Returns contributors sorted by points.
    """
    service = ContributorService(db)
    return await service.get_leaderboard(skip=skip, limit=limit, tier=tier)


@router.patch("/{username}", response_model=ContributorProfile)
async def update_contributor_profile(
    username: str,
    update: ContributorUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update a contributor's profile.
    
    - **username**: GitHub username
    - **bio**: New bio (optional)
    - **avatar_url**: New avatar URL (optional)
    
    Returns updated profile.
    """
    from sqlalchemy import select
    from app.models.contributor_profile import ContributorDB
    
    query = select(ContributorDB).where(ContributorDB.github_username == username)
    result = await db.execute(query)
    contributor = result.scalar_one_or_none()
    
    if not contributor:
        raise HTTPException(status_code=404, detail="Contributor not found")
    
    if update.bio is not None:
        contributor.bio = update.bio
    if update.avatar_url is not None:
        contributor.avatar_url = update.avatar_url
    
    # Build response
    from app.models.contributor_profile import ContributorStats
    stats = ContributorStats(
        total_prs=contributor.total_prs,
        merged_prs=contributor.merged_prs,
        total_issues=contributor.total_issues,
        closed_issues=contributor.closed_issues,
        total_commits=contributor.total_commits,
        lines_added=contributor.lines_added,
        lines_removed=contributor.lines_removed,
    )
    
    service = ContributorService(db)
    rank = await service._get_rank(contributor.points)
    
    return ContributorProfile(
        id=str(contributor.id),
        github_username=contributor.github_username,
        avatar_url=contributor.avatar_url,
        bio=contributor.bio,
        stats=stats,
        points=contributor.points,
        tier=contributor.tier,
        achievements=contributor.achievements or [],
        category_stats=contributor.category_stats,
        first_contribution=contributor.first_contribution,
        last_contribution=contributor.last_contribution,
        rank=rank,
    )