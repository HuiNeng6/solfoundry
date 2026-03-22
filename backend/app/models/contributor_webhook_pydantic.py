"""Pydantic models for contributor webhook API.

Request and response schemas for webhook registration and management.
"""

from datetime import datetime
from typing import Optional, List, Any
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl


class WebhookEventType(str, Enum):
    """Types of webhook events sent to contributors."""

    BOUNTY_CLAIMED = "bounty.claimed"
    REVIEW_STARTED = "review.started"
    REVIEW_PASSED = "review.passed"
    REVIEW_FAILED = "review.failed"
    BOUNTY_PAID = "bounty.paid"


class WebhookRegisterRequest(BaseModel):
    """Request to register a new webhook URL."""

    url: str = Field(
        ...,
        max_length=2048,
        description="Webhook URL to receive notifications",
        examples=["https://example.com/webhooks/bounty"],
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Human-readable description for this webhook",
        examples=["Production webhook for bounty notifications"],
    )

    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL is valid and uses HTTPS in production."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class WebhookUpdateRequest(BaseModel):
    """Request to update an existing webhook."""

    url: Optional[str] = Field(None, max_length=2048)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class WebhookResponse(BaseModel):
    """Webhook registration response."""

    id: str = Field(..., description="Unique webhook ID")
    url: str = Field(..., description="Webhook URL")
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    last_triggered_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    """List of registered webhooks for a user."""

    items: List[WebhookResponse]
    total: int


class WebhookPayload(BaseModel):
    """
    Payload sent to registered webhook URLs.

    All webhook notifications follow this structure.
    """

    event_type: WebhookEventType = Field(
        ...,
        description="Type of event that triggered the webhook",
        examples=[WebhookEventType.BOUNTY_CLAIMED],
    )
    bounty_id: str = Field(
        ...,
        description="UUID of the bounty this event relates to",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    timestamp: datetime = Field(
        ...,
        description="ISO 8601 timestamp when the event occurred",
    )
    data: dict = Field(
        default_factory=dict,
        description="Event-specific data (e.g., bounty title, amount, contributor)",
    )


class WebhookDeliveryStatus(str, Enum):
    """Status of a webhook delivery attempt."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class WebhookDeliveryLogResponse(BaseModel):
    """Webhook delivery log entry."""

    id: str
    webhook_id: str
    event_type: str
    bounty_id: Optional[str] = None
    status: WebhookDeliveryStatus
    attempt_number: int
    response_code: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryListResponse(BaseModel):
    """List of webhook delivery logs."""

    items: List[WebhookDeliveryLogResponse]
    total: int