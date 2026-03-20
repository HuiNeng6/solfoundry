"""Leaderboard API endpoints.

## Overview

The leaderboard ranks contributors by $FNDRY earned. Features:
- **Time Periods**: Week, month, or all-time
- **Filters**: By tier, category
- **Top 3**: Extra metadata including medal, join date, best bounty

## Time Periods

| Period | Description |
|--------|-------------|
| week | Last 7 days |
| month | Last 30 days |
| all | All time (default) |

## Tier Filters

| Filter | Description |
|--------|-------------|
| 1 | Tier 1 bounties only |
| 2 | Tier 2 bounties only |
| 3 | Tier 3 bounties only |

## Category Filters

| Filter | Description |
|--------|-------------|
| frontend | Frontend work |
| backend | Backend work |
| security | Security work |
| docs | Documentation |
| devops | DevOps/Infrastructure |

## Response Fields

### Leaderboard Entry

| Field | Type | Description |
|-------|------|-------------|
| rank | integer | Position on leaderboard |
| username | string | GitHub username |
| display_name | string | Display name |
| avatar_url | string | Profile picture URL |
| total_earned | float | Total $FNDRY earned |
| bounties_completed | integer | Number of bounties |
| reputation_score | integer | Reputation points |
| wallet_address | string | Solana wallet address |

### Top 3 Metadata (for podium)

| Field | Type | Description |
|-------|------|-------------|
| medal | string | Medal emoji (🥇🥈🥉) |
| join_date | datetime | When they joined |
| best_bounty_title | string | Highest earning bounty |
| best_bounty_earned | float | Amount earned from best bounty |

## Caching

Results are cached for 60 seconds for performance.

## Rate Limit

100 requests per minute.
"""

from typing import Optional

from fastapi import APIRouter, Query

from app.models.leaderboard import (
    CategoryFilter,
    LeaderboardResponse,
    TierFilter,
    TimePeriod,
)
from app.services.leaderboard_service import get_leaderboard

router = APIRouter(prefix="/api", tags=["leaderboard"])


@router.get(
    "/leaderboard",
    response_model=LeaderboardResponse,
    summary="Get contributor leaderboard",
    description="""
Ranked list of contributors by $FNDRY earned.

## Features

- **Time Periods**: Filter by week, month, or all-time
- **Tier Filter**: Show only specific bounty tier earnings
- **Category Filter**: Show only specific category earnings
- **Top 3 Podium**: Extra metadata for top performers

## Example Requests

```
GET /api/leaderboard?period=week
GET /api/leaderboard?period=month&tier=1
GET /api/leaderboard?category=frontend&limit=50
```

## Response Structure

The response includes:
- `top3`: Top 3 contributors with extra metadata (medal, join date, best bounty)
- `entries`: All contributors including top 3 (for consistent display)
- `period`: Current time period filter
- `total`: Total number of contributors in result

## Caching

Results are cached for 60 seconds.

## Rate Limit

100 requests per minute.
""",
    responses={
        200: {
            "description": "Leaderboard data",
            "content": {
                "application/json": {
                    "example": {
                        "period": "all",
                        "total": 150,
                        "offset": 0,
                        "limit": 20,
                        "top3": [
                            {
                                "rank": 1,
                                "username": "topdev",
                                "display_name": "Top Developer",
                                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                                "total_earned": 50000.0,
                                "bounties_completed": 25,
                                "reputation_score": 1500,
                                "wallet_address": "ABC123...",
                                "meta": {
                                    "medal": "🥇",
                                    "join_date": "2024-01-01T00:00:00Z",
                                    "best_bounty_title": "Implement core escrow contract",
                                    "best_bounty_earned": 10000.0
                                }
                            }
                        ],
                        "entries": [
                            {
                                "rank": 1,
                                "username": "topdev",
                                "display_name": "Top Developer",
                                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                                "total_earned": 50000.0,
                                "bounties_completed": 25,
                                "reputation_score": 1500,
                                "wallet_address": "ABC123..."
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def leaderboard(
    period: TimePeriod = Query(
        TimePeriod.all,
        description="Time period: week (last 7 days), month (last 30 days), or all (all-time)"
    ),
    tier: Optional[TierFilter] = Query(
        None,
        description="Filter by bounty tier: 1, 2, or 3"
    ),
    category: Optional[CategoryFilter] = Query(
        None,
        description="Filter by category: frontend, backend, security, docs, devops"
    ),
    limit: int = Query(20, ge=1, le=100, description="Results per page (max 100)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> LeaderboardResponse:
    """Get ranked list of contributors by $FNDRY earned."""
    return get_leaderboard(
        period=period,
        tier=tier,
        category=category,
        limit=limit,
        offset=offset,
    )
