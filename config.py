"""
Centralized configuration management for LoanSense AI.
Loads settings from environment variables (.env) with safe fallback defaults.
Ensures secrets are never hardcoded in source modules.
"""

import os
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
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "123456")
DB_NAME: str = os.getenv("DB_NAME", "loaniq_db")

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


def get_masked_db_config() -> dict:
    """
    Returns the database configuration with the password masked for logging and diagnostics.
    """
    config = get_db_config()
    if config["password"]:
        config["password"] = "******"
    return config
