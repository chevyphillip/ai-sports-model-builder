"""Add odds tables

Revision ID: add_odds_tables
Create Date: 2024-12-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = "add_odds_tables"
down_revision = "update_games_table_v2"
branch_labels = None
depends_on = None


def upgrade():
    # Create odds_snapshots table to store each snapshot from the API
    op.create_table(
        "odds_snapshots",
        sa.Column(
            "id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "game_id", sa.String(100), sa.ForeignKey("nba_game_lines.games.game_id")
        ),
        sa.Column("snapshot_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previous_snapshot_timestamp", sa.DateTime(timezone=True)),
        sa.Column("next_snapshot_timestamp", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        schema="nba_game_lines",
    )

    # Create bookmaker_odds table to store odds from each bookmaker
    op.create_table(
        "bookmaker_odds",
        sa.Column(
            "id", UUID, primary_key=True, server_default=sa.text("gen_random_uuid()")
        ),
        sa.Column(
            "snapshot_id", UUID, sa.ForeignKey("nba_game_lines.odds_snapshots.id")
        ),
        sa.Column("bookmaker_key", sa.String(50), nullable=False),
        sa.Column("bookmaker_title", sa.String(100), nullable=False),
        sa.Column("last_update", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "markets", JSONB, nullable=False
        ),  # Store all markets (h2h, spreads, totals) as JSONB
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        schema="nba_game_lines",
    )

    # Add indexes
    op.create_index(
        "idx_odds_snapshots_game_timestamp",
        "odds_snapshots",
        ["game_id", "snapshot_timestamp"],
        schema="nba_game_lines",
    )
    op.create_index(
        "idx_bookmaker_odds_snapshot",
        "bookmaker_odds",
        ["snapshot_id", "bookmaker_key"],
        schema="nba_game_lines",
    )


def downgrade():
    op.drop_table("bookmaker_odds", schema="nba_game_lines")
    op.drop_table("odds_snapshots", schema="nba_game_lines")
