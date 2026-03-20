"""Dispute API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dispute import (
    DisputeCreate, DisputeResolve, DisputeResponse,
    DisputeListResponse, DisputeDetailResponse, DisputeStats,
    DisputeReason, DisputeStatus,
)
from app.services.dispute_service import DisputeService
from app.database import get_db

router = APIRouter(prefix="/disputes", tags=["disputes"])


async def get_current_user_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


async def get_maintainer_user_id() -> str:
    return "00000000-0000-0000-0000-000000000002"


@router.post("/", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    data: DisputeCreate,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    service = DisputeService(db)
    try:
        return await service.create_dispute(bounty_id=data.bounty_id, submitter_id=user_id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=DisputeListResponse)
async def list_disputes(
    bounty_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    if status and status not in {s.value for s in DisputeStatus}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {status}")
    service = DisputeService(db)
    return await service.list_disputes(bounty_id=bounty_id, status=status, skip=skip, limit=limit)


@router.get("/stats", response_model=DisputeStats)
async def get_dispute_stats(db: AsyncSession = Depends(get_db)):
    return await DisputeService(db).get_dispute_stats()


@router.get("/reasons")
async def get_dispute_reasons():
    return {"reasons": [{"value": r.value, "label": r.value.replace("_", " ").title()} for r in DisputeReason]}


@router.get("/{dispute_id}", response_model=DisputeDetailResponse)
async def get_dispute(dispute_id: str, db: AsyncSession = Depends(get_db)):
    dispute = await DisputeService(db).get_dispute(dispute_id, include_history=True)
    if not dispute:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dispute not found")
    return dispute


@router.post("/{dispute_id}/review", response_model=DisputeResponse)
async def start_dispute_review(
    dispute_id: str,
    db: AsyncSession = Depends(get_db),
    reviewer_id: str = Depends(get_maintainer_user_id),
):
    try:
        return await DisputeService(db).start_review(dispute_id=dispute_id, reviewer_id=reviewer_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(
    dispute_id: str,
    data: DisputeResolve,
    db: AsyncSession = Depends(get_db),
    reviewer_id: str = Depends(get_maintainer_user_id),
):
    try:
        return await DisputeService(db).resolve_dispute(dispute_id=dispute_id, reviewer_id=reviewer_id, data=data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{dispute_id}/close", response_model=DisputeResponse)
async def close_dispute(
    dispute_id: str,
    reason: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    try:
        return await DisputeService(db).close_dispute(dispute_id=dispute_id, user_id=user_id, reason=reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/bounties/{bounty_id}/disputes", response_model=DisputeListResponse)
async def list_bounty_disputes(
    bounty_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await DisputeService(db).list_disputes(bounty_id=bounty_id, skip=skip, limit=limit)