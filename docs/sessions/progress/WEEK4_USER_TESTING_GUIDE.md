# Week 4 User Testing Guide: Archive View + AI Summarization

**Date**: 2025-12-05
**Version**: 1.0.0
**Target**: Week 3 Day 4-5 Implementation Validation
**Focus**: Q6 Done-End Archive Quality

---

## 🎯 Testing Objectives

### Primary Goals
1. **Validate AI Summarization Quality** (Q6: Done-End Archive)
   - Are AI-generated summaries accurate and helpful?
   - Do key learnings capture actual insights?
   - Are technical recommendations actionable?

2. **Verify ROI Metrics Accuracy**
   - Is efficiency calculation correct? (estimated / actual * 100)
   - Does time saved metric make sense?
   - Are quality scores aligned with actual task quality?

3. **Test Obsidian Knowledge Sync**
   - Do archived tasks sync to Obsidian correctly?
   - Is markdown note format readable and useful?
   - Are tags and links properly structured?

### Success Criteria
- **Baseline Confidence**: 72% (current from Q6 uncertainty)
- **Target Confidence**: 85% (after 5 user testing sessions)
- **Improvement Required**: +13% confidence increase

---

## 👥 Testing Participants (5 Sessions)

### Required Roles
1. **Developer** (2 sessions) - Heavy Kanban users
2. **Engineering Manager** (1 session) - ROI metrics validation
3. **Technical Lead** (1 session) - AI summary quality assessment
4. **Product Manager** (1 session) - Overall UX and value proposition

### Session Duration
- **Setup**: 10 minutes
- **Testing**: 30 minutes
- **Feedback**: 20 minutes
- **Total**: 60 minutes per session

---

## 🧪 Test Scenarios

### Scenario 1: Archive a Completed Implementation Task

**Objective**: Test full archive workflow with AI summarization

**Steps**:
1. Navigate to Kanban board (when frontend ready)
2. Create a completed task:
   ```
   Title: "Implement JWT authentication"
   Phase: Implementation
   Status: Completed
   Estimated: 16 hours
   Actual: 14.5 hours
   Quality Score: 95
   Constitutional Compliant: Yes
   ```
3. Click "Archive Task" button
4. Review AI-generated summary
5. Verify ROI metrics display
6. Check Obsidian sync status

**Expected Results**:
- AI summary includes key learnings about JWT implementation
- Technical insights mention security best practices
- Recommendations for future auth tasks
- Efficiency: 110.3% (16 / 14.5 * 100)
- Time saved: 1.5 hours
- Quality score: 95
- Obsidian note created with proper tags (#implementation, #authentication)

**Validation Questions**:
- [ ] Is the AI summary accurate?
- [ ] Are key learnings helpful?
- [ ] Are technical insights actionable?
- [ ] Do ROI metrics make sense?
- [ ] Is the Obsidian note useful?

---

### Scenario 2: Filter Archive by Phase

**Objective**: Test archive list filtering

**Steps**:
1. Archive 5+ tasks across different phases (Ideation, Design, Implementation, Testing)
2. Use phase filter to view only Implementation tasks
3. Review filtered results
4. Clear filter and view all archives

**Expected Results**:
- Filter returns only Implementation phase tasks
- Pagination works correctly (if >20 tasks)
- ROI statistics update based on filter
- Performance: <300ms for filtered query

**Validation Questions**:
- [ ] Does filtering work as expected?
- [ ] Is the UI responsive?
- [ ] Are ROI statistics accurate for filtered data?
- [ ] Can you easily clear filters?

---

### Scenario 3: Compare AI Summaries Across Phases

**Objective**: Validate phase-specific AI insights

**Steps**:
1. Archive one task from each phase:
   - Ideation: "Explore authentication approaches"
   - Design: "Design JWT authentication system"
   - MVP: "Basic JWT login/logout"
   - Implementation: "Full JWT with refresh tokens"
   - Testing: "Security testing for JWT"
2. Compare AI summaries across phases
3. Verify phase-specific insights

**Expected Results**:
- **Ideation**: Exploratory insights, multiple approaches considered
- **Design**: Architecture decisions, system design rationale
- **MVP**: Quick wins, minimal viable functionality
- **Implementation**: Code patterns, best practices, refactoring
- **Testing**: Test strategies, edge cases, quality assurance

**Validation Questions**:
- [ ] Do AI summaries differ meaningfully by phase?
- [ ] Are Ideation summaries exploratory?
- [ ] Are Implementation summaries technical?
- [ ] Are Testing summaries quality-focused?
- [ ] Is the model_used field correct (gpt-4o or mock)?

---

### Scenario 4: ROI Metrics Edge Cases

**Objective**: Test ROI calculation for over-estimated and under-estimated tasks

**Test Cases**:

#### Case A: Over-Estimated Task (Positive Efficiency)
```
Estimated: 10 hours
Actual: 8 hours
Expected Efficiency: 125% (10 / 8 * 100)
Expected Time Saved: +2 hours
```

#### Case B: Under-Estimated Task (Negative Efficiency)
```
Estimated: 10 hours
Actual: 15 hours
Expected Efficiency: 66.7% (10 / 15 * 100)
Expected Time Saved: -5 hours
```

#### Case C: Perfectly Estimated Task
```
Estimated: 10 hours
Actual: 10 hours
Expected Efficiency: 100%
Expected Time Saved: 0 hours
```

**Validation Questions**:
- [ ] Does efficiency calculation match expected?
- [ ] Is time saved correctly signed (+ or -)?
- [ ] Are negative values displayed clearly?
- [ ] Do ROI statistics aggregate correctly?

---

### Scenario 5: Obsidian Knowledge Extraction

**Objective**: Validate Obsidian sync and markdown note quality

**Steps**:
1. Archive a task with AI summarization enabled
2. Check Obsidian vault for new note
3. Review markdown note structure
4. Verify tags and links
5. Check if note is searchable in Obsidian

**Expected Markdown Structure**:
```markdown
# Task: Implement JWT Authentication

## Metadata
- **Phase**: Implementation
- **Archived**: 2025-12-05 12:30:00
- **Archived By**: test_developer
- **Quality Score**: 95/100

## AI Summary
[AI-generated summary text]

## Key Learnings
- Learning 1
- Learning 2
- Learning 3

## Technical Insights
- Insight 1
- Insight 2

## Recommendations
- Recommendation 1
- Recommendation 2

## ROI Metrics
- **Estimated**: 16.0h
- **Actual**: 14.5h
- **Time Saved**: 1.5h
- **Efficiency**: 110.3%
- **Quality**: 95/100

## Tags
#implementation #authentication #jwt #archived

## Related Tasks
- [[Task-UUID-1]]
- [[Task-UUID-2]]
```

**Validation Questions**:
- [ ] Is the markdown note well-formatted?
- [ ] Are all sections present?
- [ ] Do tags help with organization?
- [ ] Can you find the note via Obsidian search?
- [ ] Are related task links useful?

---

## 📊 Feedback Collection

### Quantitative Metrics

**AI Summary Quality** (1-5 scale):
- [ ] Accuracy: ___ / 5
- [ ] Completeness: ___ / 5
- [ ] Usefulness: ___ / 5
- [ ] Actionability: ___ / 5
- **Average**: ___ / 5

**ROI Metrics Accuracy** (1-5 scale):
- [ ] Efficiency calculation: ___ / 5
- [ ] Time saved metric: ___ / 5
- [ ] Quality score alignment: ___ / 5
- [ ] Overall ROI value: ___ / 5
- **Average**: ___ / 5

**Obsidian Integration** (1-5 scale):
- [ ] Sync reliability: ___ / 5
- [ ] Markdown format: ___ / 5
- [ ] Tag usefulness: ___ / 5
- [ ] Search findability: ___ / 5
- **Average**: ___ / 5

### Qualitative Feedback

**Open-Ended Questions**:

1. **AI Summarization**:
   - What did you like most about the AI summaries?
   - What could be improved?
   - Were the key learnings accurate?
   - Were the recommendations actionable?

2. **ROI Metrics**:
   - Do the efficiency percentages make sense?
   - Is the time saved metric useful?
   - Would you use ROI data for team planning?
   - What additional metrics would you want?

3. **Obsidian Integration**:
   - How useful are the Obsidian notes?
   - Would you reference these notes in the future?
   - Are tags helpful for organization?
   - What would you change about the format?

4. **Overall Experience**:
   - Would you use the archive feature regularly?
   - What's the most valuable aspect?
   - What's missing or confusing?
   - Rate overall experience (1-5): ___

---

## 📈 Success Metrics Tracking

### Confidence Increase Goal

**Baseline** (Before Testing):
- Q6 Confidence: 72%
- Uncertainty Areas: AI summary quality, ROI accuracy

**Target** (After 5 Sessions):
- Q6 Confidence: 85% (+13%)
- Validated: AI summary quality, ROI metrics, Obsidian sync

### Per-Session Tracking

| Session | Role | AI Quality (1-5) | ROI Accuracy (1-5) | Obsidian (1-5) | Overall (1-5) | Notes |
|---------|------|------------------|--------------------|--------------------|---------------|-------|
| 1 | Developer | | | | | |
| 2 | Developer | | | | | |
| 3 | Manager | | | | | |
| 4 | Tech Lead | | | | | |
| 5 | PM | | | | | |
| **Avg** | | | | | | |

**Formula for Confidence Increase**:
```
New Confidence = Baseline + (Target - Baseline) * (Avg Score / 5)
Example: 72% + (85% - 72%) * (4.2 / 5) = 72% + 10.9% = 82.9%
```

---

## 🐛 Bug Tracking Template

### Critical Bugs (P0 - Blocker)
- **Description**: [What's broken?]
- **Steps to Reproduce**: [How to trigger?]
- **Expected**: [What should happen?]
- **Actual**: [What happens instead?]
- **Impact**: [Why is this critical?]

### Major Bugs (P1 - High Priority)
- **Description**:
- **Impact**:
- **Workaround**:

### Minor Issues (P2 - Low Priority)
- **Description**:
- **Suggestion**:

---

## 🔧 Testing Environment Setup

### Prerequisites

**Backend**:
```bash
# Ensure backend is running
cd backend
.venv/Scripts/activate  # Windows
uvicorn main:app --reload --port 8000

# Verify archive endpoints
curl http://localhost:8000/api/kanban/archive
```

**Database**:
```bash
# Ensure mock service is enabled (until Week 4 database migration)
# Check backend/main.py lines 38-44
```

**Obsidian** (Optional):
```bash
# If testing Obsidian sync:
# 1. Ensure Obsidian vault is configured
# 2. Check OBSIDIAN_VAULT_PATH in .env
# 3. Verify obsidian_service.vault_available == True
```

**Frontend** (When Ready):
```bash
cd web-dashboard
npm run dev  # Port 3000
# Navigate to http://localhost:3000/kanban (when implemented)
```

---

## 📝 Post-Testing Actions

### After Each Session
1. **Document Feedback**: Fill out quantitative + qualitative sections
2. **Log Bugs**: Use bug tracking template for any issues
3. **Update Confidence**: Calculate new confidence score
4. **Share Insights**: Brief team on findings

### After All 5 Sessions
1. **Aggregate Results**: Calculate average scores across all sessions
2. **Final Confidence**: Determine if 85% target achieved
3. **Prioritize Fixes**: Rank bugs by severity and impact
4. **Update Documentation**: Reflect learnings in implementation docs
5. **Plan Week 4 Day 3-4**: Documentation + rollback validation

---

## 🎯 Next Steps Based on Results

### If Confidence ≥ 85% (Success)
✅ **Proceed to Week 4 Day 3**:
- Update documentation with testing insights
- Validate rollback procedures
- Prepare for production deployment (Day 4)

### If Confidence 78-84% (Partial Success)
⚠️ **Address Top 3 Issues**:
- Fix critical bugs (P0)
- Improve AI summary prompts (if quality < 4/5)
- Enhance ROI metrics display (if accuracy < 4/5)
- Re-test with 2 additional sessions

### If Confidence < 78% (Need Improvement)
❌ **Major Iteration Required**:
- Analyze root causes (AI model, metrics formula, UX)
- Redesign problematic areas
- Run full testing cycle again (5+ sessions)
- Consider delaying production deployment

---

## 📚 Reference Documents

**Implementation**:
- `backend/app/models/kanban_archive.py` - Archive models
- `backend/app/services/kanban_archive_service.py` - Archive service
- `backend/app/routers/kanban_archive.py` - Archive API
- `backend/tests/test_kanban_archive.py` - Test suite (15/15 passing)

**Design**:
- `docs/KANBAN_IMPLEMENTATION_SUMMARY.md` - Overall roadmap
- `docs/KANBAN_INTEGRATION_STRATEGY.md` - Q6 decision rationale

**Testing**:
- `docs/WEEK4_USER_TESTING_GUIDE.md` - This document

---

**Testing Status**: READY TO START
**Last Updated**: 2025-12-05
**Owner**: Engineering Team
**Approval Required**: Engineering Manager, Product Manager

---

**END OF USER TESTING GUIDE**
