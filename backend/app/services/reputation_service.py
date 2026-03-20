"""Reputation calculation and history service.

This module implements the reputation scoring system for contributors.

Reputation Score Calculation:
================================

Base Score: 0

1. Bounty Completion Score:
   - +10 points per completed bounty
   - Tier multipliers: T1 x1.0, T2 x1.5, T3 x2.0
   - Example: 3 T1 bounties = 30, 2 T3 bounties = 40

2. Success Rate Bonus (0-50 points):
   - Formula: success_rate * 50
   - success_rate = completed / (completed + cancelled)
   - Example: 80% success rate = 40 points

3. Code Quality Bonus (0-30 points):
   - Based on average code review scores (0-5 scale)
   - Formula: (avg_score / 5) * 30
   - Example: 4.2 avg score = 25.2 points

4. Timely Delivery Bonus (0-20 points):
   - Based on on-time completion rate
   - Formula: on_time_rate * 20
   - Example: 90% on-time = 18 points

Total Score = Bounty Completion + Success Rate + Code Quality + Timely Delivery
"""

from __future__ import annotations

import uuid
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from app.models.contributor import ContributorDB
from app.models.reputation import (
    ReputationHistoryDB,
    ReputationBreakdown,
    ReputationStats,
    ReputationChangeEntry,
    ReputationHistoryResponse,
    ReputationRankResponse,
    ReputationChangeSource,
    GlobalLeaderboardEntry,
    GlobalLeaderboardResponse,
    SkillLeaderboardEntry,
    SkillLeaderboardResponse,
    TierLeaderboardEntry,
    TierLeaderboardResponse,
    PeriodLeaderboardEntry,
    PeriodLeaderboardResponse,
)
from app.services.contributor_service import _store

# ---------------------------------------------------------------------------
# In-memory store for reputation history (MVP)
# ---------------------------------------------------------------------------

_reputation_history_store: dict[str, ReputationHistoryDB] = {}

# In-memory cache for leaderboard results
_leaderboard_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 60  # seconds


# ---------------------------------------------------------------------------
# Tier multipliers
# ---------------------------------------------------------------------------

TIER_MULTIPLIERS = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
}


# ---------------------------------------------------------------------------
# Core Reputation Calculation
# ---------------------------------------------------------------------------


def calculate_reputation_score(
    bounties_completed: int,
    bounties_cancelled: int,
    tier_breakdown: dict[str, int],
    avg_review_score: float = 0.0,
    on_time_rate: float = 1.0,
) -> ReputationBreakdown:
    """Calculate detailed reputation score breakdown.
    
    Args:
        bounties_completed: Number of completed bounties
        bounties_cancelled: Number of cancelled bounties
        tier_breakdown: Dict with 'tier1', 'tier2', 'tier3' counts
        avg_review_score: Average code review score (0-5)
        on_time_rate: Rate of on-time completions (0-1)
    
    Returns:
        ReputationBreakdown with all components
    """
    # 1. Bounty Completion Score with tier multipliers
    tier1 = tier_breakdown.get("tier1", 0)
    tier2 = tier_breakdown.get("tier2", 0)
    tier3 = tier_breakdown.get("tier3", 0)
    
    bounty_score = (
        tier1 * 10 * TIER_MULTIPLIERS[1] +
        tier2 * 10 * TIER_MULTIPLIERS[2] +
        tier3 * 10 * TIER_MULTIPLIERS[3]
    )
    
    tier_multipliers = {
        "tier1": tier1 * 10 * TIER_MULTIPLIERS[1],
        "tier2": tier2 * 10 * TIER_MULTIPLIERS[2],
        "tier3": tier3 * 10 * TIER_MULTIPLIERS[3],
    }
    
    # 2. Success Rate Bonus (0-50)
    total_attempts = bounties_completed + bounties_cancelled
    if total_attempts > 0:
        success_rate = bounties_completed / total_attempts
    else:
        success_rate = 1.0
    success_rate_score = int(success_rate * 50)
    
    # 3. Code Quality Bonus (0-30)
    code_quality_score = int((avg_review_score / 5.0) * 30) if avg_review_score else 0
    
    # 4. Timely Delivery Bonus (0-20)
    timely_delivery_score = int(on_time_rate * 20)
    
    total = int(bounty_score + success_rate_score + code_quality_score + timely_delivery_score)
    
    return ReputationBreakdown(
        base_score=0,
        bounty_completion_score=int(bounty_score),
        success_rate_score=success_rate_score,
        code_quality_score=code_quality_score,
        timely_delivery_score=timely_delivery_score,
        tier_multipliers=tier_multipliers,
        total_score=total,
    )


def calculate_contributor_reputation(contributor: ContributorDB) -> ReputationBreakdown:
    """Calculate reputation for a contributor from their stats.
    
    Uses contributor's stored stats plus any additional metrics.
    For MVP, we use approximations for code quality and on-time rate.
    """
    # Extract tier breakdown from badges (e.g., "tier-1" badge)
    tier_breakdown = {"tier1": 0, "tier2": 0, "tier3": 0}
    for badge in (contributor.badges or []):
        if badge == "tier-1":
            tier_breakdown["tier1"] += 1
        elif badge == "tier-2":
            tier_breakdown["tier2"] += 1
        elif badge == "tier-3":
            tier_breakdown["tier3"] += 1
    
    # For MVP, assume good code quality and on-time delivery
    # In production, these would come from actual metrics
    avg_review_score = 4.0 if contributor.total_bounties_completed > 0 else 0.0
    on_time_rate = 0.9 if contributor.total_bounties_completed > 0 else 1.0
    
    # Estimate cancelled bounties (would be tracked separately in production)
    bounties_cancelled = max(0, contributor.total_bounties_completed // 10)  # Assume 10% cancellation
    
    return calculate_reputation_score(
        bounties_completed=contributor.total_bounties_completed,
        bounties_cancelled=bounties_cancelled,
        tier_breakdown=tier_breakdown,
        avg_review_score=avg_review_score,
        on_time_rate=on_time_rate,
    )


def get_contributor_stats(contributor: ContributorDB) -> ReputationStats:
    """Get detailed stats for a contributor."""
    # Extract tier breakdown from badges
    tier_breakdown = {"tier1": 0, "tier2": 0, "tier3": 0}
    for badge in (contributor.badges or []):
        if badge == "tier-1":
            tier_breakdown["tier1"] += 1
        elif badge == "tier-2":
            tier_breakdown["tier2"] += 1
        elif badge == "tier-3":
            tier_breakdown["tier3"] += 1
    
    # Estimate metrics for MVP
    bounties_cancelled = max(0, contributor.total_bounties_completed // 10)
    total_claimed = contributor.total_bounties_completed + bounties_cancelled
    
    success_rate = contributor.total_bounties_completed / total_claimed if total_claimed > 0 else 1.0
    on_time_rate = 0.9 if contributor.total_bounties_completed > 0 else 1.0
    
    return ReputationStats(
        total_bounties_claimed=total_claimed,
        bounties_completed=contributor.total_bounties_completed,
        bounties_cancelled=bounties_cancelled,
        success_rate=success_rate,
        avg_review_score=4.0 if contributor.total_bounties_completed > 0 else 0.0,
        on_time_rate=on_time_rate,
        tier_breakdown=tier_breakdown,
    )


# ---------------------------------------------------------------------------
# Reputation History Management
# ---------------------------------------------------------------------------


def add_reputation_change(
    contributor_id: str,
    score_before: int,
    score_after: int,
    source: ReputationChangeSource,
    bounty_id: Optional[str] = None,
    description: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> ReputationHistoryDB:
    """Record a reputation change event.
    
    Args:
        contributor_id: UUID of the contributor
        score_before: Reputation score before change
        score_after: Reputation score after change
        source: Source of the change
        bounty_id: Related bounty if applicable
        description: Human-readable description
        metadata: Additional data as dict
    
    Returns:
        Created ReputationHistoryDB record
    """
    record = ReputationHistoryDB(
        id=uuid.uuid4(),
        contributor_id=uuid.UUID(contributor_id),
        score_before=score_before,
        score_after=score_after,
        change=score_after - score_before,
        source=source.value,
        bounty_id=uuid.UUID(bounty_id) if bounty_id else None,
        description=description,
        metadata=json.dumps(metadata) if metadata else None,
        created_at=datetime.now(timezone.utc),
    )
    
    _reputation_history_store[str(record.id)] = record
    return record


def get_reputation_history(
    contributor_id: str,
    skip: int = 0,
    limit: int = 50,
    source_filter: Optional[str] = None,
) -> tuple[List[ReputationHistoryDB], int]:
    """Get paginated reputation history for a contributor.
    
    Args:
        contributor_id: UUID of the contributor
        skip: Pagination offset
        limit: Max results
        source_filter: Optional source type filter
    
    Returns:
        Tuple of (history records, total count)
    """
    cid = uuid.UUID(contributor_id)
    
    records = [
        r for r in _reputation_history_store.values()
        if r.contributor_id == cid
    ]
    
    if source_filter:
        records = [r for r in records if r.source == source_filter]
    
    # Sort by created_at descending
    records.sort(key=lambda r: r.created_at, reverse=True)
    
    total = len(records)
    return records[skip:skip + limit], total


def get_reputation_history_response(
    contributor_id: str,
    contributor: ContributorDB,
    skip: int = 0,
    limit: int = 50,
) -> ReputationHistoryResponse:
    """Get full reputation info for a contributor."""
    history, total = get_reputation_history(contributor_id, skip, limit)
    
    breakdown = calculate_contributor_reputation(contributor)
    stats = get_contributor_stats(contributor)
    
    history_entries = [
        ReputationChangeEntry(
            id=str(h.id),
            score_before=h.score_before,
            score_after=h.score_after,
            change=h.change,
            source=h.source,
            bounty_id=str(h.bounty_id) if h.bounty_id else None,
            description=h.description,
            created_at=h.created_at,
        )
        for h in history
    ]
    
    return ReputationHistoryResponse(
        contributor_id=contributor_id,
        current_score=contributor.reputation_score,
        breakdown=breakdown,
        stats=stats,
        history=history_entries,
        total_history=total,
        skip=skip,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Global Leaderboard
# ---------------------------------------------------------------------------


def invalidate_leaderboard_cache() -> None:
    """Clear the leaderboard cache."""
    _leaderboard_cache.clear()


def _cache_key(prefix: str, **kwargs) -> str:
    """Generate cache key from parameters."""
    parts = [prefix]
    for k, v in sorted(kwargs.items()):
        if v is not None:
            parts.append(f"{k}={v}")
    return ":".join(parts)


def get_global_leaderboard(
    period: str = "all",
    limit: int = 20,
    offset: int = 0,
) -> GlobalLeaderboardResponse:
    """Get global reputation leaderboard.
    
    Args:
        period: Time period (week, month, all)
        limit: Results per page
        offset: Pagination offset
    
    Returns:
        GlobalLeaderboardResponse with ranked entries
    """
    key = _cache_key("global", period=period)
    now = time.time()
    
    # Check cache
    if key in _leaderboard_cache:
        cached_at, cached_full = _leaderboard_cache[key]
        if now - cached_at < CACHE_TTL:
            entries = cached_full.entries[offset:offset + limit]
            return GlobalLeaderboardResponse(
                period=period,
                total=cached_full.total,
                offset=offset,
                limit=limit,
                top3=cached_full.top3,
                entries=entries,
            )
    
    # Build fresh leaderboard
    contributors = list(_store.values())
    
    # Filter by time period (using created_at as proxy)
    cutoff = _period_cutoff(period)
    if cutoff:
        # For MVP, we don't have historical data, so just use current contributors
        pass
    
    # Sort by reputation_score desc, then total_earnings desc
    contributors.sort(
        key=lambda c: (-c.reputation_score, -c.total_earnings, c.username),
    )
    
    def to_entry(rank: int, c: ContributorDB) -> GlobalLeaderboardEntry:
        total = c.total_bounties_completed + max(0, c.total_bounties_completed // 10)
        success_rate = c.total_bounties_completed / total if total > 0 else 1.0
        
        return GlobalLeaderboardEntry(
            rank=rank,
            username=c.username,
            display_name=c.display_name,
            avatar_url=c.avatar_url,
            reputation_score=c.reputation_score,
            total_earnings=c.total_earnings,
            bounties_completed=c.total_bounties_completed,
            success_rate=round(success_rate, 2),
            badges=c.badges or [],
            skills=c.skills or [],
        )
    
    top3 = [to_entry(i, c) for i, c in enumerate(contributors[:3], start=1)]
    all_entries = [to_entry(i, c) for i, c in enumerate(contributors, start=1)]
    
    full = GlobalLeaderboardResponse(
        period=period,
        total=len(all_entries),
        offset=0,
        limit=len(all_entries),
        top3=top3,
        entries=all_entries,
    )
    
    _leaderboard_cache[key] = (now, full)
    
    return GlobalLeaderboardResponse(
        period=period,
        total=full.total,
        offset=offset,
        limit=limit,
        top3=top3,
        entries=all_entries[offset:offset + limit],
    )


# ---------------------------------------------------------------------------
# Skill Leaderboard
# ---------------------------------------------------------------------------


def get_skill_leaderboard(
    skill: str,
    period: str = "all",
    limit: int = 20,
    offset: int = 0,
) -> SkillLeaderboardResponse:
    """Get leaderboard for contributors with a specific skill.
    
    Args:
        skill: Skill to filter by (e.g., 'frontend', 'backend')
        period: Time period (week, month, all)
        limit: Results per page
        offset: Pagination offset
    
    Returns:
        SkillLeaderboardResponse
    """
    key = _cache_key("skill", skill=skill, period=period)
    now = time.time()
    
    if key in _leaderboard_cache:
        cached_at, cached_full = _leaderboard_cache[key]
        if now - cached_at < CACHE_TTL:
            entries = cached_full.entries[offset:offset + limit]
            return SkillLeaderboardResponse(
                skill=skill,
                period=period,
                total=cached_full.total,
                entries=entries,
            )
    
    # Filter contributors with this skill
    contributors = [
        c for c in _store.values()
        if skill in (c.skills or [])
    ]
    
    # Sort by reputation
    contributors.sort(key=lambda c: (-c.reputation_score, c.username))
    
    def to_entry(rank: int, c: ContributorDB) -> SkillLeaderboardEntry:
        # Estimate bounties in this skill (MVP: use total)
        return SkillLeaderboardEntry(
            rank=rank,
            username=c.username,
            display_name=c.display_name,
            avatar_url=c.avatar_url,
            skill_score=c.reputation_score,  # MVP: use total reputation
            bounties_in_skill=c.total_bounties_completed,
            reputation_score=c.reputation_score,
        )
    
    all_entries = [to_entry(i, c) for i, c in enumerate(contributors, start=1)]
    
    full = SkillLeaderboardResponse(
        skill=skill,
        period=period,
        total=len(all_entries),
        entries=all_entries,
    )
    
    _leaderboard_cache[key] = (now, full)
    
    return SkillLeaderboardResponse(
        skill=skill,
        period=period,
        total=full.total,
        entries=all_entries[offset:offset + limit],
    )


# ---------------------------------------------------------------------------
# Tier Leaderboard
# ---------------------------------------------------------------------------


def get_tier_leaderboard(
    tier: int,
    period: str = "all",
    limit: int = 20,
    offset: int = 0,
) -> TierLeaderboardResponse:
    """Get leaderboard for contributors who completed bounties in a tier.
    
    Args:
        tier: Bounty tier (1, 2, or 3)
        period: Time period (week, month, all)
        limit: Results per page
        offset: Pagination offset
    
    Returns:
        TierLeaderboardResponse
    """
    key = _cache_key("tier", tier=tier, period=period)
    now = time.time()
    
    if key in _leaderboard_cache:
        cached_at, cached_full = _leaderboard_cache[key]
        if now - cached_at < CACHE_TTL:
            entries = cached_full.entries[offset:offset + limit]
            return TierLeaderboardResponse(
                tier=tier,
                period=period,
                total=cached_full.total,
                entries=entries,
            )
    
    # Filter contributors with tier badge
    tier_badge = f"tier-{tier}"
    contributors = [
        c for c in _store.values()
        if tier_badge in (c.badges or [])
    ]
    
    # Sort by reputation
    contributors.sort(key=lambda c: (-c.reputation_score, c.username))
    
    def to_entry(rank: int, c: ContributorDB) -> TierLeaderboardEntry:
        return TierLeaderboardEntry(
            rank=rank,
            username=c.username,
            display_name=c.display_name,
            avatar_url=c.avatar_url,
            tier_bounties=1,  # MVP: count badge once
            tier_earnings=c.total_earnings,  # MVP: use total
            reputation_score=c.reputation_score,
        )
    
    all_entries = [to_entry(i, c) for i, c in enumerate(contributors, start=1)]
    
    full = TierLeaderboardResponse(
        tier=tier,
        period=period,
        total=len(all_entries),
        entries=all_entries,
    )
    
    _leaderboard_cache[key] = (now, full)
    
    return TierLeaderboardResponse(
        tier=tier,
        period=period,
        total=full.total,
        entries=all_entries[offset:offset + limit],
    )


# ---------------------------------------------------------------------------
# Period Leaderboard
# ---------------------------------------------------------------------------


def _period_cutoff(period: str) -> Optional[datetime]:
    """Get the cutoff datetime for a period."""
    now = datetime.now(timezone.utc)
    if period == "week":
        return now - timedelta(days=7)
    if period == "month":
        return now - timedelta(days=30)
    return None


def get_period_leaderboard(
    period: str,
    limit: int = 20,
    offset: int = 0,
) -> PeriodLeaderboardResponse:
    """Get leaderboard for a specific time period.
    
    Args:
        period: Time period (week, month, all)
        limit: Results per page
        offset: Pagination offset
    
    Returns:
        PeriodLeaderboardResponse
    """
    key = _cache_key("period", period=period)
    now = time.time()
    
    if key in _leaderboard_cache:
        cached_at, cached_full = _leaderboard_cache[key]
        if now - cached_at < CACHE_TTL:
            entries = cached_full.entries[offset:offset + limit]
            return PeriodLeaderboardResponse(
                period=period,
                start_date=cached_full.start_date,
                end_date=cached_full.end_date,
                total=cached_full.total,
                entries=entries,
            )
    
    cutoff = _period_cutoff(period)
    end_date = datetime.now(timezone.utc)
    
    if period == "week":
        start_date = end_date - timedelta(days=7)
    elif period == "month":
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime(2020, 1, 1, tzinfo=timezone.utc)  # All time
    
    # For MVP, use created_at as filter (actual implementation would use payout timestamps)
    if cutoff:
        contributors = [
            c for c in _store.values()
            if c.created_at and c.created_at >= cutoff
        ]
    else:
        contributors = list(_store.values())
    
    contributors.sort(key=lambda c: (-c.reputation_score, -c.total_earnings, c.username))
    
    def to_entry(rank: int, c: ContributorDB) -> PeriodLeaderboardEntry:
        return PeriodLeaderboardEntry(
            rank=rank,
            username=c.username,
            display_name=c.display_name,
            avatar_url=c.avatar_url,
            period_earnings=c.total_earnings,
            period_bounties=c.total_bounties_completed,
            reputation_change=c.reputation_score,  # MVP: use total
            total_reputation=c.reputation_score,
        )
    
    all_entries = [to_entry(i, c) for i, c in enumerate(contributors, start=1)]
    
    full = PeriodLeaderboardResponse(
        period=period,
        start_date=start_date,
        end_date=end_date,
        total=len(all_entries),
        entries=all_entries,
    )
    
    _leaderboard_cache[key] = (now, full)
    
    return PeriodLeaderboardResponse(
        period=period,
        start_date=start_date,
        end_date=end_date,
        total=full.total,
        entries=all_entries[offset:offset + limit],
    )


# ---------------------------------------------------------------------------
# Reputation Rank
# ---------------------------------------------------------------------------


def get_contributor_rank(contributor_id: str) -> ReputationRankResponse:
    """Get a contributor's rank across various leaderboards.
    
    Args:
        contributor_id: UUID of the contributor
    
    Returns:
        ReputationRankResponse with rankings
    """
    contributor = _store.get(contributor_id)
    if not contributor:
        return ReputationRankResponse(global_rank=0, global_total=0, percentile=0.0)
    
    # Global rank
    contributors = sorted(
        _store.values(),
        key=lambda c: (-c.reputation_score, -c.total_earnings, c.username),
    )
    
    global_rank = 0
    for i, c in enumerate(contributors, start=1):
        if str(c.id) == contributor_id:
            global_rank = i
            break
    
    global_total = len(contributors)
    percentile = (1 - (global_rank / global_total)) * 100 if global_total > 0 else 0.0
    
    # Category ranks (by skill)
    category_ranks: Dict[str, int] = {}
    for skill in (contributor.skills or []):
        skill_contributors = [
            c for c in _store.values()
            if skill in (c.skills or [])
        ]
        skill_contributors.sort(key=lambda c: (-c.reputation_score, c.username))
        
        for i, c in enumerate(skill_contributors, start=1):
            if str(c.id) == contributor_id:
                category_ranks[skill] = i
                break
    
    # Tier ranks
    tier_ranks: Dict[str, int] = {}
    for tier in [1, 2, 3]:
        tier_badge = f"tier-{tier}"
        if tier_badge not in (contributor.badges or []):
            continue
        
        tier_contributors = [
            c for c in _store.values()
            if tier_badge in (c.badges or [])
        ]
        tier_contributors.sort(key=lambda c: (-c.reputation_score, c.username))
        
        for i, c in enumerate(tier_contributors, start=1):
            if str(c.id) == contributor_id:
                tier_ranks[f"tier{tier}"] = i
                break
    
    return ReputationRankResponse(
        global_rank=global_rank,
        global_total=global_total,
        category_ranks=category_ranks,
        tier_ranks=tier_ranks,
        percentile=round(percentile, 1),
    )


# ---------------------------------------------------------------------------
# Update Reputation
# ---------------------------------------------------------------------------


def update_contributor_reputation(
    contributor_id: str,
    source: ReputationChangeSource,
    bounty_id: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[int]:
    """Update a contributor's reputation score.
    
    Recalculates the reputation based on current stats and records the change.
    
    Args:
        contributor_id: UUID of the contributor
        source: Source of the update
        bounty_id: Related bounty if applicable
        description: Description of the change
    
    Returns:
        New reputation score, or None if contributor not found
    """
    contributor = _store.get(contributor_id)
    if not contributor:
        return None
    
    old_score = contributor.reputation_score
    breakdown = calculate_contributor_reputation(contributor)
    new_score = breakdown.total_score
    
    if old_score != new_score:
        contributor.reputation_score = new_score
        contributor.updated_at = datetime.now(timezone.utc)
        
        add_reputation_change(
            contributor_id=contributor_id,
            score_before=old_score,
            score_after=new_score,
            source=source,
            bounty_id=bounty_id,
            description=description,
            metadata={"breakdown": breakdown.model_dump()},
        )
        
        # Invalidate leaderboard cache
        invalidate_leaderboard_cache()
    
    return new_score