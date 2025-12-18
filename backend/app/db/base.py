"""
SQLAlchemy Base Class Export

This module provides a centralized export of the declarative_base
for all SQLAlchemy ORM models to inherit from.
"""

from backend.app.db.database import Base

__all__ = ["Base"]
