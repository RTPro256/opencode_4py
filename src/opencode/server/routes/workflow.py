"""
Workflow API Routes

FastAPI routes for workflow management and execution.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio

from opencode.workflow.graph import WorkflowGraph, WorkflowNode, WorkflowEdge, WorkflowMetadata
from opencode.workflow.engine import WorkflowEngine, ExecutionEvent
from opencode.workflow.state import WorkflowState, ExecutionStatus
from opencode.workflow.registry import NodeRegistry

router = APIRouter(prefix="/workflows", tags=["workflows"])

# Global engine instance
_engine: Optional[WorkflowEngine] = None


def get_engine() -> WorkflowEngine:
    """Get or create the workflow engine."""
    global _engine
    if _engine is None:
        _engine = WorkflowEngine()
    return _engine


# Request/Response Models
class CreateWorkflowRequest(BaseModel):
    """Request to create a new workflow."""
    name: str
    description: str = ""
    variables: Dict[str, Any] = {}


class UpdateWorkflowRequest(BaseModel):
    """Request to update a workflow."""
    name: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[Dict[str, Any]] = None


class AddNodeRequest(BaseModel):
    """Request to add a node to a workflow."""
    node_type: str
    position_x: float = 0
    position_y: float = 0
    config: Dict[str, Any] = {}
    label: Optional[str] = None


class AddEdgeRequest(BaseModel):
    """Request to add an edge to a workflow."""
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str


class ExecuteWorkflowRequest(BaseModel):
    """Request to execute a workflow."""
    variables: Dict[str, Any] = {}


# In-memory workflow storage (would be database in production)
_workflows: Dict[str, WorkflowGraph] = {}


@router.get("/")
async def list_workflows() -> List[Dict[str, Any]]:
    """List all workflows."""
    return [
        {
            "id": wf.id,
            "name": wf.metadata.name,
            "description": wf.metadata.description,
            "node_count": len(wf.nodes),
            "edge_count": len(wf.edges),
            "updated_at": wf.metadata.updated_at.isoformat(),
        }
        for wf in _workflows.values()
    ]


@router.post("/")
async def create_workflow(request: CreateWorkflowRequest) -> Dict[str, Any]:
    """Create a new workflow."""
    workflow = WorkflowGraph(
        metadata=WorkflowMetadata(
            name=request.name,
            description=request.description,
        ),
        variables=request.variables,
    )
    
    _workflows[workflow.id] = workflow
    
    return {
        "id": workflow.id,
        "name": workflow.metadata.name,
        "description": workflow.metadata.description,
    }


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get a workflow by ID."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = _workflows[workflow_id]
    return workflow.to_dict()


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, request: UpdateWorkflowRequest) -> Dict[str, Any]:
    """Update a workflow."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = _workflows[workflow_id]
    
    if request.name is not None:
        workflow.metadata.name = request.name
    if request.description is not None:
        workflow.metadata.description = request.description
    if request.variables is not None:
        workflow.variables = request.variables
    
    return workflow.to_dict()


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str) -> Dict[str, str]:
    """Delete a workflow."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    del _workflows[workflow_id]
    return {"status": "deleted"}


@router.post("/{workflow_id}/nodes")
async def add_node(workflow_id: str, request: AddNodeRequest) -> Dict[str, Any]:
    """Add a node to a workflow."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = _workflows[workflow_id]
    
    node = WorkflowNode(
        node_type=request.node_type,
        position_x=request.position_x,
        position_y=request.position_y,
        config=request.config,
        label=request.label,
    )
    
    workflow.add_node(node)
    
    return {
        "node_id": node.id,
        "node_type": node.node_type,
    }


@router.delete("/{workflow_id}/nodes/{node_id}")
async def remove_node(workflow_id: str, node_id: str) -> Dict[str, str]:
    """Remove a node from a workflow."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = _workflows[workflow_id]
    
    if not workflow.remove_node(node_id):
        raise HTTPException(status_code=404, detail="Node not found")
    
    return {"status": "deleted"}


@router.post("/{workflow_id}/edges")
async def add_edge(workflow_id: str, request: AddEdgeRequest) -> Dict[str, Any]:
    """Add an edge to a workflow."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = _workflows[workflow_id]
    
    edge = WorkflowEdge(
        source_node_id=request.source_node_id,
        source_port=request.source_port,
        target_node_id=request.target_node_id,
        target_port=request.target_port,
    )
    
    success, error = workflow.add_edge(edge)
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    return {
        "edge_id": edge.id,
        "source": edge.source_node_id,
        "target": edge.target_node_id,
    }


@router.delete("/{workflow_id}/edges/{edge_id}")
async def remove_edge(workflow_id: str, edge_id: str) -> Dict[str, str]:
    """Remove an edge from a workflow."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = _workflows[workflow_id]
    
    if not workflow.remove_edge(edge_id):
        raise HTTPException(status_code=404, detail="Edge not found")
    
    return {"status": "deleted"}


@router.post("/{workflow_id}/execute")
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Execute a workflow."""
    if workflow_id not in _workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    workflow = _workflows[workflow_id]
    engine = get_engine()
    
    # Execute in background
    state = await engine.execute(workflow, request.variables)
    
    return {
        "execution_id": state.execution_id,
        "status": state.status.value,
        "started_at": state.started_at.isoformat() if state.started_at else None,
        "completed_at": state.completed_at.isoformat() if state.completed_at else None,
        "error": state.error,
    }


@router.get("/{workflow_id}/executions/{execution_id}")
async def get_execution_state(workflow_id: str, execution_id: str) -> Dict[str, Any]:
    """Get the state of a workflow execution."""
    engine = get_engine()
    state = engine.get_state(execution_id)
    
    if state is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return state.to_dict()


@router.post("/{workflow_id}/executions/{execution_id}/cancel")
async def cancel_execution(workflow_id: str, execution_id: str) -> Dict[str, Any]:
    """Cancel a running execution."""
    engine = get_engine()
    
    if not engine.cancel(execution_id):
        raise HTTPException(status_code=404, detail="Execution not found or already complete")
    
    return {"status": "cancelled"}


@router.get("/node-types")
async def list_node_types() -> List[Dict[str, Any]]:
    """List all available node types."""
    schemas = NodeRegistry.get_all_schemas()
    return [
        {
            "type": name,
            "display_name": schema.display_name,
            "description": schema.description,
            "category": schema.category,
            "inputs": [
                {"name": p.name, "type": p.data_type, "required": p.required}
                for p in schema.inputs
            ],
            "outputs": [
                {"name": p.name, "type": p.data_type}
                for p in schema.outputs
            ],
        }
        for name, schema in schemas.items()
    ]


# ============ Multi-Model Pattern Endpoints ============

class MultiModelExecuteRequest(BaseModel):
    """Request to execute a multi-model pattern."""
    prompt: str
    pattern_name: Optional[str] = None
    pattern: Optional[str] = None  # "sequential", "ensemble", "voting"
    models: Optional[List[Dict[str, Any]]] = None


class ModelStepRequest(BaseModel):
    """Model step configuration for ad-hoc patterns."""
    model: str
    provider: str = "ollama"
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096


@router.get("/multi-model/patterns")
async def list_multi_model_patterns() -> List[Dict[str, Any]]:
    """
    List available multi-model patterns from configuration.
    
    Returns patterns defined in opencode.toml under [multi_model_patterns.*].
    """
    from opencode.core.config import get_config
    
    try:
        config = get_config()
        patterns = []
        
        for name, mm_config in config.multi_model_patterns.items():
            patterns.append({
                "name": name,
                "pattern": mm_config.pattern.value,
                "models": [
                    {
                        "model": m.model,
                        "provider": m.provider,
                        "system_prompt": m.system_prompt,
                        "temperature": m.temperature,
                    }
                    for m in mm_config.models
                ],
                "enabled": mm_config.enabled,
                "aggregator_model": mm_config.aggregator_model,
                "voting_strategy": mm_config.voting_strategy,
            })
        
        return patterns
    except Exception as e:
        return []


@router.post("/multi-model/execute")
async def execute_multi_model(
    request: MultiModelExecuteRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Execute a multi-model pattern.
    
    Either specify a named pattern from config with pattern_name,
    or build an ad-hoc pattern with pattern type and models list.
    
    Example:
        POST /workflows/multi-model/execute
        {
            "prompt": "Write a Python function",
            "pattern_name": "code_review"
        }
        
        Or ad-hoc:
        {
            "prompt": "Write a Python function",
            "pattern": "sequential",
            "models": [
                {"model": "llama3.2", "provider": "ollama"},
                {"model": "mistral:7b", "provider": "ollama"}
            ]
        }
    """
    from opencode.workflow.templates import get_template
    from opencode.core.config import get_config, MultiModelConfig, MultiModelPattern, ModelStepConfig
    
    config = get_config()
    
    # Get pattern configuration
    if request.pattern_name:
        mm_config = config.multi_model_patterns.get(request.pattern_name)
        if not mm_config:
            raise HTTPException(
                status_code=404,
                detail=f"Pattern not found: {request.pattern_name}"
            )
    elif request.pattern and request.models:
        # Build ad-hoc pattern
        try:
            pattern = MultiModelPattern(request.pattern)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid pattern: {request.pattern}. Use: sequential, ensemble, voting"
            )
        
        model_configs = [
            ModelStepConfig(
                model=m.get("model", "llama3.2"),
                provider=m.get("provider", "ollama"),
                system_prompt=m.get("system_prompt"),
                temperature=m.get("temperature", 0.7),
                max_tokens=m.get("max_tokens", 4096),
            )
            for m in request.models
        ]
        
        mm_config = MultiModelConfig(
            pattern=pattern,
            models=model_configs,
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Specify pattern_name or pattern with models"
        )
    
    if not mm_config.enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Pattern is disabled"
        )
    
    try:
        # Build and execute workflow
        template = get_template(mm_config.pattern.value, mm_config)
        engine = get_engine()
        
        state = await engine.execute(template, variables={"input": request.prompt})
        
        # Extract output
        output = None
        for node_id, node_state in state.node_states.items():
            if hasattr(node_state, 'status') and str(node_state.status) == "completed":
                if hasattr(node_state, 'outputs') and node_state.outputs:
                    output = node_state.outputs.get("output")
                    if output:
                        break
        
        return {
            "execution_id": state.execution_id,
            "status": state.status.value,
            "pattern": mm_config.pattern.value,
            "model_count": len(mm_config.models),
            "output": output,
            "error": state.error,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Execution failed: {str(e)}"
        )


# WebSocket for real-time execution updates
@router.websocket("/{workflow_id}/ws")
async def workflow_websocket(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for real-time workflow execution updates."""
    await websocket.accept()
    
    engine = get_engine()
    queue: asyncio.Queue[ExecutionEvent] = asyncio.Queue()
    
    def event_handler(event: ExecutionEvent) -> None:
        """Handle execution events."""
        try:
            asyncio.get_event_loop().call_soon_threadsafe(
                queue.put_nowait, event
            )
        except Exception:
            pass
    
    engine.add_event_handler(event_handler)
    
    try:
        while True:
            # Wait for events
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                await websocket.send_json(event.to_dict())
            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json({"type": "ping"})
    except WebSocketDisconnect:
        pass
    finally:
        engine.remove_event_handler(event_handler)


# ============ GPU Management Endpoints ============

class GPUAllocateRequest(BaseModel):
    """Request to allocate a GPU for a model."""
    model_id: str
    vram_required_gb: Optional[float] = None
    preferred_gpu_id: Optional[int] = None
    exclusive: bool = False


class GPUReleaseRequest(BaseModel):
    """Request to release a GPU allocation."""
    model_id: str


class GPURecommendRequest(BaseModel):
    """Request to recommend GPU allocations for multiple models."""
    models: List[Dict[str, Any]]  # Each with model_id and vram_required_gb


@router.get("/gpu/status")
async def get_gpu_status() -> Dict[str, Any]:
    """
    Get current GPU status and allocations.
    
    Returns information about all GPUs including:
    - Memory usage
    - Models loaded on each GPU
    - Current allocations
    """
    from opencode.core.gpu_manager import get_gpu_manager
    
    try:
        manager = get_gpu_manager()
        return await manager.get_status()
    except Exception as e:
        return {
            "error": str(e),
            "gpus": [],
            "allocations": {},
        }


@router.post("/gpu/allocate")
async def allocate_gpu(request: GPUAllocateRequest) -> Dict[str, Any]:
    """
    Allocate a GPU for a model.
    
    The GPU manager will select the best available GPU based on:
    - Configured allocation strategy
    - VRAM requirements
    - Current GPU utilization
    
    Example:
        POST /workflows/gpu/allocate
        {
            "model_id": "llama3.2:70b",
            "vram_required_gb": 40.0,
            "preferred_gpu_id": 0
        }
    """
    from opencode.core.gpu_manager import get_gpu_manager
    
    manager = get_gpu_manager()
    gpu_id = await manager.allocate_gpu(
        model_id=request.model_id,
        vram_required_gb=request.vram_required_gb,
        preferred_gpu_id=request.preferred_gpu_id,
        exclusive=request.exclusive,
    )
    
    if gpu_id is None:
        raise HTTPException(
            status_code=503,
            detail="No suitable GPU available for allocation"
        )
    
    return {
        "allocated_gpu_id": gpu_id,
        "model_id": request.model_id,
        "vram_required_gb": request.vram_required_gb,
    }


@router.post("/gpu/release")
async def release_gpu(request: GPUReleaseRequest) -> Dict[str, Any]:
    """
    Release GPU allocation for a model.
    
    Example:
        POST /workflows/gpu/release
        {
            "model_id": "llama3.2:70b"
        }
    """
    from opencode.core.gpu_manager import get_gpu_manager
    
    manager = get_gpu_manager()
    released = await manager.release_gpu(request.model_id)
    
    if not released:
        raise HTTPException(
            status_code=404,
            detail=f"No allocation found for model: {request.model_id}"
        )
    
    return {
        "released": True,
        "model_id": request.model_id,
    }


@router.post("/gpu/release-all")
async def release_all_gpus() -> Dict[str, Any]:
    """Release all GPU allocations."""
    from opencode.core.gpu_manager import get_gpu_manager
    
    manager = get_gpu_manager()
    count = await manager.release_all()
    
    return {
        "released_count": count,
    }


@router.post("/gpu/recommend")
async def recommend_gpu_allocation(request: GPURecommendRequest) -> Dict[str, Any]:
    """
    Get GPU allocation recommendations for multiple models.
    
    This is useful for planning ensemble or parallel executions
    without actually allocating GPUs.
    
    Example:
        POST /workflows/gpu/recommend
        {
            "models": [
                {"model_id": "llama3.2:70b", "vram_required_gb": 40.0},
                {"model_id": "mistral:7b", "vram_required_gb": 16.0}
            ]
        }
    """
    from opencode.core.gpu_manager import get_gpu_manager
    
    manager = get_gpu_manager()
    recommendations = await manager.recommend_allocation(request.models)
    
    can_run_parallel = all(gpu_id is not None for gpu_id in recommendations.values())
    
    return {
        "recommendations": recommendations,
        "can_run_parallel": can_run_parallel,
        "model_count": len(request.models),
    }


@router.get("/gpu/can-run-parallel")
async def check_parallel_capability(
    models: str,  # Comma-separated list of model_id:vram_gb pairs
) -> Dict[str, Any]:
    """
    Check if multiple models can run in parallel on available GPUs.
    
    Query param format: model1:10,model2:20,model3:5
    (model_id:vram_required_gb pairs)
    """
    from opencode.core.gpu_manager import get_gpu_manager
    
    try:
        model_list = []
        for pair in models.split(","):
            if ":" in pair:
                model_id, vram_str = pair.rsplit(":", 1)
                model_list.append({
                    "model_id": model_id,
                    "vram_required_gb": float(vram_str),
                })
        
        manager = get_gpu_manager()
        can_run = await manager.can_run_parallel(model_list)
        recommendations = await manager.recommend_allocation(model_list)
        
        return {
            "can_run_parallel": can_run,
            "recommendations": recommendations,
            "models": model_list,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model format: {str(e)}"
        )
