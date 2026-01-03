"""
C-K Theory Data Models

Pydantic models for Concept-Knowledge Design Theory (design alternative generation)
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Dict, Optional, Any
from datetime import datetime


class RICEScore(BaseModel):
    """RICE scoring framework (Reach × Impact × Confidence / Effort)"""

    reach: int = Field(..., ge=1, le=10, description="Number of users/scope affected (1-10)")
    impact: int = Field(..., ge=1, le=10, description="Impact level on users/system (1-10)")
    confidence: int = Field(..., ge=1, le=10, description="Confidence in estimates (1-10)")
    effort: int = Field(..., ge=1, le=10, description="Implementation effort required (1-10)")
    score: float = Field(..., ge=0.0, description="Calculated RICE score")

    @model_validator(mode="after")
    def calculate_rice_score(self) -> "RICEScore":
        """Auto-calculate RICE score"""
        self.score = round((self.reach * self.impact * self.confidence) / max(self.effort, 1), 2)
        return self

    class Config:
        json_schema_extra = {"example": {"reach": 8, "impact": 7, "confidence": 6, "effort": 5, "score": 6.72}}


class DesignAlternative(BaseModel):
    """Single design alternative from C-K Theory exploration"""

    id: str = Field(..., description="Alternative ID (A, B, or C)")
    title: str = Field(..., min_length=5, max_length=100, description="Alternative title")
    description: str = Field(..., min_length=20, max_length=2000, description="Detailed description")

    # Concept Space
    concept_origin: str = Field(..., description="Origin in concept space")
    knowledge_basis: List[str] = Field(..., min_items=1, description="Knowledge elements used")

    # RICE Analysis
    rice: RICEScore = Field(..., description="RICE score analysis")

    # Trade-off Analysis
    pros: List[str] = Field(..., min_items=1, description="Advantages of this alternative")
    cons: List[str] = Field(..., min_items=1, description="Disadvantages of this alternative")
    risks: List[str] = Field(..., min_items=1, description="Implementation risks")

    # Technical Details
    technical_approach: str = Field(..., min_length=20, description="Technical implementation approach")
    dependencies: List[str] = Field(default_factory=list, description="External dependencies")
    estimated_timeline: str = Field(..., description="Estimated timeline")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v):
        """Validate alternative ID is A, B, or C"""
        if v not in ["A", "B", "C"]:
            raise ValueError("Alternative ID must be 'A', 'B', or 'C'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "A",
                "title": "JWT + OAuth2 Hybrid Authentication",
                "description": (
                    "Implement a hybrid authentication system using JWT tokens for "
                    "session management and OAuth2 for third-party provider integration..."
                ),
                "concept_origin": "Security-first approach with flexibility",
                "knowledge_basis": ["OAuth2 specification", "JWT best practices", "Multi-tenant architecture"],
                "rice": {"reach": 8, "impact": 7, "confidence": 6, "effort": 5, "score": 6.72},
                "pros": ["Industry-standard security", "Flexible provider support", "Scalable architecture"],
                "cons": ["Complex token management", "Requires OAuth configuration per provider"],
                "risks": ["Token expiration edge cases", "OAuth provider outages"],
                "technical_approach": "Use FastAPI OAuth2 password flow with JWT tokens stored in HTTP-only cookies...",
                "dependencies": ["python-jose", "passlib", "python-multipart"],
                "estimated_timeline": "2 weeks",
                "metadata": {},
            }
        }


class TradeoffAnalysis(BaseModel):
    """Comparative trade-off analysis across alternatives"""

    summary: str = Field(..., min_length=50, max_length=1000, description="Overall trade-off summary")
    recommendation: str = Field(
        ..., min_length=50, max_length=1000, description="Recommended alternative with detailed reasoning"
    )
    comparison_matrix: Dict[str, Dict[str, Any]] = Field(..., description="Feature comparison matrix across alternatives")
    decision_tree: List[str] = Field(..., min_items=1, description="Decision-making criteria and flow")

    class Config:
        json_schema_extra = {
            "example": {
                "summary": "Alternative A offers the best balance of security and flexibility...",
                "recommendation": (
                    "Choose Alternative A (JWT + OAuth2 Hybrid) because it provides "
                    "industry-standard security while maintaining flexibility for "
                    "future provider additions..."
                ),
                "comparison_matrix": {
                    "security": {"A": "High", "B": "Medium", "C": "High"},
                    "complexity": {"A": "Medium", "B": "Low", "C": "High"},
                    "scalability": {"A": "High", "B": "Medium", "C": "High"},
                },
                "decision_tree": [
                    "If security is top priority -> Choose A or C",
                    "If simplicity is critical -> Choose B",
                    "If third-party providers needed -> Choose A",
                ],
            }
        }


class CKTheoryRequest(BaseModel):
    """Request to generate design alternatives using C-K Theory"""

    challenge: str = Field(..., min_length=10, max_length=1000, description="Design challenge to explore")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Design constraints (budget, timeline, team size, etc.)")
    project: Optional[str] = Field("UDO-Development-Platform", description="Project name")

    @field_validator("challenge")
    @classmethod
    def validate_challenge(cls, v):
        """Validate challenge statement"""
        # Check for meaningful content
        if len(v.strip().split()) < 3:
            raise ValueError("Challenge must contain at least 3 words")

        # Basic spam filter
        spam_patterns = ["test test test", "asdf", "xxxx", "1234"]
        if any(pattern in v.lower() for pattern in spam_patterns):
            raise ValueError("Invalid challenge statement")

        return v.strip()

    @field_validator("constraints")
    @classmethod
    def validate_constraints(cls, v):
        """Validate constraint structure"""
        if v is None:
            return {}

        # Validate constraint keys
        allowed_keys = {
            "budget",
            "team_size",
            "timeline",
            "complexity",
            "security_requirement",
            "performance_requirement",
            "scalability_requirement",
            "maintainability_requirement",
        }

        if invalid_keys := set(v.keys()) - allowed_keys:
            raise ValueError(f"Invalid constraint keys: {invalid_keys}")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "challenge": "Design an authentication system that supports multiple providers",
                "constraints": {"budget": "2 weeks", "team_size": 2, "security_requirement": "high", "complexity": "medium"},
                "project": "UDO-Development-Platform",
            }
        }


class CKTheoryResult(BaseModel):
    """Complete C-K Theory design result with 3 alternatives"""

    id: str = Field(..., description="Unique design ID")
    challenge: str = Field(..., description="Original design challenge")
    alternatives: List[DesignAlternative] = Field(
        ..., min_items=3, max_items=3, description="Three design alternatives (A, B, C)"
    )
    tradeoff_analysis: TradeoffAnalysis = Field(..., description="Comparative analysis of alternatives")
    total_duration_ms: int = Field(..., ge=0, description="Total execution time")
    created_at: datetime = Field(default_factory=datetime.now)
    project: Optional[str] = Field("UDO-Development-Platform")
    constraints: Optional[Dict[str, Any]] = Field(None, description="Applied design constraints")
    obsidian_path: Optional[str] = Field(None, description="Path to saved Obsidian note")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("alternatives")
    @classmethod
    def validate_alternatives_ids(cls, v):
        """Validate alternatives have IDs A, B, C"""
        ids = {alt.id for alt in v}
        expected = {"A", "B", "C"}

        if ids != expected:
            raise ValueError(f"Alternatives must have IDs A, B, C. Got: {ids}")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ck-2025-11-20-001",
                "challenge": "Design an authentication system that supports multiple providers",
                "alternatives": [
                    {"id": "A", "title": "JWT + OAuth2 Hybrid", "rice": {"score": 6.72}},
                    {"id": "B", "title": "Session-Based Auth", "rice": {"score": 5.40}},
                    {"id": "C", "title": "Passwordless + WebAuthn", "rice": {"score": 6.30}},
                ],
                "tradeoff_analysis": {
                    "summary": "Alternative A offers the best balance...",
                    "recommendation": "Choose Alternative A because...",
                },
                "total_duration_ms": 42000,
                "created_at": "2025-11-20T15:45:00",
                "obsidian_path": "개발일지/2025-11-20/CK-Design-Auth-System.md",
            }
        }


class DesignSummary(BaseModel):
    """Summary of design exploration for list views"""

    id: str
    challenge: str = Field(..., max_length=100)
    recommended_alternative: str
    avg_rice_score: float = Field(..., ge=0.0)
    total_duration_ms: int
    created_at: datetime
    project: Optional[str]

    class Config:
        json_schema_extra = {
            "example": {
                "id": "ck-2025-11-20-001",
                "challenge": "Design an authentication system that supports multiple providers",
                "recommended_alternative": "A",
                "avg_rice_score": 6.14,
                "total_duration_ms": 42000,
                "created_at": "2025-11-20T15:45:00",
                "project": "UDO-Development-Platform",
            }
        }


class DesignFeedback(BaseModel):
    """Feedback on design alternatives for learning"""

    design_id: str = Field(..., description="Design ID")
    alternative_id: Optional[str] = Field(None, description="Alternative ID (A, B, or C) if specific")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5")
    comments: Optional[str] = Field(None, max_length=1000)
    selected_alternative: Optional[str] = Field(None, description="Which alternative was actually implemented")
    outcome: Optional[str] = Field(None, description="Implementation outcome (success, partial, failure)")

    @field_validator("alternative_id", "selected_alternative")
    @classmethod
    def validate_alternative_id(cls, v):
        """Validate alternative ID"""
        if v is not None and v not in ["A", "B", "C"]:
            raise ValueError("Alternative ID must be 'A', 'B', or 'C'")
        return v

    @field_validator("outcome")
    @classmethod
    def validate_outcome(cls, v):
        """Validate outcome"""
        if v is not None and v not in ["success", "partial", "failure"]:
            raise ValueError("Outcome must be 'success', 'partial', or 'failure'")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "design_id": "ck-2025-11-20-001",
                "alternative_id": "A",
                "rating": 5,
                "comments": "Excellent balance of security and flexibility",
                "selected_alternative": "A",
                "outcome": "success",
            }
        }
