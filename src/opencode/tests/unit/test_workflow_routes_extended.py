"""
Extended tests for Workflow API Routes to improve coverage.
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
class TestWorkflowRoutesExtended:
    """Extended tests for workflow routes to cover missing paths."""

    def test_update_workflow_variables(self, client, clear_workflows):
        """Test updating workflow variables."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test", "variables": {"var1": "value1"}},
        )
        workflow_id = create_response.json()["id"]

        response = client.put(
            f"/workflows/{workflow_id}",
            json={"variables": {"var2": "value2"}},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["variables"] == {"var2": "value2"}

    def test_add_edge_invalid(self, client, clear_workflows):
        """Test adding an invalid edge."""
        create_response = client.post(
            "/workflows/",
            json={"name": "Test Workflow", "description": "Test"},
        )
        workflow_id = create_response.json()["id"]

        # Add one node
        node1_response = client.post(
            f"/workflows/{workflow_id}/nodes",
            json={"node_type": "data_source"},
        )
        node1_id = node1_response.json()["node_id"]

        # Try to add edge to non-existent target node
        response = client.post(
            f"/workflows/{workflow_id}/edges",
            json={
                "source_node_id": node1_id,
                "source_port": "output",
                "target_node_id": "nonexistent",
                "target_port": "input",
            },
        )
        # Should fail because target node doesn't exist
        assert response.status_code == 400

    def test_remove_node_workflow_not_found(self, client, clear_workflows):
        """Test removing a node from a non-existent workflow."""
        response = client.delete("/workflows/nonexistent/nodes/some-node")
        assert response.status_code == 404

    def test_remove_edge_workflow_not_found(self, client, clear_workflows):
        """Test removing an edge from a non-existent workflow."""
        response = client.delete("/workflows/nonexistent/edges/some-edge")
        assert response.status_code == 404


@pytest.mark.unit
class TestGPURoutesExtended:
    """Extended tests for GPU management routes."""

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_check_parallel_capability_error(self, mock_get_gpu_manager, client, clear_workflows):
        """Test checking parallel capability with error."""
        mock_get_gpu_manager.side_effect = Exception("GPU error")

        response = client.get("/workflows/gpu/can-run-parallel?models=llama3.2:16")
        assert response.status_code == 400

    @patch("opencode.core.gpu_manager.get_gpu_manager")
    def test_recommend_gpu_allocation_partial(self, mock_get_gpu_manager, client, clear_workflows):
        """Test GPU recommendation when only some models can be allocated."""
        mock_manager = MagicMock()
        mock_manager.recommend_allocation = AsyncMock(return_value={
            "llama3.2": 0,
            "mistral:7b": None,  # Can't allocate this one
        })
        mock_get_gpu_manager.return_value = mock_manager

        response = client.post(
            "/workflows/gpu/recommend",
            json={
                "models": [
                    {"model_id": "llama3.2", "vram_required_gb": 16.0},
                    {"model_id": "mistral:7b", "vram_required_gb": 100.0},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["can_run_parallel"] is False
