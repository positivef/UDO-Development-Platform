"""
Uncertainty Map Router

API endpoints for Uncertainty Map v3.0 integration
Provides real-time uncertainty status, predictions, and mitigation strategies
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Tuple
from datetime import datetime
import logging

from app.models.uncertainty import (
    UncertaintyStatusResponse,
    UncertaintyVectorResponse,
    MitigationStrategyResponse,
    PredictiveModelResponse,
    UncertaintyStateEnum,
    ContextAnalysisRequest,
    MitigationAckRequest,
    MitigationAckResponse,
    BayesianConfidenceRequest,
    BayesianConfidenceResponse,
)
from app.models.uncertainty_time_integration import (
    UncertaintyAwareTrackingRequest,
    UncertaintyAwareTrackingResponse,
    CorrelationAnalysisResponse,
    AdjustedBaselineResponse,
)
from app.core.circuit_breaker import CircuitBreaker, SimpleTTLCache
from app.services.session_manager_v2 import get_session_manager
from app.services.bayesian_confidence import calculate_bayesian_confidence

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/uncertainty",
    tags=["uncertainty"],
    responses={
        404: {"description": "UDO system not available"},
        503: {"description": "Uncertainty Map not initialized"}
    }
)

# Lightweight circuit breaker / cache (in-memory)
uncertainty_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
status_cache = SimpleTTLCache()

# TTL map by uncertainty state
STATE_TTL_SECONDS = {
    "DETERMINISTIC": 3600,   # 1h
    "PROBABILISTIC": 1800,   # 30m
    "QUANTUM": 900,          # 15m
    "CHAOTIC": 300,          # 5m
    "VOID": 60,              # 1m
}

def get_uncertainty_map():
    """Dependency to get UncertaintyMap instance from global UDO system"""
    import sys

    # Get udo_system from backend.main module (correct module name)
    main_module = sys.modules.get('backend.main')
    if not main_module:
        # Fallback: try 'main' for backwards compatibility
        main_module = sys.modules.get('main')

    if not main_module:
        raise HTTPException(
            status_code=503,
            detail="UDO system not initialized. Uncertainty Map unavailable."
        )

    udo_system = getattr(main_module, 'udo_system', None)
    if not udo_system:
        raise HTTPException(
            status_code=503,
            detail="UDO system not initialized. Uncertainty Map unavailable."
        )

    uncertainty_map = udo_system.components.get('uncertainty')
    if not uncertainty_map:
        raise HTTPException(
            status_code=503,
            detail="Uncertainty Map component not initialized"
        )

    return uncertainty_map


def _build_context() -> Tuple[str, dict]:
    """Build a lightweight context from UDO if available."""
    import sys

    current_phase = "implementation"
    has_code = True

    main_module = sys.modules.get('main')
    if main_module:
        udo_system = getattr(main_module, 'udo_system', None)
        if udo_system and hasattr(udo_system, 'udo'):
            udo_instance = udo_system.udo
            if hasattr(udo_instance, 'current_phase'):
                current_phase = udo_instance.current_phase

    context = {
        "phase": current_phase,
        "has_code": has_code,
        "validation_score": 0.7,
        "team_size": 3,
        "timeline_weeks": 8
    }
    return current_phase, context


def _get_ttl_for_state(state_enum: UncertaintyStateEnum) -> int:
    return STATE_TTL_SECONDS.get(state_enum.name, 300)


@router.get("/status", response_model=UncertaintyStatusResponse)
@uncertainty_breaker
async def get_uncertainty_status(
    uncertainty_map = Depends(get_uncertainty_map)
):
    """
    Get current uncertainty status with predictions and mitigation strategies.
    Applies lightweight TTL caching and circuit breaker for resilience.
    """
    try:
        # Cache hit check
        cached = status_cache.get("status")
        if cached:
            return cached

        current_phase, context = _build_context()

        vector, state = uncertainty_map.analyze_context(context)
        prediction_model = uncertainty_map.predict_evolution(vector, phase=current_phase, hours=24)
        mitigations = uncertainty_map.generate_mitigations(vector, state)
        mitigations.sort(key=lambda m: m.roi(), reverse=True)

        vector_response = UncertaintyVectorResponse(
            technical=vector.technical,
            market=vector.market,
            resource=vector.resource,
            timeline=vector.timeline,
            quality=vector.quality,
            magnitude=vector.magnitude(),
            dominant_dimension=vector.dominant_dimension()
        )

        mitigation_responses = [
            MitigationStrategyResponse(
                id=m.id,
                uncertainty_id=m.uncertainty_id,
                action=m.action,
                priority=m.priority,
                estimated_impact=m.estimated_impact,
                estimated_cost=m.estimated_cost,
                prerequisites=m.prerequisites,
                success_probability=m.success_probability,
                fallback_strategy=m.fallback_strategy,
                roi=m.roi()
            )
            for m in mitigations
        ]

        prediction_response = PredictiveModelResponse(
            trend=prediction_model.trend,
            velocity=prediction_model.velocity,
            acceleration=prediction_model.acceleration,
            predicted_resolution=prediction_model.predicted_resolution,
            confidence_interval_lower=prediction_model.confidence_interval[0],
            confidence_interval_upper=prediction_model.confidence_interval[1]
        )

        state_enum = UncertaintyStateEnum(state.value)
        confidence_score = 1.0 - vector.magnitude()

        response = UncertaintyStatusResponse(
            vector=vector_response,
            state=state_enum,
            confidence_score=confidence_score,
            prediction=prediction_response,
            mitigations=mitigation_responses,
            timestamp=datetime.now()
        )

        ttl = _get_ttl_for_state(state_enum)
        status_cache.set("status", response, ttl_seconds=ttl)
        return response

    except Exception as e:
        logger.error(f"Failed to get uncertainty status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get uncertainty status: {str(e)}")


@router.post("/ack/{mitigation_id}", response_model=MitigationAckResponse)
@uncertainty_breaker
async def acknowledge_mitigation(
    mitigation_id: str,
    request: MitigationAckRequest,
    uncertainty_map = Depends(get_uncertainty_map)
):
    """
    Acknowledge a mitigation strategy and apply its impact to the uncertainty vector.

    - Finds mitigation by ID (from regenerated list)
    - Applies estimated_impact (or override) to a target dimension
    - Reclassifies state and returns updated vector
    """
    try:
        target_id = request.mitigation_id or mitigation_id

        current_phase, context = _build_context()
        vector, state = uncertainty_map.analyze_context(context)

        # Regenerate mitigations to resolve ID
        mitigations = uncertainty_map.generate_mitigations(vector, state)
        mitigations.sort(key=lambda m: m.roi(), reverse=True)

        target = next((m for m in mitigations if m.id == target_id), None)
        if not target:
            raise HTTPException(status_code=404, detail=f"Mitigation {mitigation_id} not found")

        applied_impact = request.applied_impact if request.applied_impact is not None else target.estimated_impact
        dimension = request.dimension or target.dominant_dimension if hasattr(target, "dominant_dimension") else None
        if not dimension:
            dimension = vector.dominant_dimension()

        # Apply impact to chosen dimension (work with dataclass then convert)
        adjusted_vector = type(vector)(
            technical=max(0.0, vector.technical - applied_impact) if dimension == "technical" else vector.technical,
            market=max(0.0, vector.market - applied_impact) if dimension == "market" else vector.market,
            resource=max(0.0, vector.resource - applied_impact) if dimension == "resource" else vector.resource,
            timeline=max(0.0, vector.timeline - applied_impact) if dimension == "timeline" else vector.timeline,
            quality=max(0.0, vector.quality - applied_impact) if dimension == "quality" else vector.quality,
        )

        magnitude = adjusted_vector.magnitude()
        dominant_dim = adjusted_vector.dominant_dimension()
        updated_state_enum = UncertaintyStateEnum(uncertainty_map.classify_state(magnitude).value)
        confidence_score = 1.0 - magnitude

        updated_vector = UncertaintyVectorResponse(
            technical=adjusted_vector.technical,
            market=adjusted_vector.market,
            resource=adjusted_vector.resource,
            timeline=adjusted_vector.timeline,
            quality=adjusted_vector.quality,
            magnitude=magnitude,
            dominant_dimension=dominant_dim
        )

        # Invalidate cache to ensure next status reflects change
        status_cache.set("status", None, ttl_seconds=1)

        # Broadcast update (best-effort; ignore failures)
        try:
            session_manager = await get_session_manager()
            await session_manager.broadcast_to_all({
                "type": "uncertainty_update",
                "state": updated_state_enum.value,
                "confidence": confidence_score,
                "vector": updated_vector.model_dump()
            })
        except Exception as broadcast_err:
            logger.debug(f"Broadcast skipped/failed: {broadcast_err}")

        return MitigationAckResponse(
            success=True,
            mitigation_id=target_id,
            message=f"Applied mitigation to {dimension}, impact {applied_impact:.2f}",
            updated_vector=updated_vector,
            updated_state=updated_state_enum,
            confidence_score=confidence_score,
            timestamp=datetime.now()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge mitigation {mitigation_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge mitigation: {str(e)}")


@router.post("/analyze", response_model=UncertaintyStatusResponse)
async def analyze_context(
    request: ContextAnalysisRequest,
    uncertainty_map = Depends(get_uncertainty_map)
):
    """
    Analyze a specific context and generate uncertainty assessment

    Request Body:
        - **phase**: Development phase (ideation/design/mvp/implementation/testing)
        - **has_code**: Whether code exists
        - **validation_score**: Market validation score (0-1)
        - **team_size**: Team size (>= 1)
        - **timeline_weeks**: Timeline in weeks (>= 1)

    Returns: Same as /status endpoint with context-specific analysis
    """
    try:
        # Build context dictionary
        context = {
            "phase": request.phase,
            "has_code": request.has_code,
            "validation_score": request.validation_score,
            "team_size": request.team_size,
            "timeline_weeks": request.timeline_weeks
        }

        # Analyze context
        vector, state = uncertainty_map.analyze_context(context)

        # Get prediction (24 hours ahead)
        prediction_model = uncertainty_map.predict_evolution(vector, phase=request.phase, hours=24)

        # Generate mitigation strategies
        mitigations = uncertainty_map.generate_mitigations(vector, state)
        mitigations.sort(key=lambda m: m.roi(), reverse=True)

        # Convert to response models
        vector_response = UncertaintyVectorResponse(
            technical=vector.technical,
            market=vector.market,
            resource=vector.resource,
            timeline=vector.timeline,
            quality=vector.quality,
            magnitude=vector.magnitude(),
            dominant_dimension=vector.dominant_dimension()
        )

        mitigation_responses = [
            MitigationStrategyResponse(
                id=m.id,
                uncertainty_id=m.uncertainty_id,
                action=m.action,
                priority=m.priority,
                estimated_impact=m.estimated_impact,
                estimated_cost=m.estimated_cost,
                prerequisites=m.prerequisites,
                success_probability=m.success_probability,
                fallback_strategy=m.fallback_strategy,
                roi=m.roi()
            )
            for m in mitigations
        ]

        prediction_response = PredictiveModelResponse(
            trend=prediction_model.trend,
            velocity=prediction_model.velocity,
            acceleration=prediction_model.acceleration,
            predicted_resolution=prediction_model.predicted_resolution,
            confidence_interval_lower=prediction_model.confidence_interval[0],
            confidence_interval_upper=prediction_model.confidence_interval[1]
        )

        state_enum = UncertaintyStateEnum(state.value)
        confidence_score = 1.0 - vector.magnitude()

        return UncertaintyStatusResponse(
            vector=vector_response,
            state=state_enum,
            confidence_score=confidence_score,
            prediction=prediction_response,
            mitigations=mitigation_responses,
            timestamp=datetime.now()
        )

    except Exception as e:
        logger.error(f"Failed to analyze context: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze context: {str(e)}")


@router.get("/health")
async def uncertainty_health_check():
    """Health check endpoint for Uncertainty Map availability"""
    try:
        import sys

        # Get udo_system from main module if already imported
        main_module = sys.modules.get('main')
        if not main_module:
            return {
                "status": "unavailable",
                "message": "UDO system not initialized"
            }

        udo_system = getattr(main_module, 'udo_system', None)
        if not udo_system:
            return {
                "status": "unavailable",
                "message": "UDO system not initialized"
            }

        uncertainty_map = udo_system.components.get('uncertainty')
        if not uncertainty_map:
            return {
                "status": "unavailable",
                "message": "Uncertainty Map component not initialized"
            }

        return {
            "status": "available",
            "project_name": uncertainty_map.project_name,
            "ml_available": hasattr(uncertainty_map, 'is_trained') and uncertainty_map.is_trained,
            "message": "Uncertainty Map v3.0 operational"
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


# ============================================================================
# TIME TRACKING INTEGRATION ENDPOINTS (Phase 2)
# ============================================================================


@router.post("/track-with-uncertainty", response_model=UncertaintyAwareTrackingResponse)
async def start_uncertainty_aware_tracking(
    request: UncertaintyAwareTrackingRequest,
    uncertainty_map = Depends(get_uncertainty_map)
):
    """
    Start tracking with uncertainty awareness

    Combines time tracking with uncertainty analysis to provide:
    - Uncertainty-adjusted baseline estimates
    - Risk factor identification
    - Confidence scores for task completion

    This endpoint analyzes the uncertainty context and adjusts the baseline
    time estimate accordingly. Tasks with higher uncertainty get longer baselines.

    **Example Request:**
    ```json
    {
        "task_id": "auth_refactor_001",
        "task_type": "refactoring",
        "phase": "implementation",
        "ai_used": "claude",
        "uncertainty_context": {
            "phase": "implementation",
            "has_code": true,
            "validation_score": 0.7,
            "team_size": 3,
            "timeline_weeks": 8
        }
    }
    ```

    **Returns:**
    - Uncertainty vector and state classification
    - Adjusted baseline (standard baseline + uncertainty adjustment)
    - Confidence score and risk factors
    - Session ID for tracking
    """
    try:
        # Convert has_code boolean to files list format expected by uncertainty_map
        context = dict(request.uncertainty_context)
        if 'has_code' in context and 'files' not in context:
            # Convert has_code boolean to files list
            context['files'] = ['dummy.py'] if context.pop('has_code') else []

        # Analyze uncertainty context
        vector, state = uncertainty_map.analyze_context(context)

        # Get standard baseline from time tracking config
        from app.services.time_tracking_service import TimeTrackingService
        service = TimeTrackingService()  # For baseline lookup only
        standard_baseline = service._get_baseline_seconds(request.task_type)

        # Calculate uncertainty-adjusted baseline
        magnitude = vector.magnitude()

        # Adjustment multiplier based on uncertainty state
        state_multipliers = {
            "deterministic": 1.0,   # No adjustment needed
            "probabilistic": 1.2,   # 20% buffer
            "quantum": 1.5,         # 50% buffer
            "chaotic": 2.0,         # 100% buffer (double time)
            "void": 2.5             # 150% buffer
        }

        multiplier = state_multipliers.get(state.value, 1.0)
        adjusted_baseline = int(standard_baseline * multiplier)

        # Calculate confidence score (inverse of magnitude)
        confidence_score = max(0.0, 1.0 - magnitude)

        # Identify risk factors
        risk_factors = []

        if vector.technical > 0.5:
            risk_factors.append(f"High technical uncertainty ({vector.technical:.0%})")
        if vector.market > 0.5:
            risk_factors.append(f"High market uncertainty ({vector.market:.0%})")
        if vector.resource > 0.5:
            risk_factors.append(f"Resource constraints ({vector.resource:.0%})")
        if vector.timeline > 0.5:
            risk_factors.append(f"Timeline pressure ({vector.timeline:.0%})")
        if vector.quality > 0.5:
            risk_factors.append(f"Quality uncertainty ({vector.quality:.0%})")

        if state.value in ["quantum", "chaotic", "void"]:
            risk_factors.append(f"{state.value.capitalize()} state - multiple possible outcomes")

        if not risk_factors:
            risk_factors.append("Low uncertainty - task should complete smoothly")

        # Create session ID (in real implementation, would start actual tracking session)
        from uuid import uuid4
        session_id = uuid4()

        # Convert to response models
        vector_response = UncertaintyVectorResponse(
            technical=vector.technical,
            market=vector.market,
            resource=vector.resource,
            timeline=vector.timeline,
            quality=vector.quality,
            magnitude=magnitude,
            dominant_dimension=vector.dominant_dimension()
        )

        state_enum = UncertaintyStateEnum(state.value)

        return UncertaintyAwareTrackingResponse(
            success=True,
            session_id=session_id,
            message=f"Started uncertainty-aware tracking for task {request.task_id}",
            baseline_seconds=standard_baseline,
            uncertainty_vector=vector_response,
            uncertainty_state=state_enum,
            adjusted_baseline_seconds=adjusted_baseline,
            confidence_score=confidence_score,
            risk_factors=risk_factors
        )

    except Exception as e:
        logger.error(f"Failed to start uncertainty-aware tracking: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start tracking: {str(e)}")


@router.post("/adjusted-baseline/{task_type}/{phase}", response_model=AdjustedBaselineResponse)
async def get_adjusted_baseline(
    task_type: str,
    phase: str,
    request: ContextAnalysisRequest,
    uncertainty_map = Depends(get_uncertainty_map)
):
    """
    Get uncertainty-adjusted baseline estimate

    Provides a time estimate that accounts for project uncertainty.
    More uncertain projects get longer estimates with wider confidence intervals.

    **Query Parameters:**
    - `task_type`: Type of task (implementation, testing, etc.)
    - `phase`: Development phase (ideation, design, implementation, etc.)
    - `uncertainty_context`: JSON object with context (embedded in request body for POST)

    **Example:**
    ```
    GET /api/uncertainty/adjusted-baseline/implementation/implementation
    ```

    With body:
    ```json
    {
        "phase": "implementation",
        "has_code": true,
        "validation_score": 0.7,
        "team_size": 3,
        "timeline_weeks": 8
    }
    ```

    **Returns:**
    - Standard baseline vs adjusted baseline
    - Confidence intervals (lower/upper bounds)
    - Adjustment factors explanation
    """
    try:
        # Build context from request
        #  Convert has_code to files list format expected by uncertainty_map
        context = {
            "phase": request.phase,
            "files": ['dummy.py'] if request.has_code else [],
            "market_validation": request.validation_score,
            "team_size": request.team_size,
            "timeline_weeks": request.timeline_weeks
        }

        # Analyze uncertainty
        vector, state = uncertainty_map.analyze_context(context)
        magnitude = vector.magnitude()

        # Get standard baseline
        from app.services.time_tracking_service import TimeTrackingService
        from app.models.time_tracking import TaskType, Phase

        service = TimeTrackingService()
        task_type_enum = TaskType(task_type)
        standard_baseline = service._get_baseline_seconds(task_type_enum)

        # Calculate adjustment
        state_multipliers = {
            "deterministic": 1.0,
            "probabilistic": 1.2,
            "quantum": 1.5,
            "chaotic": 2.0,
            "void": 2.5
        }

        multiplier = state_multipliers.get(state.value, 1.0)
        adjusted_baseline = int(standard_baseline * multiplier)
        adjustment_percentage = (multiplier - 1.0) * 100

        # Confidence score and intervals
        confidence_score = max(0.0, 1.0 - magnitude)

        # Wider intervals for higher uncertainty
        interval_width = int(adjusted_baseline * magnitude * 0.5)
        confidence_interval_lower = max(0, adjusted_baseline - interval_width)
        confidence_interval_upper = adjusted_baseline + interval_width

        # Explain adjustment factors
        adjustment_factors = []
        adjustment_factors.append(f"{state.value.capitalize()} uncertainty state (+{(multiplier-1)*100:.0f}%)")

        if vector.dominant_dimension() == "timeline":
            adjustment_factors.append(f"Timeline uncertainty dominant (+{vector.timeline*100:.0f}%)")
        if vector.dominant_dimension() == "technical":
            adjustment_factors.append(f"Technical uncertainty dominant (+{vector.technical*100:.0f}%)")

        if phase == "implementation":
            adjustment_factors.append("Implementation phase complexity factor applied")

        vector_response = UncertaintyVectorResponse(
            technical=vector.technical,
            market=vector.market,
            resource=vector.resource,
            timeline=vector.timeline,
            quality=vector.quality,
            magnitude=magnitude,
            dominant_dimension=vector.dominant_dimension()
        )

        return AdjustedBaselineResponse(
            task_type=task_type_enum,
            phase=Phase(phase),
            standard_baseline_seconds=standard_baseline,
            uncertainty_vector=vector_response,
            uncertainty_state=UncertaintyStateEnum(state.value),
            adjusted_baseline_seconds=adjusted_baseline,
            adjustment_percentage=adjustment_percentage,
            confidence_score=confidence_score,
            confidence_interval_lower=confidence_interval_lower,
            confidence_interval_upper=confidence_interval_upper,
            adjustment_factors=adjustment_factors
        )

    except Exception as e:
        logger.error(f"Failed to get adjusted baseline: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate adjusted baseline: {str(e)}")


# ============================================================================
# BAYESIAN CONFIDENCE SCORING ENDPOINT (v3.0)
# ============================================================================


@router.post("/confidence", response_model=BayesianConfidenceResponse)
@uncertainty_breaker
async def calculate_confidence(
    request: BayesianConfidenceRequest
):
    """
    Calculate Bayesian confidence score with uncertainty classification.

    Uses Beta-Binomial conjugacy for efficient Bayesian inference with:
    - Phase-specific priors (ideation: 40%, testing: 80%)
    - Fast mode (<5ms) for real-time use
    - Full mode (10-20ms) with credible intervals
    - 5 uncertainty states (Deterministic → Void)
    - Automatic decision logic (GO/GO_WITH_CHECKPOINTS/NO_GO)
    - Actionable recommendations

    **Request Body:**
    ```json
    {
        "phase": "implementation",
        "context": {
            "phase": "implementation",
            "has_code": true,
            "validation_score": 0.7,
            "team_size": 3,
            "timeline_weeks": 8
        },
        "historical_outcomes": [true, true, false, true, true],
        "use_fast_mode": true
    }
    ```

    **Response:**
    - `confidence_score`: Bayesian posterior confidence (0-1)
    - `state`: Uncertainty state (deterministic/probabilistic/quantum/chaotic/void)
    - `decision`: GO/GO_WITH_CHECKPOINTS/NO_GO
    - `metadata`: Full statistical context (priors, likelihood, credible intervals)
    - `recommendations`: Actionable next steps based on state

    **Performance:**
    - Fast mode: <5ms (optimized for real-time)
    - Full mode: 10-20ms (includes credible intervals)

    **Uncertainty States:**
    - 🟢 DETERMINISTIC (<10%): High confidence, proceed normally
    - 🔵 PROBABILISTIC (10-30%): Good confidence, standard checkpoints
    - 🟠 QUANTUM (30-60%): Moderate uncertainty, increase monitoring
    - 🔴 CHAOTIC (60-90%): High uncertainty, proceed with caution
    - ⚫ VOID (>90%): Extreme uncertainty, do not proceed
    """
    try:
        # Call Bayesian service
        response = calculate_bayesian_confidence(request)

        # Log performance and state
        mode = "fast" if request.use_fast_mode else "full"
        logger.info(
            f"Bayesian confidence calculated: "
            f"phase={request.phase}, "
            f"confidence={response.confidence_score:.2f}, "
            f"state={response.state.value}, "
            f"decision={response.decision}, "
            f"mode={mode}"
        )

        return response

    except ValueError as e:
        # Handle validation errors (e.g., invalid phase)
        logger.error(f"Validation error in Bayesian confidence: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Failed to calculate Bayesian confidence: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate confidence: {str(e)}")
