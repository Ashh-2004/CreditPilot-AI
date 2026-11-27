"""
Authentication and RBAC module for CreditPilot AI.
Provides credential verification with bcrypt, HMAC-SHA256 signed JWT tokens,
and role-based access validation.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Optional, Tuple, Dict, Any
import bcrypt
import config
from db import fetch_all


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(username: str, role: str, expires_in_seconds: int = 86400) -> str:
    """
    Creates an HMAC-SHA256 signed JWT containing username, role, and expiration timestamp.
    """
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode("utf-8"))
    now = int(time.time())
    payload = _b64url_encode(
        json.dumps(
            {"sub": username, "role": role, "iat": now, "exp": now + expires_in_seconds},
            separators=(",", ":")
        ).encode("utf-8")
    )
    signing_input = f"{header}.{payload}".encode("ascii")
    signature = hmac.new(config.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{header}.{payload}.{_b64url_encode(signature)}"


def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies an HMAC-SHA256 signed JWT and returns its claims if valid and unexpired.
    Returns None for invalid, tampered, or expired tokens.
    """
    if not token or token.count(".") != 2:
        return None
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(config.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
        provided_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, provided_sig):
            return None
        claims = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        if int(claims.get("exp", 0)) < int(time.time()):
            return None
        if not claims.get("sub") or not claims.get("role"):
            return None
        return claims
    except Exception:
        return None


def verify_credentials(
    username: str,
    password: str,
    expected_role: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """
    Validates user credentials against the database users table using bcrypt.
    Optionally validates that the user's authentic database role matches the expected role.

    Returns:
        (is_valid, message, user_record_or_None)
    """
    if not username or not password:
        return False, "Username and password are required.", None

    clean_username = username.strip()

    try:
        query = "SELECT user_id, username, password_hash, role FROM users WHERE username = %s"
        rows = fetch_all(query, (clean_username,))
    except Exception as err:
        return False, f"Database authentication error: {err}", None

    if not rows:
        return False, "Invalid credentials or user not found.", None

    user = rows[0]
    stored_hash = user.get("password_hash", "")

    try:
        password_matches = bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8"))
    except Exception:
        return False, "Error validating password hash.", None

    if not password_matches:
        return False, "Invalid credentials.", None

    if expected_role and user.get("role") != expected_role:
        return False, f"Role mismatch: account is registered as '{user.get('role')}', not '{expected_role}'.", None

    return True, "Authentication successful.", user
