"""Treasury API router for payouts, buybacks, and tokenomics."""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.treasury import (
    PayoutCreate, PayoutResponse, PayoutListResponse,
    BuybackCreate, BuybackResponse, BuybackListResponse,
    TreasuryStats, TokenomicsResponse,
    PayoutType, PayoutStatus
)
from app.services.treasury_service import get_treasury_service

router = APIRouter(prefix="/api/treasury", tags=["treasury"])


# ==================== Payouts Endpoints ====================

@router.get("/payouts", response_model=PayoutListResponse)
async def list_payouts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    recipient_address: Optional[str] = Query(None, description="Filter by recipient wallet address"),
    payout_type: Optional[PayoutType] = Query(None, description="Filter by payout type"),
    status: Optional[PayoutStatus] = Query(None, description="Filter by status"),
    bounty_id: Optional[str] = Query(None, description="Filter by bounty ID"),
):
    """List all payouts with pagination and filtering."""
    service = get_treasury_service()
    return service.list_payouts(
        skip=skip,
        limit=limit,
        recipient_address=recipient_address,
        payout_type=payout_type,
        status=status,
        bounty_id=bounty_id
    )


@router.get("/payouts/{tx_hash}", response_model=PayoutResponse)
async def get_payout(tx_hash: str):
    """Get detailed information about a specific payout."""
    service = get_treasury_service()
    payout = service.get_payout(tx_hash)
    
    if not payout:
        raise HTTPException(
            status_code=404,
            detail=f"Payout with tx_hash '{tx_hash}' not found"
        )
    
    return payout


@router.post("/payouts", response_model=PayoutResponse, status_code=201)
async def create_payout(data: PayoutCreate):
    """Record a new payout."""
    service = get_treasury_service()
    
    existing = service.get_payout(data.tx_hash)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Payout with tx_hash '{data.tx_hash}' already exists"
        )
    
    return service.create_payout(data)


# ==================== Treasury Endpoints ====================

@router.get("", response_model=TreasuryStats)
async def get_treasury_stats():
    """Get real-time treasury statistics."""
    service = get_treasury_service()
    return await service.get_treasury_stats()


@router.get("/balance")
async def get_treasury_balance():
    """Get current treasury wallet balance."""
    from app.services.solana_service import get_solana_service
    
    solana_service = await get_solana_service()
    return await solana_service.get_treasury_balance()


# ==================== Buybacks Endpoints ====================

@router.get("/buybacks", response_model=BuybackListResponse)
async def list_buybacks(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
):
    """List token buyback history."""
    service = get_treasury_service()
    return service.list_buybacks(skip=skip, limit=limit)


@router.post("/buybacks", response_model=BuybackResponse, status_code=201)
async def create_buyback(data: BuybackCreate):
    """Record a new buyback transaction."""
    service = get_treasury_service()
    return service.create_buyback(data)


# ==================== Tokenomics Endpoints ====================

@router.get("/tokenomics", response_model=TokenomicsResponse)
async def get_tokenomics():
    """Get tokenomics statistics and allocation data."""
    service = get_treasury_service()
    return service.get_tokenomics()


@router.patch("/tokenomics")
async def update_tokenomics(
    total_supply: Optional[str] = Query(None),
    circulating_supply: Optional[str] = Query(None),
    treasury_supply: Optional[str] = Query(None),
    burned_supply: Optional[str] = Query(None),
    team_allocation: Optional[str] = Query(None),
    community_allocation: Optional[str] = Query(None),
    rewards_pool: Optional[str] = Query(None),
    total_fees_collected: Optional[str] = Query(None),
):
    """Update tokenomics statistics."""
    from decimal import Decimal
    
    service = get_treasury_service()
    
    data = {}
    if total_supply is not None:
        data["total_supply"] = Decimal(total_supply)
    if circulating_supply is not None:
        data["circulating_supply"] = Decimal(circulating_supply)
    if treasury_supply is not None:
        data["treasury_supply"] = Decimal(treasury_supply)
    if burned_supply is not None:
        data["burned_supply"] = Decimal(burned_supply)
    if team_allocation is not None:
        data["team_allocation"] = Decimal(team_allocation)
    if community_allocation is not None:
        data["community_allocation"] = Decimal(community_allocation)
    if rewards_pool is not None:
        data["rewards_pool"] = Decimal(rewards_pool)
    if total_fees_collected is not None:
        data["total_fees_collected"] = Decimal(total_fees_collected)
    
    if not data:
        raise HTTPException(
            status_code=400,
            detail="At least one field must be provided for update"
        )
    
    service.update_tokenomics(data)
    return {"status": "updated"}


# ==================== Summary Endpoint ====================

@router.get("/summary")
async def get_treasury_summary():
    """Get a comprehensive summary of treasury activity."""
    service = get_treasury_service()
    
    treasury_stats = await service.get_treasury_stats()
    tokenomics = service.get_tokenomics()
    payouts = service.list_payouts(skip=0, limit=5)
    buybacks = service.list_buybacks(skip=0, limit=5)
    
    return {
        "balance": treasury_stats.balance.model_dump(),
        "statistics": {
            "total_payouts_sol": str(treasury_stats.total_payouts_sol),
            "total_payouts_fndry": str(treasury_stats.total_payouts_fndry),
            "total_buybacks_sol": str(treasury_stats.total_buybacks_sol),
            "total_buybacks_fndry": str(treasury_stats.total_buybacks_fndry),
            "payout_count": treasury_stats.payout_count,
            "buyback_count": treasury_stats.buyback_count,
        },
        "tokenomics": tokenomics.model_dump(),
        "recent_payouts": [p.model_dump() for p in payouts.items],
        "recent_buybacks": [b.model_dump() for b in buybacks.items],
        "last_updated": treasury_stats.last_updated.isoformat(),
    }