# Time Tracking System - Quick Reference Card

## Installation

```bash
# 1. Run database migration
cd backend/migrations
python run_migration.py 002_time_tracking_schema.sql

# 2. Start backend
cd backend
.venv\Scripts\activate
uvicorn main:app --reload

# 3. Verify
curl http://localhost:8000/api/time-tracking/health
```

## Basic Usage

### Python API

```python
from backend.app.services.time_tracking_service import TimeTrackingService
from backend.app.models.time_tracking import TaskType, Phase, AIModel

# Initialize service
service = TimeTrackingService(pool=db_pool, obsidian_service=obsidian)

# Start tracking
session_id = await service.start_task(
    task_id="fix_bug_123",
    task_type=TaskType.ERROR_RESOLUTION,
    phase=Phase.IMPLEMENTATION,
    ai_used=AIModel.CLAUDE
)

# Pause if needed
await service.pause_task(session_id)

# Resume
await service.resume_task(session_id)

# End tracking
metrics = await service.end_task(session_id, success=True)

print(f"Saved: {metrics.time_saved_hours:.2f}h")
print(f"ROI: {metrics.roi_percentage:.0f}%")
```

### REST API

```bash
# Start tracking
curl -X POST http://localhost:8000/api/time-tracking/start \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "fix_bug_123",
    "task_type": "error_resolution",
    "phase": "implementation",
    "ai_used": "claude"
  }'
# Returns: {"session_id": "uuid", "baseline_seconds": 1800}

# End tracking
curl -X POST http://localhost:8000/api/time-tracking/end/{session_id} \
  -H "Content-Type: application/json" \
  -d '{"success": true}'
# Returns: {"metrics": {...}}

# Get ROI
curl http://localhost:8000/api/time-tracking/roi?period=weekly
# Returns: Complete ROI report

# Get bottlenecks
curl http://localhost:8000/api/time-tracking/bottlenecks
# Returns: List of slow tasks
```

## Task Types

| Type | Baseline | Example |
|------|----------|---------|
| `error_resolution` | 30min | Fixing 401 auth error |
| `design_task` | 2h | API design, schema design |
| `implementation` | 4h | Feature development |
| `testing` | 1h | Writing tests |
| `documentation` | 1h | README, API docs |
| `code_review` | 30min | PR review |
| `refactoring` | 3h | Code restructuring |
| `debugging` | 45min | Bug investigation |
| `phase_transition` | 15min | Phase changes |
| `other` | 30min | Miscellaneous |

## AI Models

- `claude` - 85% efficiency (best for errors, reviews)
- `codex` - 75% efficiency (best for implementation)
- `gemini` - 70% efficiency (best for design)
- `multi` - 90% efficiency (best overall)
- `none` - No AI assistance

## Development Phases

- `ideation` - Initial planning
- `design` - Architecture and design
- `mvp` - Minimum viable product
- `implementation` - Main development
- `testing` - Testing and QA

## Database Queries

```sql
-- Active sessions
SELECT * FROM active_sessions;

-- Daily summary (last 7 days)
SELECT * FROM daily_summary
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date DESC;

-- Task type performance
SELECT * FROM task_type_performance
ORDER BY avg_saved_seconds DESC;

-- AI model performance
SELECT * FROM ai_model_performance
ORDER BY total_saved_hours DESC;

-- Phase performance
SELECT * FROM phase_performance
ORDER BY total_saved_hours DESC;

-- Recent bottlenecks
SELECT
    task_type,
    AVG(duration_seconds) as avg_duration,
    AVG(baseline_seconds) as avg_baseline,
    COUNT(*) as frequency
FROM task_sessions
WHERE end_time >= NOW() - INTERVAL '7 days'
    AND duration_seconds > baseline_seconds
GROUP BY task_type
ORDER BY (AVG(duration_seconds) - AVG(baseline_seconds)) DESC;
```

## Common Patterns

### Pattern 1: Track Critical Task

```python
session_id = await time_tracking.start_task(
    task_id=f"critical_fix_{issue_id}",
    task_type=TaskType.ERROR_RESOLUTION,
    phase=Phase.IMPLEMENTATION,
    ai_used=AIModel.CLAUDE,
    metadata={"priority": "critical", "severity": "high"}
)

try:
    await fix_issue(issue_id)
    metrics = await time_tracking.end_task(session_id, success=True)
except Exception as e:
    await time_tracking.end_task(session_id, success=False, error_message=str(e))
```

### Pattern 2: Track with Interruptions

```python
session_id = await time_tracking.start_task(...)

# Work starts
await work()

# Meeting interruption
await time_tracking.pause_task(session_id)

# Meeting ends
await time_tracking.resume_task(session_id)

# Continue work
await more_work()

# Complete
await time_tracking.end_task(session_id, success=True)
```

### Pattern 3: Weekly ROI Check

```python
import asyncio
from datetime import datetime

async def weekly_report():
    report = await time_tracking.generate_weekly_report()

    print(f"Week: {report.week_start} to {report.week_end}")
    print(f"Tasks: {report.roi_report.tasks_completed}")
    print(f"Time Saved: {report.roi_report.time_saved_hours:.1f}h")
    print(f"ROI: {report.roi_report.roi_percentage:.0f}%")
    print(f"\nTrends:")
    for key, value in report.trends.items():
        print(f"  {key}: {value}")
    print(f"\nRecommendations:")
    for rec in report.recommendations:
        print(f"  - {rec}")

# Run every Monday
asyncio.run(weekly_report())
```

### Pattern 4: Bottleneck Analysis

```python
async def analyze_bottlenecks():
    bottlenecks = await time_tracking.get_bottlenecks()

    critical = [b for b in bottlenecks if b.severity == "critical"]
    high = [b for b in bottlenecks if b.severity == "high"]

    if critical or high:
        print("🚨 Performance Issues Detected:")
        for b in critical + high:
            print(f"\n{b.severity.upper()}: {b.task_type.value}")
            print(f"  Average: {b.avg_duration_seconds}s")
            print(f"  Baseline: {b.baseline_seconds}s")
            print(f"  Overhead: {b.overhead_percentage:.0f}%")
            print(f"  Frequency: {b.frequency} times")
    else:
        print("✅ No critical bottlenecks")

asyncio.run(analyze_bottlenecks())
```

## Configuration Quick Edit

```bash
# Edit baselines
nano backend/config/baseline_times.yaml

# Update error_resolution baseline (30min → 35min)
baselines:
  error_resolution:
    manual_minutes: 35  # Was 30

# Restart server
# Changes apply immediately
```

## Troubleshooting

### Issue: "Session not found"

```python
# Check if session exists
if str(session_id) in time_tracking.active_sessions:
    await time_tracking.end_task(session_id, success=True)
else:
    logger.warning(f"Session {session_id} not active")
```

### Issue: "Negative time saved"

This is normal for bottlenecks (task took longer than baseline).

```python
# Identify and optimize slow tasks
bottlenecks = await time_tracking.get_bottlenecks()
for b in bottlenecks:
    print(f"Optimize: {b.task_type.value} ({b.overhead_percentage:.0f}% over)")
```

### Issue: "Database connection error"

Service runs in mock mode without database:

```python
# Still works, just doesn't persist
service = TimeTrackingService(pool=None, obsidian_service=None)
```

## Performance Tips

1. **Use pause/resume for interruptions** - Don't skew metrics
2. **Provide meaningful metadata** - Helps with analysis
3. **Track consistently** - Better data = better insights
4. **Review weekly reports** - Identify trends early
5. **Update baselines quarterly** - Reflect team improvements

## Key Metrics

### Time Saved

```python
time_saved_hours = (baseline_seconds - duration_seconds) / 3600
```

### Efficiency Percentage

```python
efficiency = (time_saved_seconds / baseline_seconds) * 100
```

### ROI Percentage

```python
roi = (time_saved_seconds / duration_seconds) * 100
```

### Bottleneck Severity

- **Low**: 10-25% over baseline
- **Medium**: 25-50% over baseline
- **High**: 50-100% over baseline
- **Critical**: >100% over baseline (2x+)

## API Endpoints Quick List

```
POST   /api/time-tracking/start
POST   /api/time-tracking/end/{session_id}
POST   /api/time-tracking/pause/{session_id}
POST   /api/time-tracking/resume/{session_id}
GET    /api/time-tracking/metrics/{task_id}
GET    /api/time-tracking/roi?period=weekly
GET    /api/time-tracking/bottlenecks
GET    /api/time-tracking/trends?days=30
GET    /api/time-tracking/report/weekly
GET    /api/time-tracking/health
```

Full docs: http://localhost:8000/docs

## Expected Results

### Good Performance
- Error resolution: 30min → 2min (93% efficiency, 1400% ROI)
- Design tasks: 2h → 30min (75% efficiency, 300% ROI)
- Implementation: 4h → 1h (75% efficiency, 300% ROI)

### Annual Target
- **485 hours saved** (12 weeks)
- **$48,500 value** (at $100/hour)
- **485% ROI** (first year)

## Files Reference

```
backend/app/services/time_tracking_service.py     # Core service
backend/app/models/time_tracking.py               # Data models
backend/app/routers/time_tracking.py              # API endpoints
backend/config/baseline_times.yaml                # Configuration
backend/migrations/002_time_tracking_schema.sql   # Database schema
backend/tests/test_time_tracking.py               # Tests

docs/TIME_TRACKING_GUIDE.md                       # Full guide
docs/TIME_TRACKING_IMPLEMENTATION.md              # Implementation details
docs/TIME_TRACKING_QUICK_REFERENCE.md             # This file
```

## Support

- **API Docs**: http://localhost:8000/docs
- **Tests**: `pytest backend/tests/test_time_tracking.py -v`
- **Logs**: `backend/logs/`
- **Database**: `psql udo_dev`

---

**Quick Reference Version**: 1.0.0
**Last Updated**: 2025-11-20
