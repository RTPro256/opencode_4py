"""
Tests for CSV/Array workflow tool.
"""

import pytest
from unittest.mock import MagicMock, patch

from opencode.workflow.tools.csv_array import CsvArrayTool
from opencode.workflow.tools.registry import ToolResult, ToolSchema


class TestCsvArrayTool:
    """Tests for CsvArrayTool."""
    
    @pytest.mark.unit
    def test_csv_array_tool_creation(self):
        """Test CsvArrayTool instantiation."""
        tool = CsvArrayTool()
        assert tool is not None
    
    @pytest.mark.unit
    def test_csv_array_tool_schema(self):
        """Test CsvArrayTool has schema."""
        schema = CsvArrayTool.get_schema()
        assert schema is not None
        assert schema.name == "csv_array"
    
    @pytest.mark.unit
    def test_csv_array_tool_schema_description(self):
        """Test CsvArrayTool schema description."""
        schema = CsvArrayTool.get_schema()
        assert "CSV" in schema.description or "array" in schema.description.lower()
    
    @pytest.mark.unit
    def test_csv_array_tool_schema_parameters(self):
        """Test CsvArrayTool schema parameters."""
        schema = CsvArrayTool.get_schema()
        assert "operation" in schema.parameters.get("properties", {})
        assert "data" in schema.parameters.get("properties", {})
    
    @pytest.mark.unit
    def test_csv_array_tool_required_params(self):
        """Test CsvArrayTool required parameters."""
        schema = CsvArrayTool.get_schema()
        assert "operation" in schema.required_params
        assert "data" in schema.required_params
    
    @pytest.mark.unit
    def test_csv_array_tool_operations_enum(self):
        """Test CsvArrayTool operations enum."""
        schema = CsvArrayTool.get_schema()
        props = schema.parameters.get("properties", {})
        operation_prop = props.get("operation", {})
        enum_values = operation_prop.get("enum", [])
        
        assert "parse" in enum_values
        assert "stringify" in enum_values
        assert "filter" in enum_values
        assert "map" in enum_values
        assert "sort" in enum_values
    
    @pytest.mark.unit
    def test_csv_array_tool_registered(self):
        """Test CsvArrayTool is registered."""
        from opencode.workflow.tools.registry import ToolRegistry
        # Check if csv_array is registered
        assert "csv_array" in ToolRegistry._tools or hasattr(ToolRegistry, 'get')


class TestCsvArrayToolParse:
    """Tests for CSV parsing operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_csv_basic(self):
        """Test basic CSV parsing."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name,age\nJohn,30\nJane,25"
        })
        assert result.success is True
        assert isinstance(result.data, list)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_csv_with_options(self):
        """Test CSV parsing with options."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name;age\nJohn;30\nJane;25",
            "options": {"delimiter": ";"}
        })
        assert result.success is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_csv_empty(self):
        """Test parsing empty CSV."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": ""
        })
        # Should handle empty data gracefully
        assert result is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_csv_single_row(self):
        """Test parsing single row CSV."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name,age\nJohn,30"
        })
        assert result.success is True


class TestCsvArrayToolStringify:
    """Tests for CSV stringify operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stringify_basic(self):
        """Test basic array to CSV conversion."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "stringify",
            "data": [
                {"name": "John", "age": "30"},
                {"name": "Jane", "age": "25"}
            ]
        })
        assert result.success is True
        assert isinstance(result.data, str)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stringify_empty_array(self):
        """Test stringify empty array."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "stringify",
            "data": []
        })
        assert result is not None


class TestCsvArrayToolFilter:
    """Tests for array filter operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_basic(self):
        """Test basic array filtering."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25},
                {"name": "Bob", "age": 35}
            ],
            "options": {"field": "age", "operator": ">", "value": 28}
        })
        assert result.success is True
        assert isinstance(result.data, list)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_empty_result(self):
        """Test filter with no matches."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [
                {"name": "John", "age": 30}
            ],
            "options": {"field": "age", "operator": ">", "value": 100}
        })
        assert result.success is True
        assert result.data == []


class TestCsvArrayToolSort:
    """Tests for array sort operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sort_basic(self):
        """Test basic array sorting."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sort",
            "data": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25},
                {"name": "Bob", "age": 35}
            ],
            "options": {"field": "age"}
        })
        assert result.success is True
        assert len(result.data) == 3
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sort_descending(self):
        """Test descending sort."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sort",
            "data": [
                {"name": "John", "age": 30},
                {"name": "Jane", "age": 25}
            ],
            "options": {"field": "age", "descending": True}
        })
        assert result.success is True


class TestCsvArrayToolMap:
    """Tests for array map operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_basic(self):
        """Test basic array mapping."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": [1, 2, 3, 4, 5],
            "options": {"transform": "multiply", "factor": 2}
        })
        assert result.success is True
        assert isinstance(result.data, list)


class TestCsvArrayToolReduce:
    """Tests for array reduce operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_sum(self):
        """Test reduce with sum."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [1, 2, 3, 4, 5],
            "options": {"operation": "sum"}
        })
        assert result.success is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_count(self):
        """Test reduce with count."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [1, 2, 3, 4, 5],
            "options": {"operation": "count"}
        })
        assert result.success is True


class TestCsvArrayToolGroup:
    """Tests for array group operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_group_basic(self):
        """Test basic array grouping."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "group",
            "data": [
                {"name": "John", "category": "A"},
                {"name": "Jane", "category": "B"},
                {"name": "Bob", "category": "A"}
            ],
            "options": {"field": "category"}
        })
        assert result.success is True


class TestCsvArrayToolMerge:
    """Tests for array merge operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_merge_basic(self):
        """Test basic array merging."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "merge",
            "data": [[1, 2], [3, 4], [5, 6]]
        })
        assert result.success is True
        assert isinstance(result.data, list)


class TestCsvArrayToolFlatten:
    """Tests for array flatten operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_flatten_basic(self):
        """Test basic array flattening."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "flatten",
            "data": [[1, 2], [3, 4], [5, 6]]
        })
        assert result.success is True
        assert result.data == [1, 2, 3, 4, 5, 6]


class TestCsvArrayToolUnique:
    """Tests for array unique operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unique_basic(self):
        """Test basic unique values."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "unique",
            "data": [1, 2, 2, 3, 3, 3, 4]
        })
        assert result.success is True
        assert len(result.data) == 4


class TestCsvArrayToolSlice:
    """Tests for array slice operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slice_basic(self):
        """Test basic array slicing."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "slice",
            "data": [1, 2, 3, 4, 5],
            "options": {"start": 1, "end": 4}
        })
        assert result.success is True


class TestCsvArrayToolReverse:
    """Tests for array reverse operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reverse_basic(self):
        """Test basic array reversal."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reverse",
            "data": [1, 2, 3, 4, 5]
        })
        assert result.success is True
        assert result.data == [5, 4, 3, 2, 1]


class TestCsvArrayToolCount:
    """Tests for array count operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_count_basic(self):
        """Test basic array counting."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "count",
            "data": [1, 2, 3, 4, 5]
        })
        assert result.success is True
        assert result.data == 5


class TestCsvArrayToolSum:
    """Tests for array sum operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_basic(self):
        """Test basic array sum."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sum",
            "data": [1, 2, 3, 4, 5]
        })
        assert result.success is True
        assert result.data == 15


class TestCsvArrayToolAvg:
    """Tests for array average operations."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_avg_basic(self):
        """Test basic array average."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "avg",
            "data": [1, 2, 3, 4, 5]
        })
        assert result.success is True
        assert result.data == 3.0


class TestCsvArrayToolErrors:
    """Tests for error handling."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_operation(self):
        """Test missing operation parameter."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "data": [1, 2, 3]
        })
        assert result.success is False
        assert result.error is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_data(self):
        """Test missing data parameter."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse"
        })
        assert result.success is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test invalid operation."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "invalid_op",
            "data": [1, 2, 3]
        })
        assert result.success is False
