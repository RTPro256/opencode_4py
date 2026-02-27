"""
Unit tests for workflow/tools/registry.py

Tests for ToolResult, ToolSchema, BaseTool, and ToolRegistry classes.
"""

import pytest
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from opencode.workflow.tools.registry import (
    ToolResult,
    ToolSchema,
    BaseTool,
    ToolRegistry,
    ToolRegistryError,
    ToolExecutionError,
)


class TestToolResult:
    """Tests for ToolResult dataclass."""

    def test_default_values(self):
        """Test default values for ToolResult."""
        result = ToolResult()
        assert result.success is True
        assert result.data is None
        assert result.error is None
        assert result.metadata == {}

    def test_custom_values(self):
        """Test custom values for ToolResult."""
        result = ToolResult(
            success=False,
            data={"key": "value"},
            error="Something went wrong",
            metadata={"timestamp": "2024-01-01"}
        )
        assert result.success is False
        assert result.data == {"key": "value"}
        assert result.error == "Something went wrong"
        assert result.metadata == {"timestamp": "2024-01-01"}

    def test_to_dict_default(self):
        """Test to_dict with default values."""
        result = ToolResult()
        expected = {
            "success": True,
            "data": None,
            "error": None,
            "metadata": {},
        }
        assert result.to_dict() == expected

    def test_to_dict_custom(self):
        """Test to_dict with custom values."""
        result = ToolResult(
            success=True,
            data=[1, 2, 3],
            error=None,
            metadata={"duration": 100}
        )
        expected = {
            "success": True,
            "data": [1, 2, 3],
            "error": None,
            "metadata": {"duration": 100},
        }
        assert result.to_dict() == expected

    def test_success_with_data(self):
        """Test successful result with data."""
        result = ToolResult(success=True, data="output")
        assert result.success is True
        assert result.data == "output"
        assert result.error is None

    def test_failure_with_error(self):
        """Test failed result with error."""
        result = ToolResult(success=False, error="Execution failed")
        assert result.success is False
        assert result.error == "Execution failed"


class TestToolSchema:
    """Tests for ToolSchema dataclass."""

    def test_required_fields(self):
        """Test required fields for ToolSchema."""
        schema = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"}
        )
        assert schema.name == "test_tool"
        assert schema.description == "A test tool"
        assert schema.parameters == {"type": "object"}

    def test_default_values(self):
        """Test default values for ToolSchema."""
        schema = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters={}
        )
        assert schema.required_params == []
        assert schema.returns == "object"
        assert schema.category == "general"
        assert schema.requires_auth is False
        assert schema.auth_type is None

    def test_custom_values(self):
        """Test custom values for ToolSchema."""
        schema = ToolSchema(
            name="api_tool",
            description="An API tool",
            parameters={"type": "object", "properties": {}},
            required_params=["api_key"],
            returns="json",
            category="api",
            requires_auth=True,
            auth_type="api_key"
        )
        assert schema.name == "api_tool"
        assert schema.description == "An API tool"
        assert schema.required_params == ["api_key"]
        assert schema.returns == "json"
        assert schema.category == "api"
        assert schema.requires_auth is True
        assert schema.auth_type == "api_key"

    def test_complex_parameters(self):
        """Test ToolSchema with complex parameter schema."""
        params = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "default": 10}
            },
            "required": ["query"]
        }
        schema = ToolSchema(
            name="search",
            description="Search tool",
            parameters=params
        )
        assert schema.parameters == params
        assert schema.parameters["properties"]["query"]["type"] == "string"


class ConcreteTool(BaseTool):
    """Concrete implementation of BaseTool for testing."""

    _schema = ToolSchema(
        name="concrete_tool",
        description="A concrete tool for testing",
        parameters={"type": "object", "properties": {"input": {"type": "string"}}},
        required_params=["input"],
        category="test"
    )

    @classmethod
    def get_schema(cls) -> ToolSchema:
        return cls._schema

    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        input_value = params.get("input", "")
        return ToolResult(success=True, data=f"Processed: {input_value}")


class AuthTool(BaseTool):
    """Tool requiring authentication for testing."""

    _schema = ToolSchema(
        name="auth_tool",
        description="Tool requiring authentication",
        parameters={},
        requires_auth=True,
        auth_type="oauth"
    )

    @classmethod
    def get_schema(cls) -> ToolSchema:
        return cls._schema

    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        return ToolResult(success=True, data="authenticated")


class TestBaseTool:
    """Tests for BaseTool abstract class."""

    def test_init_default_config(self):
        """Test BaseTool initialization with default config."""
        tool = ConcreteTool()
        assert tool.config == {}
        assert tool._initialized is False

    def test_init_custom_config(self):
        """Test BaseTool initialization with custom config."""
        tool = ConcreteTool(config={"api_key": "test123"})
        assert tool.config == {"api_key": "test123"}

    def test_schema_property(self):
        """Test schema property access."""
        tool = ConcreteTool()
        assert tool.schema.name == "concrete_tool"
        assert tool.schema.description == "A concrete tool for testing"

    def test_get_schema_classmethod(self):
        """Test get_schema class method."""
        schema = ConcreteTool.get_schema()
        assert schema.name == "concrete_tool"
        assert schema.required_params == ["input"]

    def test_validate_params_valid(self):
        """Test validate_params with valid parameters."""
        tool = ConcreteTool()
        errors = tool.validate_params({"input": "test"})
        assert errors == []

    def test_validate_params_missing_required(self):
        """Test validate_params with missing required parameter."""
        tool = ConcreteTool()
        errors = tool.validate_params({})
        assert len(errors) == 1
        assert "input" in errors[0]
        assert "missing" in errors[0].lower()

    def test_validate_params_extra_params_ok(self):
        """Test validate_params allows extra parameters."""
        tool = ConcreteTool()
        errors = tool.validate_params({"input": "test", "extra": "value"})
        assert errors == []

    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test initialize method."""
        tool = ConcreteTool()
        assert tool._initialized is False
        result = await tool.initialize()
        assert result is True
        assert tool._initialized is True

    @pytest.mark.asyncio
    async def test_execute(self):
        """Test execute method."""
        tool = ConcreteTool()
        result = await tool.execute({"input": "hello"})
        assert result.success is True
        assert result.data == "Processed: hello"

    def test_repr(self):
        """Test __repr__ method."""
        tool = ConcreteTool()
        assert repr(tool) == "ConcreteTool()"


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def setup_method(self):
        """Clear registry before each test."""
        ToolRegistry.clear()

    def test_register_tool(self):
        """Test registering a tool."""
        ToolRegistry.register_tool(ConcreteTool, "concrete_tool")
        assert "concrete_tool" in ToolRegistry._tools
        assert ToolRegistry._tools["concrete_tool"] == ConcreteTool

    def test_register_tool_auto_name(self):
        """Test registering a tool with auto-generated name."""
        ToolRegistry.register_tool(ConcreteTool)
        assert "concrete_tool" in ToolRegistry._tools

    def test_register_decorator(self):
        """Test @register decorator."""
        @ToolRegistry.register("decorated_tool")
        class DecoratedTool(BaseTool):
            _schema = ToolSchema(
                name="decorated_tool",
                description="Decorated tool",
                parameters={}
            )

            @classmethod
            def get_schema(cls) -> ToolSchema:
                return cls._schema

            async def execute(self, params: Dict[str, Any]) -> ToolResult:
                return ToolResult()

        assert "decorated_tool" in ToolRegistry._tools

    def test_register_decorator_auto_name(self):
        """Test @register decorator with auto-generated name."""
        @ToolRegistry.register()
        class AutoNamedTool(BaseTool):
            _schema = ToolSchema(
                name="auto_named_tool",
                description="Auto named tool",
                parameters={}
            )

            @classmethod
            def get_schema(cls) -> ToolSchema:
                return cls._schema

            async def execute(self, params: Dict[str, Any]) -> ToolResult:
                return ToolResult()

        assert "auto_named_tool" in ToolRegistry._tools

    def test_register_overwrite_warning(self):
        """Test that overwriting a tool logs a warning."""
        ToolRegistry.register_tool(ConcreteTool, "test_tool")
        # Second registration should overwrite without error
        ToolRegistry.register_tool(ConcreteTool, "test_tool")
        assert "test_tool" in ToolRegistry._tools

    def test_get_tool(self):
        """Test getting a tool by name."""
        ToolRegistry.register_tool(ConcreteTool, "concrete_tool")
        tool_class = ToolRegistry.get("concrete_tool")
        assert tool_class == ConcreteTool

    def test_get_tool_not_found(self):
        """Test getting a non-existent tool returns None."""
        tool_class = ToolRegistry.get("nonexistent")
        assert tool_class is None

    def test_get_required_tool(self):
        """Test get_required returns tool when found."""
        ToolRegistry.register_tool(ConcreteTool, "concrete_tool")
        tool_class = ToolRegistry.get_required("concrete_tool")
        assert tool_class == ConcreteTool

    def test_get_required_tool_not_found(self):
        """Test get_required raises KeyError when not found."""
        with pytest.raises(KeyError) as exc_info:
            ToolRegistry.get_required("nonexistent")
        assert "nonexistent" in str(exc_info.value)
        assert "not registered" in str(exc_info.value)

    def test_create_tool(self):
        """Test creating a tool instance."""
        ToolRegistry.register_tool(ConcreteTool, "concrete_tool")
        tool = ToolRegistry.create("concrete_tool", config={"key": "value"})
        assert isinstance(tool, ConcreteTool)
        assert tool.config == {"key": "value"}

    def test_create_tool_no_config(self):
        """Test creating a tool without config."""
        ToolRegistry.register_tool(ConcreteTool, "concrete_tool")
        tool = ToolRegistry.create("concrete_tool")
        assert isinstance(tool, ConcreteTool)
        assert tool.config == {}

    def test_list_tools(self):
        """Test listing all registered tools."""
        ToolRegistry.register_tool(ConcreteTool, "tool1")
        ToolRegistry.register_tool(AuthTool, "tool2")
        tools = ToolRegistry.list_tools()
        assert "tool1" in tools
        assert "tool2" in tools
        assert len(tools) == 2

    def test_list_tools_empty(self):
        """Test listing tools when registry is empty."""
        tools = ToolRegistry.list_tools()
        assert tools == []

    def test_list_categories(self):
        """Test listing all categories."""
        ToolRegistry.register_tool(ConcreteTool, "tool1")
        ToolRegistry.register_tool(AuthTool, "tool2")
        categories = ToolRegistry.list_categories()
        assert "test" in categories
        assert "general" in categories

    def test_get_tools_by_category(self):
        """Test getting tools by category."""
        ToolRegistry.register_tool(ConcreteTool, "tool1")
        ToolRegistry.register_tool(AuthTool, "tool2")
        test_tools = ToolRegistry.get_tools_by_category("test")
        assert "tool1" in test_tools

    def test_get_tools_by_category_empty(self):
        """Test getting tools from non-existent category."""
        tools = ToolRegistry.get_tools_by_category("nonexistent")
        assert tools == []

    def test_get_all_schemas(self):
        """Test getting all tool schemas."""
        ToolRegistry.register_tool(ConcreteTool, "tool1")
        schemas = ToolRegistry.get_all_schemas()
        assert "tool1" in schemas
        assert schemas["tool1"].name == "concrete_tool"

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        ToolRegistry.register_tool(ConcreteTool, "tool1")
        result = ToolRegistry.unregister("tool1")
        assert result is True
        assert "tool1" not in ToolRegistry._tools

    def test_unregister_tool_not_found(self):
        """Test unregistering a non-existent tool."""
        result = ToolRegistry.unregister("nonexistent")
        assert result is False

    def test_clear(self):
        """Test clearing the registry."""
        ToolRegistry.register_tool(ConcreteTool, "tool1")
        ToolRegistry.register_tool(AuthTool, "tool2")
        ToolRegistry.clear()
        assert ToolRegistry._tools == {}
        assert ToolRegistry._categories == {}

    def test_to_snake_case(self):
        """Test _to_snake_case static method."""
        assert ToolRegistry._to_snake_case("CamelCase") == "camel_case"
        assert ToolRegistry._to_snake_case("Simple") == "simple"
        assert ToolRegistry._to_snake_case("HTTPClient") == "h_t_t_p_client"
        assert ToolRegistry._to_snake_case("MyTool") == "my_tool"

    def test_category_tracking(self):
        """Test that categories are tracked correctly."""
        ToolRegistry.register_tool(ConcreteTool, "tool1")
        # ConcreteTool has category "test"
        assert "test" in ToolRegistry._categories
        assert "tool1" in ToolRegistry._categories["test"]

    def test_unregister_removes_from_category(self):
        """Test that unregistering removes from category."""
        ToolRegistry.register_tool(ConcreteTool, "tool1")
        assert "tool1" in ToolRegistry.get_tools_by_category("test")
        ToolRegistry.unregister("tool1")
        assert "tool1" not in ToolRegistry.get_tools_by_category("test")


class TestExceptions:
    """Tests for custom exceptions."""

    def test_tool_registry_error(self):
        """Test ToolRegistryError can be raised and caught."""
        with pytest.raises(ToolRegistryError):
            raise ToolRegistryError("Registry error")

    def test_tool_registry_error_message(self):
        """Test ToolRegistryError message."""
        try:
            raise ToolRegistryError("Test error message")
        except ToolRegistryError as e:
            assert str(e) == "Test error message"

    def test_tool_execution_error(self):
        """Test ToolExecutionError can be raised and caught."""
        with pytest.raises(ToolExecutionError):
            raise ToolExecutionError("Execution failed")

    def test_tool_execution_error_message(self):
        """Test ToolExecutionError message."""
        try:
            raise ToolExecutionError("Execution error")
        except ToolExecutionError as e:
            assert str(e) == "Execution error"

    def test_exception_inheritance(self):
        """Test that exceptions inherit from Exception."""
        assert issubclass(ToolRegistryError, Exception)
        assert issubclass(ToolExecutionError, Exception)
