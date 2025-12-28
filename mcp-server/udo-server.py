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


# ============================================
# Governance Tools (Layer 2)
# ============================================

@mcp.tool()
def validate_project_rules(project_path: str = ".") -> str:
    """
    Validate project governance rules using validate_system_rules.py.
    
    Args:
        project_path: Path to the project root (default: current directory)
    
    Returns:
        Validation results with pass/fail status and recommendations.
    """
    import subprocess
    from pathlib import Path
    
    # Resolve project path
    if project_path == ".":
        repo_path = Path(project_root)
    else:
        repo_path = Path(project_path).resolve()
    
    # Check if validate_system_rules.py exists
    validator_script = repo_path / "scripts" / "validate_system_rules.py"
    
    if not validator_script.exists():
        return f"""
### ❌ Validation Failed
**Reason**: validate_system_rules.py not found at {validator_script}

**Action Required**: 
Ensure the project has a scripts/validate_system_rules.py file.
"""
    
    # Run validation script
    try:
        result = subprocess.run(
            [sys.executable, str(validator_script)],
            capture_output=True,
            text=True,
            cwd=str(repo_path),
            timeout=30
        )
        
        # Parse output for summary
        output = result.stdout
        
        # Extract pass rate from output
        if "100.0%" in output:
            status = "✅ All rules passed"
        elif "CRITICAL" in output:
            status = "❌ Critical rules failed"
        else:
            status = "⚠️ Some rules failed"
        
        return f"""
### {status}

**Project**: {repo_path.name}
**Validator**: validate_system_rules.py

**Output**:
```
{output[-1500:] if len(output) > 1500 else output}
```

**Exit Code**: {result.returncode}
"""
    except subprocess.TimeoutExpired:
        return "❌ Validation timed out (>30 seconds)"
    except Exception as e:
        return f"❌ Validation error: {str(e)}"


@mcp.tool()
def get_governance_templates() -> str:
    """
    List available governance templates and their descriptions.
    
    Returns:
        List of templates with descriptions and recommended use cases.
    """
    from pathlib import Path
    
    templates_dir = Path(project_root) / "templates"
    
    if not templates_dir.exists():
        return """
### ❌ Templates Not Found

The templates/ directory does not exist.
Run Phase 1 of the governance setup first.
"""
    
    templates = {
        "minimal": {
            "description": "최소 규칙 - 개인 프로젝트/실험용",
            "features": ["Basic linting", "README required", "CLAUDE.md required"],
            "strict_mode": False,
            "ci_cd": False
        },
        "standard": {
            "description": "표준 규칙 - 팀 프로젝트용",
            "features": ["Full linting", "Type checking", "Testing required", "CI/CD"],
            "strict_mode": True,
            "ci_cd": True
        },
        "full": {
            "description": "전체 규칙 - 기업/대규모 프로젝트용",
            "features": ["All standard features", "Security audit", "Compliance", "Daily monitoring"],
            "strict_mode": True,
            "ci_cd": True
        }
    }
    
    result = "### 📋 Available Governance Templates\n\n"
    
    for name, info in templates.items():
        template_path = templates_dir / name / ".governance.yaml"
        exists = "✅" if template_path.exists() else "❌"
        
        result += f"""
#### {name.upper()} {exists}
**Description**: {info['description']}
**Strict Mode**: {"Yes" if info['strict_mode'] else "No"}
**CI/CD**: {"Yes" if info['ci_cd'] else "No"}
**Features**: {', '.join(info['features'])}

"""
    
    result += """
### Usage
To apply a template, use `apply_governance_template(project_path, template_name)`
"""
    
    return result


@mcp.tool()
def apply_governance_template(project_path: str, template_name: str = "standard") -> str:
    """
    Apply a governance template to a project.
    
    Args:
        project_path: Path to the target project
        template_name: Template to apply (minimal, standard, full)
    
    Returns:
        Status of template application with created files.
    """
    from pathlib import Path
    import shutil
    
    templates_dir = Path(project_root) / "templates"
    template_path = templates_dir / template_name
    target_path = Path(project_path).resolve()
    
    # Validate template exists
    if not template_path.exists():
        return f"""
### ❌ Template Not Found

Template '{template_name}' does not exist.
Available templates: minimal, standard, full
"""
    
    # Validate target path exists
    if not target_path.exists():
        return f"""
### ❌ Project Path Not Found

Path '{project_path}' does not exist.
"""
    
    applied_files = []
    
    # Copy .governance.yaml
    governance_src = template_path / ".governance.yaml"
    governance_dst = target_path / ".governance.yaml"
    
    if governance_src.exists():
        shutil.copy(governance_src, governance_dst)
        applied_files.append(".governance.yaml")
    
    # Copy other template files if they exist
    for file in template_path.glob("*"):
        if file.name != ".governance.yaml":
            dst = target_path / file.name
            if file.is_file():
                shutil.copy(file, dst)
            else:
                shutil.copytree(file, dst, dirs_exist_ok=True)
            applied_files.append(file.name)
    
    return f"""
### ✅ Template Applied Successfully

**Template**: {template_name}
**Target**: {target_path}
**Files Applied**: {len(applied_files)}

**Applied Files**:
{chr(10).join(f'  - {f}' for f in applied_files)}

**Next Steps**:
1. Review .governance.yaml and adjust settings
2. Run `validate_project_rules()` to verify
3. Install pre-commit hooks: `pre-commit install`
"""


if __name__ == "__main__":
    mcp.run()

