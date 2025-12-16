# Week 4 User Testing Guide

**Date**: 2025-12-16
**Status**: Active
**Goal**: Increase confidence from 72% to 85% through structured user testing

---

## Overview

This guide provides comprehensive testing scenarios for validating the Kanban-UDO integration before production deployment. The goal is to increase system confidence from 72% to 85% through 5 user testing sessions.

### Success Criteria

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Archive View Confidence | 72% | 85% | User testing |
| AI Summary Quality | 50% | 80% | GPT-4o output validation |
| Obsidian Sync | 70% | 90% | Integration testing |
| UX Satisfaction | TBD | ≥4/5 | User survey |

### Confidence Calculation Formula
```
New Confidence = 72% + (85% - 72%) × (Avg Score / 5)
```

---

## Test Scenarios (5 Sessions)

### Session 1: Developer Workflow

**Participants**: 1 Developer
**Duration**: 30 minutes
**Focus**: Task CRUD, Drag & Drop, API Integration

#### Test Cases

| # | Scenario | Steps | Expected Result | Pass/Fail |
|---|----------|-------|-----------------|-----------|
| 1.1 | Create Task | Click "Add Task" → Fill form → Submit | Task appears in "To Do" column | |
| 1.2 | Drag to In Progress | Drag task card → Drop in "In Progress" | Status updates, API call succeeds | |
| 1.3 | Edit Task Details | Click task → Modify title/description → Save | Changes persist after refresh | |
| 1.4 | Filter by Phase | Select "Implementation" filter | Only implementation tasks shown | |
| 1.5 | Delete Task | Click task → Delete → Confirm | Task removed from board | |

#### Quantitative Metrics
- [ ] Task creation: ____ seconds (target: <3s)
- [ ] Drag & drop response: ____ ms (target: <200ms)
- [ ] Filter response: ____ ms (target: <500ms)

#### Qualitative Feedback
```
1. Overall ease of use (1-5): ____
2. Visual clarity of columns (1-5): ____
3. Drag & drop intuitiveness (1-5): ____
4. Task card information density (1-5): ____
5. Suggestions for improvement:
   _______________________________________
```

---

### Session 2: AI Task Suggestion (Q2)

**Participants**: 1 Developer, 1 Tech Lead
**Duration**: 45 minutes
**Focus**: AI suggestion quality, Approval workflow, Constitutional compliance

#### Test Cases

| # | Scenario | Steps | Expected Result | Pass/Fail |
|---|----------|-------|-----------------|-----------|
| 2.1 | Generate Suggestions | Click "AI Suggest" → Select phase → Submit | 3 suggestions with confidence scores | |
| 2.2 | Approve Suggestion | Review suggestion → Click "Approve" | Task created in correct phase | |
| 2.3 | Reject Suggestion | Review suggestion → Click "Reject" | Suggestion dismissed, feedback captured | |
| 2.4 | Rate Limit Check | Generate 10+ suggestions | Rate limit message displayed | |
| 2.5 | Constitutional Check | Generate suggestion for sensitive task | P1-P17 validation applied | |

#### AI Quality Assessment

| Suggestion | Relevance (1-5) | Clarity (1-5) | Actionability (1-5) | Would Approve |
|------------|-----------------|---------------|---------------------|---------------|
| Suggestion 1 | | | | Yes / No |
| Suggestion 2 | | | | Yes / No |
| Suggestion 3 | | | | Yes / No |

#### Qualitative Feedback
```
1. AI suggestion relevance (1-5): ____
2. Confidence score accuracy (1-5): ____
3. Approval workflow clarity (1-5): ____
4. Rate of acceptable suggestions: ____/%
5. Missing context in suggestions:
   _______________________________________
```

---

### Session 3: Archive + AI Summarization (Q6)

**Participants**: 1 Manager, 1 PM
**Duration**: 45 minutes
**Focus**: Archive workflow, AI summary quality, ROI metrics, Obsidian sync

#### Test Cases

| # | Scenario | Steps | Expected Result | Pass/Fail |
|---|----------|-------|-----------------|-----------|
| 3.1 | Archive Completed Task | Mark complete → Click "Archive" | Task moved to archive | |
| 3.2 | View AI Summary | Open archived task | Summary with key learnings displayed | |
| 3.3 | Check ROI Metrics | Open archive → View statistics | Efficiency, time saved, quality scores | |
| 3.4 | Obsidian Sync | Archive task → Check Obsidian vault | Note created in correct folder | |
| 3.5 | Filter Archive | Filter by phase/archiver/date | Correct results displayed | |

#### AI Summary Quality Assessment

| Task | Summary Accuracy (1-5) | Key Insights (1-5) | Actionable Learning (1-5) |
|------|------------------------|--------------------|-----------------------|
| Task 1 | | | |
| Task 2 | | | |
| Task 3 | | | |

#### ROI Metrics Validation

| Metric | Displayed Value | Expected Range | Valid |
|--------|-----------------|----------------|-------|
| Efficiency Score | ____% | 60-100% | |
| Time Saved | ____ hours | Positive | |
| Quality Score | ____% | 0-100% | |

#### Qualitative Feedback
```
1. Summary usefulness (1-5): ____
2. ROI metrics clarity (1-5): ____
3. Archive searchability (1-5): ____
4. Obsidian integration (1-5): ____
5. Missing information in summaries:
   _______________________________________
```

---

### Session 4: Multi-Project & Dependencies (Q5, Q7)

**Participants**: 1 Tech Lead
**Duration**: 30 minutes
**Focus**: Primary project selection, Cross-project dependencies, Hard block behavior

#### Test Cases

| # | Scenario | Steps | Expected Result | Pass/Fail |
|---|----------|-------|-----------------|-----------|
| 4.1 | Select Primary Project | Click project selector → Choose primary | Primary badge displayed | |
| 4.2 | Add Related Project | Add up to 3 related projects | Max 3 limit enforced | |
| 4.3 | Create Dependency | Link task A → task B | Dependency arrow displayed | |
| 4.4 | Block Movement | Try moving blocked task | Hard block prevents movement | |
| 4.5 | Emergency Override | Use override → Move blocked task | Override logged, task moved | |

#### Dependency Management Assessment

| Feature | Works Correctly | UX Rating (1-5) | Comments |
|---------|-----------------|-----------------|----------|
| Dependency creation | Yes / No | | |
| Visual dependency display | Yes / No | | |
| Hard block behavior | Yes / No | | |
| Emergency override | Yes / No | | |

#### Qualitative Feedback
```
1. Multi-project clarity (1-5): ____
2. Dependency visibility (1-5): ____
3. Block message clarity (1-5): ____
4. Override friction level (1-5): ____  # Higher is better for safety
5. Edge cases encountered:
   _______________________________________
```

---

### Session 5: End-to-End Integration

**Participants**: 1 Developer, 1 PM
**Duration**: 60 minutes
**Focus**: Full workflow, Performance, Error handling

#### Test Cases

| # | Scenario | Steps | Expected Result | Pass/Fail |
|---|----------|-------|-----------------|-----------|
| 5.1 | Full Task Lifecycle | Create → Progress → Block → Resolve → Complete → Archive | All states transition correctly | |
| 5.2 | Network Error | Disconnect network → Perform action | Graceful error handling | |
| 5.3 | Concurrent Edit | Two users edit same task | Conflict resolution applied | |
| 5.4 | Bulk Operations | Select multiple tasks → Bulk status change | All tasks updated | |
| 5.5 | Performance Check | Load 50+ tasks → Scroll/filter | No lag, <3s load time | |

#### Performance Metrics

| Metric | Measured Value | Target | Pass/Fail |
|--------|----------------|--------|-----------|
| Initial load time | ____s | <3s | |
| Drag & drop latency | ____ms | <200ms | |
| Filter response | ____ms | <500ms | |
| API response p95 | ____ms | <500ms | |
| WebSocket latency | ____ms | <50ms | |

#### Error Handling Assessment

| Error Type | Behavior | User-Friendly | Recovery Clear |
|------------|----------|---------------|----------------|
| Network disconnect | | Yes / No | Yes / No |
| API timeout | | Yes / No | Yes / No |
| Validation error | | Yes / No | Yes / No |
| Permission denied | | Yes / No | Yes / No |

---

## Aggregated Results

### Session Summary

| Session | Avg Score | Critical Issues | Confidence Impact |
|---------|-----------|-----------------|-------------------|
| Session 1: Developer | /5 | | +___ % |
| Session 2: AI Suggest | /5 | | +___ % |
| Session 3: Archive | /5 | | +___ % |
| Session 4: Multi-Project | /5 | | +___ % |
| Session 5: E2E | /5 | | +___ % |
| **Total** | **/5** | | **+___ %** |

### Final Confidence Calculation

```
Initial Confidence: 72%
Session Contributions:
- Session 1: +___ %
- Session 2: +___ %
- Session 3: +___ %
- Session 4: +___ %
- Session 5: +___ %

Final Confidence: 72% + ___ = ___%
Target: 85%
Status: [ ] Achieved / [ ] Need Re-testing
```

---

## Issue Tracking

### Critical Issues (P0)
| # | Description | Session | Status |
|---|-------------|---------|--------|
| | | | |

### Major Issues (P1)
| # | Description | Session | Status |
|---|-------------|---------|--------|
| | | | |

### Minor Issues (P2)
| # | Description | Session | Status |
|---|-------------|---------|--------|
| | | | |

---

## Decision Tree

```
IF Final Confidence ≥ 85%:
    → Proceed to Production Deployment
    → Complete rollback validation

ELIF Final Confidence ≥ 75%:
    → Fix top 3 critical issues
    → Run 1-2 additional sessions
    → Re-calculate confidence

ELSE (< 75%):
    → Major rework required
    → Address all P0/P1 issues
    → Schedule full re-testing
```

---

## Next Steps After Testing

1. **If ≥85% confidence**:
   - [ ] Complete WEEK4_ROLLBACK_PROCEDURES.md
   - [ ] Create deployment checklist
   - [ ] Schedule production deployment

2. **If <85% confidence**:
   - [ ] Document all issues found
   - [ ] Prioritize fixes
   - [ ] Schedule re-testing sessions

---

## Appendix: Test Environment Setup

### Prerequisites
```bash
# Backend
.venv\Scripts\activate
.venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8000

# Frontend
cd web-dashboard
npm run dev  # http://localhost:3000

# Database
# Using in-memory mock service (no external DB required)
```

### Test Data Reset
```bash
# Reset mock data before each session
.venv\Scripts\python.exe -c "from backend.app.services.kanban_task_service import kanban_task_service; kanban_task_service.reset_mock_data()"
```

### Obsidian Vault Path
```
C:\Users\user\Documents\Obsidian Vault\개발일지\
```

---

*Document Version*: 1.0
*Last Updated*: 2025-12-16
*Author*: Claude Code
