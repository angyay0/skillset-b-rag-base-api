import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

# Database configuration
# Note: Using postgresql+psycopg for psycopg3 driver
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql+psycopg://user:password@localhost:5432/blinky_db'
)

# Create engine with better connection management
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # Reduced from 10
    max_overflow=10,  # Reduced from 20
    pool_pre_ping=True,  # Test connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Timeout for getting connection from pool
    echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Session:
    """Get database session - WARNING: Caller must close the session!
    
    Prefer using get_db_context() context manager instead.
    """
    db = SessionLocal()
    return db


@contextmanager
def get_db_context():
    """Context manager for database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
