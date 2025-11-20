# GI Formula & C-K Theory Visual Architecture

**Date**: 2025-11-20
**Purpose**: Visual representation of system architecture for quick understanding

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           UDO Development Platform                       │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Backend (Port 8000)                  │    │
│  │                                                                  │    │
│  │  ┌──────────────────────┐        ┌──────────────────────┐      │    │
│  │  │  GI Formula Service  │        │  C-K Theory Service  │      │    │
│  │  │                      │        │                      │      │    │
│  │  │  • 5-Stage Pipeline  │        │  • 3 Alternatives    │      │    │
│  │  │  • <30s Target       │        │  • RICE Scoring      │      │    │
│  │  │  • Sequential MCP    │        │  • <45s Target       │      │    │
│  │  └──────────┬───────────┘        └──────────┬───────────┘      │    │
│  │             │                               │                   │    │
│  │             └───────────────┬───────────────┘                   │    │
│  │                             │                                   │    │
│  │  ┌──────────────────────────▼────────────────────────────┐     │    │
│  │  │            MCP Integration Layer                       │     │    │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐            │     │    │
│  │  │  │Sequential│  │Context7  │  │Obsidian  │            │     │    │
│  │  │  │   MCP    │  │   MCP    │  │   MCP    │            │     │    │
│  │  │  │          │  │          │  │          │            │     │    │
│  │  │  │ AI Logic │  │ Patterns │  │ Storage  │            │     │    │
│  │  │  └──────────┘  └──────────┘  └──────────┘            │     │    │
│  │  └──────────────────────────────────────────────────────┘     │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────┐     │    │
│  │  │        Data Persistence Layer                        │     │    │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐           │     │    │
│  │  │  │  Redis   │  │  SQLite  │  │ Obsidian │           │     │    │
│  │  │  │  Cache   │  │  Storage │  │  Vault   │           │     │    │
│  │  │  │          │  │          │  │          │           │     │    │
│  │  │  │ <100ms   │  │ <500ms   │  │ Knowledge│           │     │    │
│  │  │  └──────────┘  └──────────┘  └──────────┘           │     │    │
│  │  └──────────────────────────────────────────────────────┘     │    │
│  └──────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## GI Formula Flow Diagram

```
User Request: "How to reduce API latency by 50%?"
│
▼
┌──────────────────────────────────────────────────────┐
│            GIFormulaService.generate_insight()        │
└──────────────┬───────────────────────────────────────┘
               │
               │ Check Cache (Memory → Redis → SQLite)
               ├─ HIT (70% probability) → Return cached result (<100ms)
               │
               └─ MISS (30% probability) → Continue generation
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Stage 1: OBSERVATION                     │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Sequential MCP: "Identify key facts and data"        │    │
│  │  Output: {facts: [...], patterns: [...]}              │    │
│  │  Duration: ~5s                                         │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Stage 2: CONNECTION                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Sequential MCP: "Link related concepts"              │    │
│  │  Input: Observation results                           │    │
│  │  Output: {connections: [...]}                         │    │
│  │  Duration: ~6s                                         │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Stage 3: PATTERN                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Sequential MCP: "Recognize recurring patterns"       │    │
│  │  Input: Connection results                            │    │
│  │  Output: {patterns: [...]}                            │    │
│  │  Duration: ~6s                                         │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Stage 4: SYNTHESIS                       │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Sequential MCP: "Combine into actionable insight"    │    │
│  │  Input: Pattern results                               │    │
│  │  Output: {insight: "..."}                             │    │
│  │  Duration: ~7s                                         │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Stage 5: BIAS CHECK                      │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Sequential MCP: "Validate for cognitive biases"      │    │
│  │  Input: Synthesis results                             │    │
│  │  Output: {biases: [...], mitigations: [...]}          │    │
│  │  Duration: ~6s                                         │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │  Save to Obsidian (Async)  │
              │  + Cache all levels        │
              └────────────┬───────────────┘
                           │
                           ▼
                  Return GIFormulaResult
                  Total: ~30s
```

---

## C-K Theory Flow Diagram

```
User Request: "Design authentication system with multiple providers"
│
▼
┌──────────────────────────────────────────────────────┐
│       CKTheoryService.generate_alternatives()        │
└──────────────┬───────────────────────────────────────┘
               │
               │ Check Cache
               ├─ HIT → Return cached result
               │
               └─ MISS → Continue generation
                  │
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│              Step 1: CONCEPT SPACE EXPLORATION                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Sequential MCP: "Explore design dimensions"           │    │
│  │  Output: [ConceptA, ConceptB, ConceptC]               │    │
│  │  Duration: ~10s                                        │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           Step 2: GENERATE 3 ALTERNATIVES (PARALLEL)            │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │  Alternative A  │  │  Alternative B  │  │  Alternative C  ││
│  │  ┌──────────┐   │  │  ┌──────────┐   │  │  ┌──────────┐   ││
│  │  │Sequential│   │  │  │Sequential│   │  │  │Sequential│   ││
│  │  │   MCP    │   │  │  │   MCP    │   │  │  │   MCP    │   ││
│  │  └────┬─────┘   │  │  └────┬─────┘   │  │  └────┬─────┘   ││
│  │       │         │  │       │         │  │       │         ││
│  │       ▼         │  │       ▼         │  │       ▼         ││
│  │  ┌──────────┐   │  │  ┌──────────┐   │  │  ┌──────────┐   ││
│  │  │Context7  │   │  │  │Context7  │   │  │  │Context7  │   ││
│  │  │Patterns  │   │  │  │Patterns  │   │  │  │Patterns  │   ││
│  │  └────┬─────┘   │  │  └────┬─────┘   │  │  └────┬─────┘   ││
│  │       │         │  │       │         │  │       │         ││
│  │       ▼         │  │       ▼         │  │       ▼         ││
│  │  JWT + OAuth2  │  │  Session-Based  │  │  WebAuthn       ││
│  │  ~8s          │  │  ~8s            │  │  ~8s            ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
│                                                                 │
│                    Total: ~25s (parallel)                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│          Step 3: CALCULATE RICE SCORES (PARALLEL)               │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  RICE(A)    │  │  RICE(B)    │  │  RICE(C)    │            │
│  │  R×I×C/E    │  │  R×I×C/E    │  │  R×I×C/E    │            │
│  │  = 6.72     │  │  = 5.40     │  │  = 6.30     │            │
│  │  ~2s        │  │  ~2s        │  │  ~2s        │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│                    Total: ~5s (parallel)                        │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              Step 4: TRADE-OFF ANALYSIS                         │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  Sequential MCP: "Compare alternatives"               │    │
│  │  Output: {                                            │    │
│  │    summary: "...",                                    │    │
│  │    recommendation: "Choose A because...",             │    │
│  │    comparison_matrix: {...}                          │    │
│  │  }                                                    │    │
│  │  Duration: ~5s                                        │    │
│  └────────────────────────────────────────────────────────┘    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────────┐
              │  Save to Obsidian (Async)  │
              │  + Cache all levels        │
              └────────────┬───────────────┘
                           │
                           ▼
                  Return CKTheoryResult
                  Total: ~45s
```

---

## Caching Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Request Arrives                             │
└──────────────┬─────────────────────────────────────────────────┘
               │
               ▼
     ┌──────────────────┐
     │  Generate Cache  │
     │  Key (Hash)      │
     └─────────┬────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Level 1: Memory Cache (In-Process)                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Python Dict                                       │     │
│  │  TTL: 5 minutes                                    │     │
│  │  Latency: <1ms                                     │     │
│  │  Hit Rate: 20% (recent queries)                    │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               └─ HIT → Return (fastest)                      │
│               │                                              │
│               └─ MISS → Continue to Level 2                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Level 2: Redis Cache (Distributed)                         │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Redis Key-Value Store                             │     │
│  │  TTL: 7 days                                       │     │
│  │  Latency: <100ms                                   │     │
│  │  Hit Rate: 50% (session queries)                   │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               ├─ HIT → Store L1 + Return                     │
│               │                                              │
│               └─ MISS → Continue to Level 3                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Level 3: SQLite Database (Persistent)                      │
│  ┌────────────────────────────────────────────────────┐     │
│  │  SQLite with FTS5 Full-Text Search                 │     │
│  │  TTL: Permanent (soft deletes)                     │     │
│  │  Latency: <500ms                                   │     │
│  │  Hit Rate: 30% (historical queries)                │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               ├─ HIT → Store L2 + L1 + Return               │
│               │                                              │
│               └─ MISS → Generate new result                  │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Level 4: Generate New (MCP Services)                       │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Sequential MCP + Context7 + Obsidian             │     │
│  │  Latency: 30-45s                                   │     │
│  │  Result: Fresh generation                          │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               └─ Store L3 + L2 + L1 + Return                │
└──────────────────────────────────────────────────────────────┘

Overall Performance:
- 70% Cache Hit Rate
- Average Response Time: 5 seconds (with cache)
- 30% Miss Rate requiring full generation
```

---

## Error Handling & Fallback Flow

```
┌────────────────────────────────────────────────────────────────┐
│              User Request (GI Formula or C-K Theory)            │
└──────────────┬─────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│  Strategy 1: Sequential MCP (Primary)                        │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Structured AI reasoning with MCP                  │     │
│  │  Highest quality output                            │     │
│  │  Performance: 30-45s                               │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               ├─ SUCCESS (95% cases) → Return result         │
│               │                                              │
│               └─ FAIL (5% cases) → Try Strategy 2            │
│                  Errors: Timeout, Connection, Server Down     │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Strategy 2: Native AI Fallback (Secondary)                 │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Direct OpenAI/Anthropic API calls                 │     │
│  │  Good quality output (less structured)             │     │
│  │  Performance: 15-25s                               │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               ├─ SUCCESS (90% of remaining) → Return result  │
│               │  with metadata["fallback_used"] = true       │
│               │                                              │
│               └─ FAIL (10% of remaining) → Try Strategy 3    │
│                  Errors: API Key, Rate Limit, Server Error   │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│  Strategy 3: Template-Based Emergency (Tertiary)            │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Pre-defined templates with placeholders           │     │
│  │  Basic output for system availability              │     │
│  │  Performance: <1s                                  │     │
│  └────────────┬───────────────────────────────────────┘     │
│               │                                              │
│               └─ ALWAYS SUCCEEDS → Return template result    │
│                  with metadata["template_used"] = true       │
└──────────────────────────────────────────────────────────────┘

Retry Logic (Strategy 1 & 2):
┌────────────────────────────────────────────┐
│  Attempt 1 (immediate)                     │
│    ↓ FAIL                                  │
│  Wait 2 seconds                            │
│  Attempt 2 (exponential backoff)           │
│    ↓ FAIL                                  │
│  Wait 4 seconds                            │
│  Attempt 3 (final attempt)                 │
│    ↓ FAIL                                  │
│  Move to next strategy                     │
└────────────────────────────────────────────┘

Success Rate by Strategy:
- Strategy 1 (MCP): 95.0%
- Strategy 2 (Native): 4.5% (90% of remaining 5%)
- Strategy 3 (Template): 0.5% (emergency only)
- Overall Availability: 100%
```

---

## Performance Optimization Strategy

```
┌────────────────────────────────────────────────────────────────┐
│                   GI Formula Optimization                       │
│                                                                 │
│  Sequential Stages (Cannot Parallelize):                       │
│  ┌──────────────┬──────────────┬────────────────────────┐     │
│  │   Stage      │   Target     │   Optimization         │     │
│  ├──────────────┼──────────────┼────────────────────────┤     │
│  │ Observation  │   <5s        │ Focused prompts        │     │
│  │ Connection   │   <6s        │ Template matching      │     │
│  │ Pattern      │   <6s        │ Pattern library        │     │
│  │ Synthesis    │   <7s        │ Structured output      │     │
│  │ Bias Check   │   <6s        │ Checklist validation   │     │
│  └──────────────┴──────────────┴────────────────────────┘     │
│                                                                 │
│  Total: 30s (sequential execution)                             │
│                                                                 │
│  Post-Processing (Parallel):                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │ Save Cache  │  │Save Obsidian│  │  Analytics  │           │
│  │   ~100ms    │  │   ~200ms    │  │   ~50ms     │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│  Max: 200ms (parallel execution)                               │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│                   C-K Theory Optimization                       │
│                                                                 │
│  Maximum Parallelization:                                      │
│  ┌──────────────┬──────────────┬────────────────────────┐     │
│  │   Step       │   Target     │   Optimization         │     │
│  ├──────────────┼──────────────┼────────────────────────┤     │
│  │ Concept      │   <10s       │ Structured search      │     │
│  │ Exploration  │              │ (sequential)           │     │
│  ├──────────────┼──────────────┼────────────────────────┤     │
│  │ Alternative  │   <25s       │ 3 parallel workers     │     │
│  │ Generation   │              │ (~8s each)             │     │
│  ├──────────────┼──────────────┼────────────────────────┤     │
│  │ RICE Scores  │   <5s        │ 3 parallel calcs       │     │
│  │              │              │ (~2s each)             │     │
│  ├──────────────┼──────────────┼────────────────────────┤     │
│  │ Trade-off    │   <5s        │ Matrix comparison      │     │
│  │ Analysis     │              │ (sequential)           │     │
│  └──────────────┴──────────────┴────────────────────────┘     │
│                                                                 │
│  Total: 45s (mixed parallel/sequential)                        │
│                                                                 │
│  Parallelization Timeline:                                     │
│  ┌────────────────────────────────────────────────────┐       │
│  │ 0s     Concept Exploration (sequential)            │       │
│  │        │                                            │       │
│  │ 10s    ├─ Alt A (8s) ─┐                            │       │
│  │        ├─ Alt B (8s) ─┼─ Parallel                  │       │
│  │        ├─ Alt C (8s) ─┘                            │       │
│  │        │                                            │       │
│  │ 35s    ├─ RICE A (2s) ─┐                           │       │
│  │        ├─ RICE B (2s) ─┼─ Parallel                 │       │
│  │        ├─ RICE C (2s) ─┘                           │       │
│  │        │                                            │       │
│  │ 40s    Trade-off Analysis (sequential)             │       │
│  │        │                                            │       │
│  │ 45s    Done                                         │       │
│  └────────────────────────────────────────────────────┘       │
└────────────────────────────────────────────────────────────────┘

Cache Strategy for Both Services:
┌────────────────────────────────────────────────────────────────┐
│  Without Cache: 30-45s every request                           │
│  With Cache:                                                   │
│    - Level 1 (Memory): <1ms    (20% hit rate)                 │
│    - Level 2 (Redis):  <100ms  (50% hit rate)                 │
│    - Level 3 (SQLite): <500ms  (30% hit rate)                 │
│                                                                 │
│  Overall: 70% cached, average 5s response time                 │
│  Cache Miss: 30% require full generation (30-45s)              │
└────────────────────────────────────────────────────────────────┘
```

---

## Database Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                         GI Formula Data                          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              gi_insights (Main Table)                 │       │
│  │  ┌────────────────────────────────────────────┐      │       │
│  │  │ id (PK)              TEXT                  │      │       │
│  │  │ problem              TEXT                  │      │       │
│  │  │ final_insight        TEXT                  │      │       │
│  │  │ project              TEXT                  │      │       │
│  │  │ stage_observation    JSON                  │      │       │
│  │  │ stage_connection     JSON                  │      │       │
│  │  │ stage_pattern        JSON                  │      │       │
│  │  │ stage_synthesis      JSON                  │      │       │
│  │  │ stage_bias_check     JSON                  │      │       │
│  │  │ biases_detected      JSON                  │      │       │
│  │  │ confidence_score     REAL                  │      │       │
│  │  │ total_duration_ms    INTEGER               │      │       │
│  │  │ obsidian_path        TEXT                  │      │       │
│  │  │ created_at           TIMESTAMP             │      │       │
│  │  │ deleted_at           TIMESTAMP (nullable)   │      │       │
│  │  └────────────────────────────────────────────┘      │       │
│  └──────────────────────────────────────────────────────┘       │
│                           │                                      │
│                           │ FTS5 Full-Text Search                │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────┐       │
│  │           gi_insights_fts (Search Index)              │       │
│  │  Search Fields: problem, final_insight                │       │
│  └──────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                       C-K Theory Data                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐       │
│  │              ck_designs (Main Table)                  │       │
│  │  ┌────────────────────────────────────────────┐      │       │
│  │  │ id (PK)              TEXT                  │      │       │
│  │  │ challenge            TEXT                  │      │       │
│  │  │ project              TEXT                  │      │       │
│  │  │ alternatives         JSON (3 items)        │      │       │
│  │  │ tradeoff_analysis    JSON                  │      │       │
│  │  │ constraints          JSON                  │      │       │
│  │  │ total_duration_ms    INTEGER               │      │       │
│  │  │ obsidian_path        TEXT                  │      │       │
│  │  │ feedback_count       INTEGER               │      │       │
│  │  │ avg_rating           REAL                  │      │       │
│  │  │ created_at           TIMESTAMP             │      │       │
│  │  │ deleted_at           TIMESTAMP (nullable)   │      │       │
│  │  └────────────────────────────────────────────┘      │       │
│  └──────────┬───────────────────────────────────────────┘       │
│             │                                                    │
│             │ One-to-Many                                        │
│             ▼                                                    │
│  ┌──────────────────────────────────────────────────────┐       │
│  │          design_feedback (Feedback Table)             │       │
│  │  ┌────────────────────────────────────────────┐      │       │
│  │  │ id (PK)              INTEGER AUTOINCREMENT │      │       │
│  │  │ design_id (FK)       TEXT                  │───┐  │       │
│  │  │ alternative_id       TEXT (A/B/C)          │   │  │       │
│  │  │ rating               INTEGER (1-5)         │   │  │       │
│  │  │ comments             TEXT                  │   │  │       │
│  │  │ selected_alternative TEXT                  │   │  │       │
│  │  │ outcome              TEXT                  │   │  │       │
│  │  │ created_at           TIMESTAMP             │   │  │       │
│  │  └────────────────────────────────────────────┘   │  │       │
│  └───────────────────────────────────────────────────┼──┘       │
│                           │                          │           │
│                           │ FTS5                     │ FK        │
│                           ▼                          │           │
│  ┌──────────────────────────────────────────────────▼──┐        │
│  │         ck_designs_fts (Search Index)               │        │
│  │  Search Fields: challenge                           │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘

Indexes for Performance:
- idx_gi_insights_created (created_at DESC)
- idx_gi_insights_project (project)
- idx_ck_designs_created (created_at DESC)
- idx_ck_designs_project (project)
- idx_feedback_design (design_id)
```

---

## API Request/Response Flow

### GI Formula API Flow

```
Client
  │
  │ POST /api/v1/gi-formula/generate
  │ {
  │   "problem": "How to reduce API latency?",
  │   "context": {"current": "200ms", "target": "100ms"}
  │ }
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Router (gi_formula.py)             │
│  1. Pydantic validates request                          │
│  2. Check authentication (if required)                  │
│  3. Call GIFormulaService                               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│           GIFormulaService (gi_formula_service.py)      │
│  1. Check cache (Memory → Redis → SQLite)               │
│  2. If miss: Execute 5-stage pipeline                   │
│  3. Save to all cache levels                            │
│  4. Save to Obsidian (async)                            │
│  5. Return GIFormulaResult                              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
Client Response:
{
  "id": "gi-2025-11-20-001",
  "problem": "How to reduce API latency?",
  "stages": {
    "observation": {...},
    "connection": {...},
    "pattern": {...},
    "synthesis": {...},
    "bias_check": {...}
  },
  "final_insight": "Implement connection pooling...",
  "bias_check": {
    "biases_detected": [],
    "confidence_score": 0.92
  },
  "total_duration_ms": 28000,
  "created_at": "2025-11-20T14:30:00",
  "obsidian_path": "개발일지/2025-11-20/GI-Insight.md"
}
```

### C-K Theory API Flow

```
Client
  │
  │ POST /api/v1/ck-theory/generate
  │ {
  │   "challenge": "Design auth system",
  │   "constraints": {"budget": "2 weeks", "security": "high"}
  │ }
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Router (ck_theory.py)              │
│  1. Pydantic validates request                          │
│  2. Validate constraints                                │
│  3. Call CKTheoryService                                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│           CKTheoryService (ck_theory_service.py)        │
│  1. Check cache                                         │
│  2. If miss: Explore concept space                      │
│  3. Generate 3 alternatives (parallel)                  │
│  4. Calculate RICE scores (parallel)                    │
│  5. Perform trade-off analysis                          │
│  6. Save to all cache levels                            │
│  7. Save to Obsidian (async)                            │
│  8. Return CKTheoryResult                               │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
Client Response:
{
  "id": "ck-2025-11-20-001",
  "challenge": "Design auth system",
  "alternatives": [
    {
      "id": "A",
      "title": "JWT + OAuth2 Hybrid",
      "rice": {"score": 6.72},
      "pros": [...],
      "cons": [...],
      "risks": [...]
    },
    {"id": "B", "title": "Session-Based", "rice": {"score": 5.40}},
    {"id": "C", "title": "WebAuthn", "rice": {"score": 6.30}}
  ],
  "tradeoff_analysis": {
    "summary": "...",
    "recommendation": "Choose A because...",
    "comparison_matrix": {...}
  },
  "total_duration_ms": 42000,
  "obsidian_path": "개발일지/2025-11-20/CK-Design.md"
}
```

---

## Implementation Status

```
Phase 1: Foundation ✅ COMPLETE
├─ Architecture Design ✅
├─ Data Models ✅
│  ├─ gi_formula.py (320 lines) ✅
│  └─ ck_theory.py (480 lines) ✅
├─ Database Schema ✅
└─ Documentation ✅

Phase 2: Services ⏳ NEXT
├─ gi_formula_service.py ⏳
│  ├─ 5-Stage Pipeline
│  ├─ MCP Integration
│  └─ Cache Manager
└─ ck_theory_service.py ⏳
   ├─ Concept Exploration
   ├─ Alternative Generation
   └─ RICE Calculation

Phase 3: API Layer ⏳
├─ gi_formula.py (router) ⏳
└─ ck_theory.py (router) ⏳

Phase 4: Testing ⏳
├─ Unit Tests ⏳
├─ Integration Tests ⏳
└─ Performance Tests ⏳

Phase 5: Deployment ⏳
├─ Documentation ⏳
└─ Monitoring ⏳

Estimated Time Remaining: 64 hours (8 working days)
```

---

**Document Version**: 1.0
**Last Updated**: 2025-11-20 16:30
**Status**: Visual Architecture Complete
**Purpose**: Quick visual reference for system understanding
