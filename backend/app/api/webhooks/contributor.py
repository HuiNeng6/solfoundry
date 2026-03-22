"""Contributor webhook API endpoints.

Provides endpoints for contributors to register webhook URLs
and receive notifications about bounty status changes.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.auth import get_current_user_id
from app.models.contributor_webhook_pydantic import (
    WebhookRegisterRequest,
    WebhookUpdateRequest,
    WebhookResponse,
    WebhookListResponse,
    WebhookEventType,
)
from app.services.contributor_webhook_service import (
    ContributorWebhookService,
    WebhookError,
    WebhookLimitExceeded,
    WebhookNotFoundError,
)

router = APIRouter(prefix="/webhooks", tags=["notifications"])


@router.post(
    "/register",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register webhook URL",
    description="Register a webhook URL to receive bounty status notifications. Max 10 webhooks per user.",
    responses={
        201: {"description": "Webhook registered successfully"},
        400: {"description": "Invalid URL or request"},
        401: {"description": "Authentication required"},
        409: {"description": "Webhook limit exceeded (max 10 per user)"},
    },
)
async def register_webhook(
    request: WebhookRegisterRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> WebhookResponse:
    """
    Register a webhook URL for bounty notifications.

    The registered URL will receive POST requests with webhook payloads
    when bounty status changes occur:
    - bounty.claimed: When a bounty is claimed
    - review.started: When review begins
    - review.passed: When review passes
    - review.failed: When review fails
    - bounty.paid: When bounty is paid out

    Each webhook receives a unique secret for HMAC-SHA256 signature verification.
    """
    service = ContributorWebhookService(db)

    try:
        webhook = await service.register_webhook(
            user_id=user_id,
            url=request.url,
            description=request.description,
        )
        return WebhookResponse(
            id=str(webhook.id),
            url=webhook.url,
            description=webhook.description,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            last_triggered_at=webhook.last_triggered_at,
        )
    except WebhookLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except WebhookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister webhook",
    description="Remove a registered webhook URL.",
    responses={
        204: {"description": "Webhook unregistered successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Webhook not found"},
    },
)
async def unregister_webhook(
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> None:
    """
    Unregister a webhook URL.

    Only the owner of the webhook can unregister it.
    """
    service = ContributorWebhookService(db)

    try:
        await service.unregister_webhook(webhook_id=webhook_id, user_id=user_id)
    except WebhookNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "",
    response_model=WebhookListResponse,
    summary="List registered webhooks",
    description="List all webhook URLs registered by the authenticated user.",
    responses={
        200: {"description": "List of webhooks"},
        401: {"description": "Authentication required"},
    },
)
async def list_webhooks(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> WebhookListResponse:
    """
    List all webhooks registered by the current user.

    Returns webhook details including URL, status, and last triggered time.
    """
    service = ContributorWebhookService(db)
    webhooks = await service.list_webhooks(user_id=user_id)

    items = [
        WebhookResponse(
            id=str(w.id),
            url=w.url,
            description=w.description,
            is_active=w.is_active,
            created_at=w.created_at,
            updated_at=w.updated_at,
            last_triggered_at=w.last_triggered_at,
        )
        for w in webhooks
    ]

    return WebhookListResponse(items=items, total=len(items))


@router.patch(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update webhook",
    description="Update a registered webhook's URL, description, or active status.",
    responses={
        200: {"description": "Webhook updated successfully"},
        401: {"description": "Authentication required"},
        404: {"description": "Webhook not found"},
    },
)
async def update_webhook(
    webhook_id: str,
    request: WebhookUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> WebhookResponse:
    """
    Update a webhook's settings.

    Can update URL, description, and active status.
    Only the owner can update the webhook.
    """
    service = ContributorWebhookService(db)

    try:
        webhook = await service.update_webhook(
            webhook_id=webhook_id,
            user_id=user_id,
            url=request.url,
            description=request.description,
            is_active=request.is_active,
        )
        return WebhookResponse(
            id=str(webhook.id),
            url=webhook.url,
            description=webhook.description,
            is_active=webhook.is_active,
            created_at=webhook.created_at,
            updated_at=webhook.updated_at,
            last_triggered_at=webhook.last_triggered_at,
        )
    except WebhookNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Get webhook details",
    description="Get details of a specific registered webhook.",
    responses={
        200: {"description": "Webhook details"},
        401: {"description": "Authentication required"},
        404: {"description": "Webhook not found"},
    },
)
async def get_webhook(
    webhook_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
) -> WebhookResponse:
    """
    Get details of a specific webhook.

    Only the owner can view webhook details.
    """
    service = ContributorWebhookService(db)
    webhook = await service.get_webhook(webhook_id=webhook_id, user_id=user_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Webhook {webhook_id} not found",
        )

    return WebhookResponse(
        id=str(webhook.id),
        url=webhook.url,
        description=webhook.description,
        is_active=webhook.is_active,
        created_at=webhook.created_at,
        updated_at=webhook.updated_at,
        last_triggered_at=webhook.last_triggered_at,
    )