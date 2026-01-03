"""
Obsidian API Routes

API endpoints for Obsidian vault integration and knowledge management.
"""

import logging
from datetime import datetime

from app.models.obsidian_sync import (
    ObsidianAutoSyncRequest,
    ObsidianErrorResolutionRequest,
    ObsidianRecentNotesResponse,
    ObsidianSearchRequest,
    ObsidianSearchResponse,
    ObsidianSearchResult,
    ObsidianSyncResponse,
    ObsidianSyncStatisticsResponse,
)
from app.services.obsidian_service import obsidian_service
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/obsidian", tags=["Obsidian"])


@router.post(
    "/sync",
    response_model=ObsidianSyncResponse,
    summary="Manual sync trigger",
    description="""
    Manually trigger synchronization of an event to Obsidian vault.

    Creates a structured daily note with YAML frontmatter and markdown content.
    Typically used for phase transitions, architecture decisions, and milestones.
    """,
)
async def manual_sync(request: ObsidianAutoSyncRequest) -> ObsidianSyncResponse:
    """
    Manually sync event to Obsidian

    Args:
        request: Auto-sync request with event type and data

    Returns:
        Sync response with success status
    """
    try:
        logger.info(f"Manual sync requested: {request.event_type}")

        # Perform sync
        success = await obsidian_service.auto_sync(event_type=request.event_type, data=request.data)

        if success:
            return ObsidianSyncResponse(
                success=True,
                message=f"Successfully synced {request.event_type} to Obsidian",
            )
        else:
            return ObsidianSyncResponse(success=False, message="Sync failed - check logs for details")

    except Exception as e:
        logger.error(f"Manual sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to sync to Obsidian: {str(e)}")


@router.post(
    "/auto-sync",
    response_model=ObsidianSyncResponse,
    summary="Auto-sync event (WebSocket trigger)",
    description="""
    Auto-sync endpoint for real-time event synchronization.

    Triggered automatically by the system when significant events occur:
    - Phase transitions
    - Task completions
    - Error resolutions
    - Architecture decisions

    Target: Complete within 3 seconds
    """,
)
async def auto_sync_event(request: ObsidianAutoSyncRequest) -> ObsidianSyncResponse:
    """
    Auto-sync event to Obsidian (triggered by system)

    Args:
        request: Auto-sync request

    Returns:
        Sync response
    """
    try:
        start_time = datetime.now()
        logger.info(f"Auto-sync triggered: {request.event_type}")

        success = await obsidian_service.auto_sync(event_type=request.event_type, data=request.data)

        elapsed = (datetime.now() - start_time).total_seconds()

        if elapsed > 3.0:
            logger.warning(f"Auto-sync took {elapsed:.2f}s (target: <3s)")

        if success:
            return ObsidianSyncResponse(
                success=True,
                message=f"Auto-synced {request.event_type} in {elapsed:.2f}s",
            )
        else:
            return ObsidianSyncResponse(success=False, message="Auto-sync failed - check logs")

    except Exception as e:
        logger.error(f"Auto-sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Auto-sync failed: {str(e)}")


@router.post(
    "/search",
    response_model=ObsidianSearchResponse,
    summary="Search knowledge base",
    description="""
    Search Obsidian vault for past solutions and knowledge.

    This is Tier 1 of the 3-Tier Error Resolution system.
    Target: <10ms response time for 70% of recurring errors.

    Use cases:
    - Find past error resolutions
    - Search development notes
    - Retrieve architecture decisions
    """,
)
async def search_knowledge(request: ObsidianSearchRequest) -> ObsidianSearchResponse:
    """
    Search Obsidian vault for knowledge

    Args:
        request: Search request with query and max results

    Returns:
        Search results with excerpts
    """
    try:
        start_time = datetime.now()
        logger.info(f"Searching Obsidian vault: '{request.query}'")

        # Perform search
        results = await obsidian_service.search_knowledge(query=request.query, max_results=request.max_results)

        elapsed = (datetime.now() - start_time).total_seconds() * 1000  # ms

        # Convert to response models
        search_results = [ObsidianSearchResult(**result) for result in results]

        logger.info(f"Search completed in {elapsed:.1f}ms: {len(results)} results")

        return ObsidianSearchResponse(
            query=request.query,
            results=search_results,
            total_found=len(results),
            search_time_ms=round(elapsed, 2),
        )

    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get(
    "/search",
    response_model=ObsidianSearchResponse,
    summary="Search knowledge base (GET)",
    description="Search Obsidian vault using query parameters (alternative to POST)",
)
async def search_knowledge_get(
    q: str = Query(..., min_length=1, description="Search query"),
    max_results: int = Query(5, ge=1, le=20, description="Maximum results"),
) -> ObsidianSearchResponse:
    """
    Search Obsidian vault (GET endpoint)

    Args:
        q: Search query
        max_results: Maximum results to return

    Returns:
        Search results
    """
    request = ObsidianSearchRequest(query=q, max_results=max_results)
    return await search_knowledge(request)


@router.get(
    "/recent",
    response_model=ObsidianRecentNotesResponse,
    summary="Get recent notes",
    description="""
    Get recent development notes from Obsidian vault.

    Returns notes from the last N days, sorted by date (most recent first).
    Useful for:
    - Reviewing recent work
    - Continuity across sessions
    - Activity timeline
    """,
)
async def get_recent_notes(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back")
) -> ObsidianRecentNotesResponse:
    """
    Get recent development notes

    Args:
        days: Number of days to look back

    Returns:
        Recent notes with metadata
    """
    try:
        logger.info(f"Retrieving notes from last {days} days")

        notes = await obsidian_service.get_recent_notes(days=days)

        logger.info(f"Retrieved {len(notes)} notes")

        return ObsidianRecentNotesResponse(notes=notes, days=days, total_found=len(notes))

    except Exception as e:
        logger.error(f"Failed to get recent notes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get recent notes: {str(e)}")


@router.post(
    "/error-resolution",
    response_model=ObsidianSyncResponse,
    summary="Save error resolution",
    description="""
    Save error resolution for future reuse in 3-Tier Error Resolution.

    When an error is resolved, save the solution to Obsidian so it can be
    automatically retrieved next time the same error occurs (Tier 1 resolution).

    This enables the 70% auto-resolution rate for recurring errors.
    """,
)
async def save_error_resolution(
    request: ObsidianErrorResolutionRequest,
) -> ObsidianSyncResponse:
    """
    Save error resolution to Obsidian

    Args:
        request: Error resolution request with error, solution, and context

    Returns:
        Sync response
    """
    try:
        logger.info(f"Saving error resolution: {request.error[:50]}...")

        success = await obsidian_service.save_error_resolution(
            error=request.error, solution=request.solution, context=request.context
        )

        if success:
            return ObsidianSyncResponse(
                success=True,
                message="Error resolution saved to Obsidian for future reuse",
            )
        else:
            return ObsidianSyncResponse(success=False, message="Failed to save error resolution")

    except Exception as e:
        logger.error(f"Failed to save error resolution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to save error resolution: {str(e)}")


@router.get(
    "/resolve-error",
    summary="Tier 1 error resolution",
    description="""
    Attempt to resolve error using past solutions from Obsidian (Tier 1).

    This is the first tier of the 3-Tier Error Resolution system.
    - Target: <10ms response time
    - Expected: 70% hit rate for recurring errors

    Returns solution if found in Obsidian vault, None otherwise.
    """,
)
async def resolve_error_tier1(error: str = Query(..., min_length=1, description="Error message to resolve")) -> dict:
    """
    Attempt Tier 1 error resolution

    Args:
        error: Error message

    Returns:
        Dict with solution if found, or indication to escalate to Tier 2/3
    """
    try:
        start_time = datetime.now()
        logger.info(f"Tier 1 resolution attempt: {error[:50]}...")

        solution = await obsidian_service.resolve_error_tier1(error)

        elapsed = (datetime.now() - start_time).total_seconds() * 1000  # ms

        if solution:
            logger.info(f"Tier 1 HIT in {elapsed:.1f}ms")
            return {
                "tier": 1,
                "found": True,
                "solution": solution,
                "response_time_ms": round(elapsed, 2),
                "message": "Solution found in Obsidian vault (past resolution)",
            }
        else:
            logger.info(f"Tier 1 MISS in {elapsed:.1f}ms - escalate to Tier 2")
            return {
                "tier": 1,
                "found": False,
                "solution": None,
                "response_time_ms": round(elapsed, 2),
                "message": "No past solution found - escalate to Tier 2 (Context7)",
            }

    except Exception as e:
        logger.error(f"Tier 1 resolution failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Tier 1 resolution failed: {str(e)}")


@router.get(
    "/statistics",
    response_model=ObsidianSyncStatisticsResponse,
    summary="Get sync statistics",
    description="""
    Get Obsidian synchronization statistics.

    Includes:
    - Total syncs
    - Success/failure rates
    - Breakdown by event type
    - Vault availability status
    """,
)
async def get_sync_statistics() -> ObsidianSyncStatisticsResponse:
    """
    Get sync statistics

    Returns:
        Sync statistics
    """
    try:
        stats = obsidian_service.get_sync_statistics()

        return ObsidianSyncStatisticsResponse(**stats)

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get(
    "/health",
    summary="Check Obsidian service health",
    description="Check if Obsidian vault is available and accessible",
)
async def health_check() -> dict:
    """
    Health check for Obsidian service

    Returns:
        Health status
    """
    return {
        "status": "healthy" if obsidian_service.vault_available else "degraded",
        "vault_available": obsidian_service.vault_available,
        "vault_path": (str(obsidian_service.vault_path) if obsidian_service.vault_path else None),
        "daily_notes_dir": (str(obsidian_service.daily_notes_dir) if obsidian_service.daily_notes_dir else None),
        "pending_events": len(obsidian_service.pending_events),
        "message": ("Obsidian vault accessible" if obsidian_service.vault_available else "Obsidian vault not found"),
    }


@router.post(
    "/event",
    response_model=ObsidianSyncResponse,
    summary="Queue event with debouncing",
    description="""
    Add event to sync queue with automatic debouncing (preferred method).

    Events within 3 seconds are batched into a single note for token optimization.
    This is the recommended way to trigger synchronization for real-time events.

    Benefits:
    - 50-70% token reduction through batching
    - Cleaner vault (fewer, more meaningful notes)
    - Automatic intelligent batching
    """,
)
async def queue_event(request: ObsidianAutoSyncRequest) -> ObsidianSyncResponse:
    """
    Queue event with debouncing (recommended)

    Args:
        request: Event to queue

    Returns:
        Sync response
    """
    try:
        logger.info(f"Queueing event: {request.event_type}")

        success = await obsidian_service.sync_event(event_type=request.event_type, data=request.data)

        pending = len(obsidian_service.pending_events)

        if success:
            return ObsidianSyncResponse(
                success=True,
                message=f"Event queued ({pending} pending, will flush in {obsidian_service.debounce_window}s or on immediate trigger)",
            )
        else:
            return ObsidianSyncResponse(success=False, message="Failed to queue event - check logs")

    except Exception as e:
        logger.error(f"Failed to queue event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to queue event: {str(e)}")


@router.post(
    "/force-flush",
    response_model=ObsidianSyncResponse,
    summary="Force flush pending events",
    description="""
    Manually trigger immediate flush of all pending events.

    Useful for:
    - End of session (save everything now)
    - Before system shutdown
    - Manual control over batching
    """,
)
async def force_flush() -> ObsidianSyncResponse:
    """
    Force flush all pending events immediately

    Returns:
        Sync response with number of events flushed
    """
    try:
        logger.info("Force flush requested")

        events_flushed = await obsidian_service.force_flush()

        return ObsidianSyncResponse(success=True, message=f"Flushed {events_flushed} pending event(s)")

    except Exception as e:
        logger.error(f"Force flush failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Force flush failed: {str(e)}")


# Export router
__all__ = ["router"]
