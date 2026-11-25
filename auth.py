"""
Authentication and RBAC module for LoanSense AI.
Provides credential verification with bcrypt and role-based access validation.
"""

from typing import Optional, Tuple, Dict, Any
import bcrypt
from db import fetch_all


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
