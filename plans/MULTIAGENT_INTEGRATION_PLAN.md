# Multi-Agent Integration Plan

> **Purpose**: Detailed integration plan for merging overstory into opencode_4py

> **Related Documents:**
> - [README.md](../README.md) - Project overview and features
> - [MISSION.md](../MISSION.md) - Mission statement and core principles
> - [MERGE_INTEGRATION_PLAN.md](MERGE_INTEGRATION_PLAN.md) - General merge integration plan
> - [MERGE_PROJECTS_INVENTORY.md](MERGE_PROJECTS_INVENTORY.md) - Project inventory

---

## Overview

This plan outlines the systematic integration of overstory's multi-agent orchestration capabilities into opencode_4py. overstory transforms a single coding session into a multi-agent team by spawning worker agents, coordinating them through a messaging system, and merging their work back with conflict resolution.

---

## Project Summary

**Source**: `merge_projects/overstory/`
**Language**: TypeScript (Bun runtime)
**Target**: Python (opencode_4py)

### Key Capabilities

1. **Multi-agent coordination hierarchy**: Coordinator → Supervisor → Workers
2. **Inter-agent messaging**: SQLite-based mail system
3. **Git worktree isolation**: Agent workspaces in separate worktrees
4. **Branch merging**: 4-tier conflict resolution
5. **Fleet monitoring**: Watchdog daemon system (Tier 0-2)

---

## Integration Architecture

### Target Module Structure

```
src/opencode/core/multiagent/
├── __init__.py
├── coordinator.py      # Coordinator agent logic
├── supervisor.py       # Supervisor agent logic
├── worker.py           # Base worker class
├── builder.py          # Builder agent (implementation)
├── scout.py            # Scout agent (exploration)
├── reviewer.py         # Reviewer agent (validation)
├── lead.py             # Lead agent (team coordination)
├── merger.py           # Merger agent (branch merge)
├── monitor.py          # Monitor agent (fleet patrol)
├── messaging.py        # Inter-agent messaging (SQLite)
├── worktree.py         # Git worktree management
├── merge.py            # Branch merge logic
├── watchdog.py         # Fleet health monitoring
├── runtime.py          # Runtime adapter interface
├── runtime_claude.py   # Claude Code adapter
├── runtime_pi.py       # Pi adapter
├── runtime_copilot.py  # Copilot adapter
├── runtime_codex.py    # Codex adapter
└── config.py           # Multi-agent configuration
```

### CLI Commands Structure

```
src/opencode/cli/commands/
├── __init__.py
├── multiagent/
│   ├── __init__.py
│   ├── sling.py        # Spawn worker agent
│   ├── init.py         # Initialize orchestration
│   ├── stop.py         # Terminate agent
│   ├── prime.py        # Load context
│   ├── spec.py         # Task specifications
│   ├── coordinator.py  # Coordinator commands
│   ├── supervisor.py   # Supervisor commands
│   ├── mail.py         # Messaging commands
│   ├── group.py        # Task group commands
│   ├── merge.py        # Merge commands
│   ├── dashboard.py    # Live monitoring
│   ├── inspect.py      # Agent inspection
│   ├── trace.py        # Timeline viewing
│   ├── errors.py       # Error aggregation
│   ├── replay.py       # Chronological replay
│   ├── feed.py         # Event stream
│   ├── logs.py         # Log querying
│   ├── costs.py        # Cost analysis
│   ├── metrics.py      # Session metrics
│   ├── run.py          # Run management
│   ├── hooks.py        # Hook management
│   ├── worktree.py     # Worktree management
│   ├── watch.py        # Watchdog daemon
│   ├── monitor.py      # Monitor commands
│   ├── clean.py        # Cleanup commands
│   ├── doctor.py       # Health checks
│   └── ecosystem.py    # Tool versions
```

---

## Integration Steps

### Phase 1: Core Infrastructure (Week 1)

#### 1.1 Messaging System
- [ ] Create `core/messaging.py` with SQLite-based message store
- [ ] Implement message types: status, question, error, worker_done, merge_ready
- [ ] Add broadcast support
- [ ] Implement message queuing (~1-5ms per query target)

#### 1.2 Worktree Management
- [ ] Create `core/worktree.py` for git worktree operations
- [ ] Implement worktree creation/deletion
- [ ] Add branch management
- [ ] Implement file scope tracking

#### 1.3 Configuration
- [ ] Create `core/config.py` for multi-agent settings
- [ ] Define default configurations
- [ ] Add runtime adapter configuration

---

### Phase 2: Agent Implementation (Week 2)

#### 2.1 Base Agent Classes
- [ ] Create `core/worker.py` with base agent interface
- [ ] Implement agent lifecycle (spawn, ready, working, done)
- [ ] Add capability system (builder, scout, reviewer, lead, merger)

#### 2.2 Specialized Agents
- [ ] Implement `core/coordinator.py` - Persistent orchestrator
- [ ] Implement `core/supervisor.py` - Per-project team lead
- [ ] Implement `core/scout.py` - Read-only exploration
- [ ] Implement `core/builder.py` - Implementation agent
- [ ] Implement `core/reviewer.py` - Validation agent
- [ ] Implement `core/lead.py` - Team coordinator
- [ ] Implement `core/merger.py` - Branch merge specialist
- [ ] Implement `core/monitor.py` - Fleet patrol

#### 2.3 Agent Prompts
- [ ] Port agent definitions from `agents/*.md`
- [ ] Create Python prompt templates
- [ ] Add failure mode detection
- [ ] Implement communication protocols

---

### Phase 3: CLI Commands (Week 3)

#### 3.1 Core Commands
- [ ] Implement `opencode sling <task-id>` - Spawn agent
- [ ] Implement `opencode init` - Initialize project
- [ ] Implement `opencode stop <agent>` - Terminate agent
- [ ] Implement `opencode prime` - Load context

#### 3.2 Coordination Commands
- [ ] Implement `opencode coordinator start/stop/status`
- [ ] Implement task specification commands

#### 3.3 Messaging Commands
- [ ] Implement `opencode mail send/check/list/read/reply`
- [ ] Implement `opencode nudge`

#### 3.4 Task Group Commands
- [ ] Implement `opencode group create/status/add/list`

#### 3.5 Merge Commands
- [ ] Implement `opencode merge` with conflict resolution

---

### Phase 4: Observability (Week 4)

#### 4.1 Monitoring Commands
- [ ] Implement `opencode status` - Enhanced with agent state
- [ ] Implement `opencode dashboard` - Live TUI
- [ ] Implement `opencode inspect` - Per-agent inspection
- [ ] Implement `opencode trace` - Timeline viewing
- [ ] Implement `opencode errors` - Error aggregation
- [ ] Implement `opencode replay` - Chronological replay
- [ ] Implement `opencode feed` - Real-time event stream

#### 4.2 Logging and Metrics
- [ ] Implement `opencode logs` - Query logs
- [ ] Implement `opencode costs` - Token/cost analysis
- [ ] Implement `opencode metrics` - Session metrics
- [ ] Implement `opencode run list/show` - Run management

---

### Phase 5: Infrastructure (Week 5)

#### 5.1 Watchdog System
- [ ] Implement Tier 0: Mechanical daemon
- [ ] Implement Tier 1: AI-assisted triage
- [ ] Implement Tier 2: Monitor agent

#### 5.2 Infrastructure Commands
- [ ] Implement `opencode hooks install/uninstall/status`
- [ ] Implement `opencode worktree list/clean`
- [ ] Implement `opencode watch` - Start watchdog
- [ ] Implement `opencode monitor start/stop/status`
- [ ] Implement `opencode clean`
- [ ] Implement `opencode doctor` - 11 health check categories
- [ ] Implement `opencode ecosystem`
- [ ] Implement `opencode agents discover`

---

### Phase 6: Runtime Adapters (Week 6)

#### 6.1 Adapter Interface
- [ ] Define `AgentRuntime` interface
- [ ] Implement adapter contract

#### 6.2 Runtime Implementations
- [ ] Implement Claude Code adapter (primary)
- [ ] Implement Pi adapter (optional)
- [ ] Implement Copilot adapter (optional)
- [ ] Implement Codex adapter (optional)

---

## Agent Definitions

### Coordinator Agent
- **Role**: Persistent orchestrator at project root
- **Access**: Read-only
- **Responsibilities**: 
  - Decompose objectives into tasks
  - Dispatch leads
  - Track task groups
  - Handle escalations

### Supervisor Agent
- **Role**: Per-project team lead
- **Access**: Read-only
- **Responsibilities**:
  - Manage worker lifecycle
  - Handle nudge/escalation
  - Coordinate within project

### Scout Agent
- **Role**: Read-only exploration
- **Access**: Read-only
- **Responsibilities**:
  - Explore codebase
  - Research topics
  - Produce specifications

### Builder Agent
- **Role**: Implementation
- **Access**: Read-write
- **Responsibilities**:
  - Write code
  - Run tests
  - Pass quality gates

### Reviewer Agent
- **Role**: Validation
- **Access**: Read-only
- **Responsibilities**:
  - Code review
  - Quality validation
  - Feedback provision

### Lead Agent
- **Role**: Team coordination
- **Access**: Read-write
- **Responsibilities**:
  - Spawn sub-workers (scouts, builders, reviewers)
  - Coordinate team efforts
  - Manage merge readiness

### Merger Agent
- **Role**: Branch merge
- **Access**: Read-write
- **Responsibilities**:
  - Handle conflict resolution
  - Merge branches
  - Resolve conflicts

### Monitor Agent
- **Role**: Fleet patrol
- **Access**: Read-only
- **Responsibilities**:
  - Continuous health monitoring
  - Issue detection
  - Escalation triggers

---

## Communication Protocol

### Message Types

```python
# Status update
Message(
    type="status",
    subject="Progress: <topic>",
    body="<update>",
    priority="normal"
)

# Question/clarification
Message(
    type="question", 
    subject="Question: <topic>",
    body="<question>",
    priority="normal"
)

# Error report
Message(
    type="error",
    subject="Error: <topic>",
    body="<error details>",
    priority="high"
)

# Completion signal
Message(
    type="worker_done",
    subject="Done: <task>",
    body="<summary>",
    priority="normal"
)

# Merge ready
Message(
    type="merge_ready",
    subject="Ready to merge",
    body="<details>",
    priority="normal"
)
```

---

## Conflict Resolution (4-Tier)

1. **Tier 1**: Automatic - Trivial conflicts (whitespace, formatting)
2. **Tier 2**: Heuristic - Pattern-based resolution
3. **Tier 3**: Agent - Merger agent intervention
4. **Tier 4**: Human - Manual resolution required

---

## Testing Strategy

### Unit Tests
- [ ] Test messaging system
- [ ] Test worktree operations
- [ ] Test agent lifecycle
- [ ] Test conflict resolution

### Integration Tests
- [ ] Test agent spawning
- [ ] Test inter-agent communication
- [ ] Test merge workflow

### E2E Tests
- [ ] Test full coordination workflow
- [ ] Test multi-agent scenario

---

## Success Criteria

1. ✅ All CLI commands implemented
2. ✅ All agent types functional
3. ✅ Messaging system operational
4. ✅ Conflict resolution working
5. ✅ Test coverage > 80%

---

## Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1: Infrastructure | Week 1 | Messaging, worktree, config |
| Phase 2: Agents | Week 2 | All 8 agent types |
| Phase 3: CLI | Week 3 | All commands |
| Phase 4: Observability | Week 4 | Monitoring tools |
| Phase 5: Infrastructure | Week 5 | Watchdog, hooks |
| Phase 6: Runtimes | Week 6 | Runtime adapters |

**Total Estimated Time**: 6 weeks

---

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|-------------|
| TypeScript → Python porting | High | Extract patterns, reimplement |
| Complexity of multi-agent | High | Incremental implementation |
| Testing difficulty | Medium | Use overstory test patterns |
| New dependencies (tmux) | Low | Make optional |

---

*Last updated: 2026-03-01*
