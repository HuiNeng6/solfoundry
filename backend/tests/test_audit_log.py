"""API endpoint tests for audit log functionality.

Tests the audit log API endpoints with PostgreSQL test database.
Run with: pytest tests/test_audit_log.py -v
"""

import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, timedelta, timezone

from app.main import app
from app.models.audit_log import AuditLogDB, Base, AuditAction
from app.database import get_db


# Test database URL (PostgreSQL required)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/solfoundry_test"
)


@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        
        # Create audit log immutability trigger
        from sqlalchemy import text
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION enforce_audit_log_immutability()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'Audit logs are immutable and cannot be modified or deleted';
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
        """))
        
        await conn.execute(text("""
            DROP TRIGGER IF EXISTS prevent_audit_log_update ON audit_logs;
            CREATE TRIGGER prevent_audit_log_update
                BEFORE UPDATE ON audit_logs
                FOR EACH ROW
                EXECUTE FUNCTION enforce_audit_log_immutability();
        """))
        
        await conn.execute(text("""
            DROP TRIGGER IF EXISTS prevent_audit_log_delete ON audit_logs;
            CREATE TRIGGER prevent_audit_log_delete
                BEFORE DELETE ON audit_logs
                FOR EACH ROW
                EXECUTE FUNCTION enforce_audit_log_immutability();
        """))
    
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
async def client(db_session):
    """Create a test client with database dependency override."""
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_audit_logs(db_session):
    """Create sample audit logs for testing."""
    now = datetime.now(timezone.utc)
    
    logs = [
        AuditLogDB(
            actor_id="00000000-0000-0000-0000-000000000001",
            actor_type="user",
            actor_address="Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7",
            action=AuditAction.BOUNTY_CREATED.value,
            resource_type="bounty",
            resource_id="00000000-0000-0000-0000-000000000010",
            description="Bounty #10 created: Implement search feature",
            bounty_id="00000000-0000-0000-0000-000000000010",
            created_at=now - timedelta(hours=3),
        ),
        AuditLogDB(
            actor_id="00000000-0000-0000-0000-000000000002",
            actor_type="user",
            action=AuditAction.BOUNTY_CLAIMED.value,
            resource_type="bounty",
            resource_id="00000000-0000-0000-0000-000000000010",
            description="Bounty #10 claimed by user",
            bounty_id="00000000-0000-0000-0000-000000000010",
            created_at=now - timedelta(hours=2),
        ),
        AuditLogDB(
            actor_id="00000000-0000-0000-0000-000000000002",
            actor_type="user",
            action=AuditAction.PR_SUBMITTED.value,
            resource_type="pr",
            description="PR #42 submitted for bounty #10",
            bounty_id="00000000-0000-0000-0000-000000000010",
            pr_number="42",
            created_at=now - timedelta(hours=1),
        ),
        AuditLogDB(
            actor_id="00000000-0000-0000-0000-000000000003",
            actor_type="admin",
            action=AuditAction.PR_APPROVED.value,
            resource_type="pr",
            description="PR #42 approved by admin",
            bounty_id="00000000-0000-0000-0000-000000000010",
            pr_number="42",
            created_at=now - timedelta(minutes=30),
        ),
        AuditLogDB(
            actor_id="00000000-0000-0000-0000-000000000001",
            actor_type="system",
            action=AuditAction.PAYMENT_COMPLETED.value,
            resource_type="payment",
            resource_id="00000000-0000-0000-0000-000000000099",
            description="Payment of 200000 FNDRY completed for bounty #10",
            bounty_id="00000000-0000-0000-0000-000000000010",
            payment_id="00000000-0000-0000-0000-000000000099",
            created_at=now - timedelta(minutes=15),
        ),
    ]
    
    for log in logs:
        db_session.add(log)
    await db_session.commit()
    
    return logs


class TestAuditLogSearchAPI:
    """Tests for audit log search API endpoints."""
    
    @pytest.mark.asyncio
    async def test_search_audit_logs_default(self, client, sample_audit_logs):
        """Test default search returns all logs."""
        response = await client.get("/api/audit-logs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert data["total"] == 5
        
    @pytest.mark.asyncio
    async def test_search_audit_logs_by_actor(self, client, sample_audit_logs):
        """Test filter by actor_id."""
        response = await client.get(
            "/api/audit-logs?actor_id=00000000-0000-0000-0000-000000000002"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 2
        for item in data["items"]:
            assert item["actor_id"] == "00000000-0000-0000-0000-000000000002"
            
    @pytest.mark.asyncio
    async def test_search_audit_logs_by_action(self, client, sample_audit_logs):
        """Test filter by action type."""
        response = await client.get("/api/audit-logs?action=bounty_created")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 1
        assert data["items"][0]["action"] == "bounty_created"
        
    @pytest.mark.asyncio
    async def test_search_audit_logs_by_resource_type(self, client, sample_audit_logs):
        """Test filter by resource type."""
        response = await client.get("/api/audit-logs?resource_type=pr")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 2
        for item in data["items"]:
            assert item["resource_type"] == "pr"
            
    @pytest.mark.asyncio
    async def test_search_audit_logs_by_bounty(self, client, sample_audit_logs):
        """Test filter by bounty_id."""
        response = await client.get(
            "/api/audit-logs?bounty_id=00000000-0000-0000-0000-000000000010"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 5
        for item in data["items"]:
            assert item["bounty_id"] == "00000000-0000-0000-0000-000000000010"
            
    @pytest.mark.asyncio
    async def test_search_audit_logs_by_time_range(self, client, sample_audit_logs):
        """Test filter by time range."""
        now = datetime.now(timezone.utc)
        start = (now - timedelta(hours=2)).isoformat()
        end = (now - timedelta(minutes=20)).isoformat()
        
        response = await client.get(f"/api/audit-logs?start_time={start}&end_time={end}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should include logs from 2 hours ago to 20 minutes ago
        assert data["total"] >= 2
        
    @pytest.mark.asyncio
    async def test_search_audit_logs_pagination(self, client, sample_audit_logs):
        """Test pagination."""
        response = await client.get("/api/audit-logs?skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["items"]) == 2
        assert data["skip"] == 0
        assert data["limit"] == 2
        
    @pytest.mark.asyncio
    async def test_search_audit_logs_invalid_action(self, client, sample_audit_logs):
        """Test with invalid action value."""
        response = await client.get("/api/audit-logs?action=invalid_action")
        
        assert response.status_code == 400
        
    @pytest.mark.asyncio
    async def test_search_audit_logs_invalid_resource_type(self, client, sample_audit_logs):
        """Test with invalid resource_type value."""
        response = await client.get("/api/audit-logs?resource_type=invalid_type")
        
        assert response.status_code == 400


class TestAuditLogGetAPI:
    """Tests for single audit log retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_audit_log(self, client, sample_audit_logs):
        """Test get single audit log."""
        log_id = sample_audit_logs[0].id
        
        response = await client.get(f"/api/audit-logs/{log_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == str(log_id)
        assert "action" in data
        assert "description" in data
        
    @pytest.mark.asyncio
    async def test_get_audit_log_not_found(self, client):
        """Test get audit log with invalid ID."""
        response = await client.get("/api/audit-logs/00000000-0000-0000-0000-000000000000")
        
        assert response.status_code == 404


class TestAuditLogBountyAPI:
    """Tests for bounty audit log endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_bounty_audit_logs(self, client, sample_audit_logs):
        """Test get all logs for a bounty."""
        response = await client.get(
            "/api/audit-logs/bounty/00000000-0000-0000-0000-000000000010"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 5
        for item in data["items"]:
            assert item["bounty_id"] == "00000000-0000-0000-0000-000000000010"


class TestAuditLogActorAPI:
    """Tests for actor audit log endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_actor_audit_logs(self, client, sample_audit_logs):
        """Test get all logs for an actor."""
        response = await client.get(
            "/api/audit-logs/actor/00000000-0000-0000-0000-000000000002"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 2


class TestAuditLogSummaryAPI:
    """Tests for audit log summary endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_audit_summary(self, client, sample_audit_logs):
        """Test get action summary."""
        response = await client.get("/api/audit-logs/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "summary" in data
        assert data["summary"]["bounty_created"] == 1
        assert data["summary"]["bounty_claimed"] == 1


class TestAuditLogActionsAPI:
    """Tests for valid actions endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_valid_actions(self, client):
        """Test list all valid actions."""
        response = await client.get("/api/audit-logs/actions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "actions" in data
        assert "bounty_created" in data["actions"]
        assert "categories" in data


class TestAuditLogImmutability:
    """Tests for audit log immutability (database level)."""
    
    @pytest.mark.asyncio
    async def test_cannot_update_audit_log(self, db_session, sample_audit_logs):
        """Test that audit logs cannot be updated."""
        from sqlalchemy import text
        
        log = sample_audit_logs[0]
        
        # Try to update the log
        with pytest.raises(Exception) as exc_info:
            await db_session.execute(
                text(f"UPDATE audit_logs SET description = 'modified' WHERE id = '{log.id}'")
            )
            await db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()
        
    @pytest.mark.asyncio
    async def test_cannot_delete_audit_log(self, db_session, sample_audit_logs):
        """Test that audit logs cannot be deleted."""
        from sqlalchemy import text
        
        log = sample_audit_logs[0]
        
        # Try to delete the log
        with pytest.raises(Exception) as exc_info:
            await db_session.execute(
                text(f"DELETE FROM audit_logs WHERE id = '{log.id}'")
            )
            await db_session.commit()
        
        assert "immutable" in str(exc_info.value).lower()


class TestAuditLogService:
    """Tests for audit log service layer."""
    
    @pytest.mark.asyncio
    async def test_create_audit_log(self, db_session):
        """Test creating an audit log entry."""
        from app.services.audit_log_service import AuditLogService
        from app.models.audit_log import AuditLogCreate
        
        service = AuditLogService(db_session)
        
        data = AuditLogCreate(
            action="bounty_created",
            resource_type="bounty",
            description="Test bounty creation",
            actor_id="00000000-0000-0000-0000-000000000001",
        )
        
        log = await service.create_log(data)
        
        assert log.id is not None
        assert log.action == "bounty_created"
        
    @pytest.mark.asyncio
    async def test_create_audit_log_invalid_action(self, db_session):
        """Test creating with invalid action raises error."""
        from app.services.audit_log_service import AuditLogService
        from app.models.audit_log import AuditLogCreate
        
        service = AuditLogService(db_session)
        
        data = AuditLogCreate(
            action="invalid_action",
            resource_type="bounty",
            description="Test",
        )
        
        with pytest.raises(ValueError) as exc_info:
            await service.create_log(data)
        
        assert "Invalid action" in str(exc_info.value)
        
    @pytest.mark.asyncio
    async def test_create_audit_log_invalid_resource_type(self, db_session):
        """Test creating with invalid resource_type raises error."""
        from app.services.audit_log_service import AuditLogService
        from app.models.audit_log import AuditLogCreate
        
        service = AuditLogService(db_session)
        
        data = AuditLogCreate(
            action="bounty_created",
            resource_type="invalid_type",
            description="Test",
        )
        
        with pytest.raises(ValueError) as exc_info:
            await service.create_log(data)
        
        assert "Invalid resource_type" in str(exc_info.value)