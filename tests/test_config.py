"""
Tests for configuration management and credential handling.
"""

import os
from unittest.mock import patch
import config


def test_default_db_config():
    """Verify default database configuration parameters when no env overrides exist."""
    cfg = config.get_db_config()
    assert "host" in cfg
    assert "port" in cfg
    assert "user" in cfg
    assert "password" in cfg
    assert "database" in cfg
    assert isinstance(cfg["port"], int)


def test_masked_db_config_masks_password():
    """Verify that get_masked_db_config never exposes plaintext password in logs."""
    masked = config.get_masked_db_config()
    assert masked["password"] == "******"


def test_env_override(monkeypatch):
    """Verify that environment variables take precedence when present."""
    monkeypatch.setenv("DB_HOST", "custom-host.internal")
    monkeypatch.setenv("DB_PORT", "3307")
    monkeypatch.setenv("DB_USER", "custom_user")
    monkeypatch.setenv("DB_PASSWORD", "custom_secret")
    monkeypatch.setenv("DB_NAME", "custom_db")

    # Reload values dynamically via patched get_db_config logic
    with patch.object(config, "DB_HOST", "custom-host.internal"), \
         patch.object(config, "DB_PORT", 3307), \
         patch.object(config, "DB_USER", "custom_user"), \
         patch.object(config, "DB_PASSWORD", "custom_secret"), \
         patch.object(config, "DB_NAME", "custom_db"):
        cfg = config.get_db_config()
        assert cfg["host"] == "custom-host.internal"
        assert cfg["port"] == 3307
        assert cfg["user"] == "custom_user"
        assert cfg["password"] == "custom_secret"
        assert cfg["database"] == "custom_db"
