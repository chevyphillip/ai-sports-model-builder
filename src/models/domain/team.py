"""Team model."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, UniqueConstraint

from src.utils.database import Base


class SportType(enum.Enum):
    """Sport type enum."""

    NBA = "NBA"
    NFL = "NFL"
    MLB = "MLB"
    NHL = "NHL"


class Team(Base):
    """Team model."""

    __tablename__ = "team"
    __table_args__ = (
        UniqueConstraint("name", "sport", name="uix_team_name_sport"),
        UniqueConstraint("abbreviation", "sport", name="uix_team_abbreviation_sport"),
        {"schema": "nba_game_lines"},
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    sport = Column(Enum(SportType), nullable=False)
    division = Column(String(100))
    conference = Column(String(100))
    venue = Column(String(100))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Team {self.city} {self.name} ({self.sport.value})>"
