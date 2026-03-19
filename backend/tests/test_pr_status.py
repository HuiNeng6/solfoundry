"""Tests for PR Status API and service."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.models.pr_status import (
    PRStage,
    StageStatus,
    PRStatusCreate,
    PRStatusResponse,
    AIReviewScore
)
from app.services.pr_status_service import PRStatusService


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_pr_status_create():
    """Sample PR status creation data."""
    return PRStatusCreate(
        pr_number=123,
        pr_title="Test PR",
        pr_url="https://github.com/test/repo/pull/123",
        author="testuser",
        bounty_id="bounty-001",
        bounty_title="Test Bounty"
    )


@pytest.fixture
def sample_ai_review_scores():
    """Sample AI review scores."""
    return AIReviewScore(
        quality=8.5,
        correctness=9.0,
        security=7.5,
        completeness=8.0,
        tests=9.5,
        overall=8.5
    )


class TestPRStatusService:
    """Tests for PR Status Service."""

    @pytest.mark.asyncio
    async def test_create_pr_status(self, mock_db, sample_pr_status_create):
        """Test creating a new PR status."""
        # Mock that PR doesn't exist yet
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await PRStatusService.create(mock_db, sample_pr_status_create)

        assert mock_db.add.called
        assert mock_db.commit.called
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_pr_status(self, mock_db, sample_pr_status_create):
        """Test creating a duplicate PR status raises error."""
        # Mock that PR already exists
        mock_db.execute.return_value.scalar_one_or_none.return_value = AsyncMock()

        with pytest.raises(ValueError) as exc_info:
            await PRStatusService.create(mock_db, sample_pr_status_create)

        assert "already has a status entry" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_pr_status_not_found(self, mock_db):
        """Test getting a non-existent PR status."""
        mock_db.execute.return_value.scalar_one_or_none.return_value = None

        result = await PRStatusService.get(mock_db, 999)

        assert result is None

    @pytest.mark.asyncio
    async def test_update_stage_ci_running_to_passed(self, mock_db):
        """Test updating CI running stage to passed."""
        # Mock existing PR status
        mock_entry = AsyncMock()
        mock_entry.pr_number = 123
        mock_entry.current_stage = PRStage.CI_RUNNING
        mock_entry.stages_data = {
            PRStage.CI_RUNNING.value: {
                "status": StageStatus.RUNNING.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_entry

        result = await PRStatusService.update_stage(
            mock_db,
            123,
            PRStage.CI_RUNNING,
            StageStatus.PASSED
        )

        assert mock_db.commit.called

    @pytest.mark.asyncio
    async def test_update_ai_review_with_scores(self, mock_db, sample_ai_review_scores):
        """Test updating AI review with score breakdown."""
        mock_entry = AsyncMock()
        mock_entry.pr_number = 123
        mock_entry.current_stage = PRStage.AI_REVIEW
        mock_entry.stages_data = {
            PRStage.AI_REVIEW.value: {
                "status": StageStatus.RUNNING.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        mock_db.execute.return_value.scalar_one_or_none.return_value = mock_entry

        result = await PRStatusService.update_stage(
            mock_db,
            123,
            PRStage.AI_REVIEW,
            StageStatus.PASSED,
            details={"scores": sample_ai_review_scores.model_dump()}
        )

        assert mock_db.commit.called


class TestPRStageEnum:
    """Tests for PR Stage enum."""

    def test_stage_values(self):
        """Test that all expected stages exist."""
        expected_stages = [
            "submitted",
            "ci_running",
            "ai_review",
            "human_review",
            "approved",
            "denied",
            "payout"
        ]

        for stage in expected_stages:
            assert hasattr(PRStage, stage.upper())

    def test_stage_order(self):
        """Test that stages are in expected order."""
        expected_order = [
            PRStage.SUBMITTED,
            PRStage.CI_RUNNING,
            PRStage.AI_REVIEW,
            PRStage.HUMAN_REVIEW,
            PRStage.APPROVED,
            PRStage.PAYOUT
        ]

        assert len(PRStage) == 7  # Including DENIED


class TestStageStatusEnum:
    """Tests for Stage Status enum."""

    def test_status_values(self):
        """Test that all expected statuses exist."""
        expected_statuses = [
            "pending",
            "running",
            "passed",
            "failed",
            "skipped"
        ]

        for status in expected_statuses:
            assert hasattr(StageStatus, status.upper())


class TestAIReviewScore:
    """Tests for AI Review Score model."""

    def test_valid_scores(self):
        """Test creating valid AI review scores."""
        scores = AIReviewScore(
            quality=8.5,
            correctness=9.0,
            security=7.5,
            completeness=8.0,
            tests=9.5,
            overall=8.5
        )

        assert scores.quality == 8.5
        assert scores.overall == 8.5

    def test_score_boundaries(self):
        """Test that scores must be between 0 and 10."""
        # Valid scores
        AIReviewScore(
            quality=0,
            correctness=10,
            security=5.5,
            completeness=7.3,
            tests=8.2,
            overall=6.2
        )

        # Invalid score (too high)
        with pytest.raises(ValueError):
            AIReviewScore(
                quality=11,
                correctness=5,
                security=5,
                completeness=5,
                tests=5,
                overall=5
            )

        # Invalid score (too low)
        with pytest.raises(ValueError):
            AIReviewScore(
                quality=-1,
                correctness=5,
                security=5,
                completeness=5,
                tests=5,
                overall=5
            )


class TestPRStatusCreate:
    """Tests for PR Status Create model."""

    def test_valid_creation(self):
        """Test creating valid PR status."""
        data = PRStatusCreate(
            pr_number=123,
            pr_title="Test PR",
            pr_url="https://github.com/test/repo/pull/123",
            author="testuser",
            bounty_id="bounty-001",
            bounty_title="Test Bounty"
        )

        assert data.pr_number == 123
        assert data.author == "testuser"

    def test_minimal_creation(self):
        """Test creating PR status with minimal fields."""
        data = PRStatusCreate(
            pr_number=456,
            pr_title="Minimal PR",
            pr_url="https://github.com/test/repo/pull/456",
            author="minimaluser"
        )

        assert data.bounty_id is None
        assert data.bounty_title is None

    def test_invalid_pr_number(self):
        """Test that invalid PR numbers are rejected."""
        with pytest.raises(ValueError):
            PRStatusCreate(
                pr_number=0,  # Must be > 0
                pr_title="Test",
                pr_url="https://github.com/test/repo/pull/0",
                author="testuser"
            )

        with pytest.raises(ValueError):
            PRStatusCreate(
                pr_number=-1,  # Must be > 0
                pr_title="Test",
                pr_url="https://github.com/test/repo/pull/-1",
                author="testuser"
            )