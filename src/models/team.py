from sqlalchemy import Column, Integer, String, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
import enum
from src.models.base import BaseModel


class SportType(enum.Enum):
    """Enumeration of supported sports."""

    NBA = "NBA"
    NFL = "NFL"
    NHL = "NHL"


class Team(BaseModel):
    """Model representing a sports team."""

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    abbreviation = Column(String(10), nullable=False)
    city = Column(String(100), nullable=False)
    sport = Column(Enum(SportType), nullable=False)

    # Additional metadata
    division = Column(String(100))
    conference = Column(String(100))
    venue = Column(String(100))

    # Ensure team names are unique within each sport
    __table_args__ = (
        UniqueConstraint("name", "sport", name="uix_team_name_sport"),
        UniqueConstraint("abbreviation", "sport", name="uix_team_abbreviation_sport"),
    )

    # Relationships will be added as we create other models
    # home_games = relationship("Game", back_populates="home_team", foreign_keys="[Game.home_team_id]")
    # away_games = relationship("Game", back_populates="away_team", foreign_keys="[Game.away_team_id]")
    # players = relationship("Player", back_populates="team")

    def __str__(self) -> str:
        """Return string representation of the team."""
        return f"{self.city} {self.name} ({self.sport.value})"
