"""Treasury database and Pydantic models for Payouts, Buybacks, and Tokenomics."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Numeric, Text, Integer, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID

from app.models.contributor import Base


class PayoutStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class PayoutType(str, Enum):
    BOUNTY = "bounty"
    REWARD = "reward"
    REFERRAL = "referral"


class PayoutDB(Base):
    __tablename__ = "payouts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tx_hash = Column(String(100), unique=True, nullable=False, index=True)
    recipient_address = Column(String(100), nullable=False, index=True)
    recipient_username = Column(String(50), nullable=True)
    amount = Column(Numeric(20, 9), nullable=False)  # SOL amount with high precision
    token_amount = Column(Numeric(20, 9), nullable=True)  # FNDRY token amount
    payout_type = Column(SQLEnum(PayoutType), nullable=False, default=PayoutType.BOUNTY)
    bounty_id = Column(String(50), nullable=True)
    bounty_title = Column(String(255), nullable=True)
    status = Column(SQLEnum(PayoutStatus), nullable=False, default=PayoutStatus.COMPLETED)
    block_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class BuybackDB(Base):
    __tablename__ = "buybacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tx_hash = Column(String(100), unique=True, nullable=False, index=True)
    amount = Column(Numeric(20, 9), nullable=False)  # SOL amount spent
    token_amount = Column(Numeric(20, 9), nullable=False)  # FNDRY tokens bought back
    price_per_token = Column(Numeric(20, 9), nullable=False)  # Price in SOL
    block_number = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class TokenomicsDB(Base):
    __tablename__ = "tokenomics_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    total_supply = Column(Numeric(30, 9), nullable=False)
    circulating_supply = Column(Numeric(30, 9), nullable=False)
    treasury_supply = Column(Numeric(30, 9), nullable=False)
    burned_supply = Column(Numeric(30, 9), nullable=False, default=0)
    team_allocation = Column(Numeric(30, 9), nullable=False)
    community_allocation = Column(Numeric(30, 9), nullable=False)
    rewards_pool = Column(Numeric(30, 9), nullable=False)
    total_fees_collected = Column(Numeric(20, 9), nullable=False, default=0)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# Pydantic Models for API

class PayoutBase(BaseModel):
    recipient_address: str = Field(..., min_length=32, max_length=100)
    recipient_username: Optional[str] = None
    amount: Decimal = Field(..., gt=0)
    token_amount: Optional[Decimal] = None
    payout_type: PayoutType = PayoutType.BOUNTY
    bounty_id: Optional[str] = None
    bounty_title: Optional[str] = None


class PayoutCreate(PayoutBase):
    tx_hash: str = Field(..., min_length=80, max_length=100)
    status: PayoutStatus = PayoutStatus.COMPLETED
    block_number: Optional[int] = None
    timestamp: datetime


class PayoutResponse(BaseModel):
    id: str
    tx_hash: str
    recipient_address: str
    recipient_username: Optional[str] = None
    amount: Decimal
    token_amount: Optional[Decimal] = None
    payout_type: PayoutType
    bounty_id: Optional[str] = None
    bounty_title: Optional[str] = None
    status: PayoutStatus
    block_number: Optional[int] = None
    timestamp: datetime
    solscan_url: str = ""
    model_config = {"from_attributes": True}


class PayoutListItem(BaseModel):
    id: str
    tx_hash: str
    recipient_address: str
    recipient_username: Optional[str] = None
    amount: Decimal
    token_amount: Optional[Decimal] = None
    payout_type: PayoutType
    bounty_id: Optional[str] = None
    bounty_title: Optional[str] = None
    status: PayoutStatus
    timestamp: datetime
    model_config = {"from_attributes": True}


class PayoutListResponse(BaseModel):
    items: List[PayoutListItem]
    total: int
    skip: int
    limit: int


class BuybackBase(BaseModel):
    amount: Decimal = Field(..., gt=0)
    token_amount: Decimal = Field(..., gt=0)
    price_per_token: Decimal = Field(..., gt=0)


class BuybackCreate(BuybackBase):
    tx_hash: str = Field(..., min_length=80, max_length=100)
    block_number: Optional[int] = None
    timestamp: datetime


class BuybackResponse(BaseModel):
    id: str
    tx_hash: str
    amount: Decimal
    token_amount: Decimal
    price_per_token: Decimal
    block_number: Optional[int] = None
    timestamp: datetime
    solscan_url: str = ""
    model_config = {"from_attributes": True}


class BuybackListItem(BaseModel):
    id: str
    tx_hash: str
    amount: Decimal
    token_amount: Decimal
    price_per_token: Decimal
    timestamp: datetime
    model_config = {"from_attributes": True}


class BuybackListResponse(BaseModel):
    items: List[BuybackListItem]
    total: int
    skip: int
    limit: int


class TreasuryBalance(BaseModel):
    sol_balance: Decimal = Field(..., description="SOL balance in treasury wallet")
    fndry_balance: Decimal = Field(..., description="FNDRY token balance")
    sol_usd_value: Optional[Decimal] = None
    fndry_usd_value: Optional[Decimal] = None
    last_updated: datetime


class TreasuryStats(BaseModel):
    balance: TreasuryBalance
    total_payouts_sol: Decimal = Field(default=Decimal("0"), description="Total SOL paid out")
    total_payouts_fndry: Decimal = Field(default=Decimal("0"), description="Total FNDRY paid out")
    total_buybacks_sol: Decimal = Field(default=Decimal("0"), description="Total SOL spent on buybacks")
    total_buybacks_fndry: Decimal = Field(default=Decimal("0"), description="Total FNDRY bought back")
    payout_count: int = 0
    buyback_count: int = 0
    last_updated: datetime


class TokenomicsStats(BaseModel):
    total_supply: Decimal
    circulating_supply: Decimal
    treasury_supply: Decimal
    burned_supply: Decimal
    team_allocation: Decimal
    community_allocation: Decimal
    rewards_pool: Decimal
    total_fees_collected: Decimal
    allocation_percentages: dict = {}
    last_updated: datetime


class TokenomicsResponse(BaseModel):
    supply: dict
    allocation: dict
    fees: dict
    last_updated: datetime