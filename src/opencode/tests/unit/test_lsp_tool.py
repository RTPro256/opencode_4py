"""
Tests for LSP (Language Server Protocol) tool.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from opencode.tool.lsp import (
    LSPMethod,
    LSPPosition,
    LSPRange,
    LSPResult,
    LSPTool,
    create_lsp_tool,
)
from opencode.tool.base import ToolResult


class TestLSPMethod:
    """Tests for LSPMethod enum."""

    @pytest.mark.unit
    def test_lsp_method_values(self):
        """Test LSP method enum values."""
        assert LSPMethod.DEFINITION.value == "textDocument/definition"
        assert LSPMethod.REFERENCES.value == "textDocument/references"
        assert LSPMethod.HOVER.value == "textDocument/hover"
        assert LSPMethod.DOCUMENT_SYMBOLS.value == "textDocument/documentSymbol"
        assert LSPMethod.WORKSPACE_SYMBOLS.value == "workspace/symbol"
        assert LSPMethod.COMPLETION.value == "textDocument/completion"
        assert LSPMethod.RENAME.value == "textDocument/rename"
        assert LSPMethod.FORMATTING.value == "textDocument/formatting"
        assert LSPMethod.RANGE_FORMATTING.value == "textDocument/rangeFormatting"

    @pytest.mark.unit
    def test_lsp_method_is_string(self):
        """Test that LSPMethod is a string enum."""
        assert isinstance(LSPMethod.DEFINITION, str)


class TestLSPPosition:
    """Tests for LSPPosition dataclass."""

    @pytest.mark.unit
    def test_position_creation(self):
        """Test creating an LSP position."""
        pos = LSPPosition(line=10, character=5)
        assert pos.line == 10
        assert pos.character == 5

    @pytest.mark.unit
    def test_position_to_lsp(self):
        """Test converting position to LSP format."""
        pos = LSPPosition(line=10, character=5)
        result = pos.to_lsp()
        assert result == {"line": 10, "character": 5}


class TestLSPRange:
    """Tests for LSPRange dataclass."""

    @pytest.mark.unit
    def test_range_creation(self):
        """Test creating an LSP range."""
        start = LSPPosition(line=0, character=0)
        end = LSPPosition(line=10, character=20)
        range_obj = LSPRange(start=start, end=end)
        assert range_obj.start == start
        assert range_obj.end == end

    @pytest.mark.unit
    def test_range_to_lsp(self):
        """Test converting range to LSP format."""
        start = LSPPosition(line=0, character=0)
        end = LSPPosition(line=10, character=20)
        range_obj = LSPRange(start=start, end=end)
        result = range_obj.to_lsp()
        assert result == {
            "start": {"line": 0, "character": 0},
            "end": {"line": 10, "character": 20},
        }


class TestLSPResult:
    """Tests for LSPResult dataclass."""

    @pytest.mark.unit
    def test_result_creation_minimal(self):
        """Test creating an LSP result with minimal fields."""
        result = LSPResult(kind="definition")
        assert result.kind == "definition"
        assert result.name is None
        assert result.location is None
        assert result.message is None
        assert result.children == []

    @pytest.mark.unit
    def test_result_creation_full(self):
        """Test creating an LSP result with all fields."""
        child = LSPResult(kind="reference", name="child_func")
        result = LSPResult(
            kind="function",
            name="my_function",
            location={"uri": "file:///test.py", "range": {}},
            message="Test function",
            children=[child],
        )
        assert result.kind == "function"
        assert result.name == "my_function"
        assert result.location == {"uri": "file:///test.py", "range": {}}
        assert result.message == "Test function"
        assert len(result.children) == 1

    @pytest.mark.unit
    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        child = LSPResult(kind="reference", name="child_func")
        result = LSPResult(
            kind="function",
            name="my_function",
            location={"uri": "file:///test.py"},
            message="Test",
            children=[child],
        )
        d = result.to_dict()
        assert d["kind"] == "function"
        assert d["name"] == "my_function"
        assert d["location"] == {"uri": "file:///test.py"}
        assert d["message"] == "Test"
        assert len(d["children"]) == 1
        assert d["children"][0]["name"] == "child_func"


class TestLSPTool:
    """Tests for LSPTool class."""

    @pytest.mark.unit
    def test_tool_name(self):
        """Test tool name property."""
        tool = LSPTool()
        assert tool.name == "lsp"

    @pytest.mark.unit
    def test_tool_description(self):
        """Test tool description property."""
        tool = LSPTool()
        desc = tool.description
        assert "definition" in desc.lower()
        assert "references" in desc.lower()
        assert "hover" in desc.lower()

    @pytest.mark.unit
    def test_tool_parameters(self):
        """Test tool parameters schema."""
        tool = LSPTool()
        params = tool.parameters
        assert params["type"] == "object"
        assert "method" in params["properties"]
        assert "file_path" in params["properties"]
        assert "line" in params["properties"]
        assert "character" in params["properties"]
        assert "method" in params["required"]

    @pytest.mark.unit
    def test_tool_permission_level(self):
        """Test tool permission level."""
        tool = LSPTool()
        from opencode.tool.base import PermissionLevel
        assert tool.permission_level == PermissionLevel.READ

    @pytest.mark.unit
    def test_tool_with_working_directory(self):
        """Test creating tool with working directory."""
        tool = LSPTool(working_directory=Path("/tmp/test"))
        assert tool.working_directory == Path("/tmp/test")


class TestLSPToolExecute:
    """Tests for LSPTool execute method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_unknown_method(self):
        """Test execute with unknown method."""
        tool = LSPTool()
        result = await tool.execute(method="unknown_method")
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "Unknown LSP method" in result.error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_definition_missing_params(self):
        """Test execute definition without required params."""
        tool = LSPTool()
        result = await tool.execute(method="definition")
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "requires file_path, line, and character" in result.error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_references_missing_params(self):
        """Test execute references without required params."""
        tool = LSPTool()
        result = await tool.execute(method="references", file_path="test.py")
        assert isinstance(result, ToolResult)
        assert not result.success

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_hover_missing_params(self):
        """Test execute hover without required params."""
        tool = LSPTool()
        result = await tool.execute(method="hover", file_path="test.py", line=0)
        assert isinstance(result, ToolResult)
        assert not result.success

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_workspace_symbols_missing_query(self):
        """Test execute workspace symbols without query."""
        tool = LSPTool()
        result = await tool.execute(method="workspaceSymbols")
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "requires a query parameter" in result.error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_rename_missing_new_name(self):
        """Test execute rename without new_name."""
        tool = LSPTool()
        result = await tool.execute(
            method="rename",
            file_path="test.py",
            line=0,
            character=0,
        )
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "requires a new_name parameter" in result.error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_no_client_for_file_type(self):
        """Test execute with unsupported file type."""
        tool = LSPTool()
        result = await tool.execute(
            method="definition",
            file_path="test.xyz",
            line=0,
            character=0,
        )
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "No LSP client available" in result.error

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_workspace_symbols_no_clients(self):
        """Test workspace symbols with no clients available."""
        tool = LSPTool()
        result = await tool.execute(method="workspaceSymbols", query="test")
        assert isinstance(result, ToolResult)
        assert not result.success
        assert "No LSP clients available" in result.error


class TestLSPToolFormatting:
    """Tests for LSPTool result formatting methods."""

    @pytest.mark.unit
    def test_format_result_none(self):
        """Test formatting None result."""
        tool = LSPTool()
        result = tool._format_result(None, "definition")
        assert "No definition found" in result

    @pytest.mark.unit
    def test_format_result_no_result_key(self):
        """Test formatting result without 'result' key."""
        tool = LSPTool()
        result = tool._format_result({"error": "Some error"}, "definition")
        assert "LSP error" in result

    @pytest.mark.unit
    def test_format_result_null_result(self):
        """Test formatting null result value."""
        tool = LSPTool()
        result = tool._format_result({"result": None}, "definition")
        assert "No definition found" in result

    @pytest.mark.unit
    def test_format_location_result_list(self):
        """Test formatting location result as list."""
        tool = LSPTool()
        lsp_result = {
            "result": [
                {"uri": "file:///test.py", "range": {"start": {"line": 10}}},
                {"uri": "file:///other.py", "range": {"start": {"line": 20}}},
            ]
        }
        result = tool._format_result(lsp_result, "definition")
        assert "Definition" in result
        assert "2 found" in result

    @pytest.mark.unit
    def test_format_location_result_single(self):
        """Test formatting single location result."""
        tool = LSPTool()
        lsp_result = {
            "result": {"uri": "file:///test.py", "range": {"start": {"line": 10}}}
        }
        result = tool._format_result(lsp_result, "definition")
        assert "Definition" in result

    @pytest.mark.unit
    def test_format_location_result_location_link(self):
        """Test formatting LocationLink result."""
        tool = LSPTool()
        lsp_result = {
            "result": [{"targetUri": "file:///target.py"}]
        }
        result = tool._format_result(lsp_result, "definition")
        assert "target.py" in result

    @pytest.mark.unit
    def test_format_hover_result_string(self):
        """Test formatting hover result as string."""
        tool = LSPTool()
        lsp_result = {
            "result": {"contents": "string content"}
        }
        result = tool._format_result(lsp_result, "hover")
        assert result == "string content"

    @pytest.mark.unit
    def test_format_hover_result_list(self):
        """Test formatting hover result as list."""
        tool = LSPTool()
        lsp_result = {
            "result": {"contents": ["line1", "line2"]}
        }
        result = tool._format_result(lsp_result, "hover")
        assert "line1" in result
        assert "line2" in result

    @pytest.mark.unit
    def test_format_hover_result_dict(self):
        """Test formatting hover result as dict."""
        tool = LSPTool()
        lsp_result = {
            "result": {"contents": {"value": "markdown content"}}
        }
        result = tool._format_result(lsp_result, "hover")
        assert result == "markdown content"

    @pytest.mark.unit
    def test_format_hover_result_none(self):
        """Test formatting None hover result."""
        tool = LSPTool()
        result = tool._format_hover_result(None)
        assert "No hover information" in result

    @pytest.mark.unit
    def test_format_symbols_result(self):
        """Test formatting symbols result."""
        tool = LSPTool()
        lsp_result = {
            "result": [
                {"name": "MyClass", "kind": 5, "location": {"uri": "file:///test.py"}},
                {"name": "my_func", "kind": 12, "location": {}},
            ]
        }
        result = tool._format_result(lsp_result, "documentSymbols")
        assert "Symbols" in result
        assert "MyClass" in result
        assert "my_func" in result

    @pytest.mark.unit
    def test_format_symbols_result_empty(self):
        """Test formatting empty symbols result."""
        tool = LSPTool()
        result = tool._format_symbols_result(None)
        assert "No symbols found" in result

    @pytest.mark.unit
    def test_format_completion_result_list(self):
        """Test formatting completion result as list."""
        tool = LSPTool()
        lsp_result = {
            "result": [
                {"label": "my_function", "kind": 3, "detail": "A function"},
                {"label": "my_var", "kind": 6},
            ]
        }
        result = tool._format_result(lsp_result, "completion")
        assert "Completions" in result
        assert "my_function" in result

    @pytest.mark.unit
    def test_format_completion_result_dict_with_items(self):
        """Test formatting completion result with items dict."""
        tool = LSPTool()
        lsp_result = {
            "result": {
                "items": [
                    {"label": "item1", "kind": 1},
                ]
            }
        }
        result = tool._format_result(lsp_result, "completion")
        assert "Completions" in result

    @pytest.mark.unit
    def test_format_completion_result_empty(self):
        """Test formatting empty completion result."""
        tool = LSPTool()
        result = tool._format_completion_result(None)
        assert "No completions found" in result

    @pytest.mark.unit
    def test_format_completion_result_truncation(self):
        """Test completion result truncation at 20 items."""
        tool = LSPTool()
        items = [{"label": f"item{i}", "kind": 1} for i in range(25)]
        result = tool._format_completion_result(items)
        assert "25 found" in result
        assert "5 more" in result

    @pytest.mark.unit
    def test_format_rename_result_document_changes(self):
        """Test formatting rename result with documentChanges."""
        tool = LSPTool()
        lsp_result = {
            "result": {
                "documentChanges": [
                    {"textDocument": {"uri": "file:///test.py"}, "edits": [{}]},
                ]
            }
        }
        result = tool._format_result(lsp_result, "rename")
        assert "Rename successful" in result
        assert "1 file" in result

    @pytest.mark.unit
    def test_format_rename_result_changes(self):
        """Test formatting rename result with changes."""
        tool = LSPTool()
        lsp_result = {
            "result": {
                "changes": {
                    "file:///test.py": [{}],
                    "file:///other.py": [{}, {}],
                }
            }
        }
        result = tool._format_result(lsp_result, "rename")
        assert "Rename successful" in result
        assert "2 file" in result

    @pytest.mark.unit
    def test_format_rename_result_none(self):
        """Test formatting None rename result."""
        tool = LSPTool()
        result = tool._format_rename_result(None)
        assert "Rename failed" in result

    @pytest.mark.unit
    def test_format_formatting_result(self):
        """Test formatting formatting result."""
        tool = LSPTool()
        lsp_result = {
            "result": [
                {"range": {"start": {"line": 0}}, "newText": "formatted"},
            ]
        }
        result = tool._format_result(lsp_result, "formatting")
        assert "Formatting applied" in result

    @pytest.mark.unit
    def test_format_formatting_result_empty(self):
        """Test formatting empty formatting result."""
        tool = LSPTool()
        result = tool._format_formatting_result(None)
        assert "No formatting changes" in result

    @pytest.mark.unit
    def test_format_formatting_result_truncation(self):
        """Test formatting result truncation at 10 edits."""
        tool = LSPTool()
        edits = [{"range": {"start": {"line": i}}, "newText": ""} for i in range(15)]
        result = tool._format_formatting_result(edits)
        assert "15 edit" in result
        assert "5 more" in result


class TestLSPToolClient:
    """Tests for LSPTool client management."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_client_unsupported_extension(self):
        """Test getting client for unsupported file extension."""
        tool = LSPTool()
        client = await tool._get_client("test.xyz")
        assert client is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_client_cached(self):
        """Test getting cached client."""
        tool = LSPTool()
        mock_client = MagicMock()
        tool.lsp_clients[".py"] = mock_client
        client = await tool._get_client("test.py")
        assert client == mock_client


class TestCreateLSPTool:
    """Tests for create_lsp_tool factory function."""

    @pytest.mark.unit
    def test_create_lsp_tool_default(self):
        """Test creating LSP tool with default path."""
        tool = create_lsp_tool()
        assert isinstance(tool, LSPTool)
        assert tool.name == "lsp"

    @pytest.mark.unit
    def test_create_lsp_tool_with_path(self):
        """Test creating LSP tool with custom path."""
        tool = create_lsp_tool(working_directory=Path("/custom/path"))
        assert isinstance(tool, LSPTool)
        assert tool.working_directory == Path("/custom/path")
