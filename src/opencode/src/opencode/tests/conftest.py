"""
Shared pytest fixtures and configuration for OpenCode tests.

This module provides common fixtures used across all test categories.
"""

import pytest
import asyncio
from typing import Generator, AsyncIterator, Dict, List, Any, Optional, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import tempfile
import os

# Configure asyncio for pytest
pytest_plugins = ('pytest_asyncio',)


# ============================================================================
# Event Loop Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# HTTP Client Mocks
# ============================================================================

@pytest.fixture
def mock_httpx_client():
    """Mock httpx client for provider tests."""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_httpx_response():
    """Mock httpx response."""
    response = MagicMock()
    response.status_code = 200
    response.json = MagicMock(return_value={})
    response.content = b""
    response.text = ""
    return response


# ============================================================================
# Ollama Fixtures
# ============================================================================

@pytest.fixture
def ollama_available() -> bool:
    """Check if Ollama is available locally."""
    import httpx
    try:
        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture
def skip_if_no_ollama(ollama_available: bool):
    """Skip test if Ollama is not available."""
    if not ollama_available:
        pytest.skip("Ollama not available at localhost:11434")


@pytest.fixture
async def ollama_provider(ollama_available: bool):
    """Get Ollama provider instance if available."""
    if not ollama_available:
        pytest.skip("Ollama not available")
    
    from opencode.provider.ollama import OllamaProvider
    provider = OllamaProvider()
    return provider


# ============================================================================
# Provider Fixtures
# ============================================================================

@pytest.fixture
def test_models() -> Dict[str, List[str]]:
    """Models to test across providers."""
    return {
        "ollama": ["llama3.2:3b", "llama3.1:8b", "qwen2.5:7b"],
        "openai": ["gpt-4o-mini", "gpt-4o"],
        "anthropic": ["claude-3-5-sonnet-20241022"],
    }


@pytest.fixture
def providers(request) -> Dict[str, Any]:
    """Get available providers based on configuration."""
    providers = {}
    
    # Always include Ollama if available
    try:
        from opencode.provider.ollama import OllamaProvider
        providers["ollama"] = OllamaProvider()
    except Exception:
        pass
    
    # Include cloud providers if API keys are available
    if os.getenv("OPENAI_API_KEY"):
        try:
            from opencode.provider.openai import OpenAIProvider
            providers["openai"] = OpenAIProvider()
        except Exception:
            pass
    
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            from opencode.provider.anthropic import AnthropicProvider
            providers["anthropic"] = AnthropicProvider()
        except Exception:
            pass
    
    return providers


@pytest.fixture
def mock_provider():
    """Create a mock provider for testing."""
    from opencode.provider.base import Provider, Message, ModelInfo, ToolDefinition, StreamChunk, FinishReason, Usage, CompletionResponse
    
    # Create a mock provider using MagicMock to avoid type issues
    provider = MagicMock(spec=Provider)
    provider.name = "mock"
    provider.models = [
        ModelInfo(
            id="mock-model",
            name="Mock Model",
            provider="mock",
            context_length=4096,
        )
    ]
    
    # Store responses for testing
    _responses: List[str] = []
    
    def set_response(response: str):
        _responses.clear()
        _responses.append(response)
    
    def set_responses(responses: List[str]):
        _responses.clear()
        _responses.extend(responses)
    
    async def complete_sync(
        messages: List[Message],
        model: str,
        tools: Optional[List[ToolDefinition]] = None,
        **kwargs,
    ) -> CompletionResponse:
        content = _responses.pop(0) if _responses else "Mock response"
        return CompletionResponse(
            content=content,
            model=model,
            finish_reason=FinishReason.STOP,
            usage=Usage(input_tokens=10, output_tokens=len(content.split())),
        )
    
    async def count_tokens(text: str, model: str) -> int:
        return len(text.split())
    
    provider.set_response = set_response
    provider.set_responses = set_responses
    provider.complete_sync = complete_sync
    provider.count_tokens = count_tokens
    
    return provider


# ============================================================================
# Prompt Fixtures
# ============================================================================

@pytest.fixture
def test_prompts() -> Dict[str, str]:
    """Standard test prompts for evaluation."""
    return {
        "simple": "What is 2 + 2?",
        "code": "Write a Python function to calculate fibonacci numbers.",
        "reasoning": "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain your reasoning.",
        "creative": "Write a haiku about programming.",
        "tool_use": "What is the weather in Tokyo?",
    }


@pytest.fixture
def comparison_prompts() -> List[Dict[str, Any]]:
    """Prompts to use for comparison testing."""
    return [
        {
            "id": "math_simple",
            "prompt": "What is 15 * 17? Show your work.",
            "expected_contains": ["255", "15", "17"],
        },
        {
            "id": "code_generation",
            "prompt": "Write a Python function that checks if a string is a palindrome.",
            "expected_contains": ["def", "return", "palindrome"],
        },
        {
            "id": "reasoning",
            "prompt": "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
            "expected_contains": ["5 minutes", "5"],
        },
        {
            "id": "explanation",
            "prompt": "Explain the difference between a list and a tuple in Python.",
            "expected_contains": ["mutable", "immutable", "list", "tuple"],
        },
    ]


# ============================================================================
# Context Fixtures
# ============================================================================

@pytest.fixture
def temp_workspace() -> Generator[Path, None, None]:
    """Create a temporary workspace directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files(temp_workspace: Path) -> Dict[str, Path]:
    """Create sample files for testing."""
    files = {}
    
    # Python file
    py_file = temp_workspace / "sample.py"
    py_file.write_text('''
def hello(name: str) -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(hello("World"))
''')
    files["python"] = py_file
    
    # Markdown file
    md_file = temp_workspace / "README.md"
    md_file.write_text('''
# Sample Project

This is a sample project for testing.

## Features

- Feature 1
- Feature 2
''')
    files["markdown"] = md_file
    
    # JSON file
    json_file = temp_workspace / "config.json"
    json_file.write_text('''
{
    "name": "test-project",
    "version": "1.0.0",
    "settings": {
        "debug": true
    }
}
''')
    files["json"] = json_file
    
    return files


# ============================================================================
# Session Fixtures
# ============================================================================

@pytest.fixture
async def mock_session():
    """Create a mock session for testing."""
    from opencode.core.session import Session
    from datetime import datetime
    import uuid
    
    session = Session(
        id=str(uuid.uuid4()),
        project_id=str(uuid.uuid4()),
        title="Test Session",
        directory="/tmp/test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return session


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
async def temp_db():
    """Create a temporary database for testing."""
    from opencode.db.connection import Database
    
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    
    db = Database(db_path)
    await db.init()
    
    yield db
    
    await db.close()
    os.unlink(db_path)


# ============================================================================
# Tool Fixtures
# ============================================================================

@pytest.fixture
def mock_tool():
    """Create a mock tool for testing."""
    from opencode.tool.base import Tool, ToolResult
    
    class MockTool(Tool):
        @property
        def name(self) -> str:
            return "mock_tool"
        
        @property
        def description(self) -> str:
            return "A mock tool for testing"
        
        @property
        def parameters(self) -> dict:
            return {
                "type": "object",
                "properties": {
                    "input": {"type": "string"}
                },
                "required": ["input"]
            }
        
        async def execute(self, input: str = "", **kwargs) -> ToolResult:
            return ToolResult.ok(output=f"Mock tool executed with: {input}")
    
    return MockTool()


@pytest.fixture
def mock_tool_registry(mock_tool):
    """Create a mock tool registry for testing."""
    from opencode.tool.base import ToolRegistry
    
    registry = ToolRegistry()
    registry.register(mock_tool)
    return registry


# ============================================================================
# RAG Fixtures
# ============================================================================

@pytest.fixture
def sample_documents() -> List[Dict[str, Any]]:
    """Sample documents for RAG testing."""
    return [
        {
            "id": "doc1",
            "content": "Python is a programming language known for its simplicity and readability.",
            "metadata": {"source": "intro.txt", "type": "text"},
        },
        {
            "id": "doc2",
            "content": "Machine learning is a subset of artificial intelligence that enables systems to learn from data.",
            "metadata": {"source": "ml.txt", "type": "text"},
        },
        {
            "id": "doc3",
            "content": "FastAPI is a modern web framework for building APIs with Python.",
            "metadata": {"source": "fastapi.txt", "type": "text"},
        },
    ]


@pytest.fixture
def mock_embeddings():
    """Mock embeddings for testing."""
    def generate_embedding(text: str) -> List[float]:
        # Simple mock: generate deterministic embedding based on text hash
        import hashlib
        hash_bytes = hashlib.md5(text.encode()).digest()
        # Generate 768 floats (typical embedding size)
        return [float(b) / 255.0 for b in hash_bytes * 48]  # 768 / 16 = 48
    
    return generate_embedding


# ============================================================================
# MCP Fixtures
# ============================================================================

@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server for testing."""
    from opencode.mcp.server import MCPServer
    
    server = MagicMock(spec=MCPServer)
    server.list_tools = AsyncMock(return_value=[])
    server.call_tool = AsyncMock(return_value={"result": "success"})
    return server


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing."""
    from opencode.mcp.client import MCPClient
    
    client = MagicMock(spec=MCPClient)
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.list_tools = AsyncMock(return_value=[])
    return client


# ============================================================================
# Subagent Fixtures
# ============================================================================

@pytest.fixture
def mock_subagent_manager():
    """Create a mock subagent manager for testing."""
    from opencode.core.subagents.manager import SubagentManager
    
    manager = MagicMock(spec=SubagentManager)
    manager.create_subagent = AsyncMock()
    manager.list_subagents = AsyncMock(return_value=[])
    manager.get_subagent = AsyncMock(return_value=None)
    return manager


# ============================================================================
# Mode Fixtures
# ============================================================================

@pytest.fixture
def mock_mode():
    """Create a mock mode for testing."""
    from opencode.core.modes.base import Mode, ModeConfig, ModeToolAccess
    
    class MockMode(Mode):
        _config = ModeConfig(
            name="mock",
            description="A mock mode for testing",
            tool_access=ModeToolAccess.ALL,
        )
        
        @classmethod
        def get_config(cls) -> ModeConfig:
            return cls._config
    
    return MockMode


# ============================================================================
# Marker Registration
# ============================================================================

def pytest_configure(config):
    """Register custom pytest markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "ollama: marks tests requiring Ollama")
    config.addinivalue_line("markers", "provider: marks tests requiring external providers")
    config.addinivalue_line("markers", "prompt: marks prompt evaluation tests")
    config.addinivalue_line("markers", "e2e: marks end-to-end tests")