"""
Tests for authentication and role-based access control logic in auth.py.
"""

from unittest.mock import patch
import bcrypt
import pytest
from auth import verify_credentials


@pytest.fixture
def hashed_admin_password():
    return bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")


def test_verify_credentials_empty():
    valid, msg, user = verify_credentials("", "")
    assert not valid
    assert "required" in msg.lower()
    assert user is None


def test_verify_credentials_user_not_found():
    with patch("auth.fetch_all", return_value=[]):
        valid, msg, user = verify_credentials("unknown_user", "password123")
        assert not valid
        assert "not found" in msg.lower() or "invalid" in msg.lower()
        assert user is None


def test_verify_credentials_success(hashed_admin_password):
    mock_user_row = {
        "user_id": 1,
        "username": "admin",
        "password_hash": hashed_admin_password,
        "role": "admin",
    }
    with patch("auth.fetch_all", return_value=[mock_user_row]):
        valid, msg, user = verify_credentials("admin", "admin123", expected_role="admin")
        assert valid
        assert user["username"] == "admin"
        assert user["role"] == "admin"


def test_verify_credentials_wrong_password(hashed_admin_password):
    mock_user_row = {
        "user_id": 1,
        "username": "admin",
        "password_hash": hashed_admin_password,
        "role": "admin",
    }
    with patch("auth.fetch_all", return_value=[mock_user_row]):
        valid, msg, user = verify_credentials("admin", "wrong_pass", expected_role="admin")
        assert not valid
        assert "invalid credentials" in msg.lower()
        assert user is None


def test_verify_credentials_role_mismatch(hashed_admin_password):
    mock_user_row = {
        "user_id": 1,
        "username": "admin",
        "password_hash": hashed_admin_password,
        "role": "admin",
    }
    with patch("auth.fetch_all", return_value=[mock_user_row]):
        # Account is admin, but logging in as viewer
        valid, msg, user = verify_credentials("admin", "admin123", expected_role="viewer")
        assert not valid
        assert "role mismatch" in msg.lower()
        assert user is None
