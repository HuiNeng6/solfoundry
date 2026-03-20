"""Database configuration and session management.

This module provides database connection pooling and session management
following the Unit of Work pattern. All transaction handling is done
automatically by the session context manager.
"""

import os
import uuid
import logging
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import String, TypeDecorator, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/solfoundry"
)

# Check if we're using SQLite (for testing)
IS_SQLITE = DATABASE_URL.startswith("sqlite")


class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID as PG_UUID
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            elif isinstance(value, int):
                return uuid.UUID(int=value)
            return value


# Connection pool settings
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
POOL_MAX_OVERFLOW = int(os.getenv("DB_POOL_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Create async engine with appropriate settings
if IS_SQLITE:
    engine = create_async_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO", "false").lower() == "true", future=True)
else:
    engine = create_async_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO", "false").lower() == "true", pool_pre_ping=True, pool_size=POOL_SIZE, max_overflow=POOL_MAX_OVERFLOW, pool_timeout=POOL_TIMEOUT)

# Create async session factory
# autocommit=False ensures explicit transaction control
# expire_on_commit=False prevents lazy loading issues after commit
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session.
    
    Implements the Unit of Work pattern:
    - A new session is created for each request
    - The session automatically commits on successful completion
    - Any exception triggers automatic rollback
    - The session is always properly closed
    
    This ensures that database operations are atomic and consistent
    without requiring manual transaction management in the service layer.
    
    Yields:
        AsyncSession: Database session for the current request.
    
    Example:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with async_session_factory() as session:
        try:
            yield session
            # Context manager exit handles commit
        except Exception:
            # Context manager exit handles rollback
            raise


@asynccontextmanager
async def get_db_session():
    """
    Context manager for database sessions outside of FastAPI.
    
    Use this for background tasks, CLI commands, or testing where
    the FastAPI dependency injection is not available.
    
    Yields:
        AsyncSession: A database session with automatic transaction handling.
    
    Example:
        async with get_db_session() as db:
            db.add(new_item)
            # Auto-commits on exit
    """
    async with async_session_factory() as session:
        try:
            yield session
            # Commit happens on successful exit
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Initialize the database schema."""
    logger.info("Initializing database schema...")
    
    async with engine.begin() as conn:
        # Import models to ensure they are registered with Base
        from app.models.bounty import BountyDB  # noqa: F401
        from app.models.contributor import ContributorDB  # noqa: F401
        from app.models.notification import NotificationDB  # noqa: F401
        from app.models.dispute import DisputeDB, DisputeHistoryDB  # noqa: F401
        
        # Create all tables from model definitions
        await conn.run_sync(Base.metadata.create_all)
        
        # PostgreSQL-specific setup
        if not IS_SQLITE:
            try:
                await conn.execute(text("""
                    CREATE OR REPLACE FUNCTION update_bounty_search_vector()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.search_vector := to_tsvector('english', 
                            coalesce(NEW.title, '') || ' ' || 
                            coalesce(NEW.description, '')
                        );
                        RETURN NEW;
                    END;
                    $$ LANGUAGE plpgsql;
                """))
                
                await conn.execute(text("""
                    DROP TRIGGER IF EXISTS bounty_search_vector_update ON bounties;
                    CREATE TRIGGER bounty_search_vector_update
                        BEFORE INSERT OR UPDATE ON bounties
                        FOR EACH ROW
                        EXECUTE FUNCTION update_bounty_search_vector();
                """))
                
                await conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_bounties_search_vector 
                    ON bounties USING GIN(search_vector);
                """))
            except Exception:
                pass  # Ignore errors for existing objects
        
        logger.info("Database schema initialized successfully")


async def close_db() -> None:
    """
    Close all database connections in the pool.
    
    This should be called during application shutdown to ensure
    clean connection closure.
    """
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("Database connections closed")