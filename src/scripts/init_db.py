import subprocess
import sys
from pathlib import Path
from src.utils.logger import logger
from src.utils.database import init_db


def run_command(command: list[str]) -> bool:
    """Run a shell command and log its output."""
    try:
        logger.info(f"Running command: {' '.join(command)}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running command: {str(e)}")
        return False


def setup_database():
    """Set up the database and run migrations."""
    try:
        # Check if database exists
        check_db = run_command(
            [
                "psql",
                "-lqt",
                "|",
                "cut",
                "-d",
                "|",
                "-f",
                "1",
                "|",
                "grep",
                "-w",
                "sports_model",
            ]
        )

        if not check_db:
            # Create database
            logger.info("Creating database...")
            if not run_command(["createdb", "sports_model"]):
                logger.error("Failed to create database")
                return False
            logger.info("Database created successfully")
        else:
            logger.info("Database already exists")

        # Initialize database tables
        logger.info("Initializing database tables...")
        init_db()

        # Run migrations
        logger.info("Running database migrations...")
        migrations_dir = Path(__file__).parent.parent / "migrations"
        if not run_command(["alembic", "--config", "alembic.ini", "upgrade", "head"]):
            logger.error("Failed to run migrations")
            return False

        logger.info("Database setup completed successfully")
        return True

    except Exception as e:
        logger.error(f"Database setup failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)
