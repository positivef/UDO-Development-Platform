# Week 1 Implementation Guide - Concrete Actions

## 🚀 Day 1: Monday - Foundation Fix (Uncertainty: 🟢 DETERMINISTIC)

### Morning Sprint (9am-12pm): Type Safety & Database Setup

#### Task 1: Fix Mypy Errors (1 hour)
```bash
# Run mypy to see current errors
mypy --strict src/ tests/

# Expected errors to fix:
# 1. Optional type annotations (3 errors)
# 2. Dict type specifications (2 errors)
# 3. Import type errors (2 errors)
```

**Concrete Fixes**:

```python
# src/uncertainty_map_v3.py - Line 142
# BEFORE:
def calculate_decision_uncertainty(self, confidence: float = None):
    timestamp = None

# AFTER:
from typing import Optional

def calculate_decision_uncertainty(self, confidence: Optional[float] = None):
    timestamp: Optional[str] = None
```

```python
# src/services/ai_orchestration_service.py - Line 78
# BEFORE:
def get_metadata(self) -> Dict:
    return {}

# AFTER:
from typing import Dict, Any

def get_metadata(self) -> Dict[str, Any]:
    return {}
```

#### Task 2: PostgreSQL + pgvector Setup (2 hours)

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  db:
    image: ankane/pgvector:v0.5.1-pg15
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: udo_dev
      POSTGRES_PASSWORD: ${DB_PASSWORD:-dev_password_123}
      POSTGRES_DB: udo_v3
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U udo_dev"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy lru

  api:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://udo_dev:${DB_PASSWORD:-dev_password_123}@db:5432/udo_v3
      REDIS_URL: redis://redis:6379/0
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app

volumes:
  postgres_data:
```

Create `scripts/init_db.sql`:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Projects table
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    owner_id UUID NOT NULL,
    current_phase VARCHAR(50) DEFAULT 'ideation',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Project contexts for RAG
CREATE TABLE project_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_path VARCHAR(500),
    content_chunk TEXT,
    embedding vector(1536),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create vector similarity search index
CREATE INDEX ON project_contexts USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Uncertainty logs
CREATE TABLE uncertainty_logs (
    id BIGSERIAL PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    state VARCHAR(50) NOT NULL,
    score FLOAT NOT NULL CHECK (score >= 0 AND score <= 100),
    decision_metadata JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create time-series index for performance
CREATE INDEX idx_uncertainty_logs_time ON uncertainty_logs(created_at DESC);

-- RLHF feedback table
CREATE TABLE uncertainty_feedback (
    id BIGSERIAL PRIMARY KEY,
    log_id BIGINT REFERENCES uncertainty_logs(id),
    rating INTEGER CHECK (rating IN (-1, 1)),
    correction TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Task 3: Database Migration Strategy (1 hour)

Create `backend/app/db/dual_write_manager.py`:
```python
"""Dual-write pattern for safe migration from mock to PostgreSQL"""

import asyncio
from typing import Any, Dict, Optional
import asyncpg
from redis import Redis
import json
import logging

logger = logging.getLogger(__name__)


class DualWriteManager:
    """Manages dual-write pattern during migration period"""

    def __init__(self, postgres_url: str, redis_url: str):
        self.postgres_url = postgres_url
        self.redis = Redis.from_url(redis_url)
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.shadow_mode = True  # Start in shadow mode
        self.write_success_rate = {"postgres": 0, "redis": 0}

    async def initialize(self):
        """Initialize database connections"""
        self.postgres_pool = await asyncpg.create_pool(
            self.postgres_url,
            min_size=5,
            max_size=20
        )

    async def write_project_context(self,
                                   project_id: str,
                                   data: Dict[str, Any]) -> bool:
        """
        Dual-write to both PostgreSQL and Redis
        Track success rates for confidence building
        """
        results = await asyncio.gather(
            self._write_to_postgres(project_id, data),
            self._write_to_redis(project_id, data),
            return_exceptions=True
        )

        # Track success rates
        if not isinstance(results[0], Exception):
            self.write_success_rate["postgres"] += 1
        if not isinstance(results[1], Exception):
            self.write_success_rate["redis"] += 1

        # Check if we can promote PostgreSQL to primary
        if self._check_promotion_criteria():
            await self._promote_postgres_to_primary()

        # Return success if at least one write succeeded
        return any(not isinstance(r, Exception) for r in results)

    async def _write_to_postgres(self,
                                project_id: str,
                                data: Dict[str, Any]) -> bool:
        """Write to PostgreSQL"""
        try:
            async with self.postgres_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO project_contexts
                    (project_id, file_path, content_chunk, metadata)
                    VALUES ($1, $2, $3, $4)
                """, project_id, data.get('file_path'),
                    data.get('content'), json.dumps(data.get('metadata', {})))
            return True
        except Exception as e:
            logger.error(f"PostgreSQL write failed: {e}")
            return False

    async def _write_to_redis(self,
                             project_id: str,
                             data: Dict[str, Any]) -> bool:
        """Write to Redis (current system)"""
        try:
            key = f"project:{project_id}:context"
            self.redis.hset(key, data.get('file_path', ''),
                          json.dumps(data))
            return True
        except Exception as e:
            logger.error(f"Redis write failed: {e}")
            return False

    def _check_promotion_criteria(self) -> bool:
        """
        Check if PostgreSQL is ready to become primary
        Criteria: 95% success rate over last 100 writes
        """
        total = sum(self.write_success_rate.values())
        if total < 100:
            return False

        pg_rate = self.write_success_rate["postgres"] / max(total, 1)
        return pg_rate >= 0.95

    async def _promote_postgres_to_primary(self):
        """Promote PostgreSQL to primary data store"""
        self.shadow_mode = False
        logger.info("PostgreSQL promoted to primary data store!")
        # TODO: Trigger notification to team
```

### Afternoon Sprint (1pm-5pm): Monitoring & Measurement

#### Task 4: Monitoring Setup (2 hours)

Create `backend/app/monitoring/metrics.py`:
```python
"""Performance monitoring with uncertainty tracking"""

from functools import wraps
import time
from typing import Callable, Any
from prometheus_client import Counter, Histogram, Gauge
import structlog

logger = structlog.get_logger()

# Define metrics
api_latency = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['method', 'endpoint', 'status'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]
)

api_requests = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

uncertainty_score = Gauge(
    'system_uncertainty_score',
    'Current system uncertainty level',
    ['component']
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['query_type']
)


def measure_latency(endpoint: str = None):
    """Decorator to measure API endpoint latency"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                logger.error(f"API error in {endpoint}", error=str(e))
                raise
            finally:
                duration = time.time() - start_time

                # Record metrics
                api_latency.labels(
                    method=kwargs.get('request', {}).get('method', 'GET'),
                    endpoint=endpoint or func.__name__,
                    status=status
                ).observe(duration)

                api_requests.labels(
                    method=kwargs.get('request', {}).get('method', 'GET'),
                    endpoint=endpoint or func.__name__,
                    status=status
                ).inc()

                # Log if slow
                if duration > 0.2:  # 200ms threshold
                    logger.warning(
                        f"Slow API call",
                        endpoint=endpoint,
                        duration=duration
                    )

        return wrapper
    return decorator


def track_uncertainty(component: str, score: float):
    """Update uncertainty score for a component"""
    uncertainty_score.labels(component=component).set(score)

    if score > 0.5:  # High uncertainty
        logger.warning(
            f"High uncertainty detected",
            component=component,
            score=score
        )


class PerformanceMonitor:
    """Central performance monitoring with circuit breaker"""

    def __init__(self):
        self.latency_buffer = []
        self.error_count = 0
        self.circuit_open = False

    def record_latency(self, latency: float):
        """Record latency and check for degradation"""
        self.latency_buffer.append(latency)
        if len(self.latency_buffer) > 100:
            self.latency_buffer.pop(0)

        # Check P95
        if len(self.latency_buffer) >= 20:
            sorted_latencies = sorted(self.latency_buffer)
            p95_index = int(len(sorted_latencies) * 0.95)
            p95_latency = sorted_latencies[p95_index]

            if p95_latency > 0.2:  # 200ms threshold
                logger.warning(f"P95 latency exceeds threshold: {p95_latency}s")
                self._activate_degraded_mode()

    def _activate_degraded_mode(self):
        """Activate degraded mode to protect system"""
        if not self.circuit_open:
            self.circuit_open = True
            logger.critical("Circuit breaker OPEN - activating degraded mode")
            # TODO: Notify team via Slack
            # TODO: Switch to cache-only mode
```

#### Task 5: Create Grafana Dashboard Config (1 hour)

Create `monitoring/grafana/dashboards/udo-dashboard.json`:
```json
{
  "dashboard": {
    "title": "UDO Platform - Uncertainty-Aware Monitoring",
    "panels": [
      {
        "title": "API Latency (P50/P95/P99)",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(api_request_duration_seconds_bucket[5m]))",
            "legendFormat": "P99"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [0.2],
                "type": "gt"
              },
              "query": {
                "params": ["P95", "5m"]
              },
              "reducer": {
                "type": "avg"
              },
              "type": "query"
            }
          ],
          "frequency": "60s",
          "name": "High P95 Latency"
        }
      },
      {
        "title": "System Uncertainty Levels",
        "targets": [
          {
            "expr": "system_uncertainty_score",
            "legendFormat": "{{component}}"
          }
        ],
        "thresholds": [
          {"value": 0.3, "color": "green"},
          {"value": 0.5, "color": "yellow"},
          {"value": 0.7, "color": "red"}
        ]
      },
      {
        "title": "AI API Success Rate",
        "targets": [
          {
            "expr": "rate(api_requests_total{status=\"success\"}[5m]) / rate(api_requests_total[5m])",
            "legendFormat": "Success Rate"
          }
        ]
      },
      {
        "title": "Database Query Performance",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))",
            "legendFormat": "{{query_type}}"
          }
        ]
      }
    ]
  }
}
```

### Evening Review (5pm-6pm): Testing & Documentation

#### Task 6: Create Load Test Script (30 minutes)

Create `tests/load/k6_baseline.js`:
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

const errorRate = new Rate('errors');

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Ramp up
    { duration: '3m', target: 100 },  // Stay at 100 users
    { duration: '1m', target: 200 },  // Peak load
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'], // 95% under 200ms
    errors: ['rate<0.02'],            // Error rate under 2%
  },
};

export default function () {
  // Test project context API
  const payload = JSON.stringify({
    project_id: 'test-project',
    query: 'How to implement authentication?'
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer test-token',
    },
  };

  const res = http.post('http://localhost:8000/api/query', payload, params);

  const success = check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
    'has uncertainty map': (r) => {
      const body = JSON.parse(r.body);
      return body.uncertainty_map !== undefined;
    },
  });

  errorRate.add(!success);
  sleep(1);
}
```

## 📝 Day 1 Checklist with Verification

### Morning Verification (12pm)
```bash
# 1. Check mypy passes
mypy --strict src/ tests/
# Expected: "Success: no issues found"

# 2. Check database is running
docker-compose ps
# Expected: db, redis, api all "Up"

# 3. Test database connection
docker-compose exec db psql -U udo_dev -d udo_v3 -c "SELECT 1;"
# Expected: "1"

# 4. Verify pgvector is enabled
docker-compose exec db psql -U udo_dev -d udo_v3 -c "SELECT * FROM pg_extension WHERE extname='vector';"
# Expected: Shows vector extension
```

### Afternoon Verification (5pm)
```bash
# 1. Check Prometheus metrics
curl http://localhost:8000/metrics | grep api_request
# Expected: Shows metric definitions

# 2. Access Grafana
open http://localhost:3000
# Expected: Dashboard loads with panels

# 3. Run load test
k6 run tests/load/k6_baseline.js
# Expected: All thresholds pass

# 4. Check dual-write is working
docker-compose logs api | grep "write_success_rate"
# Expected: Shows both postgres and redis writes
```

### End of Day Report Template
```markdown
## Day 1 Completion Report

### ✅ Completed
- [ ] Fixed X/7 mypy errors
- [ ] Database setup with pgvector
- [ ] Dual-write manager implemented
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] Baseline load test passing

### 🟡 Uncertainties Discovered
- Database migration complexity: [Adjusted from 🟢 to 🟡]
- Team velocity: [Actual vs planned hours]

### 🔴 Blockers
- [List any blockers]

### 📊 Metrics
- Time spent: X hours
- Velocity: X% of planned
- Uncertainty reduction: X%

### 🎯 Tomorrow's Adjusted Plan
- [Based on today's learnings]
```

---

## 🚦 Go/No-Go Decision Points

### End of Day 1 Decision
```python
def day1_decision():
    """Decide whether to continue as planned or adjust"""

    checklist = {
        "mypy_fixed": False,      # Must be True
        "db_running": False,       # Must be True
        "monitoring_up": False,    # Should be True
        "load_test_pass": False,   # Should be True
    }

    if all([checklist["mypy_fixed"], checklist["db_running"]]):
        if checklist["monitoring_up"] and checklist["load_test_pass"]:
            return "GREEN: Proceed as planned"
        else:
            return "YELLOW: Proceed with caution, adjust Day 2"
    else:
        return "RED: Stop and fix critical issues"
```

---

*This is your concrete Day 1 plan. Execute step by step and track progress in real-time.*