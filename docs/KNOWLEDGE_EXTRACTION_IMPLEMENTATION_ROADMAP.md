# Knowledge Extraction System - Definitive Implementation Roadmap

**Document Version**: 1.0.0
**Date**: 2025-12-28
**Author**: Backend Architect
**Status**: FINAL BLUEPRINT - Ready for Execution

---

## Executive Summary

This document provides the complete, executable implementation plan for the Knowledge Extraction System enhancement. The goal is to transform the current ~500 character output with 5 basic sections into a rich ~15,000 character output with 5 comprehensive categories, achieving commercial-grade quality (20/80 to 63/80 benchmark).

### Current State Analysis

| Component | Status | Gap |
|-----------|--------|-----|
| `scripts/knowledge_asset_extractor.py` | **Does not exist** | Critical - root cause |
| `kanban_archive_service.py` | Exists (818 lines) | Mock summaries only ~500 chars |
| `secrets_redactor.py` | Exists (831 lines) | Ready for integration |
| `log_sanitizer.py` | Exists (326 lines) | Ready for integration |
| Quality Gates | Referenced in models | Not implemented |

### Target Architecture

```
Git Commit / Task Archive
         |
         v
+------------------------+
| KnowledgeAssetExtractor|  <-- NEW (scripts/)
|  - Git diff analysis   |
|  - TODO extraction     |
|  - Pattern detection   |
|  - 5-category output   |
+------------------------+
         |
         v
+------------------------+
| KnowledgeQualityService|  <-- NEW (backend/services/)
|  - Quality gates       |
|  - Scoring algorithms  |
|  - Validation          |
+------------------------+
         |
         v
+------------------------+
| KanbanArchiveService   |  <-- MODIFY
|  - Enhanced prompts    |
|  - Integration calls   |
|  - Quality checkpoints |
+------------------------+
         |
         v
+------------------------+
| SecurityValidators     |  <-- NEW (backend/core/)
|  - SecurePathValidator |
|  - SecretsRedactor use |
|  - Test isolation      |
+------------------------+
```

---

## Week 1: Foundation Layer (Days 1-5)

### Day 1: Knowledge Asset Extractor Core (8 hours)

**File**: `scripts/knowledge_asset_extractor.py`
**Effort**: 8 hours
**Dependencies**: None
**Risk**: Medium - Complex pattern matching

#### Tasks

1. **Create base class structure** (2h)
2. **Implement Git diff analyzer** (2h)
3. **Implement TODO/FIXME extractor** (2h)
4. **Unit tests for core functions** (2h)

#### Code Skeleton

```python
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
"""

import logging
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


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
                timeout=30
            )
            return result.stdout
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
                timeout=30
            )
            return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
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
                timeout=10
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to get commit message: {e}")
            return ""


class TodoExtractor:
    """Extracts TODO, FIXME, HACK, XXX comments from code"""

    # Patterns for different comment types
    PATTERNS = {
        'todo': re.compile(r'#\s*TODO[:\s]*(.+?)(?:\n|$)', re.IGNORECASE),
        'fixme': re.compile(r'#\s*FIXME[:\s]*(.+?)(?:\n|$)', re.IGNORECASE),
        'hack': re.compile(r'#\s*HACK[:\s]*(.+?)(?:\n|$)', re.IGNORECASE),
        'xxx': re.compile(r'#\s*XXX[:\s]*(.+?)(?:\n|$)', re.IGNORECASE),
        'note': re.compile(r'#\s*NOTE[:\s]*(.+?)(?:\n|$)', re.IGNORECASE),
    }

    # JS/TS patterns
    JS_PATTERNS = {
        'todo': re.compile(r'//\s*TODO[:\s]*(.+?)(?:\n|$)', re.IGNORECASE),
        'fixme': re.compile(r'//\s*FIXME[:\s]*(.+?)(?:\n|$)', re.IGNORECASE),
    }

    def extract_from_content(self, content: str, file_type: str = "py") -> List[Dict]:
        """Extract TODO-style comments from content"""
        results = []
        patterns = self.PATTERNS if file_type == "py" else self.JS_PATTERNS

        for comment_type, pattern in patterns.items():
            for match in pattern.finditer(content):
                results.append({
                    'type': comment_type,
                    'content': match.group(1).strip(),
                    'position': match.start()
                })

        return results

    def extract_from_diff(self, diff_content: str) -> List[Dict]:
        """Extract TODOs from added lines in a diff"""
        results = []

        for line in diff_content.split('\n'):
            if line.startswith('+') and not line.startswith('+++'):
                # Check both Python and JS patterns
                for patterns in [self.PATTERNS, self.JS_PATTERNS]:
                    for comment_type, pattern in patterns.items():
                        match = pattern.search(line[1:])  # Skip the '+' prefix
                        if match:
                            results.append({
                                'type': comment_type,
                                'content': match.group(1).strip(),
                                'line': line[1:]
                            })

        return results


class PatternDetector:
    """Detects coding patterns from git diffs"""

    # Pattern signatures to detect
    PATTERN_SIGNATURES = {
        'tdd': {
            'indicators': ['test_', '_test.py', '.spec.', 'pytest', 'unittest'],
            'category': 'testing',
            'insight': 'TDD approach - tests written alongside implementation'
        },
        'error_handling': {
            'indicators': ['try:', 'except', 'raise', 'catch', 'throw'],
            'category': 'reliability',
            'insight': 'Robust error handling implementation'
        },
        'type_hints': {
            'indicators': ['def .+\\(.+:.+\\)', '-> ', 'Optional[', 'List[', 'Dict['],
            'category': 'quality',
            'insight': 'Type safety through type hints'
        },
        'refactoring': {
            'indicators': ['refactor', 'cleanup', 'extract', 'simplify'],
            'category': 'maintainability',
            'insight': 'Code structure improvement'
        },
        'security': {
            'indicators': ['sanitize', 'validate', 'escape', 'hash', 'encrypt'],
            'category': 'security',
            'insight': 'Security-focused implementation'
        },
        'performance': {
            'indicators': ['cache', 'async', 'await', 'concurrent', 'parallel'],
            'category': 'performance',
            'insight': 'Performance optimization applied'
        }
    }

    def detect_patterns(self, diff_content: str, commit_message: str) -> List[PatternItem]:
        """Detect patterns from diff and commit message"""
        detected = []
        combined_text = f"{commit_message}\n{diff_content}".lower()

        for pattern_name, config in self.PATTERN_SIGNATURES.items():
            for indicator in config['indicators']:
                if re.search(indicator, combined_text, re.IGNORECASE):
                    detected.append(PatternItem(
                        pattern_type='success',
                        name=pattern_name.replace('_', ' ').title(),
                        description=config['insight'],
                        context=config['category'],
                        anti_pattern=False
                    ))
                    break  # One match per pattern type is enough

        return detected


class KnowledgeAssetExtractor:
    """Main extraction engine for knowledge assets"""

    def __init__(
        self,
        repo_path: Optional[Path] = None,
        enable_git: bool = True,
        enable_secrets_redaction: bool = True
    ):
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
            except ImportError:
                logger.warning("SecretsRedactor not available, skipping secrets redaction")

    def _redact_secrets(self, content: str) -> str:
        """Redact secrets from content if enabled"""
        if self._secrets_redactor:
            redacted, _ = self._secrets_redactor.redact(content)
            return redacted
        return content

    def extract_from_commit(
        self,
        commit_hash: str = "HEAD",
        task_id: Optional[str] = None,
        task_title: Optional[str] = None
    ) -> ExtractionResult:
        """Extract knowledge assets from a git commit"""
        import time
        start_time = time.time()

        # Get commit data
        diff_content = ""
        commit_message = ""
        changed_files = []

        if self.git_analyzer:
            diff_content = self.git_analyzer.get_diff(commit_hash)
            commit_message = self.git_analyzer.get_commit_message(commit_hash)
            changed_files = self.git_analyzer.get_changed_files(commit_hash)

            # Redact secrets from diff
            diff_content = self._redact_secrets(diff_content)

        # Initialize result
        result = ExtractionResult(
            task_id=task_id or commit_hash[:8],
            task_title=task_title or commit_message.split('\n')[0][:80],
            extraction_timestamp=datetime.utcnow(),
            files_analyzed=len(changed_files),
            lines_changed=diff_content.count('\n+') + diff_content.count('\n-')
        )

        # Extract 5 categories
        result.beginner_concepts = self._extract_beginner_concepts(
            diff_content, changed_files, commit_message
        )
        result.management_insights = self._extract_management_insights(
            diff_content, changed_files, commit_message
        )
        result.technical_debt = self._extract_technical_debt(diff_content)
        result.patterns = self.pattern_detector.detect_patterns(diff_content, commit_message)
        result.ai_synergy = self._extract_ai_synergy(commit_message)

        result.extraction_duration_ms = (time.time() - start_time) * 1000
        result.quality_score = self._calculate_quality_score(result)

        return result

    def _extract_beginner_concepts(
        self,
        diff_content: str,
        changed_files: List[str],
        commit_message: str
    ) -> List[BeginnerConcept]:
        """Extract learning concepts for beginners"""
        concepts = []

        # Detect function extraction pattern
        if 'def ' in diff_content and len(changed_files) > 0:
            concepts.append(BeginnerConcept(
                title="Function Decomposition",
                explanation="Breaking down complex logic into smaller, reusable functions improves code readability and testability.",
                difficulty=Difficulty.EASY,
                related_files=changed_files[:3],
                tags=["refactoring", "clean-code"]
            ))

        # Detect error handling
        if 'try:' in diff_content or 'except' in diff_content:
            concepts.append(BeginnerConcept(
                title="Error Handling Pattern",
                explanation="Using try-except blocks to gracefully handle exceptions prevents application crashes and improves user experience.",
                difficulty=Difficulty.MEDIUM,
                tags=["error-handling", "reliability"]
            ))

        # Detect type hints
        if '->' in diff_content or 'Optional[' in diff_content:
            concepts.append(BeginnerConcept(
                title="Type Hints for Safety",
                explanation="Adding type hints helps catch bugs early and makes code self-documenting for other developers.",
                difficulty=Difficulty.MEDIUM,
                tags=["type-safety", "documentation"]
            ))

        # Detect test patterns
        if 'test_' in diff_content or 'pytest' in diff_content.lower():
            concepts.append(BeginnerConcept(
                title="Test-Driven Development",
                explanation="Writing tests alongside code ensures functionality works as expected and prevents regressions.",
                difficulty=Difficulty.MEDIUM,
                tags=["testing", "tdd"]
            ))

        return concepts

    def _extract_management_insights(
        self,
        diff_content: str,
        changed_files: List[str],
        commit_message: str
    ) -> List[ManagementInsight]:
        """Extract strategic insights for managers"""
        insights = []

        # Test coverage insight
        test_files = [f for f in changed_files if 'test' in f.lower()]
        if test_files:
            insights.append(ManagementInsight(
                title="Test Coverage Investment",
                description=f"Added/modified {len(test_files)} test file(s), improving regression safety.",
                impact_area="testing",
                metrics={"test_files_changed": str(len(test_files))}
            ))

        # Refactoring insight
        if 'refactor' in commit_message.lower():
            insights.append(ManagementInsight(
                title="Technical Debt Reduction",
                description="Refactoring work improves maintainability and reduces future development costs.",
                impact_area="maintainability",
                roi_estimate="15-25% faster future modifications"
            ))

        # Security insight
        security_files = [f for f in changed_files if any(
            kw in f.lower() for kw in ['security', 'auth', 'sanitize', 'validate']
        )]
        if security_files:
            insights.append(ManagementInsight(
                title="Security Hardening",
                description="Security-related changes reduce vulnerability exposure.",
                impact_area="security",
                metrics={"security_files": str(len(security_files))}
            ))

        return insights

    def _extract_technical_debt(self, diff_content: str) -> List[TechnicalDebtItem]:
        """Extract technical debt items from diff"""
        debt_items = []

        # Extract TODOs from diff
        todos = self.todo_extractor.extract_from_diff(diff_content)

        for todo in todos:
            severity = "medium"
            if todo['type'] == 'fixme':
                severity = "high"
            elif todo['type'] == 'hack':
                severity = "high"
            elif todo['type'] == 'xxx':
                severity = "critical"

            debt_items.append(TechnicalDebtItem(
                location="diff",
                debt_type="intentional" if todo['type'] == 'todo' else "unintentional",
                description=todo['content'],
                severity=severity,
                related_todo=todo['content']
            ))

        # Detect hardcoded values
        hardcoded_patterns = [
            (r'=\s*["\'][^"\']{20,}["\']', "Hardcoded string value"),
            (r'=\s*\d{4,}', "Hardcoded numeric constant"),
            (r'localhost|127\.0\.0\.1', "Hardcoded localhost reference"),
        ]

        for pattern, description in hardcoded_patterns:
            if re.search(pattern, diff_content):
                debt_items.append(TechnicalDebtItem(
                    location="diff",
                    debt_type="unintentional",
                    description=description,
                    severity="low",
                    remediation_estimate="Extract to configuration"
                ))

        return debt_items

    def _extract_ai_synergy(self, commit_message: str) -> List[AISynergyItem]:
        """Extract AI collaboration effectiveness patterns"""
        synergy_items = []

        # Detect AI tool mentions
        ai_tools = {
            'claude': 'Claude Code',
            'copilot': 'GitHub Copilot',
            'gpt': 'GPT',
            'generated': 'AI Generated',
            'co-authored-by': 'AI Co-Author'
        }

        for keyword, tool_name in ai_tools.items():
            if keyword.lower() in commit_message.lower():
                synergy_items.append(AISynergyItem(
                    tool_name=tool_name,
                    usage_pattern="Code generation/review assistance",
                    effectiveness="high"
                ))
                break

        return synergy_items

    def _calculate_quality_score(self, result: ExtractionResult) -> int:
        """Calculate quality score for extraction result"""
        score = 0

        # Base points for each category (max 20 each = 100 total)
        if result.beginner_concepts:
            score += min(len(result.beginner_concepts) * 5, 20)

        if result.management_insights:
            score += min(len(result.management_insights) * 7, 20)

        if result.technical_debt:
            score += min(len(result.technical_debt) * 4, 20)

        if result.patterns:
            score += min(len(result.patterns) * 5, 20)

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
            lines.append("\n## Beginner Concepts\n")
            for concept in result.beginner_concepts:
                lines.append(f"### {concept.title} ({concept.difficulty.value})")
                lines.append(f"\n{concept.explanation}\n")
                if concept.tags:
                    lines.append(f"**Tags**: {', '.join(concept.tags)}\n")

        # Management Insights
        if result.management_insights:
            lines.append("\n## Management Insights\n")
            for insight in result.management_insights:
                lines.append(f"### {insight.title}")
                lines.append(f"\n{insight.description}\n")
                lines.append(f"**Impact Area**: {insight.impact_area}")
                if insight.roi_estimate:
                    lines.append(f"**ROI Estimate**: {insight.roi_estimate}")

        # Technical Debt
        if result.technical_debt:
            lines.append("\n## Technical Debt\n")
            for debt in result.technical_debt:
                lines.append(f"- **[{debt.severity.upper()}]** {debt.description}")
                if debt.remediation_estimate:
                    lines.append(f"  - Remediation: {debt.remediation_estimate}")

        # Patterns
        if result.patterns:
            lines.append("\n## Patterns Detected\n")
            for pattern in result.patterns:
                icon = "!" if pattern.anti_pattern else "+"
                lines.append(f"- [{icon}] **{pattern.name}**: {pattern.description}")

        # AI Synergy
        if result.ai_synergy:
            lines.append("\n## AI Collaboration\n")
            for synergy in result.ai_synergy:
                lines.append(f"- **{synergy.tool_name}**: {synergy.usage_pattern} ({synergy.effectiveness})")

        lines.append(f"\n---\n*Extraction completed in {result.extraction_duration_ms:.1f}ms*")

        return '\n'.join(lines)


# CLI Entry Point
if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Extract knowledge assets from git commits")
    parser.add_argument("--commit", "-c", default="HEAD", help="Commit hash to analyze")
    parser.add_argument("--task-id", help="Task ID for tracking")
    parser.add_argument("--output", "-o", help="Output file path (markdown)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")

    args = parser.parse_args()

    extractor = KnowledgeAssetExtractor()
    result = extractor.extract_from_commit(
        commit_hash=args.commit,
        task_id=args.task_id
    )

    if args.json:
        import json
        from dataclasses import asdict

        # Convert to dict (handling datetime and enums)
        def serialize(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Enum):
                return obj.value
            if hasattr(obj, '__dict__'):
                return {k: serialize(v) for k, v in obj.__dict__.items()}
            if isinstance(obj, list):
                return [serialize(i) for i in obj]
            if isinstance(obj, dict):
                return {k: serialize(v) for k, v in obj.items()}
            return obj

        output = json.dumps(serialize(result), indent=2)
    else:
        output = extractor.to_markdown(result)

    if args.dry_run:
        print(output)
    elif args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Written to {args.output}")
    else:
        print(output)
```

#### Success Criteria
- [ ] `knowledge_asset_extractor.py` created (500+ lines)
- [ ] Git diff analysis working
- [ ] TODO extraction working
- [ ] CLI entry point functional
- [ ] Unit tests passing (8+ tests)

#### Risk Mitigation
- Use subprocess timeout (30s) for git commands
- Graceful degradation if git not available
- Mock data for testing without real repository

---

### Day 2: Pattern Detection and Category Logic (6 hours)

**File**: `scripts/knowledge_asset_extractor.py` (continued)
**Effort**: 6 hours
**Dependencies**: Day 1 completion
**Risk**: Medium - Pattern accuracy

#### Tasks

1. **Enhanced pattern detection** (2h)
   - Add 15+ pattern signatures
   - Improve accuracy with context

2. **5-category extraction logic** (3h)
   - Complete all 5 categories
   - Add weighting algorithms

3. **Quality scoring refinement** (1h)

#### Additional Pattern Signatures

```python
# Add to PatternDetector class
ADVANCED_PATTERNS = {
    'dependency_injection': {
        'indicators': ['inject', 'provider', 'container', 'Depends('],
        'category': 'architecture',
        'insight': 'Dependency injection for loose coupling'
    },
    'caching': {
        'indicators': ['@cache', 'redis', 'memcache', 'lru_cache'],
        'category': 'performance',
        'insight': 'Caching strategy for performance optimization'
    },
    'logging': {
        'indicators': ['logger.', 'logging.', 'log.info', 'log.error'],
        'category': 'observability',
        'insight': 'Structured logging for debugging and monitoring'
    },
    'validation': {
        'indicators': ['pydantic', 'validator', 'validate', 'Field('],
        'category': 'reliability',
        'insight': 'Input validation for data integrity'
    },
    'async_pattern': {
        'indicators': ['async def', 'await ', 'asyncio', 'aiohttp'],
        'category': 'performance',
        'insight': 'Asynchronous programming for I/O efficiency'
    },
    'circuit_breaker': {
        'indicators': ['circuit', 'breaker', 'fallback', 'retry'],
        'category': 'reliability',
        'insight': 'Resilience pattern for fault tolerance'
    },
    'rate_limiting': {
        'indicators': ['rate_limit', 'throttle', 'slowapi', 'RateLimiter'],
        'category': 'security',
        'insight': 'Rate limiting for abuse prevention'
    },
    'solid_srp': {
        'indicators': ['single responsibility', 'one reason to change'],
        'category': 'architecture',
        'insight': 'Single Responsibility Principle applied'
    },
    'documentation': {
        'indicators': ['"""', "'''", 'docstring', '@param', '@return'],
        'category': 'maintainability',
        'insight': 'Inline documentation for code clarity'
    },
    'feature_flag': {
        'indicators': ['feature_flag', 'toggle', 'is_enabled', 'feature_'],
        'category': 'operations',
        'insight': 'Feature flags for safe deployments'
    }
}
```

#### Success Criteria
- [ ] 20+ pattern signatures defined
- [ ] All 5 categories producing meaningful output
- [ ] Quality score accurately reflects extraction quality
- [ ] Pattern detection accuracy >80%

---

### Day 3: Security Validators Module (6 hours)

**File**: `backend/app/core/security_validators.py`
**Effort**: 6 hours
**Dependencies**: SecretsRedactor (exists)
**Risk**: Low - Building on existing code

#### Tasks

1. **SecurePathValidator implementation** (2h)
2. **SecretsRedactor integration wrapper** (2h)
3. **Test environment detection** (1h)
4. **Unit tests** (1h)

#### Code Implementation

```python
#!/usr/bin/env python3
"""
Security Validators - Path Validation and Secrets Protection

Provides secure path validation and secrets redaction for
knowledge extraction operations.

Author: UDO Platform Team
Date: 2025-12-28
"""

import logging
import os
import re
from pathlib import Path
from typing import List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class SecurityValidationError(Exception):
    """Base exception for security validation failures"""
    pass


class PathTraversalError(SecurityValidationError):
    """Raised when path traversal attack is detected"""
    pass


class SecurePathValidator:
    """
    Validates file paths to prevent directory traversal attacks
    and ensure operations stay within allowed boundaries.
    """

    # Dangerous path components
    DANGEROUS_PATTERNS = [
        '..',           # Parent directory traversal
        '~',            # Home directory expansion
        '/etc/',        # System config (Unix)
        '/root/',       # Root home (Unix)
        'C:\\Windows',  # Windows system
        '%SYSTEMROOT%', # Windows env var
        '%USERPROFILE%',# Windows user profile
    ]

    # Allowed file extensions for reading
    SAFE_EXTENSIONS = {
        '.py', '.js', '.ts', '.tsx', '.jsx',
        '.md', '.txt', '.json', '.yaml', '.yml',
        '.html', '.css', '.sql', '.sh', '.bat',
        '.env.example', '.gitignore', '.dockerignore'
    }

    # Never read these files
    FORBIDDEN_FILES = {
        '.env', '.env.local', '.env.production',
        'credentials.json', 'secrets.yaml',
        'id_rsa', 'id_ed25519', 'private.key',
        '.npmrc', '.pypirc'  # Package manager auth
    }

    def __init__(
        self,
        base_path: Path,
        allowed_extensions: Optional[Set[str]] = None,
        forbidden_files: Optional[Set[str]] = None
    ):
        """
        Initialize validator with base path boundary.

        Args:
            base_path: Root directory that all paths must be within
            allowed_extensions: Override default safe extensions
            forbidden_files: Override default forbidden files
        """
        self.base_path = base_path.resolve()
        self.allowed_extensions = allowed_extensions or self.SAFE_EXTENSIONS
        self.forbidden_files = forbidden_files or self.FORBIDDEN_FILES

    def validate_path(self, path: str | Path) -> Path:
        """
        Validate a path is safe and within boundaries.

        Args:
            path: Path to validate (absolute or relative)

        Returns:
            Resolved, safe Path object

        Raises:
            PathTraversalError: If path traversal detected
            SecurityValidationError: If path validation fails
        """
        # Convert to Path if string
        if isinstance(path, str):
            path = Path(path)

        # Check for dangerous patterns in string representation
        path_str = str(path)
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in path_str:
                raise PathTraversalError(
                    f"Dangerous path pattern detected: '{pattern}' in '{path_str}'"
                )

        # Resolve to absolute path
        if path.is_absolute():
            resolved = path.resolve()
        else:
            resolved = (self.base_path / path).resolve()

        # Verify within base_path boundary
        try:
            resolved.relative_to(self.base_path)
        except ValueError:
            raise PathTraversalError(
                f"Path '{resolved}' is outside allowed boundary '{self.base_path}'"
            )

        return resolved

    def is_safe_to_read(self, path: str | Path) -> Tuple[bool, str]:
        """
        Check if a file is safe to read.

        Args:
            path: Path to check

        Returns:
            Tuple of (is_safe, reason)
        """
        try:
            validated_path = self.validate_path(path)
        except SecurityValidationError as e:
            return False, str(e)

        # Check file name against forbidden list
        file_name = validated_path.name.lower()
        for forbidden in self.forbidden_files:
            if forbidden.lower() in file_name:
                return False, f"File '{file_name}' is in forbidden list"

        # Check extension
        suffix = validated_path.suffix.lower()
        if suffix and suffix not in self.allowed_extensions:
            return False, f"Extension '{suffix}' is not in allowed list"

        return True, "OK"

    def safe_read(self, path: str | Path, max_size_kb: int = 1024) -> str:
        """
        Safely read a file with all validations.

        Args:
            path: Path to read
            max_size_kb: Maximum file size in KB

        Returns:
            File contents as string

        Raises:
            SecurityValidationError: If file fails validation
        """
        is_safe, reason = self.is_safe_to_read(path)
        if not is_safe:
            raise SecurityValidationError(f"Cannot read file: {reason}")

        validated_path = self.validate_path(path)

        # Check file size
        file_size = validated_path.stat().st_size
        if file_size > max_size_kb * 1024:
            raise SecurityValidationError(
                f"File size {file_size} bytes exceeds limit {max_size_kb}KB"
            )

        return validated_path.read_text(encoding='utf-8')


class TestEnvironmentDetector:
    """
    Detects if code is running in test/CI environment.
    Prevents real file operations during testing.
    """

    # Environment variables that indicate test/CI
    TEST_ENV_VARS = {
        'PYTEST_CURRENT_TEST',  # pytest sets this
        'CI',                    # Generic CI indicator
        'GITHUB_ACTIONS',        # GitHub Actions
        'GITLAB_CI',             # GitLab CI
        'JENKINS_URL',           # Jenkins
        'CIRCLECI',              # CircleCI
        'TRAVIS',                # Travis CI
        'TEST_MODE',             # Our custom flag
    }

    # Environment variable values that indicate testing
    TEST_ENV_VALUES = {
        'ENVIRONMENT': {'test', 'testing', 'ci', 'development'},
        'NODE_ENV': {'test'},
        'FLASK_ENV': {'testing'},
    }

    @classmethod
    def is_test_environment(cls) -> bool:
        """
        Check if running in test/CI environment.

        Returns:
            True if test environment detected
        """
        # Check for presence of test indicators
        for var in cls.TEST_ENV_VARS:
            if os.getenv(var):
                return True

        # Check for specific values
        for var, test_values in cls.TEST_ENV_VALUES.items():
            value = os.getenv(var, '').lower()
            if value in test_values:
                return True

        return False

    @classmethod
    def get_test_mode_reason(cls) -> Optional[str]:
        """
        Get the reason why test mode was detected.

        Returns:
            String explaining why test mode is active, or None
        """
        for var in cls.TEST_ENV_VARS:
            if os.getenv(var):
                return f"Environment variable {var} is set"

        for var, test_values in cls.TEST_ENV_VALUES.items():
            value = os.getenv(var, '').lower()
            if value in test_values:
                return f"{var}={value} indicates test environment"

        return None


class SecretsRedactorWrapper:
    """
    Wrapper around SecretsRedactor for knowledge extraction.
    Provides convenient methods and handles import failures.
    """

    def __init__(self, min_severity: str = "MEDIUM"):
        """
        Initialize wrapper.

        Args:
            min_severity: Minimum severity to redact (CRITICAL, HIGH, MEDIUM, LOW)
        """
        self._redactor = None
        self._available = False

        try:
            from backend.app.utils.secrets_redactor import (
                SecretsRedactor, SecretSeverity
            )

            severity_map = {
                "CRITICAL": SecretSeverity.CRITICAL,
                "HIGH": SecretSeverity.HIGH,
                "MEDIUM": SecretSeverity.MEDIUM,
                "LOW": SecretSeverity.LOW,
            }

            self._redactor = SecretsRedactor(
                min_severity=severity_map.get(min_severity, SecretSeverity.MEDIUM),
                log_findings=True
            )
            self._available = True
            logger.info("SecretsRedactor initialized successfully")

        except ImportError as e:
            logger.warning(f"SecretsRedactor not available: {e}")

    @property
    def available(self) -> bool:
        """Check if redactor is available"""
        return self._available

    def redact(self, content: str) -> Tuple[str, int]:
        """
        Redact secrets from content.

        Args:
            content: Text content to scan and redact

        Returns:
            Tuple of (redacted_content, secrets_found_count)
        """
        if not self._available:
            return content, 0

        redacted, findings = self._redactor.redact(content)
        return redacted, len(findings)

    def scan_only(self, content: str) -> int:
        """
        Scan for secrets without modifying content.

        Args:
            content: Text to scan

        Returns:
            Number of secrets found
        """
        if not self._available:
            return 0

        findings = self._redactor.scan(content)
        return len(findings)

    def redact_git_diff(self, diff_content: str) -> Tuple[str, int]:
        """
        Redact secrets from git diff output.

        Args:
            diff_content: Raw git diff output

        Returns:
            Tuple of (redacted_diff, secrets_found_count)
        """
        if not self._available:
            return diff_content, 0

        redacted, findings = self._redactor.redact_git_diff(
            diff_content,
            only_added_lines=True
        )
        return redacted, len(findings)


# Convenience functions
def is_test_environment() -> bool:
    """Check if running in test environment"""
    return TestEnvironmentDetector.is_test_environment()


def validate_path(path: str | Path, base_path: Path) -> Path:
    """Validate a path is safe"""
    validator = SecurePathValidator(base_path)
    return validator.validate_path(path)


def redact_secrets(content: str) -> str:
    """Redact secrets from content"""
    wrapper = SecretsRedactorWrapper()
    redacted, _ = wrapper.redact(content)
    return redacted


# Module exports
__all__ = [
    'SecurePathValidator',
    'TestEnvironmentDetector',
    'SecretsRedactorWrapper',
    'SecurityValidationError',
    'PathTraversalError',
    'is_test_environment',
    'validate_path',
    'redact_secrets',
]
```

#### Success Criteria
- [ ] `security_validators.py` created (~200 lines)
- [ ] Path traversal protection working
- [ ] Test environment detection working
- [ ] SecretsRedactor integration working
- [ ] Unit tests passing (10+ tests)

---

### Day 4: Quality Service Implementation (8 hours)

**File**: `backend/app/services/knowledge_quality_service.py`
**Effort**: 8 hours
**Dependencies**: Day 1-3 completion
**Risk**: Medium - Quality metrics calibration

#### Tasks

1. **Quality gate definitions** (2h)
2. **Scoring algorithms** (3h)
3. **Validation middleware** (2h)
4. **Unit tests** (1h)

#### Code Implementation

```python
#!/usr/bin/env python3
"""
Knowledge Quality Service - Quality Gates and Scoring

Implements quality gates for knowledge extraction output,
ensuring commercial-grade documentation quality.

Quality Benchmark: 20/80 (current) -> 63/80 (target)

Author: UDO Platform Team
Date: 2025-12-28
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class QualityGrade(Enum):
    """Quality grades for extraction output"""
    EXCELLENT = "A"  # 80-100 points
    GOOD = "B"       # 65-79 points
    ACCEPTABLE = "C" # 50-64 points
    POOR = "D"       # 35-49 points
    FAILING = "F"    # 0-34 points


class QualityDimension(Enum):
    """Dimensions evaluated for quality"""
    COMPLETENESS = "completeness"      # All 5 categories present
    DEPTH = "depth"                    # Detail level of insights
    ACCURACY = "accuracy"              # Correctness of extracted info
    ACTIONABILITY = "actionability"    # Practical usefulness
    CLARITY = "clarity"                # Clear, understandable output


@dataclass
class QualityGateResult:
    """Result of a quality gate check"""
    gate_name: str
    passed: bool
    score: float  # 0.0 to 1.0
    message: str
    details: Dict[str, any] = field(default_factory=dict)


@dataclass
class QualityReport:
    """Complete quality assessment report"""
    overall_score: int  # 0-100
    grade: QualityGrade
    dimension_scores: Dict[QualityDimension, float]
    gate_results: List[QualityGateResult]
    recommendations: List[str]
    passed: bool

    # Character counts
    total_chars: int = 0
    target_chars: int = 15000


class QualityGates:
    """
    Quality gates for knowledge extraction.

    Each gate validates a specific quality aspect.
    All gates must pass for production-ready output.
    """

    @staticmethod
    def minimum_categories(extraction_result: dict) -> QualityGateResult:
        """
        Gate 1: Minimum 3 of 5 categories must have content.

        Categories:
        - beginner_concepts
        - management_insights
        - technical_debt
        - patterns
        - ai_synergy
        """
        categories = [
            'beginner_concepts',
            'management_insights',
            'technical_debt',
            'patterns',
            'ai_synergy'
        ]

        populated = sum(
            1 for cat in categories
            if extraction_result.get(cat) and len(extraction_result[cat]) > 0
        )

        passed = populated >= 3
        score = populated / 5.0

        return QualityGateResult(
            gate_name="minimum_categories",
            passed=passed,
            score=score,
            message=f"{populated}/5 categories populated",
            details={"categories_found": populated, "required": 3}
        )

    @staticmethod
    def minimum_character_count(extraction_result: dict, min_chars: int = 5000) -> QualityGateResult:
        """
        Gate 2: Minimum character count for meaningful output.

        Target: 15,000 chars (commercial quality)
        Minimum: 5,000 chars (acceptable)
        """
        # Serialize to count characters
        import json

        def count_text_chars(obj, count=0):
            if isinstance(obj, str):
                return count + len(obj)
            elif isinstance(obj, dict):
                for v in obj.values():
                    count = count_text_chars(v, count)
            elif isinstance(obj, list):
                for item in obj:
                    count = count_text_chars(item, count)
            return count

        total_chars = count_text_chars(extraction_result)

        passed = total_chars >= min_chars
        score = min(total_chars / 15000, 1.0)  # Target is 15,000

        return QualityGateResult(
            gate_name="minimum_character_count",
            passed=passed,
            score=score,
            message=f"{total_chars:,} chars (min: {min_chars:,}, target: 15,000)",
            details={"total_chars": total_chars, "minimum": min_chars, "target": 15000}
        )

    @staticmethod
    def beginner_concept_quality(concepts: List[dict]) -> QualityGateResult:
        """
        Gate 3: Beginner concepts must have explanations.

        Checks:
        - Each concept has title and explanation
        - Explanation is >= 50 chars
        - At least one code example present
        """
        if not concepts:
            return QualityGateResult(
                gate_name="beginner_concept_quality",
                passed=False,
                score=0.0,
                message="No beginner concepts found",
                details={}
            )

        valid_count = 0
        has_code_example = False

        for concept in concepts:
            has_title = concept.get('title') and len(concept['title']) > 5
            has_explanation = concept.get('explanation') and len(concept['explanation']) >= 50

            if has_title and has_explanation:
                valid_count += 1

            if concept.get('code_example'):
                has_code_example = True

        score = valid_count / len(concepts)
        passed = score >= 0.8 and has_code_example

        return QualityGateResult(
            gate_name="beginner_concept_quality",
            passed=passed,
            score=score,
            message=f"{valid_count}/{len(concepts)} concepts have quality content",
            details={
                "valid_concepts": valid_count,
                "total_concepts": len(concepts),
                "has_code_example": has_code_example
            }
        )

    @staticmethod
    def management_insight_quality(insights: List[dict]) -> QualityGateResult:
        """
        Gate 4: Management insights must be actionable.

        Checks:
        - Has title and description
        - Has impact area specified
        - Description >= 100 chars
        """
        if not insights:
            return QualityGateResult(
                gate_name="management_insight_quality",
                passed=True,  # Optional category
                score=0.5,
                message="No management insights (optional)",
                details={}
            )

        valid_count = 0

        for insight in insights:
            has_title = insight.get('title') and len(insight['title']) > 5
            has_description = insight.get('description') and len(insight['description']) >= 50
            has_impact = insight.get('impact_area')

            if has_title and has_description and has_impact:
                valid_count += 1

        score = valid_count / len(insights)
        passed = score >= 0.7

        return QualityGateResult(
            gate_name="management_insight_quality",
            passed=passed,
            score=score,
            message=f"{valid_count}/{len(insights)} insights are actionable",
            details={"valid_insights": valid_count, "total": len(insights)}
        )

    @staticmethod
    def technical_debt_severity(debt_items: List[dict]) -> QualityGateResult:
        """
        Gate 5: Technical debt must have severity classification.

        Checks:
        - All items have severity (low/medium/high/critical)
        - All items have description
        - No more than 2 critical items per extraction
        """
        if not debt_items:
            return QualityGateResult(
                gate_name="technical_debt_severity",
                passed=True,  # Optional
                score=0.5,
                message="No technical debt items (optional)",
                details={}
            )

        valid_severities = {'low', 'medium', 'high', 'critical'}
        valid_count = 0
        critical_count = 0

        for item in debt_items:
            severity = item.get('severity', '').lower()
            has_description = item.get('description') and len(item['description']) > 10

            if severity in valid_severities and has_description:
                valid_count += 1
                if severity == 'critical':
                    critical_count += 1

        score = valid_count / len(debt_items)
        passed = score >= 0.8 and critical_count <= 2

        return QualityGateResult(
            gate_name="technical_debt_severity",
            passed=passed,
            score=score,
            message=f"{valid_count}/{len(debt_items)} properly classified, {critical_count} critical",
            details={
                "valid_items": valid_count,
                "total": len(debt_items),
                "critical_count": critical_count
            }
        )

    @staticmethod
    def no_secrets_leaked(extraction_result: dict) -> QualityGateResult:
        """
        Gate 6: No secrets should be present in output.

        Checks for common secret patterns in all text fields.
        """
        import json
        import re

        # Secret patterns to detect
        secret_patterns = [
            r'(?i)api[_-]?key\s*[=:]\s*[\'"]?[a-zA-Z0-9]{20,}',
            r'(?i)secret[_-]?key\s*[=:]\s*[\'"]?[a-zA-Z0-9]{20,}',
            r'(?i)password\s*[=:]\s*[\'"]?[^\s\'"]{8,}',
            r'(?i)bearer\s+[a-zA-Z0-9_-]{20,}',
            r'AKIA[0-9A-Z]{16}',  # AWS access key
            r'ghp_[a-zA-Z0-9]{36}',  # GitHub token
            r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.',  # JWT
        ]

        # Serialize result
        text = json.dumps(extraction_result)

        secrets_found = []
        for pattern in secret_patterns:
            if re.search(pattern, text):
                secrets_found.append(pattern[:20] + '...')

        passed = len(secrets_found) == 0
        score = 1.0 if passed else 0.0

        return QualityGateResult(
            gate_name="no_secrets_leaked",
            passed=passed,
            score=score,
            message="No secrets detected" if passed else f"Found {len(secrets_found)} potential secrets",
            details={"patterns_matched": secrets_found if not passed else []}
        )


class KnowledgeQualityService:
    """
    Main service for quality assessment of knowledge extraction.
    """

    def __init__(
        self,
        min_quality_score: int = 50,
        required_gates: Optional[List[str]] = None
    ):
        """
        Initialize quality service.

        Args:
            min_quality_score: Minimum score to pass (0-100)
            required_gates: Gates that must pass (default: all)
        """
        self.min_quality_score = min_quality_score
        self.required_gates = required_gates or [
            'minimum_categories',
            'minimum_character_count',
            'no_secrets_leaked'
        ]

    def assess_quality(self, extraction_result: dict) -> QualityReport:
        """
        Perform full quality assessment.

        Args:
            extraction_result: Dictionary from KnowledgeAssetExtractor

        Returns:
            QualityReport with scores and recommendations
        """
        gate_results = []

        # Run all quality gates
        gate_results.append(QualityGates.minimum_categories(extraction_result))
        gate_results.append(QualityGates.minimum_character_count(extraction_result))
        gate_results.append(QualityGates.beginner_concept_quality(
            extraction_result.get('beginner_concepts', [])
        ))
        gate_results.append(QualityGates.management_insight_quality(
            extraction_result.get('management_insights', [])
        ))
        gate_results.append(QualityGates.technical_debt_severity(
            extraction_result.get('technical_debt', [])
        ))
        gate_results.append(QualityGates.no_secrets_leaked(extraction_result))

        # Calculate dimension scores
        dimension_scores = self._calculate_dimension_scores(gate_results, extraction_result)

        # Calculate overall score
        overall_score = self._calculate_overall_score(gate_results, dimension_scores)

        # Determine grade
        grade = self._score_to_grade(overall_score)

        # Check required gates
        required_passed = all(
            r.passed for r in gate_results
            if r.gate_name in self.required_gates
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(gate_results, overall_score)

        # Count characters
        import json
        total_chars = len(json.dumps(extraction_result))

        return QualityReport(
            overall_score=overall_score,
            grade=grade,
            dimension_scores=dimension_scores,
            gate_results=gate_results,
            recommendations=recommendations,
            passed=overall_score >= self.min_quality_score and required_passed,
            total_chars=total_chars,
            target_chars=15000
        )

    def _calculate_dimension_scores(
        self,
        gate_results: List[QualityGateResult],
        extraction_result: dict
    ) -> Dict[QualityDimension, float]:
        """Calculate scores for each quality dimension"""

        # Map gates to dimensions
        completeness = next(
            (r.score for r in gate_results if r.gate_name == 'minimum_categories'),
            0.5
        )

        # Depth based on character count
        char_gate = next(
            (r for r in gate_results if r.gate_name == 'minimum_character_count'),
            None
        )
        depth = char_gate.score if char_gate else 0.5

        # Accuracy approximated by concept quality
        concept_gate = next(
            (r for r in gate_results if r.gate_name == 'beginner_concept_quality'),
            None
        )
        accuracy = concept_gate.score if concept_gate else 0.5

        # Actionability from management insights
        insight_gate = next(
            (r for r in gate_results if r.gate_name == 'management_insight_quality'),
            None
        )
        actionability = insight_gate.score if insight_gate else 0.5

        # Clarity approximated (no raw errors in output)
        secrets_gate = next(
            (r for r in gate_results if r.gate_name == 'no_secrets_leaked'),
            None
        )
        clarity = secrets_gate.score if secrets_gate else 0.5

        return {
            QualityDimension.COMPLETENESS: completeness,
            QualityDimension.DEPTH: depth,
            QualityDimension.ACCURACY: accuracy,
            QualityDimension.ACTIONABILITY: actionability,
            QualityDimension.CLARITY: clarity,
        }

    def _calculate_overall_score(
        self,
        gate_results: List[QualityGateResult],
        dimension_scores: Dict[QualityDimension, float]
    ) -> int:
        """Calculate overall quality score (0-100)"""

        # Weight dimensions
        weights = {
            QualityDimension.COMPLETENESS: 0.25,
            QualityDimension.DEPTH: 0.20,
            QualityDimension.ACCURACY: 0.20,
            QualityDimension.ACTIONABILITY: 0.20,
            QualityDimension.CLARITY: 0.15,
        }

        weighted_sum = sum(
            dimension_scores[dim] * weight
            for dim, weight in weights.items()
        )

        # Scale to 0-100
        return int(weighted_sum * 100)

    def _score_to_grade(self, score: int) -> QualityGrade:
        """Convert numeric score to letter grade"""
        if score >= 80:
            return QualityGrade.EXCELLENT
        elif score >= 65:
            return QualityGrade.GOOD
        elif score >= 50:
            return QualityGrade.ACCEPTABLE
        elif score >= 35:
            return QualityGrade.POOR
        else:
            return QualityGrade.FAILING

    def _generate_recommendations(
        self,
        gate_results: List[QualityGateResult],
        overall_score: int
    ) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        for result in gate_results:
            if not result.passed:
                if result.gate_name == 'minimum_categories':
                    recommendations.append(
                        "Add more category content - aim for at least 3 of 5 categories"
                    )
                elif result.gate_name == 'minimum_character_count':
                    chars = result.details.get('total_chars', 0)
                    recommendations.append(
                        f"Increase content depth - currently {chars:,} chars, target 15,000"
                    )
                elif result.gate_name == 'beginner_concept_quality':
                    recommendations.append(
                        "Add code examples and detailed explanations to beginner concepts"
                    )
                elif result.gate_name == 'management_insight_quality':
                    recommendations.append(
                        "Include impact areas and ROI estimates in management insights"
                    )
                elif result.gate_name == 'no_secrets_leaked':
                    recommendations.append(
                        "CRITICAL: Remove detected secrets before publishing"
                    )

        if overall_score < 50:
            recommendations.append(
                "Consider re-running extraction with more detailed commit/task data"
            )

        return recommendations


# Validation middleware for FastAPI integration
async def validate_extraction_quality(
    extraction_result: dict,
    min_score: int = 50
) -> Tuple[bool, Optional[QualityReport]]:
    """
    FastAPI middleware function for quality validation.

    Args:
        extraction_result: Extraction output to validate
        min_score: Minimum acceptable quality score

    Returns:
        Tuple of (passed, report)
    """
    service = KnowledgeQualityService(min_quality_score=min_score)
    report = service.assess_quality(extraction_result)

    return report.passed, report


# Module exports
__all__ = [
    'KnowledgeQualityService',
    'QualityGates',
    'QualityGrade',
    'QualityDimension',
    'QualityReport',
    'QualityGateResult',
    'validate_extraction_quality',
]
```

#### Success Criteria
- [ ] `knowledge_quality_service.py` created (~300 lines)
- [ ] 6 quality gates implemented
- [ ] Scoring algorithm producing 0-100 scores
- [ ] Grade calculation working (A-F)
- [ ] Recommendations generated
- [ ] Unit tests passing (15+ tests)

---

### Day 5: Integration and Testing (8 hours)

**Files**:
- `backend/app/services/kanban_archive_service.py` (MODIFY)
- `backend/tests/test_knowledge_extraction.py` (NEW)

**Effort**: 8 hours
**Dependencies**: Days 1-4
**Risk**: Medium - Integration complexity

#### Tasks

1. **Modify kanban_archive_service.py** (3h)
2. **Create comprehensive test suite** (4h)
3. **Integration testing** (1h)

#### Archive Service Modifications

Add to `kanban_archive_service.py`:

```python
# Add imports at top
from scripts.knowledge_asset_extractor import KnowledgeAssetExtractor, ExtractionResult
from backend.app.services.knowledge_quality_service import (
    KnowledgeQualityService,
    QualityReport,
    validate_extraction_quality
)
from backend.app.core.security_validators import (
    is_test_environment,
    SecretsRedactorWrapper
)

# Add to __init__
def __init__(self):
    # ... existing code ...

    # Knowledge extraction integration
    self._knowledge_extractor = None
    self._quality_service = None

    if not self._is_test_mode:
        try:
            self._knowledge_extractor = KnowledgeAssetExtractor(
                repo_path=Path.cwd(),
                enable_git=True,
                enable_secrets_redaction=True
            )
            self._quality_service = KnowledgeQualityService(min_quality_score=50)
            logger.info("Knowledge extraction engine initialized")
        except Exception as e:
            logger.warning(f"Knowledge extraction not available: {e}")

# Add new method
async def _generate_rich_knowledge_extraction(
    self,
    task: Task,
    ai_summary: Optional[AISummary]
) -> Tuple[Optional[dict], Optional[QualityReport]]:
    """
    Generate rich knowledge extraction using the 5-category system.

    Args:
        task: The completed task
        ai_summary: Optional AI summary for context

    Returns:
        Tuple of (extraction_dict, quality_report)
    """
    if not self._knowledge_extractor:
        logger.info("Knowledge extractor not available, using basic extraction")
        return None, None

    try:
        # Extract from most recent commit related to task
        result = self._knowledge_extractor.extract_from_commit(
            commit_hash="HEAD",
            task_id=str(task.task_id),
            task_title=task.title
        )

        # Convert to dict for quality assessment
        extraction_dict = {
            'task_id': result.task_id,
            'task_title': result.task_title,
            'beginner_concepts': [
                {
                    'title': c.title,
                    'explanation': c.explanation,
                    'difficulty': c.difficulty.value,
                    'code_example': c.code_example,
                    'tags': c.tags
                }
                for c in result.beginner_concepts
            ],
            'management_insights': [
                {
                    'title': i.title,
                    'description': i.description,
                    'impact_area': i.impact_area,
                    'roi_estimate': i.roi_estimate
                }
                for i in result.management_insights
            ],
            'technical_debt': [
                {
                    'location': d.location,
                    'description': d.description,
                    'severity': d.severity,
                    'debt_type': d.debt_type
                }
                for d in result.technical_debt
            ],
            'patterns': [
                {
                    'name': p.name,
                    'description': p.description,
                    'pattern_type': p.pattern_type,
                    'anti_pattern': p.anti_pattern
                }
                for p in result.patterns
            ],
            'ai_synergy': [
                {
                    'tool_name': s.tool_name,
                    'usage_pattern': s.usage_pattern,
                    'effectiveness': s.effectiveness
                }
                for s in result.ai_synergy
            ],
            'metadata': {
                'files_analyzed': result.files_analyzed,
                'lines_changed': result.lines_changed,
                'extraction_time_ms': result.extraction_duration_ms
            }
        }

        # Assess quality
        quality_report = None
        if self._quality_service:
            quality_report = self._quality_service.assess_quality(extraction_dict)

            if not quality_report.passed:
                logger.warning(
                    f"Knowledge extraction quality below threshold: "
                    f"{quality_report.overall_score}/100"
                )

        return extraction_dict, quality_report

    except Exception as e:
        logger.error(f"Rich knowledge extraction failed: {e}")
        return None, None

# Modify _generate_obsidian_note to include rich extraction
def _generate_obsidian_note(
    self,
    entry: ObsidianKnowledgeEntry,
    roi_metrics: ROIMetrics,
    rich_extraction: Optional[dict] = None
) -> str:
    """Generate Obsidian markdown note content with optional rich extraction"""

    # ... existing frontmatter code ...

    # Add rich extraction sections if available
    if rich_extraction:
        note += self._format_rich_extraction(rich_extraction)

    return note

def _format_rich_extraction(self, extraction: dict) -> str:
    """Format rich extraction as markdown sections"""
    sections = []

    # Beginner Concepts
    if extraction.get('beginner_concepts'):
        sections.append("\n## Learning Concepts\n")
        for concept in extraction['beginner_concepts']:
            difficulty = concept.get('difficulty', 'medium')
            sections.append(f"### {concept['title']} [{difficulty}]\n")
            sections.append(f"{concept['explanation']}\n")
            if concept.get('tags'):
                sections.append(f"**Tags**: {', '.join(concept['tags'])}\n")

    # Management Insights
    if extraction.get('management_insights'):
        sections.append("\n## Strategic Insights\n")
        for insight in extraction['management_insights']:
            sections.append(f"### {insight['title']}\n")
            sections.append(f"{insight['description']}\n")
            if insight.get('impact_area'):
                sections.append(f"**Impact Area**: {insight['impact_area']}\n")
            if insight.get('roi_estimate'):
                sections.append(f"**ROI Estimate**: {insight['roi_estimate']}\n")

    # Technical Debt
    if extraction.get('technical_debt'):
        sections.append("\n## Technical Debt\n")
        for debt in extraction['technical_debt']:
            severity = debt.get('severity', 'medium').upper()
            sections.append(f"- [{severity}] {debt['description']}\n")

    # Patterns
    if extraction.get('patterns'):
        sections.append("\n## Patterns Detected\n")
        for pattern in extraction['patterns']:
            icon = "Anti" if pattern.get('anti_pattern') else "Good"
            sections.append(f"- [{icon}] **{pattern['name']}**: {pattern['description']}\n")

    # AI Synergy
    if extraction.get('ai_synergy'):
        sections.append("\n## AI Collaboration\n")
        for synergy in extraction['ai_synergy']:
            sections.append(f"- **{synergy['tool_name']}**: {synergy['usage_pattern']}\n")

    return ''.join(sections)
```

#### Test Suite

```python
# backend/tests/test_knowledge_extraction.py
"""
Comprehensive Test Suite for Knowledge Extraction System

Tests:
- KnowledgeAssetExtractor
- KnowledgeQualityService
- SecurityValidators
- Integration with KanbanArchiveService
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import test subjects
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.knowledge_asset_extractor import (
    KnowledgeAssetExtractor,
    ExtractionResult,
    GitDiffAnalyzer,
    TodoExtractor,
    PatternDetector,
    BeginnerConcept,
    Difficulty,
    ExtractionCategory
)
from backend.app.services.knowledge_quality_service import (
    KnowledgeQualityService,
    QualityGates,
    QualityGrade,
    QualityReport
)
from backend.app.core.security_validators import (
    SecurePathValidator,
    TestEnvironmentDetector,
    SecretsRedactorWrapper,
    PathTraversalError,
    SecurityValidationError
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_repo():
    """Create a temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_diff():
    """Sample git diff content"""
    return """
diff --git a/backend/app/services/auth_service.py b/backend/app/services/auth_service.py
index 123456..789abc 100644
--- a/backend/app/services/auth_service.py
+++ b/backend/app/services/auth_service.py
@@ -10,6 +10,20 @@ class AuthService:
+    def validate_token(self, token: str) -> bool:
+        \"\"\"Validate JWT token.\"\"\"
+        try:
+            # TODO: Add token expiration check
+            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
+            return True
+        except jwt.InvalidTokenError:
+            logger.error("Invalid token")
+            return False
+
+    async def get_user_permissions(self, user_id: str) -> List[str]:
+        \"\"\"Get user permissions.\"\"\"
+        # FIXME: Cache this for performance
+        return await self.db.get_permissions(user_id)
"""


@pytest.fixture
def sample_extraction_result():
    """Sample extraction result for quality testing"""
    return {
        'task_id': 'test-123',
        'task_title': 'Implement authentication service',
        'beginner_concepts': [
            {
                'title': 'JWT Token Validation',
                'explanation': 'JSON Web Tokens (JWT) provide a secure way to transmit information between parties. Validating tokens involves checking the signature, expiration, and claims.',
                'difficulty': 'medium',
                'code_example': 'jwt.decode(token, secret, algorithms=["HS256"])',
                'tags': ['security', 'authentication']
            },
            {
                'title': 'Error Handling in Async Code',
                'explanation': 'Using try-except blocks with async functions helps gracefully handle errors in asynchronous operations without crashing the application.',
                'difficulty': 'medium',
                'tags': ['error-handling', 'async']
            }
        ],
        'management_insights': [
            {
                'title': 'Security Implementation Progress',
                'description': 'Authentication service implementation adds critical security layer. JWT validation ensures only authorized users access protected resources.',
                'impact_area': 'security',
                'roi_estimate': 'Prevents unauthorized access, reducing potential security incident costs'
            }
        ],
        'technical_debt': [
            {
                'location': 'auth_service.py:15',
                'description': 'Token expiration check not implemented',
                'severity': 'medium',
                'debt_type': 'intentional'
            },
            {
                'location': 'auth_service.py:22',
                'description': 'Permission caching needed for performance',
                'severity': 'medium',
                'debt_type': 'intentional'
            }
        ],
        'patterns': [
            {
                'name': 'Error Handling',
                'description': 'Robust error handling with logging for debugging',
                'pattern_type': 'success',
                'anti_pattern': False
            },
            {
                'name': 'Type Hints',
                'description': 'Full type annotations for better IDE support and documentation',
                'pattern_type': 'success',
                'anti_pattern': False
            }
        ],
        'ai_synergy': [
            {
                'tool_name': 'Claude Code',
                'usage_pattern': 'Code review and refactoring suggestions',
                'effectiveness': 'high'
            }
        ]
    }


# ============================================================================
# KnowledgeAssetExtractor Tests
# ============================================================================

class TestKnowledgeAssetExtractor:
    """Test the main extraction engine"""

    def test_extractor_initialization(self, temp_repo):
        """Test extractor initializes correctly"""
        extractor = KnowledgeAssetExtractor(
            repo_path=temp_repo,
            enable_git=False,  # No real git repo
            enable_secrets_redaction=False
        )
        assert extractor is not None
        assert extractor.repo_path == temp_repo

    def test_todo_extraction(self, sample_diff):
        """Test TODO extraction from diff"""
        extractor = TodoExtractor()
        todos = extractor.extract_from_diff(sample_diff)

        assert len(todos) >= 2
        todo_types = [t['type'] for t in todos]
        assert 'todo' in todo_types
        assert 'fixme' in todo_types

    def test_pattern_detection(self, sample_diff):
        """Test pattern detection"""
        detector = PatternDetector()
        patterns = detector.detect_patterns(sample_diff, "feat: add auth service")

        assert len(patterns) > 0
        pattern_names = [p.name.lower() for p in patterns]
        # Should detect error handling pattern
        assert any('error' in name for name in pattern_names)

    def test_beginner_concept_extraction(self, temp_repo, sample_diff):
        """Test beginner concept extraction"""
        extractor = KnowledgeAssetExtractor(
            repo_path=temp_repo,
            enable_git=False
        )

        # Manually trigger extraction logic
        concepts = extractor._extract_beginner_concepts(
            diff_content=sample_diff,
            changed_files=['auth_service.py'],
            commit_message='feat: add auth service'
        )

        assert len(concepts) > 0
        assert all(isinstance(c, BeginnerConcept) for c in concepts)

    def test_extraction_result_to_markdown(self, temp_repo):
        """Test markdown output generation"""
        extractor = KnowledgeAssetExtractor(
            repo_path=temp_repo,
            enable_git=False
        )

        result = ExtractionResult(
            task_id='test-123',
            task_title='Test Task',
            extraction_timestamp=datetime.utcnow(),
            beginner_concepts=[
                BeginnerConcept(
                    title='Test Concept',
                    explanation='Test explanation',
                    difficulty=Difficulty.EASY
                )
            ]
        )

        markdown = extractor.to_markdown(result)

        assert '# Knowledge Extraction' in markdown
        assert 'Test Task' in markdown
        assert '## Beginner Concepts' in markdown
        assert 'Test Concept' in markdown


# ============================================================================
# KnowledgeQualityService Tests
# ============================================================================

class TestKnowledgeQualityService:
    """Test quality assessment service"""

    def test_quality_gate_minimum_categories(self, sample_extraction_result):
        """Test minimum categories gate"""
        result = QualityGates.minimum_categories(sample_extraction_result)

        assert result.passed is True
        assert result.score >= 0.6  # At least 3/5 categories

    def test_quality_gate_minimum_characters(self, sample_extraction_result):
        """Test minimum character count gate"""
        result = QualityGates.minimum_character_count(sample_extraction_result)

        assert result.passed is True
        assert result.details['total_chars'] > 1000

    def test_quality_gate_no_secrets(self, sample_extraction_result):
        """Test no secrets gate"""
        result = QualityGates.no_secrets_leaked(sample_extraction_result)

        assert result.passed is True
        assert result.score == 1.0

    def test_quality_gate_secrets_detected(self):
        """Test secrets detection gate"""
        bad_result = {
            'management_insights': [
                {
                    'title': 'Config',
                    'description': 'API key is AKIAIOSFODNN7EXAMPLE for AWS access',
                    'impact_area': 'security'
                }
            ]
        }

        result = QualityGates.no_secrets_leaked(bad_result)

        assert result.passed is False
        assert result.score == 0.0

    def test_full_quality_assessment(self, sample_extraction_result):
        """Test complete quality assessment"""
        service = KnowledgeQualityService(min_quality_score=50)
        report = service.assess_quality(sample_extraction_result)

        assert isinstance(report, QualityReport)
        assert report.overall_score >= 50
        assert report.passed is True
        assert report.grade in [QualityGrade.EXCELLENT, QualityGrade.GOOD, QualityGrade.ACCEPTABLE]

    def test_failing_quality_assessment(self):
        """Test quality assessment for poor extraction"""
        poor_result = {
            'task_id': 'test',
            'beginner_concepts': [],
            'management_insights': [],
            'technical_debt': [],
            'patterns': [],
            'ai_synergy': []
        }

        service = KnowledgeQualityService(min_quality_score=50)
        report = service.assess_quality(poor_result)

        assert report.passed is False
        assert report.overall_score < 50
        assert len(report.recommendations) > 0


# ============================================================================
# SecurityValidators Tests
# ============================================================================

class TestSecurePathValidator:
    """Test path validation security"""

    def test_valid_path(self, temp_repo):
        """Test valid path within boundary"""
        validator = SecurePathValidator(temp_repo)

        # Create a test file
        test_file = temp_repo / "test.py"
        test_file.touch()

        result = validator.validate_path("test.py")
        assert result == test_file

    def test_path_traversal_blocked(self, temp_repo):
        """Test path traversal attack is blocked"""
        validator = SecurePathValidator(temp_repo)

        with pytest.raises(PathTraversalError):
            validator.validate_path("../../../etc/passwd")

    def test_forbidden_file_blocked(self, temp_repo):
        """Test forbidden files are blocked"""
        validator = SecurePathValidator(temp_repo)

        is_safe, reason = validator.is_safe_to_read(".env")
        assert is_safe is False
        assert "forbidden" in reason.lower()

    def test_safe_extension_allowed(self, temp_repo):
        """Test safe extensions are allowed"""
        validator = SecurePathValidator(temp_repo)

        # Create a safe file
        safe_file = temp_repo / "code.py"
        safe_file.write_text("print('hello')")

        is_safe, reason = validator.is_safe_to_read(safe_file)
        assert is_safe is True


class TestTestEnvironmentDetector:
    """Test environment detection"""

    def test_pytest_detection(self, monkeypatch):
        """Test pytest environment detection"""
        monkeypatch.setenv("PYTEST_CURRENT_TEST", "test_file.py::test_func")

        assert TestEnvironmentDetector.is_test_environment() is True

    def test_ci_detection(self, monkeypatch):
        """Test CI environment detection"""
        monkeypatch.setenv("CI", "true")

        assert TestEnvironmentDetector.is_test_environment() is True

    def test_github_actions_detection(self, monkeypatch):
        """Test GitHub Actions detection"""
        monkeypatch.setenv("GITHUB_ACTIONS", "true")

        assert TestEnvironmentDetector.is_test_environment() is True


class TestSecretsRedactorWrapper:
    """Test secrets redaction wrapper"""

    def test_wrapper_initialization(self):
        """Test wrapper initializes (may not have SecretsRedactor)"""
        wrapper = SecretsRedactorWrapper()
        # Should not raise even if SecretsRedactor unavailable
        assert wrapper is not None

    def test_redact_with_secrets(self):
        """Test redaction of secrets"""
        wrapper = SecretsRedactorWrapper()

        if wrapper.available:
            content = "API_KEY=AKIAIOSFODNN7EXAMPLE"
            redacted, count = wrapper.redact(content)

            assert "AKIAIOSFODNN7EXAMPLE" not in redacted
            assert count > 0
        else:
            # If not available, should return unchanged
            content = "test content"
            redacted, count = wrapper.redact(content)
            assert redacted == content
            assert count == 0


# ============================================================================
# Integration Tests
# ============================================================================

class TestKnowledgeExtractionIntegration:
    """Integration tests for the full knowledge extraction pipeline"""

    @pytest.mark.asyncio
    async def test_archive_with_knowledge_extraction(self, sample_extraction_result):
        """Test archive service integration with knowledge extraction"""
        from backend.app.services.kanban_archive_service import kanban_archive_service

        # Verify service initializes in test mode
        assert kanban_archive_service._is_test_mode is True

    def test_quality_to_archive_flow(self, sample_extraction_result):
        """Test quality service to archive flow"""
        # Assess quality
        service = KnowledgeQualityService()
        report = service.assess_quality(sample_extraction_result)

        # Quality should pass
        assert report.passed is True

        # Verify character count improvement
        assert report.total_chars > 500  # Basic output
        # With full implementation, should be > 5000


# Test run summary
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

#### Success Criteria
- [ ] Archive service integration complete
- [ ] 30+ unit tests passing
- [ ] 5+ integration tests passing
- [ ] Quality score 50+ on sample data
- [ ] No secrets in test output

---

## Week 2: Enhancement and Production (Days 6-10)

### Day 6: Enhanced GPT-4o Prompts (4 hours)

**File**: `backend/app/services/kanban_archive_service.py`
**Effort**: 4 hours
**Dependencies**: Week 1 completion

#### Enhanced System Prompt

```python
KNOWLEDGE_EXTRACTION_SYSTEM_PROMPT = """You are an expert knowledge extraction engineer analyzing completed software development tasks.

Your goal is to extract RICH, ACTIONABLE knowledge in 5 categories:

## 1. BEGINNER CONCEPTS (2-4 items)
Target audience: Junior developers (0-2 years experience)
- Identify fundamental concepts demonstrated in this task
- Explain WHY each concept matters (not just WHAT)
- Include concrete code examples when possible
- Rate difficulty: easy/medium/hard
- Add relevant tags for categorization

## 2. MANAGEMENT INSIGHTS (1-3 items)
Target audience: Development managers and tech leads
- Strategic implications of this work
- ROI estimates (time saved, risk reduced, velocity impact)
- Team coordination or process improvements
- Metrics and KPIs affected

## 3. TECHNICAL DEBT (0-5 items)
Be specific about:
- LOCATION: file:line or component
- SEVERITY: critical/high/medium/low
- TYPE: intentional (known tradeoff) vs unintentional (oversight)
- REMEDIATION: estimated effort to fix
- Extract all TODO, FIXME, HACK, XXX comments

## 4. PATTERNS (2-4 items)
Identify:
- SUCCESS patterns worth replicating
- FAILURE patterns to avoid (anti-patterns)
- REFACTORING patterns applied
- Include before/after code snippets when relevant

## 5. AI COLLABORATION (1-2 items)
Document AI tool usage:
- Which tools were effective (Claude, Copilot, etc.)
- Prompt patterns that worked well
- Time saved estimates
- Areas where AI struggled

FORMAT: Respond with detailed JSON matching the schema.
AIM: Total output should be 15,000+ characters for commercial-grade documentation.
QUALITY: Each insight should be specific and actionable, not generic."""

KNOWLEDGE_EXTRACTION_USER_PROMPT_TEMPLATE = """## Task Information

**Task ID**: {task_id}
**Title**: {title}
**Phase**: {phase}
**Status**: Completed

## Description
{description}

## Metrics
- Estimated Hours: {estimated_hours}
- Actual Hours: {actual_hours}
- Quality Score: {quality_score}/100
- AI Suggested: {ai_suggested}
- AI Confidence: {ai_confidence}

## Context
{context_notes}

## Git Diff Summary
Files changed: {files_changed}
Lines added: {lines_added}
Lines removed: {lines_removed}

## Diff Content (redacted)
```
{diff_content}
```

Extract comprehensive knowledge assets following the 5-category framework."""
```

### Day 7-8: Performance Optimization (8 hours)

**Focus**: Ensure extraction completes in <5 seconds

#### Tasks

1. **Parallel extraction** (3h)
   - Use asyncio for concurrent operations

2. **Caching layer** (3h)
   - Cache git diff results
   - Cache pattern detection results

3. **Performance benchmarks** (2h)

#### Benchmark Script

```python
# scripts/benchmark_knowledge_extraction.py
import asyncio
import time
import statistics

async def benchmark_extraction(iterations: int = 10):
    """Run extraction benchmark"""
    from scripts.knowledge_asset_extractor import KnowledgeAssetExtractor

    extractor = KnowledgeAssetExtractor()
    times = []

    for i in range(iterations):
        start = time.time()
        result = extractor.extract_from_commit("HEAD")
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"Iteration {i+1}: {elapsed:.3f}s")

    print(f"\n--- Benchmark Results ---")
    print(f"Mean: {statistics.mean(times):.3f}s")
    print(f"Median: {statistics.median(times):.3f}s")
    print(f"Std Dev: {statistics.stdev(times):.3f}s")
    print(f"Min: {min(times):.3f}s")
    print(f"Max: {max(times):.3f}s")

    # Target: <5s
    if statistics.mean(times) > 5:
        print("\nWARNING: Mean exceeds 5s target!")
        return False
    else:
        print("\nPASS: Mean within 5s target")
        return True

if __name__ == "__main__":
    asyncio.run(benchmark_extraction())
```

### Day 9: CI/CD Integration (4 hours)

**File**: `.github/workflows/knowledge-extraction-ci.yml` (UPDATE)

#### Updated Workflow

```yaml
# Add to existing knowledge-extraction-ci.yml

  quality-gate-validation:
    name: Knowledge Extraction Quality Gates
    runs-on: ubuntu-latest
    needs: unit-tests

    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 10

      - name: Set up Python 3.13
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r backend/requirements.txt

      - name: Run extraction on HEAD
        run: |
          python -c "
          import sys
          sys.path.insert(0, '.')

          from scripts.knowledge_asset_extractor import KnowledgeAssetExtractor
          from backend.app.services.knowledge_quality_service import KnowledgeQualityService

          extractor = KnowledgeAssetExtractor(enable_git=True)
          result = extractor.extract_from_commit('HEAD')

          # Convert to dict
          extraction_dict = {
              'beginner_concepts': [{'title': c.title, 'explanation': c.explanation, 'difficulty': c.difficulty.value} for c in result.beginner_concepts],
              'management_insights': [{'title': i.title, 'description': i.description, 'impact_area': i.impact_area} for i in result.management_insights],
              'technical_debt': [{'description': d.description, 'severity': d.severity} for d in result.technical_debt],
              'patterns': [{'name': p.name, 'description': p.description} for p in result.patterns],
              'ai_synergy': [{'tool_name': s.tool_name} for s in result.ai_synergy]
          }

          service = KnowledgeQualityService(min_quality_score=40)
          report = service.assess_quality(extraction_dict)

          print(f'Quality Score: {report.overall_score}/100')
          print(f'Grade: {report.grade.value}')
          print(f'Passed: {report.passed}')

          if not report.passed:
              print('Quality gate FAILED')
              sys.exit(1)
          "
        env:
          TEST_MODE: "true"
          PYTHONPATH: ${{ github.workspace }}
```

### Day 10: Documentation and Handoff (4 hours)

**Files**:
- Update this roadmap with final status
- `docs/KNOWLEDGE_EXTRACTION_USER_GUIDE.md`
- `claudedocs/completion/2025-12-XX-KNOWLEDGE-EXTRACTION-COMPLETE.md`

---

## Risk Mitigation Summary

| Risk | Mitigation | Owner |
|------|------------|-------|
| Git not available | Graceful degradation to static analysis | Day 1 |
| SecretsRedactor import fail | Wrapper with fallback | Day 3 |
| Quality score calibration | Multiple test cases + manual review | Day 4-5 |
| Performance >5s | Parallel processing + caching | Day 7-8 |
| CI integration fails | Test vault structure | Day 9 |

---

## Success Metrics

| Metric | Current | Target | Verification |
|--------|---------|--------|--------------|
| Output size | ~500 chars | ~15,000 chars | Character count |
| Categories | 5 basic | 5 rich | Category audit |
| Quality score | 20/80 | 63/80 | QualityService |
| Extraction time | N/A | <5s | Benchmark |
| Test coverage | 0% | 80%+ | pytest-cov |
| Secrets leaked | N/A | 0 | Gate check |

---

## Checkpoint Schedule

| Day | Checkpoint | Success Criteria |
|-----|------------|------------------|
| 1 | Core extractor | CLI runs, outputs markdown |
| 3 | Security validators | Path traversal test passes |
| 4 | Quality service | 6 gates implemented |
| 5 | Integration | Archive service updated |
| 8 | Performance | <5s mean extraction |
| 10 | Production ready | All CI tests pass |

---

## File Summary

| File | Status | Lines | Purpose |
|------|--------|-------|---------|
| `scripts/knowledge_asset_extractor.py` | NEW | ~500 | 5-category extraction |
| `backend/app/services/knowledge_quality_service.py` | NEW | ~300 | Quality gates |
| `backend/app/core/security_validators.py` | NEW | ~200 | Path + secrets security |
| `backend/app/services/kanban_archive_service.py` | MODIFY | +150 | Integration |
| `backend/tests/test_knowledge_extraction.py` | NEW | ~400 | Test suite |

**Total new code**: ~1,550 lines
**Total effort**: 54 hours (10 days at ~5.4 hours/day)

---

## Appendix: Quick Reference Commands

```bash
# Run extraction CLI
python scripts/knowledge_asset_extractor.py --commit HEAD --output result.md

# Run quality assessment
python -c "from backend.app.services.knowledge_quality_service import *; print(KnowledgeQualityService().assess_quality({}))"

# Run all tests
pytest backend/tests/test_knowledge_extraction.py -v

# Run benchmark
python scripts/benchmark_knowledge_extraction.py

# Check for secrets
python -c "from backend.app.utils.secrets_redactor import scan_for_secrets; print(scan_for_secrets(open('file.py').read()))"
```

---

**Document Status**: FINAL BLUEPRINT
**Ready for Execution**: Yes
**Estimated Completion**: 10 working days
**Dependencies**: All identified and documented
