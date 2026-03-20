"""Treasury service for managing payouts, buybacks, and tokenomics data."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict

from app.models.treasury import (
    PayoutDB, BuybackDB, TokenomicsDB,
    PayoutCreate, PayoutResponse, PayoutListItem, PayoutListResponse,
    BuybackCreate, BuybackResponse, BuybackListItem, BuybackListResponse,
    TreasuryBalance, TreasuryStats, TokenomicsResponse,
    PayoutStatus, PayoutType
)


# In-memory storage for demo/development
_payouts_db: List[PayoutDB] = []
_buybacks_db: List[BuybackDB] = []
_tokenomics_db: List[TokenomicsDB] = []
_db_initialized = False


def _init_demo_data():
    """Initialize with demo data for development."""
    global _db_initialized, _payouts_db, _buybacks_db, _tokenomics_db
    
    if _db_initialized:
        return
    
    now = datetime.now(timezone.utc)
    
    demo_payouts = [
        PayoutDB(
            id=uuid.uuid4(),
            tx_hash="5Kq3OvxMPNtJXpYXqFdJtDxFqC6LqP9QzR2wE1vN8xS4yT6kL3mJ7hG2fD8aB1cE5",
            recipient_address="HN7cABqLq46Es1N92m3H2b8f7Y9pQ1aR5wE3sT2gK8dJ6fL4mN0",
            recipient_username="alice_dev",
            amount=Decimal("2.5"),
            token_amount=Decimal("10000"),
            payout_type=PayoutType.BOUNTY,
            bounty_id="BOUNTY-001",
            bounty_title="Implement Treasury API",
            status=PayoutStatus.COMPLETED,
            block_number=123456789,
            timestamp=now
        ),
        PayoutDB(
            id=uuid.uuid4(),
            tx_hash="3Hx9BnpJmKuYwZaRgEcSuDwPeR6MsN4P1yV5uL3fH8aS7tJ2qK5nX9cB4dF6gH2j",
            recipient_address="9Bx2kQpR5sT7vW3yZ6jL4cM8nE1hG0fD2aS5bK7tN3mP6qR9w",
            recipient_username="bob_builder",
            amount=Decimal("1.0"),
            token_amount=Decimal("4000"),
            payout_type=PayoutType.BOUNTY,
            bounty_id="BOUNTY-002",
            bounty_title="Fix Bug in Wallet Integration",
            status=PayoutStatus.COMPLETED,
            block_number=123456790,
            timestamp=now
        ),
    ]
    
    demo_buybacks = [
        BuybackDB(
            id=uuid.uuid4(),
            tx_hash="2Lp5MkNrRiYyX5dCgJvIuHtGzZaE8dR0sL2nO5mQ4jU7vW1xY6zA9bD3hF5gJ7k",
            amount=Decimal("10.0"),
            token_amount=Decimal("50000"),
            price_per_token=Decimal("0.0002"),
            block_number=123456800,
            timestamp=now
        ),
    ]
    
    demo_tokenomics = TokenomicsDB(
        id=uuid.uuid4(),
        total_supply=Decimal("1000000000"),
        circulating_supply=Decimal("500000000"),
        treasury_supply=Decimal("200000000"),
        burned_supply=Decimal("10000000"),
        team_allocation=Decimal("150000000"),
        community_allocation=Decimal("400000000"),
        rewards_pool=Decimal("240000000"),
        total_fees_collected=Decimal("50000"),
        timestamp=now
    )
    
    _payouts_db = demo_payouts
    _buybacks_db = demo_buybacks
    _tokenomics_db = [demo_tokenomics]
    _db_initialized = True


class TreasuryService:
    """Service for treasury operations."""
    
    def __init__(self):
        _init_demo_data()
    
    def list_payouts(
        self,
        skip: int = 0,
        limit: int = 20,
        recipient_address: Optional[str] = None,
        payout_type: Optional[PayoutType] = None,
        status: Optional[PayoutStatus] = None,
        bounty_id: Optional[str] = None
    ) -> PayoutListResponse:
        """List payouts with pagination and filters."""
        filtered = _payouts_db.copy()
        
        if recipient_address:
            filtered = [p for p in filtered if p.recipient_address == recipient_address]
        if payout_type:
            filtered = [p for p in filtered if p.payout_type == payout_type]
        if status:
            filtered = [p for p in filtered if p.status == status]
        if bounty_id:
            filtered = [p for p in filtered if p.bounty_id == bounty_id]
        
        filtered.sort(key=lambda x: x.timestamp, reverse=True)
        
        total = len(filtered)
        items = filtered[skip:skip + limit]
        
        # Convert UUID to string for each item
        return PayoutListResponse(
            items=[PayoutListItem(
                id=str(p.id),
                tx_hash=p.tx_hash,
                recipient_address=p.recipient_address,
                recipient_username=p.recipient_username,
                amount=p.amount,
                token_amount=p.token_amount,
                payout_type=p.payout_type,
                bounty_id=p.bounty_id,
                bounty_title=p.bounty_title,
                status=p.status,
                timestamp=p.timestamp
            ) for p in items],
            total=total,
            skip=skip,
            limit=limit
        )
    
    def get_payout(self, tx_hash: str) -> Optional[PayoutResponse]:
        """Get a single payout by transaction hash."""
        for payout in _payouts_db:
            if payout.tx_hash == tx_hash:
                return PayoutResponse(
                    id=str(payout.id),
                    tx_hash=payout.tx_hash,
                    recipient_address=payout.recipient_address,
                    recipient_username=payout.recipient_username,
                    amount=payout.amount,
                    token_amount=payout.token_amount,
                    payout_type=payout.payout_type,
                    bounty_id=payout.bounty_id,
                    bounty_title=payout.bounty_title,
                    status=payout.status,
                    block_number=payout.block_number,
                    timestamp=payout.timestamp,
                    solscan_url=f"https://solscan.io/tx/{tx_hash}"
                )
        return None
    
    def create_payout(self, data: PayoutCreate) -> PayoutResponse:
        """Create a new payout record."""
        payout = PayoutDB(
            id=uuid.uuid4(),
            tx_hash=data.tx_hash,
            recipient_address=data.recipient_address,
            recipient_username=data.recipient_username,
            amount=data.amount,
            token_amount=data.token_amount,
            payout_type=data.payout_type,
            bounty_id=data.bounty_id,
            bounty_title=data.bounty_title,
            status=data.status,
            block_number=data.block_number,
            timestamp=data.timestamp,
            created_at=datetime.now(timezone.utc)
        )
        
        _payouts_db.append(payout)
        
        return PayoutResponse(
            id=str(payout.id),
            tx_hash=payout.tx_hash,
            recipient_address=payout.recipient_address,
            recipient_username=payout.recipient_username,
            amount=payout.amount,
            token_amount=payout.token_amount,
            payout_type=payout.payout_type,
            bounty_id=payout.bounty_id,
            bounty_title=payout.bounty_title,
            status=payout.status,
            block_number=payout.block_number,
            timestamp=payout.timestamp,
            solscan_url=f"https://solscan.io/tx/{payout.tx_hash}"
        )
    
    def list_buybacks(self, skip: int = 0, limit: int = 20) -> BuybackListResponse:
        """List buybacks with pagination."""
        sorted_buybacks = sorted(_buybacks_db, key=lambda x: x.timestamp, reverse=True)
        
        total = len(sorted_buybacks)
        items = sorted_buybacks[skip:skip + limit]
        
        return BuybackListResponse(
            items=[BuybackListItem(
                id=str(b.id),
                tx_hash=b.tx_hash,
                amount=b.amount,
                token_amount=b.token_amount,
                price_per_token=b.price_per_token,
                timestamp=b.timestamp
            ) for b in items],
            total=total,
            skip=skip,
            limit=limit
        )
    
    def create_buyback(self, data: BuybackCreate) -> BuybackResponse:
        """Create a new buyback record."""
        buyback = BuybackDB(
            id=uuid.uuid4(),
            tx_hash=data.tx_hash,
            amount=data.amount,
            token_amount=data.token_amount,
            price_per_token=data.price_per_token,
            block_number=data.block_number,
            timestamp=data.timestamp,
            created_at=datetime.now(timezone.utc)
        )
        
        _buybacks_db.append(buyback)
        
        return BuybackResponse(
            id=str(buyback.id),
            tx_hash=buyback.tx_hash,
            amount=buyback.amount,
            token_amount=buyback.token_amount,
            price_per_token=buyback.price_per_token,
            block_number=buyback.block_number,
            timestamp=buyback.timestamp,
            solscan_url=f"https://solscan.io/tx/{buyback.tx_hash}"
        )
    
    async def get_treasury_stats(self) -> TreasuryStats:
        """Get comprehensive treasury statistics."""
        from app.services.solana_service import get_solana_service
        solana_service = await get_solana_service()
        balance_data = await solana_service.get_treasury_balance()
        
        total_payouts_sol = sum(p.amount for p in _payouts_db if p.status == PayoutStatus.COMPLETED)
        total_payouts_fndry = sum(p.token_amount or Decimal("0") for p in _payouts_db if p.status == PayoutStatus.COMPLETED)
        total_buybacks_sol = sum(b.amount for b in _buybacks_db)
        total_buybacks_fndry = sum(b.token_amount for b in _buybacks_db)
        
        return TreasuryStats(
            balance=TreasuryBalance(**balance_data),
            total_payouts_sol=total_payouts_sol,
            total_payouts_fndry=total_payouts_fndry,
            total_buybacks_sol=total_buybacks_sol,
            total_buybacks_fndry=total_buybacks_fndry,
            payout_count=len([p for p in _payouts_db if p.status == PayoutStatus.COMPLETED]),
            buyback_count=len(_buybacks_db),
            last_updated=datetime.now(timezone.utc)
        )
    
    def get_tokenomics(self) -> TokenomicsResponse:
        """Get tokenomics statistics."""
        if not _tokenomics_db:
            return TokenomicsResponse(
                supply={"total": "0", "circulating": "0", "treasury": "0", "burned": "0"},
                allocation={"team": "0%", "community": "0%", "rewards_pool": "0%", "treasury": "0%"},
                fees={"total_collected": "0"},
                last_updated=datetime.now(timezone.utc)
            )
        
        latest = _tokenomics_db[-1]
        total_supply = latest.total_supply
        
        team_pct = (latest.team_allocation / total_supply * 100) if total_supply > 0 else Decimal("0")
        community_pct = (latest.community_allocation / total_supply * 100) if total_supply > 0 else Decimal("0")
        rewards_pct = (latest.rewards_pool / total_supply * 100) if total_supply > 0 else Decimal("0")
        treasury_pct = (latest.treasury_supply / total_supply * 100) if total_supply > 0 else Decimal("0")
        
        return TokenomicsResponse(
            supply={
                "total": str(latest.total_supply),
                "circulating": str(latest.circulating_supply),
                "treasury": str(latest.treasury_supply),
                "burned": str(latest.burned_supply)
            },
            allocation={
                "team": f"{team_pct:.2f}%",
                "community": f"{community_pct:.2f}%",
                "rewards_pool": f"{rewards_pct:.2f}%",
                "treasury": f"{treasury_pct:.2f}%"
            },
            fees={"total_collected": str(latest.total_fees_collected)},
            last_updated=latest.timestamp
        )
    
    def update_tokenomics(self, data: Dict[str, Decimal]):
        """Update tokenomics statistics."""
        latest = _tokenomics_db[-1] if _tokenomics_db else None
        
        new_stats = TokenomicsDB(
            id=uuid.uuid4(),
            total_supply=data.get("total_supply", latest.total_supply if latest else Decimal("0")),
            circulating_supply=data.get("circulating_supply", latest.circulating_supply if latest else Decimal("0")),
            treasury_supply=data.get("treasury_supply", latest.treasury_supply if latest else Decimal("0")),
            burned_supply=data.get("burned_supply", latest.burned_supply if latest else Decimal("0")),
            team_allocation=data.get("team_allocation", latest.team_allocation if latest else Decimal("0")),
            community_allocation=data.get("community_allocation", latest.community_allocation if latest else Decimal("0")),
            rewards_pool=data.get("rewards_pool", latest.rewards_pool if latest else Decimal("0")),
            total_fees_collected=data.get("total_fees_collected", latest.total_fees_collected if latest else Decimal("0")),
            timestamp=datetime.now(timezone.utc)
        )
        
        _tokenomics_db.append(new_stats)


# Singleton instance
_treasury_service: Optional[TreasuryService] = None


def get_treasury_service() -> TreasuryService:
    """Get or create TreasuryService singleton."""
    global _treasury_service
    if _treasury_service is None:
        _treasury_service = TreasuryService()
    return _treasury_service