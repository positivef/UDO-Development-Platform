# Obsidian Service - Quick Reference

**Version**: 2.0 (Event-Based with Debouncing)

## TL;DR

**Before**: Each event → immediate sync → many small notes → high token usage
**After**: Events → queue (3s window) → batch sync → fewer meaningful notes → 60% token savings

## Basic Usage

### Python Service API

```python
from app.services.obsidian_service import obsidian_service

# Recommended: Event-based with debouncing (NEW)
await obsidian_service.sync_event("phase_transition", {
    "from_phase": "design",
    "to_phase": "implementation"
})

# Legacy: Immediate sync (still works)
await obsidian_service.auto_sync("phase_transition", {...})

# Force flush all pending
events_flushed = await obsidian_service.force_flush()
```

### REST API

```bash
# Queue event (recommended)
curl -X POST http://localhost:8000/api/obsidian/event \
  -H "Content-Type: application/json" \
  -d '{"event_type": "phase_transition", "data": {...}}'

# Force flush
curl -X POST http://localhost:8000/api/obsidian/force-flush

# Get statistics (with batching metrics)
curl http://localhost:8000/api/obsidian/statistics

# Health check
curl http://localhost:8000/api/obsidian/health
```

## Event Types

- `phase_transition` - Phase changes
- `error_resolution` - Error solutions (for Tier 1 reuse)
- `task_completion` - Task milestones
- `architecture_decision` - ADR pattern
- `session_end` - Session summaries

## Key Configuration

```python
# Default debounce window: 3 seconds
service = ObsidianService(debounce_window=3)

# Custom window (1-10s recommended)
service = ObsidianService(debounce_window=5)
```

## Statistics

```python
stats = obsidian_service.get_sync_statistics()

# Operational metrics
print(f"Total syncs: {stats['total_syncs']}")
print(f"Success rate: {stats['success_rate']}%")

# Efficiency metrics (NEW)
print(f"Avg events/sync: {stats['avg_events_per_sync']}")
print(f"Batching rate: {stats['batching_rate']}%")
print(f"Tokens saved: {stats['tokens_saved_estimate']}")
print(f"Pending: {stats['pending_events']}")
```

## Performance Targets

- `sync_event()`: <10ms (queue operation)
- `force_flush()`: <500ms (write operation)
- Delayed flush: 3s (debounce window)
- Search (Tier 1): <10ms (existing)

## Common Patterns

### Pattern 1: Phase Transition

```python
async def on_phase_change(from_phase, to_phase):
    await obsidian_service.sync_event("phase_transition", {
        "from_phase": from_phase,
        "to_phase": to_phase,
        "context": {"trigger": "User action"},
        "changes": ["List of changes"],
        "decisions": ["Architecture decisions"]
    })
```

### Pattern 2: Task Completion

```python
async def on_task_complete(task):
    await obsidian_service.sync_event("task_completion", {
        "task_title": task.title,
        "duration": task.duration,
        "complexity": task.complexity,
        "tags": ["task", task.category]
    })
```

### Pattern 3: Error Resolution (Tier 1 Reuse)

```python
async def save_error_solution(error, solution):
    await obsidian_service.sync_event("error_resolution", {
        "error_type": extract_error_type(error),
        "context": {"error_message": error},
        "solution": solution,
        "tags": ["error-resolution", "debugging"]
    })
```

### Pattern 4: Session End (Force Flush)

```python
async def on_session_end(session_id):
    # Flush all pending events
    events_flushed = await obsidian_service.force_flush()
    logger.info(f"Session end: flushed {events_flushed} events")
```

## Troubleshooting

### Issue: Events not flushing

**Check**:
```python
# View pending events
stats = obsidian_service.get_sync_statistics()
print(f"Pending: {stats['pending_events']}")

# Force flush to debug
await obsidian_service.force_flush()
```

### Issue: Low batching rate

**Expected**: Batching only works when events occur within 3s window.
If events are spread out, batching rate will be low (this is correct behavior).

### Issue: Vault not found

**Fix**:
1. Check path: `C:\Users\user\Documents\Obsidian Vault`
2. Ensure `.obsidian` directory exists
3. Create `개발일지` directory
4. Check logs for auto-detection results

## Token Optimization Formula

```
Events in window: 5
Without debouncing: 5 syncs × 100 tokens = 500 tokens
With debouncing: 1 sync × 120 tokens = 120 tokens
Savings: 380 tokens (76%)
```

## File Locations

**Service**: `backend/app/services/obsidian_service.py`
**Router**: `backend/app/routers/obsidian.py`
**Models**: `backend/app/models/obsidian_sync.py`
**Tests**: `backend/tests/test_obsidian_*.py` (80 tests)
**Docs**: `docs/Obsidian_Debouncing_Implementation.md`

## Testing

```bash
# Run all ObsidianService tests
pytest backend/tests/test_obsidian_service.py -v
pytest backend/tests/test_obsidian_debouncing.py -v

# Run specific test class
pytest backend/tests/test_obsidian_debouncing.py::TestDebouncingBasics -v

# With coverage
pytest backend/tests/test_obsidian*.py --cov=app.services.obsidian_service
```

## Migration Checklist

- [ ] Review existing `auto_sync()` calls
- [ ] Identify high-frequency events (good candidates for batching)
- [ ] Replace with `sync_event()` for those events
- [ ] Add `force_flush()` to session end handlers
- [ ] Monitor batching_rate in production
- [ ] Celebrate 60% token savings 🎉

---

**Quick Start**: Just use `sync_event()` instead of `auto_sync()` and enjoy automatic batching!
