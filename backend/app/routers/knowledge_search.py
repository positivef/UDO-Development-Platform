"""
Knowledge Search Router - 3-Tier Search API

Week 6 Day 4 PM: Knowledge Reuse Accuracy Tracking

Endpoints:
- GET /api/knowledge/search - 3-tier search with MCP integration
- GET /api/knowledge/search/stats - Search performance statistics

Integration:
- Obsidian MCP: list_files, complex_search, simple_search
- KnowledgeSearchService: 3-tier search logic
- FeedbackButtons: User feedback collection
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import os

# Import MCP tools (will be available in backend runtime)
# Note: These are injected by the MCP server at runtime
# For type hints, we'll define them as we use them

# Import search service
from app.services.knowledge_search_service import (
    KnowledgeSearchService,
    SearchResult,
)

# Import database and service
from backend.app.db.database import get_db
from backend.app.services.knowledge_feedback_service import KnowledgeFeedbackService

router = APIRouter(prefix="/api/knowledge", tags=["knowledge-search"])

# ============================================================================
# Pydantic Models
# ============================================================================

class SearchRequest(BaseModel):
    """Search request parameters"""
    query: str = Field(..., description="Search query string", min_length=3)
    error_type: Optional[str] = Field(None, description="Specific error type to filter")
    max_results: int = Field(10, description="Maximum number of results", ge=1, le=50)
    min_score: float = Field(5.0, description="Minimum relevance score", ge=0.0)


class SearchResultResponse(BaseModel):
    """Search result with scoring breakdown"""
    document_id: str
    document_path: str
    relevance_score: float
    tier1_score: float
    tier2_score: float
    tier3_score: float
    freshness_bonus: float
    usefulness_score: float
    matched_query: str
    snippet: str


class SearchResponse(BaseModel):
    """Search response with results and metadata"""
    query: str
    total_results: int
    results: List[SearchResultResponse]
    search_time_ms: float
    tier_breakdown: Dict[str, int] = Field(
        description="Count of results from each tier"
    )


class SearchStats(BaseModel):
    """Search performance statistics"""
    total_searches: int
    avg_search_time_ms: float
    tier1_hit_rate: float = Field(description="% of searches with Tier 1 results")
    tier2_hit_rate: float = Field(description="% of searches with Tier 2 results")
    tier3_hit_rate: float = Field(description="% of searches with Tier 3 results")
    avg_results_per_search: float


# ============================================================================
# Helper Functions
# ============================================================================

def get_obsidian_vault_path() -> str:
    """
    Get Obsidian vault path from environment or default

    Returns:
        Absolute path to Obsidian vault
    """
    vault_path = os.getenv("OBSIDIAN_VAULT_PATH")

    if not vault_path:
        # Auto-detect from common locations (same logic as obsidian_service)
        home = os.path.expanduser("~")
        common_paths = [
            os.path.join(home, "Documents", "Obsidian Vault"),
            os.path.join(home, "Obsidian"),
            os.path.join(home, "Documents", "Obsidian"),
        ]

        for path in common_paths:
            if os.path.exists(path):
                vault_path = path
                break

        if not vault_path:
            raise HTTPException(
                status_code=500,
                detail="Obsidian vault path not configured. Set OBSIDIAN_VAULT_PATH env var."
            )

    return vault_path


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/search", response_model=SearchResponse)
async def search_knowledge(
    query: str = Query(..., min_length=3, description="Search query"),
    error_type: Optional[str] = Query(None, description="Specific error type"),
    max_results: int = Query(10, ge=1, le=50, description="Max results"),
    min_score: float = Query(5.0, ge=0.0, description="Min relevance score"),
    db: Session = Depends(get_db),
):
    """
    3-Tier Knowledge Search

    Execution Flow:
    1. Fetch Obsidian vault files (Tier 1)
    2. Execute Tier 1: Filename pattern matching
    3. Execute Tier 2: Frontmatter YAML search (if keywords found)
    4. Execute Tier 3: Full-text content search (fallback)
    5. Merge and score results
    6. Return top N results

    Performance Target: <500ms (p95)

    Benchmarking:
    - Obsidian: Backlinks + Freshness scoring
    - Notion AI: CTR + Helpful rate feedback
    - Linear: Confidence score + Accuracy tracking
    """
    import time
    start_time = time.time()

    try:
        # Initialize search service
        vault_path = get_obsidian_vault_path()
        search_service = KnowledgeSearchService(vault_path)

        # TODO: Call Obsidian MCP tools for real data
        # For MVP Phase 1: Use mock data mode (service handles fallback)
        # For MVP Phase 2: Integrate actual MCP calls

        # Phase 2 integration (commented for MVP):
        # from mcp import obsidian
        # obsidian_files = obsidian.list_files_in_vault()
        # complex_results = obsidian.complex_search(query=build_query())
        # simple_results = obsidian.simple_search(query=query)

        # Execute 3-tier search (uses mock data for MVP)
        results = search_service.search(
            query=query,
            error_type=error_type,
            max_results=max_results,
            min_score=min_score,
        )

        # Calculate tier breakdown
        tier_breakdown = {
            "tier1": sum(1 for r in results if r.tier1_score > 0),
            "tier2": sum(1 for r in results if r.tier2_score > 0),
            "tier3": sum(1 for r in results if r.tier3_score > 0),
        }

        # Update statistics (PostgreSQL)
        search_time_ms = (time.time() - start_time) * 1000
        service = KnowledgeFeedbackService(db)
        service.create_search_stats(
            search_query=query,
            search_time_ms=search_time_ms,
            tier1_hits=tier_breakdown["tier1"],
            tier2_hits=tier_breakdown["tier2"],
            tier3_hits=tier_breakdown["tier3"],
            total_results=len(results),
            session_id=None  # TODO: Extract from request if available
        )

        # Convert to response format
        result_responses = [
            SearchResultResponse(**r.to_dict())
            for r in results
        ]

        return SearchResponse(
            query=query,
            total_results=len(results),
            results=result_responses,
            search_time_ms=round(search_time_ms, 2),
            tier_breakdown=tier_breakdown,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/search/stats", response_model=SearchStats)
async def get_search_stats(
    days: int = Query(7, ge=1, le=90, description="Time period in days"),
    db: Session = Depends(get_db),
):
    """
    Get search performance statistics (PostgreSQL)

    Metrics:
    - Total searches performed
    - Average search time
    - Tier hit rates (% of searches with results from each tier)
    - Average results per search

    Benchmarking:
    - Linear: 60%+ accuracy target
    - GitHub Copilot: 26-40% acceptance rate
    - Notion AI: <10% false positive rate

    Args:
        days: Number of days to include in statistics (default: 7)
    """
    service = KnowledgeFeedbackService(db)
    stats = service.get_search_statistics(days=days)

    return SearchStats(**stats)


# ============================================================================
# Export
# ============================================================================

__all__ = ["router"]
