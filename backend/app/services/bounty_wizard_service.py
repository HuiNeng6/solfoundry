"""Bounty Creation Wizard service."""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bounty_wizard import (
    BountyDraftDB,
    WizardStep,
    BasicsStep,
    RewardStep,
    RequirementsStep,
    WizardDraftResponse,
)
from app.models.bounty import BountyDB, VALID_CATEGORIES


class BountyWizardService:
    """Service for bounty creation wizard."""
    
    STEP_ORDER = [
        WizardStep.BASICS,
        WizardStep.REWARD,
        WizardStep.REQUIREMENTS,
        WizardStep.REVIEW,
        WizardStep.COMPLETE,
    ]
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_draft(self, user_id: str) -> BountyDraftDB:
        """Create a new bounty draft."""
        draft = BountyDraftDB(user_id=user_id)
        self.db.add(draft)
        return draft
    
    async def get_draft(self, draft_id: str, user_id: str) -> Optional[BountyDraftDB]:
        """Get a draft by ID."""
        query = select(BountyDraftDB).where(
            BountyDraftDB.id == draft_id,
            BountyDraftDB.user_id == user_id,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_basics(
        self,
        draft_id: str,
        user_id: str,
        data: BasicsStep,
    ) -> Optional[BountyDraftDB]:
        """Update basics step."""
        draft = await self.get_draft(draft_id, user_id)
        if not draft:
            return None
        
        draft.title = data.title
        draft.description = data.description
        draft.category = data.category
        draft.current_step = WizardStep.REWARD.value
        
        return draft
    
    async def update_reward(
        self,
        draft_id: str,
        user_id: str,
        data: RewardStep,
    ) -> Optional[BountyDraftDB]:
        """Update reward step."""
        draft = await self.get_draft(draft_id, user_id)
        if not draft:
            return None
        
        draft.reward_token = data.reward_token
        draft.reward_amount = data.reward_amount
        draft.tier = data.tier
        draft.current_step = WizardStep.REQUIREMENTS.value
        
        return draft
    
    async def update_requirements(
        self,
        draft_id: str,
        user_id: str,
        data: RequirementsStep,
    ) -> Optional[BountyDraftDB]:
        """Update requirements step."""
        draft = await self.get_draft(draft_id, user_id)
        if not draft:
            return None
        
        draft.skills = data.skills
        draft.deadline = data.deadline
        draft.github_issue_url = data.github_issue_url
        draft.current_step = WizardStep.REVIEW.value
        
        return draft
    
    async def finalize(
        self,
        draft_id: str,
        user_id: str,
    ) -> Optional[BountyDB]:
        """Finalize draft and create bounty."""
        draft = await self.get_draft(draft_id, user_id)
        if not draft:
            return None
        
        # Validate all steps complete
        if not all([draft.title, draft.description, draft.category, draft.reward_amount, draft.tier]):
            return None
        
        # Create bounty from draft
        bounty = BountyDB(
            title=draft.title,
            description=draft.description,
            category=draft.category,
            reward_token=draft.reward_token or "FNDRY",
            reward_amount=draft.reward_amount,
            tier=draft.tier,
            skills=draft.skills or [],
            deadline=draft.deadline,
            github_issue_url=draft.github_issue_url,
            status="open",
        )
        
        self.db.add(bounty)
        draft.current_step = WizardStep.COMPLETE.value
        
        return bounty
    
    async def delete_draft(self, draft_id: str, user_id: str) -> bool:
        """Delete a draft."""
        draft = await self.get_draft(draft_id, user_id)
        if not draft:
            return False
        
        await self.db.delete(draft)
        return True