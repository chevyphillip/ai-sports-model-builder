"""Configuration module for the sports model."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [DATA_DIR, MODELS_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "sports_model")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# API configuration
ODDS_API_KEY: Optional[str] = os.getenv("ODDS_API_KEY")
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"

# Discord configuration
DISCORD_TOKEN: Optional[str] = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID: Optional[str] = os.getenv("DISCORD_CHANNEL_ID")

# Model configuration
DEFAULT_MODEL_TYPE = "basic"
MODEL_TYPES = ["basic", "advanced"]
SUPPORTED_SPORTS = ["NBA", "NFL", "NHL"]

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = LOGS_DIR / "sports_model.log"

# API rate limiting
API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", "100"))  # requests per hour
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))  # seconds

# Cache configuration
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds

# Feature flags
ENABLE_ML_MODELS = os.getenv("ENABLE_ML_MODELS", "true").lower() == "true"
ENABLE_DISCORD_BOT = os.getenv("ENABLE_DISCORD_BOT", "false").lower() == "true"


def validate_config() -> None:
    """Validate the configuration settings."""
    required_vars = {
        "DB_PASSWORD": DB_PASSWORD,
        "ODDS_API_KEY": ODDS_API_KEY,
    }

    missing_vars = [var for var, value in required_vars.items() if not value]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    if not all(Path(d).exists() for d in [DATA_DIR, MODELS_DIR, LOGS_DIR]):
        raise ValueError("Required directories do not exist")
