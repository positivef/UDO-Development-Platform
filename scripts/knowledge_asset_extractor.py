#!/usr/bin/env python3
"""
Knowledge Asset Extractor - 5-Category Extraction System

Extracts structured knowledge from completed tasks/commits:
1. Beginner Concepts - Learning points for junior developers
2. Management Insights - Strategic decisions and ROI data
3. Technical Debt - Intentional/unintentional tradeoffs
4. Success/Failure Patterns - Reusable solutions and anti-patterns
5. AI Collaboration Synergy - Effective AI tool usage patterns

Author: UDO Platform Team
Date: 2025-12-28
Version: 1.0.0

Quality Target: ~15,000 chars output (up from ~500 chars)
Benchmark: 20/80 -> 63/80 commercial quality
"""

import logging
import re
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================


class ExtractionCategory(Enum):
    """5 categories of knowledge extraction"""

    BEGINNER_CONCEPTS = "beginner_concepts"
    MANAGEMENT_INSIGHTS = "management_insights"
    TECHNICAL_DEBT = "technical_debt"
    PATTERNS = "patterns"
    AI_SYNERGY = "ai_synergy"


class Difficulty(Enum):
    """Difficulty levels for learning concepts"""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class BeginnerConcept:
    """Learning point for junior developers"""

    title: str
    explanation: str
    difficulty: Difficulty
    code_example: Optional[str] = None
    related_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class ManagementInsight:
    """Strategic insight for development managers"""

    title: str
    description: str
    impact_area: str  # testing, performance, security, etc.
    roi_estimate: Optional[str] = None
    metrics: Dict[str, str] = field(default_factory=dict)


@dataclass
class TechnicalDebtItem:
    """Technical debt tracking item"""

    location: str  # file:line
    debt_type: str  # intentional, unintentional, legacy
    description: str
    severity: str  # low, medium, high, critical
    remediation_estimate: Optional[str] = None
    related_todo: Optional[str] = None


@dataclass
class PatternItem:
    """Success or failure pattern"""

    pattern_type: str  # success, failure, refactoring
    name: str
    description: str
    context: str
    solution: Optional[str] = None
    anti_pattern: bool = False
    code_before: Optional[str] = None
    code_after: Optional[str] = None


@dataclass
class AISynergyItem:
    """AI collaboration effectiveness item"""

    tool_name: str
    usage_pattern: str
    effectiveness: str  # high, medium, low
    prompt_pattern: Optional[str] = None
    time_saved_estimate: Optional[str] = None


@dataclass
class ExtractionResult:
    """Complete extraction result"""

    task_id: str
    task_title: str
    extraction_timestamp: datetime

    beginner_concepts: List[BeginnerConcept] = field(default_factory=list)
    management_insights: List[ManagementInsight] = field(default_factory=list)
    technical_debt: List[TechnicalDebtItem] = field(default_factory=list)
    patterns: List[PatternItem] = field(default_factory=list)
    ai_synergy: List[AISynergyItem] = field(default_factory=list)

    # Metadata
    files_analyzed: int = 0
    lines_changed: int = 0
    extraction_duration_ms: float = 0.0
    quality_score: int = 0


# =============================================================================
# Git Diff Analyzer
# =============================================================================


class GitDiffAnalyzer:
    """Analyzes git diffs for knowledge extraction"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def get_diff(self, commit_hash: str = "HEAD", context_lines: int = 5) -> str:
        """Get git diff for a commit"""
        try:
            result = subprocess.run(
                ["git", "diff", f"{commit_hash}~1", commit_hash, f"-U{context_lines}"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.error("Git diff command timed out")
            return ""
        except FileNotFoundError:
            logger.error("Git command not found")
            return ""
        except Exception as e:
            logger.error(f"Failed to get git diff: {e}")
            return ""

    def get_changed_files(self, commit_hash: str = "HEAD") -> List[str]:
        """Get list of changed files in a commit"""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{commit_hash}~1", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
            return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
        except Exception as e:
            logger.error(f"Failed to get changed files: {e}")
            return []

    def get_commit_message(self, commit_hash: str = "HEAD") -> str:
        """Get commit message"""
        try:
            result = subprocess.run(
                ["git", "log", "-1", "--format=%B", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="replace",
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to get commit message: {e}")
            return ""

    def get_commit_stats(self, commit_hash: str = "HEAD") -> Dict[str, int]:
        """Get commit statistics (insertions, deletions, files)"""
        try:
            result = subprocess.run(
                ["git", "diff", "--stat", f"{commit_hash}~1", commit_hash],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30,
                encoding="utf-8",
                errors="replace",
            )
            stats = {"files": 0, "insertions": 0, "deletions": 0}

            # Parse last line for stats
            lines = result.stdout.strip().split("\n")
            if lines:
                last_line = lines[-1]
                # Example: " 3 files changed, 45 insertions(+), 12 deletions(-)"
                if "file" in last_line:
                    file_match = re.search(r"(\d+) files? changed", last_line)
                    if file_match:
                        stats["files"] = int(file_match.group(1))

                    ins_match = re.search(r"(\d+) insertions?\(\+\)", last_line)
                    if ins_match:
                        stats["insertions"] = int(ins_match.group(1))

                    del_match = re.search(r"(\d+) deletions?\(-\)", last_line)
                    if del_match:
                        stats["deletions"] = int(del_match.group(1))

            return stats
        except Exception as e:
            logger.error(f"Failed to get commit stats: {e}")
            return {"files": 0, "insertions": 0, "deletions": 0}


# =============================================================================
# TODO Extractor
# =============================================================================


class TodoExtractor:
    """Extracts TODO, FIXME, HACK, XXX comments from code"""

    # Python patterns
    PY_PATTERNS = {
        "todo": re.compile(r"#\s*TODO[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
        "fixme": re.compile(r"#\s*FIXME[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
        "hack": re.compile(r"#\s*HACK[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
        "xxx": re.compile(r"#\s*XXX[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
        "note": re.compile(r"#\s*NOTE[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
    }

    # JS/TS patterns
    JS_PATTERNS = {
        "todo": re.compile(r"//\s*TODO[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
        "fixme": re.compile(r"//\s*FIXME[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
        "hack": re.compile(r"//\s*HACK[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
        "xxx": re.compile(r"//\s*XXX[:\s]*(.+?)(?:\n|$)", re.IGNORECASE),
    }

    def extract_from_content(self, content: str, file_type: str = "py") -> List[Dict[str, Any]]:
        """Extract TODO-style comments from content"""
        results = []
        patterns = self.PY_PATTERNS if file_type == "py" else self.JS_PATTERNS

        for comment_type, pattern in patterns.items():
            for match in pattern.finditer(content):
                results.append({"type": comment_type, "content": match.group(1).strip(), "position": match.start()})

        return results

    def extract_from_diff(self, diff_content: str) -> List[Dict[str, Any]]:
        """Extract TODOs from added lines in a diff"""
        results = []

        for line in diff_content.split("\n"):
            if line.startswith("+") and not line.startswith("+++"):
                # Check both Python and JS patterns
                for patterns in [self.PY_PATTERNS, self.JS_PATTERNS]:
                    for comment_type, pattern in patterns.items():
                        match = pattern.search(line[1:])  # Skip the '+' prefix
                        if match:
                            results.append({"type": comment_type, "content": match.group(1).strip(), "line": line[1:]})

        return results


# =============================================================================
# Pattern Detector
# =============================================================================


class PatternDetector:
    """Detects coding patterns from git diffs"""

    # Pattern signatures to detect (20+ patterns)
    PATTERN_SIGNATURES = {
        # Testing patterns
        "tdd": {
            "indicators": ["test_", "_test.py", ".spec.", "pytest", "unittest", "@pytest.fixture"],
            "category": "testing",
            "insight": "Test-Driven Development - tests written alongside implementation for quality assurance",
        },
        "unit_testing": {
            "indicators": ["assert ", "assertEqual", "assertTrue", "expect(", "toBe("],
            "category": "testing",
            "insight": "Unit testing ensures individual components work correctly in isolation",
        },
        # Error handling patterns
        "error_handling": {
            "indicators": ["try:", "except", "raise", "catch", "throw", "finally:"],
            "category": "reliability",
            "insight": "Robust error handling implementation prevents crashes and improves UX",
        },
        "graceful_degradation": {
            "indicators": ["fallback", "default", "or None", "get(", "getattr("],
            "category": "reliability",
            "insight": "Graceful degradation provides fallback behavior when primary path fails",
        },
        # Type safety patterns
        "type_hints": {
            "indicators": ["def .+\\(.+:.+\\)", "-> ", "Optional[", "List[", "Dict[", "Union["],
            "category": "quality",
            "insight": "Type hints enable static analysis and improve code documentation",
        },
        "pydantic_validation": {
            "indicators": ["BaseModel", "Field(", "validator", "@field_validator"],
            "category": "quality",
            "insight": "Pydantic models provide runtime data validation and serialization",
        },
        # Architecture patterns
        "dependency_injection": {
            "indicators": ["inject", "provider", "container", "Depends(", "@inject"],
            "category": "architecture",
            "insight": "Dependency injection enables loose coupling and testability",
        },
        "factory_pattern": {
            "indicators": ["Factory", "create_", "build_", "make_"],
            "category": "architecture",
            "insight": "Factory pattern encapsulates object creation logic",
        },
        "singleton": {
            "indicators": ["_instance", "getInstance", "__new__", "@singleton"],
            "category": "architecture",
            "insight": "Singleton ensures a single instance exists across the application",
        },
        # Performance patterns
        "caching": {
            "indicators": ["@cache", "@lru_cache", "redis", "memcache", "cached_property"],
            "category": "performance",
            "insight": "Caching reduces redundant computation and improves response times",
        },
        "async_pattern": {
            "indicators": ["async def", "await ", "asyncio", "aiohttp", "async with"],
            "category": "performance",
            "insight": "Asynchronous programming improves I/O-bound operation efficiency",
        },
        "lazy_loading": {
            "indicators": ["lazy", "__getattr__", "on_demand", "deferred"],
            "category": "performance",
            "insight": "Lazy loading defers resource initialization until needed",
        },
        # Resilience patterns
        "circuit_breaker": {
            "indicators": ["circuit", "breaker", "CircuitBreaker", "circuit_breaker"],
            "category": "reliability",
            "insight": "Circuit breaker prevents cascading failures in distributed systems",
        },
        "retry_pattern": {
            "indicators": ["retry", "backoff", "tenacity", "@retry", "max_retries"],
            "category": "reliability",
            "insight": "Retry with backoff handles transient failures gracefully",
        },
        "rate_limiting": {
            "indicators": ["rate_limit", "throttle", "slowapi", "RateLimiter", "rate_limiter"],
            "category": "security",
            "insight": "Rate limiting prevents abuse and ensures fair resource usage",
        },
        # Security patterns
        "input_validation": {
            "indicators": ["sanitize", "validate", "escape", "clean_", "purify"],
            "category": "security",
            "insight": "Input validation prevents injection attacks and data corruption",
        },
        "secrets_management": {
            "indicators": ["getenv", "environ", "config[", "settings.", "SecretStr"],
            "category": "security",
            "insight": "Environment-based secrets management protects sensitive data",
        },
        "authentication": {
            "indicators": ["jwt", "token", "authenticate", "authorize", "OAuth"],
            "category": "security",
            "insight": "Authentication and authorization protect resources from unauthorized access",
        },
        # Code quality patterns
        "refactoring": {
            "indicators": ["refactor", "cleanup", "extract", "simplify", "reorganize"],
            "category": "maintainability",
            "insight": "Refactoring improves code structure without changing behavior",
        },
        "documentation": {
            "indicators": ['"""', "'''", "docstring", "@param", "@return", ":param", ":return"],
            "category": "maintainability",
            "insight": "Inline documentation improves code understandability",
        },
        "logging": {
            "indicators": ["logger.", "logging.", "log.info", "log.error", "log.debug"],
            "category": "observability",
            "insight": "Structured logging enables debugging and monitoring",
        },
        # Operations patterns
        "feature_flag": {
            "indicators": ["feature_flag", "toggle", "is_enabled", "feature_", "FeatureFlag"],
            "category": "operations",
            "insight": "Feature flags enable safe, gradual feature rollouts",
        },
        "health_check": {
            "indicators": ["health", "/healthz", "/ready", "liveness", "readiness"],
            "category": "operations",
            "insight": "Health checks enable infrastructure to monitor application status",
        },
    }

    def detect_patterns(self, diff_content: str, commit_message: str) -> List[PatternItem]:
        """Detect patterns from diff and commit message"""
        detected = []
        combined_text = f"{commit_message}\n{diff_content}"

        for pattern_name, config in self.PATTERN_SIGNATURES.items():
            for indicator in config["indicators"]:
                if re.search(indicator, combined_text, re.IGNORECASE):
                    detected.append(
                        PatternItem(
                            pattern_type="success",
                            name=pattern_name.replace("_", " ").title(),
                            description=config["insight"],
                            context=config["category"],
                            anti_pattern=False,
                        )
                    )
                    break  # One match per pattern type is enough

        return detected

    def detect_anti_patterns(self, diff_content: str) -> List[PatternItem]:
        """Detect anti-patterns in code"""
        anti_patterns = []

        # Check for common anti-patterns
        anti_pattern_checks = [
            {
                "pattern": r"except:\s*pass",
                "name": "Silent Exception Swallowing",
                "description": "Catching all exceptions and ignoring them hides bugs",
            },
            {
                "pattern": r"# type:\s*ignore",
                "name": "Type Ignore Overuse",
                "description": "Overusing type: ignore reduces type safety benefits",
            },
            {
                "pattern": r"time\.sleep\(\d{2,}\)",
                "name": "Long Sleep",
                "description": "Long sleeps in code may indicate polling anti-pattern",
            },
            {
                "pattern": r"import \*",
                "name": "Star Import",
                "description": "Star imports pollute namespace and hide dependencies",
            },
        ]

        for check in anti_pattern_checks:
            if re.search(check["pattern"], diff_content):
                anti_patterns.append(
                    PatternItem(
                        pattern_type="failure",
                        name=check["name"],
                        description=check["description"],
                        context="quality",
                        anti_pattern=True,
                    )
                )

        return anti_patterns


# =============================================================================
# Knowledge Asset Extractor (Main Engine)
# =============================================================================


class KnowledgeAssetExtractor:
    """Main extraction engine for knowledge assets"""

    def __init__(self, repo_path: Optional[Path] = None, enable_git: bool = True, enable_secrets_redaction: bool = True):
        self.repo_path = repo_path or Path.cwd()
        self.enable_git = enable_git
        self.enable_secrets_redaction = enable_secrets_redaction

        # Initialize components
        self.git_analyzer = GitDiffAnalyzer(self.repo_path) if enable_git else None
        self.todo_extractor = TodoExtractor()
        self.pattern_detector = PatternDetector()

        # Secrets redactor integration
        self._secrets_redactor = None
        if enable_secrets_redaction:
            try:
                from backend.app.utils.secrets_redactor import SecretsRedactor

                self._secrets_redactor = SecretsRedactor(log_findings=False)
                logger.info("SecretsRedactor initialized successfully")
            except ImportError:
                logger.warning("SecretsRedactor not available, skipping secrets redaction")

    def _redact_secrets(self, content: str) -> str:
        """Redact secrets from content if enabled"""
        if self._secrets_redactor:
            try:
                redacted, _ = self._secrets_redactor.redact(content)
                return redacted
            except Exception as e:
                logger.warning(f"Secrets redaction failed: {e}")
        return content

    def extract_from_commit(
        self, commit_hash: str = "HEAD", task_id: Optional[str] = None, task_title: Optional[str] = None
    ) -> ExtractionResult:
        """Extract knowledge assets from a git commit"""
        start_time = time.time()

        # Get commit data
        diff_content = ""
        commit_message = ""
        changed_files: List[str] = []
        stats = {"files": 0, "insertions": 0, "deletions": 0}

        if self.git_analyzer:
            diff_content = self.git_analyzer.get_diff(commit_hash)
            commit_message = self.git_analyzer.get_commit_message(commit_hash)
            changed_files = self.git_analyzer.get_changed_files(commit_hash)
            stats = self.git_analyzer.get_commit_stats(commit_hash)

            # Redact secrets from diff
            diff_content = self._redact_secrets(diff_content)

        # Initialize result
        result = ExtractionResult(
            task_id=task_id or commit_hash[:8],
            task_title=task_title or commit_message.split("\n")[0][:80] if commit_message else "Unknown",
            extraction_timestamp=datetime.utcnow(),
            files_analyzed=stats["files"] or len(changed_files),
            lines_changed=stats["insertions"] + stats["deletions"],
        )

        # Extract 5 categories
        result.beginner_concepts = self._extract_beginner_concepts(diff_content, changed_files, commit_message)
        result.management_insights = self._extract_management_insights(diff_content, changed_files, commit_message, stats)
        result.technical_debt = self._extract_technical_debt(diff_content, changed_files)
        result.patterns = self.pattern_detector.detect_patterns(diff_content, commit_message)
        result.patterns.extend(self.pattern_detector.detect_anti_patterns(diff_content))
        result.ai_synergy = self._extract_ai_synergy(commit_message, diff_content)

        result.extraction_duration_ms = (time.time() - start_time) * 1000
        result.quality_score = self._calculate_quality_score(result)

        return result

    def _extract_beginner_concepts(
        self, diff_content: str, changed_files: List[str], commit_message: str
    ) -> List[BeginnerConcept]:
        """Extract learning concepts for beginners"""
        concepts = []

        # Detect function/method patterns
        if "def " in diff_content:
            # Check for different function patterns
            if re.search(r"def [a-z_]+\([^)]+:[^)]+\)", diff_content):
                concepts.append(
                    BeginnerConcept(
                        title="Function Type Annotations",
                        explanation="Adding type hints to function parameters and return values helps catch bugs early, "
                        "enables IDE autocomplete, and serves as inline documentation. Python's type system "
                        "is optional but highly recommended for maintainable code.",
                        difficulty=Difficulty.MEDIUM,
                        code_example="def greet(name: str, age: int = 0) -> str:\n    return f'Hello {name}, age {age}'",
                        related_files=changed_files[:3],
                        tags=["type-safety", "documentation", "python"],
                    )
                )

            if "async def" in diff_content:
                concepts.append(
                    BeginnerConcept(
                        title="Asynchronous Functions",
                        explanation="Async functions allow concurrent execution of I/O-bound operations. "
                        "They don't block the thread while waiting for external resources like databases "
                        "or APIs, improving application responsiveness and throughput.",
                        difficulty=Difficulty.HARD,
                        code_example=(
                            "async def fetch_data(url: str) -> dict:\n"
                            "    async with aiohttp.ClientSession() as session:\n"
                            "        async with session.get(url) as response:\n"
                            "            return await response.json()"
                        ),
                        tags=["async", "performance", "concurrency"],
                    )
                )

        # Detect error handling
        if "try:" in diff_content or "except" in diff_content:
            concepts.append(
                BeginnerConcept(
                    title="Exception Handling Pattern",
                    explanation="Using try-except blocks allows graceful handling of errors without crashing the application. "
                    "Always catch specific exceptions rather than bare except, and consider what recovery action "
                    "makes sense for each error type.",
                    difficulty=Difficulty.EASY,
                    code_example=(
                        "try:\n"
                        "    result = risky_operation()\n"
                        "except ValueError as e:\n"
                        "    logger.error(f'Invalid value: {e}')\n"
                        "    result = default_value"
                    ),
                    related_files=changed_files[:2],
                    tags=["error-handling", "reliability", "best-practices"],
                )
            )

        # Detect class patterns
        if "class " in diff_content:
            concepts.append(
                BeginnerConcept(
                    title="Class-Based Design",
                    explanation="Classes encapsulate related data and behavior together, following OOP "
                    "principles. They enable code reuse through inheritance and clear interfaces.",
                    difficulty=Difficulty.MEDIUM,
                    related_files=[f for f in changed_files if f.endswith(".py")][:3],
                    tags=["oop", "design", "encapsulation"],
                )
            )

        # Detect dataclass usage
        if "@dataclass" in diff_content:
            concepts.append(
                BeginnerConcept(
                    title="Python Dataclasses",
                    explanation="Dataclasses automatically generate __init__, __repr__, and __eq__ methods, reducing "
                    "boilerplate code for data-holding classes. They're perfect for DTOs, configuration, "
                    "and structured data.",
                    difficulty=Difficulty.EASY,
                    code_example="@dataclass\nclass User:\n    name: str\n    email: str\n    age: int = 0",
                    tags=["python", "dataclass", "clean-code"],
                )
            )

        # Detect test patterns
        if "test_" in diff_content or "pytest" in diff_content.lower():
            concepts.append(
                BeginnerConcept(
                    title="Unit Testing Fundamentals",
                    explanation="Unit tests verify that individual functions and methods work correctly in isolation. "
                    "They catch bugs early, enable safe refactoring, and serve as executable documentation "
                    "of expected behavior.",
                    difficulty=Difficulty.MEDIUM,
                    code_example="def test_add_numbers():\n    assert add(2, 3) == 5\n    assert add(-1, 1) == 0",
                    related_files=[f for f in changed_files if "test" in f.lower()][:3],
                    tags=["testing", "tdd", "quality"],
                )
            )

        # Detect logging patterns
        if "logger." in diff_content or "logging." in diff_content:
            concepts.append(
                BeginnerConcept(
                    title="Structured Logging",
                    explanation="Logging provides visibility into application behavior during development and production. "
                    "Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL) and include relevant "
                    "context in messages.",
                    difficulty=Difficulty.EASY,
                    code_example=(
                        "logger = logging.getLogger(__name__)\n"
                        "logger.info(f'Processing user {user_id}')\n"
                        "logger.error(f'Failed: {error}', exc_info=True)"
                    ),
                    tags=["logging", "debugging", "observability"],
                )
            )

        return concepts

    def _extract_management_insights(
        self, diff_content: str, changed_files: List[str], commit_message: str, stats: Dict[str, int]
    ) -> List[ManagementInsight]:
        """Extract strategic insights for managers"""
        insights = []

        # Test coverage insight
        test_files = [f for f in changed_files if "test" in f.lower()]
        impl_files = [f for f in changed_files if "test" not in f.lower() and f.endswith((".py", ".ts", ".js"))]

        if test_files:
            test_ratio = len(test_files) / max(len(impl_files), 1)
            insights.append(
                ManagementInsight(
                    title="Test Coverage Investment",
                    description=f"Added or modified {len(test_files)} test file(s) alongside {len(impl_files)} "
                    f"implementation file(s). Test-to-implementation ratio: {test_ratio:.1f}. "
                    f"This proactive testing reduces regression risk and future debugging time.",
                    impact_area="quality",
                    roi_estimate="Testing typically reduces bug-fixing costs by 10-25x compared to production fixes",
                    metrics={
                        "test_files_changed": str(len(test_files)),
                        "impl_files_changed": str(len(impl_files)),
                        "test_ratio": f"{test_ratio:.2f}",
                    },
                )
            )

        # Refactoring insight
        refactor_keywords = ["refactor", "cleanup", "reorganize", "restructure", "simplify"]
        if any(kw in commit_message.lower() for kw in refactor_keywords):
            insights.append(
                ManagementInsight(
                    title="Technical Debt Reduction",
                    description="This refactoring work improves code maintainability and reduces future development costs. "
                    "Clean code is easier to understand, modify, and debug, accelerating future feature delivery.",
                    impact_area="maintainability",
                    roi_estimate="15-25% faster future modifications in affected areas",
                    metrics={"lines_changed": str(stats.get("insertions", 0) + stats.get("deletions", 0))},
                )
            )

        # Security insight
        security_patterns = ["security", "auth", "sanitize", "validate", "permission", "encrypt"]
        security_files = [f for f in changed_files if any(kw in f.lower() for kw in security_patterns)]
        if security_files or any(kw in diff_content.lower() for kw in security_patterns):
            insights.append(
                ManagementInsight(
                    title="Security Hardening",
                    description="Security-related changes strengthen the application's defense posture. "
                    "Proactive security measures are significantly cheaper than incident response.",
                    impact_area="security",
                    roi_estimate="Security incidents cost average $4.35M (IBM 2023). Prevention is ~100x cheaper.",
                    metrics={"security_files": str(len(security_files))},
                )
            )

        # Performance insight
        perf_patterns = ["cache", "async", "performance", "optimize", "parallel"]
        if any(kw in diff_content.lower() for kw in perf_patterns):
            insights.append(
                ManagementInsight(
                    title="Performance Optimization",
                    description="Performance improvements enhance user experience and reduce infrastructure costs. "
                    "Faster applications have higher user engagement and lower bounce rates.",
                    impact_area="performance",
                    roi_estimate="1 second delay reduces conversions by 7% (Akamai). Infrastructure savings from efficiency.",
                    metrics={"files_optimized": str(stats.get("files", len(changed_files)))},
                )
            )

        # Large change insight
        total_lines = stats.get("insertions", 0) + stats.get("deletions", 0)
        if total_lines > 200:
            insights.append(
                ManagementInsight(
                    title="Significant Code Change",
                    description=(
                        f"This commit involves {total_lines} lines across "
                        f"{stats.get('files', len(changed_files))} files. "
                        f"Large changes warrant additional review attention and testing focus."
                    ),
                    impact_area="risk",
                    metrics={
                        "total_lines": str(total_lines),
                        "insertions": str(stats.get("insertions", 0)),
                        "deletions": str(stats.get("deletions", 0)),
                    },
                )
            )

        return insights

    def _extract_technical_debt(self, diff_content: str, changed_files: List[str]) -> List[TechnicalDebtItem]:
        """Extract technical debt items from diff"""
        debt_items = []

        # Extract TODOs from diff
        todos = self.todo_extractor.extract_from_diff(diff_content)

        severity_map = {"todo": "medium", "fixme": "high", "hack": "high", "xxx": "critical", "note": "low"}

        for todo in todos:
            debt_items.append(
                TechnicalDebtItem(
                    location="diff (new)",
                    debt_type="intentional" if todo["type"] in ["todo", "note"] else "unintentional",
                    description=todo["content"],
                    severity=severity_map.get(todo["type"], "medium"),
                    related_todo=todo["content"][:100],
                    remediation_estimate="1-4 hours depending on complexity",
                )
            )

        # Detect hardcoded values
        hardcoded_patterns = [
            (r'=\s*["\'][^"\']{30,}["\']', "Long hardcoded string - consider configuration", "low"),
            (r"=\s*\d{5,}", "Large hardcoded numeric constant", "low"),
            (r"localhost|127\.0\.0\.1", "Hardcoded localhost reference", "medium"),
            (r':\d{4,5}[\'"]', "Hardcoded port number", "low"),
        ]

        for pattern, description, severity in hardcoded_patterns:
            if re.search(pattern, diff_content):
                debt_items.append(
                    TechnicalDebtItem(
                        location="diff",
                        debt_type="unintentional",
                        description=description,
                        severity=severity,
                        remediation_estimate="Extract to configuration file or environment variable",
                    )
                )

        # Check for skipped tests
        if "skip" in diff_content.lower() or "@pytest.mark.skip" in diff_content:
            debt_items.append(
                TechnicalDebtItem(
                    location="test files",
                    debt_type="intentional",
                    description="Skipped tests detected - ensure these are addressed before release",
                    severity="medium",
                    remediation_estimate="Fix underlying issues or remove obsolete tests",
                )
            )

        # Check for complexity indicators
        if diff_content.count("    " * 5) > 3:  # Deep nesting
            debt_items.append(
                TechnicalDebtItem(
                    location="diff",
                    debt_type="unintentional",
                    description="Deep nesting detected (5+ levels) - consider extracting functions",
                    severity="medium",
                    remediation_estimate="Refactor to reduce cyclomatic complexity",
                )
            )

        return debt_items

    def _extract_ai_synergy(self, commit_message: str, diff_content: str) -> List[AISynergyItem]:
        """Extract AI collaboration effectiveness patterns"""
        synergy_items = []
        combined_text = f"{commit_message}\n{diff_content}".lower()

        # Detect AI tool mentions
        ai_tools = {
            "claude": {
                "name": "Claude Code",
                "pattern": "Code generation, review, and refactoring assistance",
                "effectiveness": "high",
            },
            "copilot": {
                "name": "GitHub Copilot",
                "pattern": "Inline code completion and suggestion",
                "effectiveness": "medium",
            },
            "gpt": {"name": "GPT/ChatGPT", "pattern": "Problem solving and code explanation", "effectiveness": "medium"},
            "generated": {"name": "AI Generated Code", "pattern": "Automated code generation", "effectiveness": "medium"},
            "co-authored-by": {
                "name": "AI Co-Author",
                "pattern": "Collaborative development with AI assistance",
                "effectiveness": "high",
            },
            "codex": {"name": "OpenAI Codex", "pattern": "Code analysis and automated editing", "effectiveness": "high"},
        }

        for keyword, tool_info in ai_tools.items():
            if keyword in combined_text:
                synergy_items.append(
                    AISynergyItem(
                        tool_name=tool_info["name"],
                        usage_pattern=tool_info["pattern"],
                        effectiveness=tool_info["effectiveness"],
                        time_saved_estimate="30-60% time reduction for routine tasks",
                    )
                )
                break  # Usually one primary AI tool per commit

        # Check for automated patterns
        if "auto-generated" in combined_text or "automatically generated" in combined_text:
            synergy_items.append(
                AISynergyItem(
                    tool_name="Automation Tools",
                    usage_pattern="Code generation from templates or specifications",
                    effectiveness="high",
                    time_saved_estimate="Hours of manual coding saved",
                )
            )

        return synergy_items

    def _calculate_quality_score(self, result: ExtractionResult) -> int:
        """Calculate quality score for extraction result (0-100)"""
        score = 0

        # Base points for each category (max 20 each = 100 total)
        if result.beginner_concepts:
            # More concepts with detailed explanations = higher score
            concept_score = 0
            for c in result.beginner_concepts:
                concept_score += 3  # Base for having concept
                if c.code_example:
                    concept_score += 2
                if len(c.explanation) > 100:
                    concept_score += 2
            score += min(concept_score, 20)

        if result.management_insights:
            insight_score = 0
            for i in result.management_insights:
                insight_score += 4  # Base
                if i.roi_estimate:
                    insight_score += 2
                if i.metrics:
                    insight_score += 2
            score += min(insight_score, 20)

        if result.technical_debt:
            # Having debt tracking is good, too much debt is concerning
            debt_count = len(result.technical_debt)
            if 1 <= debt_count <= 3:
                score += 15
            elif 4 <= debt_count <= 6:
                score += 10
            elif debt_count > 6:
                score += 5
            else:
                score += 5  # No debt detected might mean we're not looking hard enough

        if result.patterns:
            pattern_score = min(len(result.patterns) * 4, 20)
            # Reduce score for anti-patterns
            anti_pattern_count = sum(1 for p in result.patterns if p.anti_pattern)
            pattern_score -= anti_pattern_count * 3
            score += max(pattern_score, 0)

        if result.ai_synergy:
            score += min(len(result.ai_synergy) * 10, 20)

        return min(score, 100)

    def to_markdown(self, result: ExtractionResult) -> str:
        """Convert extraction result to markdown format"""
        lines = []

        lines.append(f"# Knowledge Extraction: {result.task_title}")
        lines.append(f"\n**Task ID**: {result.task_id}")
        lines.append(f"**Extracted**: {result.extraction_timestamp.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**Quality Score**: {result.quality_score}/100")
        lines.append(f"**Files Analyzed**: {result.files_analyzed}")
        lines.append(f"**Lines Changed**: {result.lines_changed}")

        # Beginner Concepts
        if result.beginner_concepts:
            lines.append("\n---\n\n## Beginner Concepts\n")
            for concept in result.beginner_concepts:
                lines.append(f"### {concept.title} [{concept.difficulty.value}]")
                lines.append(f"\n{concept.explanation}\n")
                if concept.code_example:
                    lines.append(f"```python\n{concept.code_example}\n```\n")
                if concept.tags:
                    lines.append(f"**Tags**: {', '.join(concept.tags)}\n")
                if concept.related_files:
                    lines.append(f"**Files**: {', '.join(concept.related_files[:3])}\n")

        # Management Insights
        if result.management_insights:
            lines.append("\n---\n\n## Management Insights\n")
            for insight in result.management_insights:
                lines.append(f"### {insight.title}")
                lines.append(f"\n{insight.description}\n")
                lines.append(f"**Impact Area**: {insight.impact_area}")
                if insight.roi_estimate:
                    lines.append(f"\n**ROI Estimate**: {insight.roi_estimate}")
                if insight.metrics:
                    metrics_str = ", ".join(f"{k}: {v}" for k, v in insight.metrics.items())
                    lines.append(f"\n**Metrics**: {metrics_str}")
                lines.append("")

        # Technical Debt
        if result.technical_debt:
            lines.append("\n---\n\n## Technical Debt\n")
            lines.append("| Severity | Type | Description | Remediation |")
            lines.append("|----------|------|-------------|-------------|")
            for debt in result.technical_debt:
                remediation = debt.remediation_estimate or "TBD"
                lines.append(
                    f"| {debt.severity.upper()} | {debt.debt_type} | {debt.description[:50]}... | {remediation[:30]}... |"
                )

        # Patterns
        if result.patterns:
            lines.append("\n---\n\n## Patterns Detected\n")
            success_patterns = [p for p in result.patterns if not p.anti_pattern]
            anti_patterns = [p for p in result.patterns if p.anti_pattern]

            if success_patterns:
                lines.append("### Success Patterns\n")
                for pattern in success_patterns:
                    lines.append(f"- **{pattern.name}** ({pattern.context}): {pattern.description}")

            if anti_patterns:
                lines.append("\n### Anti-Patterns Detected\n")
                for pattern in anti_patterns:
                    lines.append(f"- **{pattern.name}**: {pattern.description}")

        # AI Synergy
        if result.ai_synergy:
            lines.append("\n---\n\n## AI Collaboration\n")
            for synergy in result.ai_synergy:
                lines.append(f"### {synergy.tool_name}")
                lines.append(f"\n**Usage Pattern**: {synergy.usage_pattern}")
                lines.append(f"\n**Effectiveness**: {synergy.effectiveness}")
                if synergy.time_saved_estimate:
                    lines.append(f"\n**Time Saved**: {synergy.time_saved_estimate}")

        lines.append(f"\n---\n\n*Extraction completed in {result.extraction_duration_ms:.1f}ms*")

        return "\n".join(lines)

    def to_dict(self, result: ExtractionResult) -> Dict[str, Any]:
        """Convert extraction result to dictionary format"""
        return {
            "task_id": result.task_id,
            "task_title": result.task_title,
            "extraction_timestamp": result.extraction_timestamp.isoformat(),
            "quality_score": result.quality_score,
            "files_analyzed": result.files_analyzed,
            "lines_changed": result.lines_changed,
            "extraction_duration_ms": result.extraction_duration_ms,
            "beginner_concepts": [
                {
                    "title": c.title,
                    "explanation": c.explanation,
                    "difficulty": c.difficulty.value,
                    "code_example": c.code_example,
                    "related_files": c.related_files,
                    "tags": c.tags,
                }
                for c in result.beginner_concepts
            ],
            "management_insights": [
                {
                    "title": i.title,
                    "description": i.description,
                    "impact_area": i.impact_area,
                    "roi_estimate": i.roi_estimate,
                    "metrics": i.metrics,
                }
                for i in result.management_insights
            ],
            "technical_debt": [
                {
                    "location": d.location,
                    "debt_type": d.debt_type,
                    "description": d.description,
                    "severity": d.severity,
                    "remediation_estimate": d.remediation_estimate,
                    "related_todo": d.related_todo,
                }
                for d in result.technical_debt
            ],
            "patterns": [
                {
                    "pattern_type": p.pattern_type,
                    "name": p.name,
                    "description": p.description,
                    "context": p.context,
                    "anti_pattern": p.anti_pattern,
                }
                for p in result.patterns
            ],
            "ai_synergy": [
                {
                    "tool_name": s.tool_name,
                    "usage_pattern": s.usage_pattern,
                    "effectiveness": s.effectiveness,
                    "time_saved_estimate": s.time_saved_estimate,
                }
                for s in result.ai_synergy
            ],
        }


# =============================================================================
# CLI Entry Point
# =============================================================================


def main():
    """CLI entry point for knowledge asset extraction"""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Extract knowledge assets from git commits",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python knowledge_asset_extractor.py --commit HEAD
  python knowledge_asset_extractor.py --commit abc123 --output result.md
  python knowledge_asset_extractor.py --json --output result.json
        """,
    )
    parser.add_argument("--commit", "-c", default="HEAD", help="Commit hash to analyze (default: HEAD)")
    parser.add_argument("--task-id", help="Task ID for tracking")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of markdown")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing files")
    parser.add_argument("--no-secrets-redaction", action="store_true", help="Disable secrets redaction")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Initialize extractor
    extractor = KnowledgeAssetExtractor(enable_secrets_redaction=not args.no_secrets_redaction)

    # Run extraction
    logger.info(f"Extracting knowledge from commit: {args.commit}")
    result = extractor.extract_from_commit(commit_hash=args.commit, task_id=args.task_id)

    # Generate output
    if args.json:
        output = json.dumps(extractor.to_dict(result), indent=2, ensure_ascii=False)
    else:
        output = extractor.to_markdown(result)

    # Output handling
    if args.dry_run:
        print(output)
        print("\n--- Dry Run Complete ---")
        print(f"Quality Score: {result.quality_score}/100")
        print(f"Extraction Time: {result.extraction_duration_ms:.1f}ms")
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Written to {args.output}")
        print(f"Quality Score: {result.quality_score}/100")
    else:
        print(output)

    return result.quality_score


if __name__ == "__main__":
    exit(0 if main() >= 50 else 1)
