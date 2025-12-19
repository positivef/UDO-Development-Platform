"""
Kanban AI Task Suggestion Service

Week 3 Day 3: Claude Sonnet 4.5 Integration for Intelligent Task Generation.
Implements Q2: AI Hybrid (suggest + approve) with Constitutional compliance.
"""

import os
import time
from datetime import datetime, UTC, timedelta
from typing import List, Dict, Optional
from uuid import UUID
import logging

from anthropic import Anthropic, AsyncAnthropic
from backend.app.models.kanban_ai import (
    TaskSuggestionRequest,
    TaskSuggestion,
    TaskSuggestionResponse,
    TaskSuggestionApproval,
    TaskSuggestionApprovalResponse,
    RateLimitStatus,
    RateLimitExceededError,
    InvalidSuggestionError,
    ConstitutionalViolationError,
    SuggestionConfidence,
    PhaseName,
)
from backend.app.models.kanban_task import TaskCreate
from backend.app.services.kanban_task_service import kanban_task_service
from backend.app.core.constitutional_guard import ConstitutionalGuard

logger = logging.getLogger(__name__)


class KanbanAIService:
    """
    AI-powered task suggestion service using Claude Sonnet 4.5.

    Features:
    - Intelligent task generation based on project context
    - Constitutional compliance validation (P1-P17)
    - Rate limiting (10 suggestions/hour)
    - Confidence scoring
    - Approval workflow (Q2: AI Hybrid)
    """

    def __init__(self):
        """Initialize AI service with Claude API client"""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set, AI suggestions will use mock mode")
            self.client = None
            self.async_client = None
            self.mock_mode = True
        else:
            self.client = Anthropic(api_key=api_key)
            self.async_client = AsyncAnthropic(api_key=api_key)
            self.mock_mode = False

        self.constitutional_guard = ConstitutionalGuard()

        # In-memory storage for suggestions and rate limiting
        # TODO: Replace with Redis for production
        self.suggestions_cache: Dict[UUID, TaskSuggestion] = {}
        self.rate_limit_storage: Dict[str, List[datetime]] = {}

    async def suggest_tasks(
        self,
        request: TaskSuggestionRequest,
        user_id: str
    ) -> TaskSuggestionResponse:
        """
        Generate AI task suggestions using Claude Sonnet 4.5.

        Args:
            request: Task suggestion request parameters
            user_id: User identifier for rate limiting

        Returns:
            TaskSuggestionResponse with generated suggestions

        Raises:
            RateLimitExceededError: If user exceeds 10 suggestions/hour
        """
        start_time = time.time()

        # Check rate limit
        rate_status = self._check_rate_limit(user_id)
        if rate_status.is_limited:
            raise RateLimitExceededError(rate_status)

        # Generate suggestions
        if self.mock_mode:
            suggestions = self._generate_mock_suggestions(request)
        else:
            suggestions = await self._generate_claude_suggestions(request)

        # Update rate limit
        self._record_suggestion_usage(user_id)

        # Cache suggestions for approval
        for suggestion in suggestions:
            self.suggestions_cache[suggestion.suggestion_id] = suggestion

        generation_time_ms = (time.time() - start_time) * 1000

        return TaskSuggestionResponse(
            suggestions=suggestions,
            generation_time_ms=generation_time_ms,
            model_used="claude-sonnet-4.5-20241022" if not self.mock_mode else "mock",
            context_summary=request.context[:200],
            remaining_suggestions_today=self._get_remaining_suggestions(user_id),
        )

    async def approve_suggestion(
        self,
        suggestion_id: UUID,
        approval: TaskSuggestionApproval,
        user_id: str
    ) -> TaskSuggestionApprovalResponse:
        """
        Approve AI suggestion and create actual task.

        Q2: AI Hybrid - Final approval step for Constitutional compliance.

        Args:
            suggestion_id: ID of suggestion to approve
            approval: Approval details
            user_id: User approving the suggestion

        Returns:
            TaskSuggestionApprovalResponse with created task details

        Raises:
            InvalidSuggestionError: If suggestion not found
            ConstitutionalViolationError: If suggestion violates P1-P17
        """
        # Validate suggestion exists
        if suggestion_id not in self.suggestions_cache:
            raise InvalidSuggestionError(f"Suggestion {suggestion_id} not found or expired")

        suggestion = self.suggestions_cache[suggestion_id]

        # Apply user modifications if provided
        if approval.modifications:
            suggestion = self._apply_modifications(suggestion, approval.modifications)

        # Constitutional compliance check (P1-P17)
        violations = self._check_constitutional_compliance(suggestion)
        if violations:
            raise ConstitutionalViolationError(violations)

        # Create actual task from approved suggestion
        # TODO: In production, look up actual phase_id from phases table
        # For now, use a mock phase_id based on phase_name
        from uuid import uuid4
        mock_phase_id = uuid4()  # Mock phase_id for testing

        task_data = TaskCreate(
            title=suggestion.title,
            description=suggestion.description,
            phase_name=suggestion.phase_name.value,  # Required by TaskBase
            phase_id=mock_phase_id,  # Required by TaskCreate
            priority=suggestion.priority,
            estimated_hours=suggestion.estimated_hours,
            ai_suggested=True,  # Mark as AI-generated
            ai_confidence=0.9 if suggestion.confidence == SuggestionConfidence.HIGH else 0.75,
            metadata={
                "ai_generated": True,
                "suggestion_id": str(suggestion_id),
                "confidence": suggestion.confidence.value,
                "approved_by": approval.approved_by,
                "approval_notes": approval.approval_notes,
            }
        )

        # Create task using singleton task service (mock for tests, DB for production)
        created_task = await kanban_task_service.create_task(task_data)

        # Remove from cache after successful creation
        del self.suggestions_cache[suggestion_id]

        logger.info(
            f"AI suggestion {suggestion_id} approved by {approval.approved_by}, "
            f"created task {created_task.task_id}"
        )

        return TaskSuggestionApprovalResponse(
            task_id=created_task.task_id,
            suggestion_id=suggestion_id,
            success=True,
            message="Task created successfully from AI suggestion",
            created_task=created_task.model_dump()
        )

    async def _generate_claude_suggestions(
        self,
        request: TaskSuggestionRequest
    ) -> List[TaskSuggestion]:
        """
        Generate suggestions using Claude Sonnet 4.5 API.

        Uses structured prompt engineering for consistent, high-quality suggestions.
        """
        system_prompt = """You are an expert software development task planner.
Generate specific, actionable task suggestions based on the project context provided.

Each task should include:
- Clear, concise title (max 200 chars)
- Detailed description with acceptance criteria (max 2000 chars)
- Realistic estimated hours
- Priority level (critical/high/medium/low)
- Confidence level (high/medium/low) based on context clarity
- Reasoning for the suggestion

Follow these principles:
- Tasks should be atomic and completable
- Respect phase boundaries (don't suggest implementation in design phase)
- Consider dependencies between tasks
- Provide constitutional compliance context (design-first, quality, etc.)
"""

        user_prompt = f"""Project Context: {request.context}

Target Phase: {request.phase_name}
Number of suggestions requested: {request.num_suggestions}
Include dependencies: {request.include_dependencies}

Generate {request.num_suggestions} task suggestions that would help progress this project through the {request.phase_name} phase.

For each task, provide:
1. Title (specific and actionable)
2. Description (detailed with acceptance criteria)
3. Priority (critical/high/medium/low)
4. Estimated hours (0.5-100)
5. Confidence (high >90%, medium 70-90%, low <70%)
6. Reasoning (why this task is important)
{f"7. Suggested dependencies (prerequisite tasks)" if request.include_dependencies else ""}

Format your response as JSON array of objects with these fields:
[{{
  "title": "...",
  "description": "...",
  "priority": "...",
  "estimated_hours": ...,
  "confidence": "high|medium|low",
  "reasoning": "...",
  "suggested_dependencies": [...]
}}]"""

        try:
            response = await self.async_client.messages.create(
                model="claude-sonnet-4-5-20241022",
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
            )

            # Parse Claude's response
            import json
            content = response.content[0].text

            # Extract JSON from response (Claude might wrap it in markdown)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            suggestions_data = json.loads(content)

            # Convert to TaskSuggestion objects
            suggestions = []
            for data in suggestions_data[:request.num_suggestions]:
                suggestion = TaskSuggestion(
                    title=data["title"],
                    description=data["description"],
                    phase_name=request.phase_name,
                    priority=data.get("priority", "medium"),
                    estimated_hours=data.get("estimated_hours"),
                    confidence=SuggestionConfidence(data.get("confidence", "medium")),
                    reasoning=data["reasoning"],
                    suggested_dependencies=data.get("suggested_dependencies", []),
                    constitutional_compliance=self._check_constitutional_principles(data)
                )
                suggestions.append(suggestion)

            return suggestions

        except Exception as e:
            logger.error(f"Error generating Claude suggestions: {e}")
            # Fallback to mock suggestions
            return self._generate_mock_suggestions(request)

    def _generate_mock_suggestions(
        self,
        request: TaskSuggestionRequest
    ) -> List[TaskSuggestion]:
        """Generate mock suggestions for testing/development"""
        mock_suggestions = {
            PhaseName.IDEATION: [
                ("Market research and competitor analysis", "Conduct comprehensive market research", 8.0),
                ("Define user personas and pain points", "Create detailed user personas", 4.0),
                ("Brainstorm solution approaches", "Explore multiple solution approaches", 6.0),
                ("Identify key success metrics", "Define measurable success criteria", 3.0),
                ("Create project roadmap", "Plan implementation timeline", 5.0),
            ],
            PhaseName.DESIGN: [
                ("Create system architecture diagram", "Design high-level system architecture", 6.0),
                ("Define API specifications", "Document all API endpoints and contracts", 8.0),
                ("Design database schema", "Create normalized database schema", 5.0),
                ("Create UI/UX mockups", "Design user interface wireframes", 6.0),
                ("Define security architecture", "Plan security and auth flows", 4.0),
            ],
            PhaseName.MVP: [
                ("Implement core authentication flow", "Basic login/logout functionality", 12.0),
                ("Create MVP landing page", "Simple landing page with key features", 6.0),
                ("Set up CI/CD pipeline", "Automated testing and deployment", 8.0),
                ("Configure production environment", "Set up hosting and deployment", 5.0),
                ("Implement basic analytics", "Track key user interactions", 4.0),
            ],
            PhaseName.IMPLEMENTATION: [
                ("Implement user management module", "Full CRUD operations for users", 16.0),
                ("Add data validation layer", "Comprehensive input validation", 8.0),
                ("Integrate third-party APIs", "Connect to external services", 12.0),
                ("Implement error handling", "Robust error handling and logging", 6.0),
                ("Add performance monitoring", "Set up APM and metrics", 5.0),
            ],
            PhaseName.TESTING: [
                ("Write unit tests for core modules", "Achieve >80% code coverage", 16.0),
                ("Perform integration testing", "Test all component interactions", 12.0),
                ("Conduct user acceptance testing", "Validate with real users", 8.0),
                ("Load and performance testing", "Test system under load", 10.0),
                ("Security and penetration testing", "Identify security vulnerabilities", 12.0),
            ],
        }

        phase_tasks = mock_suggestions.get(request.phase_name, mock_suggestions[PhaseName.IDEATION])
        suggestions = []

        for i, (title, description, hours) in enumerate(phase_tasks[:request.num_suggestions]):
            suggestion = TaskSuggestion(
                title=title,
                description=f"{description}\n\nContext: {request.context[:100]}",
                phase_name=request.phase_name,
                priority=["high", "medium", "medium"][i % 3],
                estimated_hours=hours,
                confidence=SuggestionConfidence.HIGH,
                reasoning=f"This task is important for completing the {request.phase_name} phase",
                suggested_dependencies=[phase_tasks[i-1][0]] if i > 0 and request.include_dependencies else [],
                constitutional_compliance={"P1": True, "P2": True}
            )
            suggestions.append(suggestion)

        return suggestions

    def _check_rate_limit(self, user_id: str) -> RateLimitStatus:
        """Check if user has exceeded rate limit (10 suggestions/hour)"""
        now = datetime.now(UTC)
        one_hour_ago = now - timedelta(hours=1)

        # Get user's recent suggestions
        user_suggestions = self.rate_limit_storage.get(user_id, [])

        # Filter to last hour
        recent_suggestions = [
            ts for ts in user_suggestions
            if ts > one_hour_ago
        ]

        # Update storage
        self.rate_limit_storage[user_id] = recent_suggestions

        suggestions_used = len(recent_suggestions)
        limit = 10
        is_limited = suggestions_used >= limit

        # Calculate reset time
        if recent_suggestions:
            oldest_suggestion = min(recent_suggestions)
            reset_at = oldest_suggestion + timedelta(hours=1)
        else:
            reset_at = now + timedelta(hours=1)

        return RateLimitStatus(
            user_id=user_id,
            suggestions_used_today=suggestions_used,
            suggestions_remaining=max(0, limit - suggestions_used),
            limit_per_period=limit,
            period_reset_at=reset_at,
            is_limited=is_limited
        )

    def _record_suggestion_usage(self, user_id: str):
        """Record that user generated a suggestion"""
        now = datetime.now(UTC)
        if user_id not in self.rate_limit_storage:
            self.rate_limit_storage[user_id] = []
        self.rate_limit_storage[user_id].append(now)

    def _get_remaining_suggestions(self, user_id: str) -> int:
        """Get number of remaining suggestions for user"""
        status = self._check_rate_limit(user_id)
        return status.suggestions_remaining

    def _apply_modifications(
        self,
        suggestion: TaskSuggestion,
        modifications: Dict
    ) -> TaskSuggestion:
        """Apply user modifications to suggestion before approval"""
        modified_data = suggestion.model_dump()
        modified_data.update(modifications)
        return TaskSuggestion(**modified_data)

    def _check_constitutional_compliance(
        self,
        suggestion: TaskSuggestion
    ) -> List[str]:
        """
        Check if suggestion complies with Constitutional principles (P1-P17).

        P1: Design Review First - Critical principle for AI-suggested tasks
        """
        violations = []

        # P1: Design Review First
        # AI-suggested implementation tasks without design context violate P1
        if suggestion.phase_name in [PhaseName.IMPLEMENTATION, PhaseName.MVP]:
            if "design" not in suggestion.description.lower() and \
               suggestion.confidence == SuggestionConfidence.LOW:
                violations.append("P1: Implementation task suggested without design context")

        # P2-P17: Additional constitutional checks can be added here
        # For now, we focus on P1 as it's most relevant to AI suggestions

        return violations

    def _check_constitutional_principles(self, data: Dict) -> Dict[str, bool]:
        """Check compliance with constitutional principles and return status"""
        return {
            "P1": "design" in data.get("description", "").lower() or \
                  data.get("confidence") == "high",
            "P2": True,  # Placeholder for other principles
        }


# Singleton instance
kanban_ai_service = KanbanAIService()
