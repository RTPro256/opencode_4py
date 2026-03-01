# Memory Integration Plan

> **Purpose**: Detailed integration plan for merging beads into opencode_4py

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles
> - [MERGE_INTEGRATION_PLAN.md](MERGE_INTEGRATION_PLAN.md) - General merge integration plan
> - [MERGE_PROJECTS_INVENTORY.md](MERGE_PROJECTS_INVENTORY.md) - Project inventory

---

## Overview

This plan outlines the systematic integration of beads' memory management capabilities into opencode_4py. beads provides persistent, structured memory for coding agents through a dependency-aware graph backed by Dolt (version-controlled SQL database).

---

## Project Summary

**Source**: `merge_projects/beads/`
**Language**: Go
**Target**: Python (opencode_4py)

### Key Capabilities

1. **Task dependency graph**: Track task dependencies with zero-conflict hash IDs
2. **Version-controlled memory**: Dolt-backed SQL database with cell-level merge
3. **Memory compaction**: Semantic "memory decay" to summarize old tasks
4. **Graph links**: relates_to, duplicates, supersedes, replies_to relationships
5. **Hierarchical tasks**: Epic → Task → Sub-task structure

---

## Integration Architecture

### Target Module Structure

```
src/opencode/core/memory/
├── __init__.py
├── graph.py            # Task dependency graph
├── store.py           # SQLite/Dolt-backed storage
├── models.py          # Task, Issue, Message models
├── compaction.py      # Memory decay/summarization
├── tracker.py         # Issue tracking
├── links.py           # Graph relationship management
├── ids.py             # Zero-conflict hash ID generation
├── queries.py         # Query builders
└── config.py          # Memory configuration
```

### CLI Commands Structure

```
src/opencode/cli/commands/
├── __init__.py
├── memory/
│   ├── __init__.py
│   ├── task.py        # Task management commands
│   ├── dep.py         # Dependency commands
│   ├── graph.py       # Graph relationship commands
│   ├── compact.py     # Memory compaction
│   └── export.py      # Export commands
```

---

## Integration Steps

### Phase 1: Core Data Structures (Week 1)

#### 1.1 Models
- [ ] Create task/issue models with hash-based IDs
- [ ] Implement message models
- [ ] Define relationship types
- [ ] Add audit trail support

#### 1.2 ID Generation
- [ ] Implement zero-conflict hash ID generation (`bd-a1b2`)
- [ ] Add hierarchical ID support (Epic → Task → Sub-task)
- [ ] Implement ID parsing

#### 1.3 Storage Layer
- [ ] Create SQLite-backed storage (fallback from Dolt)
- [ ] Implement schema migrations
- [ ] Add transaction support

---

### Phase 2: Task Graph (Week 2)

#### 2.1 Graph Operations
- [ ] Implement task creation/reading/updating/deletion
- [ ] Add dependency management
- [ ] Implement graph traversal
- [ ] Add ready-task detection (tasks with no open blockers)

#### 2.2 Query API
- [ ] Implement filtering and sorting
- [ ] Add priority-based queries
- [ ] Implement date-based queries
- [ ] Add full-text search

---

### Phase 3: Relationships (Week 3)

#### 3.1 Link Types
- [ ] Implement `relates_to` relationship
- [ ] Implement `duplicates` relationship
- [ ] Implement `supersedes` relationship
- [ ] Implement `replies_to` relationship

#### 3.2 Graph Queries
- [ ] Implement relationship traversal
- [ ] Add cycle detection
- [ ] Implement reverse lookups

---

### Phase 4: Memory Features (Week 4)

#### 4.1 Memory Compaction
- [ ] Implement semantic memory decay
- [ ] Add task summarization
- [ ] Implement context window optimization
- [ ] Add compaction scheduling

#### 4.2 Export/Import
- [ ] Implement JSON export
- [ ] Implement JSON import
- [ ] Add format conversion

---

### Phase 5: CLI Commands (Week 5)

#### 5.1 Task Commands
- [ ] Implement `opencode task create "Title" -p 0`
- [ ] Implement `opencode task ready` - List unblocked tasks
- [ ] Implement `opencode task show <id>`
- [ ] Implement `opencode task list` with filters
- [ ] Implement `opencode task update --claim`
- [ ] Implement `opencode task close <id>`

#### 5.2 Dependency Commands
- [ ] Implement `opencode dep add <child> <parent>`
- [ ] Implement `opencode dep list <id>`
- [ ] Implement dependency visualization

#### 5.3 Graph Commands
- [ ] Implement `opencode graph relate <id1> <id2>`
- [ ] Implement `opencode graph duplicate <id1> <id2>`
- [ ] Implement `opencode graph supersede <old> <new>`

#### 5.4 Memory Commands
- [ ] Implement `opencode memory compact`
- [ ] Implement `opencode memory export`

---

### Phase 6: Advanced Features (Week 6)

#### 6.1 Multi-Agent Support
- [ ] Add contributor namespace isolation
- [ ] Implement maintainer workflow
- [ ] Add remote synchronization

#### 6.2 Backend Options
- [ ] Implement SQLite backend (default)
- [ ] Add Dolt backend (optional)
- [ ] Implement backend abstraction

---

## Data Models

### Task Model

```python
class Task:
    id: str           # Hash-based ID (e.g., "bd-a1b2")
    title: str        # Task title
    description: str  # Task description
    status: TaskStatus  # open, in_progress, closed
    priority: int     # P0-P4
    assignee: str     # Assigned agent/user
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
```

### Relationship Types

```python
class RelationshipType(Enum):
    BLOCKS = "blocks"
    RELATED = "relates_to"
    PARENT = "parent"
    DUPLICATES = "duplicates"
    SUPERSEDES = "supersedes"
    REPLIES_TO = "replies_to"
```

---

## Key Features to Implement

### 1. Zero-Conflict IDs
- Hash-based IDs prevent merge collisions
- Format: `bd-a1b2`, `bd-a3f8.1`, `bd-a3f8.1.1`
- Supports hierarchical IDs for epics

### 2. Ready Task Detection
```python
def get_ready_tasks():
    """Return tasks with no open blockers."""
    # Tasks where all BLOCKS dependencies are closed
```

### 3. Memory Compaction
```python
def compact_memory(max_context: int):
    """Summarize old closed tasks to save context."""
    # - Extract key information
    # - Create summary
    # - Archive original
```

### 4. Graph Links
- **relates_to**: General relationship
- **duplicates**: Duplicate tasks
- **supersedes**: Replacement tasks
- **replies_to**: Threaded discussions

---

## Testing Strategy

### Unit Tests
- [ ] Test ID generation
- [ ] Test graph operations
- [ ] Test compaction
- [ ] Test relationships

### Integration Tests
- [ ] Test CLI commands
- [ ] Test persistence
- [ ] Test multi-agent scenarios

---

## Success Criteria

1. ✅ All CLI commands implemented
2. ✅ Task graph fully functional
3. ✅ Memory compaction working
4. ✅ Zero-conflict IDs working
5. ✅ Test coverage > 80%

---

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Data Structures | Week 1 | Models, IDs, storage |
| Phase 2: Task Graph | Week 2 | Graph operations, queries |
| Phase 3: Relationships | Week 3 | Link types, traversal |
| Phase 4: Memory | Week 4 | Compaction, export |
| Phase 5: CLI | Week 5 | All commands |
| Phase 6: Advanced | Week 6 | Multi-agent, backends |

**Total Estimated Time**: 6 weeks

---

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|-------------|
| Go → Python porting | High | Extract patterns, reimplement |
| Dolt dependency | Medium | Use SQLite fallback |
| Complexity of graph | Medium | Incremental implementation |

---

## Optional: Dolt Backend

If Dolt integration is desired later:

```python
# Dolt backend (optional)
class DoltBackend(StorageBackend):
    def __init__(self, data_dir: str = ".beads/dolt"):
        # Dolt-specific implementation
    
    def commit(self, message: str):
        # Dolt commit
    
    def push(self, remote: str):
        # Dolt push
    
    def pull(self, remote: str):
        # Dolt pull
```

---

*Last updated: 2026-03-01*
