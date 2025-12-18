"""
Constitutional API Router

Provides endpoints for UDO Constitution enforcement and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import logging

from app.core.constitutional_guard import ConstitutionalGuard, ValidationResult, Severity
from app.models.constitutional_violation import ConstitutionalViolation, ConstitutionalComplianceMetrics
from database import Database
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/constitution",
    tags=["constitution"],
    responses={404: {"description": "Not found"}}
)

# Pydantic models for request/response

class DesignReviewRequest(BaseModel):
    """Request for P1: Design Review First"""
    design_id: str
    risk_assessments: Dict[str, Any]
    user_approved: bool = False
    exemption_claimed: bool = False
    exemption_reason: Optional[str] = None


class ConfidenceValidationRequest(BaseModel):
    """Request for P2: Uncertainty Disclosure"""
    response_id: str
    ai_agent: str
    recommendation: str
    confidence: Dict[str, Any]
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class EvidenceValidationRequest(BaseModel):
    """Request for P3: Evidence-Based Decision"""
    claim_id: str
    type: str  # optimization, performance_improvement
    evidence: Dict[str, Any]
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None


class PhaseComplianceRequest(BaseModel):
    """Request for P4: Phase-Aware Compliance"""
    phase: str
    action: str
    quality_score: float
    completed_deliverables: List[str] = Field(default_factory=list)
    phase_transition_requested: bool = False


class PhaseTransitionRequest(BaseModel):
    """Request for phase transition validation"""
    current_phase: str
    next_phase: str
    quality_score: float
    completed_deliverables: List[str]
    approved: bool = False


class AIConsensusRequest(BaseModel):
    """Request for P5: Multi-AI Consistency"""
    decisions: List[Dict[str, Any]]


class ViolationResolveRequest(BaseModel):
    """Request to resolve a violation"""
    resolution_notes: str
    resolved_by: str


class ComplianceReportRequest(BaseModel):
    """Request for compliance report"""
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    article: Optional[str] = None
    severity: Optional[str] = None


# Dependency injection
def get_constitutional_guard():
    """Get ConstitutionalGuard instance"""
    return ConstitutionalGuard()


def get_database():
    """Get database instance"""
    return Database()


# [EMOJI]
# Constitution Endpoints
# [EMOJI]

@router.get("/")
async def get_constitution(guard: ConstitutionalGuard = Depends(get_constitutional_guard)):
    """
    Get full UDO Constitution (P1-P17)

    Returns:
        Complete constitution YAML as JSON
    """
    try:
        if not guard.constitution:
            raise HTTPException(status_code=500, detail="Constitution not loaded")

        return JSONResponse(content={
            "version": guard.constitution.get("version"),
            "effective_date": guard.constitution.get("effective_date"),
            "applies_to": guard.constitution.get("applies_to"),
            "articles": {
                k: v for k, v in guard.constitution.items()
                if k.startswith("P") and k[1:2].isdigit()
            },
            "enforcement": guard.constitution.get("enforcement"),
            "metrics": guard.constitution.get("metrics")
        })
    except Exception as e:
        logger.error(f"Error getting constitution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles")
async def list_articles(guard: ConstitutionalGuard = Depends(get_constitutional_guard)):
    """
    List all constitutional articles (P1-P17)

    Returns:
        List of articles with titles and priorities
    """
    try:
        articles = []
        for key, value in guard.constitution.items():
            if key.startswith("P") and key[1:2].isdigit():
                articles.append({
                    "article": key,
                    "title": value.get("title"),
                    "priority": value.get("priority"),
                    "description": value.get("description", "").split("\n")[0]
                })

        return JSONResponse(content={"articles": articles})
    except Exception as e:
        logger.error(f"Error listing articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/{article}")
async def get_article(article: str, guard: ConstitutionalGuard = Depends(get_constitutional_guard)):
    """
    Get specific constitutional article

    Args:
        article: Article ID (e.g., P1_design_review_first or just P1)

    Returns:
        Article details
    """
    try:
        # Support both P1 and P1_design_review_first formats
        if article.startswith("P") and len(article) <= 3:
            # Find full article name
            for key in guard.constitution.keys():
                if key.startswith(article + "_"):
                    article = key
                    break

        if article not in guard.constitution:
            raise HTTPException(status_code=404, detail=f"Article {article} not found")

        return JSONResponse(content=guard.constitution[article])
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article {article}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# [EMOJI]
# Validation Endpoints
# [EMOJI]

@router.post("/validate/design")
async def validate_design(
    request: DesignReviewRequest,
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    P1: Validate design review (8-Risk Check)

    Args:
        request: Design review request

    Returns:
        ValidationResult
    """
    try:
        result = await guard.validate_design(request.dict())
        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"Error validating design: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/confidence")
async def validate_confidence(
    request: ConfidenceValidationRequest,
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    P2: Validate uncertainty disclosure

    Args:
        request: Confidence validation request

    Returns:
        ValidationResult
    """
    try:
        result = await guard.validate_confidence(request.dict())
        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"Error validating confidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/evidence")
async def validate_evidence(
    request: EvidenceValidationRequest,
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    P3: Validate evidence-based decision

    Args:
        request: Evidence validation request

    Returns:
        ValidationResult
    """
    try:
        result = await guard.validate_evidence(request.dict())
        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"Error validating evidence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/phase-compliance")
async def validate_phase_compliance(
    request: PhaseComplianceRequest,
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    P4: Validate phase-aware compliance

    Args:
        request: Phase compliance request

    Returns:
        ValidationResult
    """
    try:
        result = await guard.validate_phase_compliance(
            request.phase,
            request.action,
            request.dict()
        )
        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"Error validating phase compliance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/phase-transition")
async def validate_phase_transition(
    request: PhaseTransitionRequest,
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    P4: Validate phase transition

    Args:
        request: Phase transition request

    Returns:
        ValidationResult
    """
    try:
        result = await guard.validate_phase_transition(
            request.current_phase,
            request.next_phase,
            request.dict()
        )
        return JSONResponse(content=result.to_dict())
    except Exception as e:
        logger.error(f"Error validating phase transition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/ai-consensus")
async def validate_ai_consensus(
    request: AIConsensusRequest,
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    P5: Validate multi-AI consistency and get consensus

    Args:
        request: AI consensus request with decisions from multiple AIs

    Returns:
        ValidationResult and consensus decision
    """
    try:
        result, consensus = await guard.validate_ai_consensus(request.decisions)
        return JSONResponse(content={
            "validation": result.to_dict(),
            "consensus": consensus
        })
    except Exception as e:
        logger.error(f"Error validating AI consensus: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# [EMOJI]
# Violation Management Endpoints
# [EMOJI]

@router.get("/violations")
async def get_violations(
    article: Optional[str] = Query(None, description="Filter by article"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    ai_agent: Optional[str] = Query(None, description="Filter by AI agent"),
    limit: int = Query(100, description="Maximum results"),
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    Get constitutional violations with optional filtering

    Args:
        article: Filter by article (e.g., P1_design_review_first)
        severity: Filter by severity (CRITICAL, HIGH, MEDIUM, LOW)
        resolved: Filter by resolution status
        ai_agent: Filter by AI agent (claude, codex, gemini)
        limit: Maximum number of results

    Returns:
        List of violations
    """
    try:
        severity_enum = Severity(severity) if severity else None
        violations = guard.get_violations(
            article=article,
            severity=severity_enum,
            resolved=resolved
        )

        # Filter by AI agent if specified
        if ai_agent:
            violations = [v for v in violations if v.get("ai_agent") == ai_agent]

        # Limit results
        violations = violations[:limit]

        return JSONResponse(content={
            "total": len(violations),
            "violations": violations
        })
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    except Exception as e:
        logger.error(f"Error getting violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/violations/report")
async def report_violation(
    article: str,
    violation_type: str,
    description: str,
    severity: str,
    ai_agent: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    Manually report a constitutional violation

    Args:
        article: Article ID (e.g., P1_design_review_first)
        violation_type: Type of violation
        description: Detailed description
        severity: CRITICAL, HIGH, MEDIUM, or LOW
        ai_agent: AI agent responsible (optional)
        metadata: Additional context (optional)

    Returns:
        Violation record
    """
    try:
        severity_enum = Severity(severity)
        guard._log_violation(
            article=article,
            violation_type=violation_type,
            description=description,
            severity=severity_enum,
            ai_agent=ai_agent,
            metadata=metadata
        )

        return JSONResponse(content={
            "message": "Violation reported",
            "article": article,
            "severity": severity
        })
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")
    except Exception as e:
        logger.error(f"Error reporting violation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/violations/export")
async def export_violations(
    filepath: Optional[str] = Query(None, description="Export file path"),
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    Export violations to JSON file

    Args:
        filepath: Optional export path (default: /tmp/violations_{timestamp}.json)

    Returns:
        Export confirmation
    """
    try:
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"/tmp/violations_{timestamp}.json"

        export_path = Path(filepath)
        guard.export_violations(export_path)

        return JSONResponse(content={
            "message": "Violations exported",
            "filepath": str(export_path),
            "count": len(guard.violation_log)
        })
    except Exception as e:
        logger.error(f"Error exporting violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# [EMOJI]
# Compliance Metrics Endpoints
# [EMOJI]

@router.get("/compliance/score")
async def get_compliance_score(guard: ConstitutionalGuard = Depends(get_constitutional_guard)):
    """
    Get overall compliance score

    Returns:
        Compliance score (0.0-1.0) and breakdown
    """
    try:
        score = guard.get_compliance_score()

        # Count violations by severity
        violations_by_severity = {}
        for v in guard.violation_log:
            if not v["resolved"]:
                severity = v["severity"]
                violations_by_severity[severity] = violations_by_severity.get(severity, 0) + 1

        # Count violations by article
        violations_by_article = {}
        for v in guard.violation_log:
            if not v["resolved"]:
                article = v["article"]
                violations_by_article[article] = violations_by_article.get(article, 0) + 1

        return JSONResponse(content={
            "compliance_score": score,
            "grade": "A" if score >= 0.95 else "B" if score >= 0.85 else "C" if score >= 0.75 else "D" if score >= 0.65 else "F",
            "total_violations": len([v for v in guard.violation_log if not v["resolved"]]),
            "violations_by_severity": violations_by_severity,
            "violations_by_article": violations_by_article
        })
    except Exception as e:
        logger.error(f"Error getting compliance score: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance/report")
async def get_compliance_report(
    period_start: Optional[str] = Query(None, description="ISO format date"),
    period_end: Optional[str] = Query(None, description="ISO format date"),
    guard: ConstitutionalGuard = Depends(get_constitutional_guard)
):
    """
    Get comprehensive compliance report

    Args:
        period_start: Start of reporting period (ISO format)
        period_end: End of reporting period (ISO format)

    Returns:
        Detailed compliance report
    """
    try:
        # Parse dates
        start_date = datetime.fromisoformat(period_start) if period_start else datetime.now() - timedelta(days=30)
        end_date = datetime.fromisoformat(period_end) if period_end else datetime.now()

        # Filter violations by date
        period_violations = [
            v for v in guard.violation_log
            if start_date <= datetime.fromisoformat(v["timestamp"]) <= end_date
        ]

        # Generate statistics
        stats = {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "total_violations": len(period_violations),
            "resolved_violations": len([v for v in period_violations if v["resolved"]]),
            "open_violations": len([v for v in period_violations if not v["resolved"]]),
            "by_severity": {},
            "by_article": {},
            "by_ai_agent": {},
            "compliance_score": guard.get_compliance_score()
        }

        # Aggregate statistics
        for v in period_violations:
            # By severity
            severity = v["severity"]
            if severity not in stats["by_severity"]:
                stats["by_severity"][severity] = {"total": 0, "resolved": 0}
            stats["by_severity"][severity]["total"] += 1
            if v["resolved"]:
                stats["by_severity"][severity]["resolved"] += 1

            # By article
            article = v["article"]
            if article not in stats["by_article"]:
                stats["by_article"][article] = {"total": 0, "resolved": 0}
            stats["by_article"][article]["total"] += 1
            if v["resolved"]:
                stats["by_article"][article]["resolved"] += 1

            # By AI agent
            ai_agent = v.get("ai_agent", "unknown")
            if ai_agent not in stats["by_ai_agent"]:
                stats["by_ai_agent"][ai_agent] = {"total": 0, "resolved": 0}
            stats["by_ai_agent"][ai_agent]["total"] += 1
            if v["resolved"]:
                stats["by_ai_agent"][ai_agent]["resolved"] += 1

        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(guard: ConstitutionalGuard = Depends(get_constitutional_guard)):
    """
    Health check for constitutional enforcement

    Returns:
        Status of constitutional guard
    """
    try:
        return JSONResponse(content={
            "status": "healthy",
            "constitution_loaded": bool(guard.constitution),
            "version": guard.constitution.get("version") if guard.constitution else None,
            "total_violations": len(guard.violation_log),
            "compliance_score": guard.get_compliance_score()
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
