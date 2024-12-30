"""Alembic migration environment."""

import os
from logging.config import fileConfig

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from urllib.parse import quote

from src.utils.database import Base
from src.models.team import Team  # Import models to register them with Base
from src.models.game import Game  # Import models to register them with Base

# Load environment variables
load_dotenv()

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get database configuration
db_host = os.getenv("DB_HOST")
db_port = os.getenv("DB_PORT")
db_name = os.getenv("DB_NAME")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")

if not all([db_host, db_port, db_name, db_user, db_password]):
    raise ValueError(
        "Missing required database configuration. "
        "Please ensure DB_HOST, DB_PORT, DB_NAME, DB_USER, and DB_PASSWORD "
        "are set in your environment variables."
    )

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def get_db_url():
    """Get properly encoded database URL."""
    encoded_user = quote(db_user)
    encoded_password = quote(db_password)
    return (
        f"postgresql://{encoded_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=get_db_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(
        get_db_url(),
        poolclass=pool.NullPool,
        connect_args={"sslmode": "require"},
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="nba_game_lines",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
