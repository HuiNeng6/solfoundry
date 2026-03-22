"""Contributor webhook database model.

Stores webhook URLs registered by contributors to receive bounty status notifications.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class ContributorWebhookDB(Base):
    """
    Contributor webhook registration for bounty notifications.

    Contributors can register webhook URLs to receive notifications
    when bounty status changes (claimed, review started, passed, failed, paid).
    """

    __tablename__ = "contributor_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    url = Column(String(2048), nullable=False)
    secret = Column(String(128), nullable=False)  # HMAC secret for signature verification
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_contributor_webhooks_user_active", user_id, is_active),
    )


class WebhookDeliveryLogDB(Base):
    """
    Log of webhook delivery attempts for audit and retry tracking.
    """

    __tablename__ = "webhook_delivery_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    bounty_id = Column(UUID(as_uuid=True), nullable=True)
    payload_hash = Column(String(64), nullable=False)  # SHA256 hash
    status = Column(String(20), nullable=False)  # pending, success, failed, retrying
    attempt_number = Column(String(2), default="1")
    response_code = Column(String(10), nullable=True)
    error_message = Column(String(1024), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )

    __table_args__ = (
        Index("ix_webhook_delivery_logs_status", status),
        Index("ix_webhook_delivery_logs_next_retry", next_retry_at),
    )