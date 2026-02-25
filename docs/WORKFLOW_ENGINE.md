# Workflow Example

## What is a Workflow in OpenCode?

A **workflow** in OpenCode is a Directed Acyclic Graph (DAG) based execution system that orchestrates nodes, handles data flow between them, and manages execution state. It's similar to workflow systems like Apache Airflow, Prefect, or n8n.

## Workflow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      WorkflowEngine                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Node 1     │──│   Node 2     │──│   Node 3     │          │
│  │ (Data Source)│  │ (Transform)  │  │   (Output)   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                            │                                     │
│                            ▼                                     │
│                    ┌──────────────┐                             │
│                    │   Node 4     │                             │
│                    │  (LLM Call)  │                             │
│                    └──────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. WorkflowGraph
Defines the structure of a workflow with nodes and edges:
- **Nodes**: Individual processing units (data source, transform, LLM call, etc.)
- **Edges**: Connections between nodes defining data flow

### 2. WorkflowEngine
Orchestrates execution:
- Loads and validates workflows
- Determines execution order (topological sort)
- Executes nodes in parallel where possible
- Manages execution state
- Handles errors and retries
- Emits events for real-time updates

### 3. BaseNode Types
- **DataSourceNode**: Load data from files, APIs, databases
- **DataValidationNode**: Validate and clean data
- **LLMProcessNode**: Send prompts to AI models
- **HTTPNode**: Make HTTP requests
- **ToolNode**: Execute tools
- **ChartNode**: Generate visualizations
- **TimerNode**: Control timing and delays
- **JSONReformatterNode**: Transform JSON data

## Example Workflow Definition

```python
from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge
from opencode.workflow.engine import WorkflowEngine

# Create a simple workflow
graph = WorkflowGraph()

# Add nodes
graph.add_node(WorkflowNode(
    id="load_data",
    type="data_source",
    config={"source_type": "file", "path": "data.json"}
))

graph.add_node(WorkflowNode(
    id="process",
    type="llm_process",
    config={"prompt": "Summarize this data: {{load_data.output}}"}
))

graph.add_node(WorkflowNode(
    id="output",
    type="tool",
    config={"tool_name": "write_file", "path": "summary.txt"}
))

# Add edges (define data flow)
graph.add_edge(WorkflowEdge(source="load_data", target="process"))
graph.add_edge(WorkflowEdge(source="process", target="output"))

# Execute
engine = WorkflowEngine()
state = await engine.execute(graph)
```

## Workflow Execution Flow

```
1. Load Workflow Graph
        ↓
2. Validate Graph (check for cycles, missing nodes)
        ↓
3. Topological Sort (determine execution order)
        ↓
4. Execute Nodes (parallel where possible)
        ↓
5. Pass Data Between Nodes
        ↓
6. Handle Errors/Retries
        ↓
7. Emit Events (for UI updates)
        ↓
8. Return Final State
```

## Node Execution Context

Each node receives an `ExecutionContext` with:
- `workflow_id`: Unique workflow identifier
- `execution_id`: Unique execution run identifier
- `node_id`: Current node identifier
- `inputs`: Data from connected upstream nodes
- `config`: Node-specific configuration
- `state`: Mutable state for the execution

## Execution Events

The engine emits events during execution:
- `workflow_started`: Workflow execution began
- `node_started`: Node execution began
- `node_completed`: Node finished successfully
- `node_failed`: Node execution failed
- `workflow_completed`: Workflow finished successfully
- `workflow_failed`: Workflow execution failed

## Configuration Options

```python
from opencode.workflow.engine import WorkflowEngineConfig

config = WorkflowEngineConfig(
    max_concurrent_nodes=10,      # Max parallel nodes
    default_timeout_seconds=300,  # Node timeout
    retry_failed_nodes=True,      # Auto-retry on failure
    max_retries=3,                # Max retry attempts
    continue_on_error=False,      # Continue if node fails
    enable_caching=True,          # Cache node outputs
)

engine = WorkflowEngine(config=config)
```

## File Structure

```
src/opencode/
├── workflow/
│   ├── __init__.py        # Module exports
│   ├── engine.py          # WorkflowEngine class
│   ├── graph.py           # WorkflowGraph, WorkflowNode, WorkflowEdge
│   ├── node.py            # BaseNode, ExecutionContext, ExecutionResult
│   ├── state.py           # WorkflowState, ExecutionStatus
│   ├── registry.py        # Node type registry
│   └── nodes/             # Built-in node types
│       ├── __init__.py
│       ├── data_source.py
│       ├── data_validation.py
│       ├── llm_process.py
│       ├── http.py
│       ├── tool.py
│       ├── chart.py
│       ├── timer.py
│       └── json_reformatter.py
```

## Related Documentation

- [Feature Coverage](FEATURE_COVERAGE.md) - Workflow engine feature status
- [Migration Plan](MIGRATION_PLAN.md) - Implementation details
