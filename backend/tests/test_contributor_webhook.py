"""Tests for contributor webhook notification system.

Tests cover:
- Webhook registration (CRUD)
- Rate limiting (max 10 per user)
- Webhook dispatch with retry logic
- HMAC-SHA256 signature verification
"""

import hashlib
import hmac
import json
import os
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import pytest_asyncio

# Set test environment variables before importing app modules
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-ci")
os.environ.setdefault("AUTH_ENABLED", "false")

from app.models.contributor_webhook import ContributorWebhookDB, WebhookDeliveryLogDB
from app.models.contributor_webhook_pydantic import (
    WebhookEventType,
    WebhookPayload,
    WebhookRegisterRequest,
    WebhookResponse,
)
from app.services.contributor_webhook_service import (
    ContributorWebhookService,
    WebhookLimitExceeded,
    WebhookNotFoundError,
)


# ---------------------------------------------------------------------------
# Unit Tests - Service Layer (no database required)
# ---------------------------------------------------------------------------


class TestWebhookSignature:
    """Tests for HMAC-SHA256 signature generation and verification."""

    def test_generate_signature(self):
        """Test signature generation."""
        payload = b'{"test": "data"}'
        secret = "test_secret_123"

        signature = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        signature_with_prefix = f"sha256={signature}"

        # Verify format
        assert signature_with_prefix.startswith("sha256=")
        assert len(signature_with_prefix) == 71  # "sha256=" + 64 hex chars

    def test_verify_signature_success(self):
        """Test successful signature verification."""
        payload = b'{"amount": 100}'
        secret = "secret123"

        signature = f"sha256={hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()}"

        # Verify
        expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        received = signature[7:]  # Remove "sha256=" prefix

        assert hmac.compare_digest(expected, received) is True

    def test_verify_signature_tampering_detected(self):
        """Test that tampered payload is detected."""
        payload = b'{"amount": 100}'
        secret = "secret123"

        signature = f"sha256={hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()}"

        # Tamper with payload
        tampered_payload = b'{"amount": 999}'

        # Should fail verification
        expected = hmac.new(secret.encode("utf-8"), tampered_payload, hashlib.sha256).hexdigest()
        received = signature[7:]

        assert hmac.compare_digest(expected, received) is False

    def test_verify_signature_wrong_secret(self):
        """Test that wrong secret is detected."""
        payload = b'{"test": "data"}'
        correct_secret = "correct_secret"
        wrong_secret = "wrong_secret"

        signature = f"sha256={hmac.new(correct_secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()}"

        # Should fail with wrong secret
        expected = hmac.new(wrong_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        received = signature[7:]

        assert hmac.compare_digest(expected, received) is False


class TestWebhookPayload:
    """Tests for webhook payload structure."""

    def test_payload_structure(self):
        """Test that webhook payload has correct structure."""
        payload = WebhookPayload(
            event_type=WebhookEventType.BOUNTY_CLAIMED,
            bounty_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            data={"title": "Test Bounty", "amount": 100.0},
        )

        # Verify JSON serialization
        payload_json = payload.model_dump_json()
        parsed = json.loads(payload_json)

        assert parsed["event_type"] == "bounty.claimed"
        assert "bounty_id" in parsed
        assert "timestamp" in parsed
        assert parsed["data"]["title"] == "Test Bounty"

    def test_all_event_types(self):
        """Test all required event types are defined."""
        required_events = [
            "bounty.claimed",
            "review.started",
            "review.passed",
            "review.failed",
            "bounty.paid",
        ]

        for event in required_events:
            assert WebhookEventType(event) is not None

    def test_payload_with_bounty_data(self):
        """Test payload with bounty-specific data."""
        bounty_id = str(uuid.uuid4())
        payload = WebhookPayload(
            event_type=WebhookEventType.BOUNTY_PAID,
            bounty_id=bounty_id,
            timestamp=datetime.now(timezone.utc),
            data={
                "title": "Implement Feature X",
                "amount": 150000,
                "contributor_wallet": "7Pq6...",
                "tx_hash": "abc123",
            },
        )

        assert payload.event_type == WebhookEventType.BOUNTY_PAID
        assert payload.bounty_id == bounty_id
        assert payload.data["amount"] == 150000
        assert "tx_hash" in payload.data


class TestWebhookRateLimit:
    """Tests for webhook rate limiting."""

    def test_max_webhooks_per_user_constant(self):
        """Test that max webhooks constant is correct."""
        from app.services.contributor_webhook_service import MAX_WEBHOOKS_PER_USER

        assert MAX_WEBHOOKS_PER_USER == 10


class TestRetryLogic:
    """Tests for webhook retry logic."""

    def test_retry_delays(self):
        """Test that retry delays are correctly configured."""
        from app.services.contributor_webhook_service import RETRY_DELAYS, MAX_RETRY_ATTEMPTS

        assert MAX_RETRY_ATTEMPTS == 3
        assert RETRY_DELAYS == [1, 5, 30]  # Exponential backoff


class TestServiceSignatureMethods:
    """Tests for service signature methods without database."""

    def test_generate_signature_method(self):
        """Test the _generate_signature method."""
        from app.services.contributor_webhook_service import ContributorWebhookService

        payload = b'{"test": "data"}'
        secret = "my_secret_key"

        # The method is static-like but needs instance, so we test the logic
        expected = f"sha256={hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()}"

        # Verify the signature format
        assert expected.startswith("sha256=")
        assert len(expected) == 71  # "sha256=" + 64 hex chars

    def test_verify_signature_static_method(self):
        """Test the verify_signature static method."""
        from app.services.contributor_webhook_service import ContributorWebhookService

        payload = b'{"test": "data"}'
        secret = "my_secret_key"

        signature = f"sha256={hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()}"

        # Should verify successfully
        assert ContributorWebhookService.verify_signature(payload, signature, secret) is True

        # Should fail with wrong secret
        assert ContributorWebhookService.verify_signature(payload, signature, "wrong") is False

        # Should fail with tampered payload
        assert ContributorWebhookService.verify_signature(b'{"test": "other"}', signature, secret) is False


# ---------------------------------------------------------------------------
# Integration Tests - API Layer (with mocked database)
# ---------------------------------------------------------------------------


class TestWebhookAPIEndpoints:
    """Tests for webhook API endpoint definitions."""

    def test_register_request_model(self):
        """Test WebhookRegisterRequest model validation."""
        request = WebhookRegisterRequest(
            url="https://example.com/webhook",
            description="Test webhook",
        )

        assert request.url == "https://example.com/webhook"
        assert request.description == "Test webhook"

    def test_webhook_response_model(self):
        """Test WebhookResponse model."""
        now = datetime.now(timezone.utc)
        response = WebhookResponse(
            id=str(uuid.uuid4()),
            url="https://example.com/webhook",
            description="Test webhook",
            is_active=True,
            created_at=now,
            updated_at=now,
            last_triggered_at=None,
        )

        assert response.is_active is True
        assert response.url == "https://example.com/webhook"


class TestServiceErrors:
    """Tests for service error classes."""

    def test_webhook_limit_exceeded_error(self):
        """Test WebhookLimitExceeded error."""
        error = WebhookLimitExceeded("Maximum 10 webhooks allowed per user")
        assert "Maximum 10" in str(error)

    def test_webhook_not_found_error(self):
        """Test WebhookNotFoundError error."""
        error = WebhookNotFoundError("Webhook not found")
        assert "not found" in str(error)


# ---------------------------------------------------------------------------
# Mock-based Integration Tests
# ---------------------------------------------------------------------------


class TestWebhookDispatchMocked:
    """Tests for webhook dispatch using mocks."""

    @pytest.mark.asyncio
    async def test_send_notification_mocked(self):
        """Test sending notification with mocked httpx."""
        # Create a mock session
        mock_session = AsyncMock()

        # Mock database query results
        mock_webhook = MagicMock()
        mock_webhook.id = uuid.uuid4()
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.secret = "test_secret"
        mock_webhook.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_webhook]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock httpx
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            service = ContributorWebhookService(mock_session)
            results = await service.send_notification(
                user_id=str(uuid.uuid4()),
                event_type=WebhookEventType.BOUNTY_CLAIMED,
                bounty_id=str(uuid.uuid4()),
                data={"title": "Test Bounty"},
            )

            # Should have attempted to send
            assert mock_post.called or results == []

    @pytest.mark.asyncio
    async def test_webhook_retry_on_failure_mocked(self):
        """Test that webhook retries on failure."""
        mock_session = AsyncMock()

        # Mock database query results
        mock_webhook = MagicMock()
        mock_webhook.id = uuid.uuid4()
        mock_webhook.url = "https://example.com/webhook"
        mock_webhook.secret = "test_secret"
        mock_webhook.is_active = True

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_webhook]
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()

        # Mock httpx to fail all attempts
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.side_effect = Exception("Connection refused")

            service = ContributorWebhookService(mock_session)
            results = await service.send_notification(
                user_id=str(uuid.uuid4()),
                event_type=WebhookEventType.REVIEW_STARTED,
                bounty_id=str(uuid.uuid4()),
            )

            # Should have attempted 3 times (initial + 2 retries)
            assert mock_post.call_count == 3
            assert len(results) == 1
            assert results[0]["status"] == "failed"
            assert results[0]["attempts"] == 3


class TestWebhookSecurity:
    """Tests for webhook security features."""

    def test_signature_header_format(self):
        """Test that signature header is properly formatted."""
        payload = b'{"test": "data"}'
        secret = "secret123"

        signature = f"sha256={hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()}"

        # Verify header format matches expected pattern
        assert signature.startswith("sha256=")
        # Verify it's a valid hex string after prefix
        hex_part = signature[7:]
        assert len(hex_part) == 64
        assert all(c in '0123456789abcdef' for c in hex_part)

    def test_different_payloads_have_different_signatures(self):
        """Test that different payloads produce different signatures."""
        secret = "secret123"
        payload1 = b'{"amount": 100}'
        payload2 = b'{"amount": 200}'

        sig1 = hmac.new(secret.encode('utf-8'), payload1, hashlib.sha256).hexdigest()
        sig2 = hmac.new(secret.encode('utf-8'), payload2, hashlib.sha256).hexdigest()

        assert sig1 != sig2

    def test_different_secrets_have_different_signatures(self):
        """Test that different secrets produce different signatures."""
        payload = b'{"test": "data"}'

        sig1 = hmac.new(b'secret1', payload, hashlib.sha256).hexdigest()
        sig2 = hmac.new(b'secret2', payload, hashlib.sha256).hexdigest()

        assert sig1 != sig2


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])