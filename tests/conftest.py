"""Shared test fixtures."""

import os
from typing import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.base import Base

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create a SQLAlchemy engine for testing."""
    # Create an engine with SQLite's in-memory database
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # Enable foreign key support for SQLite
    def _enable_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    event.listen(engine, "connect", _enable_foreign_keys)

    return engine


@pytest.fixture(scope="session")
def tables(engine):
    """Create all database tables."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(engine, tables) -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def test_data_dir(temp_dir):
    """Create a temporary directory for test data files."""
    data_dir = temp_dir / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def test_models_dir(temp_dir):
    """Create a temporary directory for test model files."""
    models_dir = temp_dir / "models"
    models_dir.mkdir()
    return models_dir


@pytest.fixture
def test_logs_dir(temp_dir):
    """Create a temporary directory for test log files."""
    logs_dir = temp_dir / "logs"
    logs_dir.mkdir()
    return logs_dir
