"""Tests for Treasury API endpoints."""

import pytest
from decimal import Decimal
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.models.treasury import PayoutType, PayoutStatus


# Synchronous test client
client = TestClient(app)


class TestPayoutEndpoints:
    """Tests for payout endpoints."""
    
    def test_list_payouts_default(self):
        """Test listing payouts with default pagination."""
        response = client.get("/api/treasury/payouts")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert data["skip"] == 0
        assert data["limit"] == 20
    
    def test_list_payouts_pagination(self):
        """Test payout pagination parameters."""
        response = client.get("/api/treasury/payouts?skip=1&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 1
        assert data["limit"] == 1
        assert len(data["items"]) <= 1
    
    def test_list_payouts_filter_by_type(self):
        """Test filtering payouts by type."""
        response = client.get("/api/treasury/payouts?payout_type=bounty")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["payout_type"] == "bounty"
    
    def test_list_payouts_filter_by_status(self):
        """Test filtering payouts by status."""
        response = client.get("/api/treasury/payouts?status=completed")
        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["status"] == "completed"
    
    def test_get_payout_not_found(self):
        """Test getting a non-existent payout."""
        response = client.get("/api/treasury/payouts/nonexistent_tx_hash")
        assert response.status_code == 404
    
    def test_get_payout_exists(self):
        """Test getting an existing payout."""
        # First, list payouts to get a valid tx_hash
        list_response = client.get("/api/treasury/payouts")
        assert list_response.status_code == 200
        data = list_response.json()
        
        if data["items"]:
            tx_hash = data["items"][0]["tx_hash"]
            response = client.get(f"/api/treasury/payouts/{tx_hash}")
            assert response.status_code == 200
            payout = response.json()
            assert payout["tx_hash"] == tx_hash
            assert "solscan_url" in payout
            assert "solscan.io" in payout["solscan_url"]
    
    def test_create_payout_duplicate(self):
        """Test creating a duplicate payout."""
        # First, list payouts to get a valid tx_hash
        list_response = client.get("/api/treasury/payouts")
        data = list_response.json()
        
        if data["items"]:
            existing_tx_hash = data["items"][0]["tx_hash"]
            
            new_payout = {
                "tx_hash": existing_tx_hash,
                "recipient_address": "HN7cABqLq46Es1N92m3H2b8f7Y9pQ1aR5wE3sT2gK8dJ6fL4mN0",
                "recipient_username": "test_user",
                "amount": "1.5",
                "token_amount": "6000",
                "payout_type": "bounty",
                "bounty_id": "BOUNTY-TEST",
                "bounty_title": "Test Bounty",
                "status": "completed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            response = client.post("/api/treasury/payouts", json=new_payout)
            # Should return 409 Conflict for duplicate
            assert response.status_code in [409, 422]  # 422 for validation, 409 for duplicate


class TestTreasuryEndpoints:
    """Tests for treasury balance endpoints."""
    
    def test_get_treasury_stats(self):
        """Test getting treasury statistics."""
        response = client.get("/api/treasury")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "total_payouts_sol" in data
        assert "total_buybacks_sol" in data
        assert "payout_count" in data
        assert "buyback_count" in data
        assert "last_updated" in data
    
    def test_get_treasury_balance(self):
        """Test getting treasury balance."""
        response = client.get("/api/treasury/balance")
        assert response.status_code == 200
        data = response.json()
        assert "sol_balance" in data
        assert "fndry_balance" in data
        assert "last_updated" in data
    
    def test_get_treasury_summary(self):
        """Test getting treasury summary."""
        response = client.get("/api/treasury/summary")
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        assert "statistics" in data
        assert "tokenomics" in data
        assert "recent_payouts" in data
        assert "recent_buybacks" in data


class TestBuybackEndpoints:
    """Tests for buyback endpoints."""
    
    def test_list_buybacks(self):
        """Test listing buybacks."""
        response = client.get("/api/treasury/buybacks")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "skip" in data
        assert "limit" in data
    
    def test_list_buybacks_pagination(self):
        """Test buyback pagination."""
        response = client.get("/api/treasury/buybacks?skip=0&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["skip"] == 0
        assert data["limit"] == 5
    
    def test_create_buyback(self):
        """Test creating a new buyback."""
        import time
        # Generate a tx_hash with at least 80 characters
        unique_part = str(int(time.time() * 1000))
        padding = "x" * (80 - len("test_buyback_tx_hash_") - len(unique_part) - 1)
        tx_hash = "test_buyback_tx_hash_" + unique_part + "_" + padding
        new_buyback = {
            "tx_hash": tx_hash,
            "amount": "5.0",
            "token_amount": "25000",
            "price_per_token": "0.0002",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        response = client.post("/api/treasury/buybacks", json=new_buyback)
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == "5.0"
        assert "solscan_url" in data


class TestTokenomicsEndpoints:
    """Tests for tokenomics endpoints."""
    
    def test_get_tokenomics(self):
        """Test getting tokenomics data."""
        response = client.get("/api/treasury/tokenomics")
        assert response.status_code == 200
        data = response.json()
        assert "supply" in data
        assert "allocation" in data
        assert "fees" in data
        assert "last_updated" in data
        
        # Check supply fields
        assert "total" in data["supply"]
        assert "circulating" in data["supply"]
        assert "treasury" in data["supply"]
        assert "burned" in data["supply"]
        
        # Check allocation fields
        assert "team" in data["allocation"]
        assert "community" in data["allocation"]
        assert "rewards_pool" in data["allocation"]
    
    def test_update_tokenomics_no_data(self):
        """Test updating tokenomics with no data."""
        response = client.patch("/api/treasury/tokenomics")
        assert response.status_code == 400


class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# Async tests for Solana service (requires network)
@pytest.mark.asyncio
async def test_solana_service_initialization():
    """Test Solana service can be initialized."""
    from app.services.solana_service import SolanaService
    
    service = SolanaService()
    assert service.rpc_url is not None
    
    await service.close()


@pytest.mark.asyncio
async def test_get_treasury_service():
    """Test treasury service singleton."""
    from app.services.treasury_service import get_treasury_service
    
    service = get_treasury_service()
    assert service is not None
    
    # Test list_payouts
    result = service.list_payouts()
    assert result is not None
    assert hasattr(result, "items")
    assert hasattr(result, "total")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])