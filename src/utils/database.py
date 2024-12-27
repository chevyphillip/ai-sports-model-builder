from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from src.utils.logger import logger
from src.config.config import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    # Create SQLAlchemy engine with logging
    engine = create_engine(
        DATABASE_URL,
        echo=True,  # Log all SQL statements
        pool_pre_ping=True,  # Enable connection health checks
        pool_size=5,  # Set connection pool size
        max_overflow=10,  # Allow up to 10 connections beyond pool_size
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()


@contextmanager
def get_db():
    """
    Context manager for database sessions.
    Ensures proper handling of database connections and error logging.
    """
    db = SessionLocal()
    try:
        logger.debug("Database session started")
        yield db
        db.commit()
        logger.debug("Database session committed")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error occurred: {str(e)}")
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error occurred: {str(e)}")
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


def init_db():
    """
    Initialize database by creating all tables.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to create database tables: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database initialization: {str(e)}")
        raise
