# Week 4 Testing Checklist: Quick Reference

**Date**: 2025-12-05
**Version**: 1.0.0
**Purpose**: Quick checklist for user testing sessions

---

## Pre-Testing Setup ✓

### Backend Verification
- [ ] Backend running on http://localhost:8000
- [ ] Archive endpoints accessible (GET /api/kanban/archive)
- [ ] Mock service enabled (check backend/main.py:38-44)
- [ ] Test data seeded (at least 5 completed tasks)

### Frontend Verification (When Ready)
- [ ] Frontend running on http://localhost:3000
- [ ] Kanban board accessible
- [ ] Archive view page exists
- [ ] Task card actions work

### Obsidian Verification (Optional)
- [ ] Obsidian vault configured
- [ ] OBSIDIAN_VAULT_PATH in .env set
- [ ] obsidian_service.vault_available == True
- [ ] Test note creation works

---

## Scenario 1: Archive Completed Task ✓

### Setup
- [ ] Create completed Implementation task (16h estimated, 14.5h actual)
- [ ] Set quality_score = 95
- [ ] Set constitutional_compliant = True

### Actions
- [ ] Click "Archive Task" button
- [ ] Wait for AI summary generation (<10ms in mock mode)
- [ ] Review AI summary displayed

### Validation
- [ ] AI summary length ≥ 50 characters
- [ ] Key learnings list not empty
- [ ] Technical insights list not empty
- [ ] Recommendations list not empty
- [ ] Model used = "mock" (or "gpt-4o" if API key set)
- [ ] Efficiency = 110.3% (16/14.5*100)
- [ ] Time saved = 1.5 hours
- [ ] Quality score = 95
- [ ] Obsidian sync status shown

### User Feedback
- [ ] AI summary quality (1-5): ___
- [ ] ROI metrics clarity (1-5): ___
- [ ] Overall experience (1-5): ___

---

## Scenario 2: Filter Archive by Phase ✓

### Setup
- [ ] Archive ≥5 tasks across different phases
- [ ] Ensure at least 2 tasks per phase (Ideation, Design, Implementation)

### Actions
- [ ] Navigate to archive list page
- [ ] Apply phase filter (e.g., "Implementation")
- [ ] Verify filtered results
- [ ] Clear filter
- [ ] Verify all tasks shown again

### Validation
- [ ] Filter returns only selected phase tasks
- [ ] Task count updates correctly
- [ ] Pagination works (if >20 tasks)
- [ ] ROI statistics recalculate for filtered data
- [ ] Response time <300ms

### User Feedback
- [ ] Filter UI clarity (1-5): ___
- [ ] Response speed (1-5): ___
- [ ] Overall usability (1-5): ___

---

## Scenario 3: Phase-Specific AI Summaries ✓

### Setup
- [ ] Archive 1 task per phase:
  - [ ] Ideation: "Explore authentication approaches"
  - [ ] Design: "Design JWT authentication system"
  - [ ] MVP: "Basic JWT login/logout"
  - [ ] Implementation: "Full JWT with refresh tokens"
  - [ ] Testing: "Security testing for JWT"

### Actions
- [ ] Review AI summary for each phase
- [ ] Compare summaries side-by-side
- [ ] Note differences in tone and content

### Validation
- [ ] Ideation summary is exploratory
- [ ] Design summary mentions architecture
- [ ] MVP summary focuses on quick wins
- [ ] Implementation summary is technical
- [ ] Testing summary emphasizes quality

### User Feedback
- [ ] Phase differentiation (1-5): ___
- [ ] Summary relevance (1-5): ___
- [ ] Overall quality (1-5): ___

---

## Scenario 4: ROI Metrics Edge Cases ✓

### Test Case A: Over-Estimated (Efficiency > 100%)
- [ ] Create task: Estimated 10h, Actual 8h
- [ ] Archive task
- [ ] Verify: Efficiency = 125%
- [ ] Verify: Time saved = +2h
- [ ] Check: Positive time saved displayed in green

### Test Case B: Under-Estimated (Efficiency < 100%)
- [ ] Create task: Estimated 10h, Actual 15h
- [ ] Archive task
- [ ] Verify: Efficiency = 66.7%
- [ ] Verify: Time saved = -5h
- [ ] Check: Negative time saved displayed in red

### Test Case C: Perfect Estimation (Efficiency = 100%)
- [ ] Create task: Estimated 10h, Actual 10h
- [ ] Archive task
- [ ] Verify: Efficiency = 100%
- [ ] Verify: Time saved = 0h
- [ ] Check: Zero time saved displayed neutrally

### Validation
- [ ] All calculations correct
- [ ] Sign (+/-) displayed clearly
- [ ] Color coding helps understanding
- [ ] Aggregated ROI statistics accurate

### User Feedback
- [ ] ROI calculation clarity (1-5): ___
- [ ] Usefulness for planning (1-5): ___
- [ ] Overall value (1-5): ___

---

## Scenario 5: Obsidian Knowledge Extraction ✓

### Setup
- [ ] Ensure Obsidian vault accessible
- [ ] Archive task with AI summary enabled
- [ ] Wait for sync completion

### Actions
- [ ] Open Obsidian vault
- [ ] Navigate to daily notes directory
- [ ] Find archived task note (YYYY-MM-DD_task_{UUID}.md)
- [ ] Review markdown structure
- [ ] Search for note using Obsidian search

### Validation
- [ ] Note file exists in Obsidian vault
- [ ] YAML frontmatter correct
- [ ] All sections present (Summary, Learnings, Insights, ROI)
- [ ] Tags formatted as #tag
- [ ] Related tasks as [[Task-UUID]]
- [ ] ROI metrics readable
- [ ] Note searchable in Obsidian

### User Feedback
- [ ] Markdown format quality (1-5): ___
- [ ] Tag usefulness (1-5): ___
- [ ] Search findability (1-5): ___
- [ ] Future reference value (1-5): ___

---

## Post-Testing Summary ✓

### Quantitative Metrics

**AI Summary Quality**:
- Accuracy: ___ / 5
- Completeness: ___ / 5
- Usefulness: ___ / 5
- Actionability: ___ / 5
- **Average: ___ / 5**

**ROI Metrics Accuracy**:
- Efficiency calculation: ___ / 5
- Time saved metric: ___ / 5
- Quality score alignment: ___ / 5
- Overall ROI value: ___ / 5
- **Average: ___ / 5**

**Obsidian Integration**:
- Sync reliability: ___ / 5
- Markdown format: ___ / 5
- Tag usefulness: ___ / 5
- Search findability: ___ / 5
- **Average: ___ / 5**

**Overall Experience**: ___ / 5

### Confidence Calculation

**Formula**:
```
New Confidence = 72% + (85% - 72%) * (Overall Score / 5)
```

**Example**:
- If Overall Score = 4.2/5
- New Confidence = 72% + (13% * 0.84) = 72% + 10.9% = **82.9%**

**Your Score**:
- Overall Score: ___ / 5
- New Confidence: ___ %
- Target: 85%
- Status: [ ] Achieved  [ ] Not Yet

---

## Bug Tracking ✓

### Critical (P0) - Blockers
1. **Bug**: _______________
   - **Impact**: _______________
   - **Severity**: CRITICAL

2. **Bug**: _______________
   - **Impact**: _______________
   - **Severity**: CRITICAL

### Major (P1) - High Priority
1. **Issue**: _______________
   - **Impact**: _______________
   - **Workaround**: _______________

2. **Issue**: _______________
   - **Impact**: _______________
   - **Workaround**: _______________

### Minor (P2) - Low Priority
1. **Suggestion**: _______________
2. **Suggestion**: _______________

---

## Qualitative Feedback ✓

### What Worked Well?
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### What Needs Improvement?
1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Missing Features or Confusion
1. _______________________________________________
2. _______________________________________________

### Would You Use This Feature Regularly?
- [ ] Yes, definitely
- [ ] Probably
- [ ] Unsure
- [ ] Probably not
- [ ] No, not useful

**Why?** _______________________________________________

---

## Session Information ✓

**Tester Details**:
- Name: _______________
- Role: [ ] Developer  [ ] Manager  [ ] Tech Lead  [ ] PM
- Experience Level: [ ] Junior  [ ] Mid  [ ] Senior
- Kanban Usage: [ ] Heavy  [ ] Moderate  [ ] Light

**Session Metadata**:
- Date: _______________
- Duration: ___ minutes
- Environment: [ ] Local Dev  [ ] Staging  [ ] Other
- Notes: _______________________________________________

---

## Next Actions ✓

### Immediate (Today)
- [ ] Document session results
- [ ] Log all bugs in tracker
- [ ] Calculate confidence score
- [ ] Brief team on findings

### Short-term (This Week)
- [ ] Aggregate results from all sessions
- [ ] Prioritize bug fixes
- [ ] Update implementation docs
- [ ] Plan Week 4 Day 3-4 work

### Decision Point
- [ ] If Confidence ≥ 85%: Proceed to documentation + deployment
- [ ] If Confidence 78-84%: Fix top 3 issues, re-test
- [ ] If Confidence < 78%: Major iteration required

---

**Checklist Status**: READY
**Last Updated**: 2025-12-05
**Version**: 1.0.0

---

**END OF TESTING CHECKLIST**
