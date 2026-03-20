"""Complete authentication service with:
- PostgreSQL persistence for all state
- OAuth PKCE flow
- Server-issued nonce binding
- Full lifecycle validation
"""

import os, secrets, base64, logging, hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

import httpx
from jose import jwt, JWTError
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from solders.signature import Signature
from solders.pubkey import Pubkey

from app.models.user import User, UserResponse
from app.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

logger = logging.getLogger(__name__)

# Config
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:3000/auth/callback")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


# Database models for auth state
class OAuthState(Base):
    """OAuth state for CSRF protection."""
    __tablename__ = "oauth_states"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=lambda: secrets.token_urlsafe(32))
    state = Column(String(64), unique=True, nullable=False, index=True)
    code_verifier = Column(String(128), nullable=True)  # PKCE
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)


class AuthChallenge(Base):
    """Wallet auth challenge for signature verification."""
    __tablename__ = "auth_challenges"
    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=lambda: secrets.token_urlsafe(32))
    nonce = Column(String(64), unique=True, nullable=False, index=True)
    wallet_address = Column(String(64), nullable=False, index=True)
    message = Column(String(1024), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False)


# Exceptions
class AuthError(Exception): pass
class GitHubOAuthError(AuthError): pass
class WalletVerificationError(AuthError): pass
class TokenExpiredError(AuthError): pass
class InvalidTokenError(AuthError): pass
class InvalidStateError(AuthError): pass
class InvalidNonceError(AuthError): pass


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id), github_id=user.github_id, username=user.username,
        email=user.email, avatar_url=user.avatar_url, wallet_address=user.wallet_address,
        wallet_verified=user.wallet_verified, created_at=user.created_at, updated_at=user.updated_at
    )


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id, "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
        "jti": secrets.token_urlsafe(16)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id, "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
        "jti": secrets.token_urlsafe(16)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str, token_type: str = "access") -> str:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != token_type:
            raise InvalidTokenError(f"Expected {token_type} token")
        if not payload.get("sub"):
            raise InvalidTokenError("Missing subject")
        return payload["sub"]
    except JWTError as e:
        if "expired" in str(e).lower():
            raise TokenExpiredError("Token expired")
        raise InvalidTokenError(f"Invalid token: {e}")


def generate_code_verifier() -> str:
    """Generate PKCE code verifier."""
    return secrets.token_urlsafe(32)


def generate_code_challenge(verifier: str) -> str:
    """Generate PKCE code challenge from verifier."""
    return base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip('=')


async def create_oauth_state(db: AsyncSession) -> Dict[str, str]:
    """Create OAuth state with PKCE for CSRF protection."""
    state = secrets.token_urlsafe(32)
    code_verifier = generate_code_verifier()
    now = datetime.now(timezone.utc)
    
    oauth_state = OAuthState(
        state=state,
        code_verifier=code_verifier,
        expires_at=now + timedelta(minutes=10)
    )
    db.add(oauth_state)
    await db.commit()
    
    return {
        "state": state,
        "code_verifier": code_verifier,
        "code_challenge": generate_code_challenge(code_verifier)
    }


async def verify_oauth_state(db: AsyncSession, state: str) -> Optional[str]:
    """Verify OAuth state and return code_verifier if valid."""
    result = await db.execute(
        select(OAuthState).where(OAuthState.state == state)
    )
    oauth_state = result.scalar_one_or_none()
    
    if not oauth_state:
        raise InvalidStateError("Invalid state")
    
    if datetime.now(timezone.utc) > oauth_state.expires_at:
        await db.execute(delete(OAuthState).where(OAuthState.state == state))
        await db.commit()
        raise InvalidStateError("State expired")
    
    code_verifier = oauth_state.code_verifier
    
    # Delete used state
    await db.execute(delete(OAuthState).where(OAuthState.state == state))
    await db.commit()
    
    return code_verifier


def get_github_authorize_url(state: str, code_challenge: str) -> str:
    """Generate GitHub OAuth URL with PKCE."""
    if not GITHUB_CLIENT_ID:
        raise GitHubOAuthError("GITHUB_CLIENT_ID not configured")
    
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "scope": "read:user user:email",
        "state": state,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }
    
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"https://github.com/login/oauth/authorize?{query}"


async def exchange_github_code(code: str, code_verifier: str) -> Dict[str, Any]:
    """Exchange GitHub code with PKCE verification."""
    if not GITHUB_CLIENT_SECRET:
        raise GitHubOAuthError("GITHUB_CLIENT_SECRET not configured")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Exchange code with PKCE
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
                "code_verifier": code_verifier,  # PKCE verification
            },
            headers={"Accept": "application/json"}
        )
        
        if token_resp.status_code != 200:
            raise GitHubOAuthError(f"Token exchange failed: {token_resp.status_code}")
        
        token_data = token_resp.json()
        
        if "error" in token_data:
            raise GitHubOAuthError(f"OAuth error: {token_data.get('error_description', token_data['error'])}")
        
        access_token = token_data.get("access_token")
        if not access_token:
            raise GitHubOAuthError("No access token")
        
        # Get user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if user_resp.status_code != 200:
            raise GitHubOAuthError("Failed to get user info")
        
        user_data = user_resp.json()
        
        # Get email if not public
        if not user_data.get("email"):
            email_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if email_resp.status_code == 200:
                emails = email_resp.json()
                primary = next((e["email"] for e in emails if e.get("primary")), None)
                user_data["email"] = primary
        
        return user_data


async def github_oauth_login(db: AsyncSession, code: str, state: str) -> Dict[str, Any]:
    """Complete GitHub OAuth with full lifecycle validation."""
    # Verify state and get code_verifier
    code_verifier = await verify_oauth_state(db, state)
    
    # Exchange code
    github_user = await exchange_github_code(code, code_verifier)
    
    github_id = str(github_user["id"])
    
    # Find or create user
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()
    
    now = datetime.now(timezone.utc)
    
    if user:
        user.username = github_user.get("login", user.username)
        user.email = github_user.get("email") or user.email
        user.avatar_url = github_user.get("avatar_url") or user.avatar_url
        user.last_login_at = now
        user.updated_at = now
    else:
        user = User(
            github_id=github_id,
            username=github_user.get("login", ""),
            email=github_user.get("email"),
            avatar_url=github_user.get("avatar_url"),
            last_login_at=now
        )
        db.add(user)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": _user_to_response(user)
    }


async def create_auth_challenge(db: AsyncSession, wallet_address: str) -> Dict[str, Any]:
    """Create server-bound auth challenge for wallet verification."""
    nonce = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)
    
    message = f"""SolFoundry Wallet Authentication

Sign this message to verify wallet ownership.

Wallet: {wallet_address}
Nonce: {nonce}
Issued: {now.isoformat()}
Expires: {expires_at.isoformat()}

⚠️ Only sign if you initiated this request.
This signature proves you own this wallet."""
    
    challenge = AuthChallenge(
        nonce=nonce,
        wallet_address=wallet_address.lower(),
        message=message,
        expires_at=expires_at
    )
    db.add(challenge)
    await db.commit()
    
    return {
        "message": message,
        "nonce": nonce,
        "expires_at": expires_at
    }


async def verify_auth_challenge(db: AsyncSession, nonce: str, wallet_address: str, message: str) -> bool:
    """Verify auth challenge with full validation."""
    result = await db.execute(
        select(AuthChallenge).where(AuthChallenge.nonce == nonce)
    )
    challenge = result.scalar_one_or_none()
    
    if not challenge:
        raise InvalidNonceError("Invalid nonce")
    
    if datetime.now(timezone.utc) > challenge.expires_at:
        await db.execute(delete(AuthChallenge).where(AuthChallenge.nonce == nonce))
        await db.commit()
        raise InvalidNonceError("Challenge expired")
    
    if challenge.wallet_address != wallet_address.lower():
        raise InvalidNonceError("Wallet mismatch")
    
    if challenge.message != message:
        raise InvalidNonceError("Message mismatch")
    
    # Delete used challenge
    await db.execute(delete(AuthChallenge).where(AuthChallenge.nonce == nonce))
    await db.commit()
    
    return True


def verify_wallet_signature(wallet_address: str, message: str, signature: str) -> bool:
    """Verify Solana wallet signature."""
    try:
        if not wallet_address or len(wallet_address) < 32 or len(wallet_address) > 48:
            raise WalletVerificationError("Invalid wallet address")
        
        pubkey = Pubkey.from_string(wallet_address)
        sig_bytes = base64.b64decode(signature)
        
        if len(sig_bytes) != 64:
            raise WalletVerificationError("Invalid signature length")
        
        Signature(sig_bytes).verify(pubkey, message.encode('utf-8'))
        return True
        
    except WalletVerificationError:
        raise
    except Exception as e:
        raise WalletVerificationError(f"Verification failed: {e}")


async def wallet_authenticate(
    db: AsyncSession, 
    wallet_address: str, 
    signature: str, 
    message: str, 
    nonce: str
) -> Dict[str, Any]:
    """Authenticate with wallet signature and challenge verification."""
    # Verify challenge
    await verify_auth_challenge(db, nonce, wallet_address, message)
    
    # Verify signature
    verify_wallet_signature(wallet_address, message, signature)
    
    # Find or create user
    result = await db.execute(
        select(User).where(User.wallet_address == wallet_address.lower())
    )
    user = result.scalar_one_or_none()
    
    now = datetime.now(timezone.utc)
    
    if user:
        user.last_login_at = now
        user.updated_at = now
    else:
        user = User(
            github_id=f"wallet_{wallet_address[:16].lower()}",
            username=f"wallet_{wallet_address[:8].lower()}",
            wallet_address=wallet_address.lower(),
            wallet_verified=True,
            last_login_at=now
        )
        db.add(user)
    
    await db.commit()
    await db.refresh(user)
    
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": _user_to_response(user)
    }


async def refresh_access_token(db: AsyncSession, refresh_token: str) -> Dict[str, Any]:
    """Refresh access token."""
    user_id = decode_token(refresh_token, "refresh")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise InvalidTokenError("User not found")
    
    return {
        "access_token": create_access_token(user_id),
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


async def get_current_user(db: AsyncSession, user_id: str) -> UserResponse:
    """Get current user from database."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise AuthError("User not found")
    
    return _user_to_response(user)