"""Bounty search and filter API endpoints.

## Overview

Bounties are paid work opportunities on SolFoundry. Each bounty has:
- **Tier**: Difficulty level (1-3) determining reward range and deadline
- **Category**: Work type (frontend, backend, smart_contract, etc.)
- **Status**: Lifecycle state (open, claimed, completed, cancelled)
- **Reward**: $FNDRY token amount

## Bounty Tiers

| Tier | Reward Range | Deadline | Access |
|------|-------------|----------|--------|
| 1 | 50 - 500 $FNDRY | 72 hours | Open race |
| 2 | 500 - 5,000 $FNDRY | 7 days | 4+ merged T1 bounties |
| 3 | 5,000 - 50,000 $FNDRY | 14-30 days | 3+ merged T2 bounties |

## Categories

- `frontend`: UI/UX, React, Vue, CSS
- `backend`: API, database, services
- `smart_contract`: Solana programs, Anchor
- `documentation`: Docs, guides, README
- `testing`: Unit tests, integration tests
- `infrastructure`: DevOps, CI/CD, deployment
- `other`: Miscellaneous

## Status Lifecycle

```
open → claimed → completed
  │        │
  └────────┴──→ cancelled
```

## Rate Limits

- Search endpoints: 100 requests/minute
- CRUD operations: 30 requests/minute
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.bounty import (
    BountyDB,
    BountySearchParams,
    BountyListResponse,
    BountyResponse,
    BountyCreate,
    BountyUpdate,
    AutocompleteResponse,
)
from app.services.bounty_service import BountySearchService
from app.database import get_db

router = APIRouter(prefix="/api/bounties", tags=["bounties"])


@router.get(
    "/search",
    response_model=BountyListResponse,
    summary="Search and filter bounties",
    description="""
Full-text search and filter for bounties.

## Search Features

- **Full-text search**: Searches across title and description
- **Multi-filter support**: Combine tier, category, status, reward range, skills
- **Multiple sort options**: By date, reward, deadline, or popularity
- **Pagination**: Efficient browsing with skip/limit

## Example Requests

```
GET /api/bounties/search?q=smart+contract&tier=1&status=open
GET /api/bounties/search?category=frontend&reward_min=100&reward_max=500
GET /api/bounties/search?skills=rust,anchor&sort=reward_high
```

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| items | array | List of bounty objects |
| total | integer | Total matching results |
| skip | integer | Current pagination offset |
| limit | integer | Results per page |

## Rate Limit

100 requests per minute.
""",
    responses={
        200: {
            "description": "Successful search results",
            "content": {
                "application/json": {
                    "example": {
                        "items": [
                            {
                                "id": "550e8400-e29b-41d4-a716-446655440000",
                                "title": "Implement wallet connection component",
                                "description": "Create a React component for Solana wallet connection",
                                "tier": 1,
                                "category": "frontend",
                                "status": "open",
                                "reward_amount": 200.0,
                                "reward_token": "FNDRY",
                                "deadline": "2024-01-15T00:00:00Z",
                                "skills": ["react", "typescript", "solana"],
                                "popularity": 42,
                                "created_at": "2024-01-01T00:00:00Z"
                            }
                        ],
                        "total": 25,
                        "skip": 0,
                        "limit": 20
                    }
                }
            }
        },
        422: {"description": "Invalid query parameters"}
    }
)
async def search_bounties(
    q: Optional[str] = Query(
        None,
        description="Full-text search query for title and description",
        example="smart contract"
    ),
    tier: Optional[int] = Query(
        None,
        ge=1,
        le=3,
        description="Filter by bounty tier (1, 2, or 3)",
        example=1
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by category: frontend, backend, smart_contract, documentation, testing, infrastructure, other",
        example="frontend"
    ),
    status: Optional[str] = Query(
        None,
        description="Filter by status: open, claimed, completed, cancelled",
        example="open"
    ),
    reward_min: Optional[float] = Query(
        None,
        ge=0,
        description="Minimum reward amount in $FNDRY",
        example=100.0
    ),
    reward_max: Optional[float] = Query(
        None,
        ge=0,
        description="Maximum reward amount in $FNDRY",
        example=500.0
    ),
    skills: Optional[str] = Query(
        None,
        description="Comma-separated list of required skills",
        example="react,typescript"
    ),
    sort: str = Query(
        "newest",
        pattern="^(newest|reward_high|reward_low|deadline|popularity)$",
        description="Sort order: newest, reward_high, reward_low, deadline, popularity"
    ),
    skip: int = Query(
        0,
        ge=0,
        description="Pagination offset (number of items to skip)"
    ),
    limit: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of results per page (max 100)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Search bounties with full-text search and filters.
    
    Supports combining multiple filters for precise results.
    """
    
    params = BountySearchParams(
        q=q,
        tier=tier,
        category=category,
        status=status,
        reward_min=reward_min,
        reward_max=reward_max,
        skills=skills,
        sort=sort,
        skip=skip,
        limit=limit,
    )
    
    service = BountySearchService(db)
    return await service.search_bounties(params)


@router.get(
    "/autocomplete",
    response_model=AutocompleteResponse,
    summary="Get autocomplete suggestions",
    description="""
Get autocomplete suggestions for bounty search.

Returns matching bounty titles and skills based on the query string.
Minimum query length is 2 characters.

## Use Case

Use this endpoint to implement search suggestions as users type.
Results include both bounty titles and skill names.

## Rate Limit

100 requests per minute.
""",
    responses={
        200: {
            "description": "Autocomplete suggestions",
            "content": {
                "application/json": {
                    "example": {
                        "suggestions": [
                            {"text": "smart contract", "type": "skill"},
                            {"text": "Smart contract audit", "type": "title"},
                            {"text": "smart_contract", "type": "category"}
                        ]
                    }
                }
            }
        }
    }
)
async def get_autocomplete(
    q: str = Query(
        ...,
        min_length=2,
        description="Search query for autocomplete (minimum 2 characters)",
        example="sm"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=20,
        description="Number of suggestions to return (max 20)"
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get autocomplete suggestions for bounty search.
    
    Returns matching bounty titles and skills.
    """
    service = BountySearchService(db)
    return await service.get_autocomplete_suggestions(q, limit)


@router.get(
    "/{bounty_id}",
    response_model=BountyResponse,
    summary="Get a single bounty",
    description="""
Retrieve detailed information about a specific bounty.

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique bounty identifier (UUID) |
| title | string | Bounty title |
| description | string | Full bounty description |
| tier | integer | Difficulty tier (1-3) |
| category | string | Work category |
| status | string | Current status |
| reward_amount | float | $FNDRY reward amount |
| reward_token | string | Token symbol (always "FNDRY") |
| deadline | datetime | Submission deadline |
| skills | array | Required skills |
| github_issue_url | string | Link to GitHub issue |
| claimant_id | string | ID of user who claimed (if claimed) |
| winner_id | string | ID of winner (if completed) |
| popularity | integer | View/interest count |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

## Rate Limit

100 requests per minute.
""",
    responses={
        200: {
            "description": "Bounty details",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Implement wallet connection component",
                        "description": "Create a React component for Solana wallet connection using Phantom wallet adapter.",
                        "tier": 1,
                        "category": "frontend",
                        "status": "open",
                        "reward_amount": 200.0,
                        "reward_token": "FNDRY",
                        "deadline": "2024-01-15T00:00:00Z",
                        "skills": ["react", "typescript", "solana"],
                        "github_issue_url": "https://github.com/SolFoundry/solfoundry/issues/123",
                        "github_issue_number": 123,
                        "github_repo": "SolFoundry/solfoundry",
                        "claimant_id": None,
                        "winner_id": None,
                        "popularity": 42,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        404: {"description": "Bounty not found"}
    }
)
async def get_bounty(
    bounty_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single bounty by ID."""
    from sqlalchemy import select
    from app.models.bounty import BountyDB
    
    query = select(BountyDB).where(BountyDB.id == bounty_id)
    result = await db.execute(query)
    bounty = result.scalar_one_or_none()
    
    if not bounty:
        raise HTTPException(status_code=404, detail="Bounty not found")
    
    return BountyResponse.model_validate(bounty)


@router.post(
    "/",
    response_model=BountyResponse,
    status_code=201,
    summary="Create a new bounty",
    description="""
Create a new bounty on the platform.

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Bounty title (1-255 chars) |
| description | string | Yes | Full bounty description |
| tier | integer | Yes | Difficulty tier (1-3) |
| category | string | Yes | Work category |
| reward_amount | float | Yes | $FNDRY reward amount |
| reward_token | string | No | Token symbol (default: "FNDRY") |
| deadline | datetime | No | Submission deadline |
| skills | array | No | Required skills |
| github_issue_url | string | No | Link to GitHub issue |
| github_issue_number | integer | No | GitHub issue number |
| github_repo | string | No | GitHub repository name |

## Tier Rules

- **Tier 1**: 50-500 $FNDRY, 72-hour deadline
- **Tier 2**: 500-5,000 $FNDRY, 7-day deadline
- **Tier 3**: 5,000-50,000 $FNDRY, 14-30 day deadline

## Rate Limit

30 requests per minute.
""",
    responses={
        201: {
            "description": "Bounty created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "Implement wallet connection component",
                        "description": "Create a React component for Solana wallet connection",
                        "tier": 1,
                        "category": "frontend",
                        "status": "open",
                        "reward_amount": 200.0,
                        "reward_token": "FNDRY",
                        "deadline": "2024-01-15T00:00:00Z",
                        "skills": ["react", "typescript", "solana"],
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid bounty data"},
        422: {"description": "Validation error"}
    }
)
async def create_bounty(
    bounty: BountyCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new bounty."""
    from app.models.bounty import BountyDB
    
    db_bounty = BountyDB(**bounty.model_dump())
    db.add(db_bounty)
    await db.commit()
    await db.refresh(db_bounty)
    
    # Update search vector
    service = BountySearchService(db)
    await service.update_search_vector(str(db_bounty.id))
    
    return BountyResponse.model_validate(db_bounty)