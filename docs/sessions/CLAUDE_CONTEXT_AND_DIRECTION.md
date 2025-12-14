# Claude Code Context & Strategic Direction

**Date**: 2025-11-22
**Project**: UDO Development Platform v3.0
**Current Status**: Production Ready (Beta) - *Uncertainty Map Integration Pending*

---

## 1. Project Analysis & Current Status

### 📊 The "Missing Link" Discovery
The project has a powerful backend engine and a beautiful frontend dashboard, but they are **disconnected**.
- **Backend**: `UncertaintyMapV3` (Python) calculates 5-dimensional uncertainty and Quantum States.
- **Frontend**: `UncertaintyMap` (React) component exists but is unused.
- **Gap**: No API endpoint connects them. The dashboard is "flying blind" regarding uncertainty.

### 🎯 Immediate Goal
**Connect the Engine to the Dashboard.**
We need to visualize the "Quantum Uncertainty State" to the user immediately to differentiate this platform from standard project management tools.

---

## 2. Benchmarking & Differentiation Strategy

We analyzed 3 major competitors to identify our unique value proposition.

| Feature | 🔵 Linear Insights | 🟢 Atlassian Intelligence | 🟣 Pluralsight Flow | 🚀 **UDO v3 (Our Edge)** |
|:---|:---|:---|:---|:---|
| **Core Metric** | Velocity & Cycle Time | Historical Risk Trends | DORA Metrics & Health | **Quantum Uncertainty States** |
| **Prediction** | Burn-up Charts (Linear) | Project Hurdles (ML) | Delivery Forecasting | **24h Uncertainty Evolution** |
| **Risk Model** | Standard Delays | Issue-based Risks | Process Bottlenecks | **5-Dimensional Vector** (Tech, Market, etc.) |
| **Mitigation** | Manual | Manual Planning | Manual Coaching | **Auto-Generated Strategies with ROI** |
| **Context** | Cycle-based | Issue-based | Repo-based | **Phase-Aware** (Ideation → Testing) |

### 🏆 How We Win (Differentiation Points)
1.  **Quantum States vs. Red Flags**: Instead of just saying "Risk is High" (Red Flag), we classify state as "Quantum" (Superposition) or "Chaotic" (Sensitive to conditions). This is a more sophisticated, physics-inspired model that appeals to high-level engineering management.
2.  **Prescriptive vs. Descriptive**: Competitors show *what* is wrong. UDO suggests *what to do* (Auto-Mitigation) and *how much it helps* (ROI).
3.  **Phase-Awareness**: We treat "Ideation" uncertainty differently from "Testing" uncertainty. A 50% uncertainty is fine in Ideation but fatal in Testing. Competitors often apply one-size-fits-all metrics.

---

## 3. Action Plan for Claude Code

You (Claude Code) are tasked with the **"Uncertainty Map Integration"**.

### Phase 1: Integration (The "Bridge")
- [ ] **Backend**: Create `GET /api/uncertainty/status` in `backend/app/routers/uncertainty.py`.
    - Must return: `UncertaintyVector`, `QuantumState`, `ConfidenceScore`.
- [ ] **Frontend**: Update `web-dashboard/app/time-tracking/page.tsx`.
    - Import and place `<UncertaintyMap />` component.
    - Fetch data from the new API.

### Phase 2: Automation (The "Trigger")
- [ ] **Backend**: Modify `backend/app/services/time_tracking_service.py`.
    - When `actual_time > baseline * 1.2` (Bottleneck), call `UncertaintyMap.update(vector)`.
    - Increase `technical_uncertainty` automatically.

### Phase 3: Action (The "Solution")
- [ ] **Frontend**: Add "Mitigation Panel" to Dashboard.
    - Display strategies from `UncertaintyMap.generate_mitigations()`.
    - Add "Adopt" button to log the action.

---

## 4. Technical Context

### Key Files
- **Engine**: `src/uncertainty_map_v3.py` (The logic is here)
- **UI Component**: `web-dashboard/components/dashboard/uncertainty-map.tsx` (The visual is here)
- **Dashboard Page**: `web-dashboard/app/time-tracking/page.tsx` (The integration point)

### Data Structure (JSON)
```json
{
  "state": "Quantum",
  "confidence": 0.65,
  "vector": {
    "technical": 0.7,
    "market": 0.2,
    "resource": 0.4,
    "timeline": 0.6,
    "quality": 0.3
  },
  "prediction": {
    "trend": "decreasing",
    "next_24h": "Probabilistic"
  }
}
```

Use this context to guide your development. Focus on **visualizing the invisible** (uncertainty) to the user.
