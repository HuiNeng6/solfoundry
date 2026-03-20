"""Treasury database and Pydantic models for fee collection and distribution.

This module implements the fee collection system for SolFoundry:
- 5% fee deduction from bounty rewards
- Treasury pool for collected fees
- Fee distribution rules for platform operations
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Float, Integer, Text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


# Fee configuration
PLATFORM_FEE_PERCENTAGE = 0.05  # 5% platform fee
MIN_FEE_AMOUNT = 0.01  # Minimum fee to collect (avoid dust)


class FeeType(str, Enum):
    """Types of fees collected."""
    BOUNTY_COMPLETION = "bounty_completion"
    DISPUTE_RESOLUTION = "dispute_resolution"
    EXPEDITED_PAYOUT = "expedited_payout"


class DistributionCategory(str, Enum):
    """Categories for fee distribution."""
    PLATFORM_DEVELOPMENT = "platform_development"
    COMMUNITY_REWARDS = "community_rewards"
    OPERATIONAL_COSTS = "operational_costs"
    TREASURY_RESERVE = "treasury_reserve"


class TreasuryWalletDB(Base):
    """Treasury wallet for holding platform fees."""
    __tablename__ = "treasury_wallets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wallet_address = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FeeTransactionDB(Base):
    """Record of all fee transactions."""
    __tablename__ = "fee_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bounty_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    submission_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    contributor_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    fee_type = Column(String(50), nullable=False, default=FeeType.BOUNTY_COMPLETION.value)
    gross_amount = Column(Float, nullable=False)  # Original bounty amount
    fee_amount = Column(Float, nullable=False)    # Fee deducted (5%)
    net_amount = Column(Float, nullable=False)    # Amount paid to contributor
    token = Column(String(20), nullable=False, default="FNDRY")
    status = Column(String(20), nullable=False, default="pending")
    treasury_wallet_id = Column(UUID(as_uuid=True), ForeignKey("treasury_wallets.id"), nullable=True)
    tx_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_fee_transactions_status', status),
        Index('ix_fee_transactions_created', created_at),
        Index('ix_fee_transactions_type', fee_type),
    )


class FeeDistributionDB(Base):
    """Record of fee distributions to different categories."""
    __tablename__ = "fee_distributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fee_transaction_id = Column(UUID(as_uuid=True), ForeignKey("fee_transactions.id"), nullable=False)
    category = Column(String(50), nullable=False)
    percentage = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    recipient_wallet = Column(String(64), nullable=True)
    tx_hash = Column(String(128), nullable=True)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    distributed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_fee_distributions_category', category),
        Index('ix_fee_distributions_status', status),
    )


class TreasuryBalanceDB(Base):
    """Treasury balance tracking per category."""
    __tablename__ = "treasury_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(50), unique=True, nullable=False)
    total_collected = Column(Float, nullable=False, default=0.0)
    total_distributed = Column(Float, nullable=False, default=0.0)
    current_balance = Column(Float, nullable=False, default=0.0)
    token = Column(String(20), nullable=False, default="FNDRY")
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


# Distribution rules (configurable percentages)
DISTRIBUTION_RULES = {
    DistributionCategory.PLATFORM_DEVELOPMENT: 40.0,  # 40% for platform development
    DistributionCategory.COMMUNITY_REWARDS: 30.0,     # 30% for community rewards
    DistributionCategory.OPERATIONAL_COSTS: 20.0,     # 20% for operations
    DistributionCategory.TREASURY_RESERVE: 10.0,      # 10% reserve
}


# Pydantic models for API

class FeeCalculationRequest(BaseModel):
    """Request for fee calculation."""
    bounty_id: str
    gross_amount: float = Field(..., ge=0)
    token: str = "FNDRY"


class FeeCalculationResponse(BaseModel):
    """Response with fee breakdown."""
    gross_amount: float
    fee_percentage: float = PLATFORM_FEE_PERCENTAGE * 100
    fee_amount: float
    net_amount: float
    token: str
    breakdown: dict = Field(default_factory=dict)


class TreasuryStatsResponse(BaseModel):
    """Treasury statistics."""
    total_fees_collected: float = 0.0
    total_fees_distributed: float = 0.0
    current_treasury_balance: float = 0.0
    pending_distributions: int = 0
    distribution_by_category: dict = Field(default_factory=dict)


class FeeTransactionResponse(BaseModel):
    """Fee transaction response."""
    id: str
    bounty_id: Optional[str] = None
    submission_id: Optional[str] = None
    contributor_id: Optional[str] = None
    fee_type: str
    gross_amount: float
    fee_amount: float
    net_amount: float
    token: str
    status: str
    tx_hash: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    model_config = {"from_attributes": True}


class FeeTransactionListResponse(BaseModel):
    """Paginated fee transaction list."""
    items: List[FeeTransactionResponse]
    total: int
    skip: int
    limit: int


class DistributionRuleResponse(BaseModel):
    """Distribution rule response."""
    category: str
    percentage: float
    description: str


class DistributionRulesResponse(BaseModel):
    """All distribution rules."""
    rules: List[DistributionRuleResponse]
    total_percentage: float


class UpdateDistributionRuleRequest(BaseModel):
    """Request to update distribution rules."""
    category: str
    percentage: float = Field(..., ge=0, le=100)


class TreasuryWalletCreate(BaseModel):
    """Create treasury wallet request."""
    wallet_address: str = Field(..., min_length=32, max_length=64)
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class TreasuryWalletResponse(BaseModel):
    """Treasury wallet response."""
    id: str
    wallet_address: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}