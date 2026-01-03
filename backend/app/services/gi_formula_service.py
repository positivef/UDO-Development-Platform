"""
GI Formula Service

Genius Insight Formula - 5-stage insight generation system with Sequential MCP integration.

Stages:
1. Observation: Extract key facts and constraints
2. Connection: Find relationships between facts
3. Pattern: Identify recurring patterns and trends
4. Synthesis: Combine insights into actionable solution
5. Bias Check: Validate against cognitive biases
"""

import logging
import asyncio
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any

from ..models.gi_formula import (
    StageType,
    StageResult,
    BiasCheckResult,
    GIFormulaRequest,
    GIFormulaResult,
    GIInsightSummary,
)

logger = logging.getLogger(__name__)


class GIFormulaService:
    """
    Service for generating insights using Genius Insight Formula

    Features:
    - 5-stage insight generation (O -> C -> P -> S -> B)
    - Sequential MCP integration for structured reasoning
    - 3-tier caching (Memory -> Redis -> SQLite)
    - Obsidian auto-save
    - Performance target: <30 seconds
    - Graceful degradation on MCP failures
    """

    def __init__(
        self, sequential_mcp=None, obsidian_service=None, cache_service=None, config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize GI Formula Service

        Args:
            sequential_mcp: Sequential MCP client for structured reasoning
            obsidian_service: ObsidianService for knowledge sync
            cache_service: Cache service (Redis/SQLite)
            config: Service configuration
        """
        self.sequential_mcp = sequential_mcp
        self.obsidian_service = obsidian_service
        self.cache_service = cache_service
        self.config = config or {}

        # In-memory cache for recent insights
        self._memory_cache: Dict[str, GIFormulaResult] = {}
        self._max_memory_cache = self.config.get("max_memory_cache", 10)

        # Stage configurations
        self._stage_configs = {
            StageType.OBSERVATION: {
                "prompt_template": "Extract key facts and constraints from: {problem}. Context: {context}",
                "timeout": 5000,  # ms
            },
            StageType.CONNECTION: {
                "prompt_template": "Find relationships between these observations: {observations}",
                "timeout": 6000,
            },
            StageType.PATTERN: {
                "prompt_template": "Identify patterns and trends from connections: {connections}",
                "timeout": 6000,
            },
            StageType.SYNTHESIS: {
                "prompt_template": "Synthesize actionable insight from patterns: {patterns}",
                "timeout": 7000,
            },
            StageType.BIAS_CHECK: {
                "prompt_template": "Check for cognitive biases in insight: {insight}",
                "timeout": 6000,
            },
        }

        logger.info("GIFormulaService initialized")

    async def generate_insight(self, request: GIFormulaRequest) -> GIFormulaResult:
        """
        Generate insight using 5-stage GI Formula

        Args:
            request: GI Formula request with problem and context

        Returns:
            Complete GI Formula result with all stages

        Raises:
            ValueError: If request validation fails
            RuntimeError: If insight generation fails
        """
        start_time = datetime.now()

        try:
            # Generate insight ID
            insight_id = self._generate_insight_id(request.problem)

            # Check cache (3-tier: Memory -> Redis -> SQLite)
            cached_result = await self._get_cached_insight(insight_id)
            if cached_result:
                logger.info(f"Cache hit for insight {insight_id}")
                return cached_result

            logger.info(f"Generating insight {insight_id} for problem: {request.problem[:50]}...")

            # Execute 5 stages sequentially
            stages: Dict[str, StageResult] = {}

            # Stage 1: Observation
            stages["observation"] = await self._execute_stage(
                StageType.OBSERVATION, problem=request.problem, context=request.context or {}
            )

            # Stage 2: Connection
            stages["connection"] = await self._execute_stage(StageType.CONNECTION, observations=stages["observation"].content)

            # Stage 3: Pattern
            stages["pattern"] = await self._execute_stage(StageType.PATTERN, connections=stages["connection"].content)

            # Stage 4: Synthesis
            stages["synthesis"] = await self._execute_stage(StageType.SYNTHESIS, patterns=stages["pattern"].content)

            # Stage 5: Bias Check
            bias_check_result = await self._execute_bias_check(insight=stages["synthesis"].content)

            stages["bias_check"] = StageResult(
                stage=StageType.BIAS_CHECK,
                content=f"Biases detected: {len(bias_check_result.biases_detected)}",
                metadata={
                    "biases": bias_check_result.biases_detected,
                    "strategies": bias_check_result.mitigation_strategies,
                },
                duration_ms=0,  # Will be set below
            )

            # Calculate total duration
            end_time = datetime.now()
            total_duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Update bias check duration
            stages["bias_check"].duration_ms = total_duration_ms - sum(
                s.duration_ms for s in stages.values() if s.stage != StageType.BIAS_CHECK
            )

            # Build result
            result = GIFormulaResult(
                id=insight_id,
                problem=request.problem,
                stages=stages,
                final_insight=stages["synthesis"].content,
                bias_check=bias_check_result,
                total_duration_ms=total_duration_ms,
                created_at=start_time,
                project=request.project,
                metadata={
                    "context": request.context,
                    "stage_durations": {stage_type: stage.duration_ms for stage_type, stage in stages.items()},
                },
            )

            # Cache result (async, don't wait)
            asyncio.create_task(self._cache_insight(insight_id, result))

            # Save to Obsidian (async, don't wait)
            asyncio.create_task(self._save_to_obsidian(result))

            logger.info(
                f"Generated insight {insight_id} in {total_duration_ms}ms "
                f"(bias confidence: {bias_check_result.confidence_score:.2f})"
            )

            return result

        except Exception as e:
            logger.error(f"Failed to generate insight: {e}", exc_info=True)
            raise RuntimeError(f"Insight generation failed: {str(e)}") from e

    async def get_insight(self, insight_id: str) -> Optional[GIFormulaResult]:
        """
        Retrieve insight by ID

        Args:
            insight_id: Unique insight identifier

        Returns:
            GIFormulaResult if found, None otherwise
        """
        try:
            return await self._get_cached_insight(insight_id)
        except Exception as e:
            logger.error(f"Failed to retrieve insight {insight_id}: {e}")
            return None

    async def list_insights(self, project: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[GIInsightSummary]:
        """
        List recent insights

        Args:
            project: Filter by project name
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of insight summaries
        """
        try:
            # Get from memory cache first
            insights = list(self._memory_cache.values())

            # Filter by project if specified
            if project:
                insights = [i for i in insights if i.project == project]

            # Sort by creation time (newest first)
            insights.sort(key=lambda x: x.created_at, reverse=True)

            # Paginate
            insights = insights[offset : offset + limit]

            # Convert to summaries
            summaries = [
                GIInsightSummary(
                    id=insight.id,
                    problem=insight.problem[:100],
                    final_insight=insight.final_insight[:200],
                    confidence_score=insight.bias_check.confidence_score,
                    total_duration_ms=insight.total_duration_ms,
                    created_at=insight.created_at,
                    project=insight.project,
                )
                for insight in insights
            ]

            return summaries

        except Exception as e:
            logger.error(f"Failed to list insights: {e}")
            return []

    async def delete_insight(self, insight_id: str) -> bool:
        """
        Delete insight from cache

        Args:
            insight_id: Unique insight identifier

        Returns:
            True if deleted, False otherwise
        """
        try:
            # Remove from memory cache
            if insight_id in self._memory_cache:
                del self._memory_cache[insight_id]
                logger.info(f"Deleted insight {insight_id} from memory cache")

            # Remove from Redis/SQLite cache
            if self.cache_service:
                await self.cache_service.delete(f"gi:{insight_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete insight {insight_id}: {e}")
            return False

    # Private helper methods

    async def _execute_stage(self, stage_type: StageType, **kwargs) -> StageResult:
        """
        Execute a single GI Formula stage

        Args:
            stage_type: Stage to execute
            **kwargs: Stage-specific parameters

        Returns:
            Stage result with content and metadata
        """
        start_time = datetime.now()
        config = self._stage_configs[stage_type]

        try:
            # Format prompt
            prompt = config["prompt_template"].format(**kwargs)

            # Execute with Sequential MCP if available
            if self.sequential_mcp:
                content = await self._execute_with_sequential(prompt=prompt, timeout=config["timeout"])
            else:
                # Graceful degradation: use fallback logic
                content = await self._execute_fallback(stage_type, kwargs)

            # Calculate duration
            end_time = datetime.now()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)

            return StageResult(
                stage=stage_type,
                content=content,
                metadata={"prompt": prompt},
                duration_ms=duration_ms,
                timestamp=start_time,
            )

        except Exception as e:
            logger.error(f"Stage {stage_type.value} failed: {e}")
            # Return partial result with error
            return StageResult(
                stage=stage_type,
                content=f"Stage failed: {str(e)}",
                metadata={"error": str(e)},
                duration_ms=0,
                timestamp=start_time,
            )

    async def _execute_with_sequential(self, prompt: str, timeout: int) -> str:
        """
        Execute reasoning with Sequential MCP

        Args:
            prompt: Reasoning prompt
            timeout: Timeout in milliseconds

        Returns:
            Reasoning result content
        """
        try:
            # Call Sequential MCP (placeholder - actual implementation depends on MCP client)
            result = await asyncio.wait_for(self.sequential_mcp.reason(prompt), timeout=timeout / 1000.0)
            return result.get("content", "")
        except asyncio.TimeoutError:
            logger.warning(f"Sequential MCP timeout after {timeout}ms")
            raise RuntimeError(f"Sequential MCP timeout after {timeout}ms")
        except Exception as e:
            logger.error(f"Sequential MCP error: {e}")
            raise RuntimeError(f"Sequential MCP error: {str(e)}") from e

    async def _execute_fallback(self, stage_type: StageType, kwargs: Dict[str, Any]) -> str:
        """
        Fallback logic when Sequential MCP unavailable

        Args:
            stage_type: Stage to execute
            kwargs: Stage parameters

        Returns:
            Fallback content
        """
        # Simple rule-based fallback for each stage
        if stage_type == StageType.OBSERVATION:
            problem = kwargs.get("problem", "")
            return f"Key facts: {problem}. No additional observations (fallback mode)."

        elif stage_type == StageType.CONNECTION:
            _ = kwargs.get("observations", "")  # observations unused in fallback
            return "Connections: Based on observations. (fallback mode)"

        elif stage_type == StageType.PATTERN:
            _ = kwargs.get("connections", "")  # connections unused in fallback
            return "Patterns: Recurring themes identified. (fallback mode)"

        elif stage_type == StageType.SYNTHESIS:
            _ = kwargs.get("patterns", "")  # patterns unused in fallback
            return "Insight: Synthesized from patterns. (fallback mode)"

        else:
            return "Stage completed (fallback mode)"

    async def _execute_bias_check(self, insight: str) -> BiasCheckResult:
        """
        Check for cognitive biases in insight

        Args:
            insight: Generated insight to check

        Returns:
            Bias check result with detected biases and mitigation strategies
        """
        try:
            if self.sequential_mcp:
                # Use Sequential MCP for bias detection
                prompt = f"Analyze this insight for cognitive biases: {insight}"
                result = await self._execute_with_sequential(
                    prompt=prompt, timeout=self._stage_configs[StageType.BIAS_CHECK]["timeout"]
                )

                # Parse result (simplified - actual parsing depends on MCP response format)
                biases_detected = ["confirmation bias"] if "confirmation" in result.lower() else []
                mitigation_strategies = ["Seek counter-evidence"] if biases_detected else []
                confidence_score = 0.85 if not biases_detected else 0.70

            else:
                # Fallback: simple heuristic checks
                biases_detected = []
                mitigation_strategies = []

                # Check for common bias indicators
                if any(word in insight.lower() for word in ["always", "never", "everyone", "no one"]):
                    biases_detected.append("overgeneralization")
                    mitigation_strategies.append("Use quantifiable data instead of absolutes")

                if "obviously" in insight.lower() or "clearly" in insight.lower():
                    biases_detected.append("confirmation bias")
                    mitigation_strategies.append("Consider alternative perspectives")

                confidence_score = 0.90 if not biases_detected else 0.75

            return BiasCheckResult(
                biases_detected=biases_detected,
                mitigation_strategies=mitigation_strategies,
                confidence_score=confidence_score,
            )

        except Exception as e:
            logger.error(f"Bias check failed: {e}")
            return BiasCheckResult(
                biases_detected=["error in bias check"],
                mitigation_strategies=["Manual review recommended"],
                confidence_score=0.5,
            )

    def _generate_insight_id(self, problem: str) -> str:
        """
        Generate unique insight ID

        Args:
            problem: Problem statement

        Returns:
            Unique ID in format: gi-YYYY-MM-DD-{hash}
        """
        today = datetime.now().strftime("%Y-%m-%d")
        problem_hash = hashlib.sha256(problem.encode()).hexdigest()[:6]
        return f"gi-{today}-{problem_hash}"

    async def _get_cached_insight(self, insight_id: str) -> Optional[GIFormulaResult]:
        """
        Get insight from 3-tier cache

        Tier 1: Memory cache (fastest)
        Tier 2: Redis cache (fast)
        Tier 3: SQLite cache (persistent)

        Args:
            insight_id: Unique insight identifier

        Returns:
            Cached result or None
        """
        # Tier 1: Memory cache
        if insight_id in self._memory_cache:
            logger.debug(f"Memory cache hit for {insight_id}")
            return self._memory_cache[insight_id]

        # Tier 2 & 3: External cache (Redis/SQLite)
        if self.cache_service:
            try:
                cached_data = await self.cache_service.get(f"gi:{insight_id}")
                if cached_data:
                    logger.debug(f"External cache hit for {insight_id}")
                    result = GIFormulaResult(**cached_data)
                    # Populate memory cache
                    self._memory_cache[insight_id] = result
                    return result
            except Exception as e:
                logger.error(f"Cache retrieval error: {e}")

        return None

    async def _cache_insight(self, insight_id: str, result: GIFormulaResult):
        """
        Cache insight in all tiers

        Args:
            insight_id: Unique insight identifier
            result: Result to cache
        """
        try:
            # Tier 1: Memory cache
            self._memory_cache[insight_id] = result

            # Evict oldest if cache full
            if len(self._memory_cache) > self._max_memory_cache:
                oldest_id = min(self._memory_cache.keys(), key=lambda k: self._memory_cache[k].created_at)
                del self._memory_cache[oldest_id]

            # Tier 2 & 3: External cache
            if self.cache_service:
                await self.cache_service.set(
                    f"gi:{insight_id}", result.dict(), ttl=self.config.get("cache_ttl", 86400)  # 24 hours
                )

        except Exception as e:
            logger.error(f"Failed to cache insight: {e}")

    async def _save_to_obsidian(self, result: GIFormulaResult):
        """
        Save insight to Obsidian vault

        Args:
            result: GI Formula result to save
        """
        if not self.obsidian_service:
            return

        try:
            # Format Obsidian note
            today = datetime.now().strftime("%Y-%m-%d")
            safe_filename = result.problem[:50].replace(" ", "-").replace("/", "-")
            obsidian_path = f"개발일지/{today}/GI-Insight-{safe_filename}.md"

            content = self._format_obsidian_note(result)

            # Save to Obsidian
            await self.obsidian_service.create_note(path=obsidian_path, content=content)

            # Update result with Obsidian path
            result.obsidian_path = obsidian_path

            logger.info(f"Saved insight {result.id} to Obsidian: {obsidian_path}")

        except Exception as e:
            logger.error(f"Failed to save to Obsidian: {e}")

    def _format_obsidian_note(self, result: GIFormulaResult) -> str:
        """
        Format GI Formula result as Obsidian markdown

        Args:
            result: GI Formula result

        Returns:
            Formatted markdown content
        """
        content = f"""---
type: gi-insight
id: {result.id}
project: {result.project}
date: {result.created_at.strftime("%Y-%m-%d")}
confidence: {result.bias_check.confidence_score:.2f}
duration_ms: {result.total_duration_ms}
tags: [gi-formula, insight, {result.project}]
---

# GI Insight: {result.problem}

## [*] Problem Statement

{result.problem}

## [*] 5-Stage Analysis

### 1. Observation
{result.stages["observation"].content}

**Duration**: {result.stages["observation"].duration_ms}ms

### 2. Connection
{result.stages["connection"].content}

**Duration**: {result.stages["connection"].duration_ms}ms

### 3. Pattern Recognition
{result.stages["pattern"].content}

**Duration**: {result.stages["pattern"].duration_ms}ms

### 4. Synthesis
{result.stages["synthesis"].content}

**Duration**: {result.stages["synthesis"].duration_ms}ms

### 5. Bias Check
**Detected Biases**: {", ".join(result.bias_check.biases_detected) if result.bias_check.biases_detected else "None"}
**Mitigation Strategies**: {", ".join(result.bias_check.mitigation_strategies) if result.bias_check.mitigation_strategies else "N/A"}
**Confidence Score**: {result.bias_check.confidence_score:.2f}

**Duration**: {result.stages["bias_check"].duration_ms}ms

## [RESULT] Insight

{result.final_insight}

## [*] Metadata

- **Total Duration**: {result.total_duration_ms}ms ({result.total_duration_ms / 1000:.1f}s)
- **Created**: {result.created_at.strftime("%Y-%m-%d %H:%M:%S")}
- **Project**: {result.project}

## [*] Related

- [[GI Formula Framework]]
- [[Insight Patterns]]
- [[{result.project}]]
"""

        return content


# Create singleton instance (can be initialized with dependencies in main.py)
gi_formula_service = GIFormulaService()
