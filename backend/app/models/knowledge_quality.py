"""
Knowledge Extraction Quality Models

Commercial-grade quality gate system for knowledge extraction.
Benchmarked against Notion, Confluence, and LinearB.

Target: 15,000+ chars output across 5 categories.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums and Constants
# ============================================================================


class ExtractionCategory(str, Enum):
    """Knowledge extraction categories (5 required)"""

    BEGINNER_CONCEPTS = "beginner_concepts"
    MANAGER_INSIGHTS = "manager_insights"
    TECHNICAL_DEBT = "technical_debt"
    PATTERNS = "patterns"
    AI_SYNERGY = "ai_synergy"


class GateStatus(str, Enum):
    """Quality gate check status"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class QualityLevel(str, Enum):
    """Overall quality level assessment"""

    EXCELLENT = "excellent"  # G-Eval >= 4.5, all gates passed
    GOOD = "good"  # G-Eval >= 4.0, minor issues
    ACCEPTABLE = "acceptable"  # G-Eval >= 3.5, some issues
    POOR = "poor"  # G-Eval >= 3.0, significant issues
    REJECTED = "rejected"  # G-Eval < 3.0, fails minimum


class FileType(str, Enum):
    """Supported file types for extraction"""

    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    MARKDOWN = "markdown"
    YAML = "yaml"
    JSON = "json"


# ============================================================================
# Quality Thresholds Configuration
# ============================================================================


class QualityThresholds(BaseModel):
    """
    Configurable quality thresholds.

    Based on commercial system benchmarks:
    - Notion: ~2,000 chars per document section
    - Confluence: ~1,500 chars minimum for knowledge base articles
    - LinearB: Focus on actionability and developer productivity metrics
    """

    # Character count thresholds
    min_total_chars: int = Field(default=1900, description="Minimum total chars (was 500)")
    target_total_chars: int = Field(default=15000, description="Target total chars")
    min_category_chars: int = Field(default=300, description="Minimum per category")
    target_category_chars: int = Field(default=3000, description="Target per category")

    # Category coverage thresholds
    min_categories_required: int = Field(default=3, description="Minimum categories covered")
    target_categories: int = Field(default=5, description="Target all categories")

    # Quality score thresholds
    min_g_eval_score: float = Field(default=3.5, ge=1.0, le=5.0, description="Minimum G-Eval score")
    target_g_eval_score: float = Field(default=4.0, ge=1.0, le=5.0, description="Target G-Eval score")

    # Actionability thresholds
    min_actionability_score: float = Field(default=0.50, ge=0.0, le=1.0)
    target_actionability_score: float = Field(default=0.75, ge=0.0, le=1.0)

    # Freshness thresholds (days)
    fresh_threshold_days: int = Field(default=30, description="Content considered fresh")
    stale_threshold_days: int = Field(default=60, description="Content needs review")
    archive_threshold_days: int = Field(default=90, description="Content should be archived")

    # Token thresholds for AI processing
    min_input_tokens: int = Field(default=100, description="Minimum input tokens")
    max_input_tokens: int = Field(default=128000, description="Maximum input tokens")
    min_output_tokens_per_category: int = Field(default=200, description="Minimum output tokens")


# ============================================================================
# Pre-Extraction Gate Models
# ============================================================================


class InputValidationResult(BaseModel):
    """Result of pre-extraction input validation"""

    is_valid: bool
    file_path: Optional[str] = None
    file_type: Optional[FileType] = None
    file_size_bytes: int = 0
    line_count: int = 0
    token_estimate: int = 0

    # Validation checks
    has_sufficient_content: bool = False
    is_supported_type: bool = False
    is_within_size_limits: bool = False
    has_valid_encoding: bool = False

    # Context requirements
    has_git_context: bool = False
    has_project_context: bool = False
    has_test_context: bool = False

    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    validated_at: datetime = Field(default_factory=datetime.utcnow)


class ContextRequirements(BaseModel):
    """Minimum context requirements for extraction"""

    # Git context
    require_git_diff: bool = True
    require_commit_history: bool = False
    min_commits_for_history: int = 3

    # Project context
    require_project_structure: bool = True
    require_dependencies: bool = False

    # Test context
    require_test_results: bool = False
    min_test_coverage: float = 0.0

    # Documentation context
    require_existing_docs: bool = False
    check_related_docs: bool = True


class PreExtractionGateResult(BaseModel):
    """Result of all pre-extraction gates"""

    passed: bool
    input_validation: InputValidationResult
    context_met: bool

    # Individual gate results
    gates: Dict[str, GateStatus] = Field(default_factory=dict)

    # Blocking issues
    blocking_errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    checked_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Extraction Quality Gate Models
# ============================================================================


class CategoryExtraction(BaseModel):
    """Extraction result for a single category"""

    category: ExtractionCategory
    content: str = ""
    char_count: int = 0
    token_count: int = 0

    # Quality metrics
    has_actionable_items: bool = False
    actionable_item_count: int = 0
    has_code_examples: bool = False
    has_references: bool = False

    # Validation status
    meets_minimum_length: bool = False
    meets_target_length: bool = False

    @field_validator("char_count", mode="before")
    @classmethod
    def calculate_char_count(cls, v, info):
        """Auto-calculate char count from content"""
        if v == 0 and "content" in info.data:
            return len(info.data.get("content", ""))
        return v


class ExtractionQualityResult(BaseModel):
    """Quality assessment during extraction"""

    # Category-level results
    categories: Dict[ExtractionCategory, CategoryExtraction] = Field(default_factory=dict)

    # Aggregate metrics
    total_char_count: int = 0
    total_token_count: int = 0
    categories_covered: int = 0

    # Token thresholds met
    meets_min_tokens: bool = False
    within_max_tokens: bool = False

    # Mandatory field validation
    has_required_fields: bool = False
    missing_fields: List[str] = Field(default_factory=list)

    # JSON schema validation
    schema_valid: bool = False
    schema_errors: List[str] = Field(default_factory=list)

    # Prompt quality (for AI extraction)
    prompt_quality_score: float = 0.0
    prompt_issues: List[str] = Field(default_factory=list)

    # Gate status
    gates: Dict[str, GateStatus] = Field(default_factory=dict)

    processed_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Post-Extraction Gate Models
# ============================================================================


class GEvalScore(BaseModel):
    """
    G-Eval quality assessment using LLM-as-judge.

    Based on the G-Eval framework for NLG evaluation:
    - Coherence: Logical flow and structure
    - Consistency: Factual alignment with source
    - Fluency: Readability and grammar
    - Relevance: Pertinence to the task/topic
    """

    coherence: float = Field(..., ge=1.0, le=5.0)
    consistency: float = Field(..., ge=1.0, le=5.0)
    fluency: float = Field(..., ge=1.0, le=5.0)
    relevance: float = Field(..., ge=1.0, le=5.0)

    # Weighted average (can adjust weights based on use case)
    overall: float = Field(..., ge=1.0, le=5.0)

    # LLM evaluation metadata
    model_used: str = "gpt-4o"
    evaluation_prompt_version: str = "v1.0"
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    @classmethod
    def calculate_overall(
        cls, coherence: float, consistency: float, fluency: float, relevance: float, weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate weighted overall score"""
        default_weights = {
            "coherence": 0.25,
            "consistency": 0.30,  # Higher weight for accuracy
            "fluency": 0.15,
            "relevance": 0.30,  # Higher weight for usefulness
        }
        w = weights or default_weights
        return (
            coherence * w["coherence"] + consistency * w["consistency"] + fluency * w["fluency"] + relevance * w["relevance"]
        )


class ActionabilityScore(BaseModel):
    """Assessment of how actionable the extracted knowledge is"""

    # Overall actionability (0-1)
    score: float = Field(..., ge=0.0, le=1.0)

    # Component scores
    has_clear_next_steps: bool = False
    has_implementation_guidance: bool = False
    has_code_examples: bool = False
    has_decision_criteria: bool = False
    has_success_metrics: bool = False

    # Counts
    action_items_count: int = 0
    code_snippets_count: int = 0
    reference_links_count: int = 0

    # Categorized actions
    immediate_actions: List[str] = Field(default_factory=list)
    short_term_actions: List[str] = Field(default_factory=list)
    long_term_actions: List[str] = Field(default_factory=list)


class DuplicateCheckResult(BaseModel):
    """Result of duplicate content detection"""

    is_duplicate: bool = False
    is_near_duplicate: bool = False

    # Similarity scores
    exact_match_found: bool = False
    highest_similarity_score: float = 0.0
    similarity_threshold: float = 0.85

    # Related content
    similar_documents: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_merge_targets: List[str] = Field(default_factory=list)

    checked_at: datetime = Field(default_factory=datetime.utcnow)


class LinkValidationResult(BaseModel):
    """Validation of internal and external links"""

    total_links: int = 0
    valid_links: int = 0
    broken_links: int = 0

    # Categorized links
    internal_links: List[str] = Field(default_factory=list)
    external_links: List[str] = Field(default_factory=list)
    broken_link_details: List[Dict[str, str]] = Field(default_factory=list)

    # Obsidian-specific
    obsidian_wikilinks: List[str] = Field(default_factory=list)
    missing_backlinks: List[str] = Field(default_factory=list)


class PostExtractionGateResult(BaseModel):
    """Comprehensive post-extraction quality assessment"""

    passed: bool
    quality_level: QualityLevel

    # Character count validation
    total_char_count: int = 0
    meets_min_chars: bool = False
    meets_target_chars: bool = False

    # Category coverage
    categories_covered: int = 0
    meets_min_categories: bool = False
    category_details: Dict[ExtractionCategory, int] = Field(default_factory=dict)

    # Quality scores
    g_eval: Optional[GEvalScore] = None
    actionability: Optional[ActionabilityScore] = None

    # Duplicate detection
    duplicate_check: Optional[DuplicateCheckResult] = None

    # Link validation
    link_validation: Optional[LinkValidationResult] = None

    # Individual gate results
    gates: Dict[str, GateStatus] = Field(default_factory=dict)

    # Summary
    passed_gates: int = 0
    failed_gates: int = 0
    warning_gates: int = 0

    # Recommendations for improvement
    improvement_suggestions: List[str] = Field(default_factory=list)

    validated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Continuous Monitoring Gate Models
# ============================================================================


class ContentFreshness(BaseModel):
    """Content freshness tracking"""

    document_id: UUID
    document_path: str

    created_at: datetime
    last_updated_at: datetime
    last_viewed_at: Optional[datetime] = None

    # Age metrics
    age_days: int = 0
    freshness_status: str = "fresh"  # fresh, stale, archive_candidate

    # Update triggers
    needs_review: bool = False
    review_reason: Optional[str] = None
    suggested_review_date: Optional[datetime] = None


class UsageAnalytics(BaseModel):
    """Usage tracking for knowledge content"""

    document_id: UUID
    document_path: str

    # View metrics
    total_views: int = 0
    unique_viewers: int = 0
    avg_time_on_page_seconds: float = 0.0

    # Reference metrics
    times_referenced: int = 0
    referenced_by: List[str] = Field(default_factory=list)

    # Search metrics
    search_appearances: int = 0
    search_click_through_rate: float = 0.0

    # Time-based metrics
    views_last_7_days: int = 0
    views_last_30_days: int = 0
    trend: str = "stable"  # increasing, stable, decreasing

    tracked_since: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class FeedbackMetrics(BaseModel):
    """User feedback collection for knowledge content"""

    document_id: UUID
    document_path: str

    # Helpfulness
    helpful_votes: int = 0
    not_helpful_votes: int = 0
    helpfulness_ratio: float = 0.0

    # Ratings (1-5)
    average_rating: float = 0.0
    total_ratings: int = 0
    rating_distribution: Dict[int, int] = Field(default_factory=dict)

    # Comments
    total_comments: int = 0
    improvement_suggestions: List[str] = Field(default_factory=list)

    # Corrections
    factual_corrections: int = 0
    pending_corrections: List[Dict[str, Any]] = Field(default_factory=list)


class StaleContentAlert(BaseModel):
    """Alert for stale or outdated content"""

    document_id: UUID
    document_path: str
    alert_type: str  # stale, low_usage, needs_update, factual_issue

    severity: str  # low, medium, high, critical

    # Context
    age_days: int = 0
    last_update: datetime
    usage_trend: str = "stable"

    # Recommendations
    suggested_action: str
    action_deadline: Optional[datetime] = None
    assigned_to: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False


class ContinuousMonitoringResult(BaseModel):
    """Aggregate continuous monitoring status"""

    document_id: UUID
    document_path: str

    # Component results
    freshness: ContentFreshness
    usage: UsageAnalytics
    feedback: FeedbackMetrics

    # Active alerts
    active_alerts: List[StaleContentAlert] = Field(default_factory=list)

    # Health score (0-100)
    health_score: int = 100
    health_factors: Dict[str, int] = Field(default_factory=dict)

    # Recommendations
    priority_actions: List[str] = Field(default_factory=list)

    last_checked: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# Comprehensive Quality Report
# ============================================================================


class KnowledgeQualityReport(BaseModel):
    """
    Complete quality report for knowledge extraction.

    Aggregates all gate results and provides actionable insights.
    """

    extraction_id: UUID
    document_path: Optional[str] = None

    # Overall assessment
    overall_passed: bool = False
    quality_level: QualityLevel = QualityLevel.REJECTED
    overall_score: float = Field(default=0.0, ge=0.0, le=100.0)

    # Gate results
    pre_extraction: Optional[PreExtractionGateResult] = None
    extraction_quality: Optional[ExtractionQualityResult] = None
    post_extraction: Optional[PostExtractionGateResult] = None
    continuous_monitoring: Optional[ContinuousMonitoringResult] = None

    # Summary statistics
    total_gates_checked: int = 0
    gates_passed: int = 0
    gates_failed: int = 0
    gates_warning: int = 0

    # Content metrics
    total_char_count: int = 0
    categories_covered: int = 0
    g_eval_score: Optional[float] = None
    actionability_score: Optional[float] = None

    # Recommendations
    blocking_issues: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)

    # Metadata
    thresholds_used: Optional[QualityThresholds] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0

    def calculate_overall_score(self) -> float:
        """Calculate weighted overall quality score (0-100)"""
        score = 0.0
        weights = {
            "char_count": 20,  # 20% for content volume
            "categories": 15,  # 15% for coverage
            "g_eval": 35,  # 35% for content quality
            "actionability": 20,  # 20% for usefulness
            "gates": 10,  # 10% for gate compliance
        }

        # Character count score
        if self.thresholds_used:
            char_ratio = min(1.0, self.total_char_count / self.thresholds_used.target_total_chars)
            score += char_ratio * weights["char_count"]

        # Category coverage score
        cat_ratio = min(1.0, self.categories_covered / 5)
        score += cat_ratio * weights["categories"]

        # G-Eval score (1-5 scaled to 0-100)
        if self.g_eval_score:
            g_eval_ratio = (self.g_eval_score - 1) / 4  # Normalize 1-5 to 0-1
            score += g_eval_ratio * weights["g_eval"]

        # Actionability score
        if self.actionability_score:
            score += self.actionability_score * weights["actionability"]

        # Gate compliance score
        if self.total_gates_checked > 0:
            gate_ratio = self.gates_passed / self.total_gates_checked
            score += gate_ratio * weights["gates"]

        return round(score, 2)

    def determine_quality_level(self) -> QualityLevel:
        """Determine quality level based on scores"""
        if not self.g_eval_score:
            return QualityLevel.REJECTED

        if self.g_eval_score >= 4.5 and self.gates_failed == 0:
            return QualityLevel.EXCELLENT
        elif self.g_eval_score >= 4.0:
            return QualityLevel.GOOD
        elif self.g_eval_score >= 3.5:
            return QualityLevel.ACCEPTABLE
        elif self.g_eval_score >= 3.0:
            return QualityLevel.POOR
        else:
            return QualityLevel.REJECTED
