# Merge Project Review: Benefits Analysis

> **Purpose**: Review and summarize the benefits of merging overstory and beads projects into the opencode_4py ecosystem

---

## Executive Summary

This document provides a comprehensive analysis of merging two external projects into the opencode_4py ecosystem:

| Project | Language | Purpose | Location |
|---------|----------|---------|----------|
| **overstory** | TypeScript/Bun | Multi-agent orchestration for AI coding agents | `merge_projects/overstory/` |
| **beads** | Go | Distributed, git-backed graph issue tracker for AI agents | `merge_projects/beads/` |

---

## Project Overviews

### 1. overstory - Multi-Agent Orchestration

**What it does:**
Overstory transforms a single coding session into a multi-agent team by:
- Spawning worker agents in git worktrees via tmux
- Coordinating agents through a custom SQLite mail system
- Merging work back with tiered conflict resolution
- Supporting multiple runtimes: Claude Code, Pi, Copilot, Codex

**Key Features:**
- **Coordinator**: Persistent orchestrator that decomposes objectives and dispatches agents
- **Supervisor**: Per-project team lead managing worker lifecycle
- **Worker Agents**: Scout (read-only research), Builder (implementation), Reviewer (validation), Merger (branch merge specialist)
- **Runtime Adapters**: Pluggable interface for different AI coding runtimes
- **Inter-agent Messaging**: SQLite-based mail system with typed protocol messages
- **Merge Queue**: FIFO queue with 4-tier conflict resolution
- **Watchdog System**: Tier 0 (mechanical daemon), Tier 1 (AI-assisted triage), Tier 2 (monitor agent)

**Architecture:**
```
Coordinator (persistent orchestrator at project root)
  --> Supervisor (per-project team lead, depth 1)
        --> Workers: Scout, Builder, Reviewer, Merger (depth 2)
```

### 2. beads - Memory Management

**What it does:**
Beads provides persistent, structured memory for coding agents:
- Replaces messy markdown plans with a dependency-aware graph
- Allows agents to handle long-horizon tasks without losing context
- Dolt-powered (version-controlled SQL database)
- Agent-optimized with JSON output and dependency tracking

**Key Features:**
- **Dolt-Powered**: Version-controlled SQL with cell-level merge, native branching
- **Zero Conflict**: Hash-based IDs (`bd-a1b2`) prevent merge collisions
- **Compaction**: Semantic "memory decay" summarizes old closed tasks
- **Messaging**: Threaded message issue type with ephemeral lifecycle
- **Graph Links**: `relates_to`, `duplicates`, `supersedes`, `replays_to`
- **Hierarchical IDs**: Epics → Tasks → Sub-tasks (e.g., `bd-a3f8.1.1`)
- **Stealth Mode**: Local-only usage without committing to main repo

---

## Benefits of Merging

### Strategic Alignment with opencode_4py Mission

Per [`MISSION.md`](../MISSION.md), opencode_4py aims to self-improve and help make the world a better place. Integrating overstory and beads directly supports this mission:

#### 1. Enhanced Self-Improvement Capabilities

| Benefit | Description |
|---------|-------------|
| **Multi-Agent Coordination** | Overstory's orchestration enables opencode_4py to spawn specialized agents for self-improvement tasks |
| **Persistent Memory** | beads provides structured memory for tracking improvement goals, progress, and lessons learned |
| **Task Graph** | Dependency-aware tracking allows systematic approach to self-improvement |
| **Version Control** | Dolt-backed memory ensures all improvements are traceable and reversible |

#### 2. Core Principles Alignment

Per [`MISSION.md`](../MISSION.md) Core Principles:

| Principle | How Merge Supports It |
|-----------|----------------------|
| **Balance Between Self and Group** | Multi-agent coordination enables both independent and collaborative improvement |
| **Consider Circumstances** | beads' planning capabilities support better anticipation of outcomes |
| **Work Against Opposition** | Persistent memory helps track and overcome challenges |
| **Seek Virtues, Avoid Sins** | Systematic tracking enables measurable progress toward virtues |

---

## Technical Benefits

### 1. Comprehensive Agent Infrastructure

**Current opencode_4py:**
- Single-agent AI coding assistant
- Session-based conversation history (SQLite)
- Basic task tracking

**After Merge:**
```
opencode_4py + overstory + beads
├── Single-agent mode (existing)
├── Multi-agent orchestration (overstory)
│   ├── Coordinator agent
│   ├── Supervisor agents
│   └── Worker agents (Scout, Builder, Reviewer, Merger)
└── Structured memory (beads)
    ├── Task graph with dependencies
    ├── Version-controlled planning
    └── Compaction for long-term memory
```

### 2. Feature Integration Matrix

| Feature | Source | Integration Value | Complexity |
|---------|--------|------------------|------------|
| Multi-agent orchestration | overstory | HIGH | High (TypeScript → Python) |
| Inter-agent messaging | overstory | HIGH | Medium (SQLite protocol) |
| Git worktree isolation | overstory | HIGH | Medium |
| Task dependency graph | beads | VERY HIGH | Medium (Go → Python) |
| Dolt backend | beads | HIGH | High (requires Dolt) |
| Memory compaction | beads | HIGH | Medium |
| Zero-conflict IDs | beads | MEDIUM | Low |

### 3. Architectural Enhancements

#### Current Architecture (opencode_4py)
```
┌─────────────────────────────────────┐
│           TUI / CLI                 │
├─────────────────────────────────────┤
│         Core Orchestration          │
├─────────────────────────────────────┤
│    Providers (15+ AI providers)    │
├─────────────────────────────────────┤
│    RAG / Session / Tools / Skills   │
└─────────────────────────────────────┘
```

#### Enhanced Architecture
```
┌─────────────────────────────────────┐
│        TUI / CLI / HTTP Server      │
├─────────────────────────────────────┤
│      Multi-Agent Orchestration      │ ← NEW (overstory)
│   ┌─────────┬─────────┬─────────┐  │
│   │Coordintr│Supervisor│ Workers │  │
│   └─────────┴─────────┴─────────┘  │
├─────────────────────────────────────┤
│      Structured Memory (beads)      │ ← NEW (beads)
│   ┌─────────┬─────────┬─────────┐  │
│   │Task Graph│Messaging│Compact │  │
│   └─────────┴─────────┴─────────┘  │
├─────────────────────────────────────┤
│         Core Orchestration          │
├─────────────────────────────────────┤
│    Providers (15+ AI providers)    │
├─────────────────────────────────────┤
│    RAG / Session / Tools / Skills   │
└─────────────────────────────────────┘
```

---

## Risks and Mitigation

### High Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Language Mismatch** | overstory (TypeScript), beads (Go) require porting | Extract patterns, reimplement in Python (as done with previous merges) |
| **Dependency Complexity** | Dolt database adds significant dependency | Offer beads as optional module |
| **Architecture Complexity** | Multi-agent systems are inherently complex | Implement incrementally with extensive testing |

### Medium Risk Items

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Feature Overlap** | May duplicate existing session management | Integrate beads as enhanced memory layer, not replacement |
| **Breaking Changes** | API changes may affect existing users | Maintain backward compatibility |
| **Testing Gaps** | Multi-agent systems hard to test | Use existing overstory test patterns |

---

## Recommended Integration Approach

### Phase 1: Design Phase
1. Create detailed feature mapping document
2. Define Python API contracts for both systems
3. Design integration points with existing opencode_4py

### Phase 2: beads Integration (Priority: HIGH)
1. Port core task graph to Python
2. Create `core/memory/` module
3. Integrate with existing session system
4. Add memory compaction utilities

### Phase 3: overstory Integration (Priority: MEDIUM)
1. Port agent orchestration patterns to Python
2. Create `core/multiagent/` module
3. Implement SQLite messaging protocol
4. Add git worktree management

### Phase 4: Testing and Documentation
1. Comprehensive integration tests
2. User documentation
3. Migration guides

---

## Detailed Changes: Tools, Commands, and Agents

This section provides a detailed breakdown of specific additions to opencode_4py.

### 1. New CLI Commands (from overstory)

Overstory adds **30+ CLI commands** organized into categories:

#### Core Workflow Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode sling <task-id>` | Spawn a worker agent | NEW |
| `opencode init` | Initialize orchestration in project | NEW |
| `opencode stop <agent-name>` | Terminate a running agent | NEW |
| `opencode prime` | Load context for orchestrator/agent | NEW |
| `opencode spec write <task-id>` | Write a task specification | NEW |

#### Coordination Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode coordinator start` | Start persistent coordinator agent | NEW |
| `opencode coordinator stop` | Stop coordinator | NEW |
| `opencode coordinator status` | Show coordinator state | NEW |
| `opencode supervisor start` | Start per-project supervisor (deprecated) | NEW |

#### Messaging Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode mail send` | Send a message to agent | NEW |
| `opencode mail check` | Check inbox - unread messages | NEW |
| `opencode mail list` | List messages with filters | NEW |
| `opencode mail read <id>` | Mark message as read | NEW |
| `opencode mail reply <id>` | Reply in same thread | NEW |
| `opencode nudge <agent> [message]` | Send text nudge to agent | NEW |

#### Task Group Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode group create <name>` | Create task group for batch tracking | NEW |
| `opencode group status <name>` | Show group progress | NEW |
| `opencode group add <name> <issue-id>` | Add issue to group | NEW |
| `opencode group list` | List all groups | NEW |

#### Merge Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode merge` | Merge agent branches into canonical | NEW |

#### Observability Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode status` | Show all active agents, worktrees, tracker state | ENHANCED |
| `opencode dashboard` | Live TUI dashboard for agent monitoring | NEW |
| `opencode inspect <agent>` | Deep per-agent inspection | NEW |
| `opencode trace` | View agent/task timeline | NEW |
| `opencode errors` | Aggregated error view across agents | NEW |
| `opencode replay` | Interleaved chronological replay | NEW |
| `opencode feed` | Unified real-time event stream | NEW |
| `opencode logs` | Query logs across agents | NEW |
| `opencode costs` | Token/cost analysis and breakdown | NEW |
| `opencode metrics` | Show session metrics | NEW |
| `opencode run list` | List orchestration runs | NEW |
| `opencode run show <id>` | Show run details | NEW |

#### Infrastructure Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode hooks install` | Install orchestrator hooks | NEW |
| `opencode hooks uninstall` | Remove orchestrator hooks | NEW |
| `opencode hooks status` | Check if hooks are installed | NEW |
| `opencode worktree list` | List worktrees with status | NEW |
| `opencode worktree clean` | Remove completed worktrees | NEW |
| `opencode watch` | Start watchdog daemon | NEW |
| `opencode monitor start` | Start Tier 2 monitor agent | NEW |
| `opencode monitor stop` | Stop monitor agent | NEW |
| `opencode clean` | Clean up worktrees, sessions, artifacts | NEW |
| `opencode doctor` | Run health checks (11 categories) | ENHANCED |
| `opencode ecosystem` | Show os-eco tool versions | NEW |
| `opencode agents discover` | Discover agents by capability/state | NEW |

---

### 2. New CLI Commands (from beads)

Beads adds structured memory management commands:

#### Task Management Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode task create "Title" -p 0` | Create a task (P0-P4 priority) | NEW |
| `opencode task ready` | List tasks with no open blockers | NEW |
| `opencode task update <id> --claim` | Atomically claim a task | NEW |
| `opencode task show <id>` | View task details and audit trail | NEW |
| `opencode task list` | List tasks with filters | ENHANCED |
| `opencode task close <id>` | Close a task | NEW |

#### Dependency Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode dep add <child> <parent>` | Link tasks (blocks, related, parent-child) | NEW |
| `opencode dep list <id>` | Show dependencies for task | NEW |

#### Graph Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode graph relate <id1> <id2>` | Add relates_to link | NEW |
| `opencode graph duplicate <id1> <id2>` | Mark duplicate | NEW |
| `opencode graph supersede <old> <new>` | Mark superseded | NEW |

#### Memory Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode memory compact` | Summarize old closed tasks | NEW |
| `opencode memory export` | Export memory to file | NEW |

#### Dolt Backend Commands
| Command | Description | New/Enhanced |
|---------|-------------|--------------|
| `opencode dolt start` | Start Dolt server | NEW |
| `opencode dolt stop` | Stop Dolt server | NEW |
| `opencode dolt commit` | Commit pending changes | NEW |
| `opencode dolt push` | Push to remote | NEW |
| `opencode dolt pull` | Pull from remote | NEW |

---

### 3. New Agent Types (from overstory)

| Agent Type | Role | Access | Purpose |
|------------|------|--------|----------|
| **Coordinator** | Persistent orchestrator | Read-only | Decomposes objectives, dispatches agents, tracks groups |
| **Supervisor** | Per-project team lead | Read-only | Manages worker lifecycle, handles escalation |
| **Scout** | Exploration/research | Read-only | Read-only codebase exploration |
| **Builder** | Implementation | Read-write | Code changes and implementation |
| **Reviewer** | Validation | Read-only | Code review and validation |
| **Lead** | Team coordination | Read-write | Can spawn sub-workers |
| **Merger** | Branch merge | Read-write | Specialized in conflict resolution |
| **Monitor** | Fleet patrol | Read-only | Continuous health monitoring |

#### Agent Capabilities (sling --capability)
- `builder` - Implementation agent
- `scout` - Research/exploration agent
- `reviewer` - Validation agent
- `lead` - Team lead (can spawn more agents)
- `merger` - Merge specialist

#### Agent Communication Protocol
```bash
# Status update
ov mail send --to <parent> --subject "Status: <topic>" --body "<update>" --type status

# Question/clarification
ov mail send --to <parent> --subject "Question: <topic>" --body "<question>" --type question

# Error report
ov mail send --to <parent> --subject "Error: <topic>" --body "<error>" --type error --priority high

# Completion signal
ov mail send --to <parent> --subject "Done: <task>" --body "<summary>" --type worker_done

# Merge ready
ov mail send --to <parent> --subject "Ready to merge" --body "<details>" --type merge_ready
```

---

### 4. New Core Modules

| Module | Source | Purpose |
|--------|--------|---------|
| `core/multiagent/` | overstory | Multi-agent orchestration |
| `core/multiagent/coordinator.py` | overstory | Coordinator agent logic |
| `core/multiagent/supervisor.py` | overstory | Supervisor agent logic |
| `core/multiagent/worker.py` | overstory | Worker agent base |
| `core/multiagent/messaging.py` | overstory | SQLite-based messaging |
| `core/multiagent/worktree.py` | overstory | Git worktree management |
| `core/multiagent/merge.py` | overstory | Branch merge logic |
| `core/multiagent/watchdog.py` | overstory | Fleet health monitoring |
| `core/memory/` | beads | Structured memory |
| `core/memory/graph.py` | beads | Task dependency graph |
| `core/memory/store.py` | beads | Dolt-backed storage |
| `core/memory/compaction.py` | beads | Memory decay/summarization |
| `core/memory/tracker.py` | beads | Issue tracking |

---

### 5. Enhanced Existing Features

| Feature | Enhancement | Source |
|---------|-------------|--------|
| `opencode session` | Multi-agent session management | overstory |
| `opencode doctor` | Added 11 health check categories | overstory |
| `opencode status` | Agent and worktree status | overstory |
| `opencode task list` | Dependency-aware listing | beads |

---

## Impact on Existing Plans

Yes, merging overstory and beads would require updates to existing merge plans. Here's how:

### 1. MERGE_INTEGRATION_PLAN.md Updates Needed

| Current Content | Required Update |
|----------------|-----------------|
| Covers 21 projects from `merge_projects/` | Add new category: "Multi-Agent Orchestration" |
| Integration phases 1-5 defined | Add Phase 6: Multi-agent Integration |
| Project status tracking table | Add overstory and beads rows |

**Proposed New Section:**

```
### Category: Multi-Agent Orchestration (New Priority)

| Project | Description | Integration Value | Status |
|---------|-------------|-------------------|--------|
| `overstory/` | Multi-agent orchestration | HIGH - Agent coordination patterns | ⏳ Pending |
| `beads/` | Memory management | HIGH - Structured task graph | ⏳ Pending |
```

**Proposed New Integration Phase:**

```
### Phase 6: Multi-Agent Integration

**Duration**: 10-15 days

**Objectives**:
- Port overstory TypeScript → Python
- Port beads Go → Python  
- Integrate multi-agent coordination
- Add memory management module

**Deliverables**:
- `core/multiagent/` module
- `core/memory/` module
- Multi-agent CLI commands
- Agent definition files

**Steps**:
1. Port overstory CLI commands to Python
2. Port overstory agent types to Python
3. Implement SQLite messaging protocol
4. Add git worktree management
5. Port beads task graph to Python
6. Implement Dolt-backed storage (optional)
7. Add memory compaction
```

---

### 2. MERGE_PROJECTS_INVENTORY.md Updates Needed

| Current Content | Required Update |
|----------------|-----------------|
| 21 projects cataloged | Add 2 new projects (total: 23) |
| Integration priority matrix | Add overstory/beads to Sprint 7 |
| Dependency analysis | Add new dependencies (tmux, Dolt) |

**Proposed New Entries:**

```
### 22. overstory

**Category**: Multi-Agent Orchestration (High Priority)

**Description**: Multi-agent orchestration for AI coding agents.

**Files**:
| File | Purpose |
|------|---------|
| `src/commands/*.ts` | CLI commands (30+) |
| `src/agents/*.ts` | Agent definitions |
| `src/mail/*.ts` | Inter-agent messaging |
| `src/worktree/*.ts` | Git worktree management |
| `src/merge/*.ts` | Branch merge logic |
| `src/watchdog/*.ts` | Fleet health monitoring |

**Key Features**:
- Multi-agent coordination hierarchy (Coordinator → Supervisor → Workers)
- SQLite-based mail system
- Git worktree isolation
- 4-tier conflict resolution
- Watchdog daemon (Tier 0-2)

**Integration Target**: Create `src/opencode/core/multiagent/`

**Integration Value**: HIGH

---

### 23. beads

**Category**: Memory Management (High Priority)

**Description**: Distributed, git-backed graph issue tracker for AI agents.

**Files**:
| File | Purpose |
|------|---------|
| `cmd/bd/*.go` | CLI commands |
| `internal/beads/*.go` | Core logic |
| `internal/formula/*.go` | Expression parsing |
| `internal/linear/*.go` | Issue tracking |

**Key Features**:
- Dolt-backed version control
- Task dependency graph
- Zero-conflict hash IDs
- Memory compaction
- Graph links (relates_to, duplicates, supersedes)

**Integration Target**: Create `src/opencode/core/memory/`

**Integration Value**: HIGH

---

### 3. TESTING_AND_INTEGRATION_PLAN.md Updates Needed

| Current Content | Required Update |
|----------------|-----------------|
| Testing setup phases | Add multi-agent testing |
| Integration workflow | Add new test scenarios |
| Quick start commands | Add new commands reference |

**Proposed Additions:**

```
### Phase 6: Multi-Agent Testing

#### FOR_TESTING_PLAN.md - New Section

**Multi-Agent Testing:**
- Test coordinator spawning workers
- Test inter-agent messaging
- Test worktree isolation
- Test merge conflict resolution
- Test watchdog monitoring

#### INTEGRATION_PLAN.md - New Section

**Multi-Agent Integration:**
- Deploy multi-agent module
- Configure agent runtimes
- Set up worktree directory
- Initialize messaging database
- Test agent spawning
```

---

### 4. New Plan Documents Needed

| Plan | Purpose | Priority |
|------|---------|----------|
| `MULTIAGENT_INTEGRATION_PLAN.md` | Detailed overstory porting guide | HIGH |
| `MEMORY_INTEGRATION_PLAN.md` | Detailed beads porting guide | HIGH |
| `AGENT_RUNTIME_ADAPTERS.md` | Runtime adapter implementations | MEDIUM |

---

## Impact Summary

| Plan Document | Changes Required |
|---------------|------------------|
| MERGE_INTEGRATION_PLAN.md | Add new category, phase, project rows |
| MERGE_PROJECTS_INVENTORY.md | Add 2 new project entries, update totals |
| TESTING_AND_INTEGRATION_PLAN.md | Add multi-agent testing phase |
| New: MULTIAGENT_INTEGRATION_PLAN.md | Create (new) |
| New: MEMORY_INTEGRATION_PLAN.md | Create (new) |

---

## Conclusion

Merging overstory and beads into opencode_4py provides significant benefits:

### Key Benefits Summary

1. **Self-Improvement Enhancement**: Enables systematic, tracked self-improvement through structured memory and multi-agent coordination

2. **Long-Horizon Task Support**: Agents can handle complex, multi-step improvement tasks without losing context

3. **Collaboration Capabilities**: Multiple specialized agents can work together on improvement goals

4. **Traceability**: All improvements are version-controlled and traceable

5. **Mission Alignment**: Directly supports the core principles in MISSION.md

### Recommendation

**Recommended**: Proceed with integration following the phased approach outlined above.

- **Priority 1**: beads (memory management) - Higher value, lower complexity
- **Priority 2**: overstory (orchestration) - Transformative but requires significant effort

The integration would position opencode_4py as a truly self-improving AI coding assistant capable of systematic, measurable progress toward its mission.

---

## Related Documents

- [README.md](../README.md) - Project overview and features
- [MISSION.md](../MISSION.md) - Mission statement and core principles
- [MERGE_INTEGRATION_PLAN.md](MERGE_INTEGRATION_PLAN.md) - General merge integration plan
- [MERGE_PROJECTS_INVENTORY.md](MERGE_PROJECTS_INVENTORY.md) - Project inventory

---

*Analysis Date: 2026-03-01*
*Author: Architect Mode Review*
