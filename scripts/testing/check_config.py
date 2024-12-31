from src.core.logger import logger
from src.core.config import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    ODDS_API_KEY,
)


def check_database_config() -> bool:
    """Check if all required database configuration variables are set."""
    required_vars = {
        "DB_USER": DB_USER,
        "DB_PASSWORD": DB_PASSWORD,
        "DB_HOST": DB_HOST,
        "DB_PORT": DB_PORT,
        "DB_NAME": DB_NAME,
    }

    missing_vars = [name for name, value in required_vars.items() if not value]

    if missing_vars:
        logger.error(
            f"Missing required database configuration variables: {', '.join(missing_vars)}"
        )
        return False

    logger.info("Database configuration variables verified")
    return True


def check_api_config() -> bool:
    """Check if all required API configuration variables are set."""
    if not ODDS_API_KEY:
        logger.error("Missing ODDS_API_KEY configuration")
        return False

    logger.info("API configuration variables verified")
    return True


def check_all_config() -> bool:
    """Check all configuration variables."""
    db_config_ok = check_database_config()
    api_config_ok = check_api_config()

    if not (db_config_ok and api_config_ok):
        logger.error("Configuration check failed")
        return False

    logger.info("All configuration checks passed")
    return True


if __name__ == "__main__":
    import sys

    sys.exit(0 if check_all_config() else 1)
