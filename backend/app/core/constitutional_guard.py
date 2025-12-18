"""
Constitutional Guard - UDO Constitution Enforcement Engine

Validates all AI decisions and code changes against the UDO Constitution.
Ensures consistent governance across Claude, Codex, and Gemini.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Violation severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Action(str, Enum):
    """Enforcement actions"""
    BLOCK_EXECUTION = "BLOCK_EXECUTION"
    BLOCK_RESPONSE = "BLOCK_RESPONSE"
    BLOCK_COMMIT = "BLOCK_COMMIT"
    BLOCK_MERGE = "BLOCK_MERGE"
    BLOCK_DEPLOYMENT = "BLOCK_DEPLOYMENT"
    BLOCK_PHASE_TRANSITION = "BLOCK_PHASE_TRANSITION"
    REQUIRE_EVIDENCE = "REQUIRE_EVIDENCE"
    REQUIRE_CONSENSUS = "REQUIRE_CONSENSUS"
    REQUIRE_ERROR_HANDLING = "REQUIRE_ERROR_HANDLING"
    REQUIRE_UX_REVIEW = "REQUIRE_UX_REVIEW"
    WARN = "WARN"


class ValidationResult:
    """Result of constitutional validation"""

    def __init__(
        self,
        passed: bool,
        article: str,
        violations: List[str] = None,
        warnings: List[str] = None,
        metadata: Dict[str, Any] = None
    ):
        self.passed = passed
        self.article = article
        self.violations = violations or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "passed": self.passed,
            "article": self.article,
            "violations": self.violations,
            "warnings": self.warnings,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

    def __repr__(self):
        status = "[OK] PASSED" if self.passed else "[FAIL] FAILED"
        return f"{status} [{self.article}] - {len(self.violations)} violations, {len(self.warnings)} warnings"


class ConstitutionalGuard:
    """
    Constitutional enforcement engine for UDO Development Platform

    Validates all operations against the UDO Constitution (P1-P17)
    """

    def __init__(self, constitution_path: Optional[Path] = None):
        """
        Initialize Constitutional Guard

        Args:
            constitution_path: Path to UDO_CONSTITUTION.yaml
        """
        if constitution_path:
            self.constitution_path = Path(constitution_path)
        else:
            # Find project root
            current_path = Path(__file__).resolve()
            for parent in current_path.parents:
                config_path = parent / "backend" / "config" / "UDO_CONSTITUTION.yaml"
                if config_path.exists():
                    self.constitution_path = config_path
                    break
            else:
                # Fallback
                self.constitution_path = Path(__file__).parent.parent.parent / "config" / "UDO_CONSTITUTION.yaml"

        self.constitution = self._load_constitution()
        self.violation_log: List[Dict[str, Any]] = []

        logger.info(f"ConstitutionalGuard initialized with: {self.constitution_path}")

    def _load_constitution(self) -> Dict[str, Any]:
        """Load constitution from YAML file"""
        try:
            if not self.constitution_path.exists():
                logger.error(f"Constitution file not found: {self.constitution_path}")
                return {}

            with open(self.constitution_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load constitution: {e}")
            return {}

    def _log_violation(
        self,
        article: str,
        violation_type: str,
        description: str,
        severity: Severity,
        ai_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log a constitutional violation"""
        violation = {
            "article": article,
            "violation_type": violation_type,
            "description": description,
            "severity": severity.value,
            "ai_agent": ai_agent or "unknown",
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
            "resolved": False
        }
        self.violation_log.append(violation)
        logger.warning(f"Constitutional violation: [{article}] {description}")

    # [EMOJI]
    # P1: Design Review First
    # [EMOJI]

    async def validate_design(self, design: Dict[str, Any]) -> ValidationResult:
        """
        P1: Design Review First - 8-Risk Check

        Args:
            design: Design document with risk assessments

        Returns:
            ValidationResult indicating pass/fail
        """
        article = "P1_design_review_first"
        violations = []
        warnings = []

        if not self.constitution:
            return ValidationResult(False, article, ["Constitution not loaded"])

        p1 = self.constitution.get(article, {})
        risk_checks = p1.get("risk_checks", {})

        # Check all 8 required risks
        required_risks = [
            "existing_system_impact",
            "git_conflict_risk",
            "multi_session_issue",
            "performance_impact",
            "complexity_increase",
            "workflow_change",
            "rollback_plan",
            "test_method"
        ]

        for risk_key in required_risks:
            if risk_key not in design.get("risk_assessments", {}):
                violations.append(f"Missing required risk check: {risk_key}")
            else:
                risk_data = design["risk_assessments"][risk_key]

                # Validate risk has required fields
                if "assessed" not in risk_data or not risk_data["assessed"]:
                    violations.append(f"Risk {risk_key} not properly assessed")

                if "mitigation" not in risk_data or not risk_data["mitigation"]:
                    warnings.append(f"Risk {risk_key} missing mitigation strategy")

        # Check for exemptions
        exemptions = p1.get("exemptions", [])
        if design.get("exemption_claimed"):
            if design.get("exemption_reason") not in exemptions:
                violations.append(f"Invalid exemption claimed: {design.get('exemption_reason')}")

        # Check user approval
        if not design.get("user_approved") and not violations:
            violations.append("User approval required before implementation")

        passed = len(violations) == 0

        if not passed:
            self._log_violation(
                article=article,
                violation_type="design_review_incomplete",
                description=f"Design review failed: {', '.join(violations)}",
                severity=Severity.CRITICAL,
                metadata={"violations": violations, "design": design}
            )

        return ValidationResult(
            passed=passed,
            article=article,
            violations=violations,
            warnings=warnings,
            metadata={"design_id": design.get("id"), "risks_checked": len(design.get("risk_assessments", {}))}
        )

    # [EMOJI]
    # P2: Uncertainty Disclosure
    # [EMOJI]

    async def validate_confidence(self, response: Dict[str, Any]) -> ValidationResult:
        """
        P2: Uncertainty Disclosure - Confidence level validation

        Args:
            response: AI response with confidence information

        Returns:
            ValidationResult indicating pass/fail
        """
        article = "P2_uncertainty_disclosure"
        violations = []
        warnings = []

        if not self.constitution:
            return ValidationResult(False, article, ["Constitution not loaded"])

        p2 = self.constitution.get(article, {})
        required_fields_raw = p2.get("response_format", {}).get("required_fields", [])

        # Extract field names from list of dicts (YAML format: [{field: description}, ...])
        field_names = []
        for field_item in required_fields_raw:
            if isinstance(field_item, dict):
                field_names.extend(field_item.keys())
            else:
                field_names.append(field_item)

        # Check required fields
        for field in field_names:
            if field not in response:
                violations.append(f"Missing required field: {field}")

        # Validate confidence level
        confidence = response.get("confidence", {})
        if isinstance(confidence, dict):
            level = confidence.get("level")
            score = confidence.get("score")

            if level not in ["HIGH", "MEDIUM", "LOW"]:
                violations.append(f"Invalid confidence level: {level}")

            if score is not None:
                if not (0.0 <= score <= 1.0):
                    violations.append(f"Confidence score must be 0.0-1.0, got: {score}")

                # Validate score matches level
                if level == "HIGH" and score < 0.95:
                    violations.append(f"HIGH confidence requires score >= 0.95, got {score}")
                elif level == "MEDIUM" and not (0.70 <= score < 0.95):
                    violations.append(f"MEDIUM confidence requires score 0.70-0.95, got {score}")
                elif level == "LOW" and score >= 0.70:
                    violations.append(f"LOW confidence requires score < 0.70, got {score}")

            # Check alternatives for LOW/MEDIUM confidence
            if level in ["LOW", "MEDIUM"]:
                alternatives = response.get("alternatives", [])
                if not alternatives:
                    violations.append(f"{level} confidence requires alternatives")
                elif level == "LOW" and len(alternatives) < 2:
                    violations.append(f"LOW confidence requires at least 2 alternatives, got {len(alternatives)}")

            # Check rationale
            if not confidence.get("rationale"):
                warnings.append("Missing confidence rationale")

            # Check evidence
            if not confidence.get("evidence"):
                warnings.append("Missing evidence for confidence level")

        else:
            violations.append("Confidence must be a dictionary with level, score, rationale, evidence")

        passed = len(violations) == 0

        if not passed:
            self._log_violation(
                article=article,
                violation_type="uncertainty_disclosure_missing",
                description=f"Uncertainty disclosure failed: {', '.join(violations)}",
                severity=Severity.CRITICAL,
                ai_agent=response.get("ai_agent"),
                metadata={"violations": violations, "response_id": response.get("id")}
            )

        return ValidationResult(
            passed=passed,
            article=article,
            violations=violations,
            warnings=warnings,
            metadata={
                "confidence_level": confidence.get("level") if isinstance(confidence, dict) else None,
                "confidence_score": confidence.get("score") if isinstance(confidence, dict) else None
            }
        )

    # [EMOJI]
    # P3: Evidence-Based Decision
    # [EMOJI]

    async def validate_evidence(self, claim: Dict[str, Any]) -> ValidationResult:
        """
        P3: Evidence-Based Decision - Validate optimization claims

        Args:
            claim: Performance or optimization claim with evidence

        Returns:
            ValidationResult indicating pass/fail
        """
        article = "P3_evidence_based"
        violations = []
        warnings = []

        if not self.constitution:
            return ValidationResult(False, article, ["Constitution not loaded"])

        p3 = self.constitution.get(article, {})
        evidence_types = p3.get("evidence_types", {})

        # Check if this is an optimization claim
        if claim.get("type") not in ["optimization", "performance_improvement"]:
            # Not an optimization claim, skip P3 validation
            return ValidationResult(True, article, metadata={"skipped": "Not an optimization claim"})

        # Check for required evidence
        has_benchmark = "benchmark_results" in claim.get("evidence", {})
        has_ab_test = "ab_test_metrics" in claim.get("evidence", {})
        has_automated_tests = "automated_tests" in claim.get("evidence", {})

        if not (has_benchmark or has_ab_test):
            violations.append("Optimization claims require benchmark_results or ab_test_metrics")

        # Validate benchmark results
        if has_benchmark:
            benchmark = claim["evidence"]["benchmark_results"]
            required_metrics = evidence_types.get("benchmark_results", {}).get("required_metrics", [])

            for metric in required_metrics:
                if metric not in benchmark:
                    warnings.append(f"Benchmark missing recommended metric: {metric}")

        # Validate A/B test
        if has_ab_test:
            ab_test = claim["evidence"]["ab_test_metrics"]
            required_fields_raw = evidence_types.get("ab_test_metrics", {}).get("required_fields", [])

            # Extract field names from list of dicts (YAML format: [{field: description}, ...])
            field_names = []
            for field_item in required_fields_raw:
                if isinstance(field_item, dict):
                    field_names.extend(field_item.keys())
                else:
                    field_names.append(field_item)

            for field in field_names:
                if field not in ab_test:
                    violations.append(f"A/B test missing required field: {field}")

            # Check sample size
            if ab_test.get("sample_size", 0) < 100:
                warnings.append("A/B test sample size should be at least 100")

            # Check statistical significance
            if "statistical_significance" in ab_test:
                p_value = ab_test["statistical_significance"]
                if p_value >= 0.05:
                    warnings.append(f"A/B test not statistically significant (p-value: {p_value})")

        # Check for before/after comparison
        if "before" not in claim or "after" not in claim:
            violations.append("Must provide before/after comparison data")

        passed = len(violations) == 0

        if not passed:
            self._log_violation(
                article=article,
                violation_type="insufficient_evidence",
                description=f"Evidence-based decision failed: {', '.join(violations)}",
                severity=Severity.HIGH,
                metadata={"violations": violations, "claim_id": claim.get("id")}
            )

        return ValidationResult(
            passed=passed,
            article=article,
            violations=violations,
            warnings=warnings,
            metadata={"claim_type": claim.get("type"), "has_evidence": has_benchmark or has_ab_test}
        )

    # [EMOJI]
    # P4: Phase-Aware Compliance
    # [EMOJI]

    async def validate_phase_compliance(
        self,
        current_phase: str,
        action: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        P4: Phase-Aware Compliance - Validate phase-specific rules

        Args:
            current_phase: Current development phase
            action: Action being attempted
            context: Additional context

        Returns:
            ValidationResult indicating pass/fail
        """
        article = "P4_phase_aware_compliance"
        violations = []
        warnings = []

        if not self.constitution:
            return ValidationResult(False, article, ["Constitution not loaded"])

        p4 = self.constitution.get(article, {})
        phases = p4.get("phases", {})

        # Normalize phase name
        phase_key = current_phase.lower()

        if phase_key not in phases:
            violations.append(f"Unknown phase: {current_phase}")
            return ValidationResult(False, article, violations)

        phase_config = phases[phase_key]

        # Check if action is allowed in this phase
        allowed_actions = phase_config.get("allowed_actions", [])
        prohibited_actions = phase_config.get("prohibited_actions", [])

        if action in prohibited_actions:
            violations.append(f"Action '{action}' is prohibited in {current_phase} phase")

        if allowed_actions and action not in allowed_actions:
            warnings.append(f"Action '{action}' not in recommended actions for {current_phase} phase")

        # Check quality threshold
        quality_threshold = phase_config.get("quality_threshold", 0.6)
        current_quality = context.get("quality_score", 0.0)

        if current_quality < quality_threshold:
            warnings.append(
                f"Quality score {current_quality:.2f} below phase threshold {quality_threshold:.2f}"
            )

        # Check deliverables
        required_deliverables = phase_config.get("required_deliverables", [])
        completed_deliverables = context.get("completed_deliverables", [])

        missing_deliverables = set(required_deliverables) - set(completed_deliverables)
        if missing_deliverables and context.get("phase_transition_requested"):
            violations.append(f"Missing required deliverables: {', '.join(missing_deliverables)}")

        passed = len(violations) == 0

        if not passed:
            self._log_violation(
                article=article,
                violation_type="phase_compliance_violation",
                description=f"Phase compliance failed for {current_phase}: {', '.join(violations)}",
                severity=Severity.HIGH,
                metadata={"phase": current_phase, "action": action, "violations": violations}
            )

        return ValidationResult(
            passed=passed,
            article=article,
            violations=violations,
            warnings=warnings,
            metadata={"phase": current_phase, "action": action, "quality_score": current_quality}
        )

    async def validate_phase_transition(
        self,
        current_phase: str,
        next_phase: str,
        context: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate phase transition according to P4 rules

        Args:
            current_phase: Current development phase
            next_phase: Target phase
            context: Transition context with deliverables

        Returns:
            ValidationResult indicating if transition is allowed
        """
        article = "P4_phase_aware_compliance"
        violations = []
        warnings = []

        if not self.constitution:
            return ValidationResult(False, article, ["Constitution not loaded"])

        p4 = self.constitution.get(article, {})
        phases = p4.get("phases", {})
        transition_rules = p4.get("phase_transition_rules", {})

        # Validate current phase deliverables
        current_phase_config = phases.get(current_phase.lower(), {})
        required_deliverables = current_phase_config.get("required_deliverables", [])
        completed_deliverables = context.get("completed_deliverables", [])

        missing = set(required_deliverables) - set(completed_deliverables)
        if missing:
            violations.append(f"Missing deliverables from {current_phase}: {', '.join(missing)}")

        # Check quality threshold
        quality_threshold = current_phase_config.get("quality_threshold", 0.6)
        current_quality = context.get("quality_score", 0.0)

        if current_quality < quality_threshold:
            violations.append(
                f"Quality score {current_quality:.2f} below required {quality_threshold:.2f}"
            )

        # Check approval requirement
        if transition_rules.get("approval_required") and not context.get("approved"):
            violations.append("Phase transition requires approval")

        # Validate next phase readiness
        next_phase_config = phases.get(next_phase.lower(), {})
        if not next_phase_config:
            violations.append(f"Unknown target phase: {next_phase}")

        passed = len(violations) == 0

        if not passed:
            self._log_violation(
                article=article,
                violation_type="phase_transition_blocked",
                description=f"Phase transition {current_phase} -> {next_phase} blocked: {', '.join(violations)}",
                severity=Severity.HIGH,
                metadata={
                    "current_phase": current_phase,
                    "next_phase": next_phase,
                    "violations": violations
                }
            )

        return ValidationResult(
            passed=passed,
            article=article,
            violations=violations,
            warnings=warnings,
            metadata={
                "current_phase": current_phase,
                "next_phase": next_phase,
                "quality_score": current_quality,
                "missing_deliverables": list(missing) if missing else []
            }
        )

    # [EMOJI]
    # P5: Multi-AI Consistency
    # [EMOJI]

    async def validate_ai_consensus(
        self,
        decisions: List[Dict[str, Any]]
    ) -> Tuple[ValidationResult, Dict[str, Any]]:
        """
        P5: Multi-AI Consistency - Validate consensus among AI agents

        Args:
            decisions: List of decisions from different AI agents

        Returns:
            Tuple of (ValidationResult, consensus_decision)
        """
        article = "P5_multi_ai_consistency"
        violations = []
        warnings = []

        if not self.constitution:
            return ValidationResult(False, article, ["Constitution not loaded"]), {}

        if len(decisions) < 2:
            return ValidationResult(
                True,
                article,
                metadata={"skipped": "Single AI decision, consensus not required"}
            ), decisions[0] if decisions else {}

        # Group decisions by recommendation
        recommendation_votes: Dict[str, List[Dict[str, Any]]] = {}

        for decision in decisions:
            recommendation = decision.get("recommendation", "")
            if recommendation not in recommendation_votes:
                recommendation_votes[recommendation] = []
            recommendation_votes[recommendation].append(decision)

        # Calculate weighted votes (by confidence score)
        weighted_scores = {}
        for recommendation, votes in recommendation_votes.items():
            total_weight = sum(
                vote.get("confidence", {}).get("score", 0.5)
                for vote in votes
            )
            weighted_scores[recommendation] = (total_weight, votes)

        # Sort by weighted score
        sorted_recommendations = sorted(
            weighted_scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )

        # Check for 2/3 majority
        total_ais = len(decisions)
        winner_recommendation, (winner_score, winner_votes) = sorted_recommendations[0]
        winner_count = len(winner_votes)

        if winner_count < (total_ais * 2 / 3):
            warnings.append(
                f"No 2/3 majority consensus: {winner_count}/{total_ais} AIs agree"
            )

        # Build consensus decision
        consensus_decision = {
            "recommendation": winner_recommendation,
            "confidence": {
                "level": "MEDIUM",  # Consensus reduces to MEDIUM max
                "score": winner_score / winner_count,
                "rationale": f"Consensus from {winner_count}/{total_ais} AIs"
            },
            "supporting_ais": [vote.get("ai_agent") for vote in winner_votes],
            "minority_opinions": []
        }

        # Record minority opinions
        for recommendation, (score, votes) in sorted_recommendations[1:]:
            minority = {
                "recommendation": recommendation,
                "supporting_ais": [vote.get("ai_agent") for vote in votes],
                "rationale": votes[0].get("confidence", {}).get("rationale", "")
            }
            consensus_decision["minority_opinions"].append(minority)

        passed = len(violations) == 0

        return ValidationResult(
            passed=passed,
            article=article,
            violations=violations,
            warnings=warnings,
            metadata={
                "total_ais": total_ais,
                "winner_count": winner_count,
                "consensus_percentage": (winner_count / total_ais * 100)
            }
        ), consensus_decision

    # [EMOJI]
    # General Validation
    # [EMOJI]

    async def validate_all(
        self,
        operation: str,
        data: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> List[ValidationResult]:
        """
        Validate operation against all applicable constitutional articles

        Args:
            operation: Type of operation (design, response, optimization, etc.)
            data: Operation data
            context: Additional context

        Returns:
            List of ValidationResults from all applicable checks
        """
        results = []
        context = context or {}

        # Map operations to validators
        validators = {
            "design": [self.validate_design],
            "ai_response": [self.validate_confidence],
            "optimization": [self.validate_evidence],
            "phase_action": [
                lambda: self.validate_phase_compliance(
                    context.get("phase", "implementation"),
                    context.get("action", ""),
                    data
                )
            ],
            "phase_transition": [
                lambda: self.validate_phase_transition(
                    context.get("current_phase", ""),
                    context.get("next_phase", ""),
                    data
                )
            ]
        }

        # Run applicable validators
        for validator in validators.get(operation, []):
            try:
                result = await validator(data) if not callable(validator) else await validator()
                results.append(result)
            except Exception as e:
                logger.error(f"Validation error in {validator.__name__}: {e}")
                results.append(ValidationResult(
                    False,
                    "validation_error",
                    violations=[f"Internal validation error: {str(e)}"]
                ))

        return results

    def get_violations(
        self,
        article: Optional[str] = None,
        severity: Optional[Severity] = None,
        resolved: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Get logged violations with optional filtering

        Args:
            article: Filter by article (e.g., "P1_design_review_first")
            severity: Filter by severity
            resolved: Filter by resolution status

        Returns:
            List of violations
        """
        violations = self.violation_log

        if article:
            violations = [v for v in violations if v["article"] == article]

        if severity:
            violations = [v for v in violations if v["severity"] == severity.value]

        if resolved is not None:
            violations = [v for v in violations if v["resolved"] == resolved]

        return violations

    def get_compliance_score(self) -> float:
        """
        Calculate overall compliance score

        Returns:
            Score from 0.0 to 1.0
        """
        if not self.violation_log:
            return 1.0

        # Weight violations by severity
        severity_weights = {
            Severity.CRITICAL: 1.0,
            Severity.HIGH: 0.7,
            Severity.MEDIUM: 0.4,
            Severity.LOW: 0.2
        }

        total_weight = sum(
            severity_weights.get(Severity(v["severity"]), 0.5)
            for v in self.violation_log
            if not v["resolved"]
        )

        # Assume 100 total checks for scoring
        total_checks = max(100, len(self.violation_log))

        return max(0.0, 1.0 - (total_weight / total_checks))

    def export_violations(self, filepath: Path):
        """Export violations to JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.violation_log, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported {len(self.violation_log)} violations to {filepath}")
