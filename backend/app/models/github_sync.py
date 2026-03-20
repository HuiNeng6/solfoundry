"""GitHub Sync models for bi-directional synchronization.

Implements Issue #28: GitHub ↔ Platform Bi-directional Sync
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class SyncDirection(str, Enum):
    """Direction of synchronization."""
    GITHUB_TO_PLATFORM = "github_to_platform"
    PLATFORM_TO_GITHUB = "platform_to_github"


class SyncStatus(str, Enum):
    """Status of a sync operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"


class SyncEventType(str, Enum):
    """Types of events that trigger sync."""
    ISSUE_CREATED = "issue_created"
    ISSUE_LABELED = "issue_labeled"
    ISSUE_UNLABELED = "issue_unlabeled"
    ISSUE_CLOSED = "issue_closed"
    ISSUE_REOPENED = "issue_reopened"
    BOUNTY_CREATED = "bounty_created"
    BOUNTY_UPDATED = "bounty_updated"
    BOUNTY_CLAIMED = "bounty_claimed"
    BOUNTY_STATUS_CHANGED = "bounty_status_changed"


class SyncQueueDB(BaseModel):
    """Database model for sync queue (failed syncs for retry)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    direction: SyncDirection
    event_type: SyncEventType
    bounty_id: Optional[str] = None
    github_issue_number: Optional[int] = None
    github_repo: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    status: SyncStatus = SyncStatus.PENDING
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_attempt_at: Optional[datetime] = None


class SyncStatusDB(BaseModel):
    """Database model for tracking sync status dashboard."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    last_sync_at: Optional[datetime] = None
    last_successful_sync_at: Optional[datetime] = None
    pending_syncs_count: int = 0
    failed_syncs_count: int = 0
    total_syncs_count: int = 0
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GitHubIssueCreate(BaseModel):
    """Payload for creating a GitHub issue from platform bounty."""
    title: str = Field(..., min_length=1, max_length=256)
    body: str = Field(default="", max_length=65536)
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)


class GitHubIssueUpdate(BaseModel):
    """Payload for updating a GitHub issue."""
    title: Optional[str] = Field(None, min_length=1, max_length=256)
    body: Optional[str] = Field(None, max_length=65536)
    state: Optional[str] = Field(None, pattern="^(open|closed)$")
    labels: Optional[list[str]] = None


class SyncResult(BaseModel):
    """Result of a sync operation."""
    success: bool
    direction: SyncDirection
    event_type: SyncEventType
    bounty_id: Optional[str] = None
    github_issue_number: Optional[int] = None
    github_issue_url: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SyncDashboardResponse(BaseModel):
    """Response model for sync status dashboard."""
    last_sync_at: Optional[datetime] = None
    last_successful_sync_at: Optional[datetime] = None
    pending_syncs_count: int = 0
    failed_syncs_count: int = 0
    total_syncs_count: int = 0
    last_error: Optional[str] = None
    last_error_at: Optional[datetime] = None
    pending_items: list[dict] = Field(default_factory=list)
    failed_items: list[dict] = Field(default_factory=list)


class ConflictResolution(BaseModel):
    """Model for conflict resolution between GitHub and Platform."""
    bounty_id: str
    github_issue_number: int
    github_repo: str
    github_data: dict = Field(default_factory=dict)
    platform_data: dict = Field(default_factory=dict)
    resolution: str = "github_wins"  # GitHub is source of truth per requirements
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_data: dict = Field(default_factory=dict)