#!/usr/bin/env python3
"""
Obsidian RL-Compatible Tagger - Training-free GRPO Tag System

Implements RL-compatible tagging for Obsidian knowledge entries:
- Pattern classification (#success/*, #failure/*)
- Quality metrics (#resolution-time/*, #recurrence/*, #side-effects/*)
- Comparative analysis (#compare/*, #tradeoff/*)

Based on: ArXiv 2510.08191 (Training-free GRPO)

Author: UDO Platform Team
Date: 2026-01-02
Version: 1.0.0
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Data Classes
# =============================================================================


class PatternOutcome(Enum):
    """Outcome classification for patterns"""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    UNKNOWN = "unknown"


class SideEffectSeverity(Enum):
    """Severity levels for side effects"""

    NONE = "none"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


@dataclass
class RLKnowledgeEntry:
    """RL-compatible knowledge entry with quality metrics"""

    # Core identification
    id: str
    title: str
    domain: str  # auth, api, database, frontend, etc.
    pattern: str  # specific pattern name

    # Outcome
    outcome: PatternOutcome = PatternOutcome.UNKNOWN
    reason: Optional[str] = None  # For failures: why it failed

    # Quality metrics (for Group Relative Scoring)
    resolution_time_minutes: int = 0
    recurrence_count: int = 0
    side_effects: SideEffectSeverity = SideEffectSeverity.NONE

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    source_commit: Optional[str] = None
    related_files: List[str] = field(default_factory=list)

    # RL-specific
    token_prior_score: float = 0.0  # Cached Group Relative score
    tags: List[str] = field(default_factory=list)


@dataclass
class TaggingResult:
    """Result of tagging operation"""

    entry: RLKnowledgeEntry
    generated_tags: List[str]
    frontmatter: Dict[str, Any]
    markdown_content: str


# =============================================================================
# RL-Compatible Tagger
# =============================================================================


class RLObsidianTagger:
    """
    Tags Obsidian knowledge entries with RL-compatible metadata.

    Implements Training-free GRPO concepts:
    1. Token Prior: Experiential knowledge tags
    2. Group Relative: Quality metrics for comparative scoring
    3. Policy Optimization: Best-solution identification tags
    """

    # Domain mappings
    DOMAIN_KEYWORDS = {
        "auth": ["authentication", "login", "jwt", "token", "session", "oauth", "rbac"],
        "api": ["endpoint", "rest", "graphql", "request", "response", "http", "status"],
        "database": ["query", "sql", "postgres", "mongodb", "migration", "schema"],
        "frontend": ["react", "vue", "component", "ui", "css", "tailwind", "next"],
        "testing": ["test", "pytest", "jest", "e2e", "unit", "coverage", "assertion"],
        "performance": ["optimization", "cache", "speed", "latency", "memory", "cpu"],
        "security": ["vulnerability", "injection", "xss", "csrf", "sanitize", "encrypt"],
        "devops": ["deploy", "docker", "kubernetes", "ci", "cd", "pipeline", "github"],
        "websocket": ["ws", "socket", "realtime", "connection", "broadcast"],
        "config": ["environment", "env", "settings", "configuration", "yaml", "json"],
    }

    def __init__(self, obsidian_vault_path: Optional[Path] = None):
        """
        Initialize the tagger.

        Args:
            obsidian_vault_path: Path to Obsidian vault (optional)
        """
        self.vault_path = obsidian_vault_path
        self._tag_cache: Dict[str, List[str]] = {}

    def tag_knowledge_entry(self, entry: RLKnowledgeEntry) -> TaggingResult:
        """
        Generate RL-compatible tags for a knowledge entry.

        Args:
            entry: Knowledge entry to tag

        Returns:
            TaggingResult with generated tags and formatted content
        """
        tags = []

        # 1. Pattern classification tags
        tags.extend(self._generate_pattern_tags(entry))

        # 2. Quality metric tags
        tags.extend(self._generate_quality_tags(entry))

        # 3. Domain-specific tags
        tags.extend(self._generate_domain_tags(entry))

        # 4. Comparative tags (if applicable)
        tags.extend(self._generate_comparative_tags(entry))

        # Update entry with tags
        entry.tags = tags

        # Generate frontmatter and markdown
        frontmatter = self._generate_frontmatter(entry, tags)
        markdown = self._generate_markdown(entry, tags)

        return TaggingResult(entry=entry, generated_tags=tags, frontmatter=frontmatter, markdown_content=markdown)

    def _generate_pattern_tags(self, entry: RLKnowledgeEntry) -> List[str]:
        """Generate pattern classification tags."""
        tags = []

        if entry.outcome == PatternOutcome.SUCCESS:
            # #success/{domain}/{pattern}
            tags.append(f"#success/{entry.domain}/{self._slugify(entry.pattern)}")
        elif entry.outcome == PatternOutcome.FAILURE:
            # #failure/{domain}/{reason}
            reason = self._slugify(entry.reason) if entry.reason else "unknown"
            tags.append(f"#failure/{entry.domain}/{reason}")
        elif entry.outcome == PatternOutcome.PARTIAL:
            tags.append(f"#partial/{entry.domain}/{self._slugify(entry.pattern)}")

        return tags

    def _generate_quality_tags(self, entry: RLKnowledgeEntry) -> List[str]:
        """Generate quality metric tags for Group Relative Scoring."""
        tags = []

        # Resolution time category
        if entry.resolution_time_minutes > 0:
            if entry.resolution_time_minutes <= 5:
                tags.append("#resolution-time/fast")
            elif entry.resolution_time_minutes <= 30:
                tags.append("#resolution-time/medium")
            else:
                tags.append("#resolution-time/slow")
            tags.append(f"#resolution-time/{entry.resolution_time_minutes}min")

        # Recurrence count
        tags.append(f"#recurrence/{entry.recurrence_count}")
        if entry.recurrence_count == 0:
            tags.append("#solved-permanently")
        elif entry.recurrence_count >= 3:
            tags.append("#recurring-issue")

        # Side effects severity
        tags.append(f"#side-effects/{entry.side_effects.value}")

        return tags

    def _generate_domain_tags(self, entry: RLKnowledgeEntry) -> List[str]:
        """Generate domain-specific tags."""
        tags = [f"#domain/{entry.domain}"]

        # Add related domain tags based on content
        text_to_search = f"{entry.title} {entry.pattern} {entry.reason or ''}"
        text_lower = text_to_search.lower()

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            if domain != entry.domain:  # Don't duplicate primary domain
                for keyword in keywords:
                    if keyword in text_lower:
                        tags.append(f"#related/{domain}")
                        break

        return tags

    def _generate_comparative_tags(self, entry: RLKnowledgeEntry) -> List[str]:
        """Generate comparative analysis tags."""
        tags = []

        # If entry mentions alternatives or comparisons
        comparison_keywords = ["vs", "versus", "compared to", "alternative", "instead of"]
        text = f"{entry.title} {entry.pattern}".lower()

        for keyword in comparison_keywords:
            if keyword in text:
                tags.append("#compare/has-alternatives")
                break

        # Tradeoff detection
        tradeoff_pairs = [
            ("speed", "accuracy"),
            ("performance", "maintainability"),
            ("security", "convenience"),
            ("simplicity", "flexibility"),
        ]

        for metric1, metric2 in tradeoff_pairs:
            if metric1 in text and metric2 in text:
                tags.append(f"#tradeoff/{metric1}-vs-{metric2}")

        return tags

    def _generate_frontmatter(self, entry: RLKnowledgeEntry, tags: List[str]) -> Dict[str, Any]:
        """Generate YAML frontmatter for Obsidian."""
        return {
            "id": entry.id,
            "title": entry.title,
            "domain": entry.domain,
            "pattern": entry.pattern,
            "outcome": entry.outcome.value,
            "resolution_time_minutes": entry.resolution_time_minutes,
            "recurrence_count": entry.recurrence_count,
            "side_effects": entry.side_effects.value,
            "token_prior_score": entry.token_prior_score,
            "created_at": entry.created_at.isoformat(),
            "source_commit": entry.source_commit,
            "tags": [t.lstrip("#") for t in tags],  # Remove # for frontmatter
            "rl_version": "1.0",
        }

    def _generate_markdown(self, entry: RLKnowledgeEntry, tags: List[str]) -> str:
        """Generate Markdown content for Obsidian note."""
        lines = []

        # YAML frontmatter
        lines.append("---")
        fm = self._generate_frontmatter(entry, tags)
        for key, value in fm.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# {entry.title}")
        lines.append("")

        # Tags (inline for easy viewing)
        lines.append("## Tags")
        lines.append(" ".join(tags))
        lines.append("")

        # Pattern details
        lines.append("## Pattern Details")
        lines.append(f"- **Domain**: {entry.domain}")
        lines.append(f"- **Pattern**: {entry.pattern}")
        lines.append(f"- **Outcome**: {entry.outcome.value}")
        if entry.reason:
            lines.append(f"- **Reason**: {entry.reason}")
        lines.append("")

        # Quality Metrics
        lines.append("## Quality Metrics (for Group Relative Scoring)")
        lines.append(f"- **Resolution Time**: {entry.resolution_time_minutes} minutes")
        lines.append(f"- **Recurrence Count**: {entry.recurrence_count}")
        lines.append(f"- **Side Effects**: {entry.side_effects.value}")
        lines.append(f"- **Token Prior Score**: {entry.token_prior_score:.2f}")
        lines.append("")

        # Related files
        if entry.related_files:
            lines.append("## Related Files")
            for f in entry.related_files:
                lines.append(f"- [[{f}]]")
            lines.append("")

        # Metadata
        lines.append("## Metadata")
        lines.append(f"- **Created**: {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
        if entry.source_commit:
            lines.append(f"- **Source Commit**: `{entry.source_commit}`")
        lines.append("")

        return "\n".join(lines)

    def _slugify(self, text: Optional[str]) -> str:
        """Convert text to URL-safe slug."""
        if not text:
            return "unknown"
        # Lowercase, replace spaces and special chars with hyphens
        slug = text.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")
        return slug or "unknown"

    def detect_domain(self, text: str) -> str:
        """
        Auto-detect domain from text content.

        Args:
            text: Text to analyze

        Returns:
            Best matching domain
        """
        text_lower = text.lower()
        domain_scores: Dict[str, int] = {}

        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                domain_scores[domain] = score

        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        return "general"

    def parse_resolution_time(self, text: str) -> int:
        """
        Parse resolution time from text.

        Examples:
            "fixed in 5 minutes" -> 5
            "took 2 hours to debug" -> 120
            "quick fix, 30 seconds" -> 1

        Args:
            text: Text containing time information

        Returns:
            Resolution time in minutes
        """
        text_lower = text.lower()

        # Hours
        hour_match = re.search(r"(\d+)\s*hours?", text_lower)
        if hour_match:
            return int(hour_match.group(1)) * 60

        # Minutes
        min_match = re.search(r"(\d+)\s*min(?:utes?)?", text_lower)
        if min_match:
            return int(min_match.group(1))

        # Seconds (round up to 1 minute)
        sec_match = re.search(r"(\d+)\s*sec(?:onds?)?", text_lower)
        if sec_match:
            return max(1, int(sec_match.group(1)) // 60)

        # Keywords
        if any(kw in text_lower for kw in ["quick", "fast", "instantly", "immediate"]):
            return 1
        if any(kw in text_lower for kw in ["long", "hours", "day", "struggled"]):
            return 60

        return 0  # Unknown

    def parse_side_effects(self, text: str) -> SideEffectSeverity:
        """
        Parse side effect severity from text.

        Args:
            text: Text describing the solution

        Returns:
            Side effect severity level
        """
        text_lower = text.lower()

        critical_keywords = ["broke", "crashed", "production down", "data loss", "security breach"]
        major_keywords = ["broke other", "regression", "test failed", "side effect"]
        minor_keywords = ["minor issue", "small problem", "warning", "deprecation"]
        none_keywords = ["clean", "no issues", "works perfectly", "no side effects"]

        if any(kw in text_lower for kw in critical_keywords):
            return SideEffectSeverity.CRITICAL
        if any(kw in text_lower for kw in major_keywords):
            return SideEffectSeverity.MAJOR
        if any(kw in text_lower for kw in minor_keywords):
            return SideEffectSeverity.MINOR
        if any(kw in text_lower for kw in none_keywords):
            return SideEffectSeverity.NONE

        return SideEffectSeverity.NONE  # Default


# =============================================================================
# Batch Processing Utilities
# =============================================================================


class BatchTagger:
    """Batch process multiple knowledge entries."""

    def __init__(self, tagger: RLObsidianTagger):
        self.tagger = tagger

    def tag_from_git_commits(
        self, commits: List[Dict[str, Any]], success_patterns: Optional[List[str]] = None
    ) -> List[TaggingResult]:
        """
        Generate tags from git commit history.

        Args:
            commits: List of commit dicts with 'hash', 'message', 'files'
            success_patterns: Patterns indicating successful commits

        Returns:
            List of tagging results
        """
        results = []
        success_patterns = success_patterns or ["fix", "feat", "add", "implement"]

        for commit in commits:
            # Determine outcome from commit message
            msg_lower = commit.get("message", "").lower()

            if any(p in msg_lower for p in ["fix", "resolve", "solved"]):
                outcome = PatternOutcome.SUCCESS
            elif any(p in msg_lower for p in ["wip", "attempt", "try"]):
                outcome = PatternOutcome.PARTIAL
            elif any(p in msg_lower for p in ["revert", "rollback", "broken"]):
                outcome = PatternOutcome.FAILURE
            else:
                outcome = PatternOutcome.SUCCESS  # Default for completed commits

            # Create entry
            entry = RLKnowledgeEntry(
                id=commit.get("hash", "")[:8],
                title=commit.get("message", "").split("\n")[0][:80],
                domain=self.tagger.detect_domain(commit.get("message", "")),
                pattern=self._extract_pattern(commit.get("message", "")),
                outcome=outcome,
                source_commit=commit.get("hash"),
                related_files=commit.get("files", []),
            )

            result = self.tagger.tag_knowledge_entry(entry)
            results.append(result)

        return results

    def _extract_pattern(self, commit_message: str) -> str:
        """Extract pattern name from commit message."""
        # Remove common prefixes
        msg = commit_message.lower()
        for prefix in ["fix:", "feat:", "add:", "chore:", "docs:", "test:", "refactor:"]:
            if msg.startswith(prefix):
                msg = msg[len(prefix) :].strip()
                break

        # Take first meaningful phrase
        msg = msg.split("\n")[0][:50]
        return msg or "unknown-pattern"


# =============================================================================
# CLI Interface
# =============================================================================


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="RL-Compatible Obsidian Tagger")
    parser.add_argument("--test", action="store_true", help="Run test tagging")
    args = parser.parse_args()

    if args.test:
        # Test with sample entry
        tagger = RLObsidianTagger()

        entry = RLKnowledgeEntry(
            id="test001",
            title="WebSocket 403 Error Fix with project_id Parameter",
            domain="websocket",
            pattern="add-missing-project-id-parameter",
            outcome=PatternOutcome.SUCCESS,
            resolution_time_minutes=15,
            recurrence_count=0,
            side_effects=SideEffectSeverity.NONE,
            source_commit="abc123",
            related_files=["backend/app/routers/websocket_handler.py"],
        )

        result = tagger.tag_knowledge_entry(entry)

        print("=" * 60)
        print("Generated Tags:")
        for tag in result.generated_tags:
            print(f"  {tag}")
        print()
        print("Markdown Output:")
        print(result.markdown_content)


if __name__ == "__main__":
    main()
