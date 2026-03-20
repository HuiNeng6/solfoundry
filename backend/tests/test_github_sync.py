"""Tests for GitHub Sync functionality.

Tests Issue #28: GitHub ↔ Platform Bi-directional Sync
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from app.models.github_sync import (
    SyncDirection,
    SyncStatus,
    SyncEventType,
    SyncQueueDB,
    SyncStatusDB,
    SyncResult,
    GitHubIssueCreate,
)
from app.models.bounty import BountyDB, BountyTier, BountyStatus
from app.services.github_sync_service import GitHubSyncService, GitHubSyncError


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def sync_service(mock_db):
    """Create GitHubSyncService with mocked DB."""
    return GitHubSyncService(mock_db)


@pytest.fixture
def sample_bounty():
    """Create a sample bounty for testing."""
    return BountyDB(
        id="test-bounty-id",
        title="Test Bounty",
        description="Test description",
        tier=BountyTier.T2,
        reward_amount=450000,
        status=BountyStatus.OPEN,
        github_issue_url="https://github.com/SolFoundry/solfoundry/issues/28",
        created_by="test_user",
    )


class TestGitHubSyncService:
    """Tests for GitHubSyncService."""
    
    @pytest.mark.asyncio
    async def test_parse_labels_tier(self, sync_service):
        """Test label parsing for tier."""
        labels = ["bounty", "tier-2", "backend"]
        tier, category = sync_service._parse_labels(labels)
        
        assert tier == BountyTier.T2
        assert category == "backend"
    
    @pytest.mark.asyncio
    async def test_parse_labels_default(self, sync_service):
        """Test label parsing with default values."""
        labels = ["bounty", "other"]
        tier, category = sync_service._parse_labels(labels)
        
        assert tier == BountyTier.T2  # Default
        assert category == "other"
    
    @pytest.mark.asyncio
    async def test_extract_issue_number(self, sync_service):
        """Test extracting issue number from URL."""
        url = "https://github.com/SolFoundry/solfoundry/issues/28"
        issue_number = sync_service._extract_issue_number(url)
        
        assert issue_number == 28
    
    @pytest.mark.asyncio
    async def test_extract_repo(self, sync_service):
        """Test extracting repository from URL."""
        url = "https://github.com/SolFoundry/solfoundry/issues/28"
        repo = sync_service._extract_repo(url)
        
        assert repo == "SolFoundry/solfoundry"
    
    @pytest.mark.asyncio
    async def test_generate_issue_body(self, sync_service, sample_bounty):
        """Test generating issue body from bounty."""
        body = sync_service._generate_issue_body(sample_bounty)
        
        assert "Test Bounty" in body
        assert "Test description" in body
        assert "TIER.T2" in body or "T2" in body
        assert "450,000" in body
        assert "test-bounty-id" in body
    
    @pytest.mark.asyncio
    async def test_generate_labels(self, sync_service, sample_bounty):
        """Test generating labels from bounty."""
        labels = sync_service._generate_labels(sample_bounty)
        
        assert "bounty" in labels
        assert "tier-2" in labels
        assert "open" in labels
    
    @pytest.mark.asyncio
    async def test_sync_issue_to_bounty_opened(self, sync_service, mock_db):
        """Test syncing a new issue to bounty."""
        # Mock database query to return None (bounty doesn't exist)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await sync_service.sync_issue_to_bounty(
            action="opened",
            issue_number=28,
            issue_title="Test Issue",
            issue_body="Test body",
            labels=["bounty", "tier-2", "backend"],
            repository="SolFoundry/solfoundry",
            sender="test_user",
        )
        
        assert result.success is True
        assert result.direction == SyncDirection.GITHUB_TO_PLATFORM
        assert result.event_type == SyncEventType.ISSUE_CREATED
        assert result.github_issue_number == 28
    
    @pytest.mark.asyncio
    async def test_sync_issue_to_bounty_labeled(self, sync_service, mock_db):
        """Test syncing issue when labeled with bounty."""
        # Mock database query to return None (bounty doesn't exist)
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        result = await sync_service.sync_issue_to_bounty(
            action="labeled",
            issue_number=28,
            issue_title="Test Issue",
            issue_body="Test body",
            labels=["bounty", "tier-3"],
            repository="SolFoundry/solfoundry",
            sender="test_user",
        )
        
        assert result.success is True
        assert result.event_type == SyncEventType.ISSUE_LABELED
    
    @pytest.mark.asyncio
    async def test_sync_issue_to_bounty_closed(self, sync_service, mock_db, sample_bounty):
        """Test syncing issue when closed."""
        # Mock database query to return existing bounty
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_bounty
        mock_db.execute.return_value = mock_result
        
        result = await sync_service.sync_issue_to_bounty(
            action="closed",
            issue_number=28,
            issue_title="Test Issue",
            issue_body="Test body",
            labels=["bounty"],
            repository="SolFoundry/solfoundry",
            sender="test_user",
        )
        
        assert result.success is True
        assert result.event_type == SyncEventType.ISSUE_CLOSED
        assert result.message == "Bounty marked as completed"
    
    @pytest.mark.asyncio
    async def test_sync_issue_to_bounty_no_bounty_label(self, sync_service, mock_db):
        """Test syncing issue without bounty label."""
        result = await sync_service.sync_issue_to_bounty(
            action="opened",
            issue_number=28,
            issue_title="Test Issue",
            issue_body="Test body",
            labels=["other"],  # No bounty label
            repository="SolFoundry/solfoundry",
            sender="test_user",
        )
        
        # Should not create bounty
        assert result.success is False
    
    @pytest.mark.asyncio
    async def test_sync_bounty_to_issue_create(self, sync_service, mock_db, sample_bounty):
        """Test creating GitHub issue from bounty."""
        # Remove GitHub URL to force creation
        sample_bounty.github_issue_url = None
        
        # Mock _create_github_issue
        with patch.object(
            sync_service,
            '_create_github_issue',
            return_value={
                "number": 100,
                "html_url": "https://github.com/SolFoundry/solfoundry/issues/100",
            }
        ):
            result = await sync_service.sync_bounty_to_issue(sample_bounty)
        
        assert result.success is True
        assert result.direction == SyncDirection.PLATFORM_TO_GITHUB
        assert result.event_type == SyncEventType.BOUNTY_CREATED
        assert result.github_issue_number == 100
    
    @pytest.mark.asyncio
    async def test_sync_bounty_to_issue_update(self, sync_service, mock_db, sample_bounty):
        """Test updating existing GitHub issue."""
        # Mock _update_github_issue
        with patch.object(
            sync_service,
            '_update_github_issue',
            return_value={"number": 28}
        ):
            result = await sync_service.sync_bounty_to_issue(sample_bounty)
        
        assert result.success is True
        assert result.message == "GitHub issue updated"
    
    @pytest.mark.asyncio
    async def test_comment_on_issue(self, sync_service, mock_db, sample_bounty):
        """Test posting comment on GitHub issue."""
        # Mock _create_github_comment
        with patch.object(
            sync_service,
            '_create_github_comment',
            return_value={"id": 1}
        ):
            result = await sync_service.comment_on_issue(
                bounty=sample_bounty,
                comment="Test comment",
            )
        
        assert result.success is True
        assert result.event_type == SyncEventType.BOUNTY_CLAIMED
        assert result.message == "Comment posted on GitHub issue"
    
    @pytest.mark.asyncio
    async def test_comment_on_issue_no_url(self, sync_service, mock_db):
        """Test commenting on bounty without GitHub URL."""
        bounty = BountyDB(
            id="test-id",
            title="Test",
            description="Test",
            tier=BountyTier.T2,
            reward_amount=450000,
            status=BountyStatus.OPEN,
            github_issue_url=None,  # No URL
        )
        
        result = await sync_service.comment_on_issue(
            bounty=bounty,
            comment="Test comment",
        )
        
        assert result.success is False
        assert "No GitHub issue URL" in result.error
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_github_wins(self, sync_service, mock_db, sample_bounty):
        """Test conflict resolution with GitHub as source of truth."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_bounty
        mock_db.execute.return_value = mock_result
        
        resolution = await sync_service.resolve_conflict(
            bounty_id="test-bounty-id",
            github_data={
                "title": "GitHub Title",
                "body": "GitHub Body",
            },
            platform_data={
                "title": "Platform Title",
                "body": "Platform Body",
            },
        )
        
        assert resolution.resolution == "github_wins"
        assert resolution.resolved_data["title"] == "GitHub Title"
    
    @pytest.mark.asyncio
    async def test_get_sync_status(self, sync_service, mock_db):
        """Test getting sync status."""
        # Mock database query
        mock_status = SyncStatusDB()
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = mock_status
        mock_db.execute.return_value = mock_result
        
        status = await sync_service.get_sync_status()
        
        assert isinstance(status, SyncStatusDB)
    
    @pytest.mark.asyncio
    async def test_update_sync_status_success(self, sync_service, mock_db):
        """Test updating sync status on success."""
        # Mock get_sync_status
        mock_status = SyncStatusDB()
        with patch.object(
            sync_service,
            'get_sync_status',
            return_value=mock_status
        ):
            await sync_service.update_sync_status(success=True)
        
        assert mock_status.last_sync_at is not None
        assert mock_status.last_successful_sync_at is not None
        assert mock_status.total_syncs_count == 1
    
    @pytest.mark.asyncio
    async def test_update_sync_status_failure(self, sync_service, mock_db):
        """Test updating sync status on failure."""
        # Mock get_sync_status
        mock_status = SyncStatusDB()
        with patch.object(
            sync_service,
            'get_sync_status',
            return_value=mock_status
        ):
            await sync_service.update_sync_status(
                success=False,
                error="Test error"
            )
        
        assert mock_status.last_sync_at is not None
        assert mock_status.failed_syncs_count == 1
        assert mock_status.last_error == "Test error"


class TestSyncModels:
    """Tests for sync-related Pydantic models."""
    
    def test_sync_queue_db_defaults(self):
        """Test SyncQueueDB default values."""
        queue_item = SyncQueueDB(
            direction=SyncDirection.GITHUB_TO_PLATFORM,
            event_type=SyncEventType.ISSUE_CREATED,
        )
        
        assert queue_item.status == SyncStatus.PENDING
        assert queue_item.retry_count == 0
        assert queue_item.max_retries == 3
    
    def test_sync_status_db_defaults(self):
        """Test SyncStatusDB default values."""
        status = SyncStatusDB()
        
        assert status.pending_syncs_count == 0
        assert status.failed_syncs_count == 0
        assert status.total_syncs_count == 0
    
    def test_github_issue_create_validation(self):
        """Test GitHubIssueCreate validation."""
        issue = GitHubIssueCreate(
            title="Test Issue",
            body="Test body",
            labels=["bounty", "tier-2"],
        )
        
        assert issue.title == "Test Issue"
        assert "bounty" in issue.labels
    
    def test_sync_result_success(self):
        """Test SyncResult model."""
        result = SyncResult(
            success=True,
            direction=SyncDirection.GITHUB_TO_PLATFORM,
            event_type=SyncEventType.ISSUE_CREATED,
            github_issue_number=28,
            message="Success",
        )
        
        assert result.success is True
        assert result.timestamp is not None


class TestRetryQueue:
    """Tests for retry queue functionality."""
    
    @pytest.mark.asyncio
    async def test_add_to_retry_queue(self, sync_service, mock_db):
        """Test adding failed sync to retry queue."""
        with patch.object(sync_service, 'update_sync_status'):
            queue_item = await sync_service._add_to_retry_queue(
                direction=SyncDirection.GITHUB_TO_PLATFORM,
                event_type=SyncEventType.ISSUE_CREATED,
                bounty_id=None,
                github_issue_number=28,
                github_repo="SolFoundry/solfoundry",
                payload={},
                error_message="Test error",
            )
        
        assert queue_item.status == SyncStatus.FAILED
        assert queue_item.error_message == "Test error"
        mock_db.add.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_pending_syncs(self, sync_service, mock_db):
        """Test getting pending syncs from queue."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars().all.return_value = []
        mock_db.execute.return_value = mock_result
        
        pending = await sync_service.get_pending_syncs()
        
        assert isinstance(pending, list)


# Run tests with: pytest tests/test_github_sync.py -v