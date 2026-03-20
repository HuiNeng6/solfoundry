"""Audit log service for managing audit records.

This module provides the business logic for audit log operations.
Audit logs are append-only and cannot be modified or deleted.

Key features:
- Immutable records (enforced at database level)
- Comprehensive filtering
- Automatic context capture
"""

from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import (
    AuditLogDB,
    AuditLogCreate,
    AuditLogListResponse,
    AuditLogListItem,
    AuditLogSearchParams,
    AuditAction,
)


class AuditLogService:
    """Service for audit log operations."""
    
    # Valid filter values
    VALID_ACTIONS = {a.value for a in AuditAction}
    VALID_RESOURCE_TYPES = {"bounty", "pr", "payment", "user", "dispute", "system"}
    VALID_ACTOR_TYPES = {"user", "system", "admin"}
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_log(self, data: AuditLogCreate) -> AuditLogDB:
        """
        Create an immutable audit log entry.
        
        Args:
            data: Audit log creation data.
            
        Returns:
            The created audit log entry.
            
        Raises:
            ValueError: If action or resource_type is invalid.
        """
        # Validate action
        if data.action not in self.VALID_ACTIONS:
            raise ValueError(
                f"Invalid action: {data.action}. "
                f"Must be one of: {sorted(self.VALID_ACTIONS)}"
            )
        
        # Validate resource_type
        if data.resource_type not in self.VALID_RESOURCE_TYPES:
            raise ValueError(
                f"Invalid resource_type: {data.resource_type}. "
                f"Must be one of: {self.VALID_RESOURCE_TYPES}"
            )
        
        # Validate actor_type
        if data.actor_type not in self.VALID_ACTOR_TYPES:
            raise ValueError(
                f"Invalid actor_type: {data.actor_type}. "
                f"Must be one of: {self.VALID_ACTOR_TYPES}"
            )
        
        # Create the log entry
        log_entry = AuditLogDB(
            actor_id=data.actor_id,
            actor_type=data.actor_type,
            actor_address=data.actor_address,
            action=data.action,
            resource_type=data.resource_type,
            resource_id=data.resource_id,
            description=data.description,
            metadata=data.metadata,
            ip_address=data.ip_address,
            user_agent=data.user_agent,
            request_id=data.request_id,
            bounty_id=data.bounty_id,
            pr_number=data.pr_number,
            payment_id=data.payment_id,
        )
        
        self.db.add(log_entry)
        # Session will auto-commit on exit
        
        return log_entry
    
    async def get_log_by_id(self, log_id: str) -> Optional[AuditLogDB]:
        """
        Get a single audit log by ID.
        
        Args:
            log_id: The audit log ID to retrieve.
            
        Returns:
            The audit log if found, None otherwise.
        """
        query = select(AuditLogDB).where(AuditLogDB.id == log_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_logs(self, params: AuditLogSearchParams) -> AuditLogListResponse:
        """
        Search audit logs with filtering and pagination.
        
        Args:
            params: Search parameters including filters and pagination.
            
        Returns:
            AuditLogListResponse with matching logs and total count.
        """
        # Build filter conditions
        conditions = self._build_conditions(params)
        filter_condition = and_(*conditions) if conditions else True
        
        # Count query
        count_query = select(func.count(AuditLogDB.id)).where(filter_condition)
        
        # Main query
        query = (
            select(AuditLogDB)
            .where(filter_condition)
            .order_by(desc(AuditLogDB.created_at))
            .offset(params.skip)
            .limit(params.limit)
        )
        
        # Execute queries
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar() or 0
        
        return AuditLogListResponse(
            items=[AuditLogListItem.model_validate(log) for log in logs],
            total=total,
            skip=params.skip,
            limit=params.limit,
        )
    
    async def get_logs_by_actor(
        self,
        actor_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> AuditLogListResponse:
        """
        Get audit logs for a specific actor.
        
        Args:
            actor_id: The actor ID to filter by.
            skip: Pagination offset.
            limit: Number of results per page.
            
        Returns:
            AuditLogListResponse with matching logs.
        """
        params = AuditLogSearchParams(actor_id=actor_id, skip=skip, limit=limit)
        return await self.search_logs(params)
    
    async def get_logs_by_bounty(
        self,
        bounty_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> AuditLogListResponse:
        """
        Get audit logs for a specific bounty.
        
        Args:
            bounty_id: The bounty ID to filter by.
            skip: Pagination offset.
            limit: Number of results per page.
            
        Returns:
            AuditLogListResponse with matching logs.
        """
        params = AuditLogSearchParams(bounty_id=bounty_id, skip=skip, limit=limit)
        return await self.search_logs(params)
    
    async def get_logs_by_action(
        self,
        action: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> AuditLogListResponse:
        """
        Get audit logs for a specific action type.
        
        Args:
            action: The action type to filter by.
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            skip: Pagination offset.
            limit: Number of results per page.
            
        Returns:
            AuditLogListResponse with matching logs.
        """
        params = AuditLogSearchParams(
            action=action,
            start_time=start_time,
            end_time=end_time,
            skip=skip,
            limit=limit,
        )
        return await self.search_logs(params)
    
    async def get_logs_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime,
        skip: int = 0,
        limit: int = 20,
    ) -> AuditLogListResponse:
        """
        Get audit logs within a time range.
        
        Args:
            start_time: Start of the time range.
            end_time: End of the time range.
            skip: Pagination offset.
            limit: Number of results per page.
            
        Returns:
            AuditLogListResponse with matching logs.
        """
        params = AuditLogSearchParams(
            start_time=start_time,
            end_time=end_time,
            skip=skip,
            limit=limit,
        )
        return await self.search_logs(params)
    
    async def get_action_summary(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        """
        Get a summary of actions by type.
        
        Args:
            start_time: Optional start time filter.
            end_time: Optional end time filter.
            
        Returns:
            Dictionary with action counts.
        """
        conditions = []
        
        if start_time:
            conditions.append(AuditLogDB.created_at >= start_time)
        
        if end_time:
            conditions.append(AuditLogDB.created_at <= end_time)
        
        filter_condition = and_(*conditions) if conditions else True
        
        query = (
            select(AuditLogDB.action, func.count(AuditLogDB.id).label("count"))
            .where(filter_condition)
            .group_by(AuditLogDB.action)
            .order_by(desc("count"))
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return {row.action: row.count for row in rows}
    
    def _build_conditions(self, params: AuditLogSearchParams) -> List:
        """Build filter conditions from parameters."""
        conditions = []
        
        if params.actor_id:
            conditions.append(AuditLogDB.actor_id == params.actor_id)
        
        if params.action:
            conditions.append(AuditLogDB.action == params.action)
        
        if params.resource_type:
            conditions.append(AuditLogDB.resource_type == params.resource_type)
        
        if params.resource_id:
            conditions.append(AuditLogDB.resource_id == params.resource_id)
        
        if params.bounty_id:
            conditions.append(AuditLogDB.bounty_id == params.bounty_id)
        
        if params.start_time:
            conditions.append(AuditLogDB.created_at >= params.start_time)
        
        if params.end_time:
            conditions.append(AuditLogDB.created_at <= params.end_time)
        
        return conditions


# Helper function for creating audit logs from request context
def create_audit_log_from_request(
    action: str,
    resource_type: str,
    description: str,
    request,  # FastAPI Request object
    actor_id: Optional[str] = None,
    actor_type: str = "user",
    actor_address: Optional[str] = None,
    resource_id: Optional[str] = None,
    bounty_id: Optional[str] = None,
    pr_number: Optional[str] = None,
    payment_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> AuditLogCreate:
    """
    Create an AuditLogCreate object with request context.
    
    This helper extracts IP address, user agent, and request ID
    from the FastAPI request object.
    
    Args:
        action: The action being logged.
        resource_type: Type of resource being acted upon.
        description: Human-readable description.
        request: FastAPI Request object.
        actor_id: ID of the user performing the action.
        actor_type: Type of actor (user, system, admin).
        actor_address: Wallet address if applicable.
        resource_id: ID of the resource being acted upon.
        bounty_id: Related bounty ID.
        pr_number: Related PR number.
        payment_id: Related payment ID.
        metadata: Additional structured data.
        
    Returns:
        AuditLogCreate object ready for insertion.
    """
    # Extract request context
    ip_address = None
    user_agent = None
    request_id = None
    
    if request:
        # Get client IP (handle proxies)
        if "x-forwarded-for" in request.headers:
            ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()
        elif request.client:
            ip_address = request.client.host
        
        user_agent = request.headers.get("user-agent", "")[:500]
        request_id = request.headers.get("x-request-id")
    
    return AuditLogCreate(
        action=action,
        resource_type=resource_type,
        description=description,
        actor_id=actor_id,
        actor_type=actor_type,
        actor_address=actor_address,
        resource_id=resource_id,
        bounty_id=bounty_id,
        pr_number=pr_number,
        payment_id=payment_id,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
        request_id=request_id,
    )