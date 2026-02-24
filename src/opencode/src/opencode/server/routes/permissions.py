"""
Permissions API routes for OpenCode HTTP server.

Provides endpoints for managing permissions and access control.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter()


# Models
class Permission(BaseModel):
    """Permission model."""
    id: str
    name: str
    description: str
    enabled: bool = True


class PermissionCreate(BaseModel):
    """Model for creating a permission."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    enabled: bool = True


class PermissionUpdate(BaseModel):
    """Model for updating a permission."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    enabled: Optional[bool] = None


# In-memory storage (would be database in production)
_permissions: dict[str, Permission] = {
    "file_read": Permission(id="file_read", name="File Read", description="Read files from the workspace"),
    "file_write": Permission(id="file_write", name="File Write", description="Write files to the workspace"),
    "file_delete": Permission(id="file_delete", name="File Delete", description="Delete files from the workspace"),
    "shell_execute": Permission(id="shell_execute", name="Shell Execute", description="Execute shell commands"),
    "network_access": Permission(id="network_access", name="Network Access", description="Access external network resources"),
    "mcp_connect": Permission(id="mcp_connect", name="MCP Connect", description="Connect to MCP servers"),
}


@router.get("", response_model=list[Permission])
async def list_permissions() -> list[Permission]:
    """
    List all available permissions.
    
    Returns:
        List of all permissions
    """
    return list(_permissions.values())


@router.post("", response_model=Permission, status_code=201)
async def create_permission(permission: PermissionCreate) -> Permission:
    """
    Create a new permission.
    
    Args:
        permission: Permission creation data
        
    Returns:
        Created permission
        
    Raises:
        HTTPException: If permission with same name exists
    """
    # Check for duplicate name
    for existing in _permissions.values():
        if existing.name == permission.name:
            raise HTTPException(status_code=409, detail="Permission with this name already exists")
    
    # Create new permission
    import uuid
    new_permission = Permission(
        id=str(uuid.uuid4()),
        name=permission.name,
        description=permission.description,
        enabled=permission.enabled,
    )
    _permissions[new_permission.id] = new_permission
    
    return new_permission


@router.get("/{permission_id}", response_model=Permission)
async def get_permission(permission_id: str) -> Permission:
    """
    Get a specific permission by ID.
    
    Args:
        permission_id: Permission ID
        
    Returns:
        Permission details
        
    Raises:
        HTTPException: If permission not found
    """
    if permission_id not in _permissions:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    return _permissions[permission_id]


@router.patch("/{permission_id}", response_model=Permission)
async def update_permission(permission_id: str, update: PermissionUpdate) -> Permission:
    """
    Update a permission.
    
    Args:
        permission_id: Permission ID
        update: Permission update data
        
    Returns:
        Updated permission
        
    Raises:
        HTTPException: If permission not found
    """
    if permission_id not in _permissions:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    permission = _permissions[permission_id]
    
    # Apply updates
    if update.name is not None:
        permission.name = update.name
    if update.description is not None:
        permission.description = update.description
    if update.enabled is not None:
        permission.enabled = update.enabled
    
    return permission


@router.delete("/{permission_id}", status_code=204)
async def delete_permission(permission_id: str) -> None:
    """
    Delete a permission.
    
    Args:
        permission_id: Permission ID
        
    Raises:
        HTTPException: If permission not found
    """
    if permission_id not in _permissions:
        raise HTTPException(status_code=404, detail="Permission not found")
    
    del _permissions[permission_id]
