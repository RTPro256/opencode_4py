"""
Tests for permissions API routes.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from opencode.server.routes.permissions import router, Permission, PermissionCreate


@pytest.fixture
def app():
    """Create a FastAPI app with the permissions router."""
    app = FastAPI()
    app.include_router(router, prefix="/api/permissions")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestPermissionsRoutes:
    """Tests for permissions routes."""
    
    @pytest.mark.unit
    def test_list_permissions(self, client):
        """Test listing all permissions."""
        response = client.get("/api/permissions")
        assert response.status_code == 200
        permissions = response.json()
        assert isinstance(permissions, list)
        assert len(permissions) >= 6  # Default permissions
    
    @pytest.mark.unit
    def test_list_permissions_contains_defaults(self, client):
        """Test that default permissions are included."""
        response = client.get("/api/permissions")
        permissions = response.json()
        permission_ids = [p["id"] for p in permissions]
        
        assert "file_read" in permission_ids
        assert "file_write" in permission_ids
        assert "file_delete" in permission_ids
        assert "shell_execute" in permission_ids
    
    @pytest.mark.unit
    def test_get_permission_by_id(self, client):
        """Test getting a specific permission."""
        response = client.get("/api/permissions/file_read")
        assert response.status_code == 200
        permission = response.json()
        assert permission["id"] == "file_read"
        assert permission["name"] == "File Read"
    
    @pytest.mark.unit
    def test_get_permission_not_found(self, client):
        """Test getting a non-existent permission."""
        response = client.get("/api/permissions/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_create_permission(self, client):
        """Test creating a new permission."""
        new_permission = {
            "name": "Test Permission",
            "description": "A test permission",
            "enabled": True
        }
        response = client.post("/api/permissions", json=new_permission)
        assert response.status_code == 201
        permission = response.json()
        assert permission["name"] == "Test Permission"
        assert permission["description"] == "A test permission"
        assert permission["enabled"] is True
        assert "id" in permission
    
    @pytest.mark.unit
    def test_create_permission_duplicate_name(self, client):
        """Test creating a permission with duplicate name."""
        new_permission = {
            "name": "File Read",  # Already exists
            "description": "Duplicate"
        }
        response = client.post("/api/permissions", json=new_permission)
        assert response.status_code == 409
    
    @pytest.mark.unit
    def test_update_permission(self, client):
        """Test updating a permission."""
        update_data = {
            "description": "Updated description"
        }
        response = client.patch("/api/permissions/file_read", json=update_data)
        assert response.status_code == 200
        permission = response.json()
        assert permission["description"] == "Updated description"
    
    @pytest.mark.unit
    def test_update_permission_not_found(self, client):
        """Test updating a non-existent permission."""
        update_data = {"name": "New Name"}
        response = client.patch("/api/permissions/nonexistent", json=update_data)
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_delete_permission(self, client):
        """Test deleting a permission."""
        # First create a permission to delete
        new_permission = {
            "name": "To Delete",
            "description": "Will be deleted"
        }
        create_response = client.post("/api/permissions", json=new_permission)
        permission_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/permissions/{permission_id}")
        assert response.status_code == 204
        
        # Verify it's gone
        get_response = client.get(f"/api/permissions/{permission_id}")
        assert get_response.status_code == 404
    
    @pytest.mark.unit
    def test_delete_permission_not_found(self, client):
        """Test deleting a non-existent permission."""
        response = client.delete("/api/permissions/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.unit
    def test_permission_model_validation(self):
        """Test Permission model validation."""
        permission = Permission(
            id="test",
            name="Test",
            description="Test permission",
            enabled=True
        )
        assert permission.id == "test"
        assert permission.name == "Test"
        assert permission.enabled is True
    
    @pytest.mark.unit
    def test_permission_create_model_defaults(self):
        """Test PermissionCreate model defaults."""
        create = PermissionCreate(name="Test")
        assert create.name == "Test"
        assert create.description == ""
        assert create.enabled is True