"""Bounty submission API endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.submission import (
    SubmissionCreate, SubmissionUpdate, SubmissionResponse,
    SubmissionListResponse, SubmissionSearchParams, SubmissionStats,
)
from app.services.submission_service import SubmissionService
from app.database import get_db

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.post("/", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_submission(data: SubmissionCreate, request: Request, contributor_id: str = Query(..., description="Contributor UUID"), db: AsyncSession = Depends(get_db)):
    """Submit a PR for bounty claim."""
    service = SubmissionService(db)
    submission, match_result = await service.create_submission(contributor_id, data)
    return SubmissionResponse.model_validate(submission)


@router.get("/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: str, db: AsyncSession = Depends(get_db)):
    """Get a single submission by ID."""
    service = SubmissionService(db)
    submission = await service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return SubmissionResponse.model_validate(submission)


@router.patch("/{submission_id}", response_model=SubmissionResponse)
async def update_submission(submission_id: str, data: SubmissionUpdate, request: Request, reviewer_id: Optional[str] = Query(None, description="Reviewer UUID"), db: AsyncSession = Depends(get_db)):
    """Update a submission's status."""
    service = SubmissionService(db)
    submission = await service.update_submission(submission_id, data, reviewer_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return SubmissionResponse.model_validate(submission)


@router.get("/", response_model=SubmissionListResponse)
async def list_submissions(contributor_id: Optional[str] = Query(None), bounty_id: Optional[str] = Query(None), status: Optional[str] = Query(None), wallet: Optional[str] = Query(None), sort: str = Query("newest", pattern="^(newest|oldest|status|reward)$"), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """List submissions with filtering and pagination."""
    params = SubmissionSearchParams(contributor_id=contributor_id, bounty_id=bounty_id, status=status, wallet=wallet, sort=sort, skip=skip, limit=limit)
    service = SubmissionService(db)
    return await service.list_submissions(params)


@router.get("/contributor/{contributor_id}/stats", response_model=SubmissionStats)
async def get_contributor_stats(contributor_id: str, db: AsyncSession = Depends(get_db)):
    """Get submission statistics for a contributor."""
    service = SubmissionService(db)
    return await service.get_contributor_stats(contributor_id)


@router.get("/bounty/{bounty_id}", response_model=SubmissionListResponse)
async def get_bounty_submissions(bounty_id: str, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    """Get all submissions for a specific bounty."""
    service = SubmissionService(db)
    submissions = await service.get_bounty_submissions(bounty_id)
    total = len(submissions)
    paginated = submissions[skip:skip+limit]
    from app.models.submission import SubmissionListItem
    return SubmissionListResponse(items=[SubmissionListItem.model_validate(s) for s in paginated], total=total, skip=skip, limit=limit)


@router.post("/{submission_id}/approve", response_model=SubmissionResponse)
async def approve_submission(submission_id: str, request: Request, reviewer_id: str = Query(..., description="Reviewer UUID"), notes: Optional[str] = Query(None, description="Approval notes"), db: AsyncSession = Depends(get_db)):
    """Approve a submission."""
    service = SubmissionService(db)
    update_data = SubmissionUpdate(status="approved", review_notes=notes)
    submission = await service.update_submission(submission_id, update_data, reviewer_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return SubmissionResponse.model_validate(submission)


@router.post("/{submission_id}/reject", response_model=SubmissionResponse)
async def reject_submission(submission_id: str, request: Request, reviewer_id: str = Query(..., description="Reviewer UUID"), reason: str = Query(..., description="Rejection reason"), db: AsyncSession = Depends(get_db)):
    """Reject a submission."""
    service = SubmissionService(db)
    update_data = SubmissionUpdate(status="rejected", review_notes=reason)
    submission = await service.update_submission(submission_id, update_data, reviewer_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return SubmissionResponse.model_validate(submission)
