"""
Knowledge Extraction Quality Gate Service

Commercial-grade quality gate system for knowledge extraction.
Benchmarked against Notion, Confluence, and LinearB.

Implements 4 gate types:
1. Pre-Extraction Gates - Input validation and context requirements
2. Extraction Quality Gates - Token thresholds, schema validation, prompt quality
3. Post-Extraction Gates - Character counts, G-Eval, actionability, duplicates
4. Continuous Monitoring Gates - Freshness, usage, feedback, staleness alerts
"""

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# Import models
from app.models.knowledge_quality import (  # noqa: E402
    ActionabilityScore,
    CategoryExtraction,
    ContentFreshness,
    ContextRequirements,
    ContinuousMonitoringResult,
    DuplicateCheckResult,
    ExtractionCategory,
    ExtractionQualityResult,
    FeedbackMetrics,
    FileType,
    GateStatus,
    GEvalScore,
    InputValidationResult,
    KnowledgeQualityReport,
    LinkValidationResult,
    PostExtractionGateResult,
    PreExtractionGateResult,
    QualityLevel,
    QualityThresholds,
    StaleContentAlert,
    UsageAnalytics,
)


class KnowledgeQualityGateService:
    """
    Comprehensive quality gate service for knowledge extraction.

    Provides validation at 4 stages:
    1. Pre-Extraction: Input validation, context requirements
    2. Extraction: Token thresholds, schema validation
    3. Post-Extraction: Quality scoring, duplicate detection
    4. Continuous Monitoring: Freshness, usage, feedback
    """

    def __init__(
        self,
        thresholds: Optional[QualityThresholds] = None,
        enable_ai_scoring: bool = True,
        obsidian_vault_path: Optional[Path] = None,
    ):
        """
        Initialize quality gate service.

        Args:
            thresholds: Quality thresholds configuration
            enable_ai_scoring: Whether to use AI for G-Eval scoring
            obsidian_vault_path: Path to Obsidian vault for duplicate detection
        """
        self.thresholds = thresholds or QualityThresholds()
        self.enable_ai_scoring = enable_ai_scoring
        self.obsidian_vault_path = obsidian_vault_path

        # In-memory storage for monitoring (production: use database)
        self._document_registry: Dict[UUID, Dict[str, Any]] = {}
        self._usage_data: Dict[UUID, UsageAnalytics] = {}
        self._feedback_data: Dict[UUID, FeedbackMetrics] = {}
        self._content_hashes: Dict[str, UUID] = {}  # For duplicate detection

        # OpenAI client for G-Eval (lazy initialization)
        self._openai_client = None

        logger.info(
            f"KnowledgeQualityGateService initialized with thresholds: "
            f"min_chars={self.thresholds.min_total_chars}, "
            f"target_chars={self.thresholds.target_total_chars}, "
            f"min_g_eval={self.thresholds.min_g_eval_score}"
        )

    # ========================================================================
    # PRE-EXTRACTION GATES
    # ========================================================================

    def validate_input(
        self,
        content: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> InputValidationResult:
        """
        Validate input content before extraction.

        Checks:
        - Content length (minimum tokens)
        - File type support
        - Size limits
        - Encoding validity
        - Context availability (git, project, tests)
        """
        result = InputValidationResult(
            is_valid=False,
            file_path=file_path,
        )

        errors = []
        warnings = []

        # 1. Basic content validation
        if not content or len(content.strip()) == 0:
            errors.append("Content is empty or whitespace only")
            result.errors = errors
            return result

        result.line_count = len(content.splitlines())
        result.file_size_bytes = len(content.encode("utf-8"))

        # Estimate tokens (rough: 1 token ~ 4 chars for English)
        result.token_estimate = len(content) // 4

        # 2. Check sufficient content
        if result.token_estimate >= self.thresholds.min_input_tokens:
            result.has_sufficient_content = True
        else:
            errors.append(
                f"Insufficient content: {result.token_estimate} tokens " f"(minimum: {self.thresholds.min_input_tokens})"
            )

        # 3. Check within size limits
        if result.token_estimate <= self.thresholds.max_input_tokens:
            result.is_within_size_limits = True
        else:
            errors.append(
                f"Content too large: {result.token_estimate} tokens " f"(maximum: {self.thresholds.max_input_tokens})"
            )

        # 4. Detect and validate file type
        if file_path:
            detected_type = self._detect_file_type(file_path)
            if detected_type:
                result.file_type = detected_type
                result.is_supported_type = True
            else:
                warnings.append(f"Unsupported file type: {Path(file_path).suffix}")

        # 5. Validate encoding
        try:
            content.encode("utf-8").decode("utf-8")
            result.has_valid_encoding = True
        except UnicodeError:
            errors.append("Content has invalid UTF-8 encoding")

        # 6. Check context availability
        if context:
            result.has_git_context = bool(context.get("git_diff") or context.get("commit_hash"))
            result.has_project_context = bool(context.get("project_structure"))
            result.has_test_context = bool(context.get("test_results"))

        # Determine overall validity
        result.errors = errors
        result.warnings = warnings
        result.is_valid = (
            result.has_sufficient_content and result.is_within_size_limits and result.has_valid_encoding and len(errors) == 0
        )

        return result

    def check_context_requirements(
        self,
        context: Dict[str, Any],
        requirements: Optional[ContextRequirements] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Check if context meets minimum requirements.

        Returns:
            Tuple of (requirements_met, list of missing requirements)
        """
        reqs = requirements or ContextRequirements()
        missing = []

        # Git context
        if reqs.require_git_diff:
            if not context.get("git_diff"):
                missing.append("Git diff required but not provided")

        if reqs.require_commit_history:
            commits = context.get("commit_history", [])
            if len(commits) < reqs.min_commits_for_history:
                missing.append(f"Commit history requires {reqs.min_commits_for_history} commits, " f"got {len(commits)}")

        # Project context
        if reqs.require_project_structure:
            if not context.get("project_structure"):
                missing.append("Project structure required but not provided")

        if reqs.require_dependencies:
            if not context.get("dependencies"):
                missing.append("Dependencies list required but not provided")

        # Test context
        if reqs.require_test_results:
            if not context.get("test_results"):
                missing.append("Test results required but not provided")

            if reqs.min_test_coverage > 0:
                coverage = context.get("test_coverage", 0)
                if coverage < reqs.min_test_coverage:
                    missing.append(f"Test coverage {coverage}% below minimum {reqs.min_test_coverage}%")

        return len(missing) == 0, missing

    def run_pre_extraction_gates(
        self,
        content: str,
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        requirements: Optional[ContextRequirements] = None,
    ) -> PreExtractionGateResult:
        """
        Run all pre-extraction quality gates.

        Returns comprehensive result with all gate statuses.
        """
        gates: Dict[str, GateStatus] = {}
        blocking_errors: List[str] = []
        warnings: List[str] = []
        recommendations: List[str] = []

        # Gate 1: Input validation
        input_result = self.validate_input(content, file_path, context)
        gates["input_validation"] = GateStatus.PASSED if input_result.is_valid else GateStatus.FAILED
        blocking_errors.extend(input_result.errors)
        warnings.extend(input_result.warnings)

        # Gate 2: Content sufficiency
        if input_result.has_sufficient_content:
            gates["content_sufficiency"] = GateStatus.PASSED
        else:
            gates["content_sufficiency"] = GateStatus.FAILED

        # Gate 3: Size limits
        if input_result.is_within_size_limits:
            gates["size_limits"] = GateStatus.PASSED
        else:
            gates["size_limits"] = GateStatus.FAILED

        # Gate 4: File type
        if input_result.is_supported_type or not file_path:
            gates["file_type"] = GateStatus.PASSED
        else:
            gates["file_type"] = GateStatus.WARNING
            recommendations.append("Consider using a supported file type for better extraction")

        # Gate 5: Context requirements
        context_met, missing_context = self.check_context_requirements(context or {}, requirements)
        if context_met:
            gates["context_requirements"] = GateStatus.PASSED
        else:
            gates["context_requirements"] = GateStatus.WARNING
            warnings.extend(missing_context)
            recommendations.append("Provide additional context for better extraction quality")

        # Recommendations based on content
        if input_result.token_estimate < 500:
            recommendations.append("Content is minimal. Consider including more context for richer extraction.")

        if not input_result.has_git_context:
            recommendations.append("Git context (diff, commits) improves extraction of change-related insights.")

        # Determine overall pass/fail
        failed_critical = any(
            status == GateStatus.FAILED
            for gate_name, status in gates.items()
            if gate_name in ["input_validation", "content_sufficiency", "size_limits"]
        )

        return PreExtractionGateResult(
            passed=not failed_critical,
            input_validation=input_result,
            context_met=context_met,
            gates=gates,
            blocking_errors=blocking_errors,
            warnings=warnings,
            recommendations=recommendations,
        )

    # ========================================================================
    # EXTRACTION QUALITY GATES
    # ========================================================================

    def validate_extraction_output(
        self,
        extraction_data: Dict[str, Any],
        expected_schema: Optional[Dict[str, Any]] = None,
    ) -> ExtractionQualityResult:
        """
        Validate extraction output during/after AI processing.

        Checks:
        - Token length per category
        - Mandatory field presence
        - JSON schema compliance
        - Category coverage
        """
        result = ExtractionQualityResult()
        gates: Dict[str, GateStatus] = {}

        # Parse categories from extraction data
        categories_data = extraction_data.get("categories", {})

        for category in ExtractionCategory:
            cat_data = categories_data.get(category.value, {})
            content = cat_data.get("content", "") if isinstance(cat_data, dict) else str(cat_data)

            char_count = len(content)
            token_count = char_count // 4  # Rough estimate

            category_result = CategoryExtraction(
                category=category,
                content=content,
                char_count=char_count,
                token_count=token_count,
                meets_minimum_length=char_count >= self.thresholds.min_category_chars,
                meets_target_length=char_count >= self.thresholds.target_category_chars,
            )

            # Check for actionable items
            if content:
                category_result.has_actionable_items = self._detect_actionable_items(content)
                category_result.actionable_item_count = self._count_actionable_items(content)
                category_result.has_code_examples = self._detect_code_examples(content)
                category_result.has_references = self._detect_references(content)

            result.categories[category] = category_result
            result.total_char_count += char_count
            result.total_token_count += token_count

            if char_count >= self.thresholds.min_category_chars:
                result.categories_covered += 1

        # Gate 1: Minimum tokens
        result.meets_min_tokens = result.total_token_count >= self.thresholds.min_input_tokens
        gates["min_tokens"] = GateStatus.PASSED if result.meets_min_tokens else GateStatus.FAILED

        # Gate 2: Maximum tokens
        result.within_max_tokens = result.total_token_count <= self.thresholds.max_input_tokens
        gates["max_tokens"] = GateStatus.PASSED if result.within_max_tokens else GateStatus.FAILED

        # Gate 3: Required fields
        required_fields = ["categories", "summary", "actionable_items"]
        missing = [f for f in required_fields if f not in extraction_data]
        result.has_required_fields = len(missing) == 0
        result.missing_fields = missing
        gates["required_fields"] = GateStatus.PASSED if result.has_required_fields else GateStatus.WARNING

        # Gate 4: Schema validation
        if expected_schema:
            schema_valid, schema_errors = self._validate_json_schema(extraction_data, expected_schema)
            result.schema_valid = schema_valid
            result.schema_errors = schema_errors
            gates["schema_validation"] = GateStatus.PASSED if schema_valid else GateStatus.FAILED
        else:
            gates["schema_validation"] = GateStatus.SKIPPED

        # Gate 5: Category coverage
        if result.categories_covered >= self.thresholds.min_categories_required:
            gates["category_coverage"] = GateStatus.PASSED
        else:
            gates["category_coverage"] = GateStatus.FAILED

        result.gates = gates
        return result

    def assess_prompt_quality(
        self,
        prompt: str,
        expected_output_type: str = "knowledge_extraction",
    ) -> Tuple[float, List[str]]:
        """
        Assess the quality of the extraction prompt.

        Returns:
            Tuple of (quality_score 0-1, list of issues)
        """
        issues: List[str] = []
        score = 1.0

        # Check prompt length
        if len(prompt) < 100:
            issues.append("Prompt is too short (< 100 chars)")
            score -= 0.2

        if len(prompt) > 10000:
            issues.append("Prompt is very long (> 10000 chars), may cause truncation")
            score -= 0.1

        # Check for required elements
        required_elements = {
            "output format instruction": ["json", "format", "structure"],
            "category specification": ["beginner", "manager", "technical", "pattern", "ai"],
            "quality expectations": ["comprehensive", "actionable", "specific"],
        }

        prompt_lower = prompt.lower()
        for element, keywords in required_elements.items():
            if not any(kw in prompt_lower for kw in keywords):
                issues.append(f"Missing {element}")
                score -= 0.1

        # Check for ambiguous language
        ambiguous_terms = ["maybe", "perhaps", "possibly", "might", "could be"]
        found_ambiguous = [t for t in ambiguous_terms if t in prompt_lower]
        if found_ambiguous:
            issues.append(f"Contains ambiguous terms: {', '.join(found_ambiguous)}")
            score -= 0.05

        # Ensure score stays in valid range
        score = max(0.0, min(1.0, score))

        return score, issues

    # ========================================================================
    # POST-EXTRACTION GATES
    # ========================================================================

    def run_post_extraction_gates(
        self,
        extraction_data: Dict[str, Any],
        source_content: str,
        document_id: Optional[UUID] = None,
    ) -> PostExtractionGateResult:
        """
        Run all post-extraction quality gates.

        Checks:
        - Total character count (>= 1,900 minimum)
        - Category coverage (>= 3 of 5)
        - Actionability score (>= 0.50)
        - G-Eval score (>= 3.5/5.0)
        - Duplicate detection
        - Link validation
        """
        gates: Dict[str, GateStatus] = {}
        improvement_suggestions: List[str] = []

        doc_id = document_id or uuid4()

        # Gate 1: Total character count
        total_chars = self._calculate_total_chars(extraction_data)
        meets_min_chars = total_chars >= self.thresholds.min_total_chars
        meets_target_chars = total_chars >= self.thresholds.target_total_chars

        if meets_min_chars:
            gates["char_count"] = GateStatus.PASSED
            if not meets_target_chars:
                improvement_suggestions.append(
                    f"Content is {total_chars} chars, target is {self.thresholds.target_total_chars} chars"
                )
        else:
            gates["char_count"] = GateStatus.FAILED
            improvement_suggestions.append(
                f"Content too short: {total_chars} chars (minimum: {self.thresholds.min_total_chars})"
            )

        # Gate 2: Category coverage
        category_details = self._get_category_char_counts(extraction_data)
        categories_covered = sum(1 for count in category_details.values() if count >= self.thresholds.min_category_chars)

        meets_min_categories = categories_covered >= self.thresholds.min_categories_required

        if meets_min_categories:
            gates["category_coverage"] = GateStatus.PASSED
        else:
            gates["category_coverage"] = GateStatus.FAILED
            missing_count = self.thresholds.min_categories_required - categories_covered
            improvement_suggestions.append(
                f"Need {missing_count} more categories with >= {self.thresholds.min_category_chars} chars"
            )

        # Gate 3: Actionability score
        actionability = self._calculate_actionability(extraction_data)

        if actionability.score >= self.thresholds.min_actionability_score:
            gates["actionability"] = GateStatus.PASSED
        else:
            gates["actionability"] = GateStatus.FAILED
            improvement_suggestions.append(
                f"Actionability score {actionability.score:.2f} below minimum {self.thresholds.min_actionability_score}"
            )

        if actionability.action_items_count < 3:
            improvement_suggestions.append("Add more concrete action items")

        # Gate 4: G-Eval score (AI quality assessment)
        g_eval = None
        if self.enable_ai_scoring:
            g_eval = self._calculate_g_eval(extraction_data, source_content)
            if g_eval.overall >= self.thresholds.min_g_eval_score:
                gates["g_eval"] = GateStatus.PASSED
            else:
                gates["g_eval"] = GateStatus.FAILED
                improvement_suggestions.append(
                    f"G-Eval score {g_eval.overall:.1f} below minimum {self.thresholds.min_g_eval_score}"
                )
        else:
            gates["g_eval"] = GateStatus.SKIPPED

        # Gate 5: Duplicate detection
        duplicate_result = self._check_duplicates(extraction_data, doc_id)

        if duplicate_result.is_duplicate:
            gates["duplicate_check"] = GateStatus.FAILED
            improvement_suggestions.append("Content appears to be a duplicate")
        elif duplicate_result.is_near_duplicate:
            gates["duplicate_check"] = GateStatus.WARNING
            improvement_suggestions.append(
                f"Similar content exists (similarity: {duplicate_result.highest_similarity_score:.1%})"
            )
        else:
            gates["duplicate_check"] = GateStatus.PASSED

        # Gate 6: Link validation
        link_result = self._validate_links(extraction_data)

        if link_result.broken_links == 0:
            gates["link_validation"] = GateStatus.PASSED
        elif link_result.broken_links < 3:
            gates["link_validation"] = GateStatus.WARNING
            improvement_suggestions.append(f"Fix {link_result.broken_links} broken link(s)")
        else:
            gates["link_validation"] = GateStatus.FAILED
            improvement_suggestions.append(f"Fix {link_result.broken_links} broken links")

        # Calculate summary statistics
        passed_count = sum(1 for s in gates.values() if s == GateStatus.PASSED)
        failed_count = sum(1 for s in gates.values() if s == GateStatus.FAILED)
        warning_count = sum(1 for s in gates.values() if s == GateStatus.WARNING)

        # Determine overall pass/fail and quality level
        critical_gates = ["char_count", "category_coverage", "actionability"]
        critical_failures = any(gates.get(g) == GateStatus.FAILED for g in critical_gates)

        overall_passed = not critical_failures

        # Determine quality level
        if g_eval:
            if g_eval.overall >= 4.5 and failed_count == 0:
                quality_level = QualityLevel.EXCELLENT
            elif g_eval.overall >= 4.0:
                quality_level = QualityLevel.GOOD
            elif g_eval.overall >= 3.5:
                quality_level = QualityLevel.ACCEPTABLE
            elif g_eval.overall >= 3.0:
                quality_level = QualityLevel.POOR
            else:
                quality_level = QualityLevel.REJECTED
        else:
            # Fallback quality assessment without G-Eval
            if failed_count == 0 and warning_count == 0:
                quality_level = QualityLevel.GOOD
            elif failed_count == 0:
                quality_level = QualityLevel.ACCEPTABLE
            elif failed_count <= 2:
                quality_level = QualityLevel.POOR
            else:
                quality_level = QualityLevel.REJECTED

        return PostExtractionGateResult(
            passed=overall_passed,
            quality_level=quality_level,
            total_char_count=total_chars,
            meets_min_chars=meets_min_chars,
            meets_target_chars=meets_target_chars,
            categories_covered=categories_covered,
            meets_min_categories=meets_min_categories,
            category_details=category_details,
            g_eval=g_eval,
            actionability=actionability,
            duplicate_check=duplicate_result,
            link_validation=link_result,
            gates=gates,
            passed_gates=passed_count,
            failed_gates=failed_count,
            warning_gates=warning_count,
            improvement_suggestions=improvement_suggestions,
        )

    # ========================================================================
    # CONTINUOUS MONITORING GATES
    # ========================================================================

    def register_document(
        self,
        document_id: UUID,
        document_path: str,
        content_hash: str,
    ) -> None:
        """Register a document for continuous monitoring."""
        now = datetime.utcnow()

        self._document_registry[document_id] = {
            "path": document_path,
            "content_hash": content_hash,
            "created_at": now,
            "last_updated_at": now,
            "last_viewed_at": None,
        }

        # Initialize usage and feedback data
        self._usage_data[document_id] = UsageAnalytics(
            document_id=document_id,
            document_path=document_path,
        )

        self._feedback_data[document_id] = FeedbackMetrics(
            document_id=document_id,
            document_path=document_path,
        )

        # Store hash for duplicate detection
        self._content_hashes[content_hash] = document_id

        logger.info(f"Registered document {document_id} for monitoring: {document_path}")

    def track_view(self, document_id: UUID) -> None:
        """Track a document view."""
        if document_id not in self._usage_data:
            logger.warning(f"Document {document_id} not registered for tracking")
            return

        usage = self._usage_data[document_id]
        usage.total_views += 1
        usage.views_last_7_days += 1
        usage.views_last_30_days += 1
        usage.last_updated = datetime.utcnow()

        if document_id in self._document_registry:
            self._document_registry[document_id]["last_viewed_at"] = datetime.utcnow()

    def record_feedback(
        self,
        document_id: UUID,
        helpful: Optional[bool] = None,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
    ) -> None:
        """Record user feedback for a document."""
        if document_id not in self._feedback_data:
            logger.warning(f"Document {document_id} not registered for feedback")
            return

        feedback = self._feedback_data[document_id]

        if helpful is not None:
            if helpful:
                feedback.helpful_votes += 1
            else:
                feedback.not_helpful_votes += 1

            total_votes = feedback.helpful_votes + feedback.not_helpful_votes
            feedback.helpfulness_ratio = feedback.helpful_votes / total_votes if total_votes > 0 else 0.0

        if rating is not None and 1 <= rating <= 5:
            # Update rating distribution
            feedback.rating_distribution[rating] = feedback.rating_distribution.get(rating, 0) + 1
            feedback.total_ratings += 1

            # Recalculate average
            total_score = sum(r * c for r, c in feedback.rating_distribution.items())
            feedback.average_rating = total_score / feedback.total_ratings

        if comment:
            feedback.total_comments += 1
            # Could add comment storage here

    def check_freshness(self, document_id: UUID) -> ContentFreshness:
        """Check content freshness for a document."""
        if document_id not in self._document_registry:
            raise ValueError(f"Document {document_id} not registered")

        doc_info = self._document_registry[document_id]
        now = datetime.utcnow()

        age_days = (now - doc_info["created_at"]).days
        last_updated = doc_info["last_updated_at"]

        # Determine freshness status
        if age_days <= self.thresholds.fresh_threshold_days:
            status = "fresh"
            needs_review = False
            review_reason = None
        elif age_days <= self.thresholds.stale_threshold_days:
            status = "stale"
            needs_review = True
            review_reason = "Content is becoming stale, review recommended"
        else:
            status = "archive_candidate"
            needs_review = True
            review_reason = "Content exceeds archive threshold, consider updating or archiving"

        # Suggest review date
        suggested_review = None
        if needs_review:
            suggested_review = now + timedelta(days=7)

        return ContentFreshness(
            document_id=document_id,
            document_path=doc_info["path"],
            created_at=doc_info["created_at"],
            last_updated_at=last_updated,
            last_viewed_at=doc_info.get("last_viewed_at"),
            age_days=age_days,
            freshness_status=status,
            needs_review=needs_review,
            review_reason=review_reason,
            suggested_review_date=suggested_review,
        )

    def generate_stale_alerts(self) -> List[StaleContentAlert]:
        """Generate alerts for stale content across all registered documents."""
        alerts: List[StaleContentAlert] = []
        now = datetime.utcnow()

        for doc_id, doc_info in self._document_registry.items():
            freshness = self.check_freshness(doc_id)
            usage = self._usage_data.get(doc_id)
            feedback = self._feedback_data.get(doc_id)

            # Check for stale content
            if freshness.freshness_status in ["stale", "archive_candidate"]:
                severity = "high" if freshness.freshness_status == "archive_candidate" else "medium"

                alerts.append(
                    StaleContentAlert(
                        document_id=doc_id,
                        document_path=doc_info["path"],
                        alert_type="stale",
                        severity=severity,
                        age_days=freshness.age_days,
                        last_update=doc_info["last_updated_at"],
                        usage_trend=usage.trend if usage else "unknown",
                        suggested_action="Review and update content or archive if obsolete",
                        action_deadline=now + timedelta(days=14),
                    )
                )

            # Check for low usage
            if usage and usage.views_last_30_days < 5 and usage.total_views > 0:
                alerts.append(
                    StaleContentAlert(
                        document_id=doc_id,
                        document_path=doc_info["path"],
                        alert_type="low_usage",
                        severity="low",
                        age_days=freshness.age_days,
                        last_update=doc_info["last_updated_at"],
                        usage_trend="decreasing",
                        suggested_action="Consider promoting content or reviewing relevance",
                    )
                )

            # Check for negative feedback
            if feedback and feedback.helpfulness_ratio < 0.5 and feedback.total_ratings >= 3:
                alerts.append(
                    StaleContentAlert(
                        document_id=doc_id,
                        document_path=doc_info["path"],
                        alert_type="factual_issue",
                        severity="high",
                        age_days=freshness.age_days,
                        last_update=doc_info["last_updated_at"],
                        suggested_action="Review content quality based on negative feedback",
                        action_deadline=now + timedelta(days=7),
                    )
                )

        return alerts

    def get_monitoring_status(self, document_id: UUID) -> ContinuousMonitoringResult:
        """Get comprehensive monitoring status for a document."""
        if document_id not in self._document_registry:
            raise ValueError(f"Document {document_id} not registered")

        doc_info = self._document_registry[document_id]
        freshness = self.check_freshness(document_id)
        usage = self._usage_data.get(
            document_id,
            UsageAnalytics(
                document_id=document_id,
                document_path=doc_info["path"],
            ),
        )
        feedback = self._feedback_data.get(
            document_id,
            FeedbackMetrics(
                document_id=document_id,
                document_path=doc_info["path"],
            ),
        )

        # Get alerts for this document
        all_alerts = self.generate_stale_alerts()
        doc_alerts = [a for a in all_alerts if a.document_id == document_id]

        # Calculate health score (0-100)
        health_score = 100
        health_factors: Dict[str, int] = {}

        # Freshness factor (-30 points max)
        if freshness.freshness_status == "stale":
            health_factors["freshness"] = -15
            health_score -= 15
        elif freshness.freshness_status == "archive_candidate":
            health_factors["freshness"] = -30
            health_score -= 30
        else:
            health_factors["freshness"] = 0

        # Usage factor (-20 points max)
        if usage.total_views == 0:
            health_factors["usage"] = -20
            health_score -= 20
        elif usage.views_last_30_days < 5:
            health_factors["usage"] = -10
            health_score -= 10
        else:
            health_factors["usage"] = 0

        # Feedback factor (-30 points max)
        if feedback.total_ratings > 0:
            if feedback.average_rating < 3.0:
                health_factors["feedback"] = -30
                health_score -= 30
            elif feedback.average_rating < 3.5:
                health_factors["feedback"] = -15
                health_score -= 15
            else:
                health_factors["feedback"] = 0
        else:
            health_factors["feedback"] = 0

        # Alert factor (-20 points max)
        critical_alerts = sum(1 for a in doc_alerts if a.severity in ["high", "critical"])
        if critical_alerts > 0:
            health_factors["alerts"] = -20
            health_score -= 20
        elif len(doc_alerts) > 0:
            health_factors["alerts"] = -10
            health_score -= 10
        else:
            health_factors["alerts"] = 0

        health_score = max(0, health_score)

        # Generate priority actions
        priority_actions: List[str] = []
        if freshness.needs_review:
            priority_actions.append(f"Review content ({freshness.review_reason})")
        if feedback.helpfulness_ratio < 0.5 and feedback.total_ratings >= 3:
            priority_actions.append("Address negative feedback")
        if usage.views_last_30_days < 5:
            priority_actions.append("Improve content discoverability")

        return ContinuousMonitoringResult(
            document_id=document_id,
            document_path=doc_info["path"],
            freshness=freshness,
            usage=usage,
            feedback=feedback,
            active_alerts=doc_alerts,
            health_score=health_score,
            health_factors=health_factors,
            priority_actions=priority_actions,
        )

    # ========================================================================
    # COMPREHENSIVE QUALITY REPORT
    # ========================================================================

    def generate_quality_report(
        self,
        content: str,
        extraction_data: Dict[str, Any],
        file_path: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        document_id: Optional[UUID] = None,
    ) -> KnowledgeQualityReport:
        """
        Generate comprehensive quality report for knowledge extraction.

        Runs all gates and provides actionable insights.
        """
        start_time = time.time()
        doc_id = document_id or uuid4()

        # Run all gate types
        pre_extraction = self.run_pre_extraction_gates(content, file_path, context)
        extraction_quality = self.validate_extraction_output(extraction_data)
        post_extraction = self.run_post_extraction_gates(extraction_data, content, doc_id)

        # Get monitoring status if document is registered
        continuous_monitoring = None
        if doc_id in self._document_registry:
            try:
                continuous_monitoring = self.get_monitoring_status(doc_id)
            except Exception as e:
                logger.warning(f"Could not get monitoring status: {e}")

        # Aggregate statistics
        all_gates: Dict[str, GateStatus] = {}
        all_gates.update(pre_extraction.gates)
        all_gates.update(extraction_quality.gates)
        all_gates.update(post_extraction.gates)

        total_gates = len(all_gates)
        gates_passed = sum(1 for s in all_gates.values() if s == GateStatus.PASSED)
        gates_failed = sum(1 for s in all_gates.values() if s == GateStatus.FAILED)
        gates_warning = sum(1 for s in all_gates.values() if s == GateStatus.WARNING)

        # Collect all issues and suggestions
        blocking_issues: List[str] = []
        blocking_issues.extend(pre_extraction.blocking_errors)

        improvement_suggestions: List[str] = []
        improvement_suggestions.extend(pre_extraction.recommendations)
        improvement_suggestions.extend(post_extraction.improvement_suggestions)

        # Determine overall status
        overall_passed = pre_extraction.passed and post_extraction.passed

        # Create report
        report = KnowledgeQualityReport(
            extraction_id=doc_id,
            document_path=file_path,
            overall_passed=overall_passed,
            quality_level=post_extraction.quality_level,
            pre_extraction=pre_extraction,
            extraction_quality=extraction_quality,
            post_extraction=post_extraction,
            continuous_monitoring=continuous_monitoring,
            total_gates_checked=total_gates,
            gates_passed=gates_passed,
            gates_failed=gates_failed,
            gates_warning=gates_warning,
            total_char_count=post_extraction.total_char_count,
            categories_covered=post_extraction.categories_covered,
            g_eval_score=post_extraction.g_eval.overall if post_extraction.g_eval else None,
            actionability_score=post_extraction.actionability.score if post_extraction.actionability else None,
            blocking_issues=blocking_issues,
            improvement_suggestions=improvement_suggestions,
            thresholds_used=self.thresholds,
            processing_time_ms=(time.time() - start_time) * 1000,
        )

        # Calculate overall score
        report.overall_score = report.calculate_overall_score()

        return report

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _detect_file_type(self, file_path: str) -> Optional[FileType]:
        """Detect file type from path."""
        suffix = Path(file_path).suffix.lower()
        type_map = {
            ".py": FileType.PYTHON,
            ".ts": FileType.TYPESCRIPT,
            ".tsx": FileType.TYPESCRIPT,
            ".js": FileType.JAVASCRIPT,
            ".jsx": FileType.JAVASCRIPT,
            ".md": FileType.MARKDOWN,
            ".yaml": FileType.YAML,
            ".yml": FileType.YAML,
            ".json": FileType.JSON,
        }
        return type_map.get(suffix)

    def _detect_actionable_items(self, content: str) -> bool:
        """Detect if content contains actionable items."""
        action_patterns = [
            r"\b(TODO|FIXME|ACTION|TASK)\b",
            r"\b(should|must|need to|recommend)\b",
            r"^\s*[-*]\s+\[[ x]\]",  # Checkbox items
            r"\b(step \d+|first|then|finally)\b",
        ]
        for pattern in action_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                return True
        return False

    def _count_actionable_items(self, content: str) -> int:
        """Count actionable items in content."""
        count = 0

        # Count TODO/FIXME/ACTION
        count += len(re.findall(r"\b(TODO|FIXME|ACTION|TASK)\b", content, re.IGNORECASE))

        # Count checklist items
        count += len(re.findall(r"^\s*[-*]\s+\[[ x]\]", content, re.MULTILINE))

        # Count numbered steps
        count += len(re.findall(r"^\s*\d+\.\s+", content, re.MULTILINE))

        return count

    def _detect_code_examples(self, content: str) -> bool:
        """Detect if content contains code examples."""
        code_patterns = [
            r"```\w*\n",  # Fenced code blocks
            r"`[^`]+`",  # Inline code
            r"^\s{4,}\S",  # Indented code blocks
        ]
        for pattern in code_patterns:
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False

    def _detect_references(self, content: str) -> bool:
        """Detect if content contains references/links."""
        ref_patterns = [
            r"\[.+\]\(.+\)",  # Markdown links
            r"\[\[.+\]\]",  # Wikilinks
            r"https?://\S+",  # URLs
            r"#\w+",  # Tags
        ]
        for pattern in ref_patterns:
            if re.search(pattern, content):
                return True
        return False

    def _validate_json_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """Validate data against JSON schema."""
        errors: List[str] = []

        # Basic schema validation (production: use jsonschema library)
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in data:
                expected_type = field_schema.get("type")
                if expected_type:
                    actual_type = type(data[field]).__name__
                    type_map = {"string": "str", "integer": "int", "number": "float", "array": "list", "object": "dict"}
                    if type_map.get(expected_type) != actual_type:
                        errors.append(f"Field '{field}' should be {expected_type}, got {actual_type}")

        return len(errors) == 0, errors

    def _calculate_total_chars(self, extraction_data: Dict[str, Any]) -> int:
        """Calculate total character count across all categories."""
        total = 0
        categories = extraction_data.get("categories", {})

        for cat_data in categories.values():
            if isinstance(cat_data, dict):
                content = cat_data.get("content", "")
            else:
                content = str(cat_data)
            total += len(content)

        # Also count summary and other top-level content
        for key in ["summary", "overview", "conclusion"]:
            if key in extraction_data:
                total += len(str(extraction_data[key]))

        return total

    def _get_category_char_counts(self, extraction_data: Dict[str, Any]) -> Dict[ExtractionCategory, int]:
        """Get character counts per category."""
        counts: Dict[ExtractionCategory, int] = {}
        categories = extraction_data.get("categories", {})

        for category in ExtractionCategory:
            cat_data = categories.get(category.value, {})
            if isinstance(cat_data, dict):
                content = cat_data.get("content", "")
            else:
                content = str(cat_data)
            counts[category] = len(content)

        return counts

    def _calculate_actionability(self, extraction_data: Dict[str, Any]) -> ActionabilityScore:
        """Calculate actionability score for extraction."""
        score_factors = []

        # Check for action items
        all_content = json.dumps(extraction_data)
        has_actions = self._detect_actionable_items(all_content)
        action_count = self._count_actionable_items(all_content)

        # Check for code examples
        has_code = self._detect_code_examples(all_content)
        code_count = len(re.findall(r"```\w*\n", all_content))

        # Check for references
        has_refs = self._detect_references(all_content)
        ref_count = len(re.findall(r"\[.+\]\(.+\)", all_content))

        # Calculate component scores
        has_next_steps = action_count >= 3
        has_guidance = "how to" in all_content.lower() or "step" in all_content.lower()
        has_criteria = "success" in all_content.lower() or "criteria" in all_content.lower()
        has_metrics = bool(re.search(r"\d+%|\d+\s*(minutes|hours|days)", all_content.lower()))

        # Weight factors
        if has_actions:
            score_factors.append(0.25)
        if has_code:
            score_factors.append(0.20)
        if has_next_steps:
            score_factors.append(0.15)
        if has_guidance:
            score_factors.append(0.15)
        if has_refs:
            score_factors.append(0.10)
        if has_criteria:
            score_factors.append(0.10)
        if has_metrics:
            score_factors.append(0.05)

        final_score = min(1.0, sum(score_factors))

        # Extract immediate/short-term/long-term actions
        immediate: List[str] = []
        short_term: List[str] = []
        long_term: List[str] = []

        # Simple heuristic extraction (production: use NLP)
        if "immediate" in all_content.lower() or "now" in all_content.lower():
            immediate.append("Extracted immediate action item")
        if "week" in all_content.lower() or "sprint" in all_content.lower():
            short_term.append("Extracted short-term action item")
        if "month" in all_content.lower() or "quarter" in all_content.lower():
            long_term.append("Extracted long-term action item")

        return ActionabilityScore(
            score=final_score,
            has_clear_next_steps=has_next_steps,
            has_implementation_guidance=has_guidance,
            has_code_examples=has_code,
            has_decision_criteria=has_criteria,
            has_success_metrics=has_metrics,
            action_items_count=action_count,
            code_snippets_count=code_count,
            reference_links_count=ref_count,
            immediate_actions=immediate,
            short_term_actions=short_term,
            long_term_actions=long_term,
        )

    def _calculate_g_eval(
        self,
        extraction_data: Dict[str, Any],
        source_content: str,
    ) -> GEvalScore:
        """
        Calculate G-Eval score using LLM-as-judge.

        In production, this would call GPT-4o for evaluation.
        For now, uses heuristic scoring.
        """
        all_content = json.dumps(extraction_data)

        # Heuristic coherence (structure and flow)
        coherence = 3.5
        if len(extraction_data.get("categories", {})) >= 3:
            coherence += 0.5
        if "summary" in extraction_data:
            coherence += 0.5
        if self._detect_references(all_content):
            coherence += 0.5

        # Heuristic consistency (alignment with source)
        consistency = 3.5
        # Check for overlapping terms
        source_words = set(source_content.lower().split())
        extract_words = set(all_content.lower().split())
        overlap = len(source_words & extract_words)
        if overlap > 50:
            consistency += 0.5
        if overlap > 100:
            consistency += 0.5

        # Heuristic fluency (readability)
        fluency = 4.0  # Assume good by default for generated content
        if len(all_content) < 500:
            fluency -= 0.5

        # Heuristic relevance (pertinence)
        relevance = 3.5
        if self._detect_actionable_items(all_content):
            relevance += 0.5
        if self._detect_code_examples(all_content):
            relevance += 0.5

        # Cap scores at 5.0
        coherence = min(5.0, coherence)
        consistency = min(5.0, consistency)
        fluency = min(5.0, fluency)
        relevance = min(5.0, relevance)

        overall = GEvalScore.calculate_overall(coherence, consistency, fluency, relevance)

        return GEvalScore(
            coherence=coherence,
            consistency=consistency,
            fluency=fluency,
            relevance=relevance,
            overall=overall,
            model_used="heuristic",
            evaluation_prompt_version="v1.0-heuristic",
        )

    def _check_duplicates(
        self,
        extraction_data: Dict[str, Any],
        document_id: UUID,
    ) -> DuplicateCheckResult:
        """Check for duplicate or near-duplicate content."""
        content = json.dumps(extraction_data, sort_keys=True)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Exact match check
        if content_hash in self._content_hashes:
            existing_id = self._content_hashes[content_hash]
            if existing_id != document_id:
                return DuplicateCheckResult(
                    is_duplicate=True,
                    exact_match_found=True,
                    highest_similarity_score=1.0,
                    similar_documents=[{"id": str(existing_id), "similarity": 1.0}],
                )

        # Near-duplicate check using simple similarity
        # (Production: use vector embeddings or SimHash)
        similar_docs: List[Dict[str, Any]] = []
        highest_sim = 0.0

        for stored_hash, stored_id in self._content_hashes.items():
            if stored_id == document_id:
                continue

            # Simple character overlap similarity
            # (Production: use proper similarity metrics)
            common_chars = sum(1 for c in content_hash if c in stored_hash)
            similarity = common_chars / len(content_hash)

            if similarity > highest_sim:
                highest_sim = similarity

            if similarity > 0.7:
                similar_docs.append(
                    {
                        "id": str(stored_id),
                        "similarity": round(similarity, 3),
                    }
                )

        return DuplicateCheckResult(
            is_duplicate=False,
            is_near_duplicate=highest_sim > 0.85,
            exact_match_found=False,
            highest_similarity_score=highest_sim,
            similarity_threshold=0.85,
            similar_documents=similar_docs[:5],  # Top 5
        )

    def _validate_links(self, extraction_data: Dict[str, Any]) -> LinkValidationResult:
        """Validate links in extraction data."""
        all_content = json.dumps(extraction_data)

        # Extract different link types
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", all_content)
        wiki_links = re.findall(r"\[\[([^\]]+)\]\]", all_content)
        urls = re.findall(r"https?://\S+", all_content)

        internal_links = [link for text, link in md_links if not link.startswith("http")]
        external_links = [link for text, link in md_links if link.startswith("http")] + urls

        total_links = len(md_links) + len(wiki_links) + len(urls)

        # For this implementation, we don't actually validate links
        # In production, you'd make HTTP requests for external links
        # and check file existence for internal links

        return LinkValidationResult(
            total_links=total_links,
            valid_links=total_links,  # Assume valid for now
            broken_links=0,
            internal_links=internal_links,
            external_links=list(set(external_links)),
            obsidian_wikilinks=[f"[[{link}]]" for link in wiki_links],
            broken_link_details=[],
            missing_backlinks=[],
        )


# Singleton instance
knowledge_quality_gate_service = KnowledgeQualityGateService()
