"""
Tests for the memory module.
"""

import pytest
import tempfile
import os
import gc

# Import using the correct path for the test environment
from core.memory import MemoryGraph, MemoryStore
from core.memory.models import Task, TaskStatus, RelationshipType
from core.memory.ids import generate_task_id


class TestMemoryStore:
    """Test MemoryStore functionality."""
    
    def test_create_and_get_task(self):
        """Test creating and retrieving a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(os.path.join(tmpdir, "test.db"))
            
            task = Task(
                id=generate_task_id(),
                title="Test Task",
                description="Test Description",
                priority=2,
            )
            created = store.create_task(task, actor="test")
            
            retrieved = store.get_task(created.id)
            assert retrieved is not None
            assert retrieved.title == "Test Task"
            assert retrieved.description == "Test Description"
            assert retrieved.priority == 2
            assert retrieved.status == TaskStatus.OPEN
            
            store.close()
            gc.collect()
    
    def test_update_task(self):
        """Test updating a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(os.path.join(tmpdir, "test.db"))
            
            task = Task(id=generate_task_id(), title="Original")
            created = store.create_task(task, actor="test")
            created.title = "Updated"
            updated = store.update_task(created, actor="test")
            
            assert updated.title == "Updated"
            store.close()
            gc.collect()
    
    def test_list_tasks(self):
        """Test listing tasks with filters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(os.path.join(tmpdir, "test.db"))
            
            t1 = Task(id=generate_task_id(), title="Task 1", priority=0)
            t2 = Task(id=generate_task_id(), title="Task 2", priority=2)
            t3 = Task(id=generate_task_id(), title="Task 3", priority=2)
            
            store.create_task(t1, actor="test")
            store.create_task(t2, actor="test")
            store.create_task(t3, actor="test")
            
            all_tasks = store.list_tasks()
            assert len(all_tasks) == 3
            
            p0_tasks = store.list_tasks(priority=0)
            assert len(p0_tasks) == 1
            store.close()
            gc.collect()


class TestMemoryGraph:
    """Test MemoryGraph functionality."""
    
    def test_create_task_with_graph(self):
        """Test creating a task through the graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(os.path.join(tmpdir, "test.db"))
            graph = MemoryGraph(store)
            
            task = graph.create_task(
                title="Graph Task",
                description="Test",
                priority=1,
                actor="test",
            )
            
            assert task is not None
            assert task.title == "Graph Task"
            store.close()
            gc.collect()
    
    def test_claim_task(self):
        """Test claiming a task."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(os.path.join(tmpdir, "test.db"))
            graph = MemoryGraph(store)
            
            task = graph.create_task(title="Claim Me", actor="test")
            claimed = graph.claim_task(task.id, "user1", actor="test")
            
            assert claimed is not None
            assert claimed.assignee == "user1"
            assert claimed.status == TaskStatus.IN_PROGRESS
            store.close()
            gc.collect()


class TestTaskIDs:
    """Test task ID generation."""
    
    def test_unique_ids(self):
        """Test that generated IDs are unique."""
        ids = set()
        for _ in range(100):
            task_id = generate_task_id()
            ids.add(task_id)
        
        assert len(ids) == 100
    
    def test_parent_based_ids(self):
        """Test that parent-based IDs include parent prefix."""
        parent_id = generate_task_id()
        child_id = generate_task_id(parent_id=parent_id)
        
        assert child_id.startswith(parent_id[:8])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
