"""
C-K Theory API Routes

API endpoints for Concept-Knowledge Design Theory (design alternative generation)
"""

from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import Optional, List
import logging

from ..models.ck_theory import (
    CKTheoryRequest,
    CKTheoryResult,
    DesignSummary,
    DesignFeedback,
)
from ..services.ck_theory_service import ck_theory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ck-theory", tags=["C-K Theory"])


@router.post(
    "",
    response_model=CKTheoryResult,
    summary="Generate design alternatives using C-K Theory",
    description="""
    Generate 3 design alternatives using Concept-Knowledge Design Theory:

    1. **Concept Exploration**: Generate 3 distinct design concepts
    2. **Alternative Generation**: Develop detailed alternatives (A, B, C) in parallel
    3. **RICE Scoring**: Calculate (Reach × Impact × Confidence) / Effort for each
    4. **Trade-off Analysis**: Compare alternatives and recommend best option

    **Performance**: Target <45 seconds for complete analysis.

    **Features**:
    - Parallel alternative generation (3 concurrent threads)
    - Automatic RICE score calculation
    - Sequential + Context7 MCP integration
    - Obsidian knowledge base integration
    - Learning from user feedback

    **Use Cases**:
    - System architecture design
    - Technology stack selection
    - Feature implementation approaches
    - Performance optimization strategies
    """,
    response_description="Complete C-K Theory result with 3 alternatives and trade-off analysis"
)
async def generate_design(
    request: CKTheoryRequest
) -> CKTheoryResult:
    """
    Generate design alternatives using C-K Theory

    Args:
        request: C-K Theory request with challenge and optional constraints

    Returns:
        Complete design with 3 alternatives and trade-off analysis

    Raises:
        HTTPException: If design generation fails

    Example Request:
        ```json
        {
            "challenge": "Design an authentication system that supports multiple providers",
            "constraints": {
                "budget": "2 weeks",
                "team_size": 2,
                "security_requirement": "high",
                "complexity": "medium"
            },
            "project": "UDO-Development-Platform"
        }
        ```

    Example Response:
        ```json
        {
            "id": "ck-2025-11-20-xyz789",
            "challenge": "Design an authentication system...",
            "alternatives": [
                {
                    "id": "A",
                    "title": "JWT + OAuth2 Hybrid Authentication",
                    "rice": {"score": 6.72},
                    ...
                },
                {
                    "id": "B",
                    "title": "Session-Based Authentication",
                    "rice": {"score": 5.40},
                    ...
                },
                {
                    "id": "C",
                    "title": "Passwordless + WebAuthn",
                    "rice": {"score": 6.30},
                    ...
                }
            ],
            "tradeoff_analysis": {
                "summary": "Alternative A offers the best balance...",
                "recommendation": "Choose Alternative A because..."
            },
            "total_duration_ms": 42000,
            "obsidian_path": "개발일지/2025-11-20/CK-Design-Auth-System.md"
        }
        ```
    """
    try:
        logger.info(f"Generating design for: {request.challenge[:50]}...")

        result = await ck_theory_service.generate_design(request)

        # Extract recommended alternative for logging
        recommended_id = result.tradeoff_analysis.recommendation[:50]

        logger.info(
            f"Design generated: {result.id} in {result.total_duration_ms}ms "
            f"(alternatives: {', '.join(a.id for a in result.alternatives)}, "
            f"recommended: {recommended_id[:20]}...)"
        )

        return result

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )
    except RuntimeError as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Design generation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/{design_id}",
    response_model=CKTheoryResult,
    summary="Get design by ID",
    description="Retrieve a specific design by its unique identifier",
    response_description="Complete design result"
)
async def get_design(
    design_id: str = Path(
        ...,
        description="Unique design ID (format: ck-YYYY-MM-DD-{hash})",
        example="ck-2025-11-20-xyz789"
    )
) -> CKTheoryResult:
    """
    Get design by ID

    Args:
        design_id: Unique design identifier

    Returns:
        Complete design result with all alternatives

    Raises:
        HTTPException: If design not found or retrieval fails
    """
    try:
        logger.info(f"Retrieving design: {design_id}")

        result = await ck_theory_service.get_design(design_id)

        if result is None:
            logger.warning(f"Design not found: {design_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Design not found: {design_id}"
            )

        logger.info(f"Retrieved design: {design_id}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retrieval error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve design: {str(e)}"
        )


@router.get(
    "",
    response_model=List[DesignSummary],
    summary="List recent designs",
    description="""
    List recent design explorations with pagination support.

    Results are sorted by creation time (newest first).

    Each summary includes:
    - Design ID and challenge
    - Recommended alternative
    - Average RICE score across all alternatives
    - Generation time and project
    """,
    response_description="List of design summaries"
)
async def list_designs(
    project: Optional[str] = Query(
        None,
        description="Filter by project name",
        example="UDO-Development-Platform"
    ),
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of results"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Pagination offset"
    )
) -> List[DesignSummary]:
    """
    List recent designs

    Args:
        project: Optional project filter
        limit: Maximum results (1-100)
        offset: Pagination offset

    Returns:
        List of design summaries

    Raises:
        HTTPException: If listing fails
    """
    try:
        logger.info(f"Listing designs (project={project}, limit={limit}, offset={offset})")

        summaries = await ck_theory_service.list_designs(
            project=project,
            limit=limit,
            offset=offset
        )

        logger.info(f"Retrieved {len(summaries)} designs")
        return summaries

    except Exception as e:
        logger.error(f"Listing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list designs: {str(e)}"
        )


@router.post(
    "/{design_id}/feedback",
    summary="Add feedback for design",
    description="""
    Add feedback for a design exploration.

    Feedback is used for:
    - Learning which alternatives work best
    - Improving future recommendations
    - Tracking design decision outcomes

    Include:
    - Rating (1-5 stars)
    - Selected alternative (if implemented)
    - Implementation outcome (success/partial/failure)
    - Comments (optional)
    """,
    response_description="Feedback confirmation"
)
async def add_feedback(
    design_id: str = Path(
        ...,
        description="Design ID to provide feedback for",
        example="ck-2025-11-20-xyz789"
    ),
    feedback: DesignFeedback = Body(
        ...,
        description="Feedback data",
        example={
            "design_id": "ck-2025-11-20-xyz789",
            "alternative_id": "A",
            "rating": 5,
            "comments": "Excellent balance of security and flexibility",
            "selected_alternative": "A",
            "outcome": "success"
        }
    )
) -> dict:
    """
    Add feedback for design

    Args:
        design_id: Design identifier
        feedback: Feedback data

    Returns:
        Feedback confirmation

    Raises:
        HTTPException: If feedback submission fails
    """
    try:
        # Validate design_id matches feedback
        if feedback.design_id != design_id:
            raise HTTPException(
                status_code=400,
                detail=f"Design ID mismatch: path={design_id}, body={feedback.design_id}"
            )

        logger.info(
            f"Adding feedback for design {design_id}: "
            f"rating={feedback.rating}, selected={feedback.selected_alternative}"
        )

        success = await ck_theory_service.add_feedback(design_id, feedback)

        if not success:
            logger.warning(f"Failed to add feedback for design: {design_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to add feedback for design: {design_id}"
            )

        logger.info(f"Feedback added for design: {design_id}")
        return {
            "message": f"Feedback added successfully for design {design_id}",
            "design_id": design_id,
            "rating": feedback.rating,
            "selected_alternative": feedback.selected_alternative,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add feedback: {str(e)}"
        )


@router.get(
    "/{design_id}/feedback",
    response_model=List[DesignFeedback],
    summary="Get feedback for design",
    description="Retrieve all feedback for a specific design",
    response_description="List of feedback entries"
)
async def get_feedback(
    design_id: str = Path(
        ...,
        description="Design ID to get feedback for",
        example="ck-2025-11-20-xyz789"
    )
) -> List[DesignFeedback]:
    """
    Get feedback for design

    Args:
        design_id: Design identifier

    Returns:
        List of feedback entries

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info(f"Retrieving feedback for design: {design_id}")

        feedback_list = await ck_theory_service.get_feedback(design_id)

        logger.info(f"Retrieved {len(feedback_list)} feedback entries for design: {design_id}")
        return feedback_list

    except Exception as e:
        logger.error(f"Feedback retrieval error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve feedback: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check C-K Theory service health",
    response_description="Service health status"
)
async def health_check() -> dict:
    """
    Health check endpoint

    Returns:
        Service health status
    """
    return {
        "status": "healthy",
        "service": "ck-theory",
        "version": "1.0.0",
        "features": {
            "sequential_mcp": ck_theory_service.sequential_mcp is not None,
            "context7_mcp": ck_theory_service.context7_mcp is not None,
            "obsidian_sync": ck_theory_service.obsidian_service is not None,
            "caching": ck_theory_service.cache_service is not None,
            "feedback_learning": True,
        }
    }
