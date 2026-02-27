"""
Tests for server/routes/files.py.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import tempfile
import os

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from opencode.server.routes.files import (
    router,
    FileInfo,
    FileContent,
    DirectoryListing,
    FileWriteRequest,
    FileSearchRequest,
    _resolve_path,
)


@pytest.fixture
def app():
    """Create a FastAPI app with the files router."""
    app = FastAPI()
    app.include_router(router, prefix="/files")
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_config():
    """Create a mock config with a temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config = MagicMock()
        config.project_root = Path(tmpdir)
        yield config, tmpdir


class TestFileInfo:
    """Tests for FileInfo model."""

    def test_file_info_creation(self):
        """Test creating FileInfo."""
        info = FileInfo(
            path="test.py",
            name="test.py",
            is_dir=False,
            size=100,
            extension=".py",
        )
        assert info.path == "test.py"
        assert info.is_dir is False


class TestFileContent:
    """Tests for FileContent model."""

    def test_file_content_creation(self):
        """Test creating FileContent."""
        content = FileContent(
            path="test.py",
            content="print('hello')",
            size=15,
        )
        assert content.path == "test.py"
        assert content.encoding == "utf-8"


class TestDirectoryListing:
    """Tests for DirectoryListing model."""

    def test_directory_listing_creation(self):
        """Test creating DirectoryListing."""
        listing = DirectoryListing(
            path=".",
            files=[
                FileInfo(path="test.py", name="test.py", is_dir=False, size=100, extension=".py")
            ],
        )
        assert listing.path == "."
        assert len(listing.files) == 1


class TestFileWriteRequest:
    """Tests for FileWriteRequest model."""

    def test_file_write_request_creation(self):
        """Test creating FileWriteRequest."""
        request = FileWriteRequest(
            path="test.py",
            content="print('hello')",
        )
        assert request.path == "test.py"
        assert request.create_dirs is True


class TestFileSearchRequest:
    """Tests for FileSearchRequest model."""

    def test_file_search_request_creation(self):
        """Test creating FileSearchRequest."""
        request = FileSearchRequest(
            pattern="test",
        )
        assert request.pattern == "test"
        assert request.path is None
        assert request.file_pattern == "*"


class TestResolvePath:
    """Tests for _resolve_path function."""

    def test_resolve_path_valid(self, mock_config):
        """Test resolving a valid path."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            result = _resolve_path("test.py")
            assert str(result).startswith(tmpdir)

    def test_resolve_path_traversal_attack(self, mock_config):
        """Test that path traversal is blocked."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            with pytest.raises(HTTPException) as exc_info:
                _resolve_path("../../../etc/passwd")
            assert exc_info.value.status_code == 403


class TestListFiles:
    """Tests for list_files endpoint."""

    def test_list_files_empty_dir(self, mock_config):
        """Test listing an empty directory."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/list?path=.")
            
            assert response.status_code == 200
            data = response.json()
            assert data["path"] == "."
            assert isinstance(data["files"], list)

    def test_list_files_with_files(self, mock_config):
        """Test listing a directory with files."""
        config, tmpdir = mock_config
        # Create some test files
        (Path(tmpdir) / "test1.py").write_text("print('test1')")
        (Path(tmpdir) / "test2.txt").write_text("test2")
        os.makedirs(Path(tmpdir) / "subdir", exist_ok=True)
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/list?path=.")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["files"]) >= 2

    def test_list_files_not_found(self, mock_config):
        """Test listing a non-existent directory."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/list?path=nonexistent")
            
            assert response.status_code == 404

    def test_list_files_not_directory(self, mock_config):
        """Test listing a file instead of directory."""
        config, tmpdir = mock_config
        (Path(tmpdir) / "test.txt").write_text("test")
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/list?path=test.txt")
            
            assert response.status_code == 400


class TestReadFile:
    """Tests for read_file endpoint."""

    def test_read_file_success(self, mock_config):
        """Test reading a file successfully."""
        config, tmpdir = mock_config
        (Path(tmpdir) / "test.txt").write_text("Hello, World!")
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/read?path=test.txt")
            
            assert response.status_code == 200
            data = response.json()
            assert data["content"] == "Hello, World!"

    def test_read_file_not_found(self, mock_config):
        """Test reading a non-existent file."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/read?path=nonexistent.txt")
            
            assert response.status_code == 404

    def test_read_file_is_directory(self, mock_config):
        """Test reading a directory."""
        config, tmpdir = mock_config
        os.makedirs(Path(tmpdir) / "testdir", exist_ok=True)
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/read?path=testdir")
            
            assert response.status_code == 400


class TestWriteFile:
    """Tests for write_file endpoint."""

    def test_write_file_success(self, mock_config):
        """Test writing a file successfully."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.post(
                "/files/write",
                json={"path": "newfile.txt", "content": "New content"}
            )
            
            assert response.status_code == 200
            assert (Path(tmpdir) / "newfile.txt").exists()
            assert (Path(tmpdir) / "newfile.txt").read_text() == "New content"

    def test_write_file_create_dirs(self, mock_config):
        """Test writing a file with directory creation."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.post(
                "/files/write",
                json={
                    "path": "subdir/newfile.txt",
                    "content": "New content",
                    "create_dirs": True
                }
            )
            
            assert response.status_code == 200
            assert (Path(tmpdir) / "subdir" / "newfile.txt").exists()


class TestDeleteFile:
    """Tests for delete_file endpoint."""

    def test_delete_file_success(self, mock_config):
        """Test deleting a file successfully."""
        config, tmpdir = mock_config
        test_file = Path(tmpdir) / "todelete.txt"
        test_file.write_text("delete me")
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.delete("/files/delete?path=todelete.txt")
            
            assert response.status_code == 200
            assert not test_file.exists()

    def test_delete_directory_success(self, mock_config):
        """Test deleting a directory successfully."""
        config, tmpdir = mock_config
        test_dir = Path(tmpdir) / "todelete"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("content")
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.delete("/files/delete?path=todelete")
            
            assert response.status_code == 200
            assert not test_dir.exists()

    def test_delete_file_not_found(self, mock_config):
        """Test deleting a non-existent file."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.delete("/files/delete?path=nonexistent.txt")
            
            assert response.status_code == 404


class TestSearchFiles:
    """Tests for search_files endpoint."""

    def test_search_files_success(self, mock_config):
        """Test searching for files."""
        config, tmpdir = mock_config
        (Path(tmpdir) / "test1.py").write_text("test")
        (Path(tmpdir) / "test2.py").write_text("test")
        (Path(tmpdir) / "other.txt").write_text("test")
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.post(
                "/files/search",
                json={"pattern": "test"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) >= 2

    def test_search_files_not_found(self, mock_config):
        """Test searching in non-existent path."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.post(
                "/files/search",
                json={"pattern": "test", "path": "nonexistent"}
            )
            
            assert response.status_code == 404


class TestCheckExists:
    """Tests for check_exists endpoint."""

    def test_check_exists_true(self, mock_config):
        """Test checking if file exists (true)."""
        config, tmpdir = mock_config
        (Path(tmpdir) / "exists.txt").write_text("test")
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/exists?path=exists.txt")
            
            assert response.status_code == 200
            data = response.json()
            assert data["exists"] is True
            assert data["is_file"] is True

    def test_check_exists_false(self, mock_config):
        """Test checking if file exists (false)."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/exists?path=nonexistent.txt")
            
            assert response.status_code == 200
            data = response.json()
            assert data["exists"] is False


class TestCreateDirectory:
    """Tests for create_directory endpoint."""

    def test_create_directory_success(self, mock_config):
        """Test creating a directory."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.post("/files/create-directory?path=newdir")
            
            assert response.status_code == 200
            assert (Path(tmpdir) / "newdir").exists()

    def test_create_nested_directory(self, mock_config):
        """Test creating nested directories."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.post("/files/create-directory?path=parent/child/grandchild")
            
            assert response.status_code == 200
            assert (Path(tmpdir) / "parent" / "child" / "grandchild").exists()


class TestGetFileStat:
    """Tests for get_file_stat endpoint."""

    def test_get_file_stat_success(self, mock_config):
        """Test getting file stats."""
        config, tmpdir = mock_config
        (Path(tmpdir) / "stat_test.txt").write_text("test content")
        
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/stat?path=stat_test.txt")
            
            assert response.status_code == 200
            data = response.json()
            assert "size" in data
            assert "modified" in data

    def test_get_file_stat_not_found(self, mock_config):
        """Test getting stats for non-existent file."""
        config, tmpdir = mock_config
        with patch("opencode.server.routes.files.get_config", return_value=config):
            app = FastAPI()
            from opencode.server.routes.files import router
            app.include_router(router, prefix="/files")
            client = TestClient(app)
            
            response = client.get("/files/stat?path=nonexistent.txt")
            
            assert response.status_code == 404
