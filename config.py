"""
Centralized configuration management for LoanSense AI.
Loads settings from environment variables (.env) with safe fallback defaults.
Ensures secrets are never hardcoded in source modules.
"""

import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent

# Load .env file from project root if it exists
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

# ------------------------------------------------------------------------------
# Database Settings
# ------------------------------------------------------------------------------
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
DB_USER: str = os.getenv("DB_USER", "root")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_NAME: str = os.getenv("DB_NAME", "loaniq_db")

# Optional dedicated read-only MySQL credentials for AI SQL Assistant
DB_READONLY_USER: str = os.getenv("DB_READONLY_USER", "")
DB_READONLY_PASSWORD: str = os.getenv("DB_READONLY_PASSWORD", "")

# ------------------------------------------------------------------------------
# Security, JWT & CORS Settings
# ------------------------------------------------------------------------------
JWT_SECRET: str = os.getenv("JWT_SECRET") or secrets.token_hex(32)
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000"
    ).split(",")
    if origin.strip()
]

# ------------------------------------------------------------------------------
# Gemini API Settings
# ------------------------------------------------------------------------------
GEMINI_API_KEY: str | None = os.getenv("GEMINI_API_KEY")

# ------------------------------------------------------------------------------
# Application Settings
# ------------------------------------------------------------------------------
STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def get_db_config() -> dict:
    """
    Returns a dictionary of MySQL connection parameters.
    Ensures safe retrieval across all database-accessing modules.
    """
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
    }


def get_readonly_db_config() -> dict:
    """
    Returns MySQL connection parameters using dedicated read-only credentials when configured,
    falling back to the primary DB configuration otherwise.
    """
    cfg = get_db_config()
    if DB_READONLY_USER:
        cfg["user"] = DB_READONLY_USER
        cfg["password"] = DB_READONLY_PASSWORD
    return cfg


def get_masked_db_config() -> dict:
    """
    Returns the database configuration with the password masked for logging and diagnostics.
    """
    config = get_db_config()
    if config["password"]:
        config["password"] = "******"
    return config
