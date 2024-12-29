"""Update games table structure

Revision ID: update_games_table
Create Date: 2024-12-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "update_games_table_v2"
down_revision = "37505bd5f6d2"
branch_labels = None
depends_on = None


def upgrade():
    # Create a temporary table with the new structure
    op.execute(
        """
        CREATE TABLE nba_game_lines.games_new (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            game_id VARCHAR(100) UNIQUE NOT NULL,
            game_date DATE NOT NULL,
            season_year INTEGER NOT NULL,
            season VARCHAR(7) NOT NULL,
            visitor_team VARCHAR(100) NOT NULL,
            visitor_points INTEGER NOT NULL DEFAULT 0,
            home_team VARCHAR(100) NOT NULL,
            home_points INTEGER NOT NULL DEFAULT 0,
            arena VARCHAR(100) NOT NULL,
            source VARCHAR(50) NOT NULL,
            scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT valid_season_format CHECK (season ~ '^[0-9]{4}-[0-9]{2}$'),
            CONSTRAINT valid_points CHECK (visitor_points >= 0 AND home_points >= 0)
        )
    """
    )

    # Copy data from old table to new table with new game_id format
    op.execute(
        """
        INSERT INTO nba_game_lines.games_new (
            game_id, game_date, season_year, season,
            visitor_team, visitor_points, home_team, home_points,
            arena, source, scraped_at, created_at, updated_at
        )
        SELECT DISTINCT ON (game_date, home_team, visitor_team)
            'NBA-' || to_char(game_date, 'YYYY-MM-DD') || '-' || 
            regexp_replace(upper(home_team), '[^A-Z]', '', 'g') || '-' ||
            regexp_replace(upper(visitor_team), '[^A-Z]', '', 'g') as game_id,
            game_date, season_year, season,
            visitor_team, visitor_points, home_team, home_points,
            arena, source, scraped_at,
            COALESCE(created_at, scraped_at) as created_at,
            COALESCE(updated_at, scraped_at) as updated_at
        FROM nba_game_lines.games
        ORDER BY game_date, home_team, visitor_team, scraped_at DESC
    """
    )

    # Drop the old table and rename the new one
    op.execute("DROP TABLE nba_game_lines.games")
    op.execute("ALTER TABLE nba_game_lines.games_new RENAME TO games")

    # Add indexes
    op.execute(
        """
        CREATE INDEX idx_games_game_date ON nba_game_lines.games(game_date);
        CREATE INDEX idx_games_season ON nba_game_lines.games(season);
        CREATE INDEX idx_games_teams ON nba_game_lines.games(home_team, visitor_team);
    """
    )


def downgrade():
    # Note: This downgrade will lose the UUID and some constraints
    op.execute(
        """
        CREATE TABLE nba_game_lines.games_old (
            game_id VARCHAR(50) PRIMARY KEY,
            game_date DATE NOT NULL,
            season_year INTEGER,
            season VARCHAR(7),
            visitor_team VARCHAR(100),
            visitor_points INTEGER,
            home_team VARCHAR(100),
            home_points INTEGER,
            overtime BOOLEAN,
            ot_periods INTEGER,
            attendance INTEGER,
            arena VARCHAR(100),
            source VARCHAR(50),
            scraped_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE,
            updated_at TIMESTAMP WITH TIME ZONE
        )
    """
    )

    # Copy data back with original format
    op.execute(
        """
        INSERT INTO nba_game_lines.games_old (
            game_id, game_date, season_year, season,
            visitor_team, visitor_points, home_team, home_points,
            arena, source, scraped_at, created_at, updated_at
        )
        SELECT 
            substring(game_id from 'NBA-\\d{4}-\\d{2}-\\d{2}-(.*)-.*$'),
            game_date, season_year, season,
            visitor_team, visitor_points, home_team, home_points,
            arena, source, scraped_at, created_at, updated_at
        FROM nba_game_lines.games
    """
    )

    op.execute("DROP TABLE nba_game_lines.games")
    op.execute("ALTER TABLE nba_game_lines.games_old RENAME TO games")
