"""Initial schema

Revision ID: 001
Revises: None
Create Date: 2024-01-20 12:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create nba_game_lines schema if it doesn't exist
    op.execute("CREATE SCHEMA IF NOT EXISTS nba_game_lines")

    # Create games table
    op.create_table(
        "games",
        sa.Column("game_id", sa.String(100), primary_key=True),
        sa.Column("game_date", sa.DateTime(), nullable=False),
        sa.Column("season_year", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(10), nullable=False),
        sa.Column("visitor_team", sa.String(100), nullable=False),
        sa.Column("visitor_points", sa.Integer()),
        sa.Column("home_team", sa.String(100), nullable=False),
        sa.Column("home_points", sa.Integer()),
        sa.Column("attendance", sa.Integer()),
        sa.Column("arena", sa.String(200)),
        sa.Column("box_score_url", sa.String(500)),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("scraped_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            onupdate=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        schema="nba_game_lines",
    )

    # Create indexes
    op.create_index(
        "ix_games_game_date", "games", ["game_date"], schema="nba_game_lines"
    )
    op.create_index(
        "ix_games_season_year", "games", ["season_year"], schema="nba_game_lines"
    )
    op.create_index("ix_games_season", "games", ["season"], schema="nba_game_lines")
    op.create_index(
        "ix_games_visitor_team", "games", ["visitor_team"], schema="nba_game_lines"
    )
    op.create_index(
        "ix_games_home_team", "games", ["home_team"], schema="nba_game_lines"
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("ix_games_game_date", table_name="games", schema="nba_game_lines")
    op.drop_index("ix_games_season_year", table_name="games", schema="nba_game_lines")
    op.drop_index("ix_games_season", table_name="games", schema="nba_game_lines")
    op.drop_index("ix_games_visitor_team", table_name="games", schema="nba_game_lines")
    op.drop_index("ix_games_home_team", table_name="games", schema="nba_game_lines")

    # Drop tables
    op.drop_table("games", schema="nba_game_lines")

    # Drop schema
    op.execute("DROP SCHEMA IF EXISTS nba_game_lines")
