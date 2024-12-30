from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Boolean,
    JSON,
    text,
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
    """Create initial tables"""
    # Create engine with properly escaped password
    url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(url, echo=True, connect_args={"sslmode": "require"})

    # Create schema if it doesn't exist
    with engine.connect() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME}"))
        conn.commit()
        print(f"✅ Created schema: {SCHEMA_NAME}")

    # Create MetaData instance with schema
    metadata = MetaData(schema=SCHEMA_NAME)

    # Define tables
    nba_games = Table(
        "games",  # Simplified name since we're in nba_game_lines schema
        metadata,
        Column("id", Integer, primary_key=True),
        Column("game_date", DateTime, nullable=False),
        Column("season", Integer, nullable=False),
        Column("home_team", String(50), nullable=False),
        Column("away_team", String(50), nullable=False),
        Column("home_score", Integer),
        Column("away_score", Integer),
        Column("home_team_stats", JSON),  # Store detailed team stats as JSON
        Column("away_team_stats", JSON),
        Column("created_at", DateTime, default=datetime.utcnow),
        Column(
            "updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
        ),
    )

    game_odds = Table(
        "odds",  # Simplified name since we're in nba_game_lines schema
        metadata,
        Column("id", Integer, primary_key=True),
        Column(
            "game_id", Integer, ForeignKey(f"{SCHEMA_NAME}.games.id"), nullable=False
        ),
        Column("bookmaker", String(50), nullable=False),
        Column("home_spread", Float),
        Column("away_spread", Float),
        Column("home_spread_odds", Float),
        Column("away_spread_odds", Float),
        Column("home_moneyline", Float),
        Column("away_moneyline", Float),
        Column("over_under", Float),
        Column("over_odds", Float),
        Column("under_odds", Float),
        Column("odds_updated_at", DateTime, nullable=False),
        Column("created_at", DateTime, default=datetime.utcnow),
    )

    predictions = Table(
        "predictions",
        metadata,
        Column("id", Integer, primary_key=True),
        Column(
            "game_id", Integer, ForeignKey(f"{SCHEMA_NAME}.games.id"), nullable=False
        ),
        Column("predicted_home_score", Float, nullable=False),
        Column("predicted_away_score", Float, nullable=False),
        Column("predicted_spread", Float),
        Column("predicted_total", Float),
        Column("confidence_score", Float),
        Column("model_version", String(50), nullable=False),
        Column("features_used", JSON),  # Store list of features used for prediction
        Column("created_at", DateTime, default=datetime.utcnow),
    )

    model_performance = Table(
        "performance",  # Simplified name since we're in nba_game_lines schema
        metadata,
        Column("id", Integer, primary_key=True),
        Column(
            "prediction_id",
            Integer,
            ForeignKey(f"{SCHEMA_NAME}.predictions.id"),
            nullable=False,
        ),
        Column("actual_home_score", Integer),
        Column("actual_away_score", Integer),
        Column(
            "spread_accuracy", Float
        ),  # Difference between predicted and actual spread
        Column(
            "total_accuracy", Float
        ),  # Difference between predicted and actual total
        Column("bet_result", String(10)),  # 'win', 'loss', or 'push'
        Column("evaluated_at", DateTime, default=datetime.utcnow),
    )

    # Create all tables
    metadata.create_all(engine)
    print("✅ Successfully created all tables in schema:", SCHEMA_NAME)


def downgrade():
    """Remove schema and all its tables"""
    # Create engine with properly escaped password
    url = f"postgresql://{os.getenv('DB_USER')}:{quote_plus(os.getenv('DB_PASSWORD'))}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    engine = create_engine(url, echo=True, connect_args={"sslmode": "require"})

    # Drop the entire schema and all its tables
    with engine.connect() as conn:
        conn.execute(text(f"DROP SCHEMA IF EXISTS {SCHEMA_NAME} CASCADE"))
        conn.commit()
        print(f"✅ Dropped schema: {SCHEMA_NAME}")


if __name__ == "__main__":
    upgrade()
