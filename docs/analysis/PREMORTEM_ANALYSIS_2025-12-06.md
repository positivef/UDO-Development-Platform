# Pre-mortem Analysis: UDO Platform v6.0
**Date**: 2025-12-07
**Session**: Hybrid Model Review (Claude/GPT/Gemini)

## 📌 Context
Instead of asking "What went wrong?" at the end, we ask **"Assume it failed. Why did it fail?"** at the start.
This analysis is based on the integration of three AI models' perspectives.

---

## 🛑 Scenario: The "Zombie Project" Failure
**The Nightmare**: Ideally defined processes exist, but the code is brittle, the developer is overwhelmed by tools, and the dashboard works but shows irrelevant data.

### Top 5 Failure Causes & Mitigations

#### 1. Over-Engineering (Role: Gemini/Claude risk)
*   **Cause**: Implementing complex scripts (`obsidian_tag_enforcer.py`) and "Training-free RL" theories before the basic MVP works.
*   **Symptom**: 3,000 lines of "support tools" but the main Dashboard graph is blank.
*   **Mitigation (Applied)**: **Simplification**. Deleted complex tagging scripts. Focus strictly on "Graph Visibility" as the only MVP metric.

#### 2. Test-Production Divergence (Technical)
*   **Cause**: The Test (`test_uncertainty_predict.py`) tests a wrapper class (`Uncertainty`), but the Production Router uses the complex internal logic (`UncertaintyMapV3`).
*   **Symptom**: Tests pass Green, but the API 500s in production because arguments differ.
*   **Mitigation**: **Facade & Integration Test**.
    *   We implemented a `Uncertainty` Facade in `src/uncertainty_map_v3.py` to bridge the test.
    *   **Crucial Next Step**: Claude Code MUST manually verify the `/api/uncertainty/status` endpoint works (using `tests/run_udo_phase1.py` or `monitor_logs`).

#### 3. Metric Paralysis (Role: GPT risk)
*   **Cause**: Tracking 12 different KPIs (Accuracy, Coverage, ROI, Token Efficiency...) for a solo developer.
*   **Symptom**: Developer spends more time updating Jira/Obsidian/KPIs than coding.
*   **Mitigation**: **One Metric That Matters (OMTM)**.
    *   For MVP, the ONLY metric is: **"Is the Uncertainty Graph Visible?"**

#### 4. The "Missing Link" (Frontend <-> Backend)
*   **Cause**: Backend is Python/FastAPI, Frontend is Next.js/Typescript. They are developed in silos.
*   **Symptom**: Swagger UI works, but Frontend shows "Fetch Error".
*   **Mitigation**: **Priority 0 Integration Task**.
    *   The very first task for Claude Code is hitting the API from the Frontend.

#### 5. Instruction Overload
*   **Cause**: Too many markdown files (`DEVELOPMENT_ROADMAP_V6`, `IMPLEMENTATION`, `ANALYSIS`...). Claude Code gets confused on which is the "Truth".
*   **Symptom**: Claude reverts to V5 plan or ignores V6 specificities.
*   **Mitigation**: **CLAUDE.md Hierarchy**.
    *   `CLAUDE.md` is the Single Source of Truth. It links to `COMPREHENSIVE_ROADMAP_V6.md`.
    *   All other docs are "Reference".

---

## 🚦 Go/No-Go Decision
*   **Current Status**: **GO (Conditional)**
*   **Condition**:
    1.  Test failures MUST be fixed (Facade implemented).
    2.  Frontend must render data within 24 hours.

## 📝 Action Items (Immediate)
1.  [x] Create Facade in `src/uncertainty_map_v3.py` (Done).
2.  [ ] Run `tests/test_uncertainty_predict.py` (Claude Code Task).
3.  [ ] Verify `/api/uncertainty/status` (Claude Code Task).
