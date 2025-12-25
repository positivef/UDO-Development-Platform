# Week 8 Day 4: User Testing Checklist

**Quick Reference for Test Sessions**
**Duration**: 30-45 minutes per user
**Target**: 5 users, ≥4.0/5.0 satisfaction

---

## ✅ Pre-Session Setup

### Technical Preparation
- [ ] Backend server running (http://localhost:8000)
- [ ] Frontend server running (http://localhost:3000)
- [ ] Database populated with sample tasks
- [ ] Test ZIP file prepared (`test-context.zip` with 3 files)
- [ ] Screen recording software ready
- [ ] Browser dev tools open (Console tab for error monitoring)

### User Preparation
- [ ] Consent form signed (screen recording permission)
- [ ] User profile confirmed (junior dev / senior dev / PM / DevOps / PO)
- [ ] Participant comfortable, quiet environment
- [ ] Think-aloud protocol explained
- [ ] Estimated duration communicated (30-45 min)

---

## 📋 Scenario Checklist

### Scenario 1: Kanban Basics (10 min)
- [ ] Create task: "User Testing - Database Migration"
  - Title, description, phase, priority, estimated hours
- [ ] Edit task: Update description, add 3 tags
- [ ] Drag & drop: To Do → In Progress
- [ ] Delete task: Confirm deletion

**Check**:
- [ ] No console errors
- [ ] Optimistic UI update works
- [ ] Task persists after refresh

---

### Scenario 2: Dependencies (8 min)
- [ ] Create parent: "Design API Schema"
- [ ] Create child: "Implement API Endpoints" with Hard Block dependency
- [ ] Test blocking: Child blocked when parent incomplete
- [ ] Move parent to Done: Child now movable
- [ ] (Optional) Test emergency override

**Check**:
- [ ] Hard block prevents child progress
- [ ] Dependency visualized clearly
- [ ] Override requires reason (if triggered)

---

### Scenario 3: Context Upload (7 min)
- [ ] Upload `test-context.zip` (3 files)
- [ ] Verify progress bar shows
- [ ] Download ZIP
- [ ] Verify downloaded content matches upload

**Check**:
- [ ] Upload <5s for small files
- [ ] File count validation works (3 files shown)
- [ ] Download <2s

---

### Scenario 4: AI Suggestions (10 min)
- [ ] Create task: "Refactor authentication module"
- [ ] Click "AI Suggestions" button
- [ ] Review 3-5 AI-generated subtasks
- [ ] Approve 2, reject 1, edit 1
- [ ] Click "Apply Selected"
- [ ] Verify subtasks updated

**Check**:
- [ ] AI response <3s
- [ ] Suggestions relevant (70-95% confidence)
- [ ] Approval flow smooth

---

### Scenario 5: Archive & ROI (5 min)
- [ ] Create task: "Week 1 Sprint Planning"
- [ ] Move to Done → Archive
- [ ] Add archive note
- [ ] Navigate to `/archive`, find task
- [ ] Navigate to `/roi-dashboard`, view metrics

**Check**:
- [ ] AI summary generated (GPT-4o)
- [ ] Archive searchable
- [ ] ROI charts render

---

## 📝 Data Collection

### During Session
- [ ] Screen recording started
- [ ] Note: Points of confusion
- [ ] Note: Positive reactions
- [ ] Note: Error messages
- [ ] Note: Unexpected behaviors

### Observations
- [ ] Task completion time per scenario
- [ ] Mouse movements (hesitation = confusion?)
- [ ] Facial expressions (frustration? delight?)
- [ ] Verbalized thoughts logged

---

## 📊 Post-Session Survey (5 min)

**Overall Satisfaction** (1-5):
- [ ] Q1: Overall experience
- [ ] Q2: Would recommend to colleague?

**Feature Usability** (1-5 each):
- [ ] Q3: Kanban board (CRUD operations)
- [ ] Q4: Drag & drop responsiveness
- [ ] Q5: Dependency management clarity
- [ ] Q6: Context upload ease
- [ ] Q7: AI suggestion quality
- [ ] Q8: Archive workflow
- [ ] Q9: ROI dashboard usefulness

**Performance Perception**:
- [ ] Q10: Page load speed (Fast / Average / Slow)
- [ ] Q11: API response time (Fast / Average / Slow)

**Open-Ended**:
- [ ] Q12: Top 3 improvements needed
- [ ] Q13: Most frustrating part
- [ ] Q14: Most delightful part
- [ ] Q15: Production-ready? (Yes / No / Maybe + why)

---

## 🐛 Bug Tracking

**P0 (Critical)** - Fix Immediately:
- [ ] Bug 1: _______________
- [ ] Bug 2: _______________

**P1 (High)** - Week 9:
- [ ] Bug 3: _______________
- [ ] Bug 4: _______________
- [ ] Bug 5: _______________

**P2/P3 (Medium/Low)** - Backlog:
- [ ] Issue 1: _______________
- [ ] Issue 2: _______________

---

## ✅ Session Completion

- [ ] Recording saved (filename: `user-test-{user-id}-{date}.mp4`)
- [ ] Survey responses collected
- [ ] Bugs logged in checklist
- [ ] Thank participant, explain next steps
- [ ] Debrief: Ask open-ended feedback
- [ ] Schedule next session (if applicable)

---

## 📈 Success Criteria Tracking

| Metric | Target | User 1 | User 2 | User 3 | User 4 | User 5 | Avg |
|--------|--------|--------|--------|--------|--------|--------|-----|
| Overall Satisfaction | ≥4.0 | ___ | ___ | ___ | ___ | ___ | ___ |
| Task Completion | ≥80% | ___ | ___ | ___ | ___ | ___ | ___ |
| P0 Bugs | 0 | ___ | ___ | ___ | ___ | ___ | ___ |
| NPS (0-10) | ≥7 | ___ | ___ | ___ | ___ | ___ | ___ |

---

**Quick Status**:
- Sessions Completed: ___/5
- Critical Bugs Found: ___
- High Priority Bugs: ___
- Average Satisfaction: ___/5.0

**Next Action**:
- [ ] Aggregate all 5 sessions
- [ ] Prioritize P0/P1 bugs
- [ ] Update Week 8 plan
- [ ] Create GitHub Issues for bugs
