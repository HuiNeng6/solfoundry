"""JWT Token Refresh with Rotation.

Implements secure refresh token rotation to prevent token replay attacks.
Each refresh token can only be used once, and a new refresh token is
issued with each access token refresh.

Uses Redis for production token storage to work across multiple workers.
"""

import os
import secrets
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

from jose import jwt, JWTError
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Configuration - fail fast if JWT_SECRET_KEY is not set
_jwt_secret = os.getenv("JWT_SECRET_KEY")
if not _jwt_secret:
    raise ValueError(
        "JWT_SECRET_KEY environment variable is required. "
        "Set it to a secure random value (e.g., from `openssl rand -hex 32`)."
    )
JWT_SECRET_KEY = _jwt_secret

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
REFRESH_TOKEN_FAMILY_SIZE = int(os.getenv("REFRESH_TOKEN_FAMILY_SIZE", "5"))

# Redis key prefixes
RT_PREFIX = "rt:"      # rt:{family_id}:{jti} -> token data
RT_USED_PREFIX = "rt:used:"  # rt:used:{family_id}:{jti} -> "1"


def create_token_family_id(user_id: str) -> str:
    """Create a new token family ID.
    
    A token family groups all refresh tokens issued for a single
    authentication session. If any token in the family is reused
    after being rotated, the entire family is revoked.
    
    Args:
        user_id: The user's ID.
    
    Returns:
        A unique family ID.
    """
    return f"fam_{user_id}_{secrets.token_urlsafe(16)}"


def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
    family_id: Optional[str] = None,
) -> str:
    """Generate a signed JWT access token.
    
    Args:
        user_id: The user's ID.
        expires_delta: Custom expiration time.
        family_id: Token family ID for refresh rotation.
    
    Returns:
        Encoded JWT access token.
    """
    expires_delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": secrets.token_urlsafe(16),
        "fam": family_id,  # Link to refresh token family
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


async def create_refresh_token(
    user_id: str,
    family_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> tuple[str, str]:
    """Generate a signed JWT refresh token with rotation support.
    
    Args:
        user_id: The user's ID.
        family_id: Existing family ID or None to create new.
        expires_delta: Custom expiration time.
    
    Returns:
        Tuple of (encoded JWT refresh token, family_id).
    """
    if not family_id:
        family_id = create_token_family_id(user_id)
    
    expires_delta = expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    now = datetime.now(timezone.utc)
    jti = secrets.token_urlsafe(16)
    
    payload = {
        "sub": user_id,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": jti,  # Unique token ID for rotation tracking
        "fam": family_id,
    }
    
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    # Store token in Redis
    await _store_token_in_family(family_id, jti)
    
    return token, family_id


async def _store_token_in_family(family_id: str, jti: str) -> None:
    """Store a refresh token in its family using Redis.
    
    Args:
        family_id: The token family ID.
        jti: The token's unique ID.
    """
    try:
        redis = await get_redis()
        key = f"{RT_PREFIX}{family_id}:{jti}"
        ttl = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        await redis.setex(key, ttl, "1")
    except Exception as e:
        logger.error(f"Failed to store token in Redis: {e}")
        # Don't fail the request, but log the error


async def _mark_token_used(family_id: str, jti: str) -> bool:
    """Mark a refresh token as used.
    
    Args:
        family_id: The token family ID.
        jti: The token's unique ID.
    
    Returns:
        True if token was successfully marked, False if already used (replay!).
    """
    try:
        redis = await get_redis()
        
        # Check if token exists (hasn't been revoked)
        token_key = f"{RT_PREFIX}{family_id}:{jti}"
        if not await redis.exists(token_key):
            logger.warning(f"Token {jti} in family {family_id} not found - may have been revoked")
            return False
        
        # Get remaining TTL from the token key
        ttl = await redis.ttl(token_key)
        if ttl <= 0:
            ttl = REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        
        # Mark as used with same TTL (atomic SET NX)
        used_key = f"{RT_USED_PREFIX}{family_id}:{jti}"
        result = await redis.set(used_key, "1", ex=ttl, nx=True)
        
        if result is None:
            # Token was already marked as used - replay attack!
            logger.warning(
                f"Refresh token reuse detected for family {family_id}. "
                f"Revoking entire family."
            )
            await _revoke_token_family(family_id)
            return False
        
        return True
    except Exception as e:
        logger.error(f"Failed to mark token as used in Redis: {e}")
        return False


async def _revoke_token_family(family_id: str) -> None:
    """Revoke all tokens in a family.
    
    Called when replay attack is detected or user logs out.
    
    Args:
        family_id: The token family to revoke.
    """
    try:
        redis = await get_redis()
        
        # Find and delete all tokens in the family
        pattern = f"{RT_PREFIX}{family_id}:*"
        used_pattern = f"{RT_USED_PREFIX}{family_id}:*"
        
        keys = await redis.keys(pattern)
        used_keys = await redis.keys(used_pattern)
        
        all_keys = keys + used_keys
        if all_keys:
            await redis.delete(*all_keys)
        
        logger.warning(f"Token family {family_id} revoked")
    except Exception as e:
        logger.error(f"Failed to revoke token family in Redis: {e}")


def decode_token(token: str, token_type: str = "access") -> dict:
    """Decode and validate a JWT token.
    
    Args:
        token: The encoded JWT token.
        token_type: Expected token type ('access' or 'refresh').
    
    Returns:
        Decoded token payload.
    
    Raises:
        TokenExpiredError: Token has expired.
        InvalidTokenError: Token is invalid or wrong type.
    """
    from app.services.auth_service import TokenExpiredError, InvalidTokenError
    
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            raise InvalidTokenError(f"Expected {token_type} token")
        return payload
    except JWTError as e:
        if "expired" in str(e).lower():
            raise TokenExpiredError("Token expired")
        raise InvalidTokenError(f"Invalid token: {e}")


async def refresh_access_token_with_rotation(
    db: AsyncSession,
    refresh_token: str,
) -> dict:
    """Exchange a refresh token for new tokens with rotation.
    
    Implements refresh token rotation:
    1. Validates the refresh token
    2. Checks for replay attacks
    3. Issues new access and refresh tokens
    4. Invalidates the old refresh token
    
    Args:
        db: Database session.
        refresh_token: The refresh token to exchange.
    
    Returns:
        Dict with new access_token, refresh_token, and token_type.
    
    Raises:
        InvalidTokenError: Token is invalid or replay detected.
        TokenExpiredError: Token has expired.
    """
    from app.services.auth_service import InvalidTokenError, TokenExpiredError
    
    # Decode and validate
    payload = decode_token(refresh_token, "refresh")
    user_id = payload.get("sub")
    family_id = payload.get("fam")
    jti = payload.get("jti")
    
    if not user_id or not family_id or not jti:
        raise InvalidTokenError("Invalid token claims")
    
    # Check for replay attack
    if not await _mark_token_used(family_id, jti):
        # Token was already used - revoke entire family
        await _revoke_token_family(family_id)
        raise InvalidTokenError("Refresh token reuse detected. Session revoked for security.")
    
    # Verify user still exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise InvalidTokenError("User not found")
    
    # Generate new tokens with same family
    new_access_token = create_access_token(user_id, family_id=family_id)
    new_refresh_token, _ = await create_refresh_token(user_id, family_id=family_id)
    
    logger.info(f"Token refreshed for user {user_id}, family {family_id}")
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


async def revoke_token_family(family_id: str) -> None:
    """Revoke all tokens in a family (logout all sessions).
    
    Args:
        family_id: The token family to revoke.
    """
    await _revoke_token_family(family_id)
    logger.info(f"Token family {family_id} revoked (logout)")


async def revoke_all_user_sessions(user_id: str) -> None:
    """Revoke all sessions for a user.
    
    Args:
        user_id: The user's ID.
    """
    try:
        redis = await get_redis()
        
        # Find all token families for this user
        # Pattern: rt:fam_{user_id}_*
        pattern = f"{RT_PREFIX}fam_{user_id}_*"
        keys = await redis.keys(pattern)
        
        # Extract unique family IDs and revoke each
        family_ids = set()
        for key in keys:
            # key format: rt:fam_{user_id}_{random}:{jti}
            parts = key.split(":")
            if len(parts) >= 2:
                family_ids.add(parts[1])
        
        for family_id in family_ids:
            await _revoke_token_family(family_id)
        
        logger.info(f"All sessions revoked for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to revoke all user sessions: {e}")