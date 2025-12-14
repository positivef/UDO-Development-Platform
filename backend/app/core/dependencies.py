"""
Dependency Injection

FastAPI dependencies for service injection.
"""

from typing import Optional
from fastapi import Depends

from ..services.time_tracking_service import TimeTrackingService
from ..services.obsidian_service import ObsidianService
from async_database import get_async_db, AsyncDatabase


# Global service instances (initialized at startup)
_time_tracking_service: Optional[TimeTrackingService] = None
_obsidian_service: Optional[ObsidianService] = None


def get_obsidian_service() -> ObsidianService:
    """
    Get ObsidianService instance

    Returns:
        ObsidianService singleton instance
    """
    global _obsidian_service

    if _obsidian_service is None:
        _obsidian_service = ObsidianService()

    return _obsidian_service


def get_time_tracking_service(
    db: AsyncDatabase = Depends(get_async_db),
    obsidian: ObsidianService = Depends(get_obsidian_service)
) -> TimeTrackingService:
    """
    Get TimeTrackingService instance

    Args:
        db: Database instance
        obsidian: ObsidianService instance

    Returns:
        TimeTrackingService instance
    """
    global _time_tracking_service

    # Create new instance if pool is available
    if db and db._initialized:
        pool = db.get_pool()
        return TimeTrackingService(
            pool=pool,
            obsidian_service=obsidian
        )

    # Return cached instance or create mock instance
    if _time_tracking_service is None:
        _time_tracking_service = TimeTrackingService(
            pool=None,
            obsidian_service=obsidian
        )

    return _time_tracking_service


def initialize_services(db: AsyncDatabase):
    """
    Initialize global service instances at startup

    Args:
        db: Initialized database instance
    """
    global _time_tracking_service, _obsidian_service

    _obsidian_service = ObsidianService()

    if db and db._initialized:
        pool = db.get_pool()
        _time_tracking_service = TimeTrackingService(
            pool=pool,
            obsidian_service=_obsidian_service
        )
    else:
        _time_tracking_service = TimeTrackingService(
            pool=None,
            obsidian_service=_obsidian_service
        )


def cleanup_services():
    """
    Cleanup service instances at shutdown
    """
    global _time_tracking_service, _obsidian_service

    _time_tracking_service = None
    _obsidian_service = None
