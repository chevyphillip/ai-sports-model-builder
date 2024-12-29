from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    DateTime,
    text,
    Boolean,
)
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Schema name for NBA game line model
SCHEMA_NAME = "nba_game_lines"


def upgrade():
    """Update games table schema"""
    # Create engine with properly escaped password
    url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(url, echo=True, connect_args={"sslmode": "require"})

    # Create MetaData instance with schema
    metadata = MetaData(schema=SCHEMA_NAME)

    # Drop existing games table
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA_NAME}.games CASCADE"))
        conn.commit()
        print(f"✅ Dropped existing games table")

    # Define new games table
    games = Table(
        "games",
        metadata,
        Column("game_id", String(100), primary_key=True),
        Column("game_date", DateTime, nullable=False),
        Column("season_year", Integer, nullable=False),
        Column("season", String(10), nullable=False),
        Column("visitor_team", String(50), nullable=False),
        Column("visitor_points", Integer),
        Column("home_team", String(50), nullable=False),
        Column("home_points", Integer),
        Column("overtime", Boolean, default=False),
        Column("ot_periods", Integer, default=0),
        Column("attendance", Integer),
        Column("arena", String(100)),
        Column("source", String(50)),
        Column("scraped_at", DateTime),
        Column("created_at", DateTime, default=datetime.utcnow),
        Column(
            "updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        ),
    )

    # Create new table
    metadata.create_all(engine)
    print("✅ Successfully created new games table")


def downgrade():
    """Revert to original games table schema"""
    # Create engine with properly escaped password
    url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(url, echo=True, connect_args={"sslmode": "require"})

    # Drop the new games table
    with engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA_NAME}.games"))
        conn.commit()
        print(f"✅ Dropped new games table")

    # Recreate original games table
    metadata = MetaData(schema=SCHEMA_NAME)
    games = Table(
        "games",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("game_date", DateTime, nullable=False),
        Column("season", Integer, nullable=False),
        Column("home_team", String(50), nullable=False),
        Column("away_team", String(50), nullable=False),
        Column("home_score", Integer),
        Column("away_score", Integer),
        Column("home_team_stats", JSON),
        Column("away_team_stats", JSON),
        Column("created_at", DateTime, default=datetime.utcnow),
        Column(
            "updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        ),
    )

    metadata.create_all(engine)
    print("✅ Successfully reverted to original games table schema")


if __name__ == "__main__":
    upgrade()
