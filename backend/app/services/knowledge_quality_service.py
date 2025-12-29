#!/usr/bin/env python3
"""
Knowledge Quality Service - 6 Quality Gates Implementation
Quality Target: Commercial parity (63/80 benchmark)

This service validates extracted knowledge assets against quality gates
to ensure high-quality, actionable output.

Quality Gates:
1. Minimum categories (3/5 required)
2. Minimum character count (5,000 min, 15,000 target)
3. Beginner concept quality (explanation depth, code examples)
4. Management insight actionability (ROI, timeline, metrics)
5. Technical debt severity classification (intentional vs accidental)
6. No secrets leaked (integration with SecretsRedactor)
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Import SecretsRedactor for Gate 6
try:
    from backend.app.core.log_sanitizer import SecretsRedactor

    HAS_SECRETS_REDACTOR = True
except ImportError:
    HAS_SECRETS_REDACTOR = False
    SecretsRedactor = None

logger = logging.getLogger(__name__)


class QualityGateResult(Enum):
    """Quality gate evaluation result."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class QualitySeverity(Enum):
    """Severity level for quality issues."""

    CRITICAL = "critical"  # Block extraction
    HIGH = "high"  # Require fix
    MEDIUM = "medium"  # Should fix
    LOW = "low"  # Nice to fix
    INFO = "info"  # Informational


@dataclass
class GateEvaluation:
    """Result of a single quality gate evaluation."""

    gate_name: str
    gate_number: int
    result: QualityGateResult
    score: float  # 0.0 - 1.0
    max_score: float
    severity: QualitySeverity
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class QualityReport:
    """Complete quality assessment report."""

    extraction_id: str
    timestamp: datetime
    gates: List[GateEvaluation]
    total_score: float
    max_possible_score: float
    percentage: float
    passed: bool
    blocking_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class KnowledgeQualityService:
    """
    Service for validating extracted knowledge assets against quality gates.

    Implements 6 quality gates:
    1. Category Coverage Gate (3/5 minimum)
    2. Content Volume Gate (5,000 chars minimum)
    3. Beginner Concept Quality Gate
    4. Management Insight Actionability Gate
    5. Technical Debt Classification Gate
    6. Secrets Security Gate

    Scoring: Each gate contributes to total score (80 points max)
    - Gate 1: 15 points
    - Gate 2: 15 points
    - Gate 3: 15 points
    - Gate 4: 15 points
    - Gate 5: 10 points
    - Gate 6: 10 points (pass/fail)

    Target: 63/80 (commercial quality parity)
    """

    # Configuration
    MIN_CATEGORIES = 3
    MIN_CHAR_COUNT = 5000
    TARGET_CHAR_COUNT = 15000
    MIN_BEGINNER_CONCEPTS = 2
    MIN_MANAGEMENT_INSIGHTS = 1
    PASSING_THRESHOLD = 0.60  # 60% minimum to pass
    TARGET_THRESHOLD = 0.79  # 79% (63/80) commercial parity

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize quality service with optional configuration."""
        self.config = config or {}
        self._secrets_redactor = None

        # Override defaults from config
        if config:
            self.MIN_CATEGORIES = config.get("min_categories", self.MIN_CATEGORIES)
            self.MIN_CHAR_COUNT = config.get("min_char_count", self.MIN_CHAR_COUNT)
            self.TARGET_CHAR_COUNT = config.get("target_char_count", self.TARGET_CHAR_COUNT)
            self.PASSING_THRESHOLD = config.get("passing_threshold", self.PASSING_THRESHOLD)

    @property
    def secrets_redactor(self):
        """Lazy-load secrets redactor."""
        if self._secrets_redactor is None and HAS_SECRETS_REDACTOR:
            self._secrets_redactor = SecretsRedactor()
        return self._secrets_redactor

    def validate(self, extraction_result: Dict[str, Any], extraction_id: Optional[str] = None) -> QualityReport:
        """
        Validate extracted knowledge against all quality gates.

        Args:
            extraction_result: Dictionary containing extracted knowledge
            extraction_id: Optional ID for tracking

        Returns:
            QualityReport with gate evaluations and overall score
        """
        extraction_id = extraction_id or extraction_result.get("task_id", "unknown")

        # Run all gates
        gate_evaluations = [
            self._gate1_category_coverage(extraction_result),
            self._gate2_content_volume(extraction_result),
            self._gate3_beginner_quality(extraction_result),
            self._gate4_management_actionability(extraction_result),
            self._gate5_debt_classification(extraction_result),
            self._gate6_secrets_security(extraction_result),
        ]

        # Calculate totals
        total_score = sum(g.score for g in gate_evaluations)
        max_possible = sum(g.max_score for g in gate_evaluations)
        percentage = (total_score / max_possible * 100) if max_possible > 0 else 0

        # Determine blocking issues and warnings
        blocking_issues = []
        warnings = []
        recommendations = []

        for gate in gate_evaluations:
            if gate.result == QualityGateResult.FAILED:
                if gate.severity in [QualitySeverity.CRITICAL, QualitySeverity.HIGH]:
                    blocking_issues.append(f"Gate {gate.gate_number}: {gate.message}")
                else:
                    warnings.append(f"Gate {gate.gate_number}: {gate.message}")
            elif gate.result == QualityGateResult.WARNING:
                warnings.append(f"Gate {gate.gate_number}: {gate.message}")

            recommendations.extend(gate.suggestions)

        # Determine overall pass/fail
        has_critical = any(
            g.result == QualityGateResult.FAILED and g.severity == QualitySeverity.CRITICAL for g in gate_evaluations
        )
        passed = not has_critical and percentage >= (self.PASSING_THRESHOLD * 100)

        return QualityReport(
            extraction_id=extraction_id,
            timestamp=datetime.now(),
            gates=gate_evaluations,
            total_score=total_score,
            max_possible_score=max_possible,
            percentage=percentage,
            passed=passed,
            blocking_issues=blocking_issues,
            warnings=warnings,
            recommendations=recommendations,
        )

    def _gate1_category_coverage(self, data: Dict[str, Any]) -> GateEvaluation:
        """
        Gate 1: Category Coverage (3/5 minimum)
        Max Score: 15 points

        Categories:
        - beginner_concepts
        - management_insights
        - technical_debt (technical_tradeoffs)
        - patterns
        - ai_synergy
        """
        categories = [
            "beginner_concepts",
            "management_insights",
            "technical_debt",
            "technical_tradeoffs",
            "patterns",
            "ai_synergy",
        ]

        # Count non-empty categories
        filled = 0
        category_status = {}

        for cat in categories:
            items = data.get(cat, [])
            has_content = bool(items) and len(items) > 0
            category_status[cat] = has_content
            if has_content:
                filled += 1

        # Normalize (technical_debt and technical_tradeoffs are same category)
        unique_filled = min(filled, 5)

        # Calculate score (3 points per category, max 15)
        score = min(unique_filled * 3, 15)

        # Determine result
        if unique_filled >= self.MIN_CATEGORIES:
            result = QualityGateResult.PASSED
            severity = QualitySeverity.INFO
            message = f"Category coverage: {unique_filled}/5 categories filled"
        elif unique_filled >= 2:
            result = QualityGateResult.WARNING
            severity = QualitySeverity.MEDIUM
            message = f"Low category coverage: {unique_filled}/5 (minimum: {self.MIN_CATEGORIES})"
        else:
            result = QualityGateResult.FAILED
            severity = QualitySeverity.HIGH
            message = f"Insufficient categories: {unique_filled}/5 (minimum: {self.MIN_CATEGORIES})"

        suggestions = []
        if unique_filled < 5:
            empty_cats = [k for k, v in category_status.items() if not v]
            suggestions.append(f"Add content to: {', '.join(empty_cats[:3])}")

        return GateEvaluation(
            gate_name="Category Coverage",
            gate_number=1,
            result=result,
            score=score,
            max_score=15,
            severity=severity,
            message=message,
            details={"categories": category_status, "filled_count": unique_filled},
            suggestions=suggestions,
        )

    def _gate2_content_volume(self, data: Dict[str, Any]) -> GateEvaluation:
        """
        Gate 2: Content Volume (5,000 chars minimum, 15,000 target)
        Max Score: 15 points
        """
        # Calculate total character count
        total_chars = self._count_chars(data)

        # Calculate score
        if total_chars >= self.TARGET_CHAR_COUNT:
            score = 15
        elif total_chars >= self.MIN_CHAR_COUNT:
            # Linear scale from 10-15 between min and target
            ratio = (total_chars - self.MIN_CHAR_COUNT) / (self.TARGET_CHAR_COUNT - self.MIN_CHAR_COUNT)
            score = 10 + (ratio * 5)
        else:
            # Linear scale from 0-10 below minimum
            ratio = total_chars / self.MIN_CHAR_COUNT
            score = ratio * 10

        # Determine result
        if total_chars >= self.TARGET_CHAR_COUNT:
            result = QualityGateResult.PASSED
            severity = QualitySeverity.INFO
            message = f"Excellent content volume: {total_chars:,} chars (target: {self.TARGET_CHAR_COUNT:,})"
        elif total_chars >= self.MIN_CHAR_COUNT:
            result = QualityGateResult.PASSED
            severity = QualitySeverity.LOW
            message = f"Good content volume: {total_chars:,} chars (target: {self.TARGET_CHAR_COUNT:,})"
        elif total_chars >= self.MIN_CHAR_COUNT * 0.5:
            result = QualityGateResult.WARNING
            severity = QualitySeverity.MEDIUM
            message = f"Low content volume: {total_chars:,} chars (minimum: {self.MIN_CHAR_COUNT:,})"
        else:
            result = QualityGateResult.FAILED
            severity = QualitySeverity.HIGH
            message = f"Insufficient content: {total_chars:,} chars (minimum: {self.MIN_CHAR_COUNT:,})"

        suggestions = []
        if total_chars < self.TARGET_CHAR_COUNT:
            deficit = self.TARGET_CHAR_COUNT - total_chars
            suggestions.append(f"Add ~{deficit:,} more characters to reach target quality")
            suggestions.append("Expand explanations in beginner_concepts with code examples")
            suggestions.append("Add ROI calculations and metrics to management_insights")

        return GateEvaluation(
            gate_name="Content Volume",
            gate_number=2,
            result=result,
            score=round(score, 2),
            max_score=15,
            severity=severity,
            message=message,
            details={"total_chars": total_chars, "target": self.TARGET_CHAR_COUNT},
            suggestions=suggestions,
        )

    def _gate3_beginner_quality(self, data: Dict[str, Any]) -> GateEvaluation:
        """
        Gate 3: Beginner Concept Quality
        Max Score: 15 points

        Criteria:
        - Has code examples (3 points)
        - Has clear explanations (3 points)
        - Has difficulty levels (3 points)
        - Has related files (3 points)
        - Has tags (3 points)
        """
        concepts = data.get("beginner_concepts", [])

        if not concepts:
            return GateEvaluation(
                gate_name="Beginner Concept Quality",
                gate_number=3,
                result=QualityGateResult.FAILED,
                score=0,
                max_score=15,
                severity=QualitySeverity.HIGH,
                message="No beginner concepts found",
                suggestions=["Extract learning points from code patterns"],
            )

        # Evaluate quality metrics
        total_concepts = len(concepts)
        has_code = 0
        has_explanation = 0
        has_difficulty = 0
        has_files = 0
        has_tags = 0

        for concept in concepts:
            if isinstance(concept, dict):
                if concept.get("code_example"):
                    has_code += 1
                if concept.get("explanation") and len(str(concept.get("explanation", ""))) > 50:
                    has_explanation += 1
                if concept.get("difficulty"):
                    has_difficulty += 1
                if concept.get("related_files"):
                    has_files += 1
                if concept.get("tags"):
                    has_tags += 1

        # Calculate scores (3 points each, based on percentage)
        score = 0
        if total_concepts > 0:
            score += (has_code / total_concepts) * 3
            score += (has_explanation / total_concepts) * 3
            score += (has_difficulty / total_concepts) * 3
            score += (has_files / total_concepts) * 3
            score += (has_tags / total_concepts) * 3

        # Determine result
        percentage = score / 15 * 100
        if percentage >= 80:
            result = QualityGateResult.PASSED
            severity = QualitySeverity.INFO
            message = f"High-quality beginner concepts: {percentage:.0f}% completeness"
        elif percentage >= 50:
            result = QualityGateResult.WARNING
            severity = QualitySeverity.MEDIUM
            message = f"Moderate beginner concept quality: {percentage:.0f}% completeness"
        else:
            result = QualityGateResult.FAILED
            severity = QualitySeverity.HIGH
            message = f"Low beginner concept quality: {percentage:.0f}% completeness"

        suggestions = []
        if has_code < total_concepts:
            suggestions.append(f"Add code examples to {total_concepts - has_code} concepts")
        if has_explanation < total_concepts:
            suggestions.append(f"Expand explanations in {total_concepts - has_explanation} concepts")

        return GateEvaluation(
            gate_name="Beginner Concept Quality",
            gate_number=3,
            result=result,
            score=round(score, 2),
            max_score=15,
            severity=severity,
            message=message,
            details={
                "total_concepts": total_concepts,
                "has_code": has_code,
                "has_explanation": has_explanation,
                "has_difficulty": has_difficulty,
            },
            suggestions=suggestions,
        )

    def _gate4_management_actionability(self, data: Dict[str, Any]) -> GateEvaluation:
        """
        Gate 4: Management Insight Actionability
        Max Score: 15 points

        Criteria:
        - Has ROI/metrics (5 points)
        - Has timeline/deadline (5 points)
        - Has actionable recommendation (5 points)
        """
        insights = data.get("management_insights", [])

        if not insights:
            return GateEvaluation(
                gate_name="Management Actionability",
                gate_number=4,
                result=QualityGateResult.FAILED,
                score=0,
                max_score=15,
                severity=QualitySeverity.MEDIUM,
                message="No management insights found",
                suggestions=["Extract strategic insights from code changes"],
            )

        total_insights = len(insights)
        has_roi = 0
        has_timeline = 0
        has_recommendation = 0

        roi_keywords = ["roi", "metric", "kpi", "percentage", "%", "cost", "save", "reduce", "increase"]
        timeline_keywords = ["day", "week", "month", "sprint", "quarter", "deadline", "timeline", "eta"]
        action_keywords = ["should", "must", "recommend", "consider", "implement", "adopt", "migrate"]

        for insight in insights:
            text = ""
            if isinstance(insight, dict):
                text = str(insight.get("insight", "")) + str(insight.get("recommendation", ""))
            elif isinstance(insight, str):
                text = insight

            text_lower = text.lower()

            if any(kw in text_lower for kw in roi_keywords):
                has_roi += 1
            if any(kw in text_lower for kw in timeline_keywords):
                has_timeline += 1
            if any(kw in text_lower for kw in action_keywords):
                has_recommendation += 1

        # Calculate scores
        score = 0
        if total_insights > 0:
            score += (has_roi / total_insights) * 5
            score += (has_timeline / total_insights) * 5
            score += (has_recommendation / total_insights) * 5

        # Determine result
        percentage = score / 15 * 100
        if percentage >= 70:
            result = QualityGateResult.PASSED
            severity = QualitySeverity.INFO
            message = f"Actionable insights: {percentage:.0f}% completeness"
        elif percentage >= 40:
            result = QualityGateResult.WARNING
            severity = QualitySeverity.MEDIUM
            message = f"Moderate insight actionability: {percentage:.0f}%"
        else:
            result = QualityGateResult.FAILED
            severity = QualitySeverity.MEDIUM
            message = f"Low insight actionability: {percentage:.0f}%"

        suggestions = []
        if has_roi < total_insights:
            suggestions.append("Add ROI calculations or metrics to insights")
        if has_timeline < total_insights:
            suggestions.append("Include timeline estimates for recommendations")
        if has_recommendation < total_insights:
            suggestions.append("Make insights more actionable with specific recommendations")

        return GateEvaluation(
            gate_name="Management Actionability",
            gate_number=4,
            result=result,
            score=round(score, 2),
            max_score=15,
            severity=severity,
            message=message,
            details={
                "total_insights": total_insights,
                "has_roi": has_roi,
                "has_timeline": has_timeline,
                "has_recommendation": has_recommendation,
            },
            suggestions=suggestions,
        )

    def _gate5_debt_classification(self, data: Dict[str, Any]) -> GateEvaluation:
        """
        Gate 5: Technical Debt Classification
        Max Score: 10 points

        Criteria:
        - Has severity classification (4 points)
        - Distinguishes intentional vs accidental (3 points)
        - Has remediation estimate (3 points)
        """
        debt_items = data.get("technical_debt", []) or data.get("technical_tradeoffs", [])

        if not debt_items:
            # No debt found can be good or neutral
            return GateEvaluation(
                gate_name="Technical Debt Classification",
                gate_number=5,
                result=QualityGateResult.PASSED,
                score=8,  # Partial score - no debt to classify
                max_score=10,
                severity=QualitySeverity.INFO,
                message="No technical debt items to classify",
                details={"reason": "clean_code"},
            )

        total_items = len(debt_items)
        has_severity = 0
        has_intentional_flag = 0
        has_estimate = 0

        severity_keywords = ["critical", "high", "medium", "low", "severity", "priority"]
        intentional_keywords = ["intentional", "deliberate", "tradeoff", "trade-off", "accidental", "unintentional"]
        estimate_keywords = ["hour", "day", "week", "sprint", "estimate", "effort", "time"]

        for item in debt_items:
            text = ""
            if isinstance(item, dict):
                text = " ".join(str(v) for v in item.values())
            elif isinstance(item, str):
                text = item

            text_lower = text.lower()

            if any(kw in text_lower for kw in severity_keywords):
                has_severity += 1
            if any(kw in text_lower for kw in intentional_keywords):
                has_intentional_flag += 1
            if any(kw in text_lower for kw in estimate_keywords):
                has_estimate += 1

        # Calculate scores
        score = 0
        if total_items > 0:
            score += (has_severity / total_items) * 4
            score += (has_intentional_flag / total_items) * 3
            score += (has_estimate / total_items) * 3

        # Determine result
        percentage = score / 10 * 100
        if percentage >= 70:
            result = QualityGateResult.PASSED
            severity = QualitySeverity.INFO
            message = f"Well-classified debt: {percentage:.0f}%"
        elif percentage >= 40:
            result = QualityGateResult.WARNING
            severity = QualitySeverity.LOW
            message = f"Moderate debt classification: {percentage:.0f}%"
        else:
            result = QualityGateResult.FAILED
            severity = QualitySeverity.MEDIUM
            message = f"Poor debt classification: {percentage:.0f}%"

        suggestions = []
        if has_severity < total_items:
            suggestions.append("Add severity levels to technical debt items")
        if has_intentional_flag < total_items:
            suggestions.append("Distinguish intentional vs accidental debt")

        return GateEvaluation(
            gate_name="Technical Debt Classification",
            gate_number=5,
            result=result,
            score=round(score, 2),
            max_score=10,
            severity=severity,
            message=message,
            details={
                "total_items": total_items,
                "has_severity": has_severity,
                "has_intentional": has_intentional_flag,
                "has_estimate": has_estimate,
            },
            suggestions=suggestions,
        )

    def _gate6_secrets_security(self, data: Dict[str, Any]) -> GateEvaluation:
        """
        Gate 6: Secrets Security (CRITICAL - Pass/Fail)
        Max Score: 10 points

        Uses SecretsRedactor to detect leaked secrets in extraction output.
        This is a blocking gate - any secret leak fails the entire extraction.
        """
        # Convert data to string for scanning
        content = self._serialize_for_scan(data)

        # Check for common secret patterns
        secret_patterns = [
            (r'(?i)api[_-]?key\s*[=:]\s*["\']?[\w-]{20,}', "API Key"),
            (r'(?i)secret[_-]?key\s*[=:]\s*["\']?[\w-]{20,}', "Secret Key"),
            (r'(?i)password\s*[=:]\s*["\']?[^\s"\']{8,}', "Password"),
            (r'(?i)token\s*[=:]\s*["\']?[\w-]{20,}', "Token"),
            (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Token"),
            (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
            (r"sk-[a-zA-Z0-9]{48}", "OpenAI API Key"),
            (r"AKIA[0-9A-Z]{16}", "AWS Access Key"),
            (r"(?i)bearer\s+[\w-]{20,}", "Bearer Token"),
        ]

        found_secrets = []
        for pattern, secret_type in secret_patterns:
            matches = re.findall(pattern, content)
            if matches:
                found_secrets.extend([(secret_type, m[:20] + "..." if len(m) > 20 else m) for m in matches])

        # Also use SecretsRedactor if available
        if self.secrets_redactor:
            try:
                redacted = self.secrets_redactor.redact(content)
                if redacted != content:
                    found_secrets.append(("SecretsRedactor", "Additional secrets detected"))
            except Exception as e:
                logger.warning(f"SecretsRedactor error: {e}")

        if found_secrets:
            return GateEvaluation(
                gate_name="Secrets Security",
                gate_number=6,
                result=QualityGateResult.FAILED,
                score=0,
                max_score=10,
                severity=QualitySeverity.CRITICAL,
                message=f"CRITICAL: {len(found_secrets)} potential secrets detected",
                details={"secrets_found": [s[0] for s in found_secrets]},
                suggestions=[
                    "Remove all secrets from extraction output",
                    "Use environment variables for sensitive data",
                    "Review SecretsRedactor patterns for completeness",
                ],
            )

        return GateEvaluation(
            gate_name="Secrets Security",
            gate_number=6,
            result=QualityGateResult.PASSED,
            score=10,
            max_score=10,
            severity=QualitySeverity.INFO,
            message="No secrets detected in extraction output",
            details={"scanned_chars": len(content)},
        )

    def _count_chars(self, data: Dict[str, Any]) -> int:
        """Count total characters in extraction data."""

        def count_recursive(obj) -> int:
            if isinstance(obj, str):
                return len(obj)
            elif isinstance(obj, dict):
                return sum(count_recursive(v) for v in obj.values())
            elif isinstance(obj, list):
                return sum(count_recursive(item) for item in obj)
            else:
                return len(str(obj)) if obj is not None else 0

        return count_recursive(data)

    def _serialize_for_scan(self, data: Dict[str, Any]) -> str:
        """Serialize data to string for security scanning."""
        import json

        try:
            return json.dumps(data, default=str)
        except Exception:
            return str(data)

    def to_markdown(self, report: QualityReport) -> str:
        """Generate markdown report from quality assessment."""
        lines = [
            "# Knowledge Quality Report",
            "",
            f"**Extraction ID**: {report.extraction_id}",
            f"**Timestamp**: {report.timestamp.isoformat()}",
            f"**Overall Score**: {report.total_score:.1f}/{report.max_possible_score:.0f} ({report.percentage:.1f}%)",
            f"**Status**: {'PASSED' if report.passed else 'FAILED'}",
            "",
        ]

        # Status indicator
        if report.percentage >= 79:
            lines.append("> Commercial Quality Achieved (63/80+)")
        elif report.percentage >= 60:
            lines.append("> Acceptable Quality - Room for improvement")
        else:
            lines.append("> Below Threshold - Action Required")

        lines.extend(["", "## Gate Results", ""])

        # Gate results table
        lines.append("| Gate | Name | Score | Status | Severity |")
        lines.append("|------|------|-------|--------|----------|")

        for gate in report.gates:
            status_emoji = {
                QualityGateResult.PASSED: "PASS",
                QualityGateResult.FAILED: "FAIL",
                QualityGateResult.WARNING: "WARN",
                QualityGateResult.SKIPPED: "SKIP",
            }.get(gate.result, "?")

            lines.append(
                f"| {gate.gate_number} | {gate.gate_name} | "
                f"{gate.score:.1f}/{gate.max_score:.0f} | {status_emoji} | {gate.severity.value} |"
            )

        # Issues and recommendations
        if report.blocking_issues:
            lines.extend(["", "## Blocking Issues", ""])
            for issue in report.blocking_issues:
                lines.append(f"- {issue}")

        if report.warnings:
            lines.extend(["", "## Warnings", ""])
            for warning in report.warnings:
                lines.append(f"- {warning}")

        if report.recommendations:
            lines.extend(["", "## Recommendations", ""])
            for rec in report.recommendations[:5]:  # Top 5 recommendations
                lines.append(f"- {rec}")

        return "\n".join(lines)

    def to_dict(self, report: QualityReport) -> Dict[str, Any]:
        """Convert quality report to dictionary."""
        return {
            "extraction_id": report.extraction_id,
            "timestamp": report.timestamp.isoformat(),
            "total_score": report.total_score,
            "max_possible_score": report.max_possible_score,
            "percentage": report.percentage,
            "passed": report.passed,
            "gates": [
                {
                    "gate_name": g.gate_name,
                    "gate_number": g.gate_number,
                    "result": g.result.value,
                    "score": g.score,
                    "max_score": g.max_score,
                    "severity": g.severity.value,
                    "message": g.message,
                    "details": g.details,
                    "suggestions": g.suggestions,
                }
                for g in report.gates
            ],
            "blocking_issues": report.blocking_issues,
            "warnings": report.warnings,
            "recommendations": report.recommendations,
        }


# CLI for testing
def main():
    """CLI entry point for testing quality service."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Knowledge Quality Service")
    parser.add_argument("--input", "-i", help="Input JSON file with extraction result")
    parser.add_argument("--output", "-o", help="Output file for quality report")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of markdown")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Load input
    if args.input:
        with open(args.input, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        # Demo data
        data = {
            "task_id": "demo-001",
            "beginner_concepts": [
                {
                    "title": "Error Handling Pattern",
                    "explanation": "Using try-except blocks with specific exception types improves code reliability.",
                    "difficulty": "medium",
                    "code_example": "try:\n    result = api.call()\nexcept APIError as e:\n    logger.error(e)",
                    "related_files": ["src/api.py"],
                    "tags": ["error-handling", "python"],
                }
            ],
            "management_insights": [
                {
                    "insight": "Test coverage increased by 15% this sprint",
                    "recommendation": "Should continue TDD practice to reduce bug rate by 20% next quarter",
                }
            ],
            "technical_debt": [
                {
                    "item": "Legacy authentication module",
                    "severity": "high",
                    "intentional": False,
                    "estimate": "2 weeks to refactor",
                }
            ],
            "patterns": [
                {
                    "pattern": "Circuit Breaker",
                    "description": "Implemented for external API resilience",
                }
            ],
            "ai_synergy": [
                {
                    "tool": "Claude Code",
                    "effectiveness": "High for refactoring tasks",
                }
            ],
        }

    # Validate
    service = KnowledgeQualityService()
    report = service.validate(data)

    # Output
    if args.json:
        output = json.dumps(service.to_dict(report), indent=2)
    else:
        output = service.to_markdown(report)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Report saved to: {args.output}")
    else:
        print(output)

    # Exit code based on pass/fail
    return 0 if report.passed else 1


if __name__ == "__main__":
    exit(main())
