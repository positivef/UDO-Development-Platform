# GI Formula & C-K Theory API Guide

## Overview

This guide covers the GI Formula (Genius Insight) and C-K Theory (Concept-Knowledge Design) services - two powerful AI-assisted tools for problem-solving and design exploration.

## Table of Contents

- [GI Formula API](#gi-formula-api)
  - [Generate Insight](#generate-insight)
  - [Get Insight by ID](#get-insight-by-id)
  - [List Recent Insights](#list-recent-insights)
  - [Delete Insight](#delete-insight)
- [C-K Theory API](#ck-theory-api)
  - [Generate Design Alternatives](#generate-design-alternatives)
  - [Get Design by ID](#get-design-by-id)
  - [List Recent Designs](#list-recent-designs)
  - [Add Feedback](#add-feedback)
  - [Get Feedback](#get-feedback)
- [Usage Examples](#usage-examples)
- [Performance Targets](#performance-targets)
- [Error Handling](#error-handling)

---

## GI Formula API

The GI Formula uses a 5-stage process to generate actionable insights:

1. **Observation**: Extract key facts and constraints
2. **Connection**: Find relationships between facts
3. **Pattern**: Identify recurring patterns and trends
4. **Synthesis**: Combine insights into actionable solution
5. **Bias Check**: Validate against cognitive biases

### Generate Insight

**POST** `/api/v1/gi-formula`

Generate a new insight using the 5-stage GI Formula process.

#### Request Body

```json
{
  "problem": "How can we reduce API response time by 50%?",
  "context": {
    "current_latency": "200ms",
    "target_latency": "100ms",
    "bottleneck": "database queries"
  },
  "project": "UDO-Development-Platform"
}
```

#### Response

```json
{
  "id": "gi-2025-11-20-abc123",
  "problem": "How can we reduce API response time by 50%?",
  "stages": {
    "observation": {
      "stage": "observation",
      "content": "Key facts: Current latency is 200ms, target is 100ms...",
      "metadata": {"facts_count": 5},
      "duration_ms": 4800,
      "timestamp": "2025-11-20T14:30:00"
    },
    "connection": {...},
    "pattern": {...},
    "synthesis": {...},
    "bias_check": {...}
  },
  "final_insight": "Implement connection pooling and add Redis cache layer for frequently accessed data...",
  "bias_check": {
    "biases_detected": [],
    "mitigation_strategies": [],
    "confidence_score": 0.92
  },
  "total_duration_ms": 28500,
  "created_at": "2025-11-20T14:30:00",
  "obsidian_path": "개발일지/2025-11-20/GI-Insight-API-Performance.md",
  "metadata": {...}
}
```

#### Performance

- **Target**: <30 seconds
- **Typical**: 25-30 seconds
- **Stages**: 5-7 seconds each

#### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/gi-formula" \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "How can we reduce API response time by 50%?",
    "context": {
      "current_latency": "200ms",
      "target_latency": "100ms"
    }
  }'
```

### Get Insight by ID

**GET** `/api/v1/gi-formula/{insight_id}`

Retrieve a specific insight by its unique identifier.

#### Path Parameters

- `insight_id` (string): Format `gi-YYYY-MM-DD-{hash}`

#### Response

Same as Generate Insight response.

#### cURL Example

```bash
curl "http://localhost:8000/api/v1/gi-formula/gi-2025-11-20-abc123"
```

### List Recent Insights

**GET** `/api/v1/gi-formula`

List recent insights with pagination.

#### Query Parameters

- `project` (string, optional): Filter by project name
- `limit` (integer, default: 10, range: 1-100): Maximum results
- `offset` (integer, default: 0): Pagination offset

#### Response

```json
[
  {
    "id": "gi-2025-11-20-abc123",
    "problem": "How can we reduce API response time by 50%?",
    "final_insight": "Implement connection pooling and add Redis cache...",
    "confidence_score": 0.92,
    "total_duration_ms": 28500,
    "created_at": "2025-11-20T14:30:00",
    "project": "UDO-Development-Platform"
  },
  ...
]
```

#### cURL Example

```bash
curl "http://localhost:8000/api/v1/gi-formula?limit=5&project=UDO-Development-Platform"
```

### Delete Insight

**DELETE** `/api/v1/gi-formula/{insight_id}`

Delete an insight from the cache.

#### Response

```json
{
  "message": "Insight gi-2025-11-20-abc123 deleted successfully",
  "insight_id": "gi-2025-11-20-abc123"
}
```

---

## C-K Theory API

The C-K Theory uses a 4-stage process to generate design alternatives:

1. **Concept Exploration**: Generate 3 distinct design concepts
2. **Alternative Generation**: Develop detailed alternatives (A, B, C)
3. **RICE Scoring**: Calculate (Reach × Impact × Confidence) / Effort
4. **Trade-off Analysis**: Compare alternatives and recommend

### Generate Design Alternatives

**POST** `/api/v1/ck-theory`

Generate 3 design alternatives using C-K Theory.

#### Request Body

```json
{
  "challenge": "Design an authentication system that supports multiple providers",
  "constraints": {
    "budget": "2 weeks",
    "team_size": 2,
    "security_requirement": "high",
    "complexity": "medium"
  },
  "project": "UDO-Development-Platform"
}
```

**Allowed constraint keys**:
- `budget`
- `team_size`
- `timeline`
- `complexity`
- `security_requirement`
- `performance_requirement`
- `scalability_requirement`
- `maintainability_requirement`

#### Response

```json
{
  "id": "ck-2025-11-20-xyz789",
  "challenge": "Design an authentication system that supports multiple providers",
  "alternatives": [
    {
      "id": "A",
      "title": "JWT + OAuth2 Hybrid Authentication",
      "description": "Implement a hybrid authentication system...",
      "concept_origin": "Security-first approach with flexibility",
      "knowledge_basis": ["OAuth2 specification", "JWT best practices"],
      "rice": {
        "reach": 8,
        "impact": 7,
        "confidence": 6,
        "effort": 5,
        "score": 6.72
      },
      "pros": ["Industry-standard security", "Flexible provider support"],
      "cons": ["Complex token management"],
      "risks": ["Token expiration edge cases"],
      "technical_approach": "Use FastAPI OAuth2 password flow...",
      "dependencies": ["python-jose", "passlib"],
      "estimated_timeline": "2 weeks"
    },
    {
      "id": "B",
      "title": "Session-Based Authentication",
      "rice": {"score": 5.40},
      ...
    },
    {
      "id": "C",
      "title": "Passwordless + WebAuthn",
      "rice": {"score": 6.30},
      ...
    }
  ],
  "tradeoff_analysis": {
    "summary": "Alternative A offers the best balance...",
    "recommendation": "Choose Alternative A (JWT + OAuth2 Hybrid) because...",
    "comparison_matrix": {
      "security": {"A": "High", "B": "Medium", "C": "High"},
      "complexity": {"A": "Medium", "B": "Low", "C": "High"}
    },
    "decision_tree": [
      "If security is top priority → Choose A or C",
      "If simplicity is critical → Choose B"
    ]
  },
  "total_duration_ms": 42000,
  "created_at": "2025-11-20T15:45:00",
  "obsidian_path": "개발일지/2025-11-20/CK-Design-Auth-System.md"
}
```

#### Performance

- **Target**: <45 seconds
- **Typical**: 40-45 seconds
- **Parallel Generation**: 3 alternatives generated concurrently

#### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/ck-theory" \
  -H "Content-Type: application/json" \
  -d '{
    "challenge": "Design an authentication system that supports multiple providers",
    "constraints": {
      "team_size": 2,
      "security_requirement": "high"
    }
  }'
```

### Get Design by ID

**GET** `/api/v1/ck-theory/{design_id}`

Retrieve a specific design by its unique identifier.

#### Path Parameters

- `design_id` (string): Format `ck-YYYY-MM-DD-{hash}`

#### Response

Same as Generate Design response.

### List Recent Designs

**GET** `/api/v1/ck-theory`

List recent design explorations.

#### Query Parameters

- `project` (string, optional): Filter by project name
- `limit` (integer, default: 10, range: 1-100)
- `offset` (integer, default: 0)

#### Response

```json
[
  {
    "id": "ck-2025-11-20-xyz789",
    "challenge": "Design an authentication system...",
    "recommended_alternative": "A",
    "avg_rice_score": 6.14,
    "total_duration_ms": 42000,
    "created_at": "2025-11-20T15:45:00",
    "project": "UDO-Development-Platform"
  },
  ...
]
```

### Add Feedback

**POST** `/api/v1/ck-theory/{design_id}/feedback`

Add feedback for a design exploration (used for learning).

#### Request Body

```json
{
  "design_id": "ck-2025-11-20-xyz789",
  "alternative_id": "A",
  "rating": 5,
  "comments": "Excellent balance of security and flexibility",
  "selected_alternative": "A",
  "outcome": "success"
}
```

**Field descriptions**:
- `rating`: 1-5 stars
- `alternative_id`: A, B, or C (optional, for specific alternative feedback)
- `selected_alternative`: Which alternative was actually implemented
- `outcome`: "success", "partial", or "failure"

#### Response

```json
{
  "message": "Feedback added successfully for design ck-2025-11-20-xyz789",
  "design_id": "ck-2025-11-20-xyz789",
  "rating": 5,
  "selected_alternative": "A"
}
```

### Get Feedback

**GET** `/api/v1/ck-theory/{design_id}/feedback`

Retrieve all feedback for a specific design.

#### Response

```json
[
  {
    "design_id": "ck-2025-11-20-xyz789",
    "alternative_id": "A",
    "rating": 5,
    "comments": "Excellent balance of security and flexibility",
    "selected_alternative": "A",
    "outcome": "success"
  },
  ...
]
```

---

## Usage Examples

### Python Example: GI Formula

```python
import requests

# Generate insight
response = requests.post(
    "http://localhost:8000/api/v1/gi-formula",
    json={
        "problem": "How can we reduce API response time by 50%?",
        "context": {
            "current_latency": "200ms",
            "target_latency": "100ms"
        }
    }
)

result = response.json()
print(f"Insight ID: {result['id']}")
print(f"Final Insight: {result['final_insight']}")
print(f"Confidence: {result['bias_check']['confidence_score']:.2%}")
```

### Python Example: C-K Theory

```python
import requests

# Generate design alternatives
response = requests.post(
    "http://localhost:8000/api/v1/ck-theory",
    json={
        "challenge": "Design a caching strategy for API performance",
        "constraints": {
            "timeline": "1 week",
            "performance_requirement": "high"
        }
    }
)

result = response.json()

# Print alternatives
for alt in result['alternatives']:
    print(f"Alternative {alt['id']}: {alt['title']}")
    print(f"  RICE Score: {alt['rice']['score']:.2f}")
    print(f"  Timeline: {alt['estimated_timeline']}")

# Print recommendation
print(f"\nRecommendation: {result['tradeoff_analysis']['recommendation'][:100]}...")

# Add feedback
feedback_response = requests.post(
    f"http://localhost:8000/api/v1/ck-theory/{result['id']}/feedback",
    json={
        "design_id": result['id'],
        "alternative_id": "A",
        "rating": 5,
        "selected_alternative": "A",
        "outcome": "success"
    }
)
```

### JavaScript Example: GI Formula

```javascript
// Generate insight
const response = await fetch('http://localhost:8000/api/v1/gi-formula', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    problem: 'How can we reduce API response time by 50%?',
    context: {
      current_latency: '200ms',
      target_latency: '100ms'
    }
  })
});

const result = await response.json();
console.log(`Insight ID: ${result.id}`);
console.log(`Final Insight: ${result.final_insight}`);
console.log(`Confidence: ${(result.bias_check.confidence_score * 100).toFixed(0)}%`);
```

---

## Performance Targets

| Service | Target | Typical | Stages |
|---------|--------|---------|--------|
| **GI Formula** | <30s | 25-30s | 5 sequential stages |
| **C-K Theory** | <45s | 40-45s | 3 parallel alternatives + analysis |

### Performance Optimization

- **Caching**: 3-tier (Memory → Redis → SQLite)
- **Parallel Processing**: C-K Theory generates 3 alternatives concurrently
- **Graceful Degradation**: Falls back to rule-based logic if MCP unavailable
- **Async Operations**: Obsidian sync runs in background

---

## Error Handling

### HTTP Status Codes

- `200`: Success
- `400`: Invalid request (validation error)
- `404`: Resource not found
- `500`: Internal server error

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

#### GI Formula

- **400**: Problem statement too short (<3 words)
- **400**: Invalid problem statement (spam filter)
- **500**: Insight generation timeout
- **500**: Sequential MCP unavailable

#### C-K Theory

- **400**: Challenge too short (<3 words)
- **400**: Invalid constraint keys
- **400**: Design ID mismatch in feedback
- **500**: Alternative generation failed
- **500**: RICE score calculation error

### Retry Strategy

```python
import time
import requests

def generate_insight_with_retry(problem, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/api/v1/gi-formula",
                json={"problem": problem},
                timeout=60  # 60 second timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Timeout. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")
            raise

# Usage
result = generate_insight_with_retry("How can we improve performance?")
```

---

## Health Check

Both services provide health check endpoints:

**GET** `/api/v1/gi-formula/health`
**GET** `/api/v1/ck-theory/health`

```json
{
  "status": "healthy",
  "service": "gi-formula",
  "version": "1.0.0",
  "features": {
    "sequential_mcp": true,
    "obsidian_sync": true,
    "caching": true
  }
}
```

---

## Integration with Obsidian

Both services automatically save results to Obsidian vault:

- **GI Formula**: `개발일지/YYYY-MM-DD/GI-Insight-{problem}.md`
- **C-K Theory**: `개발일지/YYYY-MM-DD/CK-Design-{challenge}.md`

### Obsidian Note Format

Notes include:
- YAML frontmatter with metadata
- Structured markdown content
- Links to related notes
- Tags for easy discovery

---

## Best Practices

1. **Problem Statements**: Be specific and include measurable goals
2. **Context**: Provide relevant technical details and constraints
3. **Constraints**: Use allowed constraint keys for C-K Theory
4. **Feedback**: Always provide feedback for C-K designs to improve future recommendations
5. **Caching**: Leverage cache by checking if similar insight/design already exists
6. **Error Handling**: Implement retry logic with exponential backoff
7. **Timeouts**: Set appropriate client-side timeouts (60s recommended)

---

## Support

For issues or questions:
- Check `/api/health` for service status
- Review error messages in response
- Check logs for detailed error information
- Verify Sequential MCP is available for best results
