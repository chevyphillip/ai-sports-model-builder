"""create team table

Revision ID: 001
Revises: 
Create Date: 2023-12-27 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from src.models.team import SportType

# revision identifiers, used by Alembic
revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create SportType enum type
    sport_type = sa.Enum(SportType, name="sporttype")

    # Create team table
    op.create_table(
        "team",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("abbreviation", sa.String(length=10), nullable=False),
        sa.Column("city", sa.String(length=100), nullable=False),
        sa.Column("sport", sport_type, nullable=False),
        sa.Column("division", sa.String(length=100), nullable=True),
        sa.Column("conference", sa.String(length=100), nullable=True),
        sa.Column("venue", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "sport", name="uix_team_name_sport"),
        sa.UniqueConstraint(
            "abbreviation", "sport", name="uix_team_abbreviation_sport"
        ),
    )


def downgrade() -> None:
    # Drop team table
    op.drop_table("team")

    # Drop SportType enum type
    op.execute("DROP TYPE sporttype")
