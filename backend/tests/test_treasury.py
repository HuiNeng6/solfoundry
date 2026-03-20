"""Tests for Treasury Fee Collection and Distribution system.

Tests cover:
- Fee calculation (5% platform fee)
- Fee collection from bounty payouts
- Treasury balance tracking
- Fee distribution to categories
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.treasury import (
    FeeTransactionDB, FeeDistributionDB, TreasuryBalanceDB, TreasuryWalletDB,
    FeeType, DistributionCategory, DISTRIBUTION_RULES,
    PLATFORM_FEE_PERCENTAGE, MIN_FEE_AMOUNT,
    FeeCalculationRequest, FeeCalculationResponse,
)
from app.services.treasury_service import TreasuryService


class TestFeeCalculation:
    """Test fee calculation logic."""
    
    def test_calculate_fee_standard(self):
        """Test standard 5% fee calculation."""
        service = TreasuryService(db=None)
        
        # Test various amounts
        test_cases = [
            (100.0, 5.0, 95.0),      # 100 FNDRY -> 5 fee, 95 net
            (50.0, 2.5, 47.5),       # 50 FNDRY -> 2.5 fee, 47.5 net
            (1000.0, 50.0, 950.0),   # 1000 FNDRY -> 50 fee, 950 net
            (10.0, 0.5, 9.5),        # 10 FNDRY -> 0.5 fee, 9.5 net
        ]
        
        for gross, expected_fee, expected_net in test_cases:
            fee, net = service.calculate_fee(gross)
            assert abs(fee - expected_fee) < 0.01, f"Fee mismatch for {gross}: got {fee}, expected {expected_fee}"
            assert abs(net - expected_net) < 0.01, f"Net mismatch for {gross}: got {net}, expected {expected_net}"
    
    def test_calculate_fee_small_amounts(self):
        """Test fee calculation for small amounts (below minimum)."""
        service = TreasuryService(db=None)
        
        # Below minimum fee threshold
        fee, net = service.calculate_fee(0.1)  # 0.1 FNDRY -> 0.005 fee (below MIN_FEE_AMOUNT)
        assert fee == 0.0, "Fee should be 0 for amounts below minimum threshold"
        assert net == 0.1, "Net should equal gross for amounts below minimum"
    
    def test_calculate_fee_precision(self):
        """Test fee calculation precision with Decimal."""
        service = TreasuryService(db=None)
        
        # Test with amounts that could cause floating point errors
        fee, net = service.calculate_fee(33.33)
        expected_fee = 1.6665
        expected_net = 31.6635
        
        assert abs(fee - expected_fee) < 0.001
        assert abs(net - expected_net) < 0.001
    
    def test_calculate_fee_zero(self):
        """Test fee calculation with zero amount."""
        service = TreasuryService(db=None)
        
        fee, net = service.calculate_fee(0.0)
        assert fee == 0.0
        assert net == 0.0
    
    def test_platform_fee_percentage(self):
        """Verify platform fee is exactly 5%."""
        assert PLATFORM_FEE_PERCENTAGE == 0.05, "Platform fee should be 5% (0.05)"


class TestDistributionRules:
    """Test fee distribution rules."""
    
    def test_distribution_rules_total_100_percent(self):
        """Verify distribution rules add up to 100%."""
        total = sum(DISTRIBUTION_RULES.values())
        assert total == 100.0, f"Distribution rules should total 100%, got {total}%"
    
    def test_distribution_rules_categories(self):
        """Verify all required distribution categories exist."""
        required_categories = {
            DistributionCategory.PLATFORM_DEVELOPMENT,
            DistributionCategory.COMMUNITY_REWARDS,
            DistributionCategory.OPERATIONAL_COSTS,
            DistributionCategory.TREASURY_RESERVE,
        }
        
        assert set(DISTRIBUTION_RULES.keys()) == required_categories
    
    def test_distribution_percentages(self):
        """Test distribution percentage calculation."""
        fee_amount = 100.0
        
        expected_distributions = {
            DistributionCategory.PLATFORM_DEVELOPMENT: 40.0,   # 40%
            DistributionCategory.COMMUNITY_REWARDS: 30.0,       # 30%
            DistributionCategory.OPERATIONAL_COSTS: 20.0,       # 20%
            DistributionCategory.TREASURY_RESERVE: 10.0,        # 10%
        }
        
        for category, percentage in DISTRIBUTION_RULES.items():
            distributed = fee_amount * percentage / 100
            expected = expected_distributions[category]
            assert abs(distributed - expected) < 0.01


class TestTreasuryService:
    """Test TreasuryService methods."""
    
    @pytest.mark.asyncio
    async def test_collect_fee(self):
        """Test fee collection from bounty payout."""
        # Mock database session
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()
        
        # Mock the _update_treasury_balance query
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing balance
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = TreasuryService(mock_db)
        
        # Test fee collection
        fee_transaction, distributions = await service.collect_fee(
            bounty_id="test-bounty-id",
            submission_id="test-submission-id",
            contributor_id="test-contributor-id",
            gross_amount=100.0,
            token="FNDRY",
        )
        
        # Verify fee transaction was created
        assert fee_transaction.gross_amount == 100.0
        assert fee_transaction.fee_amount == 5.0
        assert fee_transaction.net_amount == 95.0
        assert fee_transaction.status == "collected"
        
        # Verify distributions were created for all categories
        assert len(distributions) == 4
        
        # Verify database operations were called
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_collect_fee_zero_amount(self):
        """Test fee collection with zero amount."""
        mock_db = AsyncMock()
        service = TreasuryService(mock_db)
        
        fee_transaction, distributions = await service.collect_fee(
            bounty_id="test-bounty-id",
            submission_id="test-submission-id",
            contributor_id="test-contributor-id",
            gross_amount=0.0,
            token="FNDRY",
        )
        
        assert fee_transaction.fee_amount == 0.0
        assert len(distributions) == 0
    
    @pytest.mark.asyncio
    async def test_get_treasury_stats(self):
        """Test treasury statistics retrieval."""
        mock_db = AsyncMock()
        
        # Mock query results
        mock_result = MagicMock()
        mock_result.scalar.return_value = 100.0
        
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = TreasuryService(mock_db)
        stats = await service.get_treasury_stats()
        
        assert stats.total_fees_collected >= 0
        assert stats.current_treasury_balance >= 0
    
    @pytest.mark.asyncio
    async def test_list_fee_transactions(self):
        """Test listing fee transactions with filtering."""
        mock_db = AsyncMock()
        
        # Mock query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        service = TreasuryService(mock_db)
        result = await service.list_fee_transactions(
            bounty_id="test-bounty-id",
            skip=0,
            limit=20,
        )
        
        assert result.total == 0
        assert len(result.items) == 0
    
    def test_get_distribution_rules(self):
        """Test getting distribution rules."""
        service = TreasuryService(None)
        rules = service.get_distribution_rules()
        
        assert len(rules.rules) == 4
        assert rules.total_percentage == 100.0


class TestTreasuryModels:
    """Test Treasury database models."""
    
    def test_fee_transaction_model(self):
        """Test FeeTransactionDB model creation."""
        transaction = FeeTransactionDB(
            bounty_id="test-bounty-id",
            submission_id="test-submission-id",
            contributor_id="test-contributor-id",
            fee_type=FeeType.BOUNTY_COMPLETION.value,
            gross_amount=100.0,
            fee_amount=5.0,
            net_amount=95.0,
            token="FNDRY",
            status="collected",
        )
        
        assert transaction.gross_amount == 100.0
        assert transaction.fee_amount == 5.0
        assert transaction.net_amount == 95.0
        assert transaction.fee_type == "bounty_completion"
    
    def test_fee_distribution_model(self):
        """Test FeeDistributionDB model creation."""
        distribution = FeeDistributionDB(
            fee_transaction_id="test-tx-id",
            category=DistributionCategory.PLATFORM_DEVELOPMENT.value,
            percentage=40.0,
            amount=2.0,
            status="pending",
        )
        
        assert distribution.category == "platform_development"
        assert distribution.percentage == 40.0
        assert distribution.amount == 2.0
    
    def test_treasury_balance_model(self):
        """Test TreasuryBalanceDB model creation."""
        balance = TreasuryBalanceDB(
            category=DistributionCategory.PLATFORM_DEVELOPMENT.value,
            total_collected=100.0,
            total_distributed=50.0,
            current_balance=50.0,
            token="FNDRY",
        )
        
        assert balance.category == "platform_development"
        assert balance.current_balance == 50.0
    
    def test_treasury_wallet_model(self):
        """Test TreasuryWalletDB model creation."""
        wallet = TreasuryWalletDB(
            wallet_address="Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7",
            name="Main Treasury Wallet",
            description="Primary treasury wallet for platform fees",
            is_active=1,
        )
        
        assert wallet.wallet_address == "Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7"
        assert wallet.name == "Main Treasury Wallet"
        assert wallet.is_active == 1


class TestTreasuryAPI:
    """Test Treasury API endpoints."""
    
    @pytest.mark.asyncio
    async def test_calculate_fee_endpoint(self):
        """Test fee calculation endpoint."""
        from app.api.treasury import calculate_fee
        
        # Create mock request
        request = FeeCalculationRequest(
            bounty_id="test-bounty-id",
            gross_amount=100.0,
            token="FNDRY",
        )
        
        # Mock database
        mock_db = AsyncMock()
        
        response = await calculate_fee(request, mock_db)
        
        assert response.gross_amount == 100.0
        assert response.fee_percentage == 5.0
        assert response.fee_amount == 5.0
        assert response.net_amount == 95.0
        assert response.token == "FNDRY"
        
        # Verify breakdown
        assert response.breakdown["contributor_receives"] == 95.0
        assert response.breakdown["platform_fee"] == 5.0


class TestIntegration:
    """Integration tests for fee collection workflow."""
    
    @pytest.mark.asyncio
    async def test_full_fee_collection_workflow(self):
        """Test complete fee collection workflow from bounty to distribution."""
        # This would be a more comprehensive test with actual database
        # For now, we test the calculation logic
        
        service = TreasuryService(None)
        
        # Simulate bounty reward
        gross_reward = 500.0
        
        # Calculate fee
        fee, net = service.calculate_fee(gross_reward)
        
        assert fee == 25.0, "Fee should be 25 FNDRY (5% of 500)"
        assert net == 475.0, "Net should be 475 FNDRY"
        
        # Calculate distributions
        distributions = {}
        for category, percentage in DISTRIBUTION_RULES.items():
            distributions[category] = fee * percentage / 100
        
        assert distributions[DistributionCategory.PLATFORM_DEVELOPMENT] == 10.0
        assert distributions[DistributionCategory.COMMUNITY_REWARDS] == 7.5
        assert distributions[DistributionCategory.OPERATIONAL_COSTS] == 5.0
        assert distributions[DistributionCategory.TREASURY_RESERVE] == 2.5
        
        # Verify total distributed equals fee
        assert sum(distributions.values()) == fee


# Run tests with: pytest backend/tests/test_treasury.py -v
if __name__ == "__main__":
    pytest.main([__file__, "-v"])