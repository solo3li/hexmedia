import base64
import hashlib
import hmac
import json
import time
from typing import Optional, Dict, Any

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from ninja.security import HttpBearer, django_auth


def _b64url_encode(data: bytes) -> str:
    """Encodes bytes into unpadded Base64URL string according to RFC 7515."""
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('ascii')


def _b64url_decode(s: str) -> bytes:
    """Decodes unpadded or padded Base64URL string into bytes."""
    rem = len(s) % 4
    if rem > 0:
        s += '=' * (4 - rem)
    return base64.urlsafe_b64decode(s.encode('ascii'))


def create_jwt_token(payload: Dict[str, Any], expires_in_seconds: int = 7 * 86400) -> str:
    """
    Creates an RFC-7519 HMAC-SHA256 (HS256) JWT signed with settings.SECRET_KEY.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    header_json = json.dumps(header, separators=(',', ':')).encode('utf-8')
    header_b64 = _b64url_encode(header_json)

    now = int(time.time())
    full_payload = {
        "iat": now,
        "exp": now + expires_in_seconds,
        **payload
    }
    payload_json = json.dumps(full_payload, separators=(',', ':')).encode('utf-8')
    payload_b64 = _b64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
    secret = settings.SECRET_KEY.encode('utf-8')
    signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    signature_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"


def decode_jwt_payload(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates HMAC-SHA256 JWT signature and expiration.
    Returns payload dictionary if valid, or None if invalid or expired.
    """
    try:
        if not token or not isinstance(token, str):
            return None
        parts = token.strip().split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        # Verify header algorithm
        header = json.loads(_b64url_decode(header_b64).decode('utf-8'))
        if header.get("alg") != "HS256":
            return None

        # Verify HMAC-SHA256 signature
        signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
        secret = settings.SECRET_KEY.encode('utf-8')
        expected_sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        # Verify expiration
        payload = json.loads(_b64url_decode(payload_b64).decode('utf-8'))
        exp = payload.get("exp")
        if exp is not None and time.time() > float(exp):
            return None

        return payload
    except Exception:
        return None


def decode_jwt_token(token: str) -> Optional[User]:
    """
    Decodes a Bearer JWT access token and returns the corresponding active User.
    Rejects tokens with token_type != 'access'.
    """
    payload = decode_jwt_payload(token)
    if not payload or "user_id" not in payload:
        return None

    # Refresh tokens must not be accepted for API authentication
    if payload.get("token_type") == "refresh":
        return None

    try:
        user_model = get_user_model()
        return user_model.objects.filter(id=payload["user_id"], is_active=True).first()
    except Exception:
        return None


def generate_tokens_for_user(user: User) -> Dict[str, Any]:
    """
    Generates a pair of access and refresh JWT tokens for an authenticated user.
    """
    access_payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "token_type": "access",
    }
    refresh_payload = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "token_type": "refresh",
    }

    # Access token valid for 7 days, refresh token valid for 30 days
    access_token = create_jwt_token(access_payload, expires_in_seconds=7 * 86400)
    refresh_token = create_jwt_token(refresh_payload, expires_in_seconds=30 * 86400)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }
    }


class JWTAuth(HttpBearer):
    """
    Django Ninja security handler for Bearer JWT authentication.
    Extracts Bearer token from the Authorization header and returns the authenticated User.
    """
    def authenticate(self, request, token: str) -> Optional[User]:
        return decode_jwt_token(token)
