# Testing Improvement Action Plan - UDO Development Platform

**Date**: 2025-12-14
**Goal**: Improve test coverage from 26% to 65% (prototype target)
**Timeline**: 6 weeks
**Status**: READY FOR EXECUTION

---

## Quick Start (Week 1 - P0 Fixes)

### Day 1-2: Fix Cache Manager (4 failures)
```python
# File: backend/app/core/cache_manager.py

# BEFORE: Platform-dependent sys.getsizeof()
def _calculate_size(self, value):
    return sys.getsizeof(value)  # ❌ Varies across platforms

# AFTER: Abstract size calculation
import pickle

def _calculate_size(self, value):
    """Platform-independent size calculation using pickle serialization"""
    try:
        return len(pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL))
    except (pickle.PicklingError, TypeError):
        # Fallback for unpicklable objects
        return sys.getsizeof(value)

# Test fix:
# File: backend/tests/test_cache_manager.py

def test_eviction_when_full():
    cache = CacheManager(max_size_bytes=1000)

    # Use predictable size calculation
    entry1 = "x" * 300  # Exactly 300 bytes after pickling
    entry2 = "y" * 300
    entry3 = "z" * 500  # Should evict entry1

    cache.set("key1", entry1)
    cache.set("key2", entry2)
    cache.set("key3", entry3)  # Triggers eviction

    assert cache.get("key1") is None  # Evicted (LRU)
    assert cache.get("key2") is not None
    assert cache.get("key3") is not None
```

**Run to verify**:
```bash
.venv\Scripts\python.exe -m pytest backend/tests/test_cache_manager.py -v
```

### Day 3-4: Fix Project Context Mock Service (11 failures)
```python
# File: backend/tests/conftest.py (CREATE NEW)

import pytest
from pathlib import Path
import sys

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture(autouse=True, scope="function")
def enable_project_context_mock():
    """
    Auto-enable mock service for ALL tests.
    Prevents database connection failures in test environment.
    """
    from backend.app.services.project_context_service import enable_mock_service
    enable_mock_service()
    yield
    # No cleanup needed - mock service is global state

@pytest.fixture(scope="session")
def test_config():
    """Global test configuration"""
    return {
        "performance_thresholds": {
            "dag_sort_ms": 50,
            "tier2_resolution_ms": 50,
            "stats_tracking_ms": 50
        },
        "mock_services": {
            "project_context": True,
            "obsidian": False,  # Use real for integration tests
            "context7": False
        }
    }
```

**Run to verify**:
```bash
.venv\Scripts\python.exe -m pytest backend/tests/test_project_context_api.py -v
```

### Day 5: Fix GI/CK API Schema (9 failures)
```python
# File: backend/app/models/ck_theory.py (UPDATE)

from pydantic import BaseModel
from datetime import datetime

# BEFORE: Nested response structure
class GICKResponse(BaseModel):
    result: dict  # ❌ Ambiguous

# AFTER: Flat, explicit structure
class GICKResponse(BaseModel):
    gi_value: float  # GI Formula result
    ck_value: float  # CK Theory result
    confidence: float  # Prediction confidence
    timestamp: datetime
    metadata: dict | None = None

# File: backend/app/routers/gi_ck_router.py (UPDATE)

@router.get("/calculate", response_model=GICKResponse)
async def calculate_gi_ck(
    project_id: str,
    phase_name: str
):
    result = await gi_ck_service.calculate(project_id, phase_name)

    # BEFORE: return {"result": result}
    # AFTER:
    return GICKResponse(
        gi_value=result["gi"],
        ck_value=result["ck"],
        confidence=result.get("confidence", 0.8),
        timestamp=datetime.now(),
        metadata=result.get("metadata")
    )
```

**Run to verify**:
```bash
.venv\Scripts\python.exe -m pytest backend/tests/test_gi_ck_integration.py -v
```

### Day 6-7: Fix Unified Error Resolver (4 failures)
```python
# File: scripts/unified_error_resolver.py (UPDATE)

# Fix 1: Tier 2 confidence calculation edge cases
def _calculate_confidence(self, error_msg, error_type, keywords):
    """Calculate confidence score with edge case handling"""
    base_confidence = 0.50

    # Whitelisted patterns (HIGH confidence)
    if error_type in ["ModuleNotFoundError", "ImportError"]:
        base_confidence = 0.95

    # Keyword matching (+0.05 per keyword, max +0.20)
    keyword_boost = min(len(keywords) * 0.05, 0.20)

    # Context validation (+0.10 if context is relevant)
    context_boost = 0.10 if self._validate_context() else 0.0

    # Edge case: Empty error message
    if not error_msg.strip():
        return 0.0

    # Edge case: Too long error message (likely stack trace, not pattern)
    if len(error_msg) > 1000:
        base_confidence *= 0.8  # Reduce confidence

    final_confidence = base_confidence + keyword_boost + context_boost
    return min(final_confidence, 1.0)  # Cap at 100%

# Fix 2: Context7 mock integration (for tests)
def _query_context7(self, error_msg, keywords):
    """Query Context7 with mock support for testing"""
    if self._test_mode:
        # Return mock response
        return {
            "solution": f"pip install {keywords[0]}" if keywords else None,
            "confidence": 0.85
        }

    # Real Context7 query
    # ... existing implementation

# Fix 3: Statistics tracking race conditions
import threading

def __init__(self):
    self._stats_lock = threading.Lock()
    # ... rest of init

def _update_statistics(self, tier, auto_applied=False):
    """Thread-safe statistics update"""
    with self._stats_lock:
        self.statistics["total"] += 1
        self.statistics[f"tier{tier}"] += 1
        if tier == 2 and auto_applied:
            self.statistics["tier2_auto"] += 1
```

**Run to verify**:
```bash
.venv\Scripts\python.exe -m pytest tests/test_unified_error_resolver.py -v
```

---

## Week 1 Verification
After completing all fixes, run full test suite:
```bash
.venv\Scripts\python.exe -m pytest tests/ backend/tests/ -v --cov=src --cov=backend/app --cov-report=term-missing
```

**Expected Results**:
- Pass Rate: 92.2% → 100% (32 failures fixed)
- Coverage: 26% → 30% (with fixes)
- Total Tests: 440 passing

---

## Week 2: Add Session Management Tests (45 new tests)

### File: backend/tests/test_session_manager_v2.py (CREATE NEW)
```python
"""
Comprehensive tests for SessionManagerV2

Coverage areas:
- Multi-session orchestration (15 tests)
- State persistence (10 tests)
- Checkpoint recovery (8 tests)
- Session lifecycle (12 tests)
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from backend.app.services.session_manager_v2 import SessionManagerV2

class TestMultiSessionOrchestration:
    """Test multi-session orchestration logic"""

    @pytest.mark.asyncio
    async def test_create_multiple_sessions(self):
        """Should create and track multiple concurrent sessions"""
        manager = SessionManagerV2()

        session1 = await manager.create_session(project_id="proj1")
        session2 = await manager.create_session(project_id="proj1")
        session3 = await manager.create_session(project_id="proj2")

        assert len(manager.active_sessions) == 3
        assert session1.session_id != session2.session_id

    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """Sessions should have isolated state"""
        manager = SessionManagerV2()

        session1 = await manager.create_session(project_id="proj1")
        session2 = await manager.create_session(project_id="proj1")

        # Update session1 state
        await manager.update_state(session1.session_id, {"key": "value1"})

        # Session2 should not see session1's state
        state2 = await manager.get_state(session2.session_id)
        assert state2.get("key") is None

    # ... 13 more tests

class TestStatePersistence:
    """Test session state persistence"""

    @pytest.mark.asyncio
    async def test_save_session_state(self):
        """Should persist session state to disk"""
        manager = SessionManagerV2()

        session = await manager.create_session(project_id="proj1")
        await manager.update_state(session.session_id, {"task_count": 5})

        # Save to disk
        saved = await manager.save_session(session.session_id)
        assert saved is True

        # Verify file exists
        state_file = manager.state_dir / f"{session.session_id}.json"
        assert state_file.exists()

    # ... 9 more tests

class TestCheckpointRecovery:
    """Test checkpoint recovery mechanisms"""

    @pytest.mark.asyncio
    async def test_recover_from_checkpoint(self):
        """Should restore session from checkpoint"""
        manager = SessionManagerV2()

        # Create session and checkpoint
        session = await manager.create_session(project_id="proj1")
        await manager.update_state(session.session_id, {"step": 3})
        await manager.create_checkpoint(session.session_id, "before_step_4")

        # Simulate crash
        manager.active_sessions.clear()

        # Recover
        recovered = await manager.recover_from_checkpoint(
            session.session_id,
            "before_step_4"
        )

        assert recovered.state["step"] == 3

    # ... 7 more tests

class TestSessionLifecycle:
    """Test session lifecycle management"""

    @pytest.mark.asyncio
    async def test_session_creation(self):
        """Should create session with default state"""
        manager = SessionManagerV2()

        session = await manager.create_session(project_id="proj1")

        assert session.session_id is not None
        assert session.project_id == "proj1"
        assert session.status == "active"
        assert session.created_at is not None

    @pytest.mark.asyncio
    async def test_session_termination(self):
        """Should clean up resources on termination"""
        manager = SessionManagerV2()

        session = await manager.create_session(project_id="proj1")
        await manager.update_state(session.session_id, {"data": "test"})

        # Terminate
        terminated = await manager.terminate_session(session.session_id)
        assert terminated is True

        # Verify cleanup
        assert session.session_id not in manager.active_sessions
        assert session.status == "terminated"

    # ... 10 more tests
```

**Run to verify**:
```bash
.venv\Scripts\python.exe -m pytest backend/tests/test_session_manager_v2.py -v --cov=backend/app/services/session_manager_v2.py --cov-report=term-missing
```

**Expected**: 45/45 tests passing, Session Management coverage: 25% → 65%

---

## Week 3: Add Frontend Component Tests (45 new tests)

### File: web-dashboard/components/__tests__/TaskCard.test.tsx (CREATE NEW)
```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { TaskCard } from '../kanban/TaskCard';
import { Task, TaskPriority, TaskStatus } from '@/lib/types/kanban';

describe('TaskCard Component', () => {
  const mockTask: Task = {
    task_id: '123',
    title: 'Test Task',
    description: 'Test description',
    priority: TaskPriority.HIGH,
    status: TaskStatus.PENDING,
    phase_id: '456',
    phase_name: 'ideation',
    tags: ['test', 'frontend'],
    estimated_hours: 8,
    actual_hours: 0,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  };

  it('should render task title', () => {
    render(<TaskCard task={mockTask} />);
    expect(screen.getByText('Test Task')).toBeInTheDocument();
  });

  it('should render priority badge with correct color', () => {
    render(<TaskCard task={mockTask} />);
    const badge = screen.getByText(/high/i);
    expect(badge).toHaveClass('bg-orange-500');  // HIGH priority color
  });

  it('should render tags', () => {
    render(<TaskCard task={mockTask} />);
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('frontend')).toBeInTheDocument();
  });

  it('should call onClick when clicked', () => {
    const handleClick = jest.fn();
    render(<TaskCard task={mockTask} onClick={handleClick} />);

    fireEvent.click(screen.getByText('Test Task'));
    expect(handleClick).toHaveBeenCalledWith(mockTask);
  });

  // ... 4 more tests (8 total)
});
```

### Run to verify:
```bash
cd web-dashboard
npm test -- TaskCard.test.tsx
```

**Expected**: 8/8 tests passing

---

## Week 4: Add Uncertainty Map Tests (32 new tests)

### File: tests/test_uncertainty_predict_extended.py (CREATE NEW)
```python
"""
Extended tests for Uncertainty Map v3 predictive modeling

Coverage areas:
- Quantum state classification (8 tests)
- Auto-mitigation ROI calculation (6 tests)
- 24-hour predictive window (10 tests)
- Edge cases (8 tests)
"""

import pytest
from src.uncertainty_map_v3 import UncertaintyMap, QuantumState

class TestQuantumStateClassification:
    """Test quantum state classification logic"""

    def test_deterministic_state_threshold(self):
        """Uncertainty <10% should classify as DETERMINISTIC"""
        uncertainty_map = UncertaintyMap()

        state = uncertainty_map.classify_state(uncertainty=0.05)
        assert state == QuantumState.DETERMINISTIC

    def test_probabilistic_state_range(self):
        """Uncertainty 10-30% should classify as PROBABILISTIC"""
        uncertainty_map = UncertaintyMap()

        state = uncertainty_map.classify_state(uncertainty=0.20)
        assert state == QuantumState.PROBABILISTIC

    def test_quantum_state_range(self):
        """Uncertainty 30-60% should classify as QUANTUM"""
        uncertainty_map = UncertaintyMap()

        state = uncertainty_map.classify_state(uncertainty=0.45)
        assert state == QuantumState.QUANTUM

    def test_chaotic_state_range(self):
        """Uncertainty 60-90% should classify as CHAOTIC"""
        uncertainty_map = UncertaintyMap()

        state = uncertainty_map.classify_state(uncertainty=0.75)
        assert state == QuantumState.CHAOTIC

    def test_void_state_threshold(self):
        """Uncertainty >90% should classify as VOID"""
        uncertainty_map = UncertaintyMap()

        state = uncertainty_map.classify_state(uncertainty=0.95)
        assert state == QuantumState.VOID

    # ... 3 more tests (8 total)

class TestAutoMitigationROI:
    """Test auto-mitigation ROI calculation"""

    def test_roi_calculation_positive(self):
        """ROI should be positive when mitigation cost < risk cost"""
        uncertainty_map = UncertaintyMap()

        roi = uncertainty_map.calculate_mitigation_roi(
            risk_cost=10000,
            mitigation_cost=2000,
            success_probability=0.8
        )

        # ROI = (risk_cost * success_prob - mitigation_cost) / mitigation_cost
        # ROI = (10000 * 0.8 - 2000) / 2000 = 3.0 (300%)
        assert roi == pytest.approx(3.0, abs=0.01)

    # ... 5 more tests (6 total)

class Test24HourPredictiveWindow:
    """Test 24-hour predictive window logic"""

    def test_predict_within_window(self):
        """Should predict uncertainty within 24-hour window"""
        import datetime
        uncertainty_map = UncertaintyMap()

        predictions = uncertainty_map.predict_window(
            current_uncertainty=0.30,
            window_hours=24,
            interval_hours=6
        )

        # Should have 4 predictions (0, 6, 12, 18 hours)
        assert len(predictions) == 4

    # ... 9 more tests (10 total)

class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_zero_uncertainty(self):
        """Zero uncertainty should classify as DETERMINISTIC"""
        uncertainty_map = UncertaintyMap()

        state = uncertainty_map.classify_state(uncertainty=0.0)
        assert state == QuantumState.DETERMINISTIC

    def test_exactly_100_percent_uncertainty(self):
        """100% uncertainty should classify as VOID"""
        uncertainty_map = UncertaintyMap()

        state = uncertainty_map.classify_state(uncertainty=1.0)
        assert state == QuantumState.VOID

    # ... 6 more tests (8 total)
```

**Run to verify**:
```bash
.venv\Scripts\python.exe -m pytest tests/test_uncertainty_predict_extended.py -v --cov=src/uncertainty_map_v3.py --cov-report=term-missing
```

**Expected**: 32/32 tests passing, Uncertainty Map coverage: 58% → 80%

---

## Week 5-6: Add E2E Workflow Tests (20 new tests)

### File: web-dashboard/tests/e2e/complete-task-lifecycle.spec.ts (CREATE NEW)
```typescript
import { test, expect } from '@playwright/test';

test.describe('Complete Task Lifecycle', () => {
  test('Create → Update → Complete → Archive workflow', async ({ page }) => {
    // 1. Navigate to Kanban board
    await page.goto('/kanban');
    await page.waitForLoadState('domcontentloaded');

    // 2. Create new task
    await page.click('button:has-text("Add Task")');
    await page.fill('input[name="title"]', 'E2E Test Task');
    await page.fill('textarea[name="description"]', 'Full lifecycle test');
    await page.selectOption('select[name="priority"]', 'high');
    await page.click('button:has-text("Create")');

    // 3. Verify task appears in "To Do" column
    const taskCard = page.locator('text=E2E Test Task');
    await expect(taskCard).toBeVisible();

    // 4. Drag to "In Progress"
    const inProgressColumn = page.locator('h2:has-text("In Progress")');
    await taskCard.dragTo(inProgressColumn);

    // Wait for backend update
    await page.waitForTimeout(500);

    // 5. Verify backend state via API
    const tasksResponse = await page.request.get('http://localhost:8000/api/kanban/tasks');
    const tasks = await tasksResponse.json();
    const createdTask = tasks.find((t: any) => t.title === 'E2E Test Task');

    expect(createdTask).toBeDefined();
    expect(createdTask.status).toBe('in_progress');

    // 6. Open task detail modal
    await taskCard.click();
    await page.waitForSelector('dialog[open]');

    // 7. Update task details
    await page.fill('input[name="actual_hours"]', '4');
    await page.fill('textarea[name="context_notes"]', 'Implemented feature X');
    await page.click('button:has-text("Save")');

    // 8. Mark complete
    await page.click('button:has-text("Complete")');
    await page.waitForSelector('h2:has-text("Done")');

    // 9. Verify task moved to "Done" column
    const doneColumn = page.locator('h2:has-text("Done")');
    const completedTask = doneColumn.locator('text=E2E Test Task');
    await expect(completedTask).toBeVisible();

    // 10. Verify time tracking update
    await page.goto('/time-tracking');
    const completedCount = page.locator('text=/Completed: \\d+/');
    await expect(completedCount).toBeVisible();

    // 11. Archive completed task
    await page.goto('/kanban');
    await completedTask.click();
    await page.click('button:has-text("Archive")');

    // Confirm archive
    await page.click('button:has-text("Yes, Archive")');

    // 12. Verify task removed from board
    await expect(completedTask).not.toBeVisible();

    // 13. Verify task in archive
    await page.goto('/kanban/archive');
    const archivedTask = page.locator('text=E2E Test Task');
    await expect(archivedTask).toBeVisible();

    console.log('✅ Complete task lifecycle verified');
  });

  // ... 19 more workflow tests
});
```

**Run to verify**:
```bash
cd web-dashboard
npx playwright test complete-task-lifecycle.spec.ts
```

**Expected**: 20/20 tests passing

---

## Progress Tracking

### Week 1 (P0 Fixes)
- [ ] Cache Manager fixes (4 tests)
- [ ] Project Context mock service (11 tests)
- [ ] GI/CK API schema (9 tests)
- [ ] Unified Error Resolver (4 tests)
- **Target**: 100% pass rate, 30% coverage

### Week 2 (Session Management)
- [ ] Multi-session orchestration (15 tests)
- [ ] State persistence (10 tests)
- [ ] Checkpoint recovery (8 tests)
- [ ] Session lifecycle (12 tests)
- **Target**: 40% coverage

### Week 3 (Frontend Components)
- [ ] TaskCard component (8 tests)
- [ ] KanbanBoard state (10 tests)
- [ ] useTimeTracking hook (12 tests)
- [ ] API client error handling (15 tests)
- **Target**: 50% coverage

### Week 4 (Uncertainty Map)
- [ ] Quantum state classification (8 tests)
- [ ] Auto-mitigation ROI (6 tests)
- [ ] 24-hour predictive window (10 tests)
- [ ] Edge cases (8 tests)
- **Target**: 55% coverage

### Week 5-6 (E2E & Integration)
- [ ] E2E workflow tests (20 tests)
- [ ] Cross-module integration (15 tests)
- [ ] Performance regression (10 tests)
- [ ] Security/RBAC (15 tests)
- **Target**: 65% coverage ✅

---

## Daily Checklist

**Every Day**:
1. Run affected tests: `pytest path/to/test_file.py -v`
2. Check coverage: `pytest --cov=module --cov-report=term-missing`
3. Fix failures immediately (don't accumulate)
4. Update this action plan with progress
5. Commit daily: `git commit -m "test: Add X tests for Y module"`

**Every Week**:
1. Run full test suite: `pytest tests/ backend/tests/ -v`
2. Generate coverage report: `pytest --cov=src --cov=backend/app --cov-report=html`
3. Review coverage gaps in HTML report
4. Update roadmap based on actual progress
5. Demo passing tests to team

---

## Commands Reference

### Run specific test file
```bash
.venv\Scripts\python.exe -m pytest backend/tests/test_cache_manager.py -v
```

### Run with coverage
```bash
.venv\Scripts\python.exe -m pytest tests/ --cov=src --cov-report=term-missing
```

### Run parallel tests
```bash
.venv\Scripts\python.exe -m pytest tests/ -n auto
```

### Run only failed tests
```bash
.venv\Scripts\python.exe -m pytest --lf
```

### Run with HTML report
```bash
.venv\Scripts\python.exe -m pytest tests/ --html=report.html --self-contained-html
```

### Frontend tests
```bash
cd web-dashboard
npm test
npm run test:e2e
```

---

## Success Metrics

**Week 1**: 32 failures fixed, 100% pass rate, 30% coverage
**Week 2**: +45 tests, 40% coverage
**Week 3**: +45 tests, 50% coverage
**Week 4**: +32 tests, 55% coverage
**Week 5-6**: +60 tests, 65% coverage ✅

**Final Target**: 717 tests, 65% coverage, 98%+ pass rate

---

**Action Plan Ready for Execution**
Start Date: 2025-12-14
End Date: 2026-01-25 (6 weeks)
