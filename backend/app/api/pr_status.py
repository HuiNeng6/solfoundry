"""PR Status API endpoints."""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.pr_status import (
    PRStage,
    StageStatus,
    PRStatusCreate,
    PRStatusUpdate,
    PRStatusResponse,
    PRStatusListResponse
)
from app.services.pr_status_service import PRStatusService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pr-status", tags=["pr-status"])


# WebSocket connection manager
class ConnectionManager:
    """Manage WebSocket connections for real-time PR status updates."""

    def __init__(self):
        # Map of pr_number -> list of websocket connections
        self.active_connections: Dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, pr_number: int):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        if pr_number not in self.active_connections:
            self.active_connections[pr_number] = []
        self.active_connections[pr_number].append(websocket)
        logger.info(f"WebSocket connected for PR #{pr_number}")

    def disconnect(self, websocket: WebSocket, pr_number: int):
        """Remove a WebSocket connection."""
        if pr_number in self.active_connections:
            if websocket in self.active_connections[pr_number]:
                self.active_connections[pr_number].remove(websocket)
            if not self.active_connections[pr_number]:
                del self.active_connections[pr_number]
        logger.info(f"WebSocket disconnected for PR #{pr_number}")

    async def broadcast(self, pr_number: int, message: Dict[str, Any]):
        """Broadcast a message to all connections for a PR."""
        if pr_number in self.active_connections:
            for connection in self.active_connections[pr_number]:
                try:
                    import json
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")


manager = ConnectionManager()


@router.post("", response_model=PRStatusResponse, status_code=201)
async def create_pr_status(
    data: PRStatusCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new PR status entry.
    
    This is typically called when a new PR is submitted for a bounty.
    """
    try:
        result = await PRStatusService.create(db, data)
        # Broadcast the new status
        await manager.broadcast(data.pr_number, result.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{pr_number}", response_model=PRStatusResponse)
async def get_pr_status(
    pr_number: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get PR status by PR number.
    """
    result = await PRStatusService.get(db, pr_number)
    if not result:
        raise HTTPException(status_code=404, detail=f"PR #{pr_number} not found")
    return result


@router.get("", response_model=PRStatusListResponse)
async def list_pr_statuses(
    bounty_id: Optional[str] = Query(None, description="Filter by bounty ID"),
    author: Optional[str] = Query(None, description="Filter by author"),
    current_stage: Optional[PRStage] = Query(None, description="Filter by current stage"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    db: AsyncSession = Depends(get_db)
):
    """
    List PR statuses with optional filters.
    """
    return await PRStatusService.list(
        db,
        bounty_id=bounty_id,
        author=author,
        current_stage=current_stage,
        skip=skip,
        limit=limit
    )


@router.patch("/{pr_number}", response_model=PRStatusResponse)
async def update_pr_status(
    pr_number: int,
    data: PRStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update PR status.
    
    This is typically used for manual status updates.
    """
    result = await PRStatusService.get(db, pr_number)
    if not result:
        raise HTTPException(status_code=404, detail=f"PR #{pr_number} not found")

    # For complex updates, use the stage-specific endpoints
    if data.stages:
        # Update specific stages
        for stage_name, stage_details in data.stages.items():
            try:
                stage = PRStage(stage_name)
                status = stage_details.status
                details = stage_details.model_dump(exclude={"status"})
                await PRStatusService.update_stage(db, pr_number, stage, status, details)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid stage: {stage_name}")

    result = await PRStatusService.get(db, pr_number)
    if result:
        await manager.broadcast(pr_number, result.model_dump())
    return result


@router.post("/{pr_number}/stage/{stage}", response_model=PRStatusResponse)
async def update_stage(
    pr_number: int,
    stage: PRStage,
    status: StageStatus = Query(..., description="New status for the stage"),
    message: Optional[str] = Query(None, description="Optional message"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a specific stage in the PR pipeline.
    
    This is the recommended way to update stage status.
    """
    details = {"message": message} if message else None

    result = await PRStatusService.update_stage(
        db, pr_number, stage, status, details
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"PR #{pr_number} not found")

    await manager.broadcast(pr_number, result.model_dump())
    return result


@router.post("/{pr_number}/ai-review", response_model=PRStatusResponse)
async def update_ai_review(
    pr_number: int,
    status: StageStatus = Query(..., description="AI Review status"),
    quality: float = Query(..., ge=0, le=10, description="Quality score"),
    correctness: float = Query(..., ge=0, le=10, description="Correctness score"),
    security: float = Query(..., ge=0, le=10, description="Security score"),
    completeness: float = Query(..., ge=0, le=10, description="Completeness score"),
    tests: float = Query(..., ge=0, le=10, description="Tests score"),
    message: Optional[str] = Query(None, description="Optional message"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update AI review stage with score breakdown.
    """
    overall = (quality + correctness + security + completeness + tests) / 5

    scores = {
        "quality": quality,
        "correctness": correctness,
        "security": security,
        "completeness": completeness,
        "tests": tests,
        "overall": overall
    }

    details = {
        "scores": scores,
        "message": message
    }

    result = await PRStatusService.update_stage(
        db, pr_number, PRStage.AI_REVIEW, status, details
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"PR #{pr_number} not found")

    await manager.broadcast(pr_number, result.model_dump())
    return result


@router.post("/{pr_number}/payout", response_model=PRStatusResponse)
async def update_payout(
    pr_number: int,
    tx_hash: str = Query(..., description="Solana transaction hash"),
    amount: int = Query(..., gt=0, description="Amount in $FNDRY tokens"),
    wallet_address: Optional[str] = Query(None, description="Recipient wallet address"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update payout stage with transaction details.
    """
    result = await PRStatusService.update_payout(
        db, pr_number, tx_hash, amount, wallet_address
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"PR #{pr_number} not found")

    await manager.broadcast(pr_number, result.model_dump())
    return result


@router.delete("/{pr_number}", status_code=204)
async def delete_pr_status(
    pr_number: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a PR status entry.
    """
    deleted = await PRStatusService.delete(db, pr_number)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"PR #{pr_number} not found")
    return None


# WebSocket endpoint for real-time updates
@router.websocket("/ws/{pr_number}")
async def websocket_pr_status(
    websocket: WebSocket,
    pr_number: int
):
    """
    WebSocket endpoint for real-time PR status updates.
    
    Clients can connect to this endpoint to receive live updates
    for a specific PR's status.
    """
    await manager.connect(websocket, pr_number)

    try:
        # Send initial status
        async with get_db() as db:
            result = await PRStatusService.get(db, pr_number)
            if result:
                import json
                await websocket.send_text(json.dumps(result.model_dump()))

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands if needed
            logger.debug(f"Received WebSocket message: {data}")

    except WebSocketDisconnect:
        manager.disconnect(websocket, pr_number)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, pr_number)