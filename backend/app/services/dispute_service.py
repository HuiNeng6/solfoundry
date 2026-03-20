"""Dispute service for business logic."""

import uuid
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispute import (
    DisputeDB, DisputeHistoryDB, DisputeStatus, DisputeOutcome,
    DisputeCreate, DisputeUpdate, DisputeResolve, DisputeResponse,
    DisputeListItem, DisputeListResponse, DisputeDetailResponse,
    DisputeHistoryItem, DisputeStats,
)
from app.models.bounty import BountyDB


class DisputeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_dispute(self, bounty_id: str, submitter_id: str, data: DisputeCreate) -> DisputeResponse:
        bounty = await self._get_bounty(bounty_id)
        if not bounty:
            raise ValueError(f"Bounty {bounty_id} not found")
        if bounty.status != "completed":
            raise ValueError(f"Cannot dispute bounty in '{bounty.status}' status. Only completed bounties can be disputed.")

        dispute = DisputeDB(
            bounty_id=uuid.UUID(bounty_id),
            submitter_id=uuid.UUID(submitter_id),
            reason=data.reason,
            description=data.description,
            evidence_links=[e.model_dump() for e in data.evidence_links],
            status=DisputeStatus.PENDING.value,
        )
        self.db.add(dispute)
        await self._add_history(str(dispute.id), "created", DisputeStatus.PENDING.value, submitter_id, f"Dispute created: {data.reason}")
        await self.db.commit()
        await self.db.refresh(dispute)
        return DisputeResponse.model_validate(dispute)

    async def get_dispute(self, dispute_id: str, include_history: bool = False) -> Optional[DisputeDetailResponse]:
        dispute = await self._get_dispute(dispute_id)
        if not dispute:
            return None
        resp = DisputeResponse.model_validate(dispute)
        history = await self._get_history(dispute_id) if include_history else []
        return DisputeDetailResponse(**resp.model_dump(), history=history)

    async def list_disputes(self, bounty_id: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 20) -> DisputeListResponse:
        conditions = []
        if bounty_id:
            conditions.append(DisputeDB.bounty_id == uuid.UUID(bounty_id))
        if status:
            conditions.append(DisputeDB.status == status)
        filter_cond = and_(*conditions) if conditions else True

        result = await self.db.execute(select(DisputeDB).where(filter_cond).order_by(DisputeDB.created_at.desc()).offset(skip).limit(limit))
        disputes = result.scalars().all()

        count_result = await self.db.execute(select(func.count(DisputeDB.id)).where(filter_cond))
        total = count_result.scalar() or 0

        return DisputeListResponse(items=[DisputeListItem.model_validate(d) for d in disputes], total=total, skip=skip, limit=limit)

    async def start_review(self, dispute_id: str, reviewer_id: str) -> DisputeResponse:
        dispute = await self._get_dispute(dispute_id)
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")
        if dispute.status != DisputeStatus.PENDING.value:
            raise ValueError(f"Cannot review dispute in '{dispute.status}' status")
        dispute.status = DisputeStatus.UNDER_REVIEW.value
        dispute.reviewer_id = uuid.UUID(reviewer_id)
        await self._add_history(dispute_id, "review_started", DisputeStatus.UNDER_REVIEW.value, reviewer_id, "Review started")
        await self.db.commit()
        await self.db.refresh(dispute)
        return DisputeResponse.model_validate(dispute)

    async def resolve_dispute(self, dispute_id: str, reviewer_id: str, data: DisputeResolve) -> DisputeResponse:
        dispute = await self._get_dispute(dispute_id)
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")
        if dispute.status not in {DisputeStatus.PENDING.value, DisputeStatus.UNDER_REVIEW.value}:
            raise ValueError(f"Cannot resolve dispute in '{dispute.status}' status")
        dispute.status = DisputeStatus.RESOLVED.value
        dispute.outcome = data.outcome
        dispute.reviewer_id = uuid.UUID(reviewer_id)
        dispute.review_notes = data.review_notes
        dispute.resolution_action = data.resolution_action
        dispute.resolved_at = datetime.now(timezone.utc)
        await self._add_history(dispute_id, "resolved", DisputeStatus.RESOLVED.value, reviewer_id, f"Resolved as {data.outcome}")
        await self.db.commit()
        await self.db.refresh(dispute)
        return DisputeResponse.model_validate(dispute)

    async def close_dispute(self, dispute_id: str, user_id: str, reason: Optional[str] = None) -> DisputeResponse:
        dispute = await self._get_dispute(dispute_id)
        if not dispute:
            raise ValueError(f"Dispute {dispute_id} not found")
        if str(dispute.submitter_id) != user_id:
            raise ValueError("Only the dispute submitter can close the dispute")
        if dispute.status != DisputeStatus.PENDING.value:
            raise ValueError(f"Cannot close dispute in '{dispute.status}' status")
        dispute.status = DisputeStatus.CLOSED.value
        dispute.outcome = DisputeOutcome.CANCELLED.value
        dispute.resolved_at = datetime.now(timezone.utc)
        await self._add_history(dispute_id, "closed", DisputeStatus.CLOSED.value, user_id, reason or "Closed by submitter")
        await self.db.commit()
        await self.db.refresh(dispute)
        return DisputeResponse.model_validate(dispute)

    async def get_dispute_stats(self) -> DisputeStats:
        total = (await self.db.execute(select(func.count(DisputeDB.id)))).scalar() or 0
        pending = (await self.db.execute(select(func.count(DisputeDB.id)).where(DisputeDB.status == DisputeStatus.PENDING.value))).scalar() or 0
        resolved = (await self.db.execute(select(func.count(DisputeDB.id)).where(DisputeDB.status == DisputeStatus.RESOLVED.value))).scalar() or 0
        approved = (await self.db.execute(select(func.count(DisputeDB.id)).where(and_(DisputeDB.status == DisputeStatus.RESOLVED.value, DisputeDB.outcome == DisputeOutcome.APPROVED.value)))).scalar() or 0
        rejected = (await self.db.execute(select(func.count(DisputeDB.id)).where(and_(DisputeDB.status == DisputeStatus.RESOLVED.value, DisputeDB.outcome == DisputeOutcome.REJECTED.value)))).scalar() or 0
        return DisputeStats(total_disputes=total, pending_disputes=pending, resolved_disputes=resolved, approved_disputes=approved, rejected_disputes=rejected, approval_rate=round(approved / resolved * 100, 2) if resolved > 0 else 0.0)

    async def _get_bounty(self, bounty_id: str) -> Optional[BountyDB]:
        try:
            result = await self.db.execute(select(BountyDB).where(BountyDB.id == uuid.UUID(bounty_id)))
            return result.scalar_one_or_none()
        except ValueError:
            return None

    async def _get_dispute(self, dispute_id: str) -> Optional[DisputeDB]:
        try:
            result = await self.db.execute(select(DisputeDB).where(DisputeDB.id == uuid.UUID(dispute_id)))
            return result.scalar_one_or_none()
        except ValueError:
            return None

    async def _get_history(self, dispute_id: str) -> List[DisputeHistoryItem]:
        result = await self.db.execute(select(DisputeHistoryDB).where(DisputeHistoryDB.dispute_id == uuid.UUID(dispute_id)).order_by(DisputeHistoryDB.created_at.asc()))
        return [DisputeHistoryItem.model_validate(h) for h in result.scalars().all()]

    async def _add_history(self, dispute_id: str, action: str, new_status: str, actor_id: str, notes: Optional[str] = None):
        history = DisputeHistoryDB(dispute_id=uuid.UUID(dispute_id), action=action, new_status=new_status, actor_id=uuid.UUID(actor_id), notes=notes)
        self.db.add(history)