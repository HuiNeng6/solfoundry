"""PR Status service layer."""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pr_status import (
    PRStatusDB,
    PRStatusCreate,
    PRStatusUpdate,
    PRStatusResponse,
    PRStatusListItem,
    PRStatusListResponse,
    PRStage,
    StageStatus,
    get_default_stages
)

logger = logging.getLogger(__name__)


class PRStatusService:
    """Service for managing PR status tracking."""

    @staticmethod
    async def create(
        db: AsyncSession,
        data: PRStatusCreate
    ) -> PRStatusResponse:
        """
        Create a new PR status entry.
        
        Args:
            db: Database session
            data: PR status creation data
            
        Returns:
            Created PR status
        """
        # Check if PR already exists
        existing = await db.execute(
            select(PRStatusDB).where(PRStatusDB.pr_number == data.pr_number)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"PR #{data.pr_number} already has a status entry")

        # Create new PR status with default stages
        now = datetime.now(timezone.utc)
        stages = get_default_stages()
        stages[PRStage.SUBMITTED.value]["timestamp"] = now.isoformat()
        stages[PRStage.SUBMITTED.value]["status"] = StageStatus.PASSED.value

        db_entry = PRStatusDB(
            pr_number=data.pr_number,
            pr_title=data.pr_title,
            pr_url=data.pr_url,
            author=data.author,
            bounty_id=data.bounty_id,
            bounty_title=data.bounty_title,
            current_stage=PRStage.SUBMITTED,
            stages_data=stages,
            created_at=now,
            updated_at=now
        )

        db.add(db_entry)
        await db.commit()
        await db.refresh(db_entry)

        logger.info(f"Created PR status for PR #{data.pr_number}")

        return PRStatusService._to_response(db_entry)

    @staticmethod
    async def get(
        db: AsyncSession,
        pr_number: int
    ) -> Optional[PRStatusResponse]:
        """
        Get PR status by PR number.
        
        Args:
            db: Database session
            pr_number: GitHub PR number
            
        Returns:
            PR status if found, None otherwise
        """
        result = await db.execute(
            select(PRStatusDB).where(PRStatusDB.pr_number == pr_number)
        )
        db_entry = result.scalar_one_or_none()

        if not db_entry:
            return None

        return PRStatusService._to_response(db_entry)

    @staticmethod
    async def list(
        db: AsyncSession,
        bounty_id: Optional[str] = None,
        author: Optional[str] = None,
        current_stage: Optional[PRStage] = None,
        skip: int = 0,
        limit: int = 20
    ) -> PRStatusListResponse:
        """
        List PR statuses with filters.
        
        Args:
            db: Database session
            bounty_id: Filter by bounty ID
            author: Filter by author
            current_stage: Filter by current stage
            skip: Pagination offset
            limit: Pagination limit
            
        Returns:
            List of PR statuses
        """
        query = select(PRStatusDB)

        if bounty_id:
            query = query.where(PRStatusDB.bounty_id == bounty_id)
        if author:
            query = query.where(PRStatusDB.author == author)
        if current_stage:
            query = query.where(PRStatusDB.current_stage == current_stage)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(PRStatusDB.updated_at.desc())
        result = await db.execute(query)
        entries = result.scalars().all()

        return PRStatusListResponse(
            items=[PRStatusService._to_list_item(entry) for entry in entries],
            total=total,
            skip=skip,
            limit=limit
        )

    @staticmethod
    async def update_stage(
        db: AsyncSession,
        pr_number: int,
        stage: PRStage,
        status: StageStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[PRStatusResponse]:
        """
        Update a specific stage in the PR pipeline.
        
        Args:
            db: Database session
            pr_number: GitHub PR number
            stage: Stage to update
            status: New status for the stage
            details: Additional details (message, scores, tx_hash, etc.)
            
        Returns:
            Updated PR status if found, None otherwise
        """
        result = await db.execute(
            select(PRStatusDB).where(PRStatusDB.pr_number == pr_number)
        )
        db_entry = result.scalar_one_or_none()

        if not db_entry:
            logger.warning(f"PR #{pr_number} not found for stage update")
            return None

        # Update stages data
        stages_data = db_entry.stages_data.copy()
        now = datetime.now(timezone.utc).isoformat()

        # Calculate duration if transitioning from running
        previous_status = stages_data.get(stage.value, {}).get("status")
        previous_timestamp = stages_data.get(stage.value, {}).get("timestamp")
        duration = None

        if previous_status == StageStatus.RUNNING.value and previous_timestamp:
            try:
                prev_time = datetime.fromisoformat(previous_timestamp.replace("Z", "+00:00"))
                curr_time = datetime.now(timezone.utc)
                duration = int((curr_time - prev_time).total_seconds())
            except Exception as e:
                logger.warning(f"Failed to calculate duration: {e}")

        stages_data[stage.value] = {
            "status": status.value,
            "timestamp": now,
            "duration": duration,
            **(details or {})
        }

        # Update current stage if necessary
        current_stage = db_entry.current_stage
        if status == StageStatus.PASSED:
            # Move to next stage
            stage_order = list(PRStage)
            current_idx = stage_order.index(stage)
            if current_idx < len(stage_order) - 1:
                current_stage = stage_order[current_idx + 1]
                # Skip denied stage
                if current_stage == PRStage.DENIED:
                    current_stage = stage_order[current_idx + 2] if current_idx + 2 < len(stage_order) else PRStage.APPROVED
        elif status == StageStatus.FAILED:
            # If failed at any stage before approval, set to denied
            if stage in [PRStage.CI_RUNNING, PRStage.AI_REVIEW, PRStage.HUMAN_REVIEW]:
                current_stage = PRStage.DENIED

        db_entry.stages_data = stages_data
        db_entry.current_stage = current_stage
        db_entry.updated_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(db_entry)

        logger.info(f"Updated PR #{pr_number} stage {stage.value} to {status.value}")

        return PRStatusService._to_response(db_entry)

    @staticmethod
    async def update_payout(
        db: AsyncSession,
        pr_number: int,
        tx_hash: str,
        amount: int,
        wallet_address: Optional[str] = None
    ) -> Optional[PRStatusResponse]:
        """
        Update payout information for a PR.
        
        Args:
            db: Database session
            pr_number: GitHub PR number
            tx_hash: Solana transaction hash
            amount: Amount of $FNDRY tokens
            wallet_address: Recipient wallet address
            
        Returns:
            Updated PR status if found, None otherwise
        """
        solscan_url = f"https://solscan.io/tx/{tx_hash}"

        return await PRStatusService.update_stage(
            db=db,
            pr_number=pr_number,
            stage=PRStage.PAYOUT,
            status=StageStatus.PASSED,
            details={
                "tx_hash": tx_hash,
                "solscan_url": solscan_url,
                "amount": amount,
                "wallet_address": wallet_address
            }
        )

    @staticmethod
    async def delete(
        db: AsyncSession,
        pr_number: int
    ) -> bool:
        """
        Delete a PR status entry.
        
        Args:
            db: Database session
            pr_number: GitHub PR number
            
        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(PRStatusDB).where(PRStatusDB.pr_number == pr_number)
        )
        db_entry = result.scalar_one_or_none()

        if not db_entry:
            return False

        await db.delete(db_entry)
        await db.commit()

        logger.info(f"Deleted PR status for PR #{pr_number}")
        return True

    @staticmethod
    def _to_response(db_entry: PRStatusDB) -> PRStatusResponse:
        """Convert database entry to response model."""
        # Convert stages_data dict keys to PRStage enum
        from app.models.pr_status import StageDetails
        
        stages = {}
        for stage in PRStage:
            stage_data = db_entry.stages_data.get(stage.value, {})
            stages[stage] = StageDetails(**stage_data)

        return PRStatusResponse(
            id=str(db_entry.id),
            pr_number=db_entry.pr_number,
            pr_title=db_entry.pr_title,
            pr_url=db_entry.pr_url,
            author=db_entry.author,
            bounty_id=db_entry.bounty_id,
            bounty_title=db_entry.bounty_title,
            current_stage=db_entry.current_stage,
            stages=stages,
            created_at=db_entry.created_at,
            updated_at=db_entry.updated_at
        )

    @staticmethod
    def _to_list_item(db_entry: PRStatusDB) -> PRStatusListItem:
        """Convert database entry to list item model."""
        return PRStatusListItem(
            pr_number=db_entry.pr_number,
            pr_title=db_entry.pr_title,
            author=db_entry.author,
            current_stage=db_entry.current_stage,
            bounty_id=db_entry.bounty_id,
            updated_at=db_entry.updated_at
        )