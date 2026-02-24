"""
Tests for tool base classes and registry.
"""

import pytest
from typing import Any, Optional

from opencode.tool.base import (
    PermissionLevel,
    ToolResult,
    Tool,
    ToolRegistry,
    get_registry,
    register_tool,
    get_tool,
)


class TestPermissionLevel:
    """Tests for PermissionLevel enum."""

    def test_permission_levels_exist(self):
        """Test that all permission levels exist."""
        assert PermissionLevel.READ.value == "read"
        assert PermissionLevel.WRITE.value == "write"
        assert PermissionLevel.EXECUTE.value == "execute"
        assert PermissionLevel.DANGEROUS.value == "dangerous"

    def test_permission_level_is_string(self):
        """Test that PermissionLevel is a string enum."""
        assert PermissionLevel.READ == "read"
        assert isinstance(PermissionLevel.READ, str)


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_success_result(self):
        """Test creating a successful result."""
        result = ToolResult.ok(output="Success output")
        
        assert result.output == "Success output"
        assert result.error is None
        assert result.success is True
        assert result.metadata == {}
        assert result.files_changed == []
        assert result.requires_permission is False

    def test_error_result(self):
        """Test creating an error result."""
        result = ToolResult.err(error="Something went wrong")
        
        assert result.output == ""
        assert result.error == "Something went wrong"
        assert result.success is False

    def test_error_result_with_output(self):
        """Test creating an error result with output."""
        result = ToolResult.err(error="Error", output="Partial output")
        
        assert result.output == "Partial output"
        assert result.error == "Error"
        assert result.success is False

    def test_result_with_metadata(self):
        """Test result with metadata."""
        result = ToolResult.ok(
            output="Output",
            metadata={"key": "value", "count": 42},
        )
        
        assert result.metadata == {"key": "value", "count": 42}

    def test_result_with_files_changed(self):
        """Test result with files changed."""
        result = ToolResult.ok(
            output="Modified files",
            files_changed=["/path/to/file1.py", "/path/to/file2.py"],
        )
        
        assert result.files_changed == ["/path/to/file1.py", "/path/to/file2.py"]

    def test_result_requires_permission(self):
        """Test result that requires permission."""
        result = ToolResult.ok(
            output="Output",
            requires_permission=True,
        )
        
        assert result.requires_permission is True

    def test_to_dict_success(self):
        """Test converting successful result to dict."""
        result = ToolResult.ok(
            output="Output",
            metadata={"key": "value"},
            files_changed=["/file.py"],
        )
        
        d = result.to_dict()
        
        assert d["output"] == "Output"
        assert d["error"] is None
        assert d["metadata"] == {"key": "value"}
        assert d["files_changed"] == ["/file.py"]
        assert d["success"] is True

    def test_to_dict_error(self):
        """Test converting error result to dict."""
        result = ToolResult.err(error="Error message")
        
        d = result.to_dict()
        
        assert d["output"] == ""
        assert d["error"] == "Error message"
        assert d["success"] is False


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(
        self,
        name: str = "mock_tool",
        description: str = "A mock tool",
        permission_level: PermissionLevel = PermissionLevel.READ,
    ):
        self._name = name
        self._description = description
        self._permission_level = permission_level
        self._execute_result = ToolResult.ok("Mock output")

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input parameter",
                },
                "count": {
                    "type": "integer",
                    "description": "Count parameter",
                },
            },
            "required": ["input"],
        }

    @property
    def permission_level(self) -> PermissionLevel:
        return self._permission_level

    def set_execute_result(self, result: ToolResult):
        self._execute_result = result

    async def execute(self, **params: Any) -> ToolResult:
        return self._execute_result


class TestTool:
    """Tests for Tool abstract base class."""

    def test_tool_name(self):
        """Test tool name property."""
        tool = MockTool(name="test_tool")
        assert tool.name == "test_tool"

    def test_tool_description(self):
        """Test tool description property."""
        tool = MockTool(description="Test description")
        assert tool.description == "Test description"

    def test_tool_parameters(self):
        """Test tool parameters property."""
        tool = MockTool()
        params = tool.parameters
        
        assert params["type"] == "object"
        assert "input" in params["properties"]
        assert "count" in params["properties"]
        assert params["required"] == ["input"]

    def test_tool_permission_level_default(self):
        """Test default permission level."""
        tool = MockTool()
        assert tool.permission_level == PermissionLevel.READ

    def test_tool_permission_level_custom(self):
        """Test custom permission level."""
        tool = MockTool(permission_level=PermissionLevel.DANGEROUS)
        assert tool.permission_level == PermissionLevel.DANGEROUS

    def test_tool_required_permissions_default(self):
        """Test default required permissions."""
        tool = MockTool()
        assert tool.required_permissions == []

    def test_tool_is_dangerous_read(self):
        """Test is_dangerous for READ permission."""
        tool = MockTool(permission_level=PermissionLevel.READ)
        assert tool.is_dangerous is False

    def test_tool_is_dangerous_write(self):
        """Test is_dangerous for WRITE permission."""
        tool = MockTool(permission_level=PermissionLevel.WRITE)
        assert tool.is_dangerous is True

    def test_tool_is_dangerous_execute(self):
        """Test is_dangerous for EXECUTE permission."""
        tool = MockTool(permission_level=PermissionLevel.EXECUTE)
        assert tool.is_dangerous is True

    def test_tool_is_dangerous_dangerous(self):
        """Test is_dangerous for DANGEROUS permission."""
        tool = MockTool(permission_level=PermissionLevel.DANGEROUS)
        assert tool.is_dangerous is True

    def test_to_openai_tool(self):
        """Test converting to OpenAI tool format."""
        tool = MockTool(name="test", description="Test tool")
        
        openai_tool = tool.to_openai_tool()
        
        assert openai_tool["type"] == "function"
        assert openai_tool["function"]["name"] == "test"
        assert openai_tool["function"]["description"] == "Test tool"
        assert openai_tool["function"]["parameters"] == tool.parameters

    def test_to_anthropic_tool(self):
        """Test converting to Anthropic tool format."""
        tool = MockTool(name="test", description="Test tool")
        
        anthropic_tool = tool.to_anthropic_tool()
        
        assert anthropic_tool["name"] == "test"
        assert anthropic_tool["description"] == "Test tool"
        assert anthropic_tool["input_schema"] == tool.parameters

    def test_validate_params_valid(self):
        """Test validating valid parameters."""
        tool = MockTool()
        
        error = tool.validate_params({"input": "test", "count": 5})
        
        assert error is None

    def test_validate_params_missing_required(self):
        """Test validating with missing required parameter."""
        tool = MockTool()
        
        error = tool.validate_params({"count": 5})
        
        assert error is not None
        assert "Missing required parameter" in error
        assert "input" in error

    def test_validate_params_wrong_type_string(self):
        """Test validating with wrong type for string parameter."""
        tool = MockTool()
        
        error = tool.validate_params({"input": 123})
        
        assert error is not None
        assert "wrong type" in error

    def test_validate_params_wrong_type_integer(self):
        """Test validating with wrong type for integer parameter."""
        tool = MockTool()
        
        error = tool.validate_params({"input": "test", "count": "not an int"})
        
        assert error is not None
        assert "wrong type" in error

    def test_validate_params_extra_param(self):
        """Test validating with extra parameter (should be OK)."""
        tool = MockTool()
        
        error = tool.validate_params({"input": "test", "extra": "value"})
        
        assert error is None

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test executing a tool."""
        tool = MockTool()
        tool.set_execute_result(ToolResult.ok("Custom output"))
        
        result = await tool.execute(input="test")
        
        assert result.output == "Custom output"
        assert result.success is True


class TestToolRegistry:
    """Tests for ToolRegistry."""

    def test_create_registry(self):
        """Test creating a registry."""
        registry = ToolRegistry()
        
        assert registry.list_tools() == []

    def test_register_tool(self):
        """Test registering a tool."""
        registry = ToolRegistry()
        tool = MockTool(name="tool1")
        
        registry.register(tool)
        
        assert "tool1" in registry
        assert registry.get("tool1") == tool

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        registry = ToolRegistry()
        tool = MockTool(name="tool1")
        registry.register(tool)
        
        result = registry.unregister("tool1")
        
        assert result is True
        assert "tool1" not in registry

    def test_unregister_nonexistent(self):
        """Test unregistering a non-existent tool."""
        registry = ToolRegistry()
        
        result = registry.unregister("nonexistent")
        
        assert result is False

    def test_get_tool(self):
        """Test getting a tool by name."""
        registry = ToolRegistry()
        tool = MockTool(name="tool1")
        registry.register(tool)
        
        result = registry.get("tool1")
        
        assert result == tool

    def test_get_nonexistent_tool(self):
        """Test getting a non-existent tool."""
        registry = ToolRegistry()
        
        result = registry.get("nonexistent")
        
        assert result is None

    def test_list_tools(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        tool1 = MockTool(name="tool1")
        tool2 = MockTool(name="tool2")
        
        registry.register(tool1)
        registry.register(tool2)
        
        tools = registry.list_tools()
        
        assert len(tools) == 2
        assert tool1 in tools
        assert tool2 in tools

    def test_getitem(self):
        """Test bracket access to tools."""
        registry = ToolRegistry()
        tool = MockTool(name="tool1")
        registry.register(tool)
        
        result = registry["tool1"]
        
        assert result == tool

    def test_get_tools_for_provider_openai(self):
        """Test getting tools in OpenAI format."""
        registry = ToolRegistry()
        tool = MockTool(name="tool1", description="Test tool")
        registry.register(tool)
        
        tools = registry.get_tools_for_provider("openai")
        
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "tool1"

    def test_get_tools_for_provider_anthropic(self):
        """Test getting tools in Anthropic format."""
        registry = ToolRegistry()
        tool = MockTool(name="tool1", description="Test tool")
        registry.register(tool)
        
        tools = registry.get_tools_for_provider("anthropic")
        
        assert len(tools) == 1
        assert tools[0]["name"] == "tool1"
        assert "input_schema" in tools[0]

    @pytest.mark.asyncio
    async def test_execute_tool(self):
        """Test executing a tool through registry."""
        registry = ToolRegistry()
        tool = MockTool(name="tool1")
        tool.set_execute_result(ToolResult.ok("Executed"))
        registry.register(tool)
        
        result = await registry.execute("tool1", {"input": "test"})
        
        assert result.output == "Executed"
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execute_unknown_tool(self):
        """Test executing an unknown tool."""
        registry = ToolRegistry()
        
        result = await registry.execute("unknown", {"input": "test"})
        
        assert result.success is False
        assert "Unknown tool" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_invalid_params(self):
        """Test executing with invalid parameters."""
        registry = ToolRegistry()
        tool = MockTool(name="tool1")
        registry.register(tool)
        
        result = await registry.execute("tool1", {})  # Missing required 'input'
        
        assert result.success is False
        assert "Missing required parameter" in result.error

    @pytest.mark.asyncio
    async def test_execute_with_exception(self):
        """Test executing a tool that raises an exception."""
        registry = ToolRegistry()
        
        class FailingTool(Tool):
            @property
            def name(self) -> str:
                return "failing"
            
            @property
            def description(self) -> str:
                return "A failing tool"
            
            @property
            def parameters(self) -> dict[str, Any]:
                return {"type": "object", "properties": {}}
            
            async def execute(self, **params: Any) -> ToolResult:
                raise RuntimeError("Tool failed!")
        
        registry.register(FailingTool())
        
        result = await registry.execute("failing", {})
        
        assert result.success is False
        assert "Tool execution failed" in result.error


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_get_registry_singleton(self):
        """Test that get_registry returns a singleton."""
        # Reset the global registry
        import opencode.tool.base as base_module
        base_module._registry = None
        
        registry1 = get_registry()
        registry2 = get_registry()
        
        assert registry1 is registry2

    def test_register_tool_global(self):
        """Test registering a tool globally."""
        import opencode.tool.base as base_module
        base_module._registry = None
        
        tool = MockTool(name="global_tool")
        register_tool(tool)
        
        assert get_registry().get("global_tool") == tool

    def test_get_tool_global(self):
        """Test getting a tool globally."""
        import opencode.tool.base as base_module
        base_module._registry = None
        
        tool = MockTool(name="global_tool2")
        register_tool(tool)
        
        result = get_tool("global_tool2")
        
        assert result == tool

    def test_get_tool_nonexistent_global(self):
        """Test getting a non-existent tool globally."""
        import opencode.tool.base as base_module
        base_module._registry = None
        
        result = get_tool("nonexistent")
        
        assert result is None


class TestToolTypeChecking:
    """Tests for tool type checking."""

    def test_check_type_string(self):
        """Test type checking for string."""
        tool = MockTool()
        
        assert tool._check_type("hello", "string") is True
        assert tool._check_type(123, "string") is False

    def test_check_type_integer(self):
        """Test type checking for integer."""
        tool = MockTool()
        
        assert tool._check_type(42, "integer") is True
        assert tool._check_type(42.0, "integer") is False  # float is not int
        assert tool._check_type("42", "integer") is False

    def test_check_type_number(self):
        """Test type checking for number."""
        tool = MockTool()
        
        assert tool._check_type(42, "number") is True
        assert tool._check_type(3.14, "number") is True
        assert tool._check_type("42", "number") is False

    def test_check_type_boolean(self):
        """Test type checking for boolean."""
        tool = MockTool()
        
        assert tool._check_type(True, "boolean") is True
        assert tool._check_type(False, "boolean") is True
        assert tool._check_type(1, "boolean") is False
        assert tool._check_type("true", "boolean") is False

    def test_check_type_array(self):
        """Test type checking for array."""
        tool = MockTool()
        
        assert tool._check_type([1, 2, 3], "array") is True
        assert tool._check_type([], "array") is True
        assert tool._check_type((1, 2), "array") is False

    def test_check_type_object(self):
        """Test type checking for object."""
        tool = MockTool()
        
        assert tool._check_type({"key": "value"}, "object") is True
        assert tool._check_type({}, "object") is True
        assert tool._check_type([1, 2], "object") is False

    def test_check_type_null(self):
        """Test type checking for null."""
        tool = MockTool()
        
        assert tool._check_type(None, "null") is True
        assert tool._check_type(0, "null") is False
        assert tool._check_type("", "null") is False

    def test_check_type_unknown(self):
        """Test type checking for unknown type."""
        tool = MockTool()
        
        # Unknown types should pass validation
        assert tool._check_type("anything", "unknown_type") is True
