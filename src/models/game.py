"""Game model for storing NBA game data."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship

from src.utils.database import Base


class Game(Base):
    """Game model for storing NBA game data."""

    __tablename__ = "game"
    __table_args__ = ({"schema": "nba_game_lines"},)

    id = Column(Integer, primary_key=True)
    game_id = Column(String(100), unique=True, nullable=False)
    season = Column(String(10), nullable=False)
    season_year = Column(Integer, nullable=False)
    game_date = Column(DateTime, nullable=False)
    game_day = Column(String(10), nullable=False)
    game_month = Column(Integer, nullable=False)
    game_year = Column(Integer, nullable=False)
    day_of_week = Column(String(10), nullable=False)
    start_time = Column(String(5), nullable=False)  # Format: HH:MM

    visitor_team_name = Column(String(100), nullable=False)
    home_team_name = Column(String(100), nullable=False)
    visitor_points = Column(Integer, nullable=False)
    home_points = Column(Integer, nullable=False)
    total_score = Column(Integer, nullable=False)
    score_difference = Column(Integer, nullable=False)
    home_win = Column(Boolean, nullable=False)
    overtime = Column(Boolean, nullable=False)
    ot_periods = Column(Integer, nullable=False)

    attendance = Column(Integer)
    arena = Column(String(100))

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<Game {self.game_id} - {self.visitor_team_name} @ {self.home_team_name}>"
        )
