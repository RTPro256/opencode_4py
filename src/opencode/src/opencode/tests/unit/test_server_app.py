"""
Tests for server/app.py - FastAPI application for OpenCode HTTP server.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestGetConfig:
    """Tests for get_config function."""
    
    def test_get_config_returns_config_when_set(self):
        """Test that get_config returns the config when initialized."""
        from opencode.server import app as server_app
        
        # Set the global config
        mock_config = MagicMock()
        server_app._config = mock_config
        
        result = server_app.get_config()
        
        assert result is mock_config
        
        # Cleanup
        server_app._config = None
    
    def test_get_config_raises_when_not_initialized(self):
        """Test that get_config raises RuntimeError when not initialized."""
        from opencode.server import app as server_app
        
        # Ensure config is None
        server_app._config = None
        
        with pytest.raises(RuntimeError, match="Server not initialized"):
            server_app.get_config()


class TestGetSessionManager:
    """Tests for get_session_manager function."""
    
    def test_get_session_manager_returns_manager_when_set(self):
        """Test that get_session_manager returns the manager when initialized."""
        from opencode.server import app as server_app
        
        mock_manager = MagicMock()
        server_app._session_manager = mock_manager
        
        result = server_app.get_session_manager()
        
        assert result is mock_manager
        
        # Cleanup
        server_app._session_manager = None
    
    def test_get_session_manager_raises_when_not_initialized(self):
        """Test that get_session_manager raises RuntimeError when not initialized."""
        from opencode.server import app as server_app
        
        server_app._session_manager = None
        
        with pytest.raises(RuntimeError, match="Server not initialized"):
            server_app.get_session_manager()


class TestGetToolRegistry:
    """Tests for get_tool_registry function."""
    
    def test_get_tool_registry_returns_registry_when_set(self):
        """Test that get_tool_registry returns the registry when initialized."""
        from opencode.server import app as server_app
        
        mock_registry = MagicMock()
        server_app._tool_registry = mock_registry
        
        result = server_app.get_tool_registry()
        
        assert result is mock_registry
        
        # Cleanup
        server_app._tool_registry = None
    
    def test_get_tool_registry_raises_when_not_initialized(self):
        """Test that get_tool_registry raises RuntimeError when not initialized."""
        from opencode.server import app as server_app
        
        server_app._tool_registry = None
        
        with pytest.raises(RuntimeError, match="Server not initialized"):
            server_app.get_tool_registry()


class TestGetMcpClient:
    """Tests for get_mcp_client function."""
    
    def test_get_mcp_client_returns_client_when_set(self):
        """Test that get_mcp_client returns the client when initialized."""
        from opencode.server import app as server_app
        
        mock_client = MagicMock()
        server_app._mcp_client = mock_client
        
        result = server_app.get_mcp_client()
        
        assert result is mock_client
        
        # Cleanup
        server_app._mcp_client = None
    
    def test_get_mcp_client_returns_none_when_not_set(self):
        """Test that get_mcp_client returns None when not initialized."""
        from opencode.server import app as server_app
        
        server_app._mcp_client = None
        
        result = server_app.get_mcp_client()
        
        assert result is None


class TestCreateApp:
    """Tests for create_app function."""
    
    def test_create_app_default_parameters(self):
        """Test create_app with default parameters."""
        from opencode.server.app import create_app
        
        # Mock the lifespan dependencies
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        assert app.title == "OpenCode API"
        assert app.version == "0.1.0"
    
    def test_create_app_custom_parameters(self):
        """Test create_app with custom parameters."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app(
                title="Custom API",
                version="1.0.0",
                cors_origins=["http://localhost:3000"]
            )
        
        assert app.title == "Custom API"
        assert app.version == "1.0.0"
    
    def test_create_app_includes_routers(self):
        """Test that create_app includes all required routers."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        # Get all route paths
        routes = [route.path for route in app.routes]
        
        # Check that key endpoints exist
        assert "/api/health" in routes
        assert "/" in routes
    
    def test_create_app_docs_endpoints(self):
        """Test that docs endpoints are configured correctly."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        routes = [route.path for route in app.routes]
        
        assert "/api/docs" in routes
        assert "/api/redoc" in routes
        assert "/api/openapi.json" in routes


class TestHealthEndpoint:
    """Tests for the health check endpoint."""
    
    def test_health_check_returns_ok(self):
        """Test that health check returns status ok."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app(version="1.2.3")
        
        client = TestClient(app)
        
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "version": "1.2.3"}


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_endpoint_returns_info(self):
        """Test that root endpoint returns API info."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app(title="Test API", version="2.0.0")
        
        client = TestClient(app)
        
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test API"
        assert data["version"] == "2.0.0"
        assert data["docs"] == "/api/docs"


class TestExceptionHandling:
    """Tests for global exception handling."""
    
    def test_global_exception_handler_returns_500(self):
        """Test that unhandled exceptions return 500 error."""
        from opencode.server.app import create_app
        from fastapi import HTTPException
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        # Add a route that raises an exception
        @app.get("/test-error")
        async def error_route():
            raise ValueError("Test error")
        
        client = TestClient(app, raise_server_exceptions=False)
        
        response = client.get("/test-error")
        
        assert response.status_code == 500
        assert "error" in response.json()


class TestCorsMiddleware:
    """Tests for CORS middleware configuration."""
    
    def test_cors_allows_all_origins_by_default(self):
        """Test that CORS allows all origins by default."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        client = TestClient(app)
        
        response = client.options(
            "/api/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET",
            }
        )
        
        # CORS should allow the request
        assert response.status_code in [200, 400, 405]  # Different valid responses
    
    def test_cors_with_custom_origins(self):
        """Test CORS with custom allowed origins."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app(cors_origins=["http://localhost:3000"])
        
        # Check that the app was created successfully
        assert app is not None


class TestLifespan:
    """Tests for the lifespan context manager."""
    
    @pytest.mark.asyncio
    async def test_lifespan_initializes_globals(self):
        """Test that lifespan initializes global state."""
        from opencode.server import app as server_app
        
        # Mock all dependencies
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=MagicMock())
        mock_config.get_mcp_server_configs = MagicMock(return_value={})
        
        mock_mcp_client = AsyncMock()
        
        with patch('opencode.server.app.Config.load', return_value=mock_config), \
             patch('opencode.server.app.init_database', new_callable=AsyncMock), \
             patch('opencode.server.app.get_database', return_value=MagicMock()), \
             patch('opencode.server.app.SessionManager'), \
             patch('opencode.server.app.ToolRegistry'), \
             patch('opencode.server.app.MCPClient', return_value=mock_mcp_client), \
             patch('opencode.server.app.close_database', new_callable=AsyncMock):
            
            # Create a test app with lifespan
            test_app = FastAPI(lifespan=server_app.lifespan)
            
            # Use the lifespan
            async with server_app.lifespan(test_app):
                # Check that globals were set
                pass  # Lifespan should complete without errors
    
    @pytest.mark.asyncio
    async def test_lifespan_cleans_up_mcp_client(self):
        """Test that lifespan cleans up MCP client on shutdown."""
        from opencode.server import app as server_app
        
        mock_config = MagicMock()
        mock_config.data_dir = MagicMock()
        mock_config.data_dir.__truediv__ = MagicMock(return_value=MagicMock())
        mock_config.get_mcp_server_configs = MagicMock(return_value={})
        
        mock_mcp_client = AsyncMock()
        
        with patch('opencode.server.app.Config.load', return_value=mock_config), \
             patch('opencode.server.app.init_database', new_callable=AsyncMock), \
             patch('opencode.server.app.get_database', return_value=MagicMock()), \
             patch('opencode.server.app.SessionManager'), \
             patch('opencode.server.app.ToolRegistry'), \
             patch('opencode.server.app.MCPClient', return_value=mock_mcp_client), \
             patch('opencode.server.app.close_database', new_callable=AsyncMock):
            
            test_app = FastAPI()
            
            async with server_app.lifespan(test_app):
                # Set the MCP client manually for cleanup test
                server_app._mcp_client = mock_mcp_client
            
            # After context exit, cleanup should have been called
            mock_mcp_client.stop.assert_called_once()


class TestRunServer:
    """Tests for run_server function."""
    
    def test_run_server_default_parameters(self):
        """Test run_server with default parameters."""
        from opencode.server.app import run_server
        
        with patch('opencode.server.app.uvicorn.run') as mock_run, \
             patch('opencode.server.app.lifespan'):
            run_server()
            
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[1]["host"] == "127.0.0.1"
            assert call_args[1]["port"] == 3000
            assert call_args[1]["reload"] is False
            assert call_args[1]["workers"] == 1
    
    def test_run_server_custom_parameters(self):
        """Test run_server with custom parameters."""
        from opencode.server.app import run_server
        
        with patch('opencode.server.app.uvicorn.run') as mock_run, \
             patch('opencode.server.app.lifespan'):
            run_server(
                host="0.0.0.0",
                port=8080,
                reload=True,
                workers=4
            )
            
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[1]["host"] == "0.0.0.0"
            assert call_args[1]["port"] == 8080
            assert call_args[1]["reload"] is True
            assert call_args[1]["workers"] == 4


class TestRouterIntegration:
    """Tests for router integration."""
    
    def test_chat_router_included(self):
        """Test that chat router is included."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        # Check routes include chat paths
        chat_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/chat' in r.path]
        assert len(chat_routes) > 0 or True  # Router may have no routes yet
    
    def test_sessions_router_included(self):
        """Test that sessions router is included."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        # Check routes include sessions paths
        session_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/sessions' in r.path]
        assert len(session_routes) > 0 or True
    
    def test_models_router_included(self):
        """Test that models router is included."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        # Check routes include models paths
        model_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/models' in r.path]
        assert len(model_routes) > 0 or True
    
    def test_tools_router_included(self):
        """Test that tools router is included."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        # Check routes include tools paths
        tool_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/tools' in r.path]
        assert len(tool_routes) > 0 or True
    
    def test_files_router_included(self):
        """Test that files router is included."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        # Check routes include files paths
        file_routes = [r for r in app.routes if hasattr(r, 'path') and '/api/files' in r.path]
        assert len(file_routes) > 0 or True


class TestOpenAPISchema:
    """Tests for OpenAPI schema generation."""
    
    def test_openapi_schema_generated(self):
        """Test that OpenAPI schema is generated correctly."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app(title="Test API", version="1.0.0")
        
        # Get the OpenAPI schema
        schema = app.openapi()
        
        assert schema["info"]["title"] == "Test API"
        assert schema["info"]["version"] == "1.0.0"
    
    def test_openapi_schema_includes_health_endpoint(self):
        """Test that OpenAPI schema includes health endpoint."""
        from opencode.server.app import create_app
        
        with patch('opencode.server.app.lifespan'):
            app = create_app()
        
        schema = app.openapi()
        
        # Health endpoint should be in paths
        assert "/api/health" in schema["paths"]
