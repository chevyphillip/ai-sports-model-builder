"""Database utilities."""

import os
from contextlib import contextmanager
from typing import Generator
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Load environment variables
load_dotenv()

Base = declarative_base()


def get_database_url() -> str:
    """Get database URL from environment variables."""
    # Get database configuration from environment variables
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

    # For Supabase, we need to properly encode the username and password
    # Use quote() instead of quote_plus() to match Supabase's URL format
    encoded_user = quote(db_user)
    encoded_password = quote(db_password)

    # Construct the URL as a string to match exactly what works with psycopg2
    return (
        f"postgresql://{encoded_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    )


def set_schema(dbapi_connection, _):
    """Set the schema for raw database connections."""
    if schema := os.getenv("DB_SCHEMA"):
        cursor = dbapi_connection.cursor()
        cursor.execute(f"SET search_path TO {schema}")
        cursor.close()
        dbapi_connection.commit()


def create_db_engine() -> Engine:
    """Create database engine with connection pooling."""
    # Supabase connection settings
    connect_args = {
        "sslmode": "require",  # Supabase requires SSL
        "application_name": "ai-sports-model-builder",  # Helpful for identifying connections
    }

    engine = create_engine(
        get_database_url(),
        pool_size=5,  # Maximum number of persistent connections
        max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
        pool_timeout=30,  # Timeout for getting a connection from the pool
        pool_recycle=1800,  # Recycle connections after 30 minutes
        connect_args=connect_args,
        echo=True,  # Enable SQL logging for debugging
    )

    # Set the search_path to use the correct schema
    if os.getenv("DB_SCHEMA"):
        event.listen(engine, "connect", set_schema)

    return engine


# Create global engine instance
engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)
