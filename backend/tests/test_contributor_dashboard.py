"""Tests for the Contributor Dashboard API."""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributor import ContributorDB
from app.models.bounty import BountyDB


@pytest.fixture
async def test_contributor(db: AsyncSession) -> ContributorDB:
    """Create a test contributor."""
    contributor = ContributorDB(
        id=uuid4(),
        username="testuser",
        display_name="Test User",
        email="test@example.com",
        bio="Test bio",
        skills=["python", "typescript"],
        badges=["early-adopter"],
        total_contributions=10,
        total_bounties_completed=5,
        total_earnings=500.0,
        reputation_score=85,
    )
    db.add(contributor)
    await db.commit()
    await db.refresh(contributor)
    return contributor


@pytest.fixture
async def test_bounties(db: AsyncSession, test_contributor: ContributorDB) -> list[BountyDB]:
    """Create test bounties for the contributor."""
    bounties = []
    
    # Completed bounties
    for i in range(3):
        bounty = BountyDB(
            id=uuid4(),
            title=f"Completed Bounty {i+1}",
            description=f"Description for completed bounty {i+1}",
            tier=i % 3 + 1,
            category="backend",
            status="completed",
            reward_amount=100.0 * (i + 1),
            reward_token="FNDRY",
            skills=["python"],
            winner_id=test_contributor.id,
            created_at=datetime.now(timezone.utc) - timedelta(days=30 - i * 5),
            updated_at=datetime.now(timezone.utc) - timedelta(days=i * 5),
        )
        db.add(bounty)
        bounties.append(bounty)
    
    # Claimed bounties
    for i in range(2):
        bounty = BountyDB(
            id=uuid4(),
            title=f"Claimed Bounty {i+1}",
            description=f"Description for claimed bounty {i+1}",
            tier=1,
            category="frontend",
            status="claimed",
            reward_amount=50.0 * (i + 1),
            reward_token="FNDRY",
            skills=["typescript"],
            claimant_id=test_contributor.id,
        )
        db.add(bounty)
        bounties.append(bounty)
    
    await db.commit()
    for b in bounties:
        await db.refresh(b)
    
    return bounties


class TestContributorDashboardAPI:
    """Tests for the contributor dashboard endpoints."""

    @pytest.mark.asyncio
    async def test_get_dashboard_success(
        self, 
        client: AsyncClient, 
        test_contributor: ContributorDB,
        test_bounties: list[BountyDB]
    ):
        """Test successful dashboard data retrieval."""
        response = await client.get(f"/api/dashboard/{test_contributor.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check structure
        assert "summary" in data
        assert "bounty_history" in data
        assert "earnings_chart" in data
        assert "reputation_history" in data
        
        # Check summary
        summary = data["summary"]
        assert summary["contributor_id"] == str(test_contributor.id)
        assert summary["username"] == test_contributor.username
        assert summary["display_name"] == test_contributor.display_name
        
        # Check earnings
        assert summary["earnings"]["total_earned"] == 600.0  # 100 + 200 + 300
        assert summary["earnings"]["total_bounties"] == 3
        
        # Check reputation
        assert summary["reputation"]["current_score"] == test_contributor.reputation_score
        
        # Check active bounties
        assert summary["active_bounties"] == 2

    @pytest.mark.asyncio
    async def test_get_dashboard_invalid_id(self, client: AsyncClient):
        """Test dashboard retrieval with invalid contributor ID."""
        response = await client.get("/api/dashboard/invalid-uuid")
        
        assert response.status_code == 400
        assert "Invalid contributor ID format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_dashboard_not_found(self, client: AsyncClient):
        """Test dashboard retrieval for non-existent contributor."""
        fake_id = str(uuid4())
        response = await client.get(f"/api/dashboard/{fake_id}")
        
        assert response.status_code == 404
        assert "Contributor not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_earnings_success(
        self, 
        client: AsyncClient, 
        test_contributor: ContributorDB,
        test_bounties: list[BountyDB]
    ):
        """Test successful earnings data retrieval."""
        response = await client.get(f"/api/dashboard/{test_contributor.id}/earnings")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_earned"] == 600.0
        assert data["total_bounties"] == 3
        assert data["average_reward"] == 200.0
        assert "FNDRY" in data["by_token"]
        assert data["by_token"]["FNDRY"] == 600.0

    @pytest.mark.asyncio
    async def test_get_reputation_success(
        self, 
        client: AsyncClient, 
        test_contributor: ContributorDB,
        test_bounties: list[BountyDB]
    ):
        """Test successful reputation data retrieval."""
        response = await client.get(f"/api/dashboard/{test_contributor.id}/reputation")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["current_score"] == test_contributor.reputation_score
        assert data["total_changes"] == 3  # 3 completed bounties
        assert len(data["recent_changes"]) > 0

    @pytest.mark.asyncio
    async def test_get_bounty_history_success(
        self, 
        client: AsyncClient, 
        test_contributor: ContributorDB,
        test_bounties: list[BountyDB]
    ):
        """Test successful bounty history retrieval."""
        response = await client.get(f"/api/dashboard/{test_contributor.id}/bounty-history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 5  # 3 completed + 2 claimed
        
        # Check structure of items
        for item in data:
            assert "id" in item
            assert "title" in item
            assert "status" in item
            assert "tier" in item
            assert "reward_amount" in item
            assert "reward_token" in item

    @pytest.mark.asyncio
    async def test_get_bounty_history_with_status_filter(
        self, 
        client: AsyncClient, 
        test_contributor: ContributorDB,
        test_bounties: list[BountyDB]
    ):
        """Test bounty history retrieval with status filter."""
        response = await client.get(
            f"/api/dashboard/{test_contributor.id}/bounty-history?status=completed"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 3  # Only completed bounties
        for item in data:
            assert item["status"] == "completed"

    @pytest.mark.asyncio
    async def test_earnings_chart_data_structure(
        self, 
        client: AsyncClient, 
        test_contributor: ContributorDB,
        test_bounties: list[BountyDB]
    ):
        """Test earnings chart data has correct structure."""
        response = await client.get(f"/api/dashboard/{test_contributor.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "earnings_chart" in data
        assert len(data["earnings_chart"]) == 6  # 6 months of data
        
        for item in data["earnings_chart"]:
            assert "month" in item
            assert "earned" in item
            assert isinstance(item["earned"], (int, float))

    @pytest.mark.asyncio
    async def test_reputation_history_data_structure(
        self, 
        client: AsyncClient, 
        test_contributor: ContributorDB,
        test_bounties: list[BountyDB]
    ):
        """Test reputation history data has correct structure."""
        response = await client.get(f"/api/dashboard/{test_contributor.id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "reputation_history" in data
        assert len(data["reputation_history"]) == 6  # 6 months of data
        
        for item in data["reputation_history"]:
            assert "month" in item
            assert "score" in item
            assert isinstance(item["score"], int)