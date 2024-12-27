from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.sql import text
from datetime import datetime

metadata = MetaData()

# NBA Games table
nba_games = Table(
    "nba_games",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("game_date", DateTime, nullable=False),
    Column("home_team", String, nullable=False),
    Column("away_team", String, nullable=False),
    Column("home_score", Integer),
    Column("away_score", Integer),
    Column("season", String, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
    Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
)

# Game Odds table
game_odds = Table(
    "game_odds",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("game_id", Integer, ForeignKey("nba_games.id")),
    Column("bookmaker", String, nullable=False),
    Column("home_team_spread", Float),
    Column("away_team_spread", Float),
    Column("total_points_over_under", Float),
    Column("home_team_moneyline", Float),
    Column("away_team_moneyline", Float),
    Column("odds_last_update", DateTime),
    Column("created_at", DateTime, default=datetime.utcnow),
)

# Predictions table
predictions = Table(
    "predictions",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("game_id", Integer, ForeignKey("nba_games.id")),
    Column("predicted_home_score", Float),
    Column("predicted_away_score", Float),
    Column("predicted_spread_winner", String),
    Column("predicted_total_points", Float),
    Column("predicted_winner", String),
    Column("confidence_score", Float),
    Column("prediction_timestamp", DateTime, default=datetime.utcnow),
)

# Model Performance table
model_performance = Table(
    "model_performance",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("prediction_id", Integer, ForeignKey("predictions.id")),
    Column("actual_result", String),
    Column("was_spread_correct", Boolean),
    Column("was_total_correct", Boolean),
    Column("was_winner_correct", Boolean),
    Column("error_margin", Float),
    Column("evaluated_at", DateTime, default=datetime.utcnow),
)


def upgrade(engine):
    metadata.create_all(engine)


def downgrade(engine):
    metadata.drop_all(engine)
