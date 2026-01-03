#!/usr/bin/env python3
"""
Unit tests for MockProjectService response structure validation

Tests Pydantic model compatibility and response field completeness
to ensure API contract compliance.

Critical Issue #2: Prevent regression of response structure bugs
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict  # noqa: F401
from uuid import UUID, uuid4

import pytest

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.mock_project_service import MockProjectService


class TestMockProjectServiceResponseStructure:
    """Test response structure for all MockProjectService methods"""

    @pytest.fixture
    def service(self):
        """Create MockProjectService instance"""
        return MockProjectService()

    @pytest.mark.asyncio
    async def test_list_projects_response_structure(self, service):
        """Test list_projects returns correct response structure"""
        result = await service.list_projects()

        # Required fields
        assert "projects" in result
        assert "total" in result
        assert "current_project_id" in result

        # Type validation
        assert isinstance(result["projects"], list)
        assert isinstance(result["total"], int)
        assert result["current_project_id"] is None or isinstance(result["current_project_id"], str)

        # Projects structure
        if result["projects"]:
            project = result["projects"][0]
            assert "id" in project
            assert "name" in project
            assert "description" in project
            assert "current_phase" in project
            assert "is_active" in project
            assert "has_context" in project

    @pytest.mark.asyncio
    async def test_get_current_project_response_structure(self, service):
        """Test get_current_project returns correct response structure"""
        result = await service.get_current_project()

        # Should return a project dict
        assert isinstance(result, dict)

        # Required fields
        assert "id" in result
        assert "name" in result
        assert "description" in result
        assert "current_phase" in result
        assert "is_active" in result
        assert "has_context" in result

        # Type validation
        assert isinstance(result["id"], str)
        assert isinstance(result["name"], str)
        assert isinstance(result["is_active"], bool)

    @pytest.mark.asyncio
    async def test_save_context_response_structure(self, service):
        """Test save_context returns correct response structure"""
        project_id = uuid4()

        result = await service.save_context(
            project_id=project_id,
            udo_state={"phase": "testing"},
            ml_models={"model": "test"},
            recent_executions=[{"id": "exec1"}],
            ai_preferences={"model": "claude"},
            editor_state={"cursor": 0},
        )

        # Required fields (matching ProjectContextResponse model)
        assert "id" in result  # Required by Pydantic
        assert "project_id" in result
        assert "udo_state" in result
        assert "ml_models" in result
        assert "recent_executions" in result
        assert "ai_preferences" in result
        assert "editor_state" in result
        assert "saved_at" in result  # Changed from created_at
        assert "loaded_at" in result  # Changed from updated_at

        # Type validation
        assert isinstance(result["project_id"], str)
        assert isinstance(result["udo_state"], dict)
        assert isinstance(result["ml_models"], dict)
        assert isinstance(result["recent_executions"], list)

        # Values match input
        assert result["udo_state"]["phase"] == "testing"
        assert result["ml_models"]["model"] == "test"

    @pytest.mark.asyncio
    async def test_load_context_response_structure(self, service):
        """Test load_context returns correct response structure"""
        # Get first project ID
        projects = await service.list_projects()
        project_id = UUID(projects["projects"][0]["id"])

        result = await service.load_context(project_id)

        # Should return context dict
        assert isinstance(result, dict)

        # Required fields (matching ProjectContextResponse model)
        assert "id" in result  # Critical for Pydantic
        assert "project_id" in result
        assert "udo_state" in result
        assert "ml_models" in result
        assert "recent_executions" in result
        assert "ai_preferences" in result
        assert "editor_state" in result
        assert "saved_at" in result  # Critical for Pydantic
        assert "loaded_at" in result  # Updated field name

        # Type validation
        assert isinstance(result["project_id"], str)
        assert isinstance(result["udo_state"], dict)
        assert isinstance(result["ml_models"], dict)

    @pytest.mark.asyncio
    async def test_load_context_nonexistent_project(self, service):
        """Test load_context returns None for non-existent project"""
        fake_id = uuid4()

        result = await service.load_context(fake_id)

        # Should return None (not raise exception)
        assert result is None

    @pytest.mark.asyncio
    async def test_switch_project_response_structure(self, service):
        """Test switch_project returns correct response structure (Critical!)"""
        # Get second project ID to switch to
        projects = await service.list_projects()
        target_id = UUID(projects["projects"][1]["id"])

        result = await service.switch_project(target_id)

        # Required fields (Pydantic validation)
        assert "previous_project_id" in result
        assert "new_project_id" in result
        assert "context_loaded" in result
        assert "context" in result
        assert "message" in result

        # Type validation
        assert isinstance(result["new_project_id"], str)
        assert isinstance(result["context_loaded"], bool)
        assert isinstance(result["message"], str)

        # Context should be present if context_loaded is True
        if result["context_loaded"]:
            assert result["context"] is not None
            assert isinstance(result["context"], dict)

        # Verify new project is active
        assert str(target_id) == result["new_project_id"]

    @pytest.mark.asyncio
    async def test_switch_project_invalid_id(self, service):
        """Test switch_project raises ValueError for invalid project ID"""
        fake_id = uuid4()

        with pytest.raises(ValueError) as exc_info:
            await service.switch_project(fake_id)

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_delete_context_response(self, service):
        """Test delete_context returns boolean"""
        # Get first project ID
        projects = await service.list_projects()
        project_id = UUID(projects["projects"][0]["id"])

        result = await service.delete_context(project_id)

        # Should return boolean
        assert isinstance(result, bool)
        assert result is True  # Should succeed for existing project

    @pytest.mark.asyncio
    async def test_delete_context_nonexistent_project(self, service):
        """Test delete_context returns False for non-existent project"""
        fake_id = uuid4()

        result = await service.delete_context(fake_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_merge_context_response_structure(self, service):
        """Test merge_context returns correct response structure"""
        project_id = uuid4()

        partial_context = {
            "udo_state": {"phase": "design"},
            "ml_models": {"accuracy": 0.9},
        }

        result = await service.merge_context(project_id, partial_context)

        # Required fields
        assert "project_id" in result
        assert "udo_state" in result
        assert "ml_models" in result
        assert "recent_executions" in result
        assert "ai_preferences" in result
        assert "editor_state" in result
        assert "saved_at" in result
        assert "loaded_at" in result

        # Type validation
        assert isinstance(result["project_id"], str)
        assert isinstance(result["udo_state"], dict)

        # Values match partial input
        assert result["udo_state"]["phase"] == "design"

    @pytest.mark.asyncio
    async def test_initialize_default_project_response(self, service):
        """Test initialize_default_project returns UUID"""
        result = await service.initialize_default_project()

        # Should return UUID or None
        assert result is None or isinstance(result, UUID)

        # Should return UUID if projects exist
        if service.mock_projects:
            assert isinstance(result, UUID)


class TestMockProjectServiceFieldTypes:
    """Test field types for Pydantic compatibility"""

    @pytest.fixture
    def service(self):
        """Create MockProjectService instance"""
        return MockProjectService()

    @pytest.mark.asyncio
    async def test_datetime_field_serialization(self, service):
        """Test datetime fields are properly serialized as ISO strings"""
        projects = await service.list_projects()
        project = projects["projects"][0]

        # Datetime fields should be ISO format strings
        assert isinstance(project["last_active_at"], str)
        assert isinstance(project["created_at"], str)

        # Should be parseable as datetime
        datetime.fromisoformat(project["last_active_at"])
        datetime.fromisoformat(project["created_at"])

    @pytest.mark.asyncio
    async def test_uuid_field_serialization(self, service):
        """Test UUID fields are properly serialized as strings"""
        projects = await service.list_projects()
        project = projects["projects"][0]

        # UUID should be string
        assert isinstance(project["id"], str)

        # Should be valid UUID format
        UUID(project["id"])  # Will raise if invalid

    @pytest.mark.asyncio
    async def test_boolean_field_types(self, service):
        """Test boolean fields return actual booleans"""
        projects = await service.list_projects()
        project = projects["projects"][0]

        # Boolean fields should be bool type
        assert isinstance(project["is_active"], bool)
        assert isinstance(project["has_context"], bool)
        assert isinstance(project["is_archived"], bool)


class TestMockProjectServiceContextStructure:
    """Test context object structure for nested validation"""

    @pytest.fixture
    def service(self):
        """Create MockProjectService instance"""
        return MockProjectService()

    @pytest.mark.asyncio
    async def test_context_nested_structure(self, service):
        """Test context object has correct nested structure"""
        projects = await service.list_projects()
        project_id = UUID(projects["projects"][0]["id"])

        context = await service.load_context(project_id)

        # UDO state structure
        assert "current_phase" in context["udo_state"]
        assert "confidence_level" in context["udo_state"]
        assert "quantum_state" in context["udo_state"]
        assert "decision" in context["udo_state"]

        # ML models structure
        assert "active_models" in context["ml_models"]
        assert "accuracy" in context["ml_models"]
        assert isinstance(context["ml_models"]["active_models"], list)

        # AI preferences structure
        assert "preferred_model" in context["ai_preferences"]
        assert "temperature" in context["ai_preferences"]

        # Editor state structure
        assert "open_files" in context["editor_state"]
        assert "cursor_positions" in context["editor_state"]

    @pytest.mark.asyncio
    async def test_context_consistency_across_operations(self, service):
        """Test context structure is consistent between save and load"""
        project_id = uuid4()

        # Save context
        saved = await service.save_context(
            project_id=project_id,
            udo_state={"test": "value"},
            ml_models={"model": "test"},
        )

        # Load context
        loaded = await service.load_context(project_id)

        # Both should have same required fields
        assert "project_id" in saved
        assert "project_id" in loaded

        # Types should match
        assert type(saved["udo_state"]) is type(loaded["udo_state"])
        assert type(saved["ml_models"]) is type(loaded["ml_models"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
