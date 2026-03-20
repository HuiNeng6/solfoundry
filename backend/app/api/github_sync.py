"""GitHub Sync API endpoints.

Implements Issue #28: GitHub ↔ Platform Bi-directional Sync
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.github_sync import (
    SyncDirection,
    SyncEventType,
    SyncResult,
    SyncDashboardResponse,
    GitHubIssueCreate,
)
from app.services.github_sync_service import GitHubSyncService, GitHubSyncError

router = APIRouter(prefix="/sync", tags=["github-sync"])


@router.post("/issue/{issue_number}", response_model=SyncResult)
async def sync_issue(
    issue_number: int,
    repository: str,
    action: str = "opened",
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger sync of a GitHub issue to platform bounty.
    
    This is useful for:
    - Retrying failed syncs
    - Initial sync of existing issues
    - Testing sync functionality
    """
    sync_service = GitHubSyncService(db)
    
    try:
        result = await sync_service.sync_issue_to_bounty(
            action=action,
            issue_number=issue_number,
            issue_title="",  # Would need to fetch from GitHub API
            issue_body="",
            labels=["bounty"],
            repository=repository,
            sender="manual_sync",
        )
        
        await db.commit()
        return result
        
    except GitHubSyncError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bounty/{bounty_id}", response_model=SyncResult)
async def sync_bounty(
    bounty_id: str,
    background_tasks: BackgroundTasks = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger sync of a platform bounty to GitHub issue.
    
    This creates or updates the corresponding GitHub issue.
    """
    from app.models.bounty import BountyDB
    from sqlalchemy import select
    
    sync_service = GitHubSyncService(db)
    
    # Get bounty
    query = select(BountyDB).where(BountyDB.id == bounty_id)
    result = await db.execute(query)
    bounty = result.scalar_one_or_none()
    
    if not bounty:
        raise HTTPException(status_code=404, detail="Bounty not found")
    
    try:
        sync_result = await sync_service.sync_bounty_to_issue(bounty)
        await db.commit()
        return sync_result
        
    except GitHubSyncError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/comment/{bounty_id}", response_model=SyncResult)
async def post_comment(
    bounty_id: str,
    comment: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Post a comment on the GitHub issue associated with a bounty.
    
    Used when:
    - Bounty is claimed
    - Bounty status changes
    - Important updates occur
    """
    from app.models.bounty import BountyDB
    from sqlalchemy import select
    
    sync_service = GitHubSyncService(db)
    
    # Get bounty
    query = select(BountyDB).where(BountyDB.id == bounty_id)
    result = await db.execute(query)
    bounty = result.scalar_one_or_none()
    
    if not bounty:
        raise HTTPException(status_code=404, detail="Bounty not found")
    
    try:
        sync_result = await sync_service.comment_on_issue(bounty, comment)
        await db.commit()
        return sync_result
        
    except GitHubSyncError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=SyncDashboardResponse)
async def get_sync_status(
    db: AsyncSession = Depends(get_db),
):
    """
    Get sync status dashboard.
    
    Shows:
    - Last sync time
    - Pending syncs count
    - Failed syncs count
    - Last error
    """
    from app.models.github_sync import SyncQueueDB, SyncStatus as SyncQueueStatus
    from sqlalchemy import select
    
    sync_service = GitHubSyncService(db)
    status = await sync_service.get_sync_status()
    
    # Get pending items
    pending_query = select(SyncQueueDB).where(
        SyncQueueDB.status == SyncQueueStatus.PENDING
    ).limit(10)
    pending_result = await db.execute(pending_query)
    pending_items = [
        {
            "id": item.id,
            "direction": item.direction.value,
            "event_type": item.event_type.value,
            "created_at": item.created_at.isoformat(),
        }
        for item in pending_result.scalars().all()
    ]
    
    # Get failed items
    failed_query = select(SyncQueueDB).where(
        SyncQueueDB.status == SyncQueueStatus.FAILED
    ).limit(10)
    failed_result = await db.execute(failed_query)
    failed_items = [
        {
            "id": item.id,
            "direction": item.direction.value,
            "event_type": item.event_type.value,
            "error": item.error_message,
            "created_at": item.created_at.isoformat(),
        }
        for item in failed_result.scalars().all()
    ]
    
    return SyncDashboardResponse(
        last_sync_at=status.last_sync_at,
        last_successful_sync_at=status.last_successful_sync_at,
        pending_syncs_count=status.pending_syncs_count,
        failed_syncs_count=status.failed_syncs_count,
        total_syncs_count=status.total_syncs_count,
        last_error=status.last_error,
        last_error_at=status.last_error_at,
        pending_items=pending_items,
        failed_items=failed_items,
    )


@router.post("/retry", response_model=list[SyncResult])
async def retry_failed_syncs(
    max_retries: int = 3,
    db: AsyncSession = Depends(get_db),
):
    """
    Retry failed sync operations.
    
    This endpoint triggers retry of all failed syncs that haven't
    exceeded the maximum retry count.
    """
    sync_service = GitHubSyncService(db)
    
    try:
        results = await sync_service.retry_failed_syncs(max_retries)
        await db.commit()
        return results
        
    except GitHubSyncError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resolve-conflict/{bounty_id}")
async def resolve_conflict(
    bounty_id: str,
    github_data: dict,
    platform_data: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually resolve a sync conflict between GitHub and Platform.
    
    By default, GitHub data wins (per requirements).
    """
    sync_service = GitHubSyncService(db)
    
    try:
        resolution = await sync_service.resolve_conflict(
            bounty_id=bounty_id,
            github_data=github_data,
            platform_data=platform_data,
        )
        await db.commit()
        return resolution
        
    except GitHubSyncError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=list[dict])
async def list_pending_syncs(
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    List pending sync operations in the retry queue.
    """
    from app.models.github_sync import SyncQueueDB
    from sqlalchemy import select
    
    sync_service = GitHubSyncService(db)
    pending_syncs = await sync_service.get_pending_syncs(limit)
    
    return [
        {
            "id": sync.id,
            "direction": sync.direction.value,
            "event_type": sync.event_type.value,
            "bounty_id": sync.bounty_id,
            "github_issue_number": sync.github_issue_number,
            "status": sync.status.value,
            "retry_count": sync.retry_count,
            "error": sync.error_message,
            "created_at": sync.created_at.isoformat(),
        }
        for sync in pending_syncs
    ]