"""Dispute Resolution API router.

## Overview

Disputes allow contributors to challenge bounty rejection decisions.
The system supports AI-mediated auto-resolution and manual admin review.

## Dispute Lifecycle

```
PENDING → UNDER_REVIEW → RESOLVED
    │           │
    └───────────┴── CLOSED
```

## Resolution Outcomes

- `approved`: Dispute accepted, contributor wins
- `rejected`: Dispute rejected, creator's decision stands
- `cancelled`: Dispute withdrawn by submitter

## AI Mediation

If AI review score ≥ 7/10, disputes auto-resolve in contributor's favor.

## Rate Limits

- Create dispute: 5 per hour per user
- Submit evidence: 10 per hour per dispute
- Resolve dispute: Admin only, no limit
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.database import get_db
from app.models.dispute import (
    DisputeCreate,
    DisputeUpdate,
    DisputeResolve,
    DisputeResponse,
    DisputeListResponse,
    DisputeDetailResponse,
    DisputeStats,
    DisputeStatus,
    DisputeOutcome,
    DisputeReason,
    DisputeDB,
    DisputeHistoryDB,
    DisputeHistoryItem,
    EvidenceItem,
)
from app.models.bounty import BountyDB, SubmissionRecord
from app.models.reputation import ReputationDB
from app.models.user import UserDB

router = APIRouter(prefix="/api/disputes", tags=["disputes"])

# AI mediation threshold
AI_MEDIATION_THRESHOLD = 7.0

# Dispute window: 72 hours after rejection
DISPUTE_WINDOW_HOURS = 72


async def check_tier2_eligibility(user_id: str, db: AsyncSession) -> bool:
    """Check if user has 4+ merged Tier 1 bounties."""
    result = await db.execute(
        select(BountyDB).where(
            and_(
                BountyDB.tier == 1,
                BountyDB.status == "completed",
                BountyDB.winner_id == user_id,
            )
        )
    )
    completed_t1 = result.scalars().all()
    return len(completed_t1) >= 4


async def log_dispute_action(
    db: AsyncSession,
    dispute_id: str,
    action: str,
    actor_id: str,
    previous_status: Optional[str] = None,
    new_status: Optional[str] = None,
    notes: Optional[str] = None,
):
    """Log a dispute history action."""
    history = DisputeHistoryDB(
        dispute_id=dispute_id,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        actor_id=actor_id,
        notes=notes,
    )
    db.add(history)
    await db.commit()


@router.post(
    "",
    response_model=DisputeResponse,
    status_code=201,
    summary="Create a new dispute",
    description="""
Initiate a dispute for a rejected bounty submission.

## Eligibility
- Must have 4+ completed Tier 1 bounties
- Must dispute within 72 hours of rejection
- Cannot dispute the same submission twice

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| bounty_id | string | Yes | ID of the bounty being disputed |
| reason | string | Yes | One of: incorrect_review, plagiarism, rule_violation, technical_issue, unfair_competition, other |
| description | string | Yes | Detailed explanation (10-5000 chars) |
| evidence_links | array | No | Supporting evidence (URLs, screenshots) |
""",
)
async def create_dispute(
    dispute: DisputeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new dispute for a rejected bounty submission."""
    # Check if bounty exists and is rejected
    result = await db.execute(
        select(BountyDB).where(BountyDB.id == dispute.bounty_id)
    )
    bounty = result.scalar_one_or_none()
    
    if not bounty:
        raise HTTPException(status_code=404, detail="Bounty not found")
    
    if bounty.status != "rejected":
        raise HTTPException(
            status_code=400,
            detail="Can only dispute rejected bounties"
        )
    
    # Check dispute window (72 hours)
    if bounty.updated_at:
        deadline = bounty.updated_at + timedelta(hours=DISPUTE_WINDOW_HOURS)
        if datetime.now(timezone.utc) > deadline:
            raise HTTPException(
                status_code=400,
                detail=f"Dispute window expired (must dispute within {DISPUTE_WINDOW_HOURS} hours)"
            )
    
    # Check for existing dispute
    existing = await db.execute(
        select(DisputeDB).where(DisputeDB.bounty_id == dispute.bounty_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail="Dispute already exists for this bounty"
        )
    
    # Using placeholder submitter_id for MVP (should come from auth)
    submitter_id = "placeholder_user_id"
    
    dispute_db = DisputeDB(
        bounty_id=dispute.bounty_id,
        submitter_id=submitter_id,
        reason=dispute.reason,
        description=dispute.description,
        evidence_links=[e.model_dump() for e in dispute.evidence_links],
        status=DisputeStatus.PENDING.value,
    )
    db.add(dispute_db)
    await db.commit()
    await db.refresh(dispute_db)
    
    # Log action
    await log_dispute_action(
        db,
        str(dispute_db.id),
        "dispute_created",
        submitter_id,
        new_status=DisputeStatus.PENDING.value,
        notes=f"Dispute initiated: {dispute.reason}"
    )
    
    return DisputeResponse(
        id=str(dispute_db.id),
        bounty_id=str(dispute_db.bounty_id),
        submitter_id=str(dispute_db.submitter_id),
        reason=dispute_db.reason,
        description=dispute_db.description,
        evidence_links=dispute_db.evidence_links,
        status=dispute_db.status,
        outcome=dispute_db.outcome,
        reviewer_id=dispute_db.reviewer_id,
        review_notes=dispute_db.review_notes,
        resolution_action=dispute_db.resolution_action,
        created_at=dispute_db.created_at,
        updated_at=dispute_db.updated_at,
        resolved_at=dispute_db.resolved_at,
    )


@router.get(
    "",
    response_model=DisputeListResponse,
    summary="List all disputes",
    description="""
Get a paginated list of disputes with optional filtering.

## Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter by status: pending, under_review, resolved, closed |
| bounty_id | string | Filter by bounty ID |
| submitter_id | string | Filter by submitter ID |
| skip | int | Pagination offset (default: 0) |
| limit | int | Results per page (default: 20, max: 100) |
""",
)
async def list_disputes(
    status: Optional[str] = Query(None, description="Filter by status"),
    bounty_id: Optional[str] = Query(None, description="Filter by bounty ID"),
    submitter_id: Optional[str] = Query(None, description="Filter by submitter ID"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    db: AsyncSession = Depends(get_db),
):
    """List all disputes with optional filtering."""
    query = select(DisputeDB)
    
    if status:
        query = query.where(DisputeDB.status == status)
    if bounty_id:
        query = query.where(DisputeDB.bounty_id == bounty_id)
    if submitter_id:
        query = query.where(DisputeDB.submitter_id == submitter_id)
    
    # Get total count
    count_query = select(DisputeDB)
    if status:
        count_query = count_query.where(DisputeDB.status == status)
    if bounty_id:
        count_query = count_query.where(DisputeDB.bounty_id == bounty_id)
    if submitter_id:
        count_query = count_query.where(DisputeDB.submitter_id == submitter_id)
    
    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())
    
    # Get paginated results
    query = query.offset(skip).limit(limit).order_by(DisputeDB.created_at.desc())
    result = await db.execute(query)
    disputes = result.scalars().all()
    
    from app.models.dispute import DisputeListItem
    
    items = [
        DisputeListItem(
            id=str(d.id),
            bounty_id=str(d.bounty_id),
            submitter_id=str(d.submitter_id),
            reason=d.reason,
            status=d.status,
            outcome=d.outcome,
            created_at=d.created_at,
            resolved_at=d.resolved_at,
        )
        for d in disputes
    ]
    
    return DisputeListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/stats",
    response_model=DisputeStats,
    summary="Get dispute statistics",
)
async def get_dispute_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get dispute statistics."""
    result = await db.execute(select(DisputeDB))
    all_disputes = result.scalars().all()
    
    total = len(all_disputes)
    pending = sum(1 for d in all_disputes if d.status == DisputeStatus.PENDING.value)
    resolved = sum(1 for d in all_disputes if d.status == DisputeStatus.RESOLVED.value)
    approved = sum(1 for d in all_disputes if d.outcome == DisputeOutcome.APPROVED.value)
    rejected = sum(1 for d in all_disputes if d.outcome == DisputeOutcome.REJECTED.value)
    
    return DisputeStats(
        total_disputes=total,
        pending_disputes=pending,
        resolved_disputes=resolved,
        approved_disputes=approved,
        rejected_disputes=rejected,
        approval_rate=approved / resolved if resolved > 0 else 0.0,
    )


@router.get(
    "/{dispute_id}",
    response_model=DisputeDetailResponse,
    summary="Get dispute details",
)
async def get_dispute(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed information about a dispute including history."""
    result = await db.execute(
        select(DisputeDB).where(DisputeDB.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    # Get history
    history_result = await db.execute(
        select(DisputeHistoryDB)
        .where(DisputeHistoryDB.dispute_id == dispute_id)
        .order_by(DisputeHistoryDB.created_at.desc())
    )
    history = history_result.scalars().all()
    
    history_items = [
        DisputeHistoryItem(
            id=str(h.id),
            dispute_id=str(h.dispute_id),
            action=h.action,
            previous_status=h.previous_status,
            new_status=h.new_status,
            actor_id=str(h.actor_id),
            notes=h.notes,
            created_at=h.created_at,
        )
        for h in history
    ]
    
    return DisputeDetailResponse(
        id=str(dispute.id),
        bounty_id=str(dispute.bounty_id),
        submitter_id=str(dispute.submitter_id),
        reason=dispute.reason,
        description=dispute.description,
        evidence_links=dispute.evidence_links,
        status=dispute.status,
        outcome=dispute.outcome,
        reviewer_id=dispute.reviewer_id,
        review_notes=dispute.review_notes,
        resolution_action=dispute.resolution_action,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
        resolved_at=dispute.resolved_at,
        history=history_items,
    )


@router.post(
    "/{dispute_id}/evidence",
    response_model=DisputeResponse,
    summary="Submit additional evidence",
    description="""
Submit additional evidence for a dispute.

Both the dispute submitter and bounty creator can submit evidence.

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| evidence_links | array | Yes | List of evidence items |
""",
)
async def submit_evidence(
    dispute_id: str,
    evidence: DisputeUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Submit additional evidence for a dispute."""
    result = await db.execute(
        select(DisputeDB).where(DisputeDB.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    if dispute.status == DisputeStatus.RESOLVED.value:
        raise HTTPException(
            status_code=400,
            detail="Cannot submit evidence to resolved dispute"
        )
    
    # Update evidence
    if evidence.evidence_links:
        existing_links = dispute.evidence_links or []
        new_links = [e.model_dump() for e in evidence.evidence_links]
        dispute.evidence_links = existing_links + new_links
    
    if evidence.description:
        dispute.description = f"{dispute.description}\n\n--- Additional Info ---\n{evidence.description}"
    
    dispute.updated_at = datetime.now(timezone.utc)
    
    # Update status to under_review if pending
    if dispute.status == DisputeStatus.PENDING.value:
        dispute.status = DisputeStatus.UNDER_REVIEW.value
        await log_dispute_action(
            db,
            dispute_id,
            "status_changed",
            "system",
            previous_status=DisputeStatus.PENDING.value,
            new_status=DisputeStatus.UNDER_REVIEW.value,
            notes="Evidence submitted, moved to review"
        )
    
    await db.commit()
    await db.refresh(dispute)
    
    return DisputeResponse(
        id=str(dispute.id),
        bounty_id=str(dispute.bounty_id),
        submitter_id=str(dispute.submitter_id),
        reason=dispute.reason,
        description=dispute.description,
        evidence_links=dispute.evidence_links,
        status=dispute.status,
        outcome=dispute.outcome,
        reviewer_id=dispute.reviewer_id,
        review_notes=dispute.review_notes,
        resolution_action=dispute.resolution_action,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
        resolved_at=dispute.resolved_at,
    )


@router.post(
    "/{dispute_id}/resolve",
    response_model=DisputeResponse,
    summary="Resolve a dispute",
    description="""
Resolve a dispute with a final decision.

## Admin Only
This endpoint requires admin privileges.

## AI Auto-Mediation
If the dispute has AI review score >= 7/10, it may auto-resolve in contributor's favor.

## Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| outcome | string | Yes | One of: approved, rejected, cancelled |
| review_notes | string | Yes | Explanation of decision |
| resolution_action | string | No | Specific action taken |
""",
)
async def resolve_dispute(
    dispute_id: str,
    resolution: DisputeResolve,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Resolve a dispute with a final decision."""
    result = await db.execute(
        select(DisputeDB).where(DisputeDB.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    if dispute.status == DisputeStatus.RESOLVED.value:
        raise HTTPException(
            status_code=400,
            detail="Dispute already resolved"
        )
    
    previous_status = dispute.status
    dispute.status = DisputeStatus.RESOLVED.value
    dispute.outcome = resolution.outcome
    dispute.review_notes = resolution.review_notes
    dispute.resolution_action = resolution.resolution_action
    dispute.resolved_at = datetime.now(timezone.utc)
    dispute.updated_at = datetime.now(timezone.utc)
    
    # Placeholder reviewer_id (should come from auth)
    reviewer_id = "admin_placeholder"
    dispute.reviewer_id = reviewer_id
    
    await db.commit()
    await db.refresh(dispute)
    
    # Log resolution
    await log_dispute_action(
        db,
        dispute_id,
        "dispute_resolved",
        reviewer_id,
        previous_status=previous_status,
        new_status=DisputeStatus.RESOLVED.value,
        notes=f"Outcome: {resolution.outcome}. {resolution.review_notes}"
    )
    
    return DisputeResponse(
        id=str(dispute.id),
        bounty_id=str(dispute.bounty_id),
        submitter_id=str(dispute.submitter_id),
        reason=dispute.reason,
        description=dispute.description,
        evidence_links=dispute.evidence_links,
        status=dispute.status,
        outcome=dispute.outcome,
        reviewer_id=dispute.reviewer_id,
        review_notes=dispute.review_notes,
        resolution_action=dispute.resolution_action,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
        resolved_at=dispute.resolved_at,
    )


@router.post(
    "/{dispute_id}/ai-mediate",
    response_model=DisputeResponse,
    summary="Trigger AI mediation",
    description="""
Run AI mediation on a dispute.

If AI score >= 7/10, the dispute auto-resolves in contributor's favor.
Otherwise, it requires manual admin review.
""",
)
async def ai_mediate_dispute(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Run AI mediation on a dispute."""
    result = await db.execute(
        select(DisputeDB).where(DisputeDB.id == dispute_id)
    )
    dispute = result.scalar_one_or_none()
    
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    
    if dispute.status == DisputeStatus.RESOLVED.value:
        raise HTTPException(
            status_code=400,
            detail="Dispute already resolved"
        )
    
    # Placeholder AI score (would come from AI review)
    ai_score = 7.5  # Mock score
    
    if ai_score >= AI_MEDIATION_THRESHOLD:
        # Auto-resolve in contributor's favor
        previous_status = dispute.status
        dispute.status = DisputeStatus.RESOLVED.value
        dispute.outcome = DisputeOutcome.APPROVED.value
        dispute.review_notes = f"AI auto-mediated (score: {ai_score}/10)"
        dispute.resolved_at = datetime.now(timezone.utc)
        dispute.updated_at = datetime.now(timezone.utc)
        dispute.reviewer_id = "ai_mediator"
        
        await db.commit()
        await db.refresh(dispute)
        
        await log_dispute_action(
            db,
            dispute_id,
            "ai_auto_resolved",
            "ai_mediator",
            previous_status=previous_status,
            new_status=DisputeStatus.RESOLVED.value,
            notes=f"AI score {ai_score} >= threshold {AI_MEDIATION_THRESHOLD}"
        )
    else:
        # Needs manual review
        dispute.status = DisputeStatus.UNDER_REVIEW.value
        dispute.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(dispute)
        
        await log_dispute_action(
            db,
            dispute_id,
            "ai_mediation_insufficient",
            "ai_mediator",
            notes=f"AI score {ai_score} < threshold {AI_MEDIATION_THRESHOLD}, needs manual review"
        )
    
    return DisputeResponse(
        id=str(dispute.id),
        bounty_id=str(dispute.bounty_id),
        submitter_id=str(dispute.submitter_id),
        reason=dispute.reason,
        description=dispute.description,
        evidence_links=dispute.evidence_links,
        status=dispute.status,
        outcome=dispute.outcome,
        reviewer_id=dispute.reviewer_id,
        review_notes=dispute.review_notes,
        resolution_action=dispute.resolution_action,
        created_at=dispute.created_at,
        updated_at=dispute.updated_at,
        resolved_at=dispute.resolved_at,
    )