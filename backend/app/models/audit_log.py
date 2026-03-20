"""Audit log database and Pydantic models.

This module defines the data models for the audit log system.
Audit logs are immutable records of important operations in the system.

Key features:
- Append-only (no updates or deletes allowed)
- Records all critical operations (bounty creation, PR submission, review, payment)
- Filterable by user, operation type, and time range
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, JSON, Text, Index, text
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class AuditAction(str, Enum):
    """Types of audit actions in the system."""
    # Bounty operations
    BOUNTY_CREATED = "bounty_created"
    BOUNTY_UPDATED = "bounty_updated"
    BOUNTY_CLAIMED = "bounty_claimed"
    BOUNTY_UNCLAIMED = "bounty_unclaimed"
    BOUNTY_COMPLETED = "bounty_completed"
    BOUNTY_CANCELLED = "bounty_cancelled"
    
    # PR operations
    PR_SUBMITTED = "pr_submitted"
    PR_APPROVED = "pr_approved"
    PR_REJECTED = "pr_rejected"
    PR_MERGED = "pr_merged"
    
    # Payment operations
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    
    # Review operations
    REVIEW_STARTED = "review_started"
    REVIEW_COMPLETED = "review_completed"
    
    # Dispute operations
    DISPUTE_OPENED = "dispute_opened"
    DISPUTE_RESOLVED = "dispute_resolved"
    
    # User operations
    USER_REGISTERED = "user_registered"
    WALLET_LINKED = "wallet_linked"
    WALLET_VERIFIED = "wallet_verified"
    
    # Admin operations
    ADMIN_OVERRIDDEN = "admin_overridden"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"


class AuditLogDB(Base):
    """
    Audit log database model.
    
    This is an append-only table - records cannot be modified or deleted.
    The immutability is enforced by database triggers.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who performed the action
    actor_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    actor_type = Column(String(50), nullable=False, default="user")  # user, system, admin
    actor_address = Column(String(64), nullable=True)  # Wallet address if applicable
    
    # What action was performed
    action = Column(String(50), nullable=False, index=True)
    
    # What was affected
    resource_type = Column(String(50), nullable=False)  # bounty, pr, payment, user
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Context and details
    description = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)  # Additional structured data
    
    # Request context for traceability
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Related entities
    bounty_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    pr_number = Column(String(50), nullable=True)
    payment_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Timestamp (immutable)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    __table_args__ = (
        Index('ix_audit_logs_actor_action', actor_id, action),
        Index('ix_audit_logs_resource', resource_type, resource_id),
        Index('ix_audit_logs_action_time', action, created_at),
        Index('ix_audit_logs_actor_time', actor_id, created_at),
    )


# Pydantic models

class AuditLogBase(BaseModel):
    """Base fields for audit log."""
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: str
    metadata: Optional[dict] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating an audit log entry."""
    actor_id: Optional[str] = None
    actor_type: str = "user"
    actor_address: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    bounty_id: Optional[str] = None
    pr_number: Optional[str] = None
    payment_id: Optional[str] = None


class AuditLogResponse(AuditLogBase):
    """Full audit log response."""
    id: str
    actor_id: Optional[str] = None
    actor_type: str
    actor_address: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    bounty_id: Optional[str] = None
    pr_number: Optional[str] = None
    payment_id: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class AuditLogListItem(BaseModel):
    """Brief audit log for list views."""
    id: str
    actor_id: Optional[str] = None
    actor_type: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    description: str
    bounty_id: Optional[str] = None
    pr_number: Optional[str] = None
    payment_id: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated audit log list response."""
    items: List[AuditLogListItem]
    total: int
    skip: int
    limit: int


class AuditLogSearchParams(BaseModel):
    """Parameters for audit log search endpoint."""
    actor_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    bounty_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(20, ge=1, le=100)