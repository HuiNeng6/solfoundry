"""Solana RPC service for treasury balance and transaction queries."""

import os
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, Any

import httpx


# Treasury wallet address
TREASURY_WALLET = os.getenv("TREASURY_WALLET", "Amu1YJjcKWKL6xuMTo2dx511kfzXAxgpetJrZp7N71o7")
FNDRY_TOKEN_MINT = os.getenv("FNDRY_TOKEN_MINT", "")

# Solana RPC endpoints
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

# Cache settings
CACHE_TTL = 60  # 60 seconds cache

# Simple in-memory cache
_cache: Dict[str, Any] = {}
_cache_timestamps: Dict[str, datetime] = {}


def _get_cached(key: str) -> Optional[Any]:
    """Get value from cache if not expired."""
    if key in _cache and key in _cache_timestamps:
        elapsed = (datetime.now(timezone.utc) - _cache_timestamps[key]).total_seconds()
        if elapsed < CACHE_TTL:
            return _cache[key]
    return None


def _set_cache(key: str, value: Any):
    """Set value in cache."""
    _cache[key] = value
    _cache_timestamps[key] = datetime.now(timezone.utc)


class SolanaService:
    """Service for interacting with Solana blockchain."""
    
    def __init__(self, rpc_url: str = SOLANA_RPC_URL):
        self.rpc_url = rpc_url
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for external APIs."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self):
        """Close all clients."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def get_sol_balance(self, wallet_address: str = TREASURY_WALLET) -> Decimal:
        """Get SOL balance for a wallet address via RPC."""
        cache_key = f"sol_balance_{wallet_address}"
        cached = _get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            client = await self._get_http_client()
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getBalance",
                    "params": [wallet_address, {"commitment": "confirmed"}]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and "value" in data["result"]:
                    balance = Decimal(str(data["result"]["value"])) / Decimal("1_000_000_000")
                    _set_cache(cache_key, balance)
                    return balance
            return Decimal("0")
        except Exception as e:
            print(f"Error fetching SOL balance: {e}")
            return Decimal("0")
    
    async def get_token_balance(
        self, 
        wallet_address: str = TREASURY_WALLET,
        token_mint: str = FNDRY_TOKEN_MINT
    ) -> Decimal:
        """Get SPL token balance for a wallet."""
        if not token_mint:
            return Decimal("0")
        
        cache_key = f"token_balance_{wallet_address}_{token_mint}"
        cached = _get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            client = await self._get_http_client()
            response = await client.post(
                self.rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTokenAccountsByOwner",
                    "params": [
                        wallet_address,
                        {"mint": token_mint},
                        {"encoding": "jsonParsed"}
                    ]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "result" in data and data["result"]["value"]:
                    total_balance = Decimal("0")
                    for account in data["result"]["value"]:
                        token_amount = account["account"]["data"]["parsed"]["info"]["tokenAmount"]
                        amount = Decimal(token_amount["amount"])
                        decimals = token_amount.get("decimals", 0)
                        if decimals > 0:
                            total_balance += amount / (Decimal("10") ** decimals)
                        else:
                            total_balance += amount
                    _set_cache(cache_key, total_balance)
                    return total_balance
            return Decimal("0")
        except Exception as e:
            print(f"Error fetching token balance: {e}")
            return Decimal("0")
    
    async def get_sol_price_usd(self) -> Optional[Decimal]:
        """Get current SOL price in USD from external API."""
        cache_key = "sol_price_usd"
        cached = _get_cached(cache_key)
        if cached is not None:
            return cached
        
        try:
            client = await self._get_http_client()
            response = await client.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": "solana", "vs_currencies": "usd"}
            )
            if response.status_code == 200:
                data = response.json()
                price = Decimal(str(data.get("solana", {}).get("usd", 0)))
                _set_cache(cache_key, price)
                return price
            return None
        except Exception as e:
            print(f"Error fetching SOL price: {e}")
            return None
    
    async def get_treasury_balance(self) -> Dict[str, Any]:
        """Get complete treasury balance information."""
        sol_balance = await self.get_sol_balance()
        fndry_balance = await self.get_token_balance()
        sol_price = await self.get_sol_price_usd()
        
        result = {
            "sol_balance": sol_balance,
            "fndry_balance": fndry_balance,
            "sol_usd_value": None,
            "fndry_usd_value": None,
            "last_updated": datetime.now(timezone.utc)
        }
        
        if sol_price:
            result["sol_usd_value"] = sol_balance * sol_price
        
        return result


# Singleton instance
_solana_service: Optional[SolanaService] = None


async def get_solana_service() -> SolanaService:
    """Get or create SolanaService singleton."""
    global _solana_service
    if _solana_service is None:
        _solana_service = SolanaService()
    return _solana_service


async def close_solana_service():
    """Close SolanaService singleton."""
    global _solana_service
    if _solana_service:
        await _solana_service.close()
        _solana_service = None