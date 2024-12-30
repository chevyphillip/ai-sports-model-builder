"""Test data insertion using SQLAlchemy."""

import logging
import os
from datetime import datetime

from sqlalchemy import text

from src.models.team import Team, SportType
from src.utils.database import get_db_session, init_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_team_insertion():
    """Test inserting a team into the database."""
    # Initialize database if needed
    init_db()

    # Sample team data
    test_team = Team(
        name="Lakers",
        abbreviation="LAL",
        city="Los Angeles",
        sport=SportType.NBA,
        division="Pacific",
        conference="Western",
        venue="Crypto.com Arena",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    try:
        with get_db_session() as session:
            # Set schema explicitly for this session
            if schema := os.getenv("DB_SCHEMA"):
                session.execute(text(f"SET search_path TO {schema}"))

            # Check if team already exists
            existing_team = (
                session.query(Team)
                .filter_by(abbreviation="LAL", sport=SportType.NBA)
                .first()
            )

            if existing_team:
                logger.info("Team already exists: %s", existing_team.name)
                return

            # Insert new team
            session.add(test_team)
            session.flush()  # Flush changes to get the ID
            logger.info("Successfully inserted team: %s", test_team.name)

            # Verify insertion with a new query
            session.commit()  # Commit the transaction
            inserted_team = (
                session.query(Team)
                .filter_by(abbreviation="LAL", sport=SportType.NBA)
                .first()
            )

            if inserted_team:
                logger.info("Retrieved team from database: %s", inserted_team.name)
            else:
                logger.error("Failed to retrieve team after insertion")

    except Exception as e:
        logger.error("Error during team insertion: %s", str(e))
        raise


if __name__ == "__main__":
    test_team_insertion()
