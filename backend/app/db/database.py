"""
Database connection management
Supports both PostgreSQL (primary) and SQLite (shadow) databases
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator
import logging

logger = logging.getLogger(__name__)

# Database URLs
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://udo_dev:dev_password_123@localhost:5432/udo_v3"
)
SQLITE_URL = "sqlite:///./data/udo_shadow.db"

# PostgreSQL engine (primary)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=20,  # Antigravity recommended: 20 for 15-20 concurrent requests
    max_overflow=10,
    echo=False
)

# SQLite engine (shadow)
sqlite_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Session makers
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SQLiteSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Get PostgreSQL database session (primary)

    Usage:
        with get_db() as db:
            # Use db session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_sqlite_db() -> Generator:
    """
    Get SQLite database session (shadow)

    Usage:
        with get_sqlite_db() as db:
            # Use SQLite session
    """
    db = SQLiteSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    # Create tables in both databases
    Base.metadata.create_all(bind=engine)
    Base.metadata.create_all(bind=sqlite_engine)
    logger.info("[OK] Database tables created")
