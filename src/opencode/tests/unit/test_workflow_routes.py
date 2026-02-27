"""
Tests for Workflow API Routes.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
import asyncio

from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    """Create a FastAPI app with workflow routes."""
    from opencode.server.routes.workflow import router
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def clear_workflows():
    """Clear workflows before each test."""
    from opencode.server.routes import workflow
    workflow._workflows.clear()
    yield
    workflow._workflows.clear()


@pytest.mark.unit
class TestWorkflowRoutes:
    """Tests for workflow routes."""

    def test_list_workflows_empty(self, client, clear_workflows):
        """Test listing workflows when empty."""
        response = client.get("/workflows/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_workflow(self, client, clear_workflows):
        """Test creating a workflow."""
        response = client.post(
            "/workflows/",
            json={
                "name": "Test Workflow",
                "description": "A test workflow",
                "variables": {"var1": "value1"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test Workflow"
        assert data["description"] == "A test workflow"

    def test_list_workflows_with_data(self, client, clear_workflows):
        """Test listing workflows with data."""
        # Create a workflow first
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        response = client.get("/workflows/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == workflow_id
        assert data[0]["name"] == "Test Workflow"

    def test_get_workflow(self, client, clear_workflows):
        """Test getting a workflow by ID."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        response = client.get(f"/workflows/{workflow_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == workflow_id
        assert data["metadata"]["name"] == "Test Workflow"

    def test_get_workflow_not_found(self, client, clear_workflows):
        """Test getting a non-existent workflow."""
        response = client.get("/workflows/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_workflow(self, client, clear_workflows):
        """Test updating a workflow."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        response = client.put(
            f"/workflows/{workflow_id}",
            json={"name": "Updated Name", "description": "Updated description"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "Updated Name"
        assert data["metadata"]["description"] == "Updated description"

    def test_update_workflow_partial(self, client, clear_workflows):
        """Test partially updating a workflow."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        response = client.put(
            f"/workflows/{workflow_id}",
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "Updated Name"
        assert data["metadata"]["description"] == "Test"

    def test_update_workflow_not_found(self, client, clear_workflows):
        """Test updating a non-existent workflow."""
        response = client.put(
            "/workflows/nonexistent",
            json={"name": "Updated"},
        )
        assert response.status_code == 404

    def test_delete_workflow(self, client, clear_workflows):
        """Test deleting a workflow."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        response = client.delete(f"/workflows/{workflow_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # Verify it's deleted
        get_response = client.get(f"/workflows/{workflow_id}")
        assert get_response.status_code == 404

    def test_delete_workflow_not_found(self, client, clear_workflows):
        """Test deleting a non-existent workflow."""
        response = client.delete("/workflows/nonexistent")
        assert response.status_code == 404

    def test_add_node(self, client, clear_workflows):
        """Test adding a node to a workflow."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        response = client.post(
            f"/workflows/{workflow_id}/nodes",
            json={
                "node_type": "llm_process",
                "position_x": 100,
                "position_y": 200,
                "config": {"model": "llama3.2"},
                "label": "LLM Node",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "node_id" in data
        assert data["node_type"] == "llm_process"

    def test_add_node_workflow_not_found(self, client, clear_workflows):
        """Test adding a node to a non-existent workflow."""
        response = client.post(
            "/workflows/nonexistent/nodes",
            json={"node_type": "llm_process"},
        )
        assert response.status_code == 404

    def test_remove_node(self, client, clear_workflows):
        """Test removing a node from a workflow."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        # Add a node first
        add_response = client.post(
            f"/workflows/{workflow_id}/nodes",
            json={"node_type": "llm_process"},
        )
        node_id = add_response.json()["node_id"]

        # Remove the node
        response = client.delete(f"/workflows/{workflow_id}/nodes/{node_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_remove_node_not_found(self, client, clear_workflows):
        """Test removing a non-existent node."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        response = client.delete(f"/workflows/{workflow_id}/nodes/nonexistent")
        assert response.status_code == 404

    def test_add_edge(self, client, clear_workflows):
        """Test adding an edge to a workflow."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        # Add two nodes
        node1_response = client.post(
            f"/workflows/{workflow_id}/nodes",
            json={"node_type": "data_source"},
        )
        node1_id = node1_response.json()["node_id"]

        node2_response = client.post(
            f"/workflows/{workflow_id}/nodes",
            json={"node_type": "llm_process"},
        )
        node2_id = node2_response.json()["node_id"]

        # Add edge
        response = client.post(
            f"/workflows/{workflow_id}/edges",
            json={
                "source_node_id": node1_id,
                "source_port": "output",
                "target_node_id": node2_id,
                "target_port": "input",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "edge_id" in data
        assert data["source"] == node1_id
        assert data["target"] == node2_id

    def test_add_edge_workflow_not_found(self, client, clear_workflows):
        """Test adding an edge to a non-existent workflow."""
        response = client.post(
            "/workflows/nonexistent/edges",
            json={
                "source_node_id": "node1",
                "source_port": "output",
                "target_node_id": "node2",
                "target_port": "input",
            },
        )
        assert response.status_code == 404

    def test_remove_edge(self, client, clear_workflows):
        """Test removing an edge from a workflow."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        # Add two nodes
        node1_response = client.post(
            f"/workflows/{workflow_id}/nodes",
            json={"node_type": "data_source"},
        )
        node1_id = node1_response.json()["node_id"]

        node2_response = client.post(
            f"/workflows/{workflow_id}/nodes",
            json={"node_type": "llm_process"},
        )
        node2_id = node2_response.json()["node_id"]

        # Add edge
        edge_response = client.post(
            f"/workflows/{workflow_id}/edges",
            json={
                "source_node_id": node1_id,
                "source_port": "output",
                "target_node_id": node2_id,
                "target_port": "input",
            },
        )
        edge_id = edge_response.json()["edge_id"]

        # Remove edge
        response = client.delete(f"/workflows/{workflow_id}/edges/{edge_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

    def test_remove_edge_not_found(self, client, clear_workflows):
        """Test removing a non-existent edge."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        response = client.delete(f"/workflows/{workflow_id}/edges/nonexistent")
        assert response.status_code == 404


@pytest.mark.unit
class TestWorkflowExecutionRoutes:
    """Tests for workflow execution routes."""

    @patch("opencode.server.routes.workflow.get_engine")
    def test_execute_workflow(self, mock_get_engine, client, clear_workflows):
        """Test executing a workflow."""
        # Create a workflow
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        # Mock the engine
        mock_engine = MagicMock()
        mock_state = MagicMock()
        mock_state.execution_id = "exec-123"
        mock_state.status = MagicMock()
        mock_state.status.value = "completed"
        mock_state.started_at = datetime.now()
        mock_state.completed_at = datetime.now()
        mock_state.error = None
        mock_engine.execute = AsyncMock(return_value=mock_state)
        mock_get_engine.return_value = mock_engine

        response = client.post(
            f"/workflows/{workflow_id}/execute",
            json={"variables": {"input": "test"}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == "exec-123"
        assert data["status"] == "completed"

    def test_execute_workflow_not_found(self, client, clear_workflows):
        """Test executing a non-existent workflow."""
        response = client.post(
            "/workflows/nonexistent/execute",
            json={"variables": {}},
        )
        assert response.status_code == 404

    @patch("opencode.server.routes.workflow.get_engine")
    def test_get_execution_state(self, mock_get_engine, client, clear_workflows):
        """Test getting execution state."""
        mock_engine = MagicMock()
        mock_state = MagicMock()
        mock_state.to_dict.return_value = {
            "execution_id": "exec-123",
            "status": "completed",
        }
        mock_engine.get_state.return_value = mock_state
        mock_get_engine.return_value = mock_engine

        response = client.get("/workflows/wf-123/executions/exec-123")
        assert response.status_code == 200
        data = response.json()
        assert data["execution_id"] == "exec-123"

    @patch("opencode.server.routes.workflow.get_engine")
    def test_get_execution_state_not_found(self, mock_get_engine, client, clear_workflows):
        """Test getting a non-existent execution state."""
        mock_engine = MagicMock()
        mock_engine.get_state.return_value = None
        mock_get_engine.return_value = mock_engine

        response = client.get("/workflows/wf-123/executions/nonexistent")
        assert response.status_code == 404

    @patch("opencode.server.routes.workflow.get_engine")
    def test_cancel_execution(self, mock_get_engine, client, clear_workflows):
        """Test canceling an execution."""
        mock_engine = MagicMock()
        mock_engine.cancel.return_value = True
        mock_get_engine.return_value = mock_engine

        response = client.post("/workflows/wf-123/executions/exec-123/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    @patch("opencode.server.routes.workflow.get_engine")
    def test_cancel_execution_not_found(self, mock_get_engine, client, clear_workflows):
        """Test canceling a non-existent execution."""
        mock_engine = MagicMock()
        mock_engine.cancel.return_value = False
        mock_get_engine.return_value = mock_engine

        response = client.post("/workflows/wf-123/executions/nonexistent/cancel")
        assert response.status_code == 404


@pytest.mark.unit
class TestMultiModelRoutes:
    """Tests for multi-model pattern routes."""

    @patch("opencode.core.config.get_config")
    def test_list_multi_model_patterns(self, mock_get_config, client, clear_workflows):
        """Test listing multi-model patterns."""
        mock_config = MagicMock()
        mock_config.multi_model_patterns = {}
        mock_get_config.return_value = mock_config

        response = client.get("/workflows/multi-model/patterns")
        assert response.status_code == 200
        assert response.json() == []

    @patch("opencode.core.config.get_config")
    def test_list_multi_model_patterns_error(self, mock_get_config, client, clear_workflows):
        """Test listing multi-model patterns with error."""
        mock_get_config.side_effect = Exception("Config error")

        response = client.get("/workflows/multi-model/patterns")
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.unit
class TestGPURoutes:
    """Tests for GPU management routes."""

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_get_gpu_status(self, mock_get_gpu_manager, client, clear_workflows):
        """Test getting GPU status."""
        mock_manager = MagicMock()
        mock_manager.get_status = AsyncMock(return_value={
            "gpus": [{"id": 0, "name": "RTX 4090"}],
            "allocations": {},
        })
        mock_get_gpu_manager.return_value = mock_manager

        response = client.get("/workflows/gpu/status")
        assert response.status_code == 200
        data = response.json()
        assert "gpus" in data

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_get_gpu_status_error(self, mock_get_gpu_manager, client, clear_workflows):
        """Test getting GPU status with error."""
        mock_get_gpu_manager.side_effect = Exception("GPU error")

        response = client.get("/workflows/gpu/status")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_allocate_gpu(self, mock_get_gpu_manager, client, clear_workflows):
        """Test allocating a GPU."""
        mock_manager = MagicMock()
        mock_manager.allocate_gpu = AsyncMock(return_value=0)
        mock_get_gpu_manager.return_value = mock_manager

        response = client.post(
            "/workflows/gpu/allocate",
            json={
                "model_id": "llama3.2",
                "vram_required_gb": 16.0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["allocated_gpu_id"] == 0

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_allocate_gpu_no_available(self, mock_get_gpu_manager, client, clear_workflows):
        """Test allocating a GPU when none available."""
        mock_manager = MagicMock()
        mock_manager.allocate_gpu = AsyncMock(return_value=None)
        mock_get_gpu_manager.return_value = mock_manager

        response = client.post(
            "/workflows/gpu/allocate",
            json={
                "model_id": "llama3.2",
                "vram_required_gb": 100.0,
            },
        )
        assert response.status_code == 503

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_release_gpu(self, mock_get_gpu_manager, client, clear_workflows):
        """Test releasing a GPU allocation."""
        mock_manager = MagicMock()
        mock_manager.release_gpu = AsyncMock(return_value=True)
        mock_get_gpu_manager.return_value = mock_manager

        response = client.post(
            "/workflows/gpu/release",
            json={"model_id": "llama3.2"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["released"] is True

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_release_gpu_not_found(self, mock_get_gpu_manager, client, clear_workflows):
        """Test releasing a non-existent GPU allocation."""
        mock_manager = MagicMock()
        mock_manager.release_gpu = AsyncMock(return_value=False)
        mock_get_gpu_manager.return_value = mock_manager

        response = client.post(
            "/workflows/gpu/release",
            json={"model_id": "nonexistent"},
        )
        assert response.status_code == 404

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_release_all_gpus(self, mock_get_gpu_manager, client, clear_workflows):
        """Test releasing all GPU allocations."""
        mock_manager = MagicMock()
        mock_manager.release_all = AsyncMock(return_value=3)
        mock_get_gpu_manager.return_value = mock_manager

        response = client.post("/workflows/gpu/release-all")
        assert response.status_code == 200
        data = response.json()
        assert data["released_count"] == 3

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_recommend_gpu_allocation(self, mock_get_gpu_manager, client, clear_workflows):
        """Test getting GPU allocation recommendations."""
        mock_manager = MagicMock()
        mock_manager.recommend_allocation = AsyncMock(return_value={
            "llama3.2": 0,
            "mistral:7b": 1,
        })
        mock_get_gpu_manager.return_value = mock_manager

        response = client.post(
            "/workflows/gpu/recommend",
            json={
                "models": [
                    {"model_id": "llama3.2", "vram_required_gb": 16.0},
                    {"model_id": "mistral:7b", "vram_required_gb": 8.0},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["can_run_parallel"] is True
        assert data["model_count"] == 2

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_check_parallel_capability(self, mock_get_gpu_manager, client, clear_workflows):
        """Test checking parallel capability."""
        mock_manager = MagicMock()
        mock_manager.can_run_parallel = AsyncMock(return_value=True)
        mock_manager.recommend_allocation = AsyncMock(return_value={"llama3.2": 0})
        mock_get_gpu_manager.return_value = mock_manager

        response = client.get("/workflows/gpu/can-run-parallel?models=llama3.2:16")
        assert response.status_code == 200
        data = response.json()
        assert data["can_run_parallel"] is True

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_check_parallel_capability_invalid_format(self, mock_get_gpu_manager, client, clear_workflows):
        """Test checking parallel capability with invalid format."""
        mock_manager = MagicMock()
        mock_manager.can_run_parallel = AsyncMock(return_value=False)
        mock_manager.recommend_allocation = AsyncMock(return_value={})
        mock_get_gpu_manager.return_value = mock_manager

        response = client.get("/workflows/gpu/can-run-parallel?models=invalid")
        # The route handles invalid format gracefully
        assert response.status_code == 200
