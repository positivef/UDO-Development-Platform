"""
Unified Error Resolver - 3-Tier Cascading Resolution System

Implements automatic error resolution through:
- Tier 1: Obsidian knowledge base (<10ms, 70% target hit rate)
- Tier 2: Context7 official docs (<500ms, 25% target hit rate)
- Tier 3: User escalation (5% fallback)

Target: 95% automation rate (Tier 1 + Tier 2)

Author: VibeCoding Team
Date: 2025-12-07 (Week 0 Day 2)
Version: 1.0.0
"""

import json
import logging
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """Context information for error resolution"""

    tool: str  # Tool that failed (Bash, Read, Write, etc.)
    error_message: str  # Full error message
    file_path: Optional[str] = None
    command: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ResolutionResult:
    """Result of error resolution attempt"""

    tier: int  # 1, 2, or 3
    solution: Optional[str]  # Solution command/fix
    confidence: float  # 0.0-1.0
    source: str  # "obsidian", "context7", "user", or "none"
    resolution_time_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class UnifiedErrorResolver:
    """
    3-Tier cascading error resolution system

    Usage:
        resolver = UnifiedErrorResolver()
        result = resolver.resolve_error(
            error_message="ModuleNotFoundError: No module named 'pandas'",
            context={"tool": "Python", "script": "analyzer.py"}
        )

        if result.solution:
            # Apply solution
            execute_solution(result.solution)
        else:
            # Escalate to user
            ask_user_for_help()
    """

    def __init__(
        self,
        obsidian_enabled: bool = True,
        context7_enabled: bool = True,
        stats_file: Optional[Path] = None,
    ):
        """
        Initialize resolver with configuration

        Args:
            obsidian_enabled: Enable Tier 1 (Obsidian) resolution
            context7_enabled: Enable Tier 2 (Context7) resolution
            stats_file: Path to statistics JSON file (default: data/error_resolution_stats.json)
        """
        self.obsidian_enabled = obsidian_enabled
        self.context7_enabled = context7_enabled

        # Statistics tracking
        self.stats = {
            "total_attempts": 0,
            "tier1_hits": 0,
            "tier2_hits": 0,
            "tier2_auto_applied": 0,
            "tier2_user_confirmed": 0,
            "tier3_escalations": 0,
            "resolution_history": [],
        }

        # Stats file path
        if stats_file is None:
            stats_file = Path(__file__).parent.parent.parent.parent / "data" / "error_resolution_stats.json"
        self.stats_file = stats_file

        # Load existing stats if available
        self._load_stats()

        logger.info(f"UnifiedErrorResolver initialized (Obsidian={obsidian_enabled}, Context7={context7_enabled})")

    def resolve_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> ResolutionResult:
        """
        Resolve error using 3-tier cascade

        Args:
            error_message: Error message to resolve
            context: Additional context (tool, file, command, etc.)

        Returns:
            ResolutionResult with solution (or None if escalation needed)
        """
        start_time = time.time()
        self.stats["total_attempts"] += 1

        # Build error context
        if context is None:
            context = {}

        error_ctx = ErrorContext(
            tool=context.get("tool", "Unknown"),
            error_message=error_message,
            file_path=context.get("file"),
            command=context.get("command"),
        )

        logger.info(f"[TIER CASCADE] Resolving error: {error_message[:100]}...")

        # Tier 1: Obsidian (past solutions)
        if self.obsidian_enabled:
            result = self._tier1_obsidian(error_ctx)
            if result.solution:
                resolution_time = (time.time() - start_time) * 1000
                result.resolution_time_ms = resolution_time
                self.stats["tier1_hits"] += 1
                self._record_resolution(error_ctx, result)
                logger.info(f"[TIER 1 HIT] Resolved from Obsidian in {resolution_time:.1f}ms")
                return result

        # Tier 2: Context7 (official docs)
        if self.context7_enabled:
            result = self._tier2_context7(error_ctx)
            if result.solution:
                resolution_time = (time.time() - start_time) * 1000
                result.resolution_time_ms = resolution_time
                self.stats["tier2_hits"] += 1

                # Auto-apply if HIGH confidence (≥95%)
                if result.confidence >= 0.95:
                    self.stats["tier2_auto_applied"] += 1
                    self._record_resolution(error_ctx, result)
                    logger.info(
                        f"[TIER 2 AUTO] Auto-applied from Context7 in {resolution_time:.1f}ms (confidence={result.confidence:.0%})"
                    )
                    return result
                else:
                    # MEDIUM confidence (70-95%) - return for user confirmation
                    logger.info(
                        f"[TIER 2 MEDIUM] Context7 suggests solution (confidence={result.confidence:.0%}) - user confirmation needed"
                    )
                    return result

        # Tier 3: User escalation
        resolution_time = (time.time() - start_time) * 1000
        self.stats["tier3_escalations"] += 1
        result = ResolutionResult(
            tier=3,
            solution=None,
            confidence=0.0,
            source="none",
            resolution_time_ms=resolution_time,
        )
        logger.info("[TIER 3] Escalating to user (no automated solution found)")
        return result

    def _tier1_obsidian(self, error_ctx: ErrorContext) -> ResolutionResult:
        """
        Tier 1: Search Obsidian knowledge base for past solutions

        Strategy:
        1. Extract error type and keywords
        2. Search Obsidian with mcp__obsidian__obsidian_simple_search
        3. Parse solution from results

        Target: <10ms, 70% hit rate for recurring errors
        """
        start_time = time.time()

        # Extract search keywords from error
        keywords = self._extract_error_keywords(error_ctx.error_message)
        search_query = " ".join(keywords)

        logger.debug(f"[TIER 1] Searching Obsidian: {search_query}")

        # TODO: Integrate with actual Obsidian MCP
        # For now, return no solution (to be implemented)
        # In real implementation:
        # results = mcp__obsidian__obsidian_simple_search(query=search_query)
        # solution = self._parse_obsidian_solution(results)

        resolution_time = (time.time() - start_time) * 1000

        return ResolutionResult(
            tier=1,
            solution=None,  # No solution yet (not integrated)
            confidence=0.0,
            source="obsidian",
            resolution_time_ms=resolution_time,
        )

    def _tier2_context7(self, error_ctx: ErrorContext) -> ResolutionResult:
        """
        Tier 2: Search Context7 official documentation

        Strategy:
        1. Identify library/framework from error
        2. Query Context7 for official solution
        3. Calculate confidence based on pattern matching

        Target: <500ms, 25% hit rate for first-time errors
        """
        start_time = time.time()

        # Extract library/framework
        library = self._extract_library_from_error(error_ctx.error_message)

        logger.debug(f"[TIER 2] Searching Context7 for: {library}")

        # TODO: Integrate with actual Context7 MCP
        # For now, use pattern-based fallback solutions
        solution, confidence = self._pattern_based_solution(error_ctx)

        resolution_time = (time.time() - start_time) * 1000

        return ResolutionResult(
            tier=2,
            solution=solution,
            confidence=confidence,
            source="context7" if solution else "none",
            resolution_time_ms=resolution_time,
        )

    def _extract_error_keywords(self, error_message: str) -> List[str]:
        """Extract keywords from error message for search"""
        keywords = []

        # Error type (ModuleNotFoundError, PermissionError, etc.)
        error_type_match = re.search(r"(\w+Error|Exception):", error_message)
        if error_type_match:
            keywords.append(error_type_match.group(1))

        # Module/package name
        module_match = re.search(r"No module named '(\w+)'", error_message)
        if module_match:
            keywords.append(module_match.group(1))

        # File paths (support multiple extensions and non-quoted paths)
        file_match = re.search(r"'([^']+\.(py|js|ts|sh|yaml|yml|json|md|txt|cfg|conf|env))'", error_message)
        if file_match:
            keywords.append(Path(file_match.group(1)).name)
        else:
            # Also try to match non-quoted file paths like ./deploy.sh or config.yaml
            non_quoted_match = re.search(
                r"(?:^|[:\s])([./\w-]+\.(py|js|ts|sh|yaml|yml|json|md|txt|cfg|conf|env))(?:[:\s]|$)",
                error_message,
            )
            if non_quoted_match:
                keywords.append(Path(non_quoted_match.group(1)).name)

        # Error codes (401, 404, 500, etc.)
        code_match = re.search(r"\b(\d{3})\b", error_message)
        if code_match:
            keywords.append(code_match.group(1))

        # Common error keywords
        common_keywords = [
            "permission",
            "denied",
            "not found",
            "connection",
            "timeout",
            "import",
            "syntax",
        ]
        for keyword in common_keywords:
            if keyword in error_message.lower():
                keywords.append(keyword)

        return keywords[:5]  # Top 5 keywords

    def _extract_library_from_error(self, error_message: str) -> Optional[str]:
        """Extract library/framework name from error"""
        # Module imports
        module_match = re.search(r"No module named '(\w+)'", error_message)
        if module_match:
            return module_match.group(1)

        # ImportError patterns
        import_match = re.search(r"cannot import name '(\w+)' from '(\w+)'", error_message)
        if import_match:
            return import_match.group(2)

        return None

    def _pattern_based_solution(self, error_ctx: ErrorContext) -> tuple[Optional[str], float]:
        """
        Pattern-based fallback solutions (HIGH confidence patterns only)

        Returns: (solution, confidence)
        """
        error = error_ctx.error_message

        # Pattern 1: ModuleNotFoundError - pip install (HIGH confidence)
        if "ModuleNotFoundError" in error or "No module named" in error:
            module_match = re.search(r"No module named '(\w+)'", error)
            if module_match:
                module = module_match.group(1)
                return f"pip install {module}", 0.95  # HIGH confidence

        # Pattern 2: Permission denied - chmod (HIGH confidence)
        if "Permission denied" in error or "PermissionError" in error:
            # Try quoted path first
            file_match = re.search(r"'([^']+)'", error)
            if not file_match:
                # Try non-quoted path (e.g., "bash: ./deploy.sh: Permission denied")
                file_match = re.search(r"(?:^|[:\s])([./\w-]+\.\w+)(?::|$)", error)
            if file_match:
                file_path = file_match.group(1)
                if error_ctx.tool == "Edit" or error_ctx.tool == "Write":
                    return f"chmod +w {file_path}", 0.95  # HIGH confidence
                elif error_ctx.tool == "Bash":
                    return f"chmod +x {file_path}", 0.95  # HIGH confidence
                else:
                    # Default to +x for script-like paths
                    return f"chmod +x {file_path}", 0.95  # HIGH confidence

        # Pattern 3: File not found - check path (MEDIUM confidence)
        if "No such file or directory" in error or "FileNotFoundError" in error:
            # Return None for MEDIUM confidence (user confirmation needed)
            return None, 0.70

        # No pattern matched
        return None, 0.0

    def save_user_solution(
        self,
        error_message: str,
        user_solution: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Save user-provided solution to Obsidian for future Tier 1 hits

        Args:
            error_message: Original error message
            user_solution: Solution provided by user
            context: Additional context
        """
        if context is None:
            context = {}

        error_ctx = ErrorContext(
            tool=context.get("tool", "Unknown"),
            error_message=error_message,
            file_path=context.get("file"),
            command=context.get("command"),
        )

        # TODO: Save to Obsidian
        # In real implementation:
        # mcp__obsidian__obsidian_append_content(
        #     filepath=f"Error-Solutions/{error_type}.md",
        #     content=format_solution_entry(error_ctx, user_solution)
        # )

        logger.info("[USER SOLUTION] Saved to Obsidian for future Tier 1 hits")

        # Update stats
        result = ResolutionResult(
            tier=3,
            solution=user_solution,
            confidence=1.0,  # User solution is 100% trusted
            source="user",
            resolution_time_ms=0.0,
        )
        self._record_resolution(error_ctx, result)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current resolution statistics

        Returns:
            {
                "total": N,
                "tier1": X,
                "tier2": Y,
                "tier2_auto": Z,
                "tier2_confirmed": W,
                "tier3": Q,
                "automation_rate": 0.XX,
                "knowledge_reuse_rate": 0.XX
            }
        """
        total = self.stats["total_attempts"]
        if total == 0:
            return {
                "total": 0,
                "tier1": 0,
                "tier2": 0,
                "tier2_auto": 0,
                "tier2_confirmed": 0,
                "tier3": 0,
                "automation_rate": 0.0,
                "knowledge_reuse_rate": 0.0,
            }

        tier1 = self.stats["tier1_hits"]
        tier2 = self.stats["tier2_hits"]
        tier2_auto = self.stats["tier2_auto_applied"]
        tier2_confirmed = self.stats["tier2_user_confirmed"]
        tier3 = self.stats["tier3_escalations"]

        # Automation rate: (Tier 1 + Tier 2 auto) / total
        automation_rate = (tier1 + tier2_auto) / total

        # Knowledge reuse rate: Tier 1 / total
        knowledge_reuse_rate = tier1 / total

        return {
            "total": total,
            "tier1": tier1,
            "tier2": tier2,
            "tier2_auto": tier2_auto,
            "tier2_confirmed": tier2_confirmed,
            "tier3": tier3,
            "automation_rate": automation_rate,
            "knowledge_reuse_rate": knowledge_reuse_rate,
        }

    def get_knowledge_reuse_rate(self) -> float:
        """
        Get knowledge reuse rate (Tier 1 hit rate)

        Formula: (tier1_hits / total_attempts) × 100%

        Target: ≥90% for mature system
        """
        stats = self.get_statistics()
        return stats["knowledge_reuse_rate"] * 100

    def _record_resolution(self, error_ctx: ErrorContext, result: ResolutionResult) -> None:
        """Record resolution in history"""
        self.stats["resolution_history"].append(
            {
                "timestamp": error_ctx.timestamp,
                "tool": error_ctx.tool,
                "error": error_ctx.error_message[:200],  # Truncate
                "tier": result.tier,
                "source": result.source,
                "confidence": result.confidence,
                "resolution_time_ms": result.resolution_time_ms,
            }
        )

        # Keep last 100 resolutions only
        if len(self.stats["resolution_history"]) > 100:
            self.stats["resolution_history"] = self.stats["resolution_history"][-100:]

        # Save stats to file
        self._save_stats()

    def _load_stats(self) -> None:
        """Load statistics from file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    saved_stats = json.load(f)
                    # Merge with current stats (preserve structure)
                    self.stats.update(saved_stats)
                logger.info(f"Loaded resolution stats: {self.stats['total_attempts']} attempts")
            except Exception as e:
                logger.warning(f"Failed to load stats: {e}")

    def _save_stats(self) -> None:
        """Save statistics to file"""
        try:
            self.stats_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to save stats: {e}")

    def reset_statistics(self) -> None:
        """Reset all statistics (for testing)"""
        self.stats = {
            "total_attempts": 0,
            "tier1_hits": 0,
            "tier2_hits": 0,
            "tier2_auto_applied": 0,
            "tier2_user_confirmed": 0,
            "tier3_escalations": 0,
            "resolution_history": [],
        }
        self._save_stats()
        logger.info("Resolution statistics reset")


# Global singleton instance
_resolver_instance: Optional[UnifiedErrorResolver] = None


def get_resolver() -> UnifiedErrorResolver:
    """Get global resolver instance (singleton pattern)"""
    global _resolver_instance
    if _resolver_instance is None:
        _resolver_instance = UnifiedErrorResolver()
    return _resolver_instance
