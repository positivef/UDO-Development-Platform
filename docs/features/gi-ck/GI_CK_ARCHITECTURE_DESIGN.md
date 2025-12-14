# GI Formula & C-K Theory Architecture Design

**Date**: 2025-11-20
**Status**: Design Review Phase
**Priority**: High
**Performance Targets**: GI Formula <30s, C-K Theory <45s

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Service Layer Design](#service-layer-design)
4. [Data Models](#data-models)
5. [API Endpoints](#api-endpoints)
6. [Database Schema](#database-schema)
7. [Integration Strategy](#integration-strategy)
8. [Performance Optimization](#performance-optimization)
9. [Error Handling & Validation](#error-handling--validation)
10. [Testing Strategy](#testing-strategy)
11. [Implementation Checklist](#implementation-checklist)

---

## 1. Executive Summary

### Overview

This architecture implements two AI-powered services for automated insight generation and design alternative exploration:

**GI Formula (Genius Insight Formula)**
- 5-stage automated insight generation (Observation → Connection → Pattern → Synthesis → Bias Check)
- Target: <30 seconds execution
- Automatic Obsidian knowledge base integration
- Leverages MCP Sequential server for structured reasoning

**C-K Theory (Concept-Knowledge Design Theory)**
- Automatic generation of 3 design alternatives
- RICE scoring framework (Reach × Impact × Confidence / Effort)
- Comprehensive trade-off analysis
- Target: <45 seconds execution
- Context7 integration for design patterns

### Design Principles

1. **Async-First**: All I/O operations are non-blocking
2. **Pattern Consistency**: Follows existing service patterns (QualityMetricsService, TimeTrackingService)
3. **Caching Strategy**: Redis-backed caching for repeated queries
4. **MCP Integration**: Sequential for analysis, Context7 for patterns, Obsidian for persistence
5. **Graceful Degradation**: Services function with mock data if MCP unavailable

---

## 2. System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ GI Formula   │  │  C-K Theory  │  │   Obsidian   │          │
│  │   Service    │  │   Service    │  │   Service    │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         ├──────────────────┴──────────────────┘                  │
│         │                                                         │
│  ┌──────▼──────────────────────────────────────────┐            │
│  │           MCP Integration Layer                  │            │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐         │            │
│  │  │Sequential│  │Context7 │  │Obsidian │         │            │
│  │  │  (AI)   │  │ (Docs)  │  │  (KB)   │         │            │
│  │  └─────────┘  └─────────┘  └─────────┘         │            │
│  └──────────────────────────────────────────────────┘            │
│                                                                   │
│  ┌──────────────────────────────────────────────────┐            │
│  │            Data Persistence Layer                 │            │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐          │            │
│  │  │ Redis   │  │  SQLite │  │Obsidian │          │            │
│  │  │ (Cache) │  │  (Data) │  │  Vault  │          │            │
│  │  └─────────┘  └─────────┘  └─────────┘          │            │
│  └──────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

#### GI Formula Flow
```
User Request (Problem)
    → GIFormulaService.generate_insight()
    → Sequential MCP: Stage 1 (Observation)
    → Sequential MCP: Stage 2 (Connection)
    → Sequential MCP: Stage 3 (Pattern Recognition)
    → Sequential MCP: Stage 4 (Synthesis)
    → Sequential MCP: Stage 5 (Bias Check)
    → ObsidianService.save_insight()
    → Return GIFormulaResult
```

#### C-K Theory Flow
```
User Request (Design Challenge)
    → CKTheoryService.generate_alternatives()
    → Sequential MCP: Concept Space Exploration
    → Context7 MCP: Design Pattern Reference (parallel)
    → Generate 3 Alternatives (parallel)
    → Calculate RICE Scores (parallel)
    → ObsidianService.save_design_alternatives()
    → Return CKTheoryResult
```

---

## 3. Service Layer Design

### 3.1 GIFormulaService

**Location**: `backend/app/services/gi_formula_service.py`

**Key Responsibilities**:
- Coordinate 5-stage insight generation
- Interface with Sequential MCP for structured reasoning
- Manage insight caching and versioning
- Integrate with Obsidian for knowledge persistence

**Core Methods**:

```python
class GIFormulaService:
    async def generate_insight(
        self,
        problem: str,
        context: Optional[Dict] = None
    ) -> GIFormulaResult

    async def _stage_observation(self, problem: str) -> StageResult
    async def _stage_connection(self, observations: StageResult) -> StageResult
    async def _stage_pattern(self, connections: StageResult) -> StageResult
    async def _stage_synthesis(self, patterns: StageResult) -> StageResult
    async def _stage_bias_check(self, synthesis: StageResult) -> StageResult

    async def get_insight_history(self, limit: int = 10) -> List[GIFormulaResult]
    async def search_similar_insights(self, query: str) -> List[GIFormulaResult]
```

**Dependencies**:
- `ObsidianService` (for knowledge persistence)
- `Sequential MCP` (for structured AI reasoning)
- `Redis` (for caching)

### 3.2 CKTheoryService

**Location**: `backend/app/services/ck_theory_service.py`

**Key Responsibilities**:
- Generate 3 design alternatives using C-K Theory
- Calculate RICE scores for each alternative
- Perform trade-off analysis
- Integrate with Context7 for design pattern guidance

**Core Methods**:

```python
class CKTheoryService:
    async def generate_alternatives(
        self,
        challenge: str,
        constraints: Optional[Dict] = None
    ) -> CKTheoryResult

    async def _explore_concept_space(self, challenge: str) -> List[ConceptNode]
    async def _generate_single_alternative(
        self,
        concept: ConceptNode,
        index: int
    ) -> DesignAlternative

    async def _calculate_rice_score(
        self,
        alternative: DesignAlternative
    ) -> RICEScore

    async def _analyze_tradeoffs(
        self,
        alternatives: List[DesignAlternative]
    ) -> TradeoffAnalysis

    async def get_design_history(self, limit: int = 10) -> List[CKTheoryResult]
```

**Dependencies**:
- `ObsidianService` (for knowledge persistence)
- `Sequential MCP` (for concept exploration)
- `Context7 MCP` (for design pattern reference)
- `Redis` (for caching)

---

## 4. Data Models

### 4.1 GI Formula Models

**Location**: `backend/app/models/gi_formula.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class StageType(str, Enum):
    """GI Formula stage types"""
    OBSERVATION = "observation"
    CONNECTION = "connection"
    PATTERN = "pattern"
    SYNTHESIS = "synthesis"
    BIAS_CHECK = "bias_check"

class StageResult(BaseModel):
    """Result from a single GI Formula stage"""
    stage: StageType
    content: str = Field(..., description="Stage output content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = Field(..., description="Execution time in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now)

class BiasCheckResult(BaseModel):
    """Bias check analysis result"""
    biases_detected: List[str] = Field(default_factory=list)
    mitigation_strategies: List[str] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0.0, le=1.0)

class GIFormulaRequest(BaseModel):
    """Request to generate insight"""
    problem: str = Field(..., min_length=10, description="Problem to analyze")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    project: Optional[str] = Field("UDO-Development-Platform", description="Project name")

    class Config:
        json_schema_extra = {
            "example": {
                "problem": "How can we reduce API response time by 50%?",
                "context": {
                    "current_latency": "200ms",
                    "target_latency": "100ms",
                    "bottleneck": "database queries"
                },
                "project": "UDO-Development-Platform"
            }
        }

class GIFormulaResult(BaseModel):
    """Complete GI Formula insight result"""
    id: str = Field(..., description="Unique insight ID")
    problem: str
    stages: Dict[StageType, StageResult] = Field(..., description="Results from each stage")
    final_insight: str = Field(..., description="Synthesized insight")
    bias_check: BiasCheckResult
    total_duration_ms: int
    created_at: datetime = Field(default_factory=datetime.now)
    obsidian_path: Optional[str] = Field(None, description="Path to saved Obsidian note")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "gi-2025-11-20-001",
                "problem": "How can we reduce API response time by 50%?",
                "final_insight": "Implement connection pooling and add Redis cache layer...",
                "total_duration_ms": 28500,
                "obsidian_path": "개발일지/2025-11-20/GI-Insight-API-Performance.md"
            }
        }
```

### 4.2 C-K Theory Models

**Location**: `backend/app/models/ck_theory.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime

class RICEScore(BaseModel):
    """RICE scoring framework"""
    reach: int = Field(..., ge=1, le=10, description="Number of users affected (1-10)")
    impact: int = Field(..., ge=1, le=10, description="Impact level (1-10)")
    confidence: int = Field(..., ge=1, le=10, description="Confidence in estimates (1-10)")
    effort: int = Field(..., ge=1, le=10, description="Effort required (1-10)")
    score: float = Field(..., description="RICE score = (R × I × C) / E")

    @property
    def calculate_score(self) -> float:
        """Calculate RICE score"""
        return (self.reach * self.impact * self.confidence) / max(self.effort, 1)

class DesignAlternative(BaseModel):
    """Single design alternative"""
    id: str = Field(..., description="Alternative ID (A, B, C)")
    title: str = Field(..., description="Alternative title")
    description: str = Field(..., description="Detailed description")

    # Concept Space
    concept_origin: str = Field(..., description="Concept space origin")
    knowledge_basis: List[str] = Field(..., description="Knowledge elements used")

    # RICE Analysis
    rice: RICEScore

    # Trade-off Analysis
    pros: List[str] = Field(..., description="Advantages")
    cons: List[str] = Field(..., description="Disadvantages")
    risks: List[str] = Field(..., description="Implementation risks")

    # Technical Details
    technical_approach: str = Field(..., description="Technical implementation approach")
    dependencies: List[str] = Field(default_factory=list)
    estimated_timeline: str = Field(..., description="Estimated timeline")

    metadata: Dict[str, Any] = Field(default_factory=dict)

class TradeoffAnalysis(BaseModel):
    """Comparative trade-off analysis"""
    summary: str = Field(..., description="Overall trade-off summary")
    recommendation: str = Field(..., description="Recommended alternative with reasoning")
    comparison_matrix: Dict[str, Dict[str, Any]] = Field(..., description="Feature comparison matrix")
    decision_tree: List[str] = Field(..., description="Decision-making criteria")

class CKTheoryRequest(BaseModel):
    """Request to generate design alternatives"""
    challenge: str = Field(..., min_length=10, description="Design challenge")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Design constraints")
    project: Optional[str] = Field("UDO-Development-Platform", description="Project name")

    class Config:
        json_schema_extra = {
            "example": {
                "challenge": "Design an authentication system that supports multiple providers",
                "constraints": {
                    "budget": "2 weeks",
                    "team_size": 2,
                    "security_requirement": "high"
                },
                "project": "UDO-Development-Platform"
            }
        }

class CKTheoryResult(BaseModel):
    """Complete C-K Theory design result"""
    id: str = Field(..., description="Unique design ID")
    challenge: str
    alternatives: List[DesignAlternative] = Field(..., min_items=3, max_items=3)
    tradeoff_analysis: TradeoffAnalysis
    total_duration_ms: int
    created_at: datetime = Field(default_factory=datetime.now)
    obsidian_path: Optional[str] = Field(None, description="Path to saved Obsidian note")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ck-2025-11-20-001",
                "challenge": "Design an authentication system",
                "alternatives": [
                    {
                        "id": "A",
                        "title": "JWT + OAuth2 Hybrid",
                        "rice": {"score": 7.5}
                    }
                ],
                "total_duration_ms": 42000,
                "obsidian_path": "개발일지/2025-11-20/CK-Design-Auth-System.md"
            }
        }
```

---

## 5. API Endpoints

### 5.1 GI Formula Router

**Location**: `backend/app/routers/gi_formula.py`

```python
# Endpoints

POST   /api/v1/gi-formula/generate
GET    /api/v1/gi-formula/history
GET    /api/v1/gi-formula/{insight_id}
GET    /api/v1/gi-formula/search
DELETE /api/v1/gi-formula/{insight_id}
```

**Detailed Specification**:

```python
@router.post("/generate", response_model=GIFormulaResult)
async def generate_insight(request: GIFormulaRequest):
    """
    Generate insight using GI Formula (5-stage process)

    Performance: Target <30 seconds

    Stages:
    1. Observation: Identify key facts and data
    2. Connection: Link related concepts
    3. Pattern: Recognize recurring patterns
    4. Synthesis: Combine into actionable insight
    5. Bias Check: Validate for cognitive biases

    Returns:
        GIFormulaResult with complete insight analysis
    """

@router.get("/history", response_model=List[GIFormulaResult])
async def get_insight_history(
    limit: int = Query(10, ge=1, le=100),
    project: Optional[str] = Query(None)
):
    """
    Get historical insights

    Returns:
        List of past GI Formula results
    """

@router.get("/{insight_id}", response_model=GIFormulaResult)
async def get_insight(insight_id: str):
    """
    Get specific insight by ID
    """

@router.get("/search", response_model=List[GIFormulaResult])
async def search_insights(
    query: str = Query(..., min_length=3),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Search insights by keywords

    Searches across:
    - Problem statements
    - Insights
    - Stage outputs
    """

@router.delete("/{insight_id}")
async def delete_insight(insight_id: str):
    """
    Delete an insight (soft delete)
    """
```

### 5.2 C-K Theory Router

**Location**: `backend/app/routers/ck_theory.py`

```python
# Endpoints

POST   /api/v1/ck-theory/generate
GET    /api/v1/ck-theory/history
GET    /api/v1/ck-theory/{design_id}
GET    /api/v1/ck-theory/{design_id}/alternative/{alternative_id}
POST   /api/v1/ck-theory/{design_id}/feedback
DELETE /api/v1/ck-theory/{design_id}
```

**Detailed Specification**:

```python
@router.post("/generate", response_model=CKTheoryResult)
async def generate_alternatives(request: CKTheoryRequest):
    """
    Generate 3 design alternatives using C-K Theory

    Performance: Target <45 seconds

    Process:
    1. Explore concept space
    2. Generate 3 alternatives (parallel)
    3. Calculate RICE scores
    4. Perform trade-off analysis
    5. Save to Obsidian

    Returns:
        CKTheoryResult with 3 alternatives and analysis
    """

@router.get("/history", response_model=List[CKTheoryResult])
async def get_design_history(
    limit: int = Query(10, ge=1, le=100),
    project: Optional[str] = Query(None)
):
    """
    Get historical design explorations
    """

@router.get("/{design_id}", response_model=CKTheoryResult)
async def get_design(design_id: str):
    """
    Get specific design exploration by ID
    """

@router.get("/{design_id}/alternative/{alternative_id}",
            response_model=DesignAlternative)
async def get_alternative_detail(design_id: str, alternative_id: str):
    """
    Get detailed information for specific alternative (A, B, or C)
    """

@router.post("/{design_id}/feedback")
async def submit_feedback(
    design_id: str,
    feedback: Dict[str, Any]
):
    """
    Submit feedback on design alternatives

    Used for learning and improvement
    """

@router.delete("/{design_id}")
async def delete_design(design_id: str):
    """
    Delete a design exploration (soft delete)
    """
```

---

## 6. Database Schema

### 6.1 SQLite Schema

**Location**: `backend/app/db/models.py`

```sql
-- GI Formula Insights
CREATE TABLE gi_insights (
    id TEXT PRIMARY KEY,
    problem TEXT NOT NULL,
    final_insight TEXT NOT NULL,
    project TEXT DEFAULT 'UDO-Development-Platform',

    -- Stage results (JSON)
    stage_observation TEXT,
    stage_connection TEXT,
    stage_pattern TEXT,
    stage_synthesis TEXT,
    stage_bias_check TEXT,

    -- Bias check details
    biases_detected TEXT, -- JSON array
    mitigation_strategies TEXT, -- JSON array
    confidence_score REAL,

    -- Performance metrics
    total_duration_ms INTEGER,

    -- Metadata
    context TEXT, -- JSON
    obsidian_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    -- Search optimization
    search_index TEXT -- Full-text search index
);

CREATE INDEX idx_gi_insights_created ON gi_insights(created_at DESC);
CREATE INDEX idx_gi_insights_project ON gi_insights(project);
CREATE VIRTUAL TABLE gi_insights_fts USING fts5(
    problem, final_insight, content='gi_insights'
);

-- C-K Theory Designs
CREATE TABLE ck_designs (
    id TEXT PRIMARY KEY,
    challenge TEXT NOT NULL,
    project TEXT DEFAULT 'UDO-Development-Platform',

    -- Alternatives (JSON array of 3)
    alternatives TEXT NOT NULL,

    -- Trade-off analysis (JSON)
    tradeoff_analysis TEXT NOT NULL,

    -- Performance metrics
    total_duration_ms INTEGER,

    -- Metadata
    constraints TEXT, -- JSON
    obsidian_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,

    -- Feedback tracking
    feedback_count INTEGER DEFAULT 0,
    avg_rating REAL
);

CREATE INDEX idx_ck_designs_created ON ck_designs(created_at DESC);
CREATE INDEX idx_ck_designs_project ON ck_designs(project);
CREATE VIRTUAL TABLE ck_designs_fts USING fts5(
    challenge, content='ck_designs'
);

-- Design Feedback (for learning)
CREATE TABLE design_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    design_id TEXT NOT NULL,
    alternative_id TEXT, -- A, B, or C
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    comments TEXT,
    selected_alternative TEXT,
    outcome TEXT, -- success, partial, failure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (design_id) REFERENCES ck_designs(id)
);

CREATE INDEX idx_feedback_design ON design_feedback(design_id);
```

### 6.2 Redis Cache Keys

```python
# GI Formula cache keys
gi:insight:{insight_id}           # Full insight result (TTL: 7 days)
gi:search:{query_hash}            # Search results (TTL: 1 hour)
gi:history:{project}              # Recent history (TTL: 1 hour)

# C-K Theory cache keys
ck:design:{design_id}             # Full design result (TTL: 7 days)
ck:alternative:{design_id}:{alt}  # Single alternative (TTL: 7 days)
ck:history:{project}              # Recent history (TTL: 1 hour)

# MCP response cache
mcp:sequential:{prompt_hash}      # Sequential MCP response (TTL: 1 day)
mcp:context7:{query_hash}         # Context7 response (TTL: 1 day)
```

---

## 7. Integration Strategy

### 7.1 MCP Server Integration

**Sequential MCP (Primary)**

```python
# Example: GI Formula Stage Execution
async def _execute_stage_with_sequential(
    self,
    stage: StageType,
    prompt: str,
    previous_context: Optional[Dict] = None
) -> StageResult:
    """
    Execute GI Formula stage using Sequential MCP

    Sequential MCP provides:
    - Structured multi-step reasoning
    - Hypothesis testing
    - Evidence gathering
    - Systematic analysis
    """
    start_time = datetime.now()

    # Construct Sequential prompt
    sequential_prompt = {
        "task": prompt,
        "context": previous_context or {},
        "reasoning_depth": "comprehensive",
        "output_format": "structured"
    }

    # Call Sequential MCP
    response = await self.mcp_client.sequential.think(
        prompt=sequential_prompt,
        timeout=10000  # 10 second timeout per stage
    )

    duration = (datetime.now() - start_time).total_seconds() * 1000

    return StageResult(
        stage=stage,
        content=response.get("analysis", ""),
        metadata={
            "reasoning_steps": response.get("steps", []),
            "confidence": response.get("confidence", 0.0)
        },
        duration_ms=int(duration)
    )
```

**Context7 MCP (Design Patterns)**

```python
# Example: C-K Theory Pattern Reference
async def _get_design_patterns(
    self,
    domain: str
) -> List[Dict]:
    """
    Fetch relevant design patterns from Context7

    Context7 provides:
    - Official framework patterns
    - Best practices
    - Implementation examples
    """
    # Query Context7 for design patterns
    patterns = await self.mcp_client.context7.search(
        query=f"design patterns for {domain}",
        sources=["official-docs", "best-practices"],
        max_results=5
    )

    return patterns
```

**Obsidian MCP (Knowledge Persistence)**

```python
# Example: Save GI Insight to Obsidian
async def _save_to_obsidian(
    self,
    insight: GIFormulaResult
) -> str:
    """
    Save insight to Obsidian vault

    Format:
    - YAML frontmatter with metadata
    - Structured markdown content
    - Tagged for search
    """
    # Generate Obsidian content
    content = {
        "frontmatter": {
            "date": insight.created_at.strftime("%Y-%m-%d"),
            "time": insight.created_at.strftime("%H:%M"),
            "project": "UDO-Development-Platform",
            "type": "gi-insight",
            "tags": ["insight", "gi-formula", "automation"],
            "insight_id": insight.id
        },
        "content": self._format_insight_markdown(insight)
    }

    # Save via ObsidianService
    title = f"GI Insight: {insight.problem[:50]}"
    await self.obsidian_service.create_daily_note(title, content)

    return f"개발일지/{insight.created_at.strftime('%Y-%m-%d')}/{title}.md"
```

### 7.2 Error Handling Strategy

**Graceful Degradation**

```python
class GIFormulaService:
    async def generate_insight(
        self,
        problem: str,
        context: Optional[Dict] = None
    ) -> GIFormulaResult:
        """
        Generate insight with graceful degradation

        Fallback chain:
        1. Sequential MCP (preferred)
        2. Native AI reasoning (fallback)
        3. Template-based (emergency)
        """
        try:
            # Try Sequential MCP
            return await self._generate_with_sequential(problem, context)
        except MCPUnavailableError:
            logger.warning("Sequential MCP unavailable, using fallback")
            return await self._generate_with_fallback(problem, context)
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            return await self._generate_with_template(problem, context)

    async def _generate_with_fallback(
        self,
        problem: str,
        context: Optional[Dict]
    ) -> GIFormulaResult:
        """
        Fallback: Use native AI reasoning
        """
        # Use OpenAI/Anthropic API directly
        # Less structured but still functional
        pass

    async def _generate_with_template(
        self,
        problem: str,
        context: Optional[Dict]
    ) -> GIFormulaResult:
        """
        Emergency fallback: Use templates
        """
        # Return structured template with placeholders
        # Allows system to remain operational
        pass
```

**Retry Logic**

```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
async def _call_mcp_with_retry(
    self,
    mcp_function,
    *args,
    **kwargs
):
    """
    Call MCP with automatic retry on transient failures
    """
    return await mcp_function(*args, **kwargs)
```

---

## 8. Performance Optimization

### 8.1 Parallel Execution

**GI Formula** (Sequential stages, but with caching)

```python
async def generate_insight(self, problem: str) -> GIFormulaResult:
    """
    Stages are sequential by nature, but we optimize with:
    1. Stage-level caching
    2. Async I/O for Obsidian save
    3. Background task for analytics
    """
    start_time = datetime.now()

    # Stages 1-5 (sequential)
    observation = await self._stage_observation(problem)
    connection = await self._stage_connection(observation)
    pattern = await self._stage_pattern(connection)
    synthesis = await self._stage_synthesis(pattern)
    bias_check = await self._stage_bias_check(synthesis)

    result = GIFormulaResult(...)

    # Parallel post-processing
    await asyncio.gather(
        self._save_to_cache(result),
        self._save_to_obsidian(result),
        self._update_analytics(result)
    )

    return result
```

**C-K Theory** (Maximum parallelization)

```python
async def generate_alternatives(self, challenge: str) -> CKTheoryResult:
    """
    Maximize parallel execution:
    1. Concept exploration (sequential)
    2. Generate 3 alternatives (parallel)
    3. Calculate RICE scores (parallel)
    4. Trade-off analysis (post-processing)
    """
    start_time = datetime.now()

    # Step 1: Explore concept space (sequential)
    concepts = await self._explore_concept_space(challenge)

    # Step 2: Generate 3 alternatives in parallel
    alternative_tasks = [
        self._generate_single_alternative(concepts[i], f"Alternative {chr(65+i)}")
        for i in range(3)
    ]
    alternatives = await asyncio.gather(*alternative_tasks)

    # Step 3: Calculate RICE scores in parallel
    rice_tasks = [
        self._calculate_rice_score(alt)
        for alt in alternatives
    ]
    rice_scores = await asyncio.gather(*rice_tasks)

    # Attach scores
    for alt, rice in zip(alternatives, rice_scores):
        alt.rice = rice

    # Step 4: Trade-off analysis
    tradeoff = await self._analyze_tradeoffs(alternatives)

    result = CKTheoryResult(...)

    # Parallel post-processing
    await asyncio.gather(
        self._save_to_cache(result),
        self._save_to_obsidian(result),
        self._update_analytics(result)
    )

    return result
```

### 8.2 Caching Strategy

**Multi-Level Cache**

```python
class CacheManager:
    """
    3-tier caching:
    1. Memory (fastest, 5-minute TTL)
    2. Redis (fast, 7-day TTL)
    3. SQLite (persistent)
    """

    async def get_cached_insight(self, cache_key: str) -> Optional[GIFormulaResult]:
        # Level 1: Memory
        if result := self._memory_cache.get(cache_key):
            logger.debug("Cache hit: memory")
            return result

        # Level 2: Redis
        if redis_data := await self._redis.get(f"gi:insight:{cache_key}"):
            result = GIFormulaResult.parse_raw(redis_data)
            self._memory_cache.set(cache_key, result, ttl=300)  # 5 minutes
            logger.debug("Cache hit: redis")
            return result

        # Level 3: SQLite
        if db_data := await self._db.get_insight(cache_key):
            result = GIFormulaResult(**db_data)
            await self._redis.setex(
                f"gi:insight:{cache_key}",
                604800,  # 7 days
                result.json()
            )
            self._memory_cache.set(cache_key, result, ttl=300)
            logger.debug("Cache hit: database")
            return result

        logger.debug("Cache miss")
        return None
```

### 8.3 Performance Targets

| Metric | Target | Strategy |
|--------|--------|----------|
| **GI Formula Total** | <30s | Sequential stages with optimized prompts |
| - Observation | <5s | Focused data gathering |
| - Connection | <6s | Parallel concept linking |
| - Pattern | <6s | Template matching |
| - Synthesis | <7s | Final integration |
| - Bias Check | <6s | Checklist validation |
| **C-K Theory Total** | <45s | Maximum parallelization |
| - Concept Exploration | <10s | Structured search |
| - Alternative Generation | <25s | 3 parallel tasks (~8s each) |
| - RICE Calculation | <5s | 3 parallel calculations |
| - Trade-off Analysis | <5s | Comparative matrix |
| **Cache Hit Latency** | <100ms | Redis + memory caching |
| **Database Query** | <50ms | Indexed queries + connection pooling |

---

## 9. Error Handling & Validation

### 9.1 Input Validation

```python
class GIFormulaRequest(BaseModel):
    problem: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Problem to analyze"
    )

    @validator('problem')
    def validate_problem(cls, v):
        # Check for meaningful content
        if len(v.strip().split()) < 3:
            raise ValueError("Problem must contain at least 3 words")

        # Check for spam/abuse patterns
        if any(spam in v.lower() for spam in ['test', 'asdf', 'xxxx']):
            raise ValueError("Invalid problem statement")

        return v.strip()

class CKTheoryRequest(BaseModel):
    challenge: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Design challenge"
    )

    constraints: Optional[Dict[str, Any]] = Field(None)

    @validator('constraints')
    def validate_constraints(cls, v):
        if v is None:
            return {}

        # Validate constraint structure
        allowed_keys = {'budget', 'team_size', 'timeline', 'complexity', 'security'}
        if invalid_keys := set(v.keys()) - allowed_keys:
            raise ValueError(f"Invalid constraint keys: {invalid_keys}")

        return v
```

### 9.2 Error Response Format

```python
class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Technical details")
    timestamp: datetime = Field(default_factory=datetime.now)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")

# Example usage in router
@router.post("/generate")
async def generate_insight(request: GIFormulaRequest):
    try:
        result = await gi_service.generate_insight(
            problem=request.problem,
            context=request.context
        )
        return result
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error="validation_error",
                message="Invalid request parameters",
                detail=str(e)
            ).dict()
        )
    except MCPUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                error="service_unavailable",
                message="AI reasoning service temporarily unavailable",
                detail="Using fallback system"
            ).dict()
        )
    except Exception as e:
        logger.error(f"Insight generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="internal_error",
                message="Failed to generate insight",
                detail=str(e) if settings.DEBUG else None
            ).dict()
        )
```

### 9.3 Timeout Handling

```python
async def generate_insight_with_timeout(
    self,
    problem: str,
    timeout: int = 30
) -> GIFormulaResult:
    """
    Generate insight with hard timeout

    If timeout is exceeded:
    1. Cancel all pending tasks
    2. Return partial result if available
    3. Log timeout for monitoring
    """
    try:
        return await asyncio.wait_for(
            self._generate_insight_internal(problem),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"Insight generation timeout after {timeout}s")

        # Return partial result if available
        if partial_result := self._get_partial_result():
            partial_result.metadata["timeout"] = True
            partial_result.metadata["completed_stages"] = len(partial_result.stages)
            return partial_result

        # Otherwise raise
        raise HTTPException(
            status_code=504,
            detail=ErrorResponse(
                error="timeout",
                message=f"Insight generation exceeded {timeout}s timeout",
                detail="Try again or simplify the problem"
            ).dict()
        )
```

---

## 10. Testing Strategy

### 10.1 Unit Tests

**Test Structure**:
- `backend/tests/test_gi_formula_service.py`
- `backend/tests/test_ck_theory_service.py`
- `backend/tests/test_gi_formula_router.py`
- `backend/tests/test_ck_theory_router.py`

**Coverage Targets**: >85%

```python
# Example: GI Formula Service Tests
import pytest
from app.services.gi_formula_service import GIFormulaService

@pytest.fixture
async def gi_service():
    """Fixture for GI Formula service"""
    service = GIFormulaService()
    yield service
    await service.cleanup()

class TestGIFormulaService:
    """Test suite for GI Formula service"""

    @pytest.mark.asyncio
    async def test_generate_insight_success(self, gi_service):
        """Test successful insight generation"""
        result = await gi_service.generate_insight(
            problem="How to reduce API latency by 50%?"
        )

        assert result is not None
        assert result.id.startswith("gi-")
        assert len(result.stages) == 5
        assert result.total_duration_ms < 30000  # <30s
        assert result.final_insight

    @pytest.mark.asyncio
    async def test_generate_insight_with_cache(self, gi_service):
        """Test cached insight retrieval"""
        problem = "Test caching mechanism"

        # First call (cache miss)
        result1 = await gi_service.generate_insight(problem)

        # Second call (cache hit)
        start = datetime.now()
        result2 = await gi_service.generate_insight(problem)
        duration = (datetime.now() - start).total_seconds() * 1000

        assert result1.id == result2.id
        assert duration < 100  # <100ms from cache

    @pytest.mark.asyncio
    async def test_generate_insight_mcp_fallback(self, gi_service, monkeypatch):
        """Test fallback when MCP unavailable"""
        # Mock MCP unavailability
        async def mock_mcp_error(*args, **kwargs):
            raise MCPUnavailableError("Sequential MCP down")

        monkeypatch.setattr(gi_service.mcp_client.sequential, "think", mock_mcp_error)

        result = await gi_service.generate_insight("Test fallback")

        assert result is not None
        assert result.metadata.get("fallback_used") is True

    @pytest.mark.asyncio
    async def test_stage_timeout(self, gi_service):
        """Test stage timeout handling"""
        with pytest.raises(asyncio.TimeoutError):
            await gi_service._execute_stage_with_sequential(
                stage=StageType.OBSERVATION,
                prompt="Analyze this extremely complex problem" * 1000,
                timeout=1  # 1 second timeout
            )

    @pytest.mark.asyncio
    async def test_bias_check_detects_biases(self, gi_service):
        """Test bias detection in final stage"""
        # Create synthesis with known biases
        biased_synthesis = StageResult(
            stage=StageType.SYNTHESIS,
            content="We should use technology X because everyone uses it"
        )

        result = await gi_service._stage_bias_check(biased_synthesis)

        assert len(result.metadata["biases_detected"]) > 0
        assert "bandwagon" in str(result.metadata["biases_detected"]).lower()
```

### 10.2 Integration Tests

```python
# Example: End-to-End Integration Test
@pytest.mark.integration
class TestGIFormulaIntegration:
    """Integration tests for GI Formula with real dependencies"""

    @pytest.mark.asyncio
    async def test_full_insight_generation_with_obsidian(self, test_client):
        """Test complete flow: API → Service → MCP → Obsidian"""
        response = await test_client.post(
            "/api/v1/gi-formula/generate",
            json={
                "problem": "How to improve test coverage from 70% to 90%?",
                "context": {"current_coverage": 70, "target": 90}
            }
        )

        assert response.status_code == 200
        result = response.json()

        # Validate response structure
        assert result["id"].startswith("gi-")
        assert len(result["stages"]) == 5
        assert result["final_insight"]
        assert result["total_duration_ms"] < 30000

        # Verify Obsidian save
        assert result["obsidian_path"]
        obsidian_file = Path(result["obsidian_path"])
        assert obsidian_file.exists()

        # Verify cache
        cached = await gi_service.get_cached_insight(result["id"])
        assert cached is not None
        assert cached.id == result["id"]

    @pytest.mark.asyncio
    async def test_ck_theory_parallel_generation(self, test_client):
        """Test C-K Theory generates 3 alternatives in parallel"""
        start = datetime.now()

        response = await test_client.post(
            "/api/v1/ck-theory/generate",
            json={
                "challenge": "Design a caching strategy for API responses",
                "constraints": {"complexity": "medium", "budget": "1 week"}
            }
        )

        duration = (datetime.now() - start).total_seconds() * 1000

        assert response.status_code == 200
        result = response.json()

        # Validate alternatives
        assert len(result["alternatives"]) == 3
        assert result["alternatives"][0]["id"] == "A"
        assert result["alternatives"][1]["id"] == "B"
        assert result["alternatives"][2]["id"] == "C"

        # Validate RICE scores
        for alt in result["alternatives"]:
            assert alt["rice"]["score"] > 0
            assert 1 <= alt["rice"]["reach"] <= 10
            assert 1 <= alt["rice"]["impact"] <= 10
            assert 1 <= alt["rice"]["confidence"] <= 10
            assert 1 <= alt["rice"]["effort"] <= 10

        # Validate performance
        assert duration < 45000  # <45s

        # Verify trade-off analysis
        assert result["tradeoff_analysis"]["recommendation"]
        assert result["tradeoff_analysis"]["comparison_matrix"]
```

### 10.3 Performance Tests

```python
@pytest.mark.performance
class TestPerformance:
    """Performance benchmarks"""

    @pytest.mark.asyncio
    async def test_gi_formula_performance(self, gi_service):
        """Benchmark GI Formula performance"""
        problems = [
            "How to reduce deployment time?",
            "How to improve code quality?",
            "How to scale the database?"
        ]

        durations = []
        for problem in problems:
            start = datetime.now()
            result = await gi_service.generate_insight(problem)
            duration = (datetime.now() - start).total_seconds() * 1000
            durations.append(duration)

        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        assert avg_duration < 25000  # Average <25s
        assert max_duration < 30000  # Max <30s

        print(f"\nGI Formula Performance:")
        print(f"  Average: {avg_duration:.0f}ms")
        print(f"  Max: {max_duration:.0f}ms")

    @pytest.mark.asyncio
    async def test_ck_theory_performance(self, ck_service):
        """Benchmark C-K Theory performance"""
        challenges = [
            "Design an authentication system",
            "Design a logging architecture",
            "Design a notification service"
        ]

        durations = []
        for challenge in challenges:
            start = datetime.now()
            result = await ck_service.generate_alternatives(challenge)
            duration = (datetime.now() - start).total_seconds() * 1000
            durations.append(duration)

        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)

        assert avg_duration < 40000  # Average <40s
        assert max_duration < 45000  # Max <45s

        print(f"\nC-K Theory Performance:")
        print(f"  Average: {avg_duration:.0f}ms")
        print(f"  Max: {max_duration:.0f}ms")

    @pytest.mark.asyncio
    async def test_cache_performance(self, gi_service):
        """Benchmark cache performance"""
        problem = "Test cache speed"

        # First call (cache miss)
        await gi_service.generate_insight(problem)

        # Subsequent calls (cache hit)
        cache_durations = []
        for _ in range(10):
            start = datetime.now()
            await gi_service.generate_insight(problem)
            duration = (datetime.now() - start).total_seconds() * 1000
            cache_durations.append(duration)

        avg_cache_duration = sum(cache_durations) / len(cache_durations)

        assert avg_cache_duration < 100  # <100ms from cache

        print(f"\nCache Performance:")
        print(f"  Average: {avg_cache_duration:.1f}ms")
```

---

## 11. Implementation Checklist

### Phase 1: Foundation (Week 1, Days 1-2)

- [ ] **Data Models**
  - [ ] Create `backend/app/models/gi_formula.py`
  - [ ] Create `backend/app/models/ck_theory.py`
  - [ ] Add Pydantic models with validation
  - [ ] Write model unit tests

- [ ] **Database Schema**
  - [ ] Create migration scripts
  - [ ] Add SQLite tables (`gi_insights`, `ck_designs`, `design_feedback`)
  - [ ] Add indexes for performance
  - [ ] Add full-text search indexes

### Phase 2: Service Layer (Week 1, Days 3-5)

- [ ] **GI Formula Service**
  - [ ] Create `backend/app/services/gi_formula_service.py`
  - [ ] Implement 5-stage pipeline
  - [ ] Add MCP Sequential integration
  - [ ] Add caching layer
  - [ ] Add Obsidian integration
  - [ ] Write service unit tests (>85% coverage)

- [ ] **C-K Theory Service**
  - [ ] Create `backend/app/services/ck_theory_service.py`
  - [ ] Implement concept space exploration
  - [ ] Implement parallel alternative generation
  - [ ] Add RICE scoring logic
  - [ ] Add trade-off analysis
  - [ ] Add MCP Sequential + Context7 integration
  - [ ] Write service unit tests (>85% coverage)

### Phase 3: API Layer (Week 2, Days 1-2)

- [ ] **GI Formula Router**
  - [ ] Create `backend/app/routers/gi_formula.py`
  - [ ] Implement all endpoints
  - [ ] Add request/response validation
  - [ ] Add error handling
  - [ ] Write router unit tests

- [ ] **C-K Theory Router**
  - [ ] Create `backend/app/routers/ck_theory.py`
  - [ ] Implement all endpoints
  - [ ] Add request/response validation
  - [ ] Add error handling
  - [ ] Write router unit tests

- [ ] **Main App Integration**
  - [ ] Register routers in `backend/main.py`
  - [ ] Add startup initialization
  - [ ] Add health check endpoints

### Phase 4: Integration & Testing (Week 2, Days 3-4)

- [ ] **Integration Tests**
  - [ ] End-to-end GI Formula tests
  - [ ] End-to-end C-K Theory tests
  - [ ] MCP integration tests
  - [ ] Obsidian integration tests
  - [ ] Cache integration tests

- [ ] **Performance Tests**
  - [ ] GI Formula performance benchmarks
  - [ ] C-K Theory performance benchmarks
  - [ ] Cache performance benchmarks
  - [ ] Load testing (concurrent requests)

- [ ] **Error Handling Tests**
  - [ ] MCP unavailability scenarios
  - [ ] Timeout handling
  - [ ] Invalid input handling
  - [ ] Fallback mechanism testing

### Phase 5: Documentation & Deployment (Week 2, Day 5)

- [ ] **Documentation**
  - [ ] API documentation (OpenAPI/Swagger)
  - [ ] Service documentation
  - [ ] Usage examples
  - [ ] Deployment guide

- [ ] **Deployment**
  - [ ] Update requirements.txt
  - [ ] Update docker-compose.yml (if needed)
  - [ ] Environment variable configuration
  - [ ] Production deployment checklist

- [ ] **Monitoring**
  - [ ] Add performance metrics
  - [ ] Add error tracking
  - [ ] Add usage analytics
  - [ ] Add alerting

---

## Risk Assessment & Mitigation

### High-Risk Items

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **MCP unavailability** | High | Medium | Implement fallback system with native AI |
| **Performance <30s/45s** | High | Medium | Aggressive caching + parallel execution |
| **Sequential stages timeout** | Medium | Medium | Per-stage timeout + partial result handling |
| **Obsidian vault unavailable** | Low | Low | Queue saves + retry mechanism |
| **Cache corruption** | Medium | Low | Multi-tier cache + validation |

### Rollback Strategy

1. **Feature flags** for gradual rollout
2. **Database migrations** are reversible
3. **API versioning** (/api/v1/) allows coexistence
4. **Monitoring alerts** for degraded performance

---

## Success Criteria

### Functional Requirements
- ✅ GI Formula generates 5-stage insights
- ✅ C-K Theory generates exactly 3 alternatives with RICE scores
- ✅ All results saved to Obsidian automatically
- ✅ Search functionality across historical results
- ✅ API fully documented with OpenAPI

### Non-Functional Requirements
- ✅ GI Formula executes in <30 seconds (95th percentile)
- ✅ C-K Theory executes in <45 seconds (95th percentile)
- ✅ Cache hit latency <100ms
- ✅ Test coverage >85%
- ✅ System remains operational with MCP down (fallback mode)

### Quality Gates
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ Performance benchmarks met
- ✅ Code review approved
- ✅ Documentation complete

---

## Appendix

### A. Prompt Engineering for MCP

**GI Formula - Observation Stage**

```
You are conducting the OBSERVATION stage of the Genius Insight Formula.

Problem: {problem}
Context: {context}

Your task:
1. Identify key facts and data points
2. List observable patterns
3. Note assumptions and constraints
4. Highlight critical variables

Format your response as structured JSON:
{
  "facts": ["fact1", "fact2", ...],
  "patterns": ["pattern1", "pattern2", ...],
  "assumptions": ["assumption1", ...],
  "variables": ["var1", "var2", ...]
}
```

**C-K Theory - Alternative Generation**

```
You are generating a DESIGN ALTERNATIVE using C-K Theory.

Challenge: {challenge}
Constraints: {constraints}
Concept Origin: {concept_origin}

Your task:
1. Develop a complete design alternative
2. Explain technical approach in detail
3. Identify dependencies and risks
4. Estimate timeline and effort

Format as structured JSON:
{
  "title": "Alternative A: [Title]",
  "description": "[Detailed description]",
  "technical_approach": "[Implementation strategy]",
  "pros": ["pro1", "pro2", ...],
  "cons": ["con1", "con2", ...],
  "risks": ["risk1", "risk2", ...],
  "dependencies": ["dep1", ...],
  "timeline": "[estimate]"
}
```

### B. Obsidian Template Examples

**GI Insight Template**

```markdown
---
date: 2025-11-20
time: 14:30
project: UDO-Development-Platform
type: gi-insight
tags: [insight, gi-formula, automation]
insight_id: gi-2025-11-20-001
---

# GI Insight: [Problem Title]

## Problem Statement
[Original problem]

## Insight Journey

### 1. Observation
[Key facts and observations]

### 2. Connections
[Conceptual connections identified]

### 3. Patterns
[Recurring patterns found]

### 4. Synthesis
[Integrated insight]

### 5. Bias Check
**Biases Detected**: [List]
**Mitigation Strategies**: [List]

## Final Insight
[Synthesized actionable insight]

## Metadata
- Duration: [X]ms
- Generated: [timestamp]
- Confidence: [score]
```

**C-K Design Template**

```markdown
---
date: 2025-11-20
time: 15:45
project: UDO-Development-Platform
type: ck-design
tags: [design, ck-theory, alternatives]
design_id: ck-2025-11-20-001
---

# C-K Design: [Challenge Title]

## Design Challenge
[Original challenge]

## Alternative A: [Title]
**RICE Score**: [score]
- Reach: [1-10]
- Impact: [1-10]
- Confidence: [1-10]
- Effort: [1-10]

**Description**: [...]
**Pros**: [...]
**Cons**: [...]
**Risks**: [...]

## Alternative B: [Title]
[Same structure]

## Alternative C: [Title]
[Same structure]

## Trade-off Analysis
[Comparative analysis]

## Recommendation
[Final recommendation with reasoning]
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-20
**Review Status**: Ready for Implementation
**Estimated Implementation Time**: 2 weeks (80 hours)
