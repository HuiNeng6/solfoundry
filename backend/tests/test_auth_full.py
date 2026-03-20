"""Tests for auth service."""

import pytest, base64
from datetime import datetime, timezone, timedelta

class TestOAuth:
    def test_state_gen(self):
        from app.services.auth_service import generate_code_verifier, generate_code_challenge
        v, c = generate_code_verifier(), generate_code_challenge(generate_code_verifier())
        assert v and c

class TestTokens:
    def test_access(self):
        from app.services.auth_service import create_access_token, decode_token
        t = create_access_token("u1")
        assert decode_token(t, "access") == "u1"

class TestWallet:
    def test_invalid_addr(self):
        from app.services.auth_service import verify_wallet_signature, WalletVerificationError
        with pytest.raises(WalletVerificationError): verify_wallet_signature("x", "m", "s")

if __name__ == "__main__": pytest.main([__file__, "-v"])