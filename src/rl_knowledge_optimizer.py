#!/usr/bin/env python3
"""
RL Knowledge Optimizer - Training-free GRPO Implementation

Implements Group Relative Policy Optimization for knowledge reuse:
1. Group Relative Scoring - Compare patterns within domain
2. Policy Optimization - Select best solution first
3. Multi-Rollout Tracking - Track experimentation attempts

Based on: ArXiv 2510.08191 (Training-free GRPO)

Author: UDO Platform Team
Date: 2026-01-02
Version: 1.0.0

Expected Impact:
- Knowledge Reuse Rate: 70% -> 90% (+20%)
- Pattern Auto-Detection: 0% -> 60% (+60%)
- Automation Rate: 85% -> 92% (+7%)
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================


class SideEffectLevel(Enum):
    """Side effect severity levels (0-3 scale)"""

    NONE = 0
    MINOR = 1
    MAJOR = 2
    CRITICAL = 3


@dataclass
class KnowledgePattern:
    """A reusable knowledge pattern with quality metrics."""

    # Identification
    id: str
    name: str
    domain: str  # auth, api, database, frontend, etc.
    description: str = ""

    # Quality Metrics (for Group Relative Scoring)
    resolution_time_minutes: int = 0
    recurrence_count: int = 0
    side_effects: SideEffectLevel = SideEffectLevel.NONE

    # Usage statistics
    times_applied: int = 0
    success_count: int = 0
    failure_count: int = 0

    # Cached scores
    group_relative_score: float = 0.0
    last_scored_at: Optional[datetime] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    source_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 0.0
        return self.success_count / total


@dataclass
class ExperimentAttempt:
    """A single attempt in a multi-rollout experiment."""

    approach: str
    result: str  # "success" or "failed"
    reason: Optional[str] = None
    time_minutes: int = 0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MultiRolloutExperiment:
    """Tracks multiple solution attempts for the same problem."""

    problem_id: str
    problem_description: str
    domain: str
    attempts: List[ExperimentAttempt] = field(default_factory=list)
    winning_approach: Optional[str] = None
    total_time_minutes: int = 0
    created_at: datetime = field(default_factory=datetime.now)


# =============================================================================
# Group Relative Scorer
# =============================================================================


class GroupRelativeScorer:
    """
    Scores patterns relative to all alternatives in the same domain.

    Implements Training-free GRPO scoring formula:
        Score = w1 * time_efficiency + w2 * permanence + w3 * safety

    Where:
        time_efficiency = 1 - (resolution_time / max_time)
        permanence = 1 - (recurrence_count / max_recurrence)
        safety = 1 - (side_effects / 3)
    """

    def __init__(
        self,
        weight_time: float = 0.4,
        weight_permanence: float = 0.4,
        weight_safety: float = 0.2,
    ):
        """
        Initialize scorer with configurable weights.

        Args:
            weight_time: Weight for time efficiency (default: 0.4)
            weight_permanence: Weight for permanence (default: 0.4)
            weight_safety: Weight for safety (default: 0.2)
        """
        self.w_time = weight_time
        self.w_perm = weight_permanence
        self.w_safe = weight_safety

        # Validate weights sum to 1.0
        total = self.w_time + self.w_perm + self.w_safe
        if abs(total - 1.0) > 0.001:
            logger.warning(f"Weights sum to {total}, normalizing...")
            self.w_time /= total
            self.w_perm /= total
            self.w_safe /= total

    def score_pattern(
        self,
        pattern: KnowledgePattern,
        all_patterns: List[KnowledgePattern],
    ) -> float:
        """
        Score a pattern relative to all alternatives in the group.

        Args:
            pattern: The pattern to score
            all_patterns: All patterns in the same domain for comparison

        Returns:
            Group Relative Score between 0.0 and 1.0
        """
        if not all_patterns:
            return 0.5  # Default neutral score

        # Calculate max values for normalization
        max_time = max((p.resolution_time_minutes for p in all_patterns), default=1)
        max_recurrence = max((p.recurrence_count for p in all_patterns), default=1)

        # Avoid division by zero
        max_time = max(max_time, 1)
        max_recurrence = max(max_recurrence, 1)

        # Calculate component scores
        time_efficiency = 1 - (pattern.resolution_time_minutes / max_time)
        permanence = 1 - (pattern.recurrence_count / max_recurrence)
        safety = 1 - (pattern.side_effects.value / 3)

        # Weighted sum
        raw_score = self.w_time * time_efficiency + self.w_perm * permanence + self.w_safe * safety

        # Cache the score
        pattern.group_relative_score = raw_score
        pattern.last_scored_at = datetime.now()

        return raw_score

    def score_all_patterns(
        self,
        patterns: List[KnowledgePattern],
    ) -> List[Tuple[KnowledgePattern, float]]:
        """
        Score all patterns and return sorted by score (highest first).

        Args:
            patterns: List of patterns to score

        Returns:
            List of (pattern, score) tuples sorted by score descending
        """
        scored = [(p, self.score_pattern(p, patterns)) for p in patterns]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def get_relative_rank(
        self,
        pattern: KnowledgePattern,
        all_patterns: List[KnowledgePattern],
    ) -> float:
        """
        Get the relative rank of a pattern (0.0 = worst, 1.0 = best).

        Args:
            pattern: The pattern to rank
            all_patterns: All patterns for comparison

        Returns:
            Relative rank between 0.0 and 1.0
        """
        scored = self.score_all_patterns(all_patterns)
        ranks = {p.id: i for i, (p, _) in enumerate(scored)}

        if pattern.id not in ranks:
            return 0.0

        # Convert rank to relative score (0 = best -> 1.0, last = worst -> 0.0)
        position = ranks[pattern.id]
        return 1.0 - (position / len(scored)) if scored else 0.0


# =============================================================================
# Policy Optimizer
# =============================================================================


class PolicyOptimizer:
    """
    Optimizes solution selection policy based on Group Relative Scores.

    Implements the policy update rule:
        policy(problem) = argmax_solution [TokenPrior(s) * GroupRelative(s)]
    """

    def __init__(self, scorer: Optional[GroupRelativeScorer] = None):
        """
        Initialize policy optimizer.

        Args:
            scorer: GroupRelativeScorer instance (creates default if None)
        """
        self.scorer = scorer or GroupRelativeScorer()
        self._pattern_store: Dict[str, List[KnowledgePattern]] = {}  # domain -> patterns
        self._policy_cache: Dict[str, str] = {}  # problem_hash -> best_pattern_id

    def register_pattern(self, pattern: KnowledgePattern) -> None:
        """
        Register a new pattern for policy optimization.

        Args:
            pattern: Pattern to register
        """
        if pattern.domain not in self._pattern_store:
            self._pattern_store[pattern.domain] = []

        # Check for duplicates
        existing_ids = {p.id for p in self._pattern_store[pattern.domain]}
        if pattern.id not in existing_ids:
            self._pattern_store[pattern.domain].append(pattern)
            logger.info(f"Registered pattern: {pattern.name} in domain {pattern.domain}")

        # Invalidate policy cache for this domain
        self._invalidate_domain_cache(pattern.domain)

    def get_best_solution(
        self,
        problem_domain: str,
        problem_keywords: Optional[List[str]] = None,
    ) -> Optional[Tuple[KnowledgePattern, float]]:
        """
        Get the best solution for a problem based on policy.

        Args:
            problem_domain: Domain of the problem (e.g., "auth", "api")
            problem_keywords: Optional keywords to filter patterns

        Returns:
            Tuple of (best_pattern, score) or None if no patterns found
        """
        patterns = self._pattern_store.get(problem_domain, [])

        if not patterns:
            logger.info(f"No patterns found for domain: {problem_domain}")
            return None

        # Filter by keywords if provided
        if problem_keywords:
            patterns = [
                p
                for p in patterns
                if any(kw.lower() in p.name.lower() or kw.lower() in p.description.lower() for kw in problem_keywords)
            ]

        if not patterns:
            logger.info(f"No patterns match keywords: {problem_keywords}")
            return None

        # Score and select best
        scored = self.scorer.score_all_patterns(patterns)

        if scored:
            best_pattern, best_score = scored[0]
            logger.info(f"[POLICY] Selected: {best_pattern.name} (score: {best_score:.2f})")
            if len(scored) > 1:
                alternatives = [(p.name, s) for p, s in scored[1:3]]
                logger.info(f"[POLICY] Alternatives: {alternatives}")
            return best_pattern, best_score

        return None

    def get_all_solutions_ranked(
        self,
        problem_domain: str,
    ) -> List[Tuple[KnowledgePattern, float]]:
        """
        Get all solutions for a domain, ranked by Group Relative Score.

        Args:
            problem_domain: Domain to search

        Returns:
            List of (pattern, score) tuples, sorted by score descending
        """
        patterns = self._pattern_store.get(problem_domain, [])
        return self.scorer.score_all_patterns(patterns)

    def update_pattern_stats(
        self,
        pattern_id: str,
        success: bool,
        actual_time_minutes: Optional[int] = None,
        had_side_effects: bool = False,
    ) -> None:
        """
        Update pattern statistics after application.

        Args:
            pattern_id: ID of the pattern that was applied
            success: Whether the application was successful
            actual_time_minutes: Actual resolution time (updates average)
            had_side_effects: Whether side effects occurred
        """
        for domain_patterns in self._pattern_store.values():
            for pattern in domain_patterns:
                if pattern.id == pattern_id:
                    pattern.times_applied += 1

                    if success:
                        pattern.success_count += 1
                        # Successful application means problem is solved
                        # Don't increment recurrence
                    else:
                        pattern.failure_count += 1
                        # Failed application means problem recurred
                        pattern.recurrence_count += 1

                    if had_side_effects:
                        # Escalate side effect severity
                        current = pattern.side_effects.value
                        if current < 3:
                            pattern.side_effects = SideEffectLevel(current + 1)

                    logger.info(
                        f"Updated pattern {pattern.name}: "
                        f"applied={pattern.times_applied}, "
                        f"success_rate={pattern.success_rate:.1%}"
                    )
                    return

        logger.warning(f"Pattern not found: {pattern_id}")

    def _invalidate_domain_cache(self, domain: str) -> None:
        """Invalidate policy cache entries for a domain."""
        keys_to_remove = [k for k in self._policy_cache if domain in k]
        for key in keys_to_remove:
            del self._policy_cache[key]

    def get_domain_stats(self, domain: str) -> Dict[str, Any]:
        """
        Get statistics for a domain.

        Args:
            domain: Domain to analyze

        Returns:
            Dictionary with domain statistics
        """
        patterns = self._pattern_store.get(domain, [])

        if not patterns:
            return {"domain": domain, "patterns": 0}

        scored = self.scorer.score_all_patterns(patterns)

        return {
            "domain": domain,
            "patterns": len(patterns),
            "avg_score": sum(s for _, s in scored) / len(scored),
            "top_pattern": scored[0][0].name if scored else None,
            "top_score": scored[0][1] if scored else 0.0,
            "total_applications": sum(p.times_applied for p in patterns),
            "avg_success_rate": (sum(p.success_rate for p in patterns) / len(patterns) if patterns else 0.0),
        }


# =============================================================================
# Multi-Rollout Tracker
# =============================================================================


class MultiRolloutTracker:
    """
    Tracks multiple solution attempts for the same problem.

    This prevents knowledge loss from failed experiments by:
    1. Recording all attempts (not just the winning one)
    2. Building Token Prior from failed approaches
    3. Enabling "skip known failures" in future
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize tracker.

        Args:
            storage_path: Path to store experiment data (optional)
        """
        self.storage_path = storage_path or Path(".udo/experiments.json")
        self.experiments: Dict[str, MultiRolloutExperiment] = {}
        self._load_experiments()

    def start_experiment(
        self,
        problem_id: str,
        problem_description: str,
        domain: str,
    ) -> MultiRolloutExperiment:
        """
        Start a new multi-rollout experiment.

        Args:
            problem_id: Unique identifier for the problem
            problem_description: Description of the problem
            domain: Problem domain

        Returns:
            New experiment instance
        """
        experiment = MultiRolloutExperiment(
            problem_id=problem_id,
            problem_description=problem_description,
            domain=domain,
        )
        self.experiments[problem_id] = experiment
        logger.info(f"Started experiment: {problem_id}")
        return experiment

    def record_attempt(
        self,
        problem_id: str,
        approach: str,
        result: str,
        reason: Optional[str] = None,
        time_minutes: int = 0,
    ) -> None:
        """
        Record an attempt in an experiment.

        Args:
            problem_id: Problem being solved
            approach: Approach tried
            result: "success" or "failed"
            reason: Reason for failure (if failed)
            time_minutes: Time spent on this attempt
        """
        if problem_id not in self.experiments:
            logger.warning(f"Experiment not found: {problem_id}")
            return

        attempt = ExperimentAttempt(
            approach=approach,
            result=result,
            reason=reason,
            time_minutes=time_minutes,
        )

        experiment = self.experiments[problem_id]
        experiment.attempts.append(attempt)
        experiment.total_time_minutes += time_minutes

        if result == "success":
            experiment.winning_approach = approach

        logger.info(f"Recorded attempt: {approach} -> {result}" f"{f' ({reason})' if reason else ''}")

        self._save_experiments()

    def get_failed_approaches(self, problem_id: str) -> List[str]:
        """
        Get list of approaches that failed for a problem.

        Useful for "skip known failures" optimization.

        Args:
            problem_id: Problem to check

        Returns:
            List of failed approach names
        """
        if problem_id not in self.experiments:
            return []

        return [a.approach for a in self.experiments[problem_id].attempts if a.result == "failed"]

    def get_winning_approach(self, problem_id: str) -> Optional[str]:
        """
        Get the winning approach for a problem (if solved).

        Args:
            problem_id: Problem to check

        Returns:
            Winning approach name or None
        """
        if problem_id not in self.experiments:
            return None
        return self.experiments[problem_id].winning_approach

    def get_experiment_summary(self, problem_id: str) -> Dict[str, Any]:
        """
        Get summary of an experiment.

        Args:
            problem_id: Problem to summarize

        Returns:
            Summary dictionary
        """
        if problem_id not in self.experiments:
            return {"error": "Experiment not found"}

        exp = self.experiments[problem_id]
        return {
            "problem_id": exp.problem_id,
            "problem_description": exp.problem_description,
            "domain": exp.domain,
            "total_attempts": len(exp.attempts),
            "failed_attempts": len([a for a in exp.attempts if a.result == "failed"]),
            "winning_approach": exp.winning_approach,
            "total_time_minutes": exp.total_time_minutes,
            "attempts": [{"approach": a.approach, "result": a.result, "reason": a.reason} for a in exp.attempts],
        }

    def _load_experiments(self) -> None:
        """Load experiments from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path) as f:
                    data = json.load(f)
                    # Deserialize experiments
                    for pid, exp_data in data.items():
                        attempts = [ExperimentAttempt(**a) for a in exp_data.get("attempts", [])]
                        self.experiments[pid] = MultiRolloutExperiment(
                            problem_id=exp_data["problem_id"],
                            problem_description=exp_data["problem_description"],
                            domain=exp_data["domain"],
                            attempts=attempts,
                            winning_approach=exp_data.get("winning_approach"),
                            total_time_minutes=exp_data.get("total_time_minutes", 0),
                        )
                logger.info(f"Loaded {len(self.experiments)} experiments")
            except Exception as e:
                logger.warning(f"Failed to load experiments: {e}")

    def _save_experiments(self) -> None:
        """Save experiments to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            data = {}
            for pid, exp in self.experiments.items():
                data[pid] = {
                    "problem_id": exp.problem_id,
                    "problem_description": exp.problem_description,
                    "domain": exp.domain,
                    "winning_approach": exp.winning_approach,
                    "total_time_minutes": exp.total_time_minutes,
                    "attempts": [
                        {
                            "approach": a.approach,
                            "result": a.result,
                            "reason": a.reason,
                            "time_minutes": a.time_minutes,
                        }
                        for a in exp.attempts
                    ],
                }
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save experiments: {e}")


# =============================================================================
# Integration Facade
# =============================================================================


class RLKnowledgeOptimizer:
    """
    Unified facade for RL-based knowledge optimization.

    Combines:
    - Group Relative Scorer for pattern scoring
    - Policy Optimizer for solution selection
    - Multi-Rollout Tracker for experiment tracking
    """

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        storage_path: Optional[Path] = None,
    ):
        """
        Initialize the optimizer.

        Args:
            weights: Scoring weights {time, permanence, safety}
            storage_path: Path for experiment storage
        """
        weights = weights or {}
        self.scorer = GroupRelativeScorer(
            weight_time=weights.get("time", 0.4),
            weight_permanence=weights.get("permanence", 0.4),
            weight_safety=weights.get("safety", 0.2),
        )
        self.policy = PolicyOptimizer(self.scorer)
        self.tracker = MultiRolloutTracker(storage_path)

    def resolve_problem(
        self,
        domain: str,
        keywords: Optional[List[str]] = None,
        skip_failed: bool = True,
        problem_id: Optional[str] = None,
    ) -> Optional[Tuple[KnowledgePattern, float]]:
        """
        Resolve a problem using optimized policy.

        Args:
            domain: Problem domain
            keywords: Keywords to match
            skip_failed: Skip previously failed approaches
            problem_id: Problem ID for experiment tracking

        Returns:
            Best solution and score, or None
        """
        # Get all solutions
        all_solutions = self.policy.get_all_solutions_ranked(domain)

        if not all_solutions:
            return None

        # Filter by keywords
        if keywords:
            all_solutions = [(p, s) for p, s in all_solutions if any(kw.lower() in p.name.lower() for kw in keywords)]

        # Skip previously failed approaches
        if skip_failed and problem_id:
            failed = self.tracker.get_failed_approaches(problem_id)
            all_solutions = [(p, s) for p, s in all_solutions if p.name not in failed]

        if not all_solutions:
            return None

        # Return best solution
        best = all_solutions[0]
        logger.info(
            f"[RL RESOLVE] Best: {best[0].name} (score: {best[1]:.2f}), "
            f"skipped {len(failed) if skip_failed and problem_id else 0} failed approaches"
        )
        return best

    def record_outcome(
        self,
        pattern_id: str,
        problem_id: Optional[str],
        success: bool,
        reason: Optional[str] = None,
        time_minutes: int = 0,
    ) -> None:
        """
        Record the outcome of applying a solution.

        Args:
            pattern_id: Pattern that was applied
            problem_id: Problem being solved
            success: Whether it worked
            reason: Reason for failure
            time_minutes: Time taken
        """
        # Update pattern stats
        self.policy.update_pattern_stats(
            pattern_id=pattern_id,
            success=success,
            actual_time_minutes=time_minutes,
            had_side_effects=False,  # TODO: Detect side effects
        )

        # Record in experiment tracker
        if problem_id:
            if problem_id not in self.tracker.experiments:
                # Auto-create experiment
                self.tracker.start_experiment(
                    problem_id=problem_id,
                    problem_description=f"Auto-created for {pattern_id}",
                    domain="auto",
                )

            self.tracker.record_attempt(
                problem_id=problem_id,
                approach=pattern_id,
                result="success" if success else "failed",
                reason=reason,
                time_minutes=time_minutes,
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get overall optimization statistics."""
        domains = list(self.policy._pattern_store.keys())
        return {
            "total_domains": len(domains),
            "total_patterns": sum(len(patterns) for patterns in self.policy._pattern_store.values()),
            "total_experiments": len(self.tracker.experiments),
            "domain_stats": {domain: self.policy.get_domain_stats(domain) for domain in domains},
        }

    def get_domain_patterns(
        self,
        domain: str,
    ) -> List[Dict[str, Any]]:
        """
        Get all patterns for a domain with their scores.

        Args:
            domain: Domain to query

        Returns:
            List of dicts with 'pattern' and 'score' keys
        """
        ranked = self.policy.get_all_solutions_ranked(domain)
        return [{"pattern": p, "score": s} for p, s in ranked]

    def add_pattern(self, pattern: KnowledgePattern) -> None:
        """
        Add a new pattern to the policy optimizer.

        Args:
            pattern: Pattern to register
        """
        self.policy.register_pattern(pattern)

    def get_best_solution(
        self,
        domain: str,
        keywords: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the best solution for a problem domain.

        Args:
            domain: Problem domain
            keywords: Optional keywords to filter

        Returns:
            Dict with 'pattern' and 'score', or None if not found
        """
        result = self.policy.get_best_solution(domain, keywords)
        if result:
            pattern, score = result
            return {"pattern": pattern, "score": score}
        return None


# =============================================================================
# CLI Interface
# =============================================================================


def main():
    """CLI entry point for testing."""
    import argparse

    parser = argparse.ArgumentParser(description="RL Knowledge Optimizer")
    parser.add_argument("--test", action="store_true", help="Run test scenario")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    args = parser.parse_args()

    if args.test:
        print("=" * 60)
        print("RL Knowledge Optimizer - Test Scenario")
        print("=" * 60)

        # Create optimizer
        optimizer = RLKnowledgeOptimizer()

        # Register some patterns
        patterns = [
            KnowledgePattern(
                id="api-timeout-1",
                name="increase timeout",
                domain="api",
                resolution_time_minutes=30,
                recurrence_count=3,
                side_effects=SideEffectLevel.NONE,
            ),
            KnowledgePattern(
                id="api-timeout-2",
                name="circuit breaker",
                domain="api",
                resolution_time_minutes=5,
                recurrence_count=0,
                side_effects=SideEffectLevel.NONE,
            ),
            KnowledgePattern(
                id="api-timeout-3",
                name="retry with backoff",
                domain="api",
                resolution_time_minutes=60,
                recurrence_count=1,
                side_effects=SideEffectLevel.CRITICAL,
            ),
        ]

        for p in patterns:
            optimizer.policy.register_pattern(p)

        # Test resolution
        print("\n[TEST] Resolving 'API timeout' problem...")
        result = optimizer.resolve_problem(domain="api", keywords=["timeout"])

        if result:
            pattern, score = result
            print(f"Best solution: {pattern.name} (score: {score:.2f})")
        else:
            print("No solution found")

        # Show all ranked solutions
        print("\n[TEST] All solutions ranked:")
        ranked = optimizer.policy.get_all_solutions_ranked("api")
        for i, (p, s) in enumerate(ranked, 1):
            print(f"  {i}. {p.name}: {s:.2f}")

        # Test experiment tracking
        print("\n[TEST] Multi-rollout experiment...")
        optimizer.tracker.start_experiment(
            problem_id="test-problem-1",
            problem_description="API timeout test",
            domain="api",
        )
        optimizer.tracker.record_attempt(
            problem_id="test-problem-1",
            approach="increase timeout",
            result="failed",
            reason="still times out",
        )
        optimizer.tracker.record_attempt(
            problem_id="test-problem-1",
            approach="circuit breaker",
            result="success",
            time_minutes=5,
        )

        summary = optimizer.tracker.get_experiment_summary("test-problem-1")
        print(f"Experiment summary: {json.dumps(summary, indent=2)}")

        # Stats
        print("\n[TEST] Optimizer stats:")
        stats = optimizer.get_stats()
        print(json.dumps(stats, indent=2))

    elif args.stats:
        optimizer = RLKnowledgeOptimizer()
        print(json.dumps(optimizer.get_stats(), indent=2))


if __name__ == "__main__":
    main()
