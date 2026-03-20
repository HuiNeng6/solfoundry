"""Tests for bounty submission workflow."""

import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.bounty import BountyDB, BountyStatus

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session(test_engine):
    async_session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(test_session):
    async def override_get_db():
        yield test_session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_bounty(test_session: AsyncSession):
    bounty = BountyDB(id=uuid.uuid4(), title="Test Bounty", description="A test bounty", tier=1, category="backend", status=BountyStatus.OPEN.value, reward_amount=100.0, reward_token="FNDRY", github_repo="test-owner/test-repo")
    test_session.add(bounty)
    await test_session.commit()
    await test_session.refresh(bounty)
    return bounty


@pytest.fixture
def contributor_id():
    return str(uuid.uuid4())


@pytest.fixture
def test_wallet():
    return "Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7"


class TestSubmissionCreation:
    @pytest.mark.asyncio
    async def test_create_submission_with_pr_url(self, client, contributor_id, test_wallet):
        response = await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": "https://github.com/test-owner/test-repo/pull/123", "contributor_wallet": test_wallet})
        assert response.status_code == 201
        data = response.json()
        assert data["pr_url"] == "https://github.com/test-owner/test-repo/pull/123"
        assert data["contributor_wallet"] == test_wallet
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_create_submission_with_bounty_id(self, client, contributor_id, test_wallet, test_bounty):
        response = await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": "https://github.com/test-owner/test-repo/pull/124", "contributor_wallet": test_wallet, "bounty_id": str(test_bounty.id)})
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "matched"
        assert data["bounty_id"] == str(test_bounty.id)
        assert data["match_confidence"] == "high"

    @pytest.mark.asyncio
    async def test_create_submission_invalid_url(self, client, contributor_id, test_wallet):
        response = await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": "https://not-github.com/something", "contributor_wallet": test_wallet})
        assert response.status_code == 422


class TestSubmissionRetrieval:
    @pytest.mark.asyncio
    async def test_get_submission(self, client, contributor_id, test_wallet):
        create_response = await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": "https://github.com/owner/repo/pull/1", "contributor_wallet": test_wallet})
        submission_id = create_response.json()["id"]
        response = await client.get(f"/api/submissions/{submission_id}")
        assert response.status_code == 200
        assert response.json()["id"] == submission_id

    @pytest.mark.asyncio
    async def test_get_nonexistent_submission(self, client):
        response = await client.get(f"/api/submissions/{str(uuid.uuid4())}")
        assert response.status_code == 404


class TestSubmissionListing:
    @pytest.mark.asyncio
    async def test_list_submissions(self, client, contributor_id, test_wallet):
        for i in range(3):
            await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": f"https://github.com/owner/repo/pull/{i}", "contributor_wallet": test_wallet})
        response = await client.get("/api/submissions/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3


class TestSubmissionStatusUpdate:
    @pytest.mark.asyncio
    async def test_approve_submission(self, client, contributor_id, test_wallet):
        create_response = await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": "https://github.com/owner/repo/pull/1", "contributor_wallet": test_wallet})
        submission_id = create_response.json()["id"]
        reviewer_id = str(uuid.uuid4())
        response = await client.post(f"/api/submissions/{submission_id}/approve", params={"reviewer_id": reviewer_id, "notes": "Great work!"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["review_notes"] == "Great work!"

    @pytest.mark.asyncio
    async def test_reject_submission(self, client, contributor_id, test_wallet):
        create_response = await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": "https://github.com/owner/repo/pull/1", "contributor_wallet": test_wallet})
        submission_id = create_response.json()["id"]
        reviewer_id = str(uuid.uuid4())
        response = await client.post(f"/api/submissions/{submission_id}/reject", params={"reviewer_id": reviewer_id, "reason": "Does not meet requirements"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"


class TestContributorStats:
    @pytest.mark.asyncio
    async def test_get_contributor_stats(self, client, contributor_id, test_wallet):
        for i in range(3):
            await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": f"https://github.com/owner/repo/pull/{i}", "contributor_wallet": test_wallet})
        response = await client.get(f"/api/submissions/contributor/{contributor_id}/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_submissions"] >= 3


class TestAutoMatching:
    @pytest.mark.asyncio
    async def test_auto_match_by_repo(self, client, contributor_id, test_wallet, test_bounty):
        response = await client.post("/api/submissions/", params={"contributor_id": contributor_id}, json={"pr_url": f"https://github.com/{test_bounty.github_repo}/pull/999", "contributor_wallet": test_wallet})
        assert response.status_code == 201
        data = response.json()
        if data.get("bounty_id"):
            assert data["match_confidence"] in ["high", "medium", "low"]
