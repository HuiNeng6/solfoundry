"""Treasury service for fee collection and distribution.

This module handles:
- Calculating platform fees from bounty rewards
- Collecting fees into the treasury
- Distributing fees according to defined rules
- Tracking treasury balances
"""

import logging
from typing import Optional, List, Tuple, Dict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, update

from app.models.treasury import (
    FeeTransactionDB, FeeDistributionDB, TreasuryBalanceDB, TreasuryWalletDB,
    FeeType, DistributionCategory, DISTRIBUTION_RULES,
    PLATFORM_FEE_PERCENTAGE, MIN_FEE_AMOUNT,
    FeeCalculationResponse, FeeTransactionResponse, TreasuryStatsResponse,
    FeeTransactionListResponse, DistributionRuleResponse, DistributionRulesResponse,
)

logger = logging.getLogger(__name__)


class TreasuryService:
    """Service for managing platform fees and treasury operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def calculate_fee(self, gross_amount: float, fee_percentage: float = PLATFORM_FEE_PERCENTAGE) -> Tuple[float, float]:
        """
        Calculate platform fee and net amount.
        
        Args:
            gross_amount: Original bounty reward amount
            fee_percentage: Fee percentage (default 5%)
        
        Returns:
            Tuple of (fee_amount, net_amount)
        """
        # Use Decimal for precise financial calculations
        gross_decimal = Decimal(str(gross_amount))
        fee_decimal = Decimal(str(fee_percentage))
        
        fee_amount = float((gross_decimal * fee_decimal).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
        net_amount = float((gross_decimal - Decimal(str(fee_amount))).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP))
        
        # Don't collect dust (very small amounts)
        if fee_amount < MIN_FEE_AMOUNT:
            fee_amount = 0.0
            net_amount = gross_amount
        
        return fee_amount, net_amount
    
    async def collect_fee(
        self,
        bounty_id: str,
        submission_id: str,
        contributor_id: str,
        gross_amount: float,
        token: str = "FNDRY",
        fee_type: FeeType = FeeType.BOUNTY_COMPLETION,
    ) -> Tuple[FeeTransactionDB, Dict[str, FeeDistributionDB]]:
        """
        Collect platform fee from a bounty reward.
        
        Args:
            bounty_id: UUID of the bounty
            submission_id: UUID of the submission
            contributor_id: UUID of the contributor receiving payment
            gross_amount: Original bounty reward amount
            token: Token symbol (default FNDRY)
            fee_type: Type of fee (default bounty completion)
        
        Returns:
            Tuple of (FeeTransactionDB, Dict of category -> FeeDistributionDB)
        """
        fee_amount, net_amount = self.calculate_fee(gross_amount)
        
        # Create fee transaction record
        fee_transaction = FeeTransactionDB(
            bounty_id=bounty_id,
            submission_id=submission_id,
            contributor_id=contributor_id,
            fee_type=fee_type.value,
            gross_amount=gross_amount,
            fee_amount=fee_amount,
            net_amount=net_amount,
            token=token,
            status="collected",
            processed_at=datetime.now(timezone.utc),
        )
        self.db.add(fee_transaction)
        
        # Create distribution records
        distributions = {}
        if fee_amount > 0:
            for category, percentage in DISTRIBUTION_RULES.items():
                distribution_amount = float(
                    (Decimal(str(fee_amount)) * Decimal(str(percentage)) / 100).quantize(
                        Decimal('0.0001'), rounding=ROUND_HALF_UP
                    )
                )
                
                distribution = FeeDistributionDB(
                    fee_transaction_id=fee_transaction.id,
                    category=category.value,
                    percentage=percentage,
                    amount=distribution_amount,
                    status="pending",
                )
                self.db.add(distribution)
                distributions[category.value] = distribution
                
                # Update treasury balance
                await self._update_treasury_balance(category.value, distribution_amount, token)
        
        await self.db.commit()
        await self.db.refresh(fee_transaction)
        
        logger.info(f"Collected fee: {fee_amount} {token} from bounty {bounty_id}")
        
        return fee_transaction, distributions
    
    async def _update_treasury_balance(self, category: str, amount: float, token: str) -> None:
        """Update treasury balance for a category."""
        # Try to get existing balance record
        query = select(TreasuryBalanceDB).where(TreasuryBalanceDB.category == category)
        result = await self.db.execute(query)
        balance = result.scalar_one_or_none()
        
        if balance:
            balance.total_collected = float(Decimal(str(balance.total_collected)) + Decimal(str(amount)))
            balance.current_balance = float(Decimal(str(balance.current_balance)) + Decimal(str(amount)))
        else:
            # Create new balance record
            balance = TreasuryBalanceDB(
                category=category,
                total_collected=amount,
                current_balance=amount,
                token=token,
            )
            self.db.add(balance)
    
    async def get_treasury_stats(self) -> TreasuryStatsResponse:
        """Get treasury statistics."""
        # Total fees collected
        total_query = select(func.sum(FeeTransactionDB.fee_amount)).where(
            FeeTransactionDB.status == "collected"
        )
        total_result = await self.db.execute(total_query)
        total_collected = float(total_result.scalar() or 0)
        
        # Total distributed
        dist_query = select(func.sum(FeeDistributionDB.amount)).where(
            FeeDistributionDB.status == "distributed"
        )
        dist_result = await self.db.execute(dist_query)
        total_distributed = float(dist_result.scalar() or 0)
        
        # Current balance
        balance_query = select(func.sum(TreasuryBalanceDB.current_balance))
        balance_result = await self.db.execute(balance_query)
        current_balance = float(balance_result.scalar() or 0)
        
        # Pending distributions
        pending_query = select(func.count(FeeDistributionDB.id)).where(
            FeeDistributionDB.status == "pending"
        )
        pending_result = await self.db.execute(pending_query)
        pending_count = pending_result.scalar() or 0
        
        # Distribution by category
        cat_query = select(
            TreasuryBalanceDB.category,
            TreasuryBalanceDB.total_collected,
            TreasuryBalanceDB.current_balance
        )
        cat_result = await self.db.execute(cat_query)
        distribution_by_category = {}
        for row in cat_result:
            distribution_by_category[row[0]] = {
                "total_collected": float(row[1]),
                "current_balance": float(row[2]),
            }
        
        return TreasuryStatsResponse(
            total_fees_collected=total_collected,
            total_fees_distributed=total_distributed,
            current_treasury_balance=current_balance,
            pending_distributions=pending_count,
            distribution_by_category=distribution_by_category,
        )
    
    async def list_fee_transactions(
        self,
        bounty_id: Optional[str] = None,
        contributor_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> FeeTransactionListResponse:
        """List fee transactions with filtering."""
        query = select(FeeTransactionDB)
        count_query = select(func.count(FeeTransactionDB.id))
        
        conditions = []
        if bounty_id:
            conditions.append(FeeTransactionDB.bounty_id == bounty_id)
        if contributor_id:
            conditions.append(FeeTransactionDB.contributor_id == contributor_id)
        if status:
            conditions.append(FeeTransactionDB.status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))
        
        query = query.order_by(FeeTransactionDB.created_at.desc()).offset(skip).limit(limit)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        result = await self.db.execute(query)
        transactions = result.scalars().all()
        
        return FeeTransactionListResponse(
            items=[FeeTransactionResponse.model_validate(t) for t in transactions],
            total=total,
            skip=skip,
            limit=limit,
        )
    
    async def get_fee_transaction(self, transaction_id: str) -> Optional[FeeTransactionDB]:
        """Get a single fee transaction."""
        query = select(FeeTransactionDB).where(FeeTransactionDB.id == transaction_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    def get_distribution_rules(self) -> DistributionRulesResponse:
        """Get current distribution rules."""
        rules = []
        for category, percentage in DISTRIBUTION_RULES.items():
            description = self._get_category_description(category)
            rules.append(DistributionRuleResponse(
                category=category.value,
                percentage=percentage,
                description=description,
            ))
        
        return DistributionRulesResponse(
            rules=rules,
            total_percentage=sum(DISTRIBUTION_RULES.values()),
        )
    
    def _get_category_description(self, category: DistributionCategory) -> str:
        """Get human-readable description for a category."""
        descriptions = {
            DistributionCategory.PLATFORM_DEVELOPMENT: "Fund for ongoing platform development and improvements",
            DistributionCategory.COMMUNITY_REWARDS: "Rewards for active community members and contributors",
            DistributionCategory.OPERATIONAL_COSTS: "Server, infrastructure, and operational expenses",
            DistributionCategory.TREASURY_RESERVE: "Emergency reserve for unexpected expenses",
        }
        return descriptions.get(category, "Unknown category")
    
    async def create_treasury_wallet(
        self,
        wallet_address: str,
        name: str,
        description: Optional[str] = None,
    ) -> TreasuryWalletDB:
        """Create a new treasury wallet."""
        wallet = TreasuryWalletDB(
            wallet_address=wallet_address,
            name=name,
            description=description,
            is_active=1,
        )
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet
    
    async def list_treasury_wallets(self, active_only: bool = True) -> List[TreasuryWalletDB]:
        """List treasury wallets."""
        query = select(TreasuryWalletDB)
        if active_only:
            query = query.where(TreasuryWalletDB.is_active == 1)
        query = query.order_by(TreasuryWalletDB.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def distribute_pending_fees(self, category: Optional[str] = None) -> int:
        """
        Distribute pending fees to treasury wallets.
        
        In a real implementation, this would:
        1. Call Solana smart contract to transfer tokens
        2. Update distribution status
        3. Record transaction hashes
        
        For now, we just mark them as distributed.
        
        Returns:
            Number of distributions processed
        """
        query = select(FeeDistributionDB).where(FeeDistributionDB.status == "pending")
        if category:
            query = query.where(FeeDistributionDB.category == category)
        
        result = await self.db.execute(query)
        pending = result.scalars().all()
        
        count = 0
        for distribution in pending:
            # In production: call Solana transfer
            distribution.status = "distributed"
            distribution.distributed_at = datetime.now(timezone.utc)
            # distribution.tx_hash = await self._transfer_on_solana(...)
            count += 1
        
        # Update treasury balances
        if count > 0:
            await self._update_distributed_balances()
        
        await self.db.commit()
        return count
    
    async def _update_distributed_balances(self) -> None:
        """Update treasury balances after distribution."""
        query = select(TreasuryBalanceDB)
        result = await self.db.execute(query)
        balances = result.scalars().all()
        
        for balance in balances:
            # Calculate total distributed for this category
            dist_query = select(func.sum(FeeDistributionDB.amount)).where(
                and_(
                    FeeDistributionDB.category == balance.category,
                    FeeDistributionDB.status == "distributed",
                )
            )
            dist_result = await self.db.execute(dist_query)
            total_distributed = float(dist_result.scalar() or 0)
            
            balance.total_distributed = total_distributed
            balance.current_balance = float(
                Decimal(str(balance.total_collected)) - Decimal(str(total_distributed))
            )