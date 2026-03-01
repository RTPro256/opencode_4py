"""
Graph operations for the memory module.

Based on beads (https://github.com/steveyegge/beads)
"""

from typing import List, Optional, Set
from .models import Task, TaskStatus, TaskRelationship, RelationshipType, Message
from .store import MemoryStore
from .ids import generate_task_id, generate_relationship_id


class MemoryGraph:
    """
    Graph-based memory management for tasks.
    
    Provides high-level operations for task dependencies and relationships.
    """
    
    def __init__(self, store: MemoryStore):
        """
        Initialize the memory graph.
        
        Args:
            store: The underlying storage backend
        """
        self.store = store
    
    # Task operations
    
    def create_task(
        self,
        title: str,
        description: str = "",
        priority: int = 2,
        parent_id: Optional[str] = None,
        actor: str = "system",
    ) -> Task:
        """
        Create a new task.
        
        Args:
            title: Task title
            description: Task description
            priority: Priority (0=P0 highest, 4=P4 lowest)
            parent_id: Parent task ID for hierarchical tasks
            actor: Who is creating the task
        
        Returns:
            The created task
        """
        task_id = generate_task_id(parent_id=parent_id)
        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            parent_id=parent_id,
        )
        return self.store.create_task(task, actor)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.store.get_task(task_id)
    
    def update_task(self, task: Task, actor: str = "system") -> Task:
        """Update an existing task."""
        return self.store.update_task(task, actor)
    
    def close_task(self, task_id: str, actor: str = "system") -> Optional[Task]:
        """
        Close a task.
        
        Args:
            task_id: Task ID to close
            actor: Who is closing the task
        
        Returns:
            The closed task, or None if not found
        """
        task = self.store.get_task(task_id)
        if task is None:
            return None
        
        task.status = TaskStatus.CLOSED
        return self.store.update_task(task, actor)
    
    def claim_task(self, task_id: str, assignee: str, actor: str = "system") -> Optional[Task]:
        """
        Atomically claim a task (set assignee and in_progress status).
        
        Args:
            task_id: Task ID to claim
            assignee: Who is claiming the task
            actor: Who is performing the claim
        
        Returns:
            The claimed task, or None if not found
        """
        task = self.store.get_task(task_id)
        if task is None:
            return None
        
        task.assignee = assignee
        task.status = TaskStatus.IN_PROGRESS
        return self.store.update_task(task, actor)
    
    def delete_task(self, task_id: str, actor: str = "system") -> bool:
        """Delete a task and all its relationships."""
        return self.store.delete_task(task_id, actor)
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        priority: Optional[int] = None,
        assignee: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> List[Task]:
        """List tasks with optional filters."""
        return self.store.list_tasks(status, priority, assignee, parent_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """
        Get tasks with no open blockers.
        
        A task is ready if all tasks that block it are closed.
        """
        return self.store.get_ready_tasks()
    
    # Relationship operations
    
    def add_dependency(
        self,
        child_id: str,
        parent_id: str,
        actor: str = "system",
    ) -> TaskRelationship:
        """
        Add a BLOCKS dependency relationship.
        
        Child task cannot be worked on until parent is closed.
        
        Args:
            child_id: The task being blocked
            parent_id: The blocking task
            actor: Who is adding the dependency
        
        Returns:
            The created relationship
        """
        rel_id = generate_relationship_id(child_id, parent_id, "blocks")
        rel = TaskRelationship(
            id=rel_id,
            source_id=child_id,
            target_id=parent_id,
            relationship_type=RelationshipType.BLOCKS,
        )
        return self.store.add_relationship(rel)
    
    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: RelationshipType,
        actor: str = "system",
    ) -> TaskRelationship:
        """
        Add a relationship between tasks.
        
        Args:
            source_id: Source task ID
            target_id: Target task ID
            rel_type: Type of relationship
            actor: Who is adding the relationship
        
        Returns:
            The created relationship
        """
        rel_id = generate_relationship_id(source_id, target_id, rel_type.value)
        rel = TaskRelationship(
            id=rel_id,
            source_id=source_id,
            target_id=target_id,
            relationship_type=rel_type,
        )
        return self.store.add_relationship(rel)
    
    def get_blockers(self, task_id: str) -> List[Task]:
        """
        Get all tasks that block the given task.
        
        Args:
            task_id: Task ID to get blockers for
        
        Returns:
            List of blocking tasks
        """
        relationships = self.store.get_relationships(task_id)
        blockers = []
        
        for rel in relationships:
            if rel.relationship_type == RelationshipType.BLOCKS and rel.source_id == task_id:
                blocker = self.store.get_task(rel.target_id)
                if blocker:
                    blockers.append(blocker)
        
        return blockers
    
    def get_blocked_tasks(self, task_id: str) -> List[Task]:
        """
        Get all tasks that are blocked by the given task.
        
        Args:
            task_id: Task ID to get blocked tasks for
        
        Returns:
            List of blocked tasks
        """
        relationships = self.store.get_relationships(task_id)
        blocked = []
        
        for rel in relationships:
            if rel.relationship_type == RelationshipType.BLOCKS and rel.target_id == task_id:
                blocked_task = self.store.get_task(rel.source_id)
                if blocked_task:
                    blocked.append(blocked_task)
        
        return blocked
    
    def is_ready(self, task_id: str) -> bool:
        """
        Check if a task is ready to work on.
        
        A task is ready if all blocking tasks are closed.
        
        Args:
            task_id: Task ID to check
        
        Returns:
            True if task is ready
        """
        blockers = self.get_blockers(task_id)
        return all(blocker.status == TaskStatus.CLOSED for blocker in blockers)
    
    def remove_relationship(self, rel_id: str) -> bool:
        """Remove a relationship."""
        return self.store.remove_relationship(rel_id)
    
    def remove_dependency(self, child_id: str, parent_id: str) -> bool:
        """
        Remove a BLOCKS dependency relationship.
        
        Args:
            child_id: The task that was being blocked
            parent_id: The blocking task
        
        Returns:
            True if removed, False if not found
        """
        relationships = self.store.get_relationships(child_id)
        
        for rel in relationships:
            if (rel.relationship_type == RelationshipType.BLOCKS and 
                rel.source_id == child_id and rel.target_id == parent_id):
                return self.store.remove_relationship(rel.id)
        
        return False
    
    def get_parents(self, task_id: str) -> List[Task]:
        """
        Get all parent tasks (tasks that this task blocks).
        
        Args:
            task_id: Task ID to get parents for
        
        Returns:
            List of parent tasks
        """
        return self.get_blockers(task_id)
    
    def detect_cycles(self) -> List[List[str]]:
        """
        Detect cycles in the dependency graph.
        
        Returns:
            List of cycles, where each cycle is a list of task IDs
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(task_id: str, path: List[str]) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            path.append(task_id)
            
            # Get all blocked tasks (outgoing edges)
            relationships = self.store.get_relationships(task_id)
            
            for rel in relationships:
                if rel.relationship_type == RelationshipType.BLOCKS:
                    blocked_task_id = rel.target_id
                    
                    if blocked_task_id not in visited:
                        if dfs(blocked_task_id, path.copy()):
                            return True
                    elif blocked_task_id in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(blocked_task_id)
                        cycle = path[cycle_start:] + [blocked_task_id]
                        cycles.append(cycle)
            
            rec_stack.remove(task_id)
            return False
        
        # Get all tasks
        all_tasks = self.store.list_tasks()
        
        for task in all_tasks:
            if task.id not in visited:
                dfs(task.id, [])
        
        return cycles
    
    # Message operations
    
    def add_message(
        self,
        task_id: str,
        author: str,
        content: str,
        message_type: str = "comment",
        priority: str = "normal",
        reply_to: Optional[str] = None,
    ):
        """Add a message to a task."""
        import uuid
        message = Message(
            id=str(uuid.uuid4()),
            task_id=task_id,
            author=author,
            content=content,
            message_type=message_type,
            priority=priority,
            reply_to=reply_to,
        )
        return self.store.add_message(message)
    
    def get_messages(self, task_id: str):
        """Get all messages for a task."""
        return self.store.get_messages(task_id)
    
    # Audit
    
    def get_audit_trail(self, task_id: str):
        """Get audit trail for a task."""
        return self.store.get_audit_trail(task_id)
    
    # Hierarchy
    
    def get_children(self, parent_id: str) -> List[Task]:
        """Get all direct children of a task."""
        return self.store.list_tasks(parent_id=parent_id)
    
    def get_descendants(self, parent_id: str) -> List[Task]:
        """
        Get all descendants of a task (recursive).
        
        Args:
            parent_id: Parent task ID
        
        Returns:
            List of all descendant tasks
        """
        descendants = []
        children = self.store.list_tasks(parent_id=parent_id)
        
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_descendants(child.id))
        
        return descendants
    
    def get_epic_tree(self, task_id: str) -> dict:
        """
        Get the full epic tree for a task.
        
        Args:
            task_id: Task ID to get tree for
        
        Returns:
            Dictionary representing the tree structure
        """
        task = self.store.get_task(task_id)
        if task is None:
            return {}
        
        def build_tree(t: Task) -> dict:
            children = self.store.list_tasks(parent_id=t.id)
            return {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority,
                "children": [build_tree(c) for c in children],
            }
        
        return build_tree(task)
