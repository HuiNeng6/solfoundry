"""Contributor profile service."""

from typing import List, Optional
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributor_profile import (
    ContributorDB,
    ContributorProfile,
    ContributorListItem,
    LeaderboardResponse,
    ContributorStats,
    ContributorTier,
)


class ContributorService:
    """Service for contributor profile operations."""
    
    # Points thresholds for tiers
    TIER_THRESHOLDS = {
        ContributorTier.BRONZE: 0,
        ContributorTier.SILVER: 100,
        ContributorTier.GOLD: 500,
        ContributorTier.PLATINUM: 2000,
        ContributorTier.LEGENDARY: 10000,
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_profile(self, github_username: str) -> Optional[ContributorProfile]:
        """
        Get a contributor's full profile.
        
        Args:
            github_username: GitHub username.
            
        Returns:
            ContributorProfile or None if not found.
        """
        query = select(ContributorDB).where(
            ContributorDB.github_username == github_username
        )
        
        result = await self.db.execute(query)
        contributor = result.scalar_one_or_none()
        
        if not contributor:
            return None
        
        # Build stats
        stats = ContributorStats(
            total_prs=contributor.total_prs,
            merged_prs=contributor.merged_prs,
            total_issues=contributor.total_issues,
            closed_issues=contributor.closed_issues,
            total_commits=contributor.total_commits,
            lines_added=contributor.lines_added,
            lines_removed=contributor.lines_removed,
        )
        
        # Get rank
        rank = await self._get_rank(contributor.points)
        
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
    
    async def get_leaderboard(
        self,
        skip: int = 0,
        limit: int = 20,
        tier: Optional[str] = None,
    ) -> LeaderboardResponse:
        """
        Get the contributor leaderboard.
        
        Args:
            skip: Pagination offset.
            limit: Results per page.
            tier: Filter by tier (optional).
            
        Returns:
            LeaderboardResponse with contributors sorted by points.
        """
        conditions = []
        if tier:
            conditions.append(ContributorDB.tier == tier)
        
        filter_condition = conditions[0] if conditions else None
        
        # Count query
        count_query = select(func.count(ContributorDB.id))
        if filter_condition is not None:
            count_query = count_query.where(filter_condition)
        
        # Main query
        query = select(ContributorDB).order_by(desc(ContributorDB.points))
        if filter_condition is not None:
            query = query.where(filter_condition)
        query = query.offset(skip).limit(limit)
        
        # Execute
        result = await self.db.execute(query)
        contributors = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        return LeaderboardResponse(
            items=[ContributorListItem.model_validate(c) for c in contributors],
            total=total,
            skip=skip,
            limit=limit,
        )
    
    async def _get_rank(self, points: int) -> int:
        """Get global rank for a contributor based on points."""
        query = select(func.count(ContributorDB.id)).where(
            ContributorDB.points > points
        )
        result = await self.db.execute(query)
        higher_count = result.scalar() or 0
        return higher_count + 1
    
    @classmethod
    def calculate_tier(cls, points: int) -> str:
        """
        Calculate tier based on points.
        
        Args:
            points: Total points.
            
        Returns:
            Tier name.
        """
        if points >= cls.TIER_THRESHOLDS[ContributorTier.LEGENDARY]:
            return ContributorTier.LEGENDARY.value
        elif points >= cls.TIER_THRESHOLDS[ContributorTier.PLATINUM]:
            return ContributorTier.PLATINUM.value
        elif points >= cls.TIER_THRESHOLDS[ContributorTier.GOLD]:
            return ContributorTier.GOLD.value
        elif points >= cls.TIER_THRESHOLDS[ContributorTier.SILVER]:
            return ContributorTier.SILVER.value
        else:
            return ContributorTier.BRONZE.value