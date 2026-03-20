"""Reputation and Ranking API endpoints.

This module provides endpoints for:
- Global reputation leaderboard
- Skill-based leaderboards
- Tier-based leaderboards
- Period-based leaderboards
- Individual contributor reputation details and history
"""

from typing import Optional

from fastapi import APIRouter, Query, HTTPException, Path

from app.models.reputation import (
    ReputationHistoryResponse,
    ReputationRankResponse,
    GlobalLeaderboardResponse,
    SkillLeaderboardResponse,
    TierLeaderboardResponse,
    PeriodLeaderboardResponse,
)
from app.services.reputation_service import (
    get_global_leaderboard,
    get_skill_leaderboard,
    get_tier_leaderboard,
    get_period_leaderboard,
    get_reputation_history_response,
    get_contributor_rank,
)
from app.services.contributor_service import _store, get_contributor

router = APIRouter(prefix="/api", tags=["reputation"])


# ---------------------------------------------------------------------------
# Global Leaderboard
# ---------------------------------------------------------------------------


@router.get(
    "/reputation/leaderboard",
    response_model=GlobalLeaderboardResponse,
    summary="Global Reputation Leaderboard",
    description="""
    Get the global reputation leaderboard ranked by reputation score.
    
    The reputation score is calculated from:
    - Bounty completion points (with tier multipliers)
    - Success rate bonus (0-50 points)
    - Code quality bonus (0-30 points)
    - Timely delivery bonus (0-20 points)
    
    Top 3 contributors are highlighted with extra metadata.
    Results are cached for 60 seconds.
    """,
)
async def global_leaderboard(
    period: str = Query("all", description="Time period: week, month, or all", pattern="^(week|month|all)$"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> GlobalLeaderboardResponse:
    """Global reputation leaderboard."""
    return get_global_leaderboard(period=period, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Skill Leaderboard
# ---------------------------------------------------------------------------


@router.get(
    "/reputation/leaderboard/skill/{skill}",
    response_model=SkillLeaderboardResponse,
    summary="Skill-based Leaderboard",
    description="""
    Get leaderboard for contributors with a specific skill.
    
    Skills include: frontend, backend, smart_contract, documentation, testing, infrastructure
    
    Contributors are ranked by their reputation score within that skill category.
    """,
)
async def skill_leaderboard(
    skill: str = Path(..., description="Skill to filter by", examples=["frontend", "backend"]),
    period: str = Query("all", description="Time period: week, month, or all", pattern="^(week|month|all)$"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> SkillLeaderboardResponse:
    """Leaderboard for a specific skill."""
    return get_skill_leaderboard(skill=skill, period=period, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Tier Leaderboard
# ---------------------------------------------------------------------------


@router.get(
    "/reputation/leaderboard/tier/{tier}",
    response_model=TierLeaderboardResponse,
    summary="Tier-based Leaderboard",
    description="""
    Get leaderboard for contributors who completed bounties in a specific tier.
    
    Tiers:
    - Tier 1: Simple tasks, 72-hour deadline, x1 multiplier
    - Tier 2: Medium tasks, 7-day deadline, x1.5 multiplier
    - Tier 3: Complex tasks, 30-day deadline, x2 multiplier
    """,
)
async def tier_leaderboard(
    tier: int = Path(..., ge=1, le=3, description="Bounty tier (1, 2, or 3)"),
    period: str = Query("all", description="Time period: week, month, or all", pattern="^(week|month|all)$"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> TierLeaderboardResponse:
    """Leaderboard for a specific bounty tier."""
    return get_tier_leaderboard(tier=tier, period=period, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Period Leaderboard
# ---------------------------------------------------------------------------


@router.get(
    "/reputation/leaderboard/period/{period}",
    response_model=PeriodLeaderboardResponse,
    summary="Period-based Leaderboard",
    description="""
    Get leaderboard for a specific time period.
    
    Periods:
    - week: Last 7 days
    - month: Last 30 days
    - all: All time
    
    Shows earnings and bounties completed within the period.
    """,
)
async def period_leaderboard(
    period: str = Path(..., description="Time period", pattern="^(week|month|all)$"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> PeriodLeaderboardResponse:
    """Leaderboard for a specific time period."""
    return get_period_leaderboard(period=period, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Contributor Reputation Details
# ---------------------------------------------------------------------------


@router.get(
    "/reputation/{contributor_id}",
    response_model=ReputationHistoryResponse,
    summary="Contributor Reputation Details",
    description="""
    Get detailed reputation information for a contributor.
    
    Includes:
    - Current reputation score
    - Score breakdown by component
    - Statistics used for calculation
    - Recent reputation change history
    """,
)
async def contributor_reputation(
    contributor_id: str = Path(..., description="Contributor UUID"),
    skip: int = Query(0, ge=0, description="History pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="History page size"),
) -> ReputationHistoryResponse:
    """Get detailed reputation info for a contributor."""
    contributor = _store.get(contributor_id)
    if not contributor:
        raise HTTPException(status_code=404, detail="Contributor not found")
    
    return get_reputation_history_response(
        contributor_id=contributor_id,
        contributor=contributor,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/reputation/{contributor_id}/rank",
    response_model=ReputationRankResponse,
    summary="Contributor Rankings",
    description="""
    Get a contributor's rank across various leaderboards.
    
    Includes:
    - Global rank and percentile
    - Rank within each skill category
    - Rank within each bounty tier
    """,
)
async def contributor_rank(
    contributor_id: str = Path(..., description="Contributor UUID"),
) -> ReputationRankResponse:
    """Get contributor's rank in various leaderboards."""
    contributor = _store.get(contributor_id)
    if not contributor:
        raise HTTPException(status_code=404, detail="Contributor not found")
    
    return get_contributor_rank(contributor_id)


# ---------------------------------------------------------------------------
# Available Skills Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/reputation/skills",
    summary="List Available Skills",
    description="Get list of all skills that can be used for skill-based leaderboards.",
)
async def list_skills():
    """List all available skills for filtering."""
    return {
        "skills": [
            {"id": "frontend", "name": "Frontend", "description": "UI/UX, React, Vue, CSS"},
            {"id": "backend", "name": "Backend", "description": "APIs, databases, server-side"},
            {"id": "smart_contract", "name": "Smart Contracts", "description": "Solana, Solidity, blockchain"},
            {"id": "documentation", "name": "Documentation", "description": "Docs, tutorials, guides"},
            {"id": "testing", "name": "Testing", "description": "Unit tests, integration tests, QA"},
            {"id": "infrastructure", "name": "Infrastructure", "description": "DevOps, CI/CD, cloud"},
        ]
    }


# ---------------------------------------------------------------------------
# Reputation Summary Endpoint
# ---------------------------------------------------------------------------


@router.get(
    "/reputation/summary",
    summary="Reputation System Summary",
    description="Get a summary of the reputation system including total contributors and statistics.",
)
async def reputation_summary():
    """Get overall reputation system statistics."""
    contributors = list(_store.values())
    
    if not contributors:
        return {
            "total_contributors": 0,
            "total_reputation": 0,
            "avg_reputation": 0,
            "top_contributor": None,
            "tiers": {"tier1": 0, "tier2": 0, "tier3": 0},
        }
    
    total_rep = sum(c.reputation_score for c in contributors)
    avg_rep = total_rep / len(contributors)
    
    # Count tier badges
    tiers = {"tier1": 0, "tier2": 0, "tier3": 0}
    for c in contributors:
        for badge in (c.badges or []):
            if badge == "tier-1":
                tiers["tier1"] += 1
            elif badge == "tier-2":
                tiers["tier2"] += 1
            elif badge == "tier-3":
                tiers["tier3"] += 1
    
    # Top contributor
    top = max(contributors, key=lambda c: c.reputation_score)
    
    return {
        "total_contributors": len(contributors),
        "total_reputation": total_rep,
        "avg_reputation": round(avg_rep, 1),
        "top_contributor": {
            "username": top.username,
            "display_name": top.display_name,
            "reputation_score": top.reputation_score,
        } if top else None,
        "tiers": tiers,
    }