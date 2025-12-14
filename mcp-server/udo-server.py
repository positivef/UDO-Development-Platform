#!/usr/bin/env python3
"""
UDO MCP Server
Exposes UDO's Uncertainty Map capabilities as MCP tools.
"""

import sys
import os
import json
import asyncio
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)

# Import UDO components
try:
    from src.uncertainty_map_v3 import UncertaintyMapV3, UncertaintyVector
except ImportError:
    # Fallback for when running in isolation
    sys.path.append(os.path.join(project_root, "src"))
    from uncertainty_map_v3 import UncertaintyMapV3, UncertaintyVector

# Initialize MCP Server
mcp = FastMCP("UDO-MCP-Server")

# Initialize Uncertainty Map
# In a real scenario, this might connect to a shared state or DB
# For now, we initialize a fresh instance or load from file
udo_map = UncertaintyMapV3("UDO-Platform")

@mcp.tool()
def get_uncertainty_state(phase: str = "implementation") -> str:
    """
    Get the current uncertainty state and vector for a given phase.
    Returns a formatted string with state, confidence, and vector details.
    """
    # Create a dummy context for current state analysis
    # In production, this would fetch real context from the project
    context = {
        "phase": phase,
        "files": ["dummy.py"], # Simulate having code
        "team_size": 3,
        "timeline_weeks": 8,
        "market_validation": 0.6
    }
    
    vector, state = udo_map.analyze_context(context)
    return udo_map.visualize_map(vector, state)

@mcp.tool()
def predict_risk_impact(change_description: str, phase: str = "implementation") -> str:
    """
    Predict the impact of a proposed change on project uncertainty.
    
    Args:
        change_description: Description of the proposed change (e.g., "Refactor auth system")
        phase: Current development phase
    """
    # 1. Analyze current state
    context = {
        "phase": phase,
        "files": ["dummy.py"],
        "team_size": 3,
        "timeline_weeks": 8
    }
    current_vector, _ = udo_map.analyze_context(context)
    
    # 2. Simulate impact (Heuristic based on keywords)
    # In a real system, this would use an LLM or more complex logic
    impact_vector = type(current_vector)(
        technical=current_vector.technical,
        market=current_vector.market,
        resource=current_vector.resource,
        timeline=current_vector.timeline,
        quality=current_vector.quality
    )
    
    desc_lower = change_description.lower()
    
    if "refactor" in desc_lower:
        impact_vector.technical += 0.2
        impact_vector.quality -= 0.1 # Short term risk
    if "test" in desc_lower:
        impact_vector.quality -= 0.3
        impact_vector.technical -= 0.1
    if "feature" in desc_lower:
        impact_vector.technical += 0.1
        impact_vector.timeline += 0.1
        
    # Clamp values
    impact_vector.technical = min(1.0, max(0.0, impact_vector.technical))
    impact_vector.quality = min(1.0, max(0.0, impact_vector.quality))
    impact_vector.timeline = min(1.0, max(0.0, impact_vector.timeline))
    
    # 3. Compare
    new_magnitude = impact_vector.magnitude()
    new_state = udo_map.classify_state(new_magnitude)
    
    return f"""
### Risk Impact Prediction
**Change**: "{change_description}"

**Current State**: {current_vector.magnitude():.2f}
**Predicted State**: {new_magnitude:.2f} ({new_state.value})

**Impact Analysis**:
- Technical: {current_vector.technical:.2f} -> {impact_vector.technical:.2f}
- Quality: {current_vector.quality:.2f} -> {impact_vector.quality:.2f}
- Timeline: {current_vector.timeline:.2f} -> {impact_vector.timeline:.2f}

**Recommendation**:
{_get_recommendation(new_state.value)}
"""

def _get_recommendation(state: str) -> str:
    if state == "deterministic":
        return "✅ Safe to proceed. Low risk."
    elif state == "probabilistic":
        return "⚠️ Proceed with standard review."
    elif state == "quantum":
        return "🛑 High risk (Quantum). Suggest breaking down the task."
    elif state == "chaotic":
        return "⛔ CRITICAL RISK. Do not proceed without architectural review."
    else:
        return "Unknown state."

@mcp.tool()
def log_work_session(task_id: str, duration_minutes: int, success: bool = True) -> str:
    """
    Log a completed work session to the Time Tracking Service.
    """
    # In a real implementation, this would call the TimeTrackingService
    # For now, we'll just log to stdout/file or return a confirmation
    return f"Logged {duration_minutes} minutes for task '{task_id}'. Success: {success}"

if __name__ == "__main__":
    mcp.run()
