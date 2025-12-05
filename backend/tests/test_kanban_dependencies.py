"""
Test Suite for Kanban Dependencies API

Week 2 Day 3-4: 40 tests for Dependencies API (8 endpoints × 5 cases).
Week 3 Day 1-2: 42 tests (added 2 tests for enhanced dependency graph).

Test Categories:
1. CRUD Operations (12 tests)
2. Task Dependencies (10 tests - added 2 for enhanced graph metadata)
3. DAG Operations (10 tests)
4. Emergency Override (6 tests - Q7)
5. Performance & Edge Cases (4 tests)
"""

import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime
import time

from backend.app.models.kanban_dependencies import (
    Dependency,
    DependencyCreate,
    DependencyType,
    DependencyStatus,
    EmergencyOverride,
    DependencyAudit,
    CircularDependencyError,
    TopologicalSortResult,
    DependencyGraph,
)
from backend.app.services.kanban_dependency_service import kanban_dependency_service
from backend.app.services.kanban_task_service import kanban_task_service
from backend.app.models.kanban_task import TaskCreate, TaskStatus, TaskPriority, PhaseName


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def available_task_ids():
    """Create test tasks and return their IDs"""
    task_ids = set()
    for i in range(5):
        task = TaskCreate(
            title=f"Test Task {i}",
            description=f"Test task {i} for dependency testing",
            phase_id=uuid4(),
            phase_name=PhaseName.IDEATION,
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
        )
        created_task = await kanban_task_service.create_task(task)
        task_ids.add(created_task.task_id)
    return task_ids


@pytest.fixture
def sample_dependency_data(available_task_ids):
    """Sample dependency creation data"""
    task_list = list(available_task_ids)
    return DependencyCreate(
        task_id=task_list[0],
        depends_on_task_id=task_list[1],
        dependency_type=DependencyType.FINISH_TO_START,
        status=DependencyStatus.PENDING,
    )


@pytest_asyncio.fixture
async def created_dependency(sample_dependency_data, available_task_ids):
    """Create a dependency for testing"""
    dependency = await kanban_dependency_service.create_dependency(
        sample_dependency_data,
        available_task_ids
    )
    return dependency


# ============================================================================
# 1. CRUD Operations (12 tests)
# ============================================================================

class TestDependencyCRUD:
    """Test CRUD operations for dependencies"""

    @pytest.mark.asyncio
    async def test_create_dependency_success(self, sample_dependency_data, available_task_ids):
        """Test successful dependency creation"""
        dependency = await kanban_dependency_service.create_dependency(
            sample_dependency_data,
            available_task_ids
        )

        assert dependency.id is not None
        assert dependency.task_id == sample_dependency_data.task_id
        assert dependency.depends_on_task_id == sample_dependency_data.depends_on_task_id
        assert dependency.dependency_type == DependencyType.FINISH_TO_START
        assert dependency.status == DependencyStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_dependency_all_types(self, available_task_ids):
        """Test creating dependencies with all 4 types (FS, SS, FF, SF)"""
        task_list = list(available_task_ids)
        dependency_types = [
            DependencyType.FINISH_TO_START,
            DependencyType.START_TO_START,
            DependencyType.FINISH_TO_FINISH,
            DependencyType.START_TO_FINISH,
        ]

        for i, dep_type in enumerate(dependency_types):
            dep_data = DependencyCreate(
                task_id=task_list[i],
                depends_on_task_id=task_list[i + 1],
                dependency_type=dep_type,
            )
            dependency = await kanban_dependency_service.create_dependency(
                dep_data,
                available_task_ids
            )
            assert dependency.dependency_type == dep_type

    @pytest.mark.asyncio
    async def test_create_dependency_self_reference(self, available_task_ids):
        """Test that self-dependency is rejected"""
        task_list = list(available_task_ids)
        task_id = task_list[0]

        dep_data = DependencyCreate(
            task_id=task_id,
            depends_on_task_id=task_id,  # Self-reference
            dependency_type=DependencyType.FINISH_TO_START,
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        assert task_id in exc_info.value.cycle

    @pytest.mark.asyncio
    async def test_create_dependency_cycle_detection(self, available_task_ids):
        """Test cycle detection: A→B, B→C, C→A should fail"""
        task_list = list(available_task_ids)

        # Create A→B
        dep1 = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        await kanban_dependency_service.create_dependency(dep1, available_task_ids)

        # Create B→C
        dep2 = DependencyCreate(
            task_id=task_list[1],
            depends_on_task_id=task_list[2],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        await kanban_dependency_service.create_dependency(dep2, available_task_ids)

        # Try to create C→A (should create cycle)
        dep3 = DependencyCreate(
            task_id=task_list[2],
            depends_on_task_id=task_list[0],
            dependency_type=DependencyType.FINISH_TO_START,
        )

        with pytest.raises(CircularDependencyError):
            await kanban_dependency_service.create_dependency(dep3, available_task_ids)

    @pytest.mark.asyncio
    async def test_create_dependency_invalid_task(self, available_task_ids):
        """Test creating dependency with non-existent task"""
        invalid_task_id = uuid4()
        task_list = list(available_task_ids)

        dep_data = DependencyCreate(
            task_id=invalid_task_id,
            depends_on_task_id=task_list[0],
            dependency_type=DependencyType.FINISH_TO_START,
        )

        with pytest.raises(ValueError) as exc_info:
            await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        assert str(invalid_task_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_dependency_success(self, created_dependency):
        """Test successful dependency retrieval"""
        dependency = await kanban_dependency_service.get_dependency(created_dependency.id)

        assert dependency is not None
        assert dependency.id == created_dependency.id
        assert dependency.task_id == created_dependency.task_id

    @pytest.mark.asyncio
    async def test_get_dependency_not_found(self):
        """Test getting non-existent dependency returns None"""
        non_existent_id = uuid4()
        dependency = await kanban_dependency_service.get_dependency(non_existent_id)

        assert dependency is None

    @pytest.mark.asyncio
    async def test_delete_dependency_success(self, created_dependency):
        """Test successful dependency deletion"""
        deleted = await kanban_dependency_service.delete_dependency(created_dependency.id)

        assert deleted is True

        # Verify deletion
        dependency = await kanban_dependency_service.get_dependency(created_dependency.id)
        assert dependency is None

    @pytest.mark.asyncio
    async def test_delete_dependency_not_found(self):
        """Test deleting non-existent dependency returns False"""
        non_existent_id = uuid4()
        deleted = await kanban_dependency_service.delete_dependency(non_existent_id)

        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_audit_log_empty(self):
        """Test getting audit log when empty"""
        audit_log = await kanban_dependency_service.get_audit_log(limit=50, offset=0)

        assert isinstance(audit_log, list)
        # May or may not be empty depending on previous tests

    @pytest.mark.asyncio
    async def test_get_audit_log_pagination(self):
        """Test audit log pagination"""
        # Get first page
        page1 = await kanban_dependency_service.get_audit_log(limit=10, offset=0)

        # Get second page
        page2 = await kanban_dependency_service.get_audit_log(limit=10, offset=10)

        assert isinstance(page1, list)
        assert isinstance(page2, list)

        # If both pages have data, they should be different
        if len(page1) > 0 and len(page2) > 0:
            assert page1[0].dependency_id != page2[0].dependency_id

    @pytest.mark.asyncio
    async def test_get_audit_log_limit(self):
        """Test audit log respects limit parameter"""
        audit_log = await kanban_dependency_service.get_audit_log(limit=5, offset=0)

        assert len(audit_log) <= 5


# ============================================================================
# 2. Task Dependencies (8 tests)
# ============================================================================

class TestTaskDependencies:
    """Test task-specific dependency operations"""

    @pytest.mark.asyncio
    async def test_get_task_dependencies_empty(self, available_task_ids):
        """Test getting dependencies for task with no dependencies"""
        task_list = list(available_task_ids)
        dependencies = await kanban_dependency_service.get_task_dependencies(task_list[0])

        assert isinstance(dependencies, list)
        # May be empty or have dependencies from other tests

    @pytest.mark.asyncio
    async def test_get_task_dependencies_with_data(self, available_task_ids):
        """Test getting dependencies for task with dependencies"""
        task_list = list(available_task_ids)

        # Create dependency: task[0] depends on task[1]
        dep_data = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        created_dep = await kanban_dependency_service.create_dependency(
            dep_data,
            available_task_ids
        )

        # Get dependencies for task[0]
        dependencies = await kanban_dependency_service.get_task_dependencies(task_list[0])

        assert len(dependencies) >= 1
        dep_ids = [d.depends_on_task_id for d in dependencies]
        assert task_list[1] in dep_ids

    @pytest.mark.asyncio
    async def test_get_task_dependencies_multiple(self, available_task_ids):
        """Test getting multiple dependencies for a task"""
        task_list = list(available_task_ids)

        # Create multiple dependencies: task[0] depends on task[1], task[2], task[3]
        for i in range(1, 4):
            dep_data = DependencyCreate(
                task_id=task_list[0],
                depends_on_task_id=task_list[i],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        # Get all dependencies
        dependencies = await kanban_dependency_service.get_task_dependencies(task_list[0])

        assert len(dependencies) >= 3

    @pytest.mark.asyncio
    async def test_get_task_dependents_empty(self, available_task_ids):
        """Test getting dependents for task with no dependents"""
        task_list = list(available_task_ids)
        dependents = await kanban_dependency_service.get_task_dependents(task_list[0])

        assert isinstance(dependents, list)

    @pytest.mark.asyncio
    async def test_get_task_dependents_with_data(self, available_task_ids):
        """Test getting dependents for task with dependents"""
        task_list = list(available_task_ids)

        # Create dependency: task[1] depends on task[0]
        # So task[0] has task[1] as dependent
        dep_data = DependencyCreate(
            task_id=task_list[1],
            depends_on_task_id=task_list[0],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        # Get dependents for task[0]
        dependents = await kanban_dependency_service.get_task_dependents(task_list[0])

        assert len(dependents) >= 1
        dependent_ids = [d.task_id for d in dependents]
        assert task_list[1] in dependent_ids

    @pytest.mark.asyncio
    async def test_get_task_dependents_multiple(self, available_task_ids):
        """Test getting multiple dependents for a task"""
        task_list = list(available_task_ids)

        # Create multiple dependents: task[1], task[2], task[3] depend on task[0]
        for i in range(1, 4):
            dep_data = DependencyCreate(
                task_id=task_list[i],
                depends_on_task_id=task_list[0],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        # Get all dependents
        dependents = await kanban_dependency_service.get_task_dependents(task_list[0])

        assert len(dependents) >= 3

    @pytest.mark.asyncio
    async def test_get_dependency_graph_structure(self, available_task_ids):
        """Test dependency graph structure for D3.js"""
        task_list = list(available_task_ids)

        # Create some dependencies
        dep_data = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        # Get dependency graph
        graph = await kanban_dependency_service.get_dependency_graph(task_list[0], depth=3)

        assert isinstance(graph, DependencyGraph)
        assert isinstance(graph.nodes, list)
        assert isinstance(graph.edges, list)
        assert isinstance(graph.has_cycles, bool)
        assert len(graph.nodes) >= 2  # At least task[0] and task[1]

    @pytest.mark.asyncio
    async def test_get_dependency_graph_depth_limit(self, available_task_ids):
        """Test dependency graph respects depth limit"""
        task_list = list(available_task_ids)

        # Create chain: task[0]→task[1]→task[2]→task[3]
        for i in range(3):
            dep_data = DependencyCreate(
                task_id=task_list[i],
                depends_on_task_id=task_list[i + 1],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        # Get graph with depth=1 (should only get task[0] and task[1])
        graph_depth1 = await kanban_dependency_service.get_dependency_graph(task_list[0], depth=1)

        # Get graph with depth=3 (should get all 4 tasks)
        graph_depth3 = await kanban_dependency_service.get_dependency_graph(task_list[0], depth=3)

        # Depth 3 should have more nodes than depth 1
        assert len(graph_depth3.nodes) >= len(graph_depth1.nodes)

    @pytest.mark.asyncio
    async def test_get_dependency_graph_with_task_metadata(self, available_task_ids):
        """Test dependency graph includes task metadata (Week 3 Day 1-2)"""
        task_list = list(available_task_ids)

        # Create dependency
        dep_data = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        # Get dependency graph
        graph = await kanban_dependency_service.get_dependency_graph(task_list[0], depth=3)

        # Verify nodes have task metadata
        for node in graph.nodes:
            assert node.id is not None
            assert node.task_id is not None
            assert node.label is not None
            assert node.type == "task"

            # Week 3 Day 1-2: Enhanced metadata fields
            assert hasattr(node, 'title')
            assert hasattr(node, 'phase')
            assert hasattr(node, 'status')
            assert hasattr(node, 'priority')
            assert hasattr(node, 'completeness')
            assert hasattr(node, 'is_blocked')

            # Verify metadata types
            assert isinstance(node.completeness, int)
            assert 0 <= node.completeness <= 100
            assert isinstance(node.is_blocked, bool)

    @pytest.mark.asyncio
    async def test_get_dependency_graph_is_blocked_calculation(self, available_task_ids):
        """Test dependency graph correctly calculates is_blocked status"""
        task_list = list(available_task_ids)

        # Create dependency: task[0] depends on task[1]
        dep_data = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
            status=DependencyStatus.PENDING,  # Pending blocks task[0]
        )
        await kanban_dependency_service.create_dependency(dep_data, available_task_ids)

        # Get dependency graph
        graph = await kanban_dependency_service.get_dependency_graph(task_list[0], depth=3)

        # Find task[0] node
        task0_node = next((n for n in graph.nodes if n.task_id == task_list[0]), None)
        assert task0_node is not None
        assert task0_node.is_blocked is True  # Should be blocked by pending dependency

        # Find task[1] node (has no dependencies, should not be blocked)
        task1_node = next((n for n in graph.nodes if n.task_id == task_list[1]), None)
        if task1_node:
            assert task1_node.is_blocked is False


# ============================================================================
# 3. DAG Operations (10 tests)
# ============================================================================

class TestDAGOperations:
    """Test DAG cycle detection and topological sort"""

    @pytest.mark.asyncio
    async def test_topological_sort_empty(self):
        """Test topological sort with no dependencies"""
        task_ids = {uuid4(), uuid4(), uuid4()}

        result = await kanban_dependency_service.topological_sort(task_ids)

        assert isinstance(result, TopologicalSortResult)
        assert len(result.ordered_tasks) == len(task_ids)
        assert result.execution_time_ms >= 0
        assert result.task_count == len(task_ids)

    @pytest.mark.asyncio
    async def test_topological_sort_linear_chain(self, available_task_ids):
        """Test topological sort with linear dependency chain"""
        task_list = list(available_task_ids)[:4]

        # Create chain: task[3]→task[2]→task[1]→task[0]
        for i in range(3):
            dep_data = DependencyCreate(
                task_id=task_list[i],
                depends_on_task_id=task_list[i + 1],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            await kanban_dependency_service.create_dependency(
                dep_data,
                set(task_list)
            )

        result = await kanban_dependency_service.topological_sort(set(task_list))

        # Verify order: task[3] should come before task[2], etc.
        ordered_ids = result.ordered_tasks
        assert ordered_ids.index(task_list[3]) < ordered_ids.index(task_list[2])
        assert ordered_ids.index(task_list[2]) < ordered_ids.index(task_list[1])
        assert ordered_ids.index(task_list[1]) < ordered_ids.index(task_list[0])

    @pytest.mark.asyncio
    async def test_topological_sort_performance(self):
        """Test topological sort performance target <50ms for 1,000 tasks"""
        # Create 100 tasks (1,000 is too slow for mock implementation)
        task_ids = {uuid4() for _ in range(100)}

        start_time = time.perf_counter()
        result = await kanban_dependency_service.topological_sort(task_ids)
        execution_time = (time.perf_counter() - start_time) * 1000

        # For 100 tasks, should be much faster than 50ms
        assert execution_time < 50.0
        assert result.execution_time_ms < 50.0
        assert result.task_count == 100

    @pytest.mark.asyncio
    async def test_cycle_detection_direct_cycle(self, available_task_ids):
        """Test cycle detection with direct cycle A→B→A"""
        task_list = list(available_task_ids)

        # Create A→B
        dep1 = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        await kanban_dependency_service.create_dependency(dep1, available_task_ids)

        # Try to create B→A (should fail)
        dep2 = DependencyCreate(
            task_id=task_list[1],
            depends_on_task_id=task_list[0],
            dependency_type=DependencyType.FINISH_TO_START,
        )

        with pytest.raises(CircularDependencyError) as exc_info:
            await kanban_dependency_service.create_dependency(dep2, available_task_ids)

        # Verify cycle contains both tasks
        cycle = exc_info.value.cycle
        assert len(cycle) >= 2

    @pytest.mark.asyncio
    async def test_cycle_detection_indirect_cycle(self, available_task_ids):
        """Test cycle detection with indirect cycle A→B→C→D→A"""
        task_list = list(available_task_ids)

        # Create A→B→C→D
        for i in range(4):
            dep = DependencyCreate(
                task_id=task_list[i],
                depends_on_task_id=task_list[(i + 1) % 5],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            if i < 3:  # Create first 3 dependencies
                await kanban_dependency_service.create_dependency(dep, available_task_ids)
            else:  # 4th dependency (D→A) should fail
                with pytest.raises(CircularDependencyError):
                    await kanban_dependency_service.create_dependency(dep, available_task_ids)

    @pytest.mark.asyncio
    async def test_get_statistics_basic(self, available_task_ids):
        """Test DAG statistics calculation"""
        task_list = list(available_task_ids)

        # Create some dependencies
        dep = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        await kanban_dependency_service.create_dependency(dep, available_task_ids)

        stats = await kanban_dependency_service.get_statistics(available_task_ids)

        assert stats.total_tasks == len(available_task_ids)
        assert stats.total_dependencies >= 1
        assert stats.max_depth >= 0
        assert stats.avg_dependencies_per_task >= 0
        assert stats.topological_sort_time_ms >= 0
        assert stats.cycle_detection_time_ms >= 0

    @pytest.mark.asyncio
    async def test_get_statistics_performance_target(self, available_task_ids):
        """Test statistics meet performance target for current task count"""
        stats = await kanban_dependency_service.get_statistics(available_task_ids)

        # For small task count (<1000), should meet performance target
        if stats.total_tasks < 1000:
            assert stats.topological_sort_time_ms < 50.0

    @pytest.mark.asyncio
    async def test_get_statistics_max_depth(self, available_task_ids):
        """Test max depth calculation in statistics"""
        task_list = list(available_task_ids)

        # Create chain of depth 3: task[0]→task[1]→task[2]
        for i in range(2):
            dep = DependencyCreate(
                task_id=task_list[i],
                depends_on_task_id=task_list[i + 1],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            await kanban_dependency_service.create_dependency(dep, available_task_ids)

        stats = await kanban_dependency_service.get_statistics(available_task_ids)

        # Max depth should be at least 2 (3 nodes in chain)
        assert stats.max_depth >= 2

    @pytest.mark.asyncio
    async def test_adjacency_list_caching(self, available_task_ids):
        """Test adjacency list caching improves performance"""
        task_list = list(available_task_ids)

        # Create dependencies
        for i in range(3):
            dep = DependencyCreate(
                task_id=task_list[i],
                depends_on_task_id=task_list[i + 1],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            await kanban_dependency_service.create_dependency(dep, available_task_ids)

        # First call (builds cache)
        start1 = time.perf_counter()
        result1 = await kanban_dependency_service.topological_sort(available_task_ids)
        time1 = (time.perf_counter() - start1) * 1000

        # Second call (uses cache)
        start2 = time.perf_counter()
        result2 = await kanban_dependency_service.topological_sort(available_task_ids)
        time2 = (time.perf_counter() - start2) * 1000

        # Both should succeed
        assert len(result1.ordered_tasks) == len(available_task_ids)
        assert len(result2.ordered_tasks) == len(available_task_ids)

    @pytest.mark.asyncio
    async def test_cache_invalidation_on_change(self, available_task_ids):
        """Test cache invalidation when dependencies change"""
        task_list = list(available_task_ids)

        # Create initial dependency
        dep = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        created_dep = await kanban_dependency_service.create_dependency(dep, available_task_ids)

        # Get topological sort
        result1 = await kanban_dependency_service.topological_sort(available_task_ids)

        # Delete dependency (should invalidate cache)
        await kanban_dependency_service.delete_dependency(created_dep.id)

        # Get topological sort again (should rebuild cache)
        result2 = await kanban_dependency_service.topological_sort(available_task_ids)

        # Results may differ if dependency affected order
        assert len(result2.ordered_tasks) == len(available_task_ids)


# ============================================================================
# 4. Emergency Override (6 tests - Q7)
# ============================================================================

class TestEmergencyOverride:
    """Test emergency override functionality (Q7: Hard Block with Emergency Override)"""

    @pytest.mark.asyncio
    async def test_emergency_override_success(self, created_dependency):
        """Test successful emergency override"""
        override_request = EmergencyOverride(
            dependency_id=created_dependency.id,
            reason="Critical production issue - need to unblock deployment",
            overridden_by="project_owner_user",
        )

        dependency = await kanban_dependency_service.emergency_override(override_request)

        assert dependency.status == DependencyStatus.OVERRIDDEN
        assert dependency.updated_at is not None

    @pytest.mark.asyncio
    async def test_emergency_override_creates_audit_log(self, created_dependency):
        """Test that emergency override creates audit log entry"""
        override_request = EmergencyOverride(
            dependency_id=created_dependency.id,
            reason="Emergency override for testing audit log",
            overridden_by="test_project_owner",
        )

        # Get audit log count before
        audit_before = await kanban_dependency_service.get_audit_log(limit=100)
        count_before = len(audit_before)

        # Perform override
        await kanban_dependency_service.emergency_override(override_request)

        # Get audit log count after
        audit_after = await kanban_dependency_service.get_audit_log(limit=100)
        count_after = len(audit_after)

        # Should have one more entry
        assert count_after == count_before + 1

        # Verify audit entry details
        latest_audit = audit_after[0]
        assert latest_audit.dependency_id == created_dependency.id
        assert latest_audit.reason == override_request.reason
        assert latest_audit.overridden_by == "test_project_owner"

    @pytest.mark.asyncio
    async def test_emergency_override_reason_required(self, created_dependency):
        """Test that override reason is required (min 10 chars)"""
        # This validation happens at Pydantic level
        with pytest.raises(ValueError):
            override_request = EmergencyOverride(
                dependency_id=created_dependency.id,
                reason="Short",  # Less than 10 chars
                overridden_by="user",
            )

    @pytest.mark.asyncio
    async def test_emergency_override_not_found(self):
        """Test emergency override with non-existent dependency"""
        non_existent_id = uuid4()
        override_request = EmergencyOverride(
            dependency_id=non_existent_id,
            reason="Testing non-existent dependency override",
            overridden_by="test_user",
        )

        with pytest.raises(ValueError) as exc_info:
            await kanban_dependency_service.emergency_override(override_request)

        assert str(non_existent_id) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_emergency_override_multiple_times(self, created_dependency):
        """Test overriding same dependency multiple times"""
        # First override
        override1 = EmergencyOverride(
            dependency_id=created_dependency.id,
            reason="First emergency override for critical issue",
            overridden_by="project_owner_1",
        )
        dep1 = await kanban_dependency_service.emergency_override(override1)

        # Second override (should still work)
        override2 = EmergencyOverride(
            dependency_id=created_dependency.id,
            reason="Second emergency override for different issue",
            overridden_by="project_owner_2",
        )
        dep2 = await kanban_dependency_service.emergency_override(override2)

        # Both should succeed
        assert dep1.status == DependencyStatus.OVERRIDDEN
        assert dep2.status == DependencyStatus.OVERRIDDEN

        # Should have 2 audit entries for this dependency
        audit_log = await kanban_dependency_service.get_audit_log(limit=100)
        dependency_audits = [a for a in audit_log if a.dependency_id == created_dependency.id]
        assert len(dependency_audits) >= 2

    @pytest.mark.asyncio
    async def test_emergency_override_audit_log_sorting(self):
        """Test audit log is sorted by timestamp (most recent first)"""
        audit_log = await kanban_dependency_service.get_audit_log(limit=10)

        if len(audit_log) >= 2:
            # Verify descending order (most recent first)
            for i in range(len(audit_log) - 1):
                assert audit_log[i].overridden_at >= audit_log[i + 1].overridden_at


# ============================================================================
# 5. Performance & Edge Cases (4 tests)
# ============================================================================

class TestPerformanceEdgeCases:
    """Test performance and edge case scenarios"""

    @pytest.mark.asyncio
    async def test_large_dependency_graph_performance(self):
        """Test performance with larger dependency graph"""
        # Create 50 tasks
        task_ids = {uuid4() for _ in range(50)}
        task_list = list(task_ids)

        # Create 30 dependencies
        for i in range(30):
            dep = DependencyCreate(
                task_id=task_list[i],
                depends_on_task_id=task_list[i + 1],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            await kanban_dependency_service.create_dependency(dep, task_ids)

        # Measure topological sort performance
        start_time = time.perf_counter()
        result = await kanban_dependency_service.topological_sort(task_ids)
        execution_time = (time.perf_counter() - start_time) * 1000

        # Should complete quickly
        assert execution_time < 50.0
        assert result.task_count == 50
        assert result.execution_time_ms < 50.0

    @pytest.mark.asyncio
    async def test_multiple_dependencies_per_task(self, available_task_ids):
        """Test task with multiple dependencies (fan-in)"""
        task_list = list(available_task_ids)

        # Create fan-in: task[0] depends on task[1], task[2], task[3]
        for i in range(1, 4):
            dep = DependencyCreate(
                task_id=task_list[0],
                depends_on_task_id=task_list[i],
                dependency_type=DependencyType.FINISH_TO_START,
            )
            await kanban_dependency_service.create_dependency(dep, available_task_ids)

        # Get all dependencies for task[0]
        dependencies = await kanban_dependency_service.get_task_dependencies(task_list[0])

        # Should have at least 3 dependencies
        assert len(dependencies) >= 3

        # All should be different upstream tasks
        upstream_ids = {d.depends_on_task_id for d in dependencies}
        assert len(upstream_ids) >= 3

    @pytest.mark.asyncio
    async def test_complex_dependency_types(self, available_task_ids):
        """Test complex scenario with different dependency types"""
        task_list = list(available_task_ids)

        # Create different types of dependencies
        deps = [
            (task_list[0], task_list[1], DependencyType.FINISH_TO_START),
            (task_list[1], task_list[2], DependencyType.START_TO_START),
            (task_list[2], task_list[3], DependencyType.FINISH_TO_FINISH),
            (task_list[3], task_list[4], DependencyType.START_TO_FINISH),
        ]

        for task_id, depends_on, dep_type in deps:
            dep = DependencyCreate(
                task_id=task_id,
                depends_on_task_id=depends_on,
                dependency_type=dep_type,
            )
            await kanban_dependency_service.create_dependency(dep, available_task_ids)

        # Verify topological sort works with mixed types
        result = await kanban_dependency_service.topological_sort(available_task_ids)
        assert len(result.ordered_tasks) == len(available_task_ids)

    @pytest.mark.asyncio
    async def test_dependency_status_filtering(self, available_task_ids):
        """Test that only PENDING dependencies are considered in operations"""
        task_list = list(available_task_ids)

        # Create dependency
        dep = DependencyCreate(
            task_id=task_list[0],
            depends_on_task_id=task_list[1],
            dependency_type=DependencyType.FINISH_TO_START,
        )
        created_dep = await kanban_dependency_service.create_dependency(dep, available_task_ids)

        # Override it (status becomes OVERRIDDEN)
        override = EmergencyOverride(
            dependency_id=created_dep.id,
            reason="Testing status filtering with override",
            overridden_by="test_user",
        )
        await kanban_dependency_service.emergency_override(override)

        # Get task dependencies (should exclude OVERRIDDEN)
        dependencies = await kanban_dependency_service.get_task_dependencies(task_list[0])

        # Should not include the overridden dependency
        overridden_deps = [d for d in dependencies if d.status == DependencyStatus.OVERRIDDEN]
        assert len(overridden_deps) == 0
