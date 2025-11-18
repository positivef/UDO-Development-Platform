"""
Project Context Models

Pydantic models for project context auto-loading and state management.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID


# ============================================================
# UDO State Models
# ============================================================

class UDOState(BaseModel):
    """UDO System State for a project"""
    last_decision: Optional[str] = Field(None, description="Last UDO decision (GO/GO_WITH_CHECKPOINTS/NO_GO)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence level")
    quantum_state: Optional[str] = Field(None, description="Quantum state (Deterministic/Probabilistic/etc)")
    uncertainty_map: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Current uncertainty map")
    phase: Optional[str] = Field(None, description="Current development phase")

    class Config:
        json_schema_extra = {
            "example": {
                "last_decision": "GO",
                "confidence": 0.85,
                "quantum_state": "Deterministic",
                "uncertainty_map": {
                    "implementation": "low",
                    "testing": "medium"
                },
                "phase": "implementation"
            }
        }


class MLModelsState(BaseModel):
    """ML Models State for a project"""
    confidence_predictor: Optional[str] = Field(None, description="Path to confidence predictor model")
    task_classifier: Optional[str] = Field(None, description="Path to task classifier model")
    custom_models: Optional[Dict[str, str]] = Field(default_factory=dict, description="Custom model paths")

    class Config:
        json_schema_extra = {
            "example": {
                "confidence_predictor": "models/confidence_v1.pkl",
                "task_classifier": "models/classifier_v2.pkl",
                "custom_models": {
                    "bug_detector": "models/bug_detector_v1.pkl"
                }
            }
        }


class ExecutionRecord(BaseModel):
    """Single execution record"""
    timestamp: str = Field(..., description="Execution timestamp")
    task: str = Field(..., description="Task description")
    decision: str = Field(..., description="UDO decision")
    confidence: float = Field(..., ge=0.0, le=1.0)
    success: bool = Field(..., description="Execution success status")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-17T14:30:00",
                "task": "Implement authentication",
                "decision": "GO",
                "confidence": 0.92,
                "success": True
            }
        }


class AIPreferences(BaseModel):
    """AI Service Preferences"""
    preferred_model: Optional[str] = Field("claude-sonnet-4.5", description="Preferred AI model")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="AI temperature")
    max_tokens: Optional[int] = Field(2000, gt=0, description="Max tokens per request")
    custom_settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom AI settings")

    class Config:
        json_schema_extra = {
            "example": {
                "preferred_model": "claude-sonnet-4.5",
                "temperature": 0.7,
                "max_tokens": 2000,
                "custom_settings": {
                    "streaming": True,
                    "retry_count": 3
                }
            }
        }


class EditorState(BaseModel):
    """Editor State (open files, cursor positions, etc)"""
    open_files: Optional[List[str]] = Field(default_factory=list, description="List of open file paths")
    cursor_positions: Optional[Dict[str, Dict[str, int]]] = Field(
        default_factory=dict,
        description="Cursor positions per file"
    )
    breakpoints: Optional[List[str]] = Field(default_factory=list, description="Debugger breakpoints")
    terminal_history: Optional[List[str]] = Field(default_factory=list, description="Terminal command history")

    class Config:
        json_schema_extra = {
            "example": {
                "open_files": [
                    "backend/main.py",
                    "backend/app/routers/quality_metrics.py"
                ],
                "cursor_positions": {
                    "backend/main.py": {"line": 45, "column": 12}
                },
                "breakpoints": ["backend/main.py:45"],
                "terminal_history": ["pytest", "python main.py"]
            }
        }


# ============================================================
# Project Context Models
# ============================================================

class ProjectContextCreate(BaseModel):
    """Create new project context"""
    project_id: UUID = Field(..., description="Project UUID")
    udo_state: Optional[UDOState] = Field(default_factory=UDOState, description="UDO system state")
    ml_models: Optional[MLModelsState] = Field(default_factory=MLModelsState, description="ML models state")
    recent_executions: Optional[List[ExecutionRecord]] = Field(default_factory=list, description="Recent executions (max 10)")
    ai_preferences: Optional[AIPreferences] = Field(default_factory=AIPreferences, description="AI preferences")
    editor_state: Optional[EditorState] = Field(default_factory=EditorState, description="Editor state")


class ProjectContextUpdate(BaseModel):
    """Update existing project context (all fields optional)"""
    udo_state: Optional[UDOState] = None
    ml_models: Optional[MLModelsState] = None
    recent_executions: Optional[List[ExecutionRecord]] = None
    ai_preferences: Optional[AIPreferences] = None
    editor_state: Optional[EditorState] = None


class ProjectContextResponse(BaseModel):
    """Project context response"""
    id: UUID
    project_id: UUID
    udo_state: Dict[str, Any]
    ml_models: Dict[str, Any]
    recent_executions: List[Dict[str, Any]]
    ai_preferences: Dict[str, Any]
    editor_state: Dict[str, Any]
    saved_at: datetime
    loaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "project_id": "660e8400-e29b-41d4-a716-446655440000",
                "udo_state": {
                    "last_decision": "GO",
                    "confidence": 0.85,
                    "quantum_state": "Deterministic"
                },
                "ml_models": {
                    "confidence_predictor": "models/confidence_v1.pkl"
                },
                "recent_executions": [
                    {
                        "timestamp": "2025-11-17T14:30:00",
                        "task": "Implement auth",
                        "decision": "GO",
                        "confidence": 0.92,
                        "success": True
                    }
                ],
                "ai_preferences": {
                    "preferred_model": "claude-sonnet-4.5",
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                "editor_state": {
                    "open_files": ["backend/main.py"],
                    "cursor_positions": {}
                },
                "saved_at": "2025-11-17T14:30:00",
                "loaded_at": None
            }
        }


class ProjectSwitchRequest(BaseModel):
    """Request to switch to a different project"""
    project_id: UUID = Field(..., description="Target project UUID")
    auto_save_current: bool = Field(True, description="Auto-save current project context before switching")


class ProjectSwitchResponse(BaseModel):
    """Response after project switch"""
    previous_project_id: Optional[UUID] = None
    new_project_id: UUID
    context_loaded: bool
    context: Optional[ProjectContextResponse] = None
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "previous_project_id": "550e8400-e29b-41d4-a716-446655440000",
                "new_project_id": "660e8400-e29b-41d4-a716-446655440000",
                "context_loaded": True,
                "context": {
                    "udo_state": {"last_decision": "GO"},
                    "ai_preferences": {"preferred_model": "claude-sonnet-4.5"}
                },
                "message": "Successfully switched to project 'My Project'"
            }
        }


# ============================================================
# Project Models (simplified for context use)
# ============================================================

class ProjectListResponse(BaseModel):
    """Simplified project info for listing"""
    id: UUID
    name: str
    description: Optional[str] = None
    current_phase: str
    last_active_at: datetime
    is_archived: bool = False
    has_context: bool = False  # Whether project context exists

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "660e8400-e29b-41d4-a716-446655440000",
                "name": "UDO-Development-Platform",
                "description": "AI-powered development automation",
                "current_phase": "testing",
                "last_active_at": "2025-11-17T14:30:00",
                "is_archived": False,
                "has_context": True
            }
        }


class ProjectsListResponse(BaseModel):
    """List of projects with pagination"""
    projects: List[ProjectListResponse]
    total: int
    current_project_id: Optional[UUID] = None

    class Config:
        json_schema_extra = {
            "example": {
                "projects": [
                    {
                        "id": "660e8400-e29b-41d4-a716-446655440000",
                        "name": "UDO-Development-Platform",
                        "current_phase": "testing",
                        "has_context": True
                    }
                ],
                "total": 1,
                "current_project_id": "660e8400-e29b-41d4-a716-446655440000"
            }
        }
