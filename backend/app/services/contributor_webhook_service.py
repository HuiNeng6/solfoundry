"""Contributor webhook notification service.

Handles webhook registration, notification dispatch, retry logic with exponential backoff,
and HMAC-SHA256 signature verification.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contributor_webhook import (
    ContributorWebhookDB,
    WebhookDeliveryLogDB,
)
from app.models.contributor_webhook_pydantic import (
    WebhookEventType,
    WebhookPayload,
    WebhookDeliveryStatus,
)

logger = logging.getLogger(__name__)

# Configuration constants
MAX_WEBHOOKS_PER_USER = 10
MAX_RETRY_ATTEMPTS = 3
RETRY_DELAYS = [1, 5, 30]  # Exponential backoff: 1s, 5s, 30s
WEBHOOK_TIMEOUT_SECONDS = 10


class WebhookError(Exception):
    """Base exception for webhook operations."""

    pass


class WebhookLimitExceeded(WebhookError):
    """Raised when user exceeds webhook limit."""

    pass


class WebhookNotFoundError(WebhookError):
    """Raised when webhook is not found."""

    pass


class ContributorWebhookService:
    """
    Service for managing contributor webhooks.

    Features:
    - Register/unregister webhooks (max 10 per user)
    - Send notifications on bounty events
    - HMAC-SHA256 signature verification
    - Retry logic with exponential backoff (3 attempts)
    """

    def __init__(self, db: AsyncSession):
        """Initialize the service with database session."""
        self.db = db

    async def register_webhook(
        self,
        user_id: str,
        url: str,
        description: Optional[str] = None,
    ) -> ContributorWebhookDB:
        """
        Register a new webhook URL for a user.

        Args:
            user_id: UUID of the user registering the webhook
            url: Webhook URL to receive notifications
            description: Optional human-readable description

        Returns:
            Created webhook record

        Raises:
            WebhookLimitExceeded: If user already has 10 webhooks
        """
        # Check webhook limit
        existing_count = await self._count_user_webhooks(user_id)
        if existing_count >= MAX_WEBHOOKS_PER_USER:
            raise WebhookLimitExceeded(
                f"Maximum {MAX_WEBHOOKS_PER_USER} webhooks allowed per user"
            )

        # Generate secret for HMAC signature
        secret = secrets.token_hex(32)

        webhook = ContributorWebhookDB(
            user_id=uuid.UUID(user_id),
            url=url,
            secret=secret,
            description=description,
            is_active=True,
        )

        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)

        logger.info("Registered webhook %s for user %s", webhook.id, user_id)
        return webhook

    async def unregister_webhook(self, webhook_id: str, user_id: str) -> bool:
        """
        Unregister a webhook.

        Args:
            webhook_id: UUID of the webhook to unregister
            user_id: UUID of the user (for authorization)

        Returns:
            True if webhook was deleted, False if not found

        Raises:
            WebhookNotFoundError: If webhook doesn't exist or doesn't belong to user
        """
        query = select(ContributorWebhookDB).where(
            ContributorWebhookDB.id == uuid.UUID(webhook_id),
            ContributorWebhookDB.user_id == uuid.UUID(user_id),
        )
        result = await self.db.execute(query)
        webhook = result.scalar_one_or_none()

        if not webhook:
            raise WebhookNotFoundError(
                f"Webhook {webhook_id} not found or not owned by user"
            )

        await self.db.delete(webhook)
        await self.db.commit()

        logger.info("Unregistered webhook %s for user %s", webhook_id, user_id)
        return True

    async def list_webhooks(self, user_id: str) -> List[ContributorWebhookDB]:
        """
        List all webhooks for a user.

        Args:
            user_id: UUID of the user

        Returns:
            List of webhook records
        """
        query = (
            select(ContributorWebhookDB)
            .where(ContributorWebhookDB.user_id == uuid.UUID(user_id))
            .order_by(ContributorWebhookDB.created_at.desc())
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def send_notification(
        self,
        user_id: str,
        event_type: WebhookEventType,
        bounty_id: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Send webhook notification to all active webhooks for a user.

        Args:
            user_id: UUID of the user to notify
            event_type: Type of event (bounty.claimed, review.started, etc.)
            bounty_id: UUID of the bounty
            data: Additional event data

        Returns:
            List of delivery results for each webhook
        """
        # Get all active webhooks for user
        query = select(ContributorWebhookDB).where(
            ContributorWebhookDB.user_id == uuid.UUID(user_id),
            ContributorWebhookDB.is_active == True,
        )
        result = await self.db.execute(query)
        webhooks = list(result.scalars().all())

        if not webhooks:
            logger.debug("No active webhooks for user %s", user_id)
            return []

        # Create payload
        payload = WebhookPayload(
            event_type=event_type,
            bounty_id=bounty_id,
            timestamp=datetime.now(timezone.utc),
            data=data or {},
        )

        results = []
        for webhook in webhooks:
            delivery_result = await self._dispatch_webhook(webhook, payload)
            results.append(delivery_result)

        return results

    async def _dispatch_webhook(
        self,
        webhook: ContributorWebhookDB,
        payload: WebhookPayload,
    ) -> Dict[str, Any]:
        """
        Dispatch a webhook with retry logic.

        Implements exponential backoff with 3 attempts.

        Args:
            webhook: Webhook record
            payload: Event payload

        Returns:
            Delivery result with status and details
        """
        payload_json = payload.model_dump_json()
        payload_bytes = payload_json.encode("utf-8")
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()

        # Create delivery log
        log = WebhookDeliveryLogDB(
            webhook_id=webhook.id,
            event_type=payload.event_type.value,
            bounty_id=uuid.UUID(payload.bounty_id) if payload.bounty_id else None,
            payload_hash=payload_hash,
            status=WebhookDeliveryStatus.PENDING.value,
            attempt_number="1",
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        # Generate HMAC signature
        signature = self._generate_signature(payload_bytes, webhook.secret)

        headers = {
            "Content-Type": "application/json",
            "X-SolFoundry-Signature": signature,
            "X-SolFoundry-Event": payload.event_type.value,
            "X-SolFoundry-Delivery": str(log.id),
        }

        # Attempt delivery with retries
        last_error = None
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT_SECONDS) as client:
                    response = await client.post(
                        webhook.url,
                        content=payload_bytes,
                        headers=headers,
                    )

                    if 200 <= response.status_code < 300:
                        # Success
                        log.status = WebhookDeliveryStatus.SUCCESS.value
                        log.response_code = str(response.status_code)
                        webhook.last_triggered_at = datetime.now(timezone.utc)
                        await self.db.commit()

                        logger.info(
                            "Webhook %s delivered successfully (attempt %d)",
                            webhook.id,
                            attempt + 1,
                        )
                        return {
                            "webhook_id": str(webhook.id),
                            "status": "success",
                            "attempt": attempt + 1,
                            "response_code": response.status_code,
                        }

                    # Non-2xx response
                    last_error = f"HTTP {response.status_code}"
                    logger.warning(
                        "Webhook %s returned %d (attempt %d/%d)",
                        webhook.id,
                        response.status_code,
                        attempt + 1,
                        MAX_RETRY_ATTEMPTS,
                    )

            except httpx.TimeoutException:
                last_error = "Request timeout"
                logger.warning(
                    "Webhook %s timed out (attempt %d/%d)",
                    webhook.id,
                    attempt + 1,
                    MAX_RETRY_ATTEMPTS,
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "Webhook %s failed: %s (attempt %d/%d)",
                    webhook.id,
                    e,
                    attempt + 1,
                    MAX_RETRY_ATTEMPTS,
                )

            # Update log for retry
            if attempt < MAX_RETRY_ATTEMPTS - 1:
                log.status = WebhookDeliveryStatus.RETRYING.value
                log.attempt_number = str(attempt + 2)
                log.error_message = last_error
                next_retry = datetime.now(timezone.utc) + timedelta(
                    seconds=RETRY_DELAYS[attempt]
                )
                log.next_retry_at = next_retry
                await self.db.commit()

                # Wait before retry
                await asyncio.sleep(RETRY_DELAYS[attempt])

        # All retries exhausted
        log.status = WebhookDeliveryStatus.FAILED.value
        log.error_message = last_error
        await self.db.commit()

        logger.error(
            "Webhook %s failed after %d attempts: %s",
            webhook.id,
            MAX_RETRY_ATTEMPTS,
            last_error,
        )

        return {
            "webhook_id": str(webhook.id),
            "status": "failed",
            "attempts": MAX_RETRY_ATTEMPTS,
            "error": last_error,
        }

    def _generate_signature(self, payload: bytes, secret: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.

        Args:
            payload: Raw payload bytes
            secret: Webhook secret

        Returns:
            Signature string in format "sha256=<hex>"
        """
        signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    def verify_signature(
        payload: bytes,
        signature_header: str,
        secret: str,
    ) -> bool:
        """
        Verify webhook signature.

        Args:
            payload: Raw payload bytes received
            signature_header: X-SolFoundry-Signature header value
            secret: Webhook secret

        Returns:
            True if signature is valid, False otherwise
        """
        if not signature_header or not signature_header.startswith("sha256="):
            return False

        expected = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()

        received = signature_header[7:]  # Remove "sha256=" prefix

        return hmac.compare_digest(expected, received)

    async def _count_user_webhooks(self, user_id: str) -> int:
        """Count webhooks for a user."""
        from sqlalchemy import func

        query = select(func.count()).select_from(ContributorWebhookDB).where(
            ContributorWebhookDB.user_id == uuid.UUID(user_id)
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_webhook(self, webhook_id: str, user_id: str) -> Optional[ContributorWebhookDB]:
        """
        Get a specific webhook by ID.

        Args:
            webhook_id: UUID of the webhook
            user_id: UUID of the user (for authorization)

        Returns:
            Webhook record or None if not found
        """
        query = select(ContributorWebhookDB).where(
            ContributorWebhookDB.id == uuid.UUID(webhook_id),
            ContributorWebhookDB.user_id == uuid.UUID(user_id),
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_webhook(
        self,
        webhook_id: str,
        user_id: str,
        url: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> ContributorWebhookDB:
        """
        Update a webhook.

        Args:
            webhook_id: UUID of the webhook
            user_id: UUID of the user
            url: New URL (optional)
            description: New description (optional)
            is_active: New active status (optional)

        Returns:
            Updated webhook record

        Raises:
            WebhookNotFoundError: If webhook doesn't exist
        """
        webhook = await self.get_webhook(webhook_id, user_id)
        if not webhook:
            raise WebhookNotFoundError(
                f"Webhook {webhook_id} not found or not owned by user"
            )

        if url is not None:
            webhook.url = url
        if description is not None:
            webhook.description = description
        if is_active is not None:
            webhook.is_active = is_active

        webhook.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(webhook)

        logger.info("Updated webhook %s", webhook_id)
        return webhook

    async def process_pending_retries(self) -> int:
        """
        Process pending webhook retries.

        Called by background task to retry failed webhooks.

        Returns:
            Number of retries processed
        """
        now = datetime.now(timezone.utc)
        query = select(WebhookDeliveryLogDB).where(
            WebhookDeliveryLogDB.status == WebhookDeliveryStatus.RETRYING.value,
            WebhookDeliveryLogDB.next_retry_at <= now,
        )
        result = await self.db.execute(query)
        pending = list(result.scalars().all())

        for log in pending:
            # Get webhook
            webhook_query = select(ContributorWebhookDB).where(
                ContributorWebhookDB.id == log.webhook_id
            )
            webhook_result = await self.db.execute(webhook_query)
            webhook = webhook_result.scalar_one_or_none()

            if not webhook or not webhook.is_active:
                log.status = WebhookDeliveryStatus.FAILED.value
                log.error_message = "Webhook no longer active"
                await self.db.commit()
                continue

            # Reconstruct payload (simplified - in production would store full payload)
            # For now, mark as failed and rely on new events
            log.status = WebhookDeliveryStatus.FAILED.value
            log.error_message = "Retry not implemented for this version"
            await self.db.commit()

        return len(pending)


# Convenience function for use in other services
async def notify_contributor(
    db: AsyncSession,
    user_id: str,
    event_type: WebhookEventType,
    bounty_id: str,
    data: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Send webhook notification to a contributor.

    Convenience wrapper around ContributorWebhookService.

    Args:
        db: Database session
        user_id: UUID of the user to notify
        event_type: Type of event
        bounty_id: UUID of the bounty
        data: Additional event data

    Returns:
        List of delivery results
    """
    service = ContributorWebhookService(db)
    return await service.send_notification(user_id, event_type, bounty_id, data)