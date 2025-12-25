# Week 8 Day 4: User Testing Guide

**Date**: 2025-12-23
**Purpose**: 5-user testing sessions for Kanban integration validation
**Duration**: 30-45 minutes per session
**Success Criteria**: ≥4.0/5.0 satisfaction, 0 critical bugs

---

## 📋 Testing Overview

### Objectives
1. **Usability Validation**: Kanban board intuitive workflows
2. **Feature Quality**: AI suggestions, context upload, dependency management
3. **Bug Discovery**: Identify critical issues before production
4. **UX Insights**: Collect improvement suggestions

### Participants (Target: 5 users)
- **Profile 1**: Junior developer (1-2 years experience)
- **Profile 2**: Senior developer (5+ years experience)
- **Profile 3**: Project manager (non-technical)
- **Profile 4**: DevOps engineer (technical operations)
- **Profile 5**: Product owner (business focus)

---

## 🎯 Test Scenarios

### Scenario 1: Kanban Board Basics (10 minutes)

**Objective**: Validate core task management workflows

**Tasks**:
1. **Create New Task**
   - Navigate to `/kanban` page
   - Click "Create Task" button
   - Fill in:
     - Title: "User Testing - Database Migration"
     - Description: "Migrate users table to PostgreSQL 16"
     - Phase: Implementation
     - Priority: High
     - Estimated hours: 8
   - Click "Save"

2. **Edit Task**
   - Click on newly created task
   - Update description: Add "with zero downtime"
   - Add tags: "database", "migration", "critical"
   - Save changes

3. **Drag & Drop**
   - Drag task from "To Do" to "In Progress"
   - Observe optimistic UI update
   - Wait for API confirmation (backend sync)

4. **Delete Task**
   - Open task detail
   - Click "Delete" button
   - Confirm deletion
   - Verify task removed from board

**Expected Results**:
- All CRUD operations work smoothly
- Drag & drop feels responsive (<100ms delay)
- No errors in browser console
- Task persists after page refresh

**Evaluation Questions**:
1. Was the task creation flow intuitive? (1-5)
2. Did drag & drop feel responsive? (1-5)
3. Any confusion or unexpected behavior?

---

### Scenario 2: Dependency Management (8 minutes)

**Objective**: Test task dependency features (Q7: Hard Block)

**Tasks**:
1. **Create Parent Task**
   - Title: "Design API Schema"
   - Phase: Design
   - Priority: High

2. **Create Child Task with Dependency**
   - Title: "Implement API Endpoints"
   - Phase: Implementation
   - Priority: Medium
   - Open "Dependencies" section
   - Add dependency: Select "Design API Schema"
   - Dependency type: "Hard Block"

3. **Test Blocking Behavior**
   - Try to move "Implement API Endpoints" to "In Progress"
   - Observe: Should show warning or prevent move
   - Move "Design API Schema" to "Done"
   - Now move child task to "In Progress" - should work

4. **Emergency Override** (if needed)
   - Test override button if hard block activated
   - Check if override reason dialog appears
   - Submit override with reason

**Expected Results**:
- Hard block prevents child task progression
- Override flow works but requires justification
- Dependency chain visualized clearly

**Evaluation Questions**:
1. Was dependency setup clear? (1-5)
2. Did blocking behavior make sense? (1-5)
3. Override flow too easy or too hard? (qualitative)

---

### Scenario 3: Context Upload (7 minutes)

**Objective**: Validate ZIP upload and file preview (Q4: Double-click auto-load)

**Tasks**:
1. **Prepare Test ZIP**
   - Create folder: `test-context/`
   - Add 3 files:
     - `api.py` (sample code)
     - `schema.sql` (sample DDL)
     - `README.md` (documentation)
   - Zip folder → `test-context.zip`

2. **Upload Context**
   - Open any task detail
   - Switch to "Context" tab
   - Drag & drop `test-context.zip` OR click upload
   - Observe:
     - Upload progress bar
     - File count validation (should show 3 files)
     - Size validation (under 50MB)

3. **Download Context**
   - Click "Download ZIP" button
   - Measure download time (expect <2s for small files)
   - Verify downloaded ZIP contains all 3 files

4. **Double-click Auto-load** (Future feature)
   - Double-click task card
   - Check if context auto-loads in modal
   - Verify load time tracking

**Expected Results**:
- Upload completes without errors
- Progress bar shows accurate percentage
- Download ZIP matches uploaded content
- File preview works (if implemented)

**Evaluation Questions**:
1. Upload process smooth? (1-5)
2. Progress feedback clear? (1-5)
3. Download speed acceptable? (1-5)

---

### Scenario 4: AI Task Suggestions (10 minutes)

**Objective**: Test AI suggestion quality and approval flow (Q2: AI Hybrid)

**Tasks**:
1. **Trigger AI Suggestion**
   - Create task: "Refactor authentication module"
   - Phase: Implementation
   - Click "AI Suggestions" button in task detail

2. **Review Suggestions**
   - Observe AI-generated subtasks (powered by Claude Sonnet 4.5)
   - Expected suggestions:
     - "Extract JWT logic to separate service"
     - "Add unit tests for token validation"
     - "Update API documentation"
   - Check confidence scores (should be 70-95%)

3. **Approve/Reject Suggestions**
   - Approve 2 suggestions (click checkmark)
   - Reject 1 suggestion (click X)
   - Edit 1 suggestion (modify text)
   - Click "Apply Selected"

4. **Verify Task Update**
   - Check if approved suggestions added as subtasks
   - Verify rejected suggestions not added
   - Confirm edited suggestion has updated text

**Expected Results**:
- AI generates 3-5 relevant suggestions in <3s
- Confidence scores visible and make sense
- Approval flow smooth (bulk select + apply)
- Suggestions match task context

**Evaluation Questions**:
1. AI suggestion quality relevant? (1-5)
2. Approval/reject flow clear? (1-5)
3. Response time acceptable? (1-5)
4. Would you use this feature regularly? (Yes/No)

---

### Scenario 5: Archive & ROI Dashboard (5 minutes)

**Objective**: Test archive workflow and ROI calculations (Q6: Done-End archiving)

**Tasks**:
1. **Archive Completed Task**
   - Create task: "Week 1 Sprint Planning"
   - Move to "Done"
   - Wait 5 seconds (simulate end-of-phase)
   - Click "Archive" button
   - Add archive note: "Sprint successful, all goals met"
   - Confirm archival

2. **View Archive**
   - Navigate to `/archive` page
   - Find archived task
   - Click to view details
   - Check AI summary generated (GPT-4o)

3. **ROI Dashboard**
   - Navigate to `/roi-dashboard`
   - Observe metrics:
     - Total tasks completed
     - Time saved (automation vs manual)
     - Confidence improvement trend
   - Check charts render (Recharts visualization)

**Expected Results**:
- Archive process smooth
- AI summary accurate (80%+ relevance)
- ROI metrics display correctly
- Charts load without errors

**Evaluation Questions**:
1. Archive flow intuitive? (1-5)
2. AI summary quality good? (1-5)
3. ROI metrics useful? (1-5)

---

## 📊 Data Collection

### During Session
- **Screen Recording**: Record full session (with consent)
- **Think-Aloud Protocol**: Encourage users to verbalize thoughts
- **Note Taking**: Document:
  - Points of confusion
  - Positive reactions ("That's nice!")
  - Error messages encountered
  - Unexpected behaviors

### Post-Session Survey (5 minutes)
See `WEEK8_DAY4_FEEDBACK_TEMPLATE.md` for full questionnaire.

**Key Questions**:
1. Overall satisfaction (1-5)
2. Feature usefulness ratings (1-5 per feature)
3. Performance perception (Fast/Average/Slow)
4. Top 3 improvements needed
5. Would you use in production? (Yes/No/Maybe)

---

## 🐛 Bug Reporting

### Severity Levels
- **P0 (Critical)**: Data loss, security issues, complete feature breakdown
- **P1 (High)**: Major functionality broken, poor UX, performance issues
- **P2 (Medium)**: Minor bugs, cosmetic issues, rare edge cases
- **P3 (Low)**: Typos, documentation gaps, nice-to-have improvements

### Bug Template
```markdown
**Severity**: P0 / P1 / P2 / P3
**Feature**: Kanban / Dependencies / Context / AI / Archive
**Steps to Reproduce**:
1. ...
2. ...
**Expected**: ...
**Actual**: ...
**Screenshot**: [if applicable]
**Browser**: Chrome/Firefox/Safari + version
```

---

## ✅ Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Overall Satisfaction | ≥4.0/5.0 | Average of Q1-Q10 in survey |
| Feature Usability | ≥3.5/5.0 per feature | Individual feature ratings |
| Critical Bugs | 0 | P0 bugs discovered |
| High Bugs | ≤3 | P1 bugs discovered |
| Task Completion Rate | ≥80% | Users completing all 5 scenarios |
| NPS Score | ≥7/10 | "Recommend to colleague?" |

---

## 📅 Testing Schedule

**Suggested Timeline**:
- **Day 1**: Sessions 1-2 (morning/afternoon)
- **Day 2**: Sessions 3-4 (morning/afternoon)
- **Day 3**: Session 5 + data analysis

**Session Format**:
1. Introduction (5 min): Explain purpose, consent for recording
2. Scenarios 1-5 (30 min): Guided tasks with think-aloud
3. Survey (5 min): Post-session questionnaire
4. Debrief (5 min): Open discussion, additional feedback

---

## 🔄 Next Steps After Testing

1. **Aggregate Results** (1 hour):
   - Calculate average satisfaction scores
   - Categorize bugs by severity
   - Identify common pain points

2. **Prioritize Fixes** (30 min):
   - P0 bugs → immediate fix (Week 8 Day 5)
   - P1 bugs → Week 9 backlog
   - P2/P3 bugs → future iterations

3. **Update Documentation** (1 hour):
   - Add learnings to `docs/USER_FEEDBACK_SUMMARY.md`
   - Update Week 8 plan with results
   - Create tickets in GitHub Issues

---

**Document Version**: 1.0
**Last Updated**: 2025-12-23
**Related Docs**:
- `WEEK8_DAY4_TESTING_CHECKLIST.md` - Quick reference
- `WEEK8_DAY4_FEEDBACK_TEMPLATE.md` - Survey template
- `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` - Feature reference
