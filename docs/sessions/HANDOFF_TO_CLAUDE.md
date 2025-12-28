# Technical Handoff Guide for Claude Code
**To**: Claude Code (Agent)
**From**: Antigravity (Architect Agent)
**Date**: 2025-12-07

## 🚀 Mission: Execute V6 MVP

You are taking over the execution phase. The strategy is set. The "Simplification" has been applied.
Your goal is to get the **Uncertainty Graph visible on the Frontend**.

### 🔧 Key Technical Decision: The "Facade" Pattern

To fix `tests/test_uncertainty_predict.py` without rewriting the complex `UncertaintyMapV3` engine or the test suite, I have implemented a **Facade Class** in `src/uncertainty_map_v3.py`.

```python
class Uncertainty:
    """
    Facade for UncertaintyMapV3 to match simple test API.
    Used for MVP testing and backward compatibility.
    """
    def __init__(self):
        self.engine = UncertaintyMapV3("default_project")
        ...

    def predict(self, hours_ahead: int):
        # Wraps self.engine.predict_evolution(...)
        ...
```

**Why this matters to you:**
1.  **Do NOT delete this class.** The tests depend on it.
2.  **Do NOT change the test to use `UncertaintyMapV3` directly** unless you are willing to refactor the entire test data structure. The Facade is the bridge.
3.  **Production Router (`backend/app/routers/uncertainty.py`)** uses `UncertaintyMapV3` directly. This is fine. The logic is shared via the Facade calling the Engine.

### 📂 Critical Files
*   **Source**: `src/uncertainty_map_v3.py` (Contains Engine + Facade)
*   **Test**: `tests/test_uncertainty_predict.py` (Target to pass)
*   **Plan**: `docs/COMPREHENSIVE_ROADMAP_V6.md` (The Master Plan)
*   **Risk**: `docs/PREMORTEM_ANALYSIS_2025-12-06.md` (Read to understand why we simplified)

### ⚡ Execution Checklist (P0)

1.  **Run the Test**:
    ```bash
    .venv\Scripts\python.exe -m pytest tests/test_uncertainty_predict.py
    ```
    *Expectation*: It should pass now (or require minor tweaking of the Facade return structure).

2.  **Frontend Integration**:
    *   Check `web-dashboard/app/uncertainty/page.tsx`.
    *   Ensure it fetches from `/api/uncertainty/status`.
    *   Check the Types: `UncertaintyStatusResponse` in backend vs Typescript interfaces.

3.  **Verify**:
    *   Start Backend: `python -m uvicorn backend.main:app --reload`
    *   Start Frontend: `npm run dev` in `web-dashboard`
    *   **Visit http://localhost:3000/uncertainty**

**Good Luck.**
