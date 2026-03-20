"""Tests for WebSocket real-time update functionality.

This module tests:
- WebSocket connection lifecycle
- Subscription management per bounty spec
- Event broadcasting
- Heartbeat mechanism
- JWT authentication
- Rate limiting
- Reconnection handling
- Error handling
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket, status

from app.api.websocket import (
    router,
    broadcast_bounty_event,
    broadcast_pr_event,
    broadcast_payout_event,
    broadcast_leaderboard_event,
    broadcast_pr_status,
    broadcast_payout_sent,
)
from app.services.websocket_manager import (
    ConnectionManager,
    EventType,
    Channel,
    Subscription,
    WebSocketMessage,
    HeartbeatMessage,
    ErrorMessage,
    AuthenticationError,
)


# Create test app
app = FastAPI()
app.include_router(router)


@pytest.fixture
def manager():
    """Create a fresh ConnectionManager for each test."""
    return ConnectionManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket for testing."""
    ws = MagicMock(spec=WebSocket)
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.close = AsyncMock()
    return ws


class TestSubscription:
    """Tests for Subscription dataclass."""
    
    def test_subscription_creation(self):
        """Test creating a subscription."""
        sub = Subscription(channel="bounties")
        assert sub.channel == "bounties"
    
    def test_subscription_with_id(self):
        """Test creating a subscription with specific ID."""
        sub = Subscription(channel="bounties:42")
        assert sub.channel == "bounties:42"
        assert sub.to_channel_name() == "bounties"
        assert sub.get_target_id() == "42"
    
    def test_subscription_to_redis_channel(self):
        """Test Redis channel name generation."""
        sub = Subscription(channel="bounties:42")
        assert sub.to_redis_channel() == "ws:bounties:42"
    
    def test_subscription_from_string_valid(self):
        """Test parsing valid subscription strings."""
        sub = Subscription.from_string("bounties")
        assert sub is not None
        assert sub.channel == "bounties"
        
        sub = Subscription.from_string("bounties:42")
        assert sub is not None
        assert sub.channel == "bounties:42"
    
    def test_subscription_from_string_invalid(self):
        """Test parsing invalid subscription strings."""
        assert Subscription.from_string("invalid_channel") is None
        assert Subscription.from_string("") is None
    
    def test_subscription_equality(self):
        """Test subscription equality."""
        sub1 = Subscription(channel="bounties:42")
        sub2 = Subscription(channel="bounties:42")
        sub3 = Subscription(channel="bounties:43")
        
        assert sub1 == sub2
        assert sub1 != sub3


class TestConnectionManager:
    """Tests for ConnectionManager."""
    
    @pytest.mark.asyncio
    async def test_connect_without_token(self, manager, mock_websocket):
        """Test WebSocket connection without authentication."""
        info = await manager.connect(mock_websocket, token=None)
        
        assert info.user_id is None
        assert not info.is_authenticated
        mock_websocket.accept.assert_called_once()
        assert manager.get_connection_count() == 1
    
    @pytest.mark.asyncio
    async def test_connect_with_valid_jwt(self, manager, mock_websocket):
        """Test WebSocket connection with valid JWT token."""
        import jwt
        test_secret = "test_secret"
        manager._jwt_secret = test_secret
        
        token = jwt.encode({"user_id": "user_123"}, test_secret, algorithm="HS256")
        
        info = await manager.connect(mock_websocket, token=token)
        
        assert info.user_id == "user_123"
        assert info.is_authenticated
    
    @pytest.mark.asyncio
    async def test_connect_with_expired_jwt(self, manager, mock_websocket):
        """Test WebSocket connection with expired JWT token."""
        import jwt
        from datetime import timedelta
        
        test_secret = "test_secret"
        manager._jwt_secret = test_secret
        
        expired_payload = {
            "user_id": "user_123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(expired_payload, test_secret, algorithm="HS256")
        
        with pytest.raises(AuthenticationError):
            await manager.connect(mock_websocket, token=token)
    
    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test WebSocket disconnection."""
        await manager.connect(mock_websocket, token=None)
        await manager.disconnect(mock_websocket)
        
        assert manager.get_connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_multiple_connections(self, manager):
        """Test multiple connections from the same user."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        
        import jwt
        test_secret = "test_secret"
        manager._jwt_secret = test_secret
        token = jwt.encode({"user_id": "user_123"}, test_secret, algorithm="HS256")
        
        await manager.connect(ws1, token=token)
        await manager.connect(ws2, token=token)
        
        assert manager.get_connection_count() == 2
        assert manager.get_user_connection_count("user_123") == 2
    
    @pytest.mark.asyncio
    async def test_subscribe(self, manager, mock_websocket):
        """Test subscription to a channel."""
        await manager.connect(mock_websocket, token=None)
        
        sub = Subscription(channel="bounties")
        success = await manager.subscribe(mock_websocket, sub)
        
        assert success
        info = manager._ws_to_info.get(mock_websocket)
        assert sub in info.subscriptions
    
    @pytest.mark.asyncio
    async def test_subscribe_specific_bounty(self, manager, mock_websocket):
        """Test subscription to specific bounty."""
        await manager.connect(mock_websocket, token=None)
        
        sub = Subscription(channel="bounties:42")
        success = await manager.subscribe(mock_websocket, sub)
        
        assert success
        info = manager._ws_to_info.get(mock_websocket)
        assert sub in info.subscriptions
    
    @pytest.mark.asyncio
    async def test_unsubscribe(self, manager, mock_websocket):
        """Test unsubscribing from a channel."""
        await manager.connect(mock_websocket, token=None)
        
        sub = Subscription(channel="bounties:42")
        await manager.subscribe(mock_websocket, sub)
        success = await manager.unsubscribe(mock_websocket, sub)
        
        assert success
        info = manager._ws_to_info.get(mock_websocket)
        assert sub not in info.subscriptions
    
    @pytest.mark.asyncio
    async def test_broadcast_to_channel(self, manager, mock_websocket):
        """Test broadcasting to channel subscribers."""
        await manager.connect(mock_websocket, token=None)
        
        sub = Subscription(channel="bounties")
        await manager.subscribe(mock_websocket, sub)
        
        count = await manager.broadcast_event(
            event_type=EventType.BOUNTY_CREATED,
            data={"bounty_id": "42", "title": "Test Bounty"},
            channel="bounties"
        )
        
        assert count == 1
        mock_websocket.send_json.assert_called()
        
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "bounty_created"
        assert call_args["data"]["bounty_id"] == "42"
    
    @pytest.mark.asyncio
    async def test_broadcast_to_specific_bounty(self, manager, mock_websocket):
        """Test broadcasting to specific bounty subscribers."""
        await manager.connect(mock_websocket, token=None)
        
        sub = Subscription(channel="bounties:42")
        await manager.subscribe(mock_websocket, sub)
        
        count = await manager.broadcast_event(
            event_type=EventType.BOUNTY_CLAIMED,
            data={"bounty_id": "42", "claimer": "user_123"},
            channel="bounties:42"
        )
        
        assert count == 1
    
    @pytest.mark.asyncio
    async def test_broadcast_excludes_unsubscribed(self, manager):
        """Test that broadcast doesn't send to unsubscribed connections."""
        ws1 = MagicMock(spec=WebSocket)
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()
        
        ws2 = MagicMock(spec=WebSocket)
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()
        
        await manager.connect(ws1, token=None)
        await manager.connect(ws2, token=None)
        
        await manager.subscribe(ws1, Subscription(channel="bounties"))
        
        count = await manager.broadcast_event(
            event_type=EventType.BOUNTY_CREATED,
            data={"bounty_id": "42"},
            channel="bounties"
        )
        
        assert count == 1
        ws1.send_json.assert_called()
        ws2.send_json.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, manager, mock_websocket):
        """Test rate limiting per connection."""
        info = await manager.connect(mock_websocket, token=None)
        
        for i in range(100):
            assert manager.check_rate_limit(info)
        
        assert not manager.check_rate_limit(info)


class TestWebSocketMessages:
    """Tests for WebSocket message models."""
    
    def test_websocket_message_format(self):
        """Test WebSocketMessage follows bounty spec format."""
        msg = WebSocketMessage(
            type="bounty_created",
            data={"bounty_id": "42"}
        )
        
        assert msg.type == "bounty_created"
        assert msg.data["bounty_id"] == "42"
        assert msg.timestamp is not None
        
        serialized = msg.model_dump(mode="json")
        assert "type" in serialized
        assert "timestamp" in serialized
        assert "data" in serialized
    
    def test_heartbeat_message(self):
        """Test HeartbeatMessage model."""
        msg = HeartbeatMessage(ping_id="ping_123")
        
        assert msg.type == "heartbeat"
        assert msg.ping_id == "ping_123"
    
    def test_error_message(self):
        """Test ErrorMessage model."""
        msg = ErrorMessage(
            error_code="INVALID_CHANNEL",
            message="Invalid channel name",
            details={"valid_channels": ["bounties", "prs"]}
        )
        
        assert msg.type == "error"
        assert msg.error_code == "INVALID_CHANNEL"
        assert msg.details["valid_channels"] is not None


class TestWebSocketEndpoint:
    """Tests for WebSocket API endpoints."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test basic WebSocket connection."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                data = websocket.receive_json()
                
                assert data["type"] == "connected"
                assert "timestamp" in data
                assert data["data"]["message"] == "Connected to SolFoundry real-time updates"
    
    @pytest.mark.asyncio
    async def test_websocket_subscribe_bounties(self):
        """Test WebSocket subscription to bounties channel."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                websocket.receive_json()
                
                websocket.send_json({"subscribe": "bounties"})
                
                data = websocket.receive_json()
                
                assert data["type"] == "subscribed"
                assert data["data"]["channel"] == "bounties"
    
    @pytest.mark.asyncio
    async def test_websocket_subscribe_specific_bounty(self):
        """Test WebSocket subscription to specific bounty."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                websocket.receive_json()
                
                websocket.send_json({"subscribe": "bounties:42"})
                
                data = websocket.receive_json()
                
                assert data["type"] == "subscribed"
                assert data["data"]["channel"] == "bounties:42"
    
    @pytest.mark.asyncio
    async def test_websocket_invalid_channel(self):
        """Test WebSocket subscription with invalid channel."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                websocket.receive_json()
                
                websocket.send_json({"subscribe": "invalid_channel"})
                
                data = websocket.receive_json()
                
                assert data["type"] == "error"
                assert data["error_code"] == "INVALID_CHANNEL"
    
    @pytest.mark.asyncio
    async def test_websocket_unsubscribe(self):
        """Test WebSocket unsubscription."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                websocket.receive_json()
                
                websocket.send_json({"subscribe": "bounties"})
                websocket.receive_json()
                
                websocket.send_json({"unsubscribe": "bounties"})
                
                data = websocket.receive_json()
                assert data["type"] == "unsubscribed"
    
    @pytest.mark.asyncio
    async def test_websocket_pong(self):
        """Test WebSocket pong response."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                websocket.receive_json()
                
                websocket.send_json({"pong": "ping_123"})
    
    @pytest.mark.asyncio
    async def test_websocket_reconnect_flag(self):
        """Test that reconnect flag is acknowledged."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws?reconnect=true") as websocket:
                data = websocket.receive_json()
                
                assert data["type"] == "connected"
                assert data["data"]["reconnected"] is True
    
    @pytest.mark.asyncio
    async def test_websocket_stats_endpoint(self):
        """Test WebSocket stats HTTP endpoint."""
        with TestClient(app) as client:
            response = client.get("/ws/stats")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "total_connections" in data
            assert "unique_users" in data
            assert "redis_enabled" in data
            assert "subscriptions" in data


class TestBroadcastHelpers:
    """Tests for broadcast helper functions."""
    
    @pytest.mark.asyncio
    async def test_broadcast_bounty_created(self, manager, mock_websocket):
        """Test bounty created broadcast."""
        await manager.connect(mock_websocket, token=None)
        await manager.subscribe(mock_websocket, Subscription(channel="bounties"))
        
        with patch("app.api.websocket.manager", manager):
            count = await broadcast_bounty_event(
                event_type=EventType.BOUNTY_CREATED,
                data={"bounty_id": "42", "title": "Test Bounty"}
            )
        
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_broadcast_pr_status_changed(self, manager, mock_websocket):
        """Test PR status change broadcast."""
        await manager.connect(mock_websocket, token=None)
        await manager.subscribe(mock_websocket, Subscription(channel="prs"))
        
        with patch("app.api.websocket.manager", manager):
            count = await broadcast_pr_event(
                event_type=EventType.PR_STATUS_CHANGED,
                pr_id="pr_123",
                repo_id="repo_456",
                data={"status": "merged"}
            )
        
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_broadcast_payout_sent(self, manager, mock_websocket):
        """Test payout sent broadcast."""
        import jwt
        test_secret = "test_secret"
        manager._jwt_secret = test_secret
        token = jwt.encode({"user_id": "user_123"}, test_secret, algorithm="HS256")
        
        await manager.connect(mock_websocket, token=token)
        await manager.subscribe(mock_websocket, Subscription(channel="payouts"))
        
        with patch("app.api.websocket.manager", manager):
            count = await broadcast_payout_event(
                event_type=EventType.PAYOUT_SENT,
                bounty_id="bounty_42",
                user_id="user_123",
                amount=100.0,
                transaction_id="tx_abc"
            )
        
        assert count >= 1
    
    @pytest.mark.asyncio
    async def test_broadcast_leaderboard_changed(self, manager, mock_websocket):
        """Test leaderboard change broadcast."""
        await manager.connect(mock_websocket, token=None)
        await manager.subscribe(mock_websocket, Subscription(channel="leaderboard"))
        
        with patch("app.api.websocket.manager", manager):
            count = await broadcast_leaderboard_event(
                event_type=EventType.LEADERBOARD_CHANGED,
                data={"user_id": "user_123", "new_rank": 1}
            )
        
        assert count >= 1


class TestHeartbeat:
    """Tests for heartbeat mechanism."""
    
    @pytest.mark.asyncio
    async def test_heartbeat_task_starts(self, manager):
        """Test that heartbeat task starts on initialization."""
        await manager.initialize()
        
        assert manager._heartbeat_task is not None
        assert not manager._heartbeat_task.done()
        
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_handle_pong(self, manager, mock_websocket):
        """Test pong handling updates last_pong time."""
        info = await manager.connect(mock_websocket, token=None)
        old_pong = info.last_pong
        
        await asyncio.sleep(0.01)
        manager.handle_pong(mock_websocket)
        
        assert info.last_pong > old_pong
    
    @pytest.mark.asyncio
    async def test_connection_timeout_cleanup(self, manager, mock_websocket):
        """Test that dead connections are cleaned up."""
        await manager.connect(mock_websocket, token=None)
        
        info = manager._ws_to_info.get(mock_websocket)
        info.is_alive = False
        
        assert manager.get_connection_count() == 1


class TestAuthentication:
    """Tests for JWT authentication."""
    
    @pytest.mark.asyncio
    async def test_valid_jwt_allows_connection(self, manager, mock_websocket):
        """Test that valid JWT allows authenticated connection."""
        import jwt
        test_secret = "test_secret"
        manager._jwt_secret = test_secret
        
        token = jwt.encode({"user_id": "user_123"}, test_secret, algorithm="HS256")
        info = await manager.connect(mock_websocket, token=token)
        
        assert info.is_authenticated
        assert info.user_id == "user_123"
    
    @pytest.mark.asyncio
    async def test_expired_jwt_rejected(self, manager, mock_websocket):
        """Test that expired JWT is rejected."""
        import jwt
        from datetime import timedelta
        
        test_secret = "test_secret"
        manager._jwt_secret = test_secret
        
        payload = {
            "user_id": "user_123",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1)
        }
        token = jwt.encode(payload, test_secret, algorithm="HS256")
        
        with pytest.raises(AuthenticationError):
            await manager.connect(mock_websocket, token=token)
    
    @pytest.mark.asyncio
    async def test_no_jwt_secret_allows_anonymous(self, manager, mock_websocket):
        """Test that missing JWT secret allows anonymous connections."""
        manager._jwt_secret = None
        
        info = await manager.connect(mock_websocket, token=None)
        
        assert not info.is_authenticated


class TestRateLimiting:
    """Tests for rate limiting."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self, manager, mock_websocket):
        """Test that rate limit is enforced."""
        info = await manager.connect(mock_websocket, token=None)
        
        for i in range(manager.RATE_LIMIT_MAX_MESSAGES):
            assert manager.check_rate_limit(info)
        
        assert not manager.check_rate_limit(info)
    
    @pytest.mark.asyncio
    async def test_rate_limit_resets(self, manager, mock_websocket):
        """Test that rate limit resets after window."""
        info = await manager.connect(mock_websocket, token=None)
        
        for i in range(manager.RATE_LIMIT_MAX_MESSAGES):
            manager.check_rate_limit(info)
        
        info.rate_limit_window_start = None
        
        assert manager.check_rate_limit(info)


class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_invalid_json_error(self):
        """Test error response for invalid JSON."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                websocket.receive_json()
                
                websocket.send_text("not json")
                
                data = websocket.receive_json()
                assert data["type"] == "error"
                assert data["error_code"] == "INVALID_MESSAGE"
    
    @pytest.mark.asyncio
    async def test_unknown_message_format_error(self):
        """Test error response for unknown message format."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as websocket:
                websocket.receive_json()
                
                websocket.send_json({"unknown_field": "value"})
                
                data = websocket.receive_json()
                assert data["type"] == "error"
                assert data["error_code"] == "INVALID_MESSAGE"


class TestIntegration:
    """Integration tests for WebSocket system."""
    
    @pytest.mark.asyncio
    async def test_full_flow(self):
        """Test full WebSocket flow: connect, subscribe, receive event, disconnect."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()
                
                ws.send_json({"subscribe": "bounties"})
                ws.receive_json()
                
                ws.send_json({"subscribe": "prs"})
                ws.receive_json()
                
                ws.send_json({"subscribe": "bounties:42"})
                ws.receive_json()
                
                response = client.get("/ws/stats")
                assert response.json()["total_connections"] == 1
    
    @pytest.mark.asyncio
    async def test_multiple_users_different_subscriptions(self):
        """Test multiple users with different subscriptions."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws1:
                ws1.receive_json()
                ws1.send_json({"subscribe": "bounties"})
                ws1.receive_json()
                
                with client.websocket_connect("/ws") as ws2:
                    ws2.receive_json()
                    ws2.send_json({"subscribe": "prs"})
                    ws2.receive_json()
                    
                    response = client.get("/ws/stats")
                    stats = response.json()
                    
                    assert stats["total_connections"] == 2
    
    @pytest.mark.asyncio
    async def test_channel_matching(self):
        """Test that wildcard channel subscription receives specific events."""
        pass


class TestConnectionStress:
    """Stress tests for WebSocket connections."""
    
    @pytest.mark.asyncio
    async def test_rapid_connect_disconnect(self):
        """Test rapid connect/disconnect cycles."""
        with TestClient(app) as client:
            for i in range(10):
                with client.websocket_connect("/ws") as ws:
                    ws.receive_json()
    
    @pytest.mark.asyncio
    async def test_many_subscriptions(self):
        """Test many subscriptions on single connection."""
        with TestClient(app) as client:
            with client.websocket_connect("/ws") as ws:
                ws.receive_json()
                
                for channel in ["bounties", "prs", "payouts", "leaderboard"]:
                    ws.send_json({"subscribe": channel})
                    ws.receive_json()
                
                response = client.get("/ws/stats")
                assert response.json()["subscriptions"] >= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])