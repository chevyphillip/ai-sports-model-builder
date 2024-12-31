#!/usr/bin/env python3
"""Script to run live odds collection."""

# Standard library imports
import asyncio
import logging
import os
import signal
import sys
from datetime import datetime
from typing import Optional

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

# Local imports
from src.data_collection.collectors.live_odds_collector import LiveOddsCollector
from src.utils.database import get_db_session
from src.utils.logging import setup_logging

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)


class GracefulExit(SystemExit):
    """Custom exception for graceful shutdown."""

    pass


def handle_signal(signum: int, frame) -> None:
    """Handle shutdown signals.

    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    raise GracefulExit()


async def run_collector(collection_interval: int = 300, max_retries: int = 3) -> None:
    """Run the live odds collector.

    Args:
        collection_interval: Interval between collections in seconds
        max_retries: Maximum number of retries for failed operations
    """
    session = get_db_session()
    collector = LiveOddsCollector(
        session=session,
        collection_interval=collection_interval,
        max_retries=max_retries,
    )

    try:
        logger.info(
            f"Starting live odds collection (interval: {collection_interval}s, "
            f"max retries: {max_retries})"
        )
        await collector.run_collection_loop()
    except GracefulExit:
        logger.info("Gracefully shutting down...")
    except Exception as e:
        logger.error(f"Fatal error in collection loop: {str(e)}")
        raise
    finally:
        session.close()
        logger.info("Collection stopped, database session closed")


def main() -> None:
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Get configuration from environment
    collection_interval = int(os.getenv("COLLECTION_INTERVAL", "300"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))

    try:
        asyncio.run(
            run_collector(
                collection_interval=collection_interval, max_retries=max_retries
            )
        )
    except Exception as e:
        logger.error(f"Error running collector: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
