"""
RL Knowledge Router - Training-free GRPO based knowledge optimization

Implements ArXiv 2510.08191 concepts:
- Token Prior: Past decision storage for knowledge reuse
- Group Relative: Compare patterns within domain
- Policy Optimization: Improve predictions based on feedback

Endpoints:
- GET /api/rl/token-prior/stats - Token Prior statistics
- GET /api/rl/patterns/{domain} - Get patterns for a domain
- GET /api/rl/best-solution - Get best solution for a problem
- POST /api/rl/pattern - Record a new knowledge pattern
- POST /api/rl/experiment/attempt - Record experiment attempt
- GET /api/rl/experiments - List all experiments
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.rl_knowledge_optimizer import (  # noqa: E402
    KnowledgePattern,
    RLKnowledgeOptimizer,
)
from src.uncertainty_map_v3 import UncertaintyWithTokenPrior  # noqa: E402

router = APIRouter(prefix="/api/rl", tags=["rl-knowledge"])

# Initialize services (singleton pattern)
_token_prior_instance: Optional[UncertaintyWithTokenPrior] = None
_optimizer_instance: Optional[RLKnowledgeOptimizer] = None


def get_token_prior() -> UncertaintyWithTokenPrior:
    """Get or create Token Prior instance."""
    global _token_prior_instance
    if _token_prior_instance is None:
        _token_prior_instance = UncertaintyWithTokenPrior()
    return _token_prior_instance


def get_optimizer() -> RLKnowledgeOptimizer:
    """Get or create RL Knowledge Optimizer instance."""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = RLKnowledgeOptimizer()
    return _optimizer_instance


# ============================================================================
# Pydantic Models
# ============================================================================


class TokenPriorStats(BaseModel):
    """Token Prior statistics response."""

    total_decisions: int = Field(..., description="Total decisions recorded")
    unique_hours: int = Field(..., description="Unique prediction hours")
    validated_count: int = Field(..., description="Validated predictions count")
    accuracy: Optional[float] = Field(None, description="Overall accuracy if available")
    last_updated: Optional[str] = Field(None, description="Last update timestamp")


class PatternCreate(BaseModel):
    """Request to create a new knowledge pattern."""

    domain: str = Field(..., description="Problem domain (e.g., 'websocket', 'auth')")
    name: str = Field(..., description="Pattern name/identifier")
    resolution_time_minutes: int = Field(..., ge=0, description="Time to resolve in minutes")
    recurrence_count: int = Field(0, ge=0, description="How many times this recurred")
    side_effects: int = Field(0, ge=0, le=3, description="Side effects level (0-3)")
    solution_description: str = Field(..., description="Description of the solution")
    tags: List[str] = Field(default_factory=list, description="Associated tags")


class PatternResponse(BaseModel):
    """Pattern with computed score."""

    domain: str
    name: str
    score: float
    resolution_time_minutes: int
    recurrence_count: int
    side_effects: int
    solution_description: str
    tags: List[str]


class BestSolutionResponse(BaseModel):
    """Best solution recommendation."""

    found: bool
    domain: str
    pattern_name: Optional[str] = None
    score: Optional[float] = None
    solution: Optional[str] = None
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)


class ExperimentAttemptCreate(BaseModel):
    """Request to record an experiment attempt."""

    problem_id: str = Field(..., description="Unique problem identifier")
    approach: str = Field(..., description="Approach/solution tried")
    result: str = Field(..., description="Result: 'success', 'partial', 'failure'")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    notes: Optional[str] = Field(None, description="Additional notes")


class ExperimentResponse(BaseModel):
    """Experiment with all attempts."""

    problem_id: str
    attempts: List[Dict[str, Any]]
    best_approach: Optional[str]
    created_at: str


# ============================================================================
# Token Prior Endpoints
# ============================================================================


@router.get("/token-prior/stats", response_model=TokenPriorStats)
async def get_token_prior_stats():
    """
    Get Token Prior statistics.

    Returns metrics about stored past decisions for knowledge reuse.
    """
    try:
        token_prior = get_token_prior()
        stats = token_prior.get_token_prior_stats()

        return TokenPriorStats(
            total_decisions=stats.get("total_decisions", 0),
            unique_hours=stats.get("unique_hours", 0),
            validated_count=stats.get("validated_count", 0),
            accuracy=stats.get("accuracy"),
            last_updated=stats.get("last_updated"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/token-prior/validate/{decision_id}")
async def validate_decision(
    decision_id: str,
    actual_level: float = Query(..., ge=0.0, le=1.0, description="Actual uncertainty level"),
):
    """
    Validate a past prediction with actual outcome.

    Used for Policy Optimization - improves future predictions.
    """
    try:
        token_prior = get_token_prior()
        result = token_prior.validate_prediction(decision_id, actual_level)

        if not result.get("validated"):
            raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found or already validated")

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


# ============================================================================
# Pattern Scoring Endpoints
# ============================================================================


@router.get("/patterns/{domain}", response_model=List[PatternResponse])
async def get_domain_patterns(
    domain: str,
    limit: int = Query(10, ge=1, le=100, description="Maximum patterns to return"),
):
    """
    Get all patterns for a domain, ranked by Group Relative Score.

    Score formula: 0.4*time_efficiency + 0.4*permanence + 0.2*safety
    """
    try:
        optimizer = get_optimizer()
        patterns = optimizer.get_domain_patterns(domain)

        if not patterns:
            return []

        # Sort by score descending
        sorted_patterns = sorted(patterns, key=lambda x: x.get("score", 0), reverse=True)

        return [
            PatternResponse(
                domain=p["pattern"].domain,
                name=p["pattern"].name,
                score=p["score"],
                resolution_time_minutes=p["pattern"].resolution_time_minutes,
                recurrence_count=p["pattern"].recurrence_count,
                side_effects=p["pattern"].side_effects,
                solution_description=p["pattern"].solution_description,
                tags=p["pattern"].tags,
            )
            for p in sorted_patterns[:limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patterns: {str(e)}")


@router.post("/pattern", response_model=PatternResponse)
async def create_pattern(pattern: PatternCreate):
    """
    Record a new knowledge pattern.

    The pattern will be scored relative to other patterns in the same domain.
    """
    try:
        optimizer = get_optimizer()

        knowledge_pattern = KnowledgePattern(
            domain=pattern.domain,
            name=pattern.name,
            resolution_time_minutes=pattern.resolution_time_minutes,
            recurrence_count=pattern.recurrence_count,
            side_effects=pattern.side_effects,
            solution_description=pattern.solution_description,
            tags=pattern.tags,
        )

        optimizer.add_pattern(knowledge_pattern)

        # Get the score
        all_patterns = optimizer.get_domain_patterns(pattern.domain)
        pattern_data = next((p for p in all_patterns if p["pattern"].name == pattern.name), None)

        score = pattern_data["score"] if pattern_data else 0.0

        return PatternResponse(
            domain=pattern.domain,
            name=pattern.name,
            score=score,
            resolution_time_minutes=pattern.resolution_time_minutes,
            recurrence_count=pattern.recurrence_count,
            side_effects=pattern.side_effects,
            solution_description=pattern.solution_description,
            tags=pattern.tags,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pattern: {str(e)}")


@router.get("/best-solution", response_model=BestSolutionResponse)
async def get_best_solution(
    domain: str = Query(..., description="Problem domain"),
    keywords: Optional[str] = Query(None, description="Comma-separated keywords"),
):
    """
    Get the best solution for a problem based on policy optimization.

    Returns the highest-scored pattern for the domain, optionally filtered by keywords.
    """
    try:
        optimizer = get_optimizer()

        keyword_list = keywords.split(",") if keywords else None
        result = optimizer.get_best_solution(domain, keyword_list)

        if not result:
            return BestSolutionResponse(found=False, domain=domain)

        # Get alternatives (top 3 excluding best)
        all_patterns = optimizer.get_domain_patterns(domain)
        alternatives = [
            {"name": p["pattern"].name, "score": p["score"]}
            for p in sorted(all_patterns, key=lambda x: x["score"], reverse=True)[1:4]
        ]

        return BestSolutionResponse(
            found=True,
            domain=domain,
            pattern_name=result["pattern"].name,
            score=result["score"],
            solution=result["pattern"].solution_description,
            alternatives=alternatives,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get solution: {str(e)}")


# ============================================================================
# Experiment Tracking Endpoints
# ============================================================================


@router.post("/experiment/attempt")
async def record_experiment_attempt(attempt: ExperimentAttemptCreate):
    """
    Record an experiment attempt (multi-rollout tracking).

    Preserves all solution attempts including failures for knowledge retention.
    """
    try:
        optimizer = get_optimizer()

        optimizer.tracker.record_attempt(
            problem_id=attempt.problem_id,
            approach=attempt.approach,
            result=attempt.result,
            metrics=attempt.metrics,
            notes=attempt.notes,
        )

        return {"status": "recorded", "problem_id": attempt.problem_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record attempt: {str(e)}")


@router.get("/experiments", response_model=List[ExperimentResponse])
async def list_experiments(
    limit: int = Query(20, ge=1, le=100, description="Maximum experiments to return"),
):
    """
    List all tracked experiments.

    Returns experiments with all their attempts and best approach.
    """
    try:
        optimizer = get_optimizer()
        # Access experiments dictionary directly (no get_all_experiments method)
        experiments = list(optimizer.tracker.experiments.values())

        return [
            ExperimentResponse(
                problem_id=exp.problem_id,
                attempts=[{"approach": a.approach, "result": a.result, "reason": a.reason} for a in exp.attempts],
                best_approach=exp.winning_approach,
                created_at=exp.created_at.isoformat() if exp.created_at else datetime.now(timezone.utc).isoformat(),
            )
            for exp in experiments[:limit]
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list experiments: {str(e)}")


@router.get("/experiment/{problem_id}", response_model=ExperimentResponse)
async def get_experiment(problem_id: str):
    """
    Get a specific experiment by problem ID.
    """
    try:
        optimizer = get_optimizer()
        # Access experiments dictionary directly (no get_experiment method)
        exp = optimizer.tracker.experiments.get(problem_id)

        if not exp:
            raise HTTPException(status_code=404, detail=f"Experiment {problem_id} not found")

        return ExperimentResponse(
            problem_id=exp.problem_id,
            attempts=[{"approach": a.approach, "result": a.result, "reason": a.reason} for a in exp.attempts],
            best_approach=exp.winning_approach,
            created_at=exp.created_at.isoformat() if exp.created_at else datetime.now(timezone.utc).isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get experiment: {str(e)}")


# ============================================================================
# Summary Endpoint
# ============================================================================


@router.get("/summary")
async def get_rl_summary():
    """
    Get a complete summary of RL Knowledge system status.

    Combines Token Prior stats, pattern counts, and experiment counts.
    """
    try:
        token_prior = get_token_prior()
        optimizer = get_optimizer()

        token_stats = token_prior.get_token_prior_stats()

        # Count patterns by domain from policy's pattern store
        all_domains = {}
        total_patterns = 0
        for domain, patterns in optimizer.policy._pattern_store.items():
            all_domains[domain] = len(patterns)
            total_patterns += len(patterns)

        # Count experiments from tracker
        experiments = list(optimizer.tracker.experiments.values())

        return {
            "token_prior": {
                "total_decisions": token_stats.get("total_decisions", 0),
                "validated_count": token_stats.get("validated_count", 0),
                "accuracy": token_stats.get("accuracy"),
            },
            "patterns": {
                "total": total_patterns,
                "by_domain": all_domains,
            },
            "experiments": {
                "total": len(experiments),
                "with_success": sum(1 for e in experiments if e.winning_approach is not None),
            },
            "system_status": "operational",
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
