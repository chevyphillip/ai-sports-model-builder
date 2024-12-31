"""Database models for NBA games and odds data."""

from datetime import datetime
from typing import List
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
    Enum,
    Index,
    Boolean,
)
import enum
from sqlalchemy.orm import relationship
from .base import Base


class MarketType(enum.Enum):
    """Core market types supported by the API."""

    H2H = "h2h"  # Moneyline
    SPREAD = "spreads"  # Point spread
    TOTAL = "totals"  # Over/under


class Team(Base):
    """NBA teams master table."""

    __tablename__ = "nba_teams"
    __table_args__ = {"schema": "nba_game_lines"}

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # Full team name
    location = Column(String, nullable=False)  # City/Location
    abbreviation = Column(String(3), unique=True)  # 3-letter code
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    home_games = relationship(
        "Game", foreign_keys="Game.home_team_id", back_populates="home_team"
    )
    away_games = relationship(
        "Game", foreign_keys="Game.away_team_id", back_populates="away_team"
    )


class Bookmaker(Base):
    """Licensed bookmakers in New York State."""

    __tablename__ = "bookmakers"
    __table_args__ = {"schema": "nba_game_lines"}

    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)  # API key
    name = Column(String, nullable=False)  # Display name
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    odds = relationship("GameOdds", back_populates="bookmaker")


class Game(Base):
    """NBA game data."""

    __tablename__ = "games"
    __table_args__ = (
        Index("idx_game_commence_time", "commence_time"),
        {"schema": "nba_game_lines"},
    )

    id = Column(Integer, primary_key=True)
    game_id = Column(String, unique=True, nullable=False)  # API game ID
    home_team_id = Column(
        Integer, ForeignKey("nba_game_lines.nba_teams.id"), nullable=False
    )
    away_team_id = Column(
        Integer, ForeignKey("nba_game_lines.nba_teams.id"), nullable=False
    )
    commence_time = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    home_team = relationship(
        "Team", foreign_keys=[home_team_id], back_populates="home_games"
    )
    away_team = relationship(
        "Team", foreign_keys=[away_team_id], back_populates="away_games"
    )
    odds = relationship("GameOdds", back_populates="game", cascade="all, delete-orphan")


class GameOdds(Base):
    """Game odds data for ML training."""

    __tablename__ = "game_odds"
    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "bookmaker_id",
            "market_type",
            "timestamp",
            name="unique_game_odds",
        ),
        Index("idx_odds_timestamp", "timestamp"),
        {"schema": "nba_game_lines"},
    )

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey("nba_game_lines.games.id"), nullable=False)
    bookmaker_id = Column(
        Integer, ForeignKey("nba_game_lines.bookmakers.id"), nullable=False
    )
    market_type = Column(Enum(MarketType), nullable=False)
    timestamp = Column(
        DateTime(timezone=True), nullable=False
    )  # When odds were captured

    # Market-specific fields
    home_price = Column(Float)  # Moneyline/spread price for home team
    away_price = Column(Float)  # Moneyline/spread price for away team
    spread = Column(Float)  # Point spread (positive for home team favorite)
    total = Column(Float)  # Over/under total
    over_price = Column(Float)  # Price for over
    under_price = Column(Float)  # Price for under

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    game = relationship("Game", back_populates="odds")
    bookmaker = relationship("Bookmaker", back_populates="odds")
