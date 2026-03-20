"""Audit log API endpoints.

This module provides the REST API for querying audit logs.
Audit logs are append-only and cannot be modified or deleted via API.

Endpoints:
- GET /api/audit-logs - Search audit logs with filters
- GET /api/audit-logs/{log_id} - Get single audit log
- GET /api/audit-logs/bounty/{bounty_id} - Get logs for a bounty
- GET /api/audit-logs/actor/{actor_id} - Get logs for an actor
- GET /api/audit-logs/summary - Get action summary
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
    AuditAction,
)
from app.services.audit_log_service import AuditLogService
from app.database import get_db

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


@router.get("", response_model=AuditLogListResponse)
async def search_audit_logs(
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    action: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (bounty, pr, payment, user)"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    bounty_id: Optional[str] = Query(None, description="Filter by bounty ID"),
    start_time: Optional[datetime] = Query(None, description="Filter logs after this time (ISO 8601)"),
    end_time: Optional[datetime] = Query(None, description="Filter logs before this time (ISO 8601)"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    db: AsyncSession = Depends(get_db),
):
    """
    Search audit logs with comprehensive filtering.
    
    - **actor_id**: Filter by the user who performed the action
    - **action**: Filter by action type (see AuditAction enum)
    - **resource_type**: Filter by resource type (bounty, pr, payment, user, dispute, system)
    - **resource_id**: Filter by specific resource ID
    - **bounty_id**: Filter by related bounty ID
    - **start_time**: Filter logs created after this timestamp
    - **end_time**: Filter logs created before this timestamp
    - **skip**: Pagination offset
    - **limit**: Number of results per page (max 100)
    
    Returns paginated results ordered by creation time (newest first).
    """
    from app.models.audit_log import AuditLogSearchParams
    
    # Validate action if provided
    if action and action not in AuditLogService.VALID_ACTIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {action}. Valid actions: {sorted(AuditLogService.VALID_ACTIONS)}"
        )
    
    # Validate resource_type if provided
    if resource_type and resource_type not in AuditLogService.VALID_RESOURCE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resource_type: {resource_type}. Valid types: {AuditLogService.VALID_RESOURCE_TYPES}"
        )
    
    params = AuditLogSearchParams(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        bounty_id=bounty_id,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )
    
    service = AuditLogService(db)
    return await service.search_logs(params)


@router.get("/summary")
async def get_audit_summary(
    start_time: Optional[datetime] = Query(None, description="Start time for summary"),
    end_time: Optional[datetime] = Query(None, description="End time for summary"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a summary of audit actions by type.
    
    Returns counts of each action type within the specified time range.
    Useful for dashboards and analytics.
    """
    service = AuditLogService(db)
    summary = await service.get_action_summary(start_time, end_time)
    
    return {
        "summary": summary,
        "start_time": start_time,
        "end_time": end_time,
    }


@router.get("/actions")
async def list_valid_actions():
    """
    List all valid audit action types.
    
    Returns the complete list of valid action values for filtering.
    """
    return {
        "actions": sorted([a.value for a in AuditAction]),
        "categories": {
            "bounty": ["bounty_created", "bounty_updated", "bounty_claimed", "bounty_unclaimed", "bounty_completed", "bounty_cancelled"],
            "pr": ["pr_submitted", "pr_approved", "pr_rejected", "pr_merged"],
            "payment": ["payment_initiated", "payment_completed", "payment_failed"],
            "review": ["review_started", "review_completed"],
            "dispute": ["dispute_opened", "dispute_resolved"],
            "user": ["user_registered", "wallet_linked", "wallet_verified"],
            "admin": ["admin_overridden", "system_config_changed"],
        }
    }


@router.get("/resource-types")
async def list_valid_resource_types():
    """
    List all valid resource types.
    
    Returns the complete list of valid resource_type values for filtering.
    """
    return {
        "resource_types": list(AuditLogService.VALID_RESOURCE_TYPES),
    }


@router.get("/bounty/{bounty_id}", response_model=AuditLogListResponse)
async def get_bounty_audit_logs(
    bounty_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all audit logs for a specific bounty.
    
    Returns the complete audit trail for a bounty, including:
    - Creation
    - Claims
    - PR submissions
    - Reviews
    - Payments
    """
    service = AuditLogService(db)
    return await service.get_logs_by_bounty(bounty_id, skip, limit)


@router.get("/actor/{actor_id}", response_model=AuditLogListResponse)
async def get_actor_audit_logs(
    actor_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all audit logs for a specific actor.
    
    Returns all actions performed by a specific user.
    Useful for user activity tracking and compliance.
    """
    service = AuditLogService(db)
    return await service.get_logs_by_actor(actor_id, skip, limit)


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single audit log by ID.
    
    Returns the complete audit log entry with all details.
    """
    service = AuditLogService(db)
    log = await service.get_log_by_id(log_id)
    
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")
    
    return AuditLogResponse.model_validate(log)