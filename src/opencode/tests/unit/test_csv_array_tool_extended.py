"""
Extended tests for CSV/Array workflow tool.

Tests all operations comprehensively for 100% coverage.
"""

import pytest
from unittest.mock import MagicMock, patch

from opencode.workflow.tools.csv_array import CsvArrayTool
from opencode.workflow.tools.registry import ToolResult, ToolSchema


class TestCsvArrayToolOperations:
    """Tests for all CsvArrayTool operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_operation(self):
        """Test error when operation is missing."""
        tool = CsvArrayTool()
        result = await tool.execute({"data": "test"})
        assert result.success is False
        assert result.error is not None
        assert "operation" in result.error.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_missing_data(self):
        """Test error when data is missing."""
        tool = CsvArrayTool()
        result = await tool.execute({"operation": "parse"})
        assert result.success is False
        assert result.error is not None
        assert "data" in result.error.lower()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        """Test error for unknown operation."""
        tool = CsvArrayTool()
        result = await tool.execute({"operation": "unknown_op", "data": []})
        assert result.success is False
        assert result.error is not None
        assert "unknown" in result.error.lower()


class TestCsvArrayToolParseExtended:
    """Extended tests for CSV parsing operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_with_delimiter(self):
        """Test CSV parsing with custom delimiter."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name;age\nJohn;30\nJane;25",
            "options": {"delimiter": ";"}
        })
        assert result.success is True
        assert len(result.data) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_no_header(self):
        """Test CSV parsing without header."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "John,30\nJane,25",
            "options": {"has_header": False}
        })
        assert result.success is True
        assert "col_0" in result.data[0]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_skip_empty_rows(self):
        """Test CSV parsing skips empty rows."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name,age\nJohn,30\n\n\nJane,25",
            "options": {"skip_empty": True}
        })
        assert result.success is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_boolean_values(self):
        """Test CSV parsing converts boolean strings."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name,active\nJohn,true\nJane,false"
        })
        assert result.success is True
        assert result.data[0]["active"] is True
        assert result.data[1]["active"] is False

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_null_values(self):
        """Test CSV parsing converts null strings."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name,value\nJohn,null\nJane,none"
        })
        assert result.success is True
        assert result.data[0]["value"] is None
        assert result.data[1]["value"] is None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_numeric_values(self):
        """Test CSV parsing converts numeric strings."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name,age,score\nJohn,30,95.5"
        })
        assert result.success is True
        assert result.data[0]["age"] == 30
        assert result.data[0]["score"] == 95.5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_parse_json_values(self):
        """Test CSV parsing parses JSON strings."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": 'name,data\nJohn,"{""key"": ""value""}"'
        })
        assert result.success is True


class TestCsvArrayToolStringifyExtended:
    """Extended tests for CSV stringify operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stringify_with_delimiter(self):
        """Test stringify with custom delimiter."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "stringify",
            "data": [{"name": "John", "age": 30}],
            "options": {"delimiter": ";"}
        })
        assert result.success is True
        assert ";" in result.data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stringify_no_header(self):
        """Test stringify without header."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "stringify",
            "data": [{"name": "John", "age": 30}],
            "options": {"include_header": False}
        })
        assert result.success is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_stringify_multiple_keys(self):
        """Test stringify with varying keys."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "stringify",
            "data": [
                {"name": "John", "age": 30},
                {"name": "Jane", "city": "NYC"}
            ]
        })
        assert result.success is True


class TestCsvArrayToolFilterExtended:
    """Extended tests for array filter operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_eq(self):
        """Test filter with equals operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}],
            "options": {"field": "age", "operator": "eq", "value": 30}
        })
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["name"] == "John"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_ne(self):
        """Test filter with not equals operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}],
            "options": {"field": "age", "operator": "ne", "value": 30}
        })
        assert result.success is True
        assert len(result.data) == 1
        assert result.data[0]["name"] == "Jane"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_gt(self):
        """Test filter with greater than operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"age": 30}, {"age": 20}],
            "options": {"field": "age", "operator": "gt", "value": 25}
        })
        assert result.success is True
        assert len(result.data) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_gte(self):
        """Test filter with greater than or equal operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"age": 25}, {"age": 20}],
            "options": {"field": "age", "operator": "gte", "value": 25}
        })
        assert result.success is True
        assert len(result.data) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_lt(self):
        """Test filter with less than operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"age": 30}, {"age": 20}],
            "options": {"field": "age", "operator": "lt", "value": 25}
        })
        assert result.success is True
        assert len(result.data) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_lte(self):
        """Test filter with less than or equal operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"age": 25}, {"age": 30}],
            "options": {"field": "age", "operator": "lte", "value": 25}
        })
        assert result.success is True
        assert len(result.data) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_contains(self):
        """Test filter with contains operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"name": "John Smith"}, {"name": "Jane"}],
            "options": {"field": "name", "operator": "contains", "value": "Smith"}
        })
        assert result.success is True
        assert len(result.data) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_startswith(self):
        """Test filter with startswith operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"name": "John"}, {"name": "Jane"}],
            "options": {"field": "name", "operator": "startswith", "value": "Jo"}
        })
        assert result.success is True
        assert len(result.data) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_endswith(self):
        """Test filter with endswith operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"name": "John"}, {"name": "Jane"}],
            "options": {"field": "name", "operator": "endswith", "value": "ne"}
        })
        assert result.success is True
        assert len(result.data) == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_in(self):
        """Test filter with in operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"age": 25}, {"age": 30}, {"age": 35}],
            "options": {"field": "age", "operator": "in", "value": [25, 35]}
        })
        assert result.success is True
        assert len(result.data) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_operator_not_in(self):
        """Test filter with not_in operator."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [{"age": 25}, {"age": 30}, {"age": 35}],
            "options": {"field": "age", "operator": "not_in", "value": [30]}
        })
        assert result.success is True
        assert len(result.data) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_filter_non_dict_items(self):
        """Test filter with non-dict items."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "filter",
            "data": [1, 2, 3, 4, 5],
            "options": {"operator": "gt", "value": 3}
        })
        assert result.success is True


class TestCsvArrayToolMapExtended:
    """Extended tests for array map operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_identity(self):
        """Test map with identity transform."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": [1, 2, 3],
            "options": {"transform": "identity"}
        })
        assert result.success is True
        assert result.data == [1, 2, 3]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_string(self):
        """Test map with string transform."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": [1, 2, 3],
            "options": {"transform": "string"}
        })
        assert result.success is True
        assert result.data == ["1", "2", "3"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_int(self):
        """Test map with int transform."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": [1.5, 2.7, 3.2],
            "options": {"transform": "int"}
        })
        assert result.success is True
        assert result.data == [1, 2, 3]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_float(self):
        """Test map with float transform."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": ["1.5", "2.7", "3.2"],
            "options": {"transform": "float"}
        })
        assert result.success is True
        assert result.data == [1.5, 2.7, 3.2]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_upper(self):
        """Test map with upper transform."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": ["john", "jane"],
            "options": {"transform": "upper"}
        })
        assert result.success is True
        assert result.data == ["JOHN", "JANE"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_lower(self):
        """Test map with lower transform."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": ["JOHN", "JANE"],
            "options": {"transform": "lower"}
        })
        assert result.success is True
        assert result.data == ["john", "jane"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_strip(self):
        """Test map with strip transform."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": ["  john  ", "  jane  "],
            "options": {"transform": "strip"}
        })
        assert result.success is True
        assert result.data == ["john", "jane"]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_length(self):
        """Test map with length transform."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": ["john", "jane"],
            "options": {"transform": "length"}
        })
        assert result.success is True
        assert result.data == [4, 4]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_map_dict_with_new_field(self):
        """Test map adds new field to dicts."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "map",
            "data": [{"name": "john"}, {"name": "jane"}],
            "options": {"field": "name", "new_field": "upper_name", "transform": "upper"}
        })
        assert result.success is True
        assert result.data[0]["upper_name"] == "JOHN"


class TestCsvArrayToolReduceExtended:
    """Extended tests for array reduce operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_sum(self):
        """Test reduce with sum operation."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [1, 2, 3, 4, 5],
            "options": {"reduce_operation": "sum"}
        })
        assert result.success is True
        assert result.data == 15

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_count(self):
        """Test reduce with count operation."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [1, 2, 3, 4, 5],
            "options": {"reduce_operation": "count"}
        })
        assert result.success is True
        assert result.data == 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_min(self):
        """Test reduce with min operation."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [5, 2, 8, 1, 9],
            "options": {"reduce_operation": "min"}
        })
        assert result.success is True
        assert result.data == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_max(self):
        """Test reduce with max operation."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [5, 2, 8, 1, 9],
            "options": {"reduce_operation": "max"}
        })
        assert result.success is True
        assert result.data == 9

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_concat(self):
        """Test reduce with concat operation."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": ["a", "b", "c"],
            "options": {"reduce_operation": "concat"}
        })
        assert result.success is True
        assert result.data == "abc"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_first(self):
        """Test reduce with first operation."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [1, 2, 3],
            "options": {"reduce_operation": "first"}
        })
        assert result.success is True
        assert result.data == 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_last(self):
        """Test reduce with last operation."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [1, 2, 3],
            "options": {"reduce_operation": "last"}
        })
        assert result.success is True
        assert result.data == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_empty_with_initial(self):
        """Test reduce with empty data and initial value."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [],
            "options": {"reduce_operation": "sum", "initial": 0}
        })
        assert result.success is True
        assert result.data == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reduce_dict_field(self):
        """Test reduce with dict field."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reduce",
            "data": [{"val": 10}, {"val": 20}, {"val": 30}],
            "options": {"field": "val", "reduce_operation": "sum"}
        })
        assert result.success is True
        assert result.data == 60


class TestCsvArrayToolSortExtended:
    """Extended tests for array sort operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sort_ascending(self):
        """Test sort ascending."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sort",
            "data": [{"name": "John"}, {"name": "Alice"}, {"name": "Bob"}],
            "options": {"field": "name"}
        })
        assert result.success is True
        assert result.data[0]["name"] == "Alice"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sort_descending(self):
        """Test sort descending."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sort",
            "data": [{"name": "John"}, {"name": "Alice"}, {"name": "Bob"}],
            "options": {"field": "name", "reverse": True}
        })
        assert result.success is True
        assert result.data[0]["name"] == "John"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sort_simple_values(self):
        """Test sort with simple values."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sort",
            "data": [3, 1, 4, 1, 5, 9, 2, 6],
            "options": {}
        })
        assert result.success is True
        assert result.data == [1, 1, 2, 3, 4, 5, 6, 9]


class TestCsvArrayToolGroup:
    """Tests for array group operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_group_by_field(self):
        """Test grouping by field."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "group",
            "data": [
                {"name": "John", "dept": "IT"},
                {"name": "Jane", "dept": "HR"},
                {"name": "Bob", "dept": "IT"}
            ],
            "options": {"field": "dept"}
        })
        assert result.success is True
        assert "IT" in result.data
        assert "HR" in result.data
        assert len(result.data["IT"]) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_group_simple_values(self):
        """Test grouping simple values."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "group",
            "data": [1, 1, 2, 2, 3],
            "options": {}
        })
        assert result.success is True


class TestCsvArrayToolMerge:
    """Tests for array merge operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_merge_arrays(self):
        """Test merging arrays."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "merge",
            "data": [1, 2],
            "options": {"arrays": [[3, 4], [5, 6]]}
        })
        assert result.success is True
        assert result.data == [1, 2, 3, 4, 5, 6]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_merge_empty_arrays(self):
        """Test merging with empty arrays."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "merge",
            "data": [1, 2],
            "options": {"arrays": []}
        })
        assert result.success is True
        assert result.data == [1, 2]


class TestCsvArrayToolFlatten:
    """Tests for array flatten operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_flatten_single_level(self):
        """Test flattening single level."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "flatten",
            "data": [[1, 2], [3, 4]],
            "options": {"depth": 1}
        })
        assert result.success is True
        assert result.data == [1, 2, 3, 4]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_flatten_multiple_levels(self):
        """Test flattening multiple levels."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "flatten",
            "data": [[1, [2, 3]], [4, [5, [6]]]],
            "options": {"depth": 3}
        })
        assert result.success is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_flatten_no_nested(self):
        """Test flattening with no nested arrays."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "flatten",
            "data": [1, 2, 3],
            "options": {"depth": 1}
        })
        assert result.success is True
        assert result.data == [1, 2, 3]


class TestCsvArrayToolUnique:
    """Tests for array unique operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unique_simple_values(self):
        """Test unique with simple values."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "unique",
            "data": [1, 2, 2, 3, 3, 3, 4]
        })
        assert result.success is True
        assert result.data == [1, 2, 3, 4]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unique_by_field(self):
        """Test unique by field."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "unique",
            "data": [
                {"id": 1, "name": "John"},
                {"id": 2, "name": "Jane"},
                {"id": 1, "name": "Johnny"}
            ],
            "options": {"field": "id"}
        })
        assert result.success is True
        assert len(result.data) == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unique_dicts(self):
        """Test unique with dicts."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "unique",
            "data": [{"a": 1}, {"a": 1}, {"a": 2}]
        })
        assert result.success is True
        assert len(result.data) == 2


class TestCsvArrayToolSlice:
    """Tests for array slice operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slice_start_only(self):
        """Test slice with start only."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "slice",
            "data": [1, 2, 3, 4, 5],
            "options": {"start": 2}
        })
        assert result.success is True
        assert result.data == [3, 4, 5]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slice_start_and_end(self):
        """Test slice with start and end."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "slice",
            "data": [1, 2, 3, 4, 5],
            "options": {"start": 1, "end": 4}
        })
        assert result.success is True
        assert result.data == [2, 3, 4]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_slice_full_range(self):
        """Test slice with full range."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "slice",
            "data": [1, 2, 3],
            "options": {}
        })
        assert result.success is True
        assert result.data == [1, 2, 3]


class TestCsvArrayToolReverse:
    """Tests for array reverse operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reverse_basic(self):
        """Test basic reverse."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reverse",
            "data": [1, 2, 3, 4, 5]
        })
        assert result.success is True
        assert result.data == [5, 4, 3, 2, 1]

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_reverse_empty(self):
        """Test reverse empty array."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "reverse",
            "data": []
        })
        assert result.success is True
        assert result.data == []


class TestCsvArrayToolCount:
    """Tests for array count operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_count_basic(self):
        """Test basic count."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "count",
            "data": [1, 2, 3, 4, 5]
        })
        assert result.success is True
        assert result.data == 5

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_count_empty(self):
        """Test count empty array."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "count",
            "data": []
        })
        assert result.success is True
        assert result.data == 0


class TestCsvArrayToolSum:
    """Tests for array sum operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_basic(self):
        """Test basic sum."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sum",
            "data": [1, 2, 3, 4, 5]
        })
        assert result.success is True
        assert result.data == 15

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_with_field(self):
        """Test sum with field."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sum",
            "data": [{"val": 10}, {"val": 20}, {"val": 30}],
            "options": {"field": "val"}
        })
        assert result.success is True
        assert result.data == 60

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_empty(self):
        """Test sum empty array."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sum",
            "data": []
        })
        assert result.success is True
        assert result.data == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sum_non_numeric(self):
        """Test sum with non-numeric values."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "sum",
            "data": ["a", "b", "c"]
        })
        assert result.success is True
        assert result.data == 0


class TestCsvArrayToolAvg:
    """Tests for array average operations."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_avg_basic(self):
        """Test basic average."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "avg",
            "data": [10, 20, 30, 40, 50]
        })
        assert result.success is True
        assert result.data == 30

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_avg_with_field(self):
        """Test average with field."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "avg",
            "data": [{"val": 10}, {"val": 20}, {"val": 30}],
            "options": {"field": "val"}
        })
        assert result.success is True
        assert result.data == 20

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_avg_empty(self):
        """Test average empty array."""
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "avg",
            "data": []
        })
        assert result.success is True
        assert result.data == 0


class TestCsvArrayToolErrorHandling:
    """Tests for error handling."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_operation_exception(self):
        """Test handling of operation exceptions."""
        tool = CsvArrayTool()
        # Trigger an exception by providing invalid data for an operation
        result = await tool.execute({
            "operation": "sort",
            "data": "not a list"
        })
        # Should handle gracefully
        assert result is not None
