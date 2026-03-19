"""Tests for bounty search and filter functionality.

Uses PostgreSQL test database to match production environment.
Run with: pytest tests/test_bounty_search.py -v
"""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.main import app
from app.models.bounty import BountyDB, Base
from app.services.bounty_service import BountySearchService
from app.models.bounty import BountySearchParams


# Test database URL (PostgreSQL required for FTS)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/solfoundry_test"
)


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=True)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create a test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    """Create a test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_search_bounties_basic(db_session):
    """Test basic bounty search without filters."""
    
    # Create test bounties
    bounty1 = BountyDB(
        title="Implement search feature",
        description="Add full-text search to the bounty system",
        tier=1,
        category="backend",
        status="open",
        reward_amount=200000.0,
        skills=["python", "fastapi", "postgresql"],
    )
    bounty2 = BountyDB(
        title="Fix login bug",
        description="Fix authentication issue on login page",
        tier=1,
        category="frontend",
        status="open",
        reward_amount=50000.0,
        skills=["javascript", "react"],
    )
    
    db_session.add(bounty1)
    db_session.add(bounty2)
    await db_session.commit()
    
    # Test search
    service = BountySearchService(db_session)
    params = BountySearchParams(skip=0, limit=10)
    result = await service.search_bounties(params)
    
    assert result.total == 2
    assert len(result.items) == 2


@pytest.mark.asyncio
async def test_search_bounties_filter_by_tier(db_session):
    """Test bounty search filtered by tier."""
    
    # Create test bounties with different tiers
    bounty1 = BountyDB(
        title="Tier 1 bounty",
        description="Small task",
        tier=1,
        category="backend",
        status="open",
        reward_amount=50000.0,
    )
    bounty2 = BountyDB(
        title="Tier 2 bounty",
        description="Medium task",
        tier=2,
        category="backend",
        status="open",
        reward_amount=500000.0,
    )
    
    db_session.add(bounty1)
    db_session.add(bounty2)
    await db_session.commit()
    
    # Test filter
    service = BountySearchService(db_session)
    params = BountySearchParams(tier=1, skip=0, limit=10)
    result = await service.search_bounties(params)
    
    assert result.total == 1
    assert result.items[0].tier == 1


@pytest.mark.asyncio
async def test_search_bounties_filter_by_reward_range(db_session):
    """Test bounty search filtered by reward range."""
    
    # Create test bounties
    bounty1 = BountyDB(
        title="Low reward bounty",
        description="Small task",
        tier=1,
        category="backend",
        status="open",
        reward_amount=50000.0,
    )
    bounty2 = BountyDB(
        title="High reward bounty",
        description="Large task",
        tier=2,
        category="backend",
        status="open",
        reward_amount=500000.0,
    )
    
    db_session.add(bounty1)
    db_session.add(bounty2)
    await db_session.commit()
    
    # Test filter
    service = BountySearchService(db_session)
    params = BountySearchParams(reward_min=100000.0, reward_max=600000.0, skip=0, limit=10)
    result = await service.search_bounties(params)
    
    assert result.total == 1
    assert result.items[0].reward_amount == 500000.0


@pytest.mark.asyncio
async def test_search_bounties_sort_by_reward(db_session):
    """Test bounty search sorted by reward."""
    
    # Create test bounties
    bounty1 = BountyDB(
        title="Low reward",
        description="Small task",
        tier=1,
        category="backend",
        status="open",
        reward_amount=50000.0,
    )
    bounty2 = BountyDB(
        title="High reward",
        description="Large task",
        tier=1,
        category="backend",
        status="open",
        reward_amount=500000.0,
    )
    
    db_session.add(bounty1)
    db_session.add(bounty2)
    await db_session.commit()
    
    # Test sort high to low
    service = BountySearchService(db_session)
    params = BountySearchParams(sort="reward_high", skip=0, limit=10)
    result = await service.search_bounties(params)
    
    assert result.items[0].reward_amount >= result.items[1].reward_amount


@pytest.mark.asyncio
async def test_pagination(db_session):
    """Test pagination of search results."""
    
    # Create multiple bounties
    for i in range(25):
        bounty = BountyDB(
            title=f"Bounty {i}",
            description=f"Description {i}",
            tier=1,
            category="backend",
            status="open",
            reward_amount=100000.0 * (i + 1),
        )
        db_session.add(bounty)
    
    await db_session.commit()
    
    # Test pagination
    service = BountySearchService(db_session)
    
    # First page
    params1 = BountySearchParams(skip=0, limit=10)
    result1 = await service.search_bounties(params1)
    assert len(result1.items) == 10
    assert result1.skip == 0
    
    # Second page
    params2 = BountySearchParams(skip=10, limit=10)
    result2 = await service.search_bounties(params2)
    assert len(result2.items) == 10
    assert result2.skip == 10


@pytest.mark.asyncio
async def test_filter_combinations(db_session):
    """Test various filter combinations."""
    
    # Create test bounties
    bounties = [
        BountyDB(title="Python Backend", description="Backend task", tier=1, category="backend", status="open", reward_amount=100000.0, skills=["python"]),
        BountyDB(title="React Frontend", description="Frontend task", tier=1, category="frontend", status="open", reward_amount=100000.0, skills=["react"]),
        BountyDB(title="Smart Contract", description="Contract task", tier=2, category="smart_contract", status="open", reward_amount=300000.0, skills=["rust"]),
        BountyDB(title="Completed Task", description="Done", tier=1, category="backend", status="completed", reward_amount=50000.0, skills=["python"]),
    ]
    
    for b in bounties:
        db_session.add(b)
    await db_session.commit()
    
    service = BountySearchService(db_session)
    
    # Test: tier + category
    params = BountySearchParams(tier=1, category="backend", skip=0, limit=10)
    result = await service.search_bounties(params)
    assert result.total == 1  # Only "Python Backend" (open)
    
    # Test: status filter
    params = BountySearchParams(status="completed", skip=0, limit=10)
    result = await service.search_bounties(params)
    assert result.total == 1