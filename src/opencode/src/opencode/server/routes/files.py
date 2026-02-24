"""
Files API routes for OpenCode HTTP server.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from opencode.server.app import get_config


router = APIRouter()


class FileInfo(BaseModel):
    """File information."""
    path: str
    name: str
    is_dir: bool
    size: int
    extension: str


class FileContent(BaseModel):
    """File content response."""
    path: str
    content: str
    size: int
    encoding: str = "utf-8"


class DirectoryListing(BaseModel):
    """Directory listing response."""
    path: str
    files: list[FileInfo]


class FileWriteRequest(BaseModel):
    """File write request."""
    path: str
    content: str
    create_dirs: bool = True


class FileSearchRequest(BaseModel):
    """File search request."""
    pattern: str
    path: Optional[str] = None
    file_pattern: str = "*"


def _get_project_root() -> Path:
    """Get the project root directory."""
    config = get_config()
    return config.project_root


def _resolve_path(path: str) -> Path:
    """Resolve a path relative to project root."""
    project_root = _get_project_root()
    full_path = (project_root / path).resolve()
    
    # Security check - prevent path traversal
    if not str(full_path).startswith(str(project_root.resolve())):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return full_path


@router.get("/list", response_model=DirectoryListing)
async def list_files(path: str = "."):
    """List files in a directory."""
    full_path = _resolve_path(path)
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    
    if not full_path.is_dir():
        raise HTTPException(status_code=400, detail="Not a directory")
    
    files = []
    for item in full_path.iterdir():
        # Skip hidden files and common ignore patterns
        if item.name.startswith("."):
            continue
        if item.name in ["node_modules", "__pycache__", "venv", ".venv"]:
            continue
        
        files.append(FileInfo(
            path=str(item.relative_to(_get_project_root())),
            name=item.name,
            is_dir=item.is_dir(),
            size=item.stat().st_size if item.is_file() else 0,
            extension=item.suffix if item.is_file() else "",
        ))
    
    return DirectoryListing(path=path, files=sorted(files, key=lambda f: (not f.is_dir, f.name)))


@router.get("/read", response_model=FileContent)
async def read_file(path: str):
    """Read a file's content."""
    full_path = _resolve_path(path)
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    # Check file size
    max_size = 10 * 1024 * 1024  # 10 MB
    if full_path.stat().st_size > max_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    try:
        content = full_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="Binary file or unsupported encoding")
    
    return FileContent(
        path=path,
        content=content,
        size=len(content),
    )


@router.post("/write")
async def write_file(request: FileWriteRequest):
    """Write content to a file."""
    full_path = _resolve_path(request.path)
    
    # Create parent directories if needed
    if request.create_dirs:
        full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write content
    full_path.write_text(request.content, encoding="utf-8")
    
    return {
        "status": "ok",
        "path": request.path,
        "size": len(request.content),
    }


@router.delete("/delete")
async def delete_file(path: str):
    """Delete a file or directory."""
    full_path = _resolve_path(path)
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if full_path.is_file():
        full_path.unlink()
    elif full_path.is_dir():
        import shutil
        shutil.rmtree(full_path)
    
    return {"status": "ok", "path": path}


@router.post("/search")
async def search_files(request: FileSearchRequest):
    """Search for files matching a pattern."""
    project_root = _get_project_root()
    search_path = _resolve_path(request.path) if request.path else project_root
    
    if not search_path.exists():
        raise HTTPException(status_code=404, detail="Path not found")
    
    results = []
    for item in search_path.rglob(request.file_pattern):
        if request.pattern.lower() in item.name.lower():
            results.append(str(item.relative_to(project_root)))
    
    return {
        "pattern": request.pattern,
        "results": results[:1000],  # Limit results
        "count": len(results),
    }


@router.get("/download")
async def download_file(path: str):
    """Download a file."""
    full_path = _resolve_path(path)
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not full_path.is_file():
        raise HTTPException(status_code=400, detail="Not a file")
    
    return FileResponse(
        path=full_path,
        filename=full_path.name,
    )


@router.post("/upload")
async def upload_file(
    path: str,
    file: UploadFile = File(...),
):
    """Upload a file."""
    full_path = _resolve_path(path)
    
    # Create parent directories
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write uploaded content
    content = await file.read()
    full_path.write_bytes(content)
    
    return {
        "status": "ok",
        "path": path,
        "size": len(content),
    }


@router.post("/create-directory")
async def create_directory(path: str):
    """Create a directory."""
    full_path = _resolve_path(path)
    full_path.mkdir(parents=True, exist_ok=True)
    
    return {"status": "ok", "path": path}


@router.get("/exists")
async def check_exists(path: str):
    """Check if a file or directory exists."""
    full_path = _resolve_path(path)
    
    return {
        "exists": full_path.exists(),
        "is_file": full_path.is_file() if full_path.exists() else False,
        "is_dir": full_path.is_dir() if full_path.exists() else False,
    }


@router.get("/stat")
async def get_file_stat(path: str):
    """Get file statistics."""
    full_path = _resolve_path(path)
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    stat = full_path.stat()
    
    return {
        "path": path,
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "created": stat.st_ctime,
        "is_file": full_path.is_file(),
        "is_dir": full_path.is_dir(),
    }
