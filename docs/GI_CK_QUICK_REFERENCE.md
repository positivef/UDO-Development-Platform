# GI Formula & C-K Theory Quick Reference

**Last Updated**: 2025-11-20
**Status**: Phase 1 Complete (Data Models ✅)

---

## Quick Start

### What's Been Implemented (Phase 1)

✅ **Architecture Design** (18,500 words)
- System component diagrams
- Data flow sequences
- Performance optimization strategy
- Integration patterns
- Testing strategy

✅ **Data Models** (800 lines)
- GI Formula models (6 classes)
- C-K Theory models (7 classes)
- Pydantic validation
- OpenAPI schema examples

✅ **Documentation**
- Architecture document
- Implementation summary
- Quick reference (this file)

### What's Next (Phase 2-5)

⏳ **Services** (Est. 24 hours)
- GIFormulaService
- CKTheoryService

⏳ **Routers** (Est. 16 hours)
- API endpoints
- Request/response handling

⏳ **Testing** (Est. 16 hours)
- Unit tests (>85% coverage)
- Integration tests
- Performance benchmarks

⏳ **Deployment** (Est. 8 hours)
- Documentation
- Monitoring setup

**Total Time Remaining**: 64 hours (8 working days)

---

## GI Formula Overview

### Purpose
Generate actionable insights through 5-stage AI-powered analysis.

### 5 Stages
1. **Observation** - Identify key facts and data
2. **Connection** - Link related concepts
3. **Pattern** - Recognize recurring patterns
4. **Synthesis** - Combine into insight
5. **Bias Check** - Validate for cognitive biases

### Performance Target
**<30 seconds** execution time

### API Endpoint
```bash
POST /api/v1/gi-formula/generate
Content-Type: application/json

{
  "problem": "How can we reduce API response time by 50%?",
  "context": {
    "current_latency": "200ms",
    "target_latency": "100ms"
  },
  "project": "UDO-Development-Platform"
}
```

### Response
```json
{
  "id": "gi-2025-11-20-001",
  "problem": "How can we reduce API response time by 50%?",
  "stages": {
    "observation": { "content": "...", "duration_ms": 4800 },
    "connection": { "content": "...", "duration_ms": 5200 },
    "pattern": { "content": "...", "duration_ms": 5800 },
    "synthesis": { "content": "...", "duration_ms": 6500 },
    "bias_check": { "content": "...", "duration_ms": 5700 }
  },
  "final_insight": "Implement connection pooling...",
  "bias_check": {
    "biases_detected": [],
    "confidence_score": 0.92
  },
  "total_duration_ms": 28000,
  "obsidian_path": "개발일지/2025-11-20/GI-Insight-API-Performance.md"
}
```

### Use Cases
- Problem solving
- Performance optimization
- Architecture decisions
- Technical debt analysis
- Feature design

---

## C-K Theory Overview

### Purpose
Generate 3 design alternatives using Concept-Knowledge theory with RICE scoring.

### Process
1. **Explore Concept Space** - Identify design dimensions
2. **Generate Alternatives** - Create 3 distinct approaches (A, B, C)
3. **RICE Scoring** - Calculate prioritization scores
4. **Trade-off Analysis** - Compare alternatives

### Performance Target
**<45 seconds** execution time

### RICE Scoring Formula
```
RICE Score = (Reach × Impact × Confidence) / Effort

Where:
- Reach: 1-10 (users affected)
- Impact: 1-10 (impact level)
- Confidence: 1-10 (estimate confidence)
- Effort: 1-10 (implementation effort)
```

### API Endpoint
```bash
POST /api/v1/ck-theory/generate
Content-Type: application/json

{
  "challenge": "Design an authentication system supporting multiple providers",
  "constraints": {
    "budget": "2 weeks",
    "team_size": 2,
    "security_requirement": "high"
  },
  "project": "UDO-Development-Platform"
}
```

### Response
```json
{
  "id": "ck-2025-11-20-001",
  "challenge": "Design an authentication system...",
  "alternatives": [
    {
      "id": "A",
      "title": "JWT + OAuth2 Hybrid",
      "description": "...",
      "rice": {
        "reach": 8,
        "impact": 7,
        "confidence": 6,
        "effort": 5,
        "score": 6.72
      },
      "pros": ["Industry-standard", "Flexible"],
      "cons": ["Complex token management"],
      "risks": ["Token expiration edge cases"]
    },
    {
      "id": "B",
      "title": "Session-Based Auth",
      "rice": { "score": 5.40 }
    },
    {
      "id": "C",
      "title": "Passwordless + WebAuthn",
      "rice": { "score": 6.30 }
    }
  ],
  "tradeoff_analysis": {
    "summary": "Alternative A offers the best balance...",
    "recommendation": "Choose A because...",
    "comparison_matrix": {
      "security": {"A": "High", "B": "Medium", "C": "High"}
    }
  },
  "total_duration_ms": 42000
}
```

### Use Cases
- Architecture design
- Technology selection
- Feature planning
- Risk assessment
- Trade-off evaluation

---

## Data Models Reference

### GI Formula Models

**Location**: `backend/app/models/gi_formula.py`

```python
from app.models import (
    StageType,           # Enum: observation, connection, pattern, synthesis, bias_check
    StageResult,         # Single stage output
    BiasCheckResult,     # Bias detection result
    GIFormulaRequest,    # API request
    GIFormulaResult,     # Complete result
    GIInsightSummary,    # List view summary
)
```

**Example Usage**:
```python
# Create request
request = GIFormulaRequest(
    problem="How to improve test coverage?",
    context={"current": 70, "target": 90}
)

# Validate automatically via Pydantic
assert len(request.problem.split()) >= 3
```

### C-K Theory Models

**Location**: `backend/app/models/ck_theory.py`

```python
from app.models import (
    RICEScore,           # RICE scoring
    DesignAlternative,   # Single alternative
    TradeoffAnalysis,    # Comparative analysis
    CKTheoryRequest,     # API request
    CKTheoryResult,      # Complete result
    DesignSummary,       # List view summary
    DesignFeedback,      # Feedback collection
)
```

**Example Usage**:
```python
# Create RICE score (auto-calculates)
rice = RICEScore(
    reach=8,
    impact=7,
    confidence=6,
    effort=5
)
assert rice.score == 6.72  # (8 × 7 × 6) / 5

# Create alternative
alt = DesignAlternative(
    id="A",
    title="JWT + OAuth2",
    description="Hybrid authentication...",
    rice=rice,
    pros=["Standard", "Flexible"],
    cons=["Complex"],
    risks=["Token expiration"]
)
```

---

## Integration Points

### MCP Servers

#### Sequential MCP (Primary)
**Purpose**: Structured AI reasoning
**Used By**: Both GI Formula & C-K Theory
**Capabilities**:
- Multi-step reasoning
- Hypothesis testing
- Evidence gathering
- Systematic analysis

#### Context7 MCP (Patterns)
**Purpose**: Design pattern reference
**Used By**: C-K Theory only
**Capabilities**:
- Official documentation lookup
- Best practices
- Implementation examples

#### Obsidian MCP (Persistence)
**Purpose**: Knowledge base storage
**Used By**: Both services
**Capabilities**:
- Automatic note creation
- Markdown formatting
- YAML frontmatter
- Tagging and search

### Caching Strategy

```
┌─────────────────┐
│  Request        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐ <1ms   ✅ HIT → Return
│  Memory Cache   │───────────────────────────→
└────────┬────────┘
         │ MISS
         ▼
┌─────────────────┐ <100ms ✅ HIT → Store + Return
│  Redis Cache    │───────────────────────────→
└────────┬────────┘
         │ MISS
         ▼
┌─────────────────┐ <500ms ✅ HIT → Store + Return
│  SQLite DB      │───────────────────────────→
└────────┬────────┘
         │ MISS
         ▼
┌─────────────────┐ <30s   ✅ Generate → Store all levels
│  Generate New   │───────────────────────────→
└─────────────────┘
```

---

## Performance Optimization

### GI Formula Optimization

| Stage | Target | Strategy |
|-------|--------|----------|
| Observation | <5s | Focused data gathering |
| Connection | <6s | Parallel concept linking |
| Pattern | <6s | Template matching |
| Synthesis | <7s | Final integration |
| Bias Check | <6s | Checklist validation |
| **Total** | **<30s** | Sequential + caching |

### C-K Theory Optimization

| Step | Target | Strategy |
|------|--------|----------|
| Concept Exploration | <10s | Structured search |
| 3 Alternatives | <25s | Parallel generation (~8s each) |
| RICE Calculation | <5s | 3 parallel calculations |
| Trade-off Analysis | <5s | Comparative matrix |
| **Total** | **<45s** | Maximum parallelization |

### Caching Performance

| Cache Level | Latency | Hit Rate | TTL |
|-------------|---------|----------|-----|
| Memory | <1ms | 20% | 5 minutes |
| Redis | <100ms | 50% | 7 days |
| SQLite | <500ms | 30% | Permanent |

**Overall Cache Hit Rate**: 70%
**Average Response Time**: 5 seconds (with cache)

---

## Error Handling

### Graceful Degradation

```
1. Try Sequential MCP
   ↓ FAIL
2. Try Native AI
   ↓ FAIL
3. Use Template
   ↓
4. Return with metadata["fallback_used"] = true
```

### Timeout Handling

- Per-stage timeout: 10 seconds
- Total timeout: 35s (GI), 50s (C-K)
- Partial results returned if timeout
- Clear timeout messages to user

### Validation Errors

- Pydantic validates all inputs
- 422 status for validation errors
- Clear error messages
- Example payloads in error response

---

## Database Schema

### Tables

```sql
-- GI Insights
gi_insights (
    id, problem, final_insight, project,
    stage_observation, stage_connection, stage_pattern,
    stage_synthesis, stage_bias_check,
    biases_detected, mitigation_strategies, confidence_score,
    total_duration_ms, context, obsidian_path,
    created_at, updated_at, deleted_at
)

-- C-K Designs
ck_designs (
    id, challenge, project, alternatives,
    tradeoff_analysis, total_duration_ms,
    constraints, obsidian_path,
    created_at, updated_at, deleted_at,
    feedback_count, avg_rating
)

-- Design Feedback
design_feedback (
    id, design_id, alternative_id,
    rating, comments, selected_alternative, outcome,
    created_at
)
```

### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_gi_insights_created ON gi_insights(created_at DESC);
CREATE INDEX idx_gi_insights_project ON gi_insights(project);
CREATE INDEX idx_ck_designs_created ON ck_designs(created_at DESC);
CREATE INDEX idx_ck_designs_project ON ck_designs(project);
CREATE INDEX idx_feedback_design ON design_feedback(design_id);

-- Full-text search
CREATE VIRTUAL TABLE gi_insights_fts USING fts5(
    problem, final_insight, content='gi_insights'
);
CREATE VIRTUAL TABLE ck_designs_fts USING fts5(
    challenge, content='ck_designs'
);
```

---

## Testing Checklist

### Unit Tests (Phase 4)

- [ ] Data model validation
- [ ] Service method success cases
- [ ] Service method error cases
- [ ] Cache hit/miss scenarios
- [ ] MCP integration (mocked)
- [ ] Timeout handling
- [ ] Fallback mechanisms

### Integration Tests (Phase 4)

- [ ] End-to-end GI Formula
- [ ] End-to-end C-K Theory
- [ ] Real MCP servers
- [ ] Obsidian save verification
- [ ] Cache persistence

### Performance Tests (Phase 4)

- [ ] GI Formula <30s (avg)
- [ ] C-K Theory <45s (avg)
- [ ] Cache <100ms
- [ ] 10 concurrent users

**Coverage Target**: >85%

---

## Implementation Progress

### Phase 1: Foundation ✅ (Complete)

- ✅ Architecture design (18,500 words)
- ✅ Data models (800 lines)
  - ✅ GI Formula models (6 classes)
  - ✅ C-K Theory models (7 classes)
  - ✅ Pydantic validation
  - ✅ OpenAPI examples
- ✅ Database schema design
- ✅ API endpoint specifications
- ✅ Integration strategy
- ✅ Testing strategy

**Time Spent**: 2.5 hours

### Phase 2: Services ⏳ (Next)

- [ ] GIFormulaService implementation
- [ ] CKTheoryService implementation
- [ ] MCP client integration
- [ ] Cache manager
- [ ] Service unit tests

**Estimated Time**: 24 hours (3 days)

### Phase 3: API Layer ⏳

- [ ] GI Formula router
- [ ] C-K Theory router
- [ ] Main app integration
- [ ] Router unit tests

**Estimated Time**: 16 hours (2 days)

### Phase 4: Testing ⏳

- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Error handling validation
- [ ] Load testing

**Estimated Time**: 16 hours (2 days)

### Phase 5: Deployment ⏳

- [ ] OpenAPI documentation
- [ ] Usage examples
- [ ] Deployment guide
- [ ] Monitoring setup

**Estimated Time**: 8 hours (1 day)

**Total Remaining**: 64 hours (8 working days)

---

## Key Files

### Documentation
- `docs/GI_CK_ARCHITECTURE_DESIGN.md` - Full architecture (18,500 words)
- `docs/GI_CK_IMPLEMENTATION_SUMMARY.md` - Implementation status
- `docs/GI_CK_QUICK_REFERENCE.md` - This file

### Data Models (Phase 1 ✅)
- `backend/app/models/gi_formula.py` - GI Formula models
- `backend/app/models/ck_theory.py` - C-K Theory models
- `backend/app/models/__init__.py` - Model exports

### Services (Phase 2 ⏳)
- `backend/app/services/gi_formula_service.py` - To be implemented
- `backend/app/services/ck_theory_service.py` - To be implemented

### Routers (Phase 3 ⏳)
- `backend/app/routers/gi_formula.py` - To be implemented
- `backend/app/routers/ck_theory.py` - To be implemented

### Tests (Phase 4 ⏳)
- `backend/tests/test_gi_formula_*.py` - To be implemented
- `backend/tests/test_ck_theory_*.py` - To be implemented

---

## Quick Commands

### Run Tests (When Implemented)
```bash
# All tests
pytest backend/tests/test_gi_*.py backend/tests/test_ck_*.py -v

# Unit tests only
pytest backend/tests/test_gi_formula_service.py -v

# Integration tests
pytest backend/tests/test_gi_ck_integration.py -v

# Performance tests
pytest backend/tests/test_gi_ck_performance.py -v --benchmark
```

### Start Backend
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### API Documentation
```
http://localhost:8000/docs
http://localhost:8000/redoc
```

---

## Support & Resources

### Architecture Details
See: `docs/GI_CK_ARCHITECTURE_DESIGN.md`

### Implementation Status
See: `docs/GI_CK_IMPLEMENTATION_SUMMARY.md`

### Issues & Questions
- Check architecture document first
- Review data model examples
- Test with mock data
- Log detailed errors for debugging

---

**Document Version**: 1.0
**Last Updated**: 2025-11-20 16:15
**Status**: Phase 1 Complete ✅
**Next Phase**: Service Implementation (24 hours)
