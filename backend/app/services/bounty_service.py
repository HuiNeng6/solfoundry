"""Bounty search and filter service."""

from typing import Optional, List
from sqlalchemy import select, or_, and_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.models.bounty import BountyDB, BountySearchParams, BountyListItem, BountyListResponse, AutocompleteSuggestion, AutocompleteResponse


class BountySearchService:
    """Service for bounty search and filtering."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search_bounties(self, params: BountySearchParams) -> BountyListResponse:
        """
        Full-text search with filtering and sorting.
        
        Uses PostgreSQL tsvector for efficient full-text search.
        All filters are combined with AND logic for predictable results.
        """
        
        # Build filter conditions list
        conditions = []
        
        # Default to open bounties only
        if params.status:
            conditions.append(BountyDB.status == params.status)
        else:
            conditions.append(BountyDB.status == "open")
        
        # Filter by tier
        if params.tier:
            conditions.append(BountyDB.tier == params.tier)
        
        # Filter by category
        if params.category:
            conditions.append(BountyDB.category == params.category)
        
        # Filter by reward range
        if params.reward_min is not None:
            conditions.append(BountyDB.reward_amount >= params.reward_min)
        
        if params.reward_max is not None:
            conditions.append(BountyDB.reward_amount <= params.reward_max)
        
        # Filter by skills (parse comma-separated string)
        skills_list = params.get_skills_list()
        if skills_list:
            for skill in skills_list:
                conditions.append(BountyDB.skills.op('?')(skill))
        
        # Build base queries
        base_filter = and_(*conditions) if conditions else True
        
        # Full-text search using PostgreSQL tsvector
        if params.q:
            ts_query = func.plainto_tsquery('english', params.q)
            search_condition = BountyDB.search_vector.op('@@')(ts_query)
            final_filter = and_(base_filter, search_condition)
        else:
            final_filter = base_filter
        
        # Count query
        count_query = select(func.count(BountyDB.id)).where(final_filter)
        
        # Main query with sorting
        sort_column = {
            "newest": desc(BountyDB.created_at),
            "reward_high": desc(BountyDB.reward_amount),
            "reward_low": asc(BountyDB.reward_amount),
            "deadline": asc(BountyDB.deadline),
            "popularity": desc(BountyDB.popularity),
        }.get(params.sort, desc(BountyDB.created_at))
        
        query = (
            select(BountyDB)
            .where(final_filter)
            .order_by(sort_column)
            .offset(params.skip)
            .limit(params.limit)
        )
        
        # Execute queries
        result = await self.db.execute(query)
        bounties = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        return BountyListResponse(
            items=[BountyListItem.model_validate(b) for b in bounties],
            total=total,
            skip=params.skip,
            limit=params.limit,
        )
    
    async def get_autocomplete_suggestions(self, query: str, limit: int = 10) -> AutocompleteResponse:
        """Get autocomplete suggestions for search."""
        
        suggestions = []
        
        if len(query) < 2:
            return AutocompleteResponse(suggestions=suggestions)
        
        # Search in titles using trigram similarity
        title_query = select(BountyDB.title).where(
            BountyDB.title.ilike(f"%{query}%")
        ).distinct().limit(limit)
        
        result = await self.db.execute(title_query)
        titles = result.scalars().all()
        
        for title in titles:
            suggestions.append(AutocompleteSuggestion(
                text=title,
                type="title"
            ))
        
        # Search in skills
        skill_query = select(func.distinct(func.jsonb_array_elements_text(BountyDB.skills))).where(
            func.jsonb_array_elements_text(BountyDB.skills).ilike(f"{query}%")
        ).limit(limit - len(suggestions))
        
        result = await self.db.execute(skill_query)
        skills = result.scalars().all()
        
        for skill in skills:
            if skill and len(suggestions) < limit:
                suggestions.append(AutocompleteSuggestion(
                    text=skill,
                    type="skill"
                ))
        
        return AutocompleteResponse(suggestions=suggestions)
    
    async def update_search_vector(self, bounty_id: str) -> None:
        """Update the search vector for a bounty after title/description change."""
        
        await self.db.execute(
            text("""
                UPDATE bounties 
                SET search_vector = to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, ''))
                WHERE id = :bounty_id
            """),
            {"bounty_id": bounty_id}
        )
        await self.db.commit()