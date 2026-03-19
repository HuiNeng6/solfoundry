"""Bounty Creation Wizard API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty_wizard import (
    WizardDraftResponse,
    CreateDraftRequest,
    UpdateBasicsRequest,
    UpdateRewardRequest,
    UpdateRequirementsRequest,
    FinalizeRequest,
)
from app.models.bounty import BountyResponse
from app.services.bounty_wizard_service import BountyWizardService
from app.database import get_db

router = APIRouter(prefix="/bounty-wizard", tags=["bounty-wizard"])


@router.post("/drafts", response_model=WizardDraftResponse, status_code=201)
async def create_draft(
    data: CreateDraftRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new bounty creation draft.
    
    Creates a draft that guides through wizard steps.
    """
    service = BountyWizardService(db)
    draft = await service.create_draft(data.user_id)
    
    return WizardDraftResponse.model_validate(draft)


@router.get("/drafts/{draft_id}", response_model=WizardDraftResponse)
async def get_draft(
    draft_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a draft by ID.
    
    - **draft_id**: Draft ID
    - **user_id**: User ID (for ownership)
    """
    service = BountyWizardService(db)
    draft = await service.get_draft(draft_id, user_id)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return WizardDraftResponse.model_validate(draft)


@router.patch("/drafts/{draft_id}/basics", response_model=WizardDraftResponse)
async def update_basics(
    draft_id: str,
    user_id: str,
    data: UpdateBasicsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update basics step (title, description, category).
    
    - **draft_id**: Draft ID
    - **user_id**: User ID
    """
    service = BountyWizardService(db)
    draft = await service.update_basics(draft_id, user_id, data)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return WizardDraftResponse.model_validate(draft)


@router.patch("/drafts/{draft_id}/reward", response_model=WizardDraftResponse)
async def update_reward(
    draft_id: str,
    user_id: str,
    data: UpdateRewardRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update reward step (token, amount, tier).
    
    - **draft_id**: Draft ID
    - **user_id**: User ID
    """
    service = BountyWizardService(db)
    draft = await service.update_reward(draft_id, user_id, data)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return WizardDraftResponse.model_validate(draft)


@router.patch("/drafts/{draft_id}/requirements", response_model=WizardDraftResponse)
async def update_requirements(
    draft_id: str,
    user_id: str,
    data: UpdateRequirementsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update requirements step (skills, deadline, GitHub issue).
    
    - **draft_id**: Draft ID
    - **user_id**: User ID
    """
    service = BountyWizardService(db)
    draft = await service.update_requirements(draft_id, user_id, data)
    
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return WizardDraftResponse.model_validate(draft)


@router.post("/drafts/{draft_id}/finalize", response_model=BountyResponse)
async def finalize_draft(
    draft_id: str,
    user_id: str,
    data: FinalizeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Finalize draft and create bounty.
    
    - **draft_id**: Draft ID
    - **user_id**: User ID
    - **confirm**: Must be true to finalize
    """
    if not data.confirm:
        raise HTTPException(status_code=400, detail="Must confirm to finalize")
    
    service = BountyWizardService(db)
    bounty = await service.finalize(draft_id, user_id)
    
    if not bounty:
        raise HTTPException(
            status_code=400,
            detail="Cannot finalize: missing required fields"
        )
    
    return BountyResponse.model_validate(bounty)


@router.delete("/drafts/{draft_id}")
async def delete_draft(
    draft_id: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a draft.
    
    - **draft_id**: Draft ID
    - **user_id**: User ID
    """
    service = BountyWizardService(db)
    success = await service.delete_draft(draft_id, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Draft not found")
    
    return {"message": "Draft deleted"}