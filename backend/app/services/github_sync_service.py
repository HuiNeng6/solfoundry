"""GitHub Sync Service for bi-directional synchronization.

Implements Issue #28: GitHub ↔ Platform Bi-directional Sync

Features:
- GitHub → Platform: auto-create bounty from labeled issue
- GitHub → Platform: update bounty tier/category/status from labels
- Platform → GitHub: create GitHub issue from platform bounty
- Platform → GitHub: comment on issue when bounty claimed
- Conflict resolution: GitHub is source of truth
- Retry queue for failed syncs
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_sync import (
    SyncDirection,
    SyncStatus,
    SyncEventType,
    SyncQueueDB,
    SyncStatusDB,
    GitHubIssueCreate,
    GitHubIssueUpdate,
    SyncResult,
    ConflictResolution,
)
from app.models.bounty import BountyDB, BountyTier, BountyStatus

logger = logging.getLogger(__name__)


class GitHubSyncError(Exception):
    """Raised when GitHub sync operation fails."""
    pass


class GitHubSyncService:
    """Handles bi-directional sync between GitHub and Platform."""
    
    # Tier mapping from GitHub labels
    TIER_LABELS = {
        "tier-1": BountyTier.T1,
        "tier-2": BountyTier.T2,
        "tier-3": BountyTier.T3,
    }
    
    # Category mapping from GitHub labels
    CATEGORY_LABELS = {
        "frontend": "frontend",
        "backend": "backend",
        "smart_contract": "smart_contract",
        "smart-contract": "smart_contract",
        "documentation": "documentation",
        "testing": "testing",
        "infrastructure": "infrastructure",
        "api": "backend",
        "python": "backend",
        "fastapi": "backend",
    }
    
    # Status mapping from GitHub issue state
    STATUS_MAPPING = {
        "open": BountyStatus.OPEN,
        "closed": BountyStatus.COMPLETED,
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_api_url = "https://api.github.com"
    
    # -------------------------------------------------------------------------
    # GitHub → Platform Sync
    # -------------------------------------------------------------------------
    
    async def sync_issue_to_bounty(
        self,
        action: str,
        issue_number: int,
        issue_title: str,
        issue_body: Optional[str],
        labels: List[str],
        repository: str,
        sender: str,
    ) -> SyncResult:
        """
        Sync a GitHub issue to a platform bounty.
        
        Handles:
        - opened: Create bounty if has "bounty" label
        - labeled: Create or update bounty when "bounty" label added
        - unlabeled: Update bounty metadata
        - closed: Update bounty status
        - reopened: Update bounty status
        """
        try:
            has_bounty_label = "bounty" in labels
            
            if action in ["opened", "labeled"] and has_bounty_label:
                # Create or update bounty
                bounty = await self._create_or_update_bounty_from_issue(
                    github_issue_number=issue_number,
                    github_repo=repository,
                    title=issue_title,
                    description=issue_body or "",
                    labels=labels,
                    state="open",
                )
                
                if bounty:
                    return SyncResult(
                        success=True,
                        direction=SyncDirection.GITHUB_TO_PLATFORM,
                        event_type=SyncEventType.ISSUE_CREATED if action == "opened" else SyncEventType.ISSUE_LABELED,
                        bounty_id=bounty.id,
                        github_issue_number=issue_number,
                        github_issue_url=f"https://github.com/{repository}/issues/{issue_number}",
                        message=f"Bounty {'created' if action == 'opened' else 'updated'} from GitHub issue",
                    )
            
            elif action == "unlabeled" and has_bounty_label:
                # Update bounty metadata when labels change
                updated = await self._update_bounty_from_labels(
                    github_issue_number=issue_number,
                    github_repo=repository,
                    labels=labels,
                )
                
                if updated:
                    return SyncResult(
                        success=True,
                        direction=SyncDirection.GITHUB_TO_PLATFORM,
                        event_type=SyncEventType.ISSUE_UNLABELED,
                        github_issue_number=issue_number,
                        message="Bounty updated from label change",
                    )
            
            elif action == "closed":
                # Update bounty status to completed
                updated = await self._update_bounty_status(
                    github_issue_number=issue_number,
                    github_repo=repository,
                    new_status=BountyStatus.COMPLETED,
                )
                
                if updated:
                    return SyncResult(
                        success=True,
                        direction=SyncDirection.GITHUB_TO_PLATFORM,
                        event_type=SyncEventType.ISSUE_CLOSED,
                        github_issue_number=issue_number,
                        message="Bounty marked as completed",
                    )
            
            elif action == "reopened":
                # Update bounty status back to open
                updated = await self._update_bounty_status(
                    github_issue_number=issue_number,
                    github_repo=repository,
                    new_status=BountyStatus.OPEN,
                )
                
                if updated:
                    return SyncResult(
                        success=True,
                        direction=SyncDirection.GITHUB_TO_PLATFORM,
                        event_type=SyncEventType.ISSUE_REOPENED,
                        github_issue_number=issue_number,
                        message="Bounty reopened",
                    )
            
            return SyncResult(
                success=False,
                direction=SyncDirection.GITHUB_TO_PLATFORM,
                event_type=SyncEventType.ISSUE_CREATED,
                message=f"No action taken for {action}",
            )
            
        except Exception as e:
            logger.error(f"Failed to sync issue #{issue_number} to bounty: {e}")
            
            # Add to retry queue
            await self._add_to_retry_queue(
                direction=SyncDirection.GITHUB_TO_PLATFORM,
                event_type=SyncEventType.ISSUE_CREATED,
                github_issue_number=issue_number,
                github_repo=repository,
                payload={
                    "action": action,
                    "issue_number": issue_number,
                    "issue_title": issue_title,
                    "issue_body": issue_body,
                    "labels": labels,
                    "repository": repository,
                    "sender": sender,
                },
                error_message=str(e),
            )
            
            return SyncResult(
                success=False,
                direction=SyncDirection.GITHUB_TO_PLATFORM,
                event_type=SyncEventType.ISSUE_CREATED,
                github_issue_number=issue_number,
                error=str(e),
            )
    
    # -------------------------------------------------------------------------
    # Platform → GitHub Sync
    # -------------------------------------------------------------------------
    
    async def sync_bounty_to_issue(
        self,
        bounty: BountyDB,
        event_type: SyncEventType = SyncEventType.BOUNTY_CREATED,
    ) -> SyncResult:
        """
        Sync a platform bounty to a GitHub issue.
        
        Creates or updates a GitHub issue based on platform bounty data.
        """
        try:
            if bounty.github_issue_url:
                # Update existing issue
                issue_number = self._extract_issue_number(bounty.github_issue_url)
                repo = self._extract_repo(bounty.github_issue_url)
                
                update_data = GitHubIssueUpdate(
                    title=bounty.title,
                    body=self._generate_issue_body(bounty),
                    labels=self._generate_labels(bounty),
                )
                
                await self._update_github_issue(repo, issue_number, update_data)
                
                return SyncResult(
                    success=True,
                    direction=SyncDirection.PLATFORM_TO_GITHUB,
                    event_type=event_type,
                    bounty_id=bounty.id,
                    github_issue_number=issue_number,
                    github_issue_url=bounty.github_issue_url,
                    message="GitHub issue updated",
                )
            else:
                # Create new issue
                issue_create = GitHubIssueCreate(
                    title=bounty.title,
                    body=self._generate_issue_body(bounty),
                    labels=self._generate_labels(bounty),
                )
                
                repo = os.getenv("GITHUB_DEFAULT_REPO", "SolFoundry/solfoundry")
                result = await self._create_github_issue(repo, issue_create)
                
                issue_number = result.get("number")
                issue_url = result.get("html_url")
                
                # Update bounty with GitHub issue URL
                bounty.github_issue_url = issue_url
                # Note: We would need to add github_issue_number field to BountyDB
                
                return SyncResult(
                    success=True,
                    direction=SyncDirection.PLATFORM_TO_GITHUB,
                    event_type=SyncEventType.BOUNTY_CREATED,
                    bounty_id=bounty.id,
                    github_issue_number=issue_number,
                    github_issue_url=issue_url,
                    message="GitHub issue created",
                )
                
        except Exception as e:
            logger.error(f"Failed to sync bounty {bounty.id} to GitHub: {e}")
            
            # Add to retry queue
            await self._add_to_retry_queue(
                direction=SyncDirection.PLATFORM_TO_GITHUB,
                event_type=event_type,
                bounty_id=bounty.id,
                github_repo=bounty.github_issue_url.split("/issues/")[0].replace("https://github.com/", "") if bounty.github_issue_url else None,
                payload={
                    "bounty_id": bounty.id,
                    "title": bounty.title,
                    "description": bounty.description,
                    "tier": bounty.tier.value,
                    "status": bounty.status.value,
                },
                error_message=str(e),
            )
            
            return SyncResult(
                success=False,
                direction=SyncDirection.PLATFORM_TO_GITHUB,
                event_type=event_type,
                bounty_id=bounty.id,
                error=str(e),
            )
    
    async def comment_on_issue(
        self,
        bounty: BountyDB,
        comment: str,
    ) -> SyncResult:
        """
        Post a comment on a GitHub issue (e.g., when bounty claimed).
        """
        try:
            if not bounty.github_issue_url:
                return SyncResult(
                    success=False,
                    direction=SyncDirection.PLATFORM_TO_GITHUB,
                    event_type=SyncEventType.BOUNTY_CLAIMED,
                    bounty_id=bounty.id,
                    error="No GitHub issue URL",
                )
            
            issue_number = self._extract_issue_number(bounty.github_issue_url)
            repo = self._extract_repo(bounty.github_issue_url)
            
            await self._create_github_comment(repo, issue_number, comment)
            
            return SyncResult(
                success=True,
                direction=SyncDirection.PLATFORM_TO_GITHUB,
                event_type=SyncEventType.BOUNTY_CLAIMED,
                bounty_id=bounty.id,
                github_issue_number=issue_number,
                github_issue_url=bounty.github_issue_url,
                message="Comment posted on GitHub issue",
            )
            
        except Exception as e:
            logger.error(f"Failed to comment on issue: {e}")
            
            return SyncResult(
                success=False,
                direction=SyncDirection.PLATFORM_TO_GITHUB,
                event_type=SyncEventType.BOUNTY_CLAIMED,
                bounty_id=bounty.id,
                error=str(e),
            )
    
    # -------------------------------------------------------------------------
    # Conflict Resolution
    # -------------------------------------------------------------------------
    
    async def resolve_conflict(
        self,
        bounty_id: str,
        github_data: Dict[str, Any],
        platform_data: Dict[str, Any],
    ) -> ConflictResolution:
        """
        Resolve conflict between GitHub and Platform data.
        
        Per requirements: GitHub is source of truth.
        """
        query = select(BountyDB).where(BountyDB.id == bounty_id)
        result = await self.db.execute(query)
        bounty = result.scalar_one_or_none()
        
        if not bounty:
            raise GitHubSyncError(f"Bounty {bounty_id} not found")
        
        # Apply GitHub data (source of truth)
        if "title" in github_data:
            bounty.title = github_data["title"]
        if "body" in github_data:
            bounty.description = github_data["body"]
        if "labels" in github_data:
            tier, category = self._parse_labels(github_data["labels"])
            bounty.tier = tier
            # Note: category would need to be added to BountyDB
        
        resolution = ConflictResolution(
            bounty_id=bounty_id,
            github_issue_number=self._extract_issue_number(bounty.github_issue_url) if bounty.github_issue_url else 0,
            github_repo=self._extract_repo(bounty.github_issue_url) if bounty.github_issue_url else "",
            github_data=github_data,
            platform_data=platform_data,
            resolution="github_wins",
            resolved_data={
                "title": bounty.title,
                "description": bounty.description,
                "tier": bounty.tier.value,
            },
        )
        
        logger.info(f"Conflict resolved for bounty {bounty_id}: GitHub data applied")
        
        return resolution
    
    # -------------------------------------------------------------------------
    # Retry Queue
    # -------------------------------------------------------------------------
    
    async def get_pending_syncs(self, limit: int = 100) -> List[SyncQueueDB]:
        """Get pending sync operations from retry queue."""
        query = select(SyncQueueDB).where(
            SyncQueueDB.status == SyncStatus.PENDING
        ).order_by(SyncQueueDB.created_at.asc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def retry_failed_syncs(self, max_retries: int = 3) -> List[SyncResult]:
        """Retry failed sync operations."""
        query = select(SyncQueueDB).where(
            SyncQueueDB.status == SyncStatus.FAILED,
            SyncQueueDB.retry_count < SyncQueueDB.max_retries,
        ).order_by(SyncQueueDB.created_at.asc())
        
        result = await self.db.execute(query)
        failed_syncs = list(result.scalars().all())
        
        results = []
        for sync_item in failed_syncs:
            # Retry the sync operation
            # This would need to be implemented based on event_type
            sync_item.retry_count += 1
            sync_item.status = SyncStatus.IN_PROGRESS
            sync_item.last_attempt_at = datetime.now(timezone.utc)
            
            # Placeholder for retry logic
            # In real implementation, would retry the actual sync operation
            logger.info(f"Retrying sync {sync_item.id} (attempt {sync_item.retry_count})")
            
            results.append(SyncResult(
                success=False,  # Placeholder
                direction=sync_item.direction,
                event_type=sync_item.event_type,
                bounty_id=sync_item.bounty_id,
                github_issue_number=sync_item.github_issue_number,
                message="Retry queued",
            ))
        
        return results
    
    # -------------------------------------------------------------------------
    # Sync Status Dashboard
    # -------------------------------------------------------------------------
    
    async def get_sync_status(self) -> SyncStatusDB:
        """Get current sync status for dashboard."""
        query = select(SyncStatusDB).limit(1)
        result = await self.db.execute(query)
        status = result.scalar_one_or_none()
        
        if not status:
            # Create initial status
            status = SyncStatusDB()
            self.db.add(status)
        
        return status
    
    async def update_sync_status(
        self,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """Update sync status after operation."""
        status = await self.get_sync_status()
        
        status.last_sync_at = datetime.now(timezone.utc)
        status.total_syncs_count += 1
        
        if success:
            status.last_successful_sync_at = datetime.now(timezone.utc)
        else:
            status.failed_syncs_count += 1
            status.last_error = error
            status.last_error_at = datetime.now(timezone.utc)
        
        status.updated_at = datetime.now(timezone.utc)
    
    # -------------------------------------------------------------------------
    # Private Helper Methods
    # -------------------------------------------------------------------------
    
    async def _create_or_update_bounty_from_issue(
        self,
        github_issue_number: int,
        github_repo: str,
        title: str,
        description: str,
        labels: List[str],
        state: str,
    ) -> Optional[BountyDB]:
        """Create or update bounty from GitHub issue data."""
        # Check if bounty exists
        query = select(BountyDB).where(
            BountyDB.github_issue_url.like(f"%github.com%/{github_repo}/issues/{github_issue_number}%")
        )
        result = await self.db.execute(query)
        bounty = result.scalar_one_or_none()
        
        tier, category = self._parse_labels(labels)
        status = self.STATUS_MAPPING.get(state, BountyStatus.OPEN)
        
        if bounty:
            # Update existing bounty
            bounty.title = title
            bounty.description = description
            bounty.tier = tier
            bounty.status = status
            bounty.updated_at = datetime.now(timezone.utc)
            
            logger.info(f"Updated bounty {bounty.id} from GitHub issue #{github_issue_number}")
        else:
            # Create new bounty
            # Calculate reward based on tier
            reward_amount = {BountyTier.T1: 100000, BountyTier.T2: 450000, BountyTier.T3: 1000000}
            
            bounty = BountyDB(
                title=title,
                description=description,
                tier=tier,
                reward_amount=reward_amount.get(tier, 450000),
                status=status,
                github_issue_url=f"https://github.com/{github_repo}/issues/{github_issue_number}",
                created_by="github_sync",
            )
            
            self.db.add(bounty)
            logger.info(f"Created bounty from GitHub issue #{github_issue_number}")
        
        return bounty
    
    async def _update_bounty_from_labels(
        self,
        github_issue_number: int,
        github_repo: str,
        labels: List[str],
    ) -> bool:
        """Update bounty tier and category from labels."""
        query = select(BountyDB).where(
            BountyDB.github_issue_url.like(f"%github.com%/{github_repo}/issues/{github_issue_number}%")
        )
        result = await self.db.execute(query)
        bounty = result.scalar_one_or_none()
        
        if not bounty:
            return False
        
        tier, category = self._parse_labels(labels)
        bounty.tier = tier
        bounty.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated bounty {bounty.id} tier/category from labels")
        return True
    
    async def _update_bounty_status(
        self,
        github_issue_number: int,
        github_repo: str,
        new_status: BountyStatus,
    ) -> bool:
        """Update bounty status."""
        query = select(BountyDB).where(
            BountyDB.github_issue_url.like(f"%github.com%/{github_repo}/issues/{github_issue_number}%")
        )
        result = await self.db.execute(query)
        bounty = result.scalar_one_or_none()
        
        if not bounty:
            return False
        
        bounty.status = new_status
        bounty.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Updated bounty {bounty.id} status to {new_status}")
        return True
    
    def _parse_labels(self, labels: List[str]) -> tuple[BountyTier, str]:
        """Parse tier and category from GitHub labels."""
        tier = BountyTier.T2  # Default
        category = "other"
        
        for label in labels:
            label_lower = label.lower()
            
            # Check for tier
            if label_lower in self.TIER_LABELS:
                tier = self.TIER_LABELS[label_lower]
            
            # Check for category
            if label_lower in self.CATEGORY_LABELS:
                category = self.CATEGORY_LABELS[label_lower]
        
        return tier, category
    
    async def _create_github_issue(
        self,
        repo: str,
        issue_data: GitHubIssueCreate,
    ) -> Dict[str, Any]:
        """Create a GitHub issue via API."""
        if not self.github_token:
            raise GitHubSyncError("GITHUB_TOKEN not configured")
        
        url = f"{self.github_api_url}/repos/{repo}/issues"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=issue_data.model_dump(exclude_none=True),
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            
            if response.status_code not in [200, 201]:
                raise GitHubSyncError(f"Failed to create issue: {response.text}")
            
            return response.json()
    
    async def _update_github_issue(
        self,
        repo: str,
        issue_number: int,
        issue_data: GitHubIssueUpdate,
    ) -> Dict[str, Any]:
        """Update a GitHub issue via API."""
        if not self.github_token:
            raise GitHubSyncError("GITHUB_TOKEN not configured")
        
        url = f"{self.github_api_url}/repos/{repo}/issues/{issue_number}"
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                json=issue_data.model_dump(exclude_none=True),
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            
            if response.status_code != 200:
                raise GitHubSyncError(f"Failed to update issue: {response.text}")
            
            return response.json()
    
    async def _create_github_comment(
        self,
        repo: str,
        issue_number: int,
        comment: str,
    ) -> Dict[str, Any]:
        """Create a comment on a GitHub issue."""
        if not self.github_token:
            raise GitHubSyncError("GITHUB_TOKEN not configured")
        
        url = f"{self.github_api_url}/repos/{repo}/issues/{issue_number}/comments"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"body": comment},
                headers={
                    "Authorization": f"Bearer {self.github_token}",
                    "Accept": "application/vnd.github+json",
                },
            )
            
            if response.status_code not in [200, 201]:
                raise GitHubSyncError(f"Failed to create comment: {response.text}")
            
            return response.json()
    
    def _generate_issue_body(self, bounty: BountyDB) -> str:
        """Generate GitHub issue body from bounty data."""
        body = f"""# {bounty.title}

## Description
{bounty.description}

## Bounty Details
- **Tier**: {bounty.tier.name}
- **Reward**: {bounty.reward_amount:,} $FNDRY
- **Status**: {bounty.status.value}

---
*This bounty is synced from SolFoundry platform.*
*Bounty ID: {bounty.id}*
"""
        return body
    
    def _generate_labels(self, bounty: BountyDB) -> List[str]:
        """Generate GitHub labels from bounty data."""
        labels = ["bounty"]
        
        # Add tier label
        labels.append(f"tier-{bounty.tier.value}")
        
        # Add status label
        labels.append(bounty.status.value)
        
        return labels
    
    def _extract_issue_number(self, url: str) -> int:
        """Extract issue number from GitHub URL."""
        parts = url.split("/issues/")
        if len(parts) == 2:
            return int(parts[1].split("/")[0].split("?")[0])
        raise ValueError(f"Invalid GitHub issue URL: {url}")
    
    def _extract_repo(self, url: str) -> str:
        """Extract repository from GitHub URL."""
        parts = url.replace("https://github.com/", "").split("/issues/")
        if len(parts) == 2:
            return parts[0]
        raise ValueError(f"Invalid GitHub issue URL: {url}")
    
    async def _add_to_retry_queue(
        self,
        direction: SyncDirection,
        event_type: SyncEventType,
        bounty_id: Optional[str],
        github_issue_number: Optional[int],
        github_repo: Optional[str],
        payload: Dict[str, Any],
        error_message: str,
    ) -> SyncQueueDB:
        """Add failed sync to retry queue."""
        queue_item = SyncQueueDB(
            direction=direction,
            event_type=event_type,
            bounty_id=bounty_id,
            github_issue_number=github_issue_number,
            github_repo=github_repo,
            payload=payload,
            status=SyncStatus.FAILED,
            error_message=error_message,
        )
        
        self.db.add(queue_item)
        
        # Update sync status
        await self.update_sync_status(success=False, error=error_message)
        
        return queue_item