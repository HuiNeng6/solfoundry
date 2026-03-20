"""Treasury API endpoints for fee collection and distribution."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.treasury import (
    FeeCalculationRequest,
    FeeCalculationResponse,
    TreasuryStatsResponse,
    FeeTransactionResponse,
    FeeTransactionListResponse,
    DistributionRulesResponse,
    TreasuryWalletCreate,
    TreasuryWalletResponse,
)
from app.services.treasury_service import TreasuryService
from app.database import get_db

router = APIRouter(prefix="/treasury", tags=["treasury"])


@router.post("/calculate-fee", response_model=FeeCalculationResponse)
async def calculate_fee(
    data: FeeCalculationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate platform fee for a bounty reward.
    
    Shows the fee breakdown without actually collecting it.
    """
    service = TreasuryService(db)
    fee_amount, net_amount = service.calculate_fee(data.gross_amount)
    
    return FeeCalculationResponse(
        gross_amount=data.gross_amount,
        fee_percentage=5.0,  # 5%
        fee_amount=fee_amount,
        net_amount=net_amount,
        token=data.token,
        breakdown={
            "contributor_receives": net_amount,
            "platform_fee": fee_amount,
            "treasury_allocation": {
                "platform_development": fee_amount * 0.40,
                "community_rewards": fee_amount * 0.30,
                "operational_costs": fee_amount * 0.20,
                "treasury_reserve": fee_amount * 0.10,
            },
        },
    )


@router.get("/stats", response_model=TreasuryStatsResponse)
async def get_treasury_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get treasury statistics including total fees collected and distribution status."""
    service = TreasuryService(db)
    return await service.get_treasury_stats()


@router.get("/distribution-rules", response_model=DistributionRulesResponse)
async def get_distribution_rules():
    """Get current fee distribution rules and percentages."""
    service = TreasuryService(None)  # No DB needed for rules
    return service.get_distribution_rules()


@router.get("/transactions", response_model=FeeTransactionListResponse)
async def list_fee_transactions(
    bounty_id: Optional[str] = Query(None, description="Filter by bounty ID"),
    contributor_id: Optional[str] = Query(None, description="Filter by contributor ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List fee transactions with filtering and pagination."""
    service = TreasuryService(db)
    return await service.list_fee_transactions(
        bounty_id=bounty_id,
        contributor_id=contributor_id,
        status=status,
        skip=skip,
        limit=limit,
    )


@router.get("/transactions/{transaction_id}", response_model=FeeTransactionResponse)
async def get_fee_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single fee transaction by ID."""
    service = TreasuryService(db)
    transaction = await service.get_fee_transaction(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Fee transaction not found")
    return FeeTransactionResponse.model_validate(transaction)


@router.post("/wallets", response_model=TreasuryWalletResponse, status_code=status.HTTP_201_CREATED)
async def create_treasury_wallet(
    data: TreasuryWalletCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new treasury wallet for receiving platform fees."""
    service = TreasuryService(db)
    wallet = await service.create_treasury_wallet(
        wallet_address=data.wallet_address,
        name=data.name,
        description=data.description,
    )
    return TreasuryWalletResponse.model_validate(wallet)


@router.get("/wallets", response_model=list[TreasuryWalletResponse])
async def list_treasury_wallets(
    active_only: bool = Query(True, description="Only show active wallets"),
    db: AsyncSession = Depends(get_db),
):
    """List all treasury wallets."""
    service = TreasuryService(db)
    wallets = await service.list_treasury_wallets(active_only=active_only)
    return [TreasuryWalletResponse.model_validate(w) for w in wallets]


@router.post("/distribute", response_model=dict)
async def distribute_pending_fees(
    category: Optional[str] = Query(None, description="Distribute only specific category"),
    db: AsyncSession = Depends(get_db),
):
    """
    Distribute pending fees to treasury wallets.
    
    This endpoint triggers the distribution of collected fees
    to their designated treasury wallets.
    """
    service = TreasuryService(db)
    count = await service.distribute_pending_fees(category)
    
    return {
        "status": "success",
        "distributions_processed": count,
        "message": f"Successfully distributed {count} pending fee(s)",
    }


@router.post("/distribute/{category}", response_model=dict)
async def distribute_category_fees(
    category: str,
    db: AsyncSession = Depends(get_db),
):
    """Distribute pending fees for a specific category."""
    service = TreasuryService(db)
    count = await service.distribute_pending_fees(category)
    
    return {
        "status": "success",
        "category": category,
        "distributions_processed": count,
    }