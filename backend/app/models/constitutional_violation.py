"""
Constitutional Violation Model

Tracks violations of the UDO Constitution for audit and compliance
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any


# Use the same Base as other models
try:
    from app.models.project_context import Base
except ImportError:
    # Fallback for standalone use
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()


class ConstitutionalViolation(Base):
    """
    Constitutional Violation Model

    Tracks all violations of UDO Constitution (P1-P17)
    """
    __tablename__ = "constitutional_violations"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Article information
    article = Column(String(50), nullable=False, index=True)
    """Constitutional article (e.g., P1_design_review_first)"""

    title = Column(String(200), nullable=True)
    """Human-readable article title"""

    # Violation details
    violation_type = Column(String(100), nullable=False, index=True)
    """Type of violation (e.g., design_review_incomplete)"""

    description = Column(Text, nullable=False)
    """Detailed description of the violation"""

    severity = Column(String(20), nullable=False, index=True)
    """Severity: CRITICAL, HIGH, MEDIUM, LOW"""

    # AI agent information
    ai_agent = Column(String(50), nullable=True, index=True)
    """AI agent that caused violation (claude, codex, gemini)"""

    # Context and metadata
    violation_metadata = Column(JSON, nullable=True)
    """Additional context as JSON (violations, design, etc.)"""

    operation_type = Column(String(50), nullable=True, index=True)
    """Type of operation (design, response, optimization, etc.)"""

    # Resolution tracking
    resolved = Column(Boolean, default=False, nullable=False, index=True)
    """Whether violation has been resolved"""

    resolution_notes = Column(Text, nullable=True)
    """Notes on how violation was resolved"""

    resolved_at = Column(DateTime, nullable=True)
    """Timestamp when violation was resolved"""

    resolved_by = Column(String(100), nullable=True)
    """Who resolved the violation (user ID or AI agent)"""

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    """When violation was created"""

    updated_at = Column(DateTime, onupdate=func.now(), nullable=True)
    """When violation was last updated"""

    # Project context
    project_id = Column(String(100), nullable=True, index=True)
    """Associated project ID"""

    session_id = Column(String(100), nullable=True, index=True)
    """Associated session ID"""

    phase = Column(String(50), nullable=True, index=True)
    """Development phase when violation occurred"""

    def __repr__(self):
        status = "[OK] RESOLVED" if self.resolved else "[FAIL] OPEN"
        return f"<ConstitutionalViolation {status} [{self.article}] {self.severity}: {self.violation_type}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "article": self.article,
            "title": self.title,
            "violation_type": self.violation_type,
            "description": self.description,
            "severity": self.severity,
            "ai_agent": self.ai_agent,
            "violation_metadata": self.violation_metadata,
            "operation_type": self.operation_type,
            "resolved": self.resolved,
            "resolution_notes": self.resolution_notes,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "phase": self.phase
        }

    @classmethod
    def from_guard_log(cls, log_entry: Dict[str, Any]) -> "ConstitutionalViolation":
        """
        Create instance from ConstitutionalGuard log entry

        Args:
            log_entry: Log entry from ConstitutionalGuard.violation_log

        Returns:
            ConstitutionalViolation instance
        """
        return cls(
            article=log_entry.get("article"),
            violation_type=log_entry.get("violation_type"),
            description=log_entry.get("description"),
            severity=log_entry.get("severity"),
            ai_agent=log_entry.get("ai_agent"),
            violation_metadata=log_entry.get("metadata"),
            resolved=log_entry.get("resolved", False)
        )

    def resolve(self, notes: str, resolved_by: str):
        """
        Mark violation as resolved

        Args:
            notes: Resolution notes
            resolved_by: Who resolved it
        """
        self.resolved = True
        self.resolution_notes = notes
        self.resolved_at = datetime.now()
        self.resolved_by = resolved_by


class ConstitutionalComplianceMetrics(Base):
    """
    Constitutional Compliance Metrics

    Tracks overall compliance metrics over time
    """
    __tablename__ = "constitutional_compliance_metrics"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Metrics
    compliance_score = Column(JSON, nullable=False)
    """Overall compliance score (0.0-1.0)"""

    violation_count = Column(JSON, nullable=False)
    """Violation counts by severity"""

    article_violations = Column(JSON, nullable=False)
    """Violations by article (P1-P17)"""

    ai_agent_violations = Column(JSON, nullable=False)
    """Violations by AI agent"""

    phase_violations = Column(JSON, nullable=False)
    """Violations by development phase"""

    # Improvement tracking
    improvement_rate = Column(JSON, nullable=True)
    """Rate of improvement over time"""

    automation_rate = Column(JSON, nullable=True)
    """Percentage of automated compliance checks"""

    # Timestamps
    measured_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)
    """When metrics were measured"""

    period_start = Column(DateTime, nullable=True)
    """Start of measurement period"""

    period_end = Column(DateTime, nullable=True)
    """End of measurement period"""

    def __repr__(self):
        score = self.compliance_score.get("overall", 0) if isinstance(self.compliance_score, dict) else 0
        return f"<ComplianceMetrics {score:.2%} @ {self.measured_at}>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "compliance_score": self.compliance_score,
            "violation_count": self.violation_count,
            "article_violations": self.article_violations,
            "ai_agent_violations": self.ai_agent_violations,
            "phase_violations": self.phase_violations,
            "improvement_rate": self.improvement_rate,
            "automation_rate": self.automation_rate,
            "measured_at": self.measured_at.isoformat() if self.measured_at else None,
            "period_start": self.period_start.isoformat() if self.period_start else None,
            "period_end": self.period_end.isoformat() if self.period_end else None
        }
