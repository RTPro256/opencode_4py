"""
Unit tests for LSP tool implementation.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
import asyncio

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

    def test_method_values(self):
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

    def test_method_is_string(self):
        """Test that LSPMethod is a string enum."""
        assert isinstance(LSPMethod.DEFINITION, str)


class TestLSPPosition:
    """Tests for LSPPosition dataclass."""

    def test_position_creation(self):
        """Test creating an LSP position."""
        pos = LSPPosition(line=10, character=5)
        assert pos.line == 10
        assert pos.character == 5

    def test_position_to_lsp(self):
        """Test converting position to LSP format."""
        pos = LSPPosition(line=10, character=5)
        result = pos.to_lsp()
        assert result == {"line": 10, "character": 5}


class TestLSPRange:
    """Tests for LSPRange dataclass."""

    def test_range_creation(self):
        """Test creating an LSP range."""
        start = LSPPosition(line=0, character=0)
        end = LSPPosition(line=10, character=20)
        range_obj = LSPRange(start=start, end=end)
        assert range_obj.start == start
        assert range_obj.end == end

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

    def test_result_creation_minimal(self):
        """Test creating an LSP result with minimal fields."""
        result = LSPResult(kind="definition")
        assert result.kind == "definition"
        assert result.name is None
        assert result.location is None
        assert result.message is None
        assert result.children == []

    def test_result_creation_full(self):
        """Test creating an LSP result with all fields."""
        result = LSPResult(
            kind="symbol",
            name="MyClass",
            location={"uri": "file:///test.py", "range": {}},
            message="A test class",
            children=[LSPResult(kind="method", name="my_method")],
        )
        assert result.kind == "symbol"
        assert result.name == "MyClass"
        assert result.location is not None
        assert result.message == "A test class"
        assert len(result.children) == 1

    def test_result_to_dict(self):
        """Test converting result to dictionary."""
        result = LSPResult(
            kind="symbol",
            name="MyClass",
            children=[LSPResult(kind="method", name="my_method")],
        )
        d = result.to_dict()
        assert d["kind"] == "symbol"
        assert d["name"] == "MyClass"
        assert len(d["children"]) == 1
        assert d["children"][0]["name"] == "my_method"


class TestLSPTool:
    """Tests for LSPTool class."""

    @pytest.fixture
    def lsp_tool(self):
        """Create an LSP tool instance."""
        return LSPTool(working_directory=Path("C:/test/project"))

    def test_tool_name(self, lsp_tool):
        """Test tool name property."""
        assert lsp_tool.name == "lsp"

    def test_tool_description(self, lsp_tool):
        """Test tool description property."""
        desc = lsp_tool.description
        assert "definition" in desc.lower()
        assert "references" in desc.lower()
        assert "hover" in desc.lower()

    def test_tool_parameters(self, lsp_tool):
        """Test tool parameters schema."""
        params = lsp_tool.parameters
        assert params["type"] == "object"
        assert "method" in params["properties"]
        assert "file_path" in params["properties"]
        assert "line" in params["properties"]
        assert "character" in params["properties"]
        assert "required" in params
        assert "method" in params["required"]

    def test_tool_permission_level(self, lsp_tool):
        """Test tool permission level."""
        from opencode.tool.base import PermissionLevel
        assert lsp_tool.permission_level == PermissionLevel.READ

    @pytest.mark.asyncio
    async def test_execute_unknown_method(self, lsp_tool):
        """Test execute with unknown method."""
        result = await lsp_tool.execute(method="unknown_method")
        assert not result.success
        assert "Unknown LSP method" in result.error

    @pytest.mark.asyncio
    async def test_execute_definition_missing_params(self, lsp_tool):
        """Test definition method with missing parameters."""
        result = await lsp_tool.execute(method="definition")
        assert not result.success
        assert "requires file_path, line, and character" in result.error

    @pytest.mark.asyncio
    async def test_execute_definition_partial_params(self, lsp_tool):
        """Test definition method with partial parameters."""
        result = await lsp_tool.execute(method="definition", file_path="test.py")
        assert not result.success
        assert "requires file_path, line, and character" in result.error

    @pytest.mark.asyncio
    async def test_execute_workspace_symbols_missing_query(self, lsp_tool):
        """Test workspace symbols without query."""
        result = await lsp_tool.execute(method="workspaceSymbols")
        assert not result.success
        assert "requires a query parameter" in result.error

    @pytest.mark.asyncio
    async def test_execute_rename_missing_new_name(self, lsp_tool):
        """Test rename without new_name."""
        result = await lsp_tool.execute(
            method="rename",
            file_path="test.py",
            line=0,
            character=0,
        )
        assert not result.success
        assert "requires a new_name parameter" in result.error

    @pytest.mark.asyncio
    async def test_execute_no_client_for_file_type(self, lsp_tool):
        """Test execute with unsupported file type."""
        result = await lsp_tool.execute(
            method="definition",
            file_path="test.xyz",
            line=0,
            character=0,
        )
        assert not result.success
        assert "No LSP client available" in result.error

    @pytest.mark.asyncio
    async def test_execute_workspace_symbols_no_clients(self, lsp_tool):
        """Test workspace symbols with no clients available."""
        result = await lsp_tool.execute(method="workspaceSymbols", query="test")
        assert not result.success
        assert "No LSP clients available" in result.error


class TestLSPToolFormatting:
    """Tests for LSPTool result formatting methods."""

    @pytest.fixture
    def lsp_tool(self):
        """Create an LSP tool instance."""
        return LSPTool(working_directory=Path("C:/test/project"))

    def test_format_completion_result_empty(self, lsp_tool):
        """Test formatting empty completion result."""
        result = lsp_tool._format_completion_result(None)
        assert "No completions found" in result

    def test_format_completion_result_list(self, lsp_tool):
        """Test formatting completion list."""
        items = [
            {"label": "my_function", "kind": 3, "detail": "A function"},
            {"label": "MyClass", "kind": 7, "detail": "A class"},
        ]
        result = lsp_tool._format_completion_result(items)
        assert "Completions" in result
        assert "my_function" in result
        assert "MyClass" in result

    def test_format_completion_result_dict_with_items(self, lsp_tool):
        """Test formatting completion result with items dict."""
        result = lsp_tool._format_completion_result({"items": [{"label": "test", "kind": 1}]})
        assert "Completions" in result
        assert "test" in result

    def test_format_completion_result_truncation(self, lsp_tool):
        """Test completion result truncation at 20 items."""
        items = [{"label": f"item_{i}", "kind": 1} for i in range(25)]
        result = lsp_tool._format_completion_result(items)
        assert "and 5 more" in result

    def test_format_rename_result_empty(self, lsp_tool):
        """Test formatting empty rename result."""
        result = lsp_tool._format_rename_result(None)
        assert "no changes made" in result.lower()

    def test_format_rename_result_document_changes(self, lsp_tool):
        """Test formatting rename result with documentChanges."""
        result = lsp_tool._format_rename_result({
            "documentChanges": [
                {
                    "textDocument": {"uri": "file:///test.py"},
                    "edits": [{"range": {}, "newText": "new_name"}],
                }
            ]
        })
        assert "Rename successful" in result
        assert "1 file" in result

    def test_format_rename_result_changes(self, lsp_tool):
        """Test formatting rename result with changes."""
        result = lsp_tool._format_rename_result({
            "changes": {
                "file:///test.py": [{"range": {}, "newText": "new_name"}],
            }
        })
        assert "Rename successful" in result
        assert "1 file" in result

    def test_format_rename_result_default(self, lsp_tool):
        """Test formatting rename result with unknown format."""
        result = lsp_tool._format_rename_result({"some": "data"})
        assert "Rename completed" in result

    def test_format_formatting_result_empty(self, lsp_tool):
        """Test formatting empty formatting result."""
        result = lsp_tool._format_formatting_result(None)
        assert "No formatting changes" in result

    def test_format_formatting_result_list(self, lsp_tool):
        """Test formatting formatting result list."""
        edits = [
            {"range": {"start": {"line": 0}}, "newText": "def "},
            {"range": {"start": {"line": 5}}, "newText": "    "},
        ]
        result = lsp_tool._format_formatting_result(edits)
        assert "Formatting applied" in result
        assert "2 edit" in result

    def test_format_formatting_result_truncation(self, lsp_tool):
        """Test formatting result truncation at 10 items."""
        edits = [{"range": {"start": {"line": i}}, "newText": "x"} for i in range(15)]
        result = lsp_tool._format_formatting_result(edits)
        assert "and 5 more" in result

    def test_format_location_result_empty_list(self, lsp_tool):
        """Test formatting empty location list."""
        result = lsp_tool._format_location_result([], "Definition")
        assert "No definition found" in result

    def test_format_location_result_list(self, lsp_tool):
        """Test formatting location list."""
        locations = [
            {"uri": "file:///test.py", "range": {"start": {"line": 10}}},
            {"uri": "file:///other.py", "range": {"start": {"line": 5}}},
        ]
        result = lsp_tool._format_location_result(locations, "References")
        assert "References" in result
        assert "2 found" in result

    def test_format_location_result_location_link(self, lsp_tool):
        """Test formatting location with LocationLink format."""
        locations = [{"targetUri": "file:///test.py"}]
        result = lsp_tool._format_location_result(locations, "Definition")
        assert "file:///test.py" in result

    def test_format_location_result_single(self, lsp_tool):
        """Test formatting single location."""
        location = {"uri": "file:///test.py", "range": {"start": {"line": 10}}}
        result = lsp_tool._format_location_result(location, "Definition")
        assert "Definition:" in result
        assert "test.py" in result

    def test_format_hover_result_empty(self, lsp_tool):
        """Test formatting empty hover result."""
        result = lsp_tool._format_hover_result(None)
        assert "No hover information" in result

    def test_format_hover_result_string(self, lsp_tool):
        """Test formatting hover result with string content."""
        result = lsp_tool._format_hover_result({"contents": "str"})
        assert result == "str"

    def test_format_hover_result_list(self, lsp_tool):
        """Test formatting hover result with list content."""
        result = lsp_tool._format_hover_result({"contents": ["line1", "line2"]})
        assert "line1" in result
        assert "line2" in result

    def test_format_hover_result_dict(self, lsp_tool):
        """Test formatting hover result with dict content."""
        result = lsp_tool._format_hover_result({"contents": {"value": "my_value"}})
        assert "my_value" in result

    def test_format_symbols_result_empty(self, lsp_tool):
        """Test formatting empty symbols result."""
        result = lsp_tool._format_symbols_result(None)
        assert "No symbols found" in result

    def test_format_symbols_result_list(self, lsp_tool):
        """Test formatting symbols list."""
        symbols = [
            {"name": "MyClass", "kind": 5, "location": {"uri": "file:///test.py"}},
            {"name": "my_func", "kind": 12, "location": {}},
        ]
        result = lsp_tool._format_symbols_result(symbols)
        assert "Symbols" in result
        assert "MyClass" in result
        assert "my_func" in result

    def test_format_symbols_result_no_location(self, lsp_tool):
        """Test formatting symbols without location."""
        symbols = [{"name": "MyClass", "kind": 5}]
        result = lsp_tool._format_symbols_result(symbols)
        assert "MyClass" in result


class TestLSPToolClientManagement:
    """Tests for LSPTool client management."""

    @pytest.fixture
    def lsp_tool(self):
        """Create an LSP tool instance."""
        return LSPTool(working_directory=Path("C:/test/project"))

    @pytest.mark.asyncio
    async def test_get_client_cached(self, lsp_tool):
        """Test getting a cached client."""
        mock_client = MagicMock()
        lsp_tool.lsp_clients[".py"] = mock_client
        
        result = await lsp_tool._get_client("test.py")
        assert result == mock_client

    @pytest.mark.asyncio
    async def test_get_client_unsupported_extension(self, lsp_tool):
        """Test getting client for unsupported extension."""
        result = await lsp_tool._get_client("test.xyz")
        assert result is None


class TestCreateLSPTool:
    """Tests for create_lsp_tool factory function."""

    def test_create_lsp_tool_default(self):
        """Test creating LSP tool with default path."""
        tool = create_lsp_tool()
        assert tool.name == "lsp"
        assert tool.working_directory == Path(".")

    def test_create_lsp_tool_custom_path(self):
        """Test creating LSP tool with custom path."""
        tool = create_lsp_tool(working_directory=Path("C:/custom/path"))
        assert tool.working_directory == Path("C:/custom/path")


class TestLSPToolFormatResult:
    """Tests for _format_result method."""

    @pytest.fixture
    def lsp_tool(self):
        """Create an LSP tool instance."""
        return LSPTool(working_directory=Path("C:/test/project"))

    def test_format_result_none(self, lsp_tool):
        """Test formatting None result."""
        result = lsp_tool._format_result(None, "definition")
        assert "No definition found" in result

    def test_format_result_no_result_key(self, lsp_tool):
        """Test formatting result without 'result' key."""
        result = lsp_tool._format_result({"error": "Some error"}, "definition")
        assert "LSP error" in result

    def test_format_result_null_result(self, lsp_tool):
        """Test formatting null result value."""
        result = lsp_tool._format_result({"result": None}, "definition")
        assert "No definition found" in result

    def test_format_result_definition(self, lsp_tool):
        """Test formatting definition result."""
        lsp_result = {
            "result": {"uri": "file:///test.py", "range": {"start": {"line": 10}}}
        }
        result = lsp_tool._format_result(lsp_result, "definition")
        assert "Definition:" in result

    def test_format_result_references(self, lsp_tool):
        """Test formatting references result."""
        lsp_result = {
            "result": [
                {"uri": "file:///test.py", "range": {"start": {"line": 10}}},
            ]
        }
        result = lsp_tool._format_result(lsp_result, "references")
        assert "References" in result

    def test_format_result_hover(self, lsp_tool):
        """Test formatting hover result."""
        lsp_result = {"result": {"contents": "type: str"}}
        result = lsp_tool._format_result(lsp_result, "hover")
        assert "type: str" in result

    def test_format_result_document_symbols(self, lsp_tool):
        """Test formatting document symbols result."""
        lsp_result = {
            "result": [{"name": "MyClass", "kind": 5}]
        }
        result = lsp_tool._format_result(lsp_result, "documentSymbols")
        assert "Symbols" in result

    def test_format_result_workspace_symbols(self, lsp_tool):
        """Test formatting workspace symbols result."""
        lsp_result = {
            "result": [{"name": "search_result", "kind": 12}]
        }
        result = lsp_tool._format_result(lsp_result, "workspaceSymbols")
        assert "Symbols" in result

    def test_format_result_completion(self, lsp_tool):
        """Test formatting completion result."""
        lsp_result = {
            "result": [{"label": "my_func", "kind": 3}]
        }
        result = lsp_tool._format_result(lsp_result, "completion")
        assert "Completions" in result

    def test_format_result_rename(self, lsp_tool):
        """Test formatting rename result."""
        lsp_result = {
            "result": {"changes": {"file:///test.py": []}}
        }
        result = lsp_tool._format_result(lsp_result, "rename")
        assert "Rename successful" in result

    def test_format_result_formatting(self, lsp_tool):
        """Test formatting formatting result."""
        lsp_result = {
            "result": [{"range": {"start": {"line": 0}}, "newText": "x"}]
        }
        result = lsp_tool._format_result(lsp_result, "formatting")
        assert "Formatting applied" in result

    def test_format_result_unknown_method(self, lsp_tool):
        """Test formatting result for unknown method."""
        lsp_result = {"result": {"some": "data"}}
        result = lsp_tool._format_result(lsp_result, "unknown")
        assert "some" in result  # Falls through to json.dumps


class TestLSPToolSendRequest:
    """Tests for _send_request method."""

    @pytest.fixture
    def lsp_tool(self):
        """Create an LSP tool instance."""
        return LSPTool(working_directory=Path("C:/test/project"))

    @pytest.mark.asyncio
    async def test_send_request_definition(self, lsp_tool):
        """Test sending definition request."""
        mock_client = MagicMock()
        mock_client.stdin = MagicMock()
        mock_client.stdout = MagicMock()
        
        with patch.object(lsp_tool, '_send_lsp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"result": None}
            result = await lsp_tool._send_request(
                mock_client,
                LSPMethod.DEFINITION,
                "test.py",
                10,
                5,
            )
            assert result is not None
            # Verify the call was made with correct params
            call_args = mock_send.call_args
            assert call_args[0][1] == "textDocument/definition"

    @pytest.mark.asyncio
    async def test_send_request_references(self, lsp_tool):
        """Test sending references request."""
        mock_client = MagicMock()
        
        with patch.object(lsp_tool, '_send_lsp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"result": []}
            result = await lsp_tool._send_request(
                mock_client,
                LSPMethod.REFERENCES,
                "test.py",
                10,
                5,
            )
            call_args = mock_send.call_args
            params = call_args[0][2]
            assert "context" in params
            assert params["context"]["includeDeclaration"] is True

    @pytest.mark.asyncio
    async def test_send_request_rename(self, lsp_tool):
        """Test sending rename request."""
        mock_client = MagicMock()
        
        with patch.object(lsp_tool, '_send_lsp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"result": {}}
            result = await lsp_tool._send_request(
                mock_client,
                LSPMethod.RENAME,
                "test.py",
                10,
                5,
                new_name="new_variable",
            )
            call_args = mock_send.call_args
            params = call_args[0][2]
            assert params["newName"] == "new_variable"

    @pytest.mark.asyncio
    async def test_send_request_formatting(self, lsp_tool):
        """Test sending formatting request."""
        mock_client = MagicMock()
        
        with patch.object(lsp_tool, '_send_lsp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"result": []}
            result = await lsp_tool._send_request(
                mock_client,
                LSPMethod.FORMATTING,
                "test.py",
                None,
                None,
            )
            call_args = mock_send.call_args
            params = call_args[0][2]
            assert "options" in params
            assert params["options"]["tabSize"] == 4

    @pytest.mark.asyncio
    async def test_send_request_range_formatting(self, lsp_tool):
        """Test sending range formatting request."""
        mock_client = MagicMock()
        
        with patch.object(lsp_tool, '_send_lsp_message', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"result": []}
            result = await lsp_tool._send_request(
                mock_client,
                LSPMethod.RANGE_FORMATTING,
                "test.py",
                0,
                0,
                end_line=10,
                end_character=20,
            )
            call_args = mock_send.call_args
            params = call_args[0][2]
            assert "range" in params
            assert params["range"]["end"]["line"] == 10


class TestLSPToolIntegration:
    """Integration tests for LSPTool."""

    @pytest.fixture
    def lsp_tool(self):
        """Create an LSP tool instance."""
        return LSPTool(working_directory=Path("C:/test/project"))

    @pytest.mark.asyncio
    async def test_execute_with_mock_client(self, lsp_tool):
        """Test execute with a mocked LSP client."""
        mock_client = MagicMock()
        mock_client.stdin = MagicMock()
        mock_client.stdout = MagicMock()
        lsp_tool.lsp_clients[".py"] = mock_client
        
        with patch.object(lsp_tool, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"result": {"uri": "file:///test.py", "range": {"start": {"line": 10}}}}
            
            result = await lsp_tool.execute(
                method="definition",
                file_path="test.py",
                line=5,
                character=10,
            )
            
            assert result.success
            assert "Definition:" in result.output

    @pytest.mark.asyncio
    async def test_execute_exception_handling(self, lsp_tool):
        """Test execute handles exceptions gracefully."""
        mock_client = MagicMock()
        lsp_tool.lsp_clients[".py"] = mock_client
        
        with patch.object(lsp_tool, '_send_request', new_callable=AsyncMock) as mock_send:
            mock_send.side_effect = Exception("LSP connection error")
            
            result = await lsp_tool.execute(
                method="definition",
                file_path="test.py",
                line=5,
                character=10,
            )
            
            assert not result.success
            assert "LSP query failed" in result.error
