"""
CSV/Array Tool

Utilities for working with CSV data and arrays in workflows.
"""

import csv
import io
import json
import logging
from typing import Any, Dict, List, Optional, Union, ClassVar

from opencode.workflow.tools.registry import BaseTool, ToolResult, ToolSchema, ToolRegistry

logger = logging.getLogger(__name__)


@ToolRegistry.register("csv_array")
class CsvArrayTool(BaseTool):
    """
    CSV/Array Tool - Utilities for CSV and array data manipulation.
    
    This tool provides various operations for working with CSV data
    and arrays in workflows, including parsing, formatting, filtering,
    and transforming data.
    
    Operations:
        - parse: Parse CSV string to array of objects
        - stringify: Convert array of objects to CSV string
        - filter: Filter array by conditions
        - map: Transform array elements
        - reduce: Reduce array to single value
        - sort: Sort array by field
        - group: Group array by field
        - merge: Merge multiple arrays
        - flatten: Flatten nested arrays
        - unique: Get unique values
    
    Example:
        tool = CsvArrayTool()
        result = await tool.execute({
            "operation": "parse",
            "data": "name,age\\nJohn,30\\nJane,25"
        })
    """
    
    _schema = ToolSchema(
        name="csv_array",
        description="Parse, format, and manipulate CSV and array data",
        parameters={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "enum": [
                        "parse", "stringify", "filter", "map", "reduce",
                        "sort", "group", "merge", "flatten", "unique",
                        "slice", "reverse", "count", "sum", "avg"
                    ],
                },
                "data": {
                    "type": "any",
                    "description": "Input data (CSV string or array)",
                },
                "options": {
                    "type": "object",
                    "description": "Operation-specific options",
                },
            },
        },
        required_params=["operation", "data"],
        returns="object",
        category="data",
        requires_auth=False,
    )
    
    @classmethod
    def get_schema(cls) -> ToolSchema:
        """Return the schema for this tool."""
        return cls._schema
    
    async def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        Execute a CSV/Array operation.
        
        Args:
            params: Dictionary containing:
                - operation: Operation to perform (required)
                - data: Input data (required)
                - options: Operation-specific options
            
        Returns:
            ToolResult with operation result
        """
        operation = params.get("operation")
        if not operation:
            return ToolResult(
                success=False,
                error="Required parameter 'operation' is missing",
            )
        
        data = params.get("data")
        if data is None:
            return ToolResult(
                success=False,
                error="Required parameter 'data' is missing",
            )
        
        options = params.get("options", {})
        
        # Dispatch to operation handler
        operations = {
            "parse": self._parse,
            "stringify": self._stringify,
            "filter": self._filter,
            "map": self._map,
            "reduce": self._reduce,
            "sort": self._sort,
            "group": self._group,
            "merge": self._merge,
            "flatten": self._flatten,
            "unique": self._unique,
            "slice": self._slice,
            "reverse": self._reverse,
            "count": self._count,
            "sum": self._sum,
            "avg": self._avg,
        }
        
        handler = operations.get(operation)
        if not handler:
            return ToolResult(
                success=False,
                error=f"Unknown operation: {operation}",
            )
        
        try:
            result = handler(data, options)
            return ToolResult(
                success=True,
                data=result,
                metadata={"operation": operation},
            )
        except Exception as e:
            logger.exception(f"CSV/Array operation failed: {e}")
            return ToolResult(
                success=False,
                error=f"Operation failed: {str(e)}",
            )
    
    def _parse(self, data: str, options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse CSV string to array of objects."""
        delimiter = options.get("delimiter", ",")
        has_header = options.get("has_header", True)
        skip_empty = options.get("skip_empty", True)
        
        reader = csv.reader(io.StringIO(data), delimiter=delimiter)
        rows = list(reader)
        
        if not rows:
            return []
        
        if has_header:
            headers = [h.strip() for h in rows[0]]
            data_rows = rows[1:]
        else:
            headers = [f"col_{i}" for i in range(len(rows[0]))]
            data_rows = rows
        
        result = []
        for row in data_rows:
            if skip_empty and not any(row):
                continue
            
            obj = {}
            for i, value in enumerate(row):
                if i < len(headers):
                    obj[headers[i]] = self._parse_value(value.strip())
            result.append(obj)
        
        return result
    
    def _stringify(self, data: List[Dict[str, Any]], options: Dict[str, Any]) -> str:
        """Convert array of objects to CSV string."""
        delimiter = options.get("delimiter", ",")
        include_header = options.get("include_header", True)
        
        if not data:
            return ""
        
        # Get all unique keys
        keys = []
        for item in data:
            for key in item.keys():
                if key not in keys:
                    keys.append(key)
        
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        
        if include_header:
            writer.writerow(keys)
        
        for item in data:
            row = [str(item.get(k, "")) for k in keys]
            writer.writerow(row)
        
        return output.getvalue()
    
    def _filter(self, data: List[Any], options: Dict[str, Any]) -> List[Any]:
        """Filter array by conditions."""
        field = options.get("field")
        operator = options.get("operator", "eq")
        value = options.get("value")
        
        result = []
        for item in data:
            if not isinstance(item, dict):
                continue
            
            item_value = item.get(field) if field else item
            
            if self._compare(item_value, operator, value):
                result.append(item)
        
        return result
    
    def _map(self, data: List[Any], options: Dict[str, Any]) -> List[Any]:
        """Transform array elements."""
        field = options.get("field")
        new_field = options.get("new_field")
        transform = options.get("transform", "identity")
        
        result = []
        for item in data:
            if isinstance(item, dict):
                new_item = dict(item)
                if field and new_field:
                    value = item.get(field)
                    new_item[new_field] = self._transform(value, transform)
                result.append(new_item)
            else:
                result.append(self._transform(item, transform))
        
        return result
    
    def _reduce(self, data: List[Any], options: Dict[str, Any]) -> Any:
        """Reduce array to single value."""
        field = options.get("field")
        operation = options.get("reduce_operation", "sum")
        initial = options.get("initial")
        
        values = [item.get(field) if isinstance(item, dict) else item for item in data]
        values = [v for v in values if v is not None]
        
        if not values:
            return initial
        
        if operation == "sum":
            return sum(float(v) for v in values if self._is_numeric(v))
        elif operation == "count":
            return len(values)
        elif operation == "min":
            return min(values)
        elif operation == "max":
            return max(values)
        elif operation == "concat":
            return "".join(str(v) for v in values)
        elif operation == "first":
            return values[0]
        elif operation == "last":
            return values[-1]
        
        return initial
    
    def _sort(self, data: List[Any], options: Dict[str, Any]) -> List[Any]:
        """Sort array by field."""
        field = options.get("field")
        reverse = options.get("reverse", False)
        
        def sort_key(item):
            if isinstance(item, dict):
                return item.get(field, "")
            return item
        
        return sorted(data, key=sort_key, reverse=reverse)
    
    def _group(self, data: List[Any], options: Dict[str, Any]) -> Dict[str, List[Any]]:
        """Group array by field."""
        field = options.get("field")
        
        groups: Dict[str, List[Any]] = {}
        for item in data:
            if isinstance(item, dict):
                key = str(item.get(field, "unknown"))
            else:
                key = str(item)
            
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        
        return groups
    
    def _merge(self, data: List[Any], options: Dict[str, Any]) -> List[Any]:
        """Merge multiple arrays."""
        additional = options.get("arrays", [])
        
        result = list(data)
        for arr in additional:
            if isinstance(arr, list):
                result.extend(arr)
        
        return result
    
    def _flatten(self, data: List[Any], options: Dict[str, Any]) -> List[Any]:
        """Flatten nested arrays."""
        depth = options.get("depth", 1)
        
        def flatten_recursive(items: List[Any], current_depth: int) -> List[Any]:
            if current_depth >= depth:
                return items
            
            result = []
            for item in items:
                if isinstance(item, list):
                    result.extend(flatten_recursive(item, current_depth + 1))
                else:
                    result.append(item)
            return result
        
        return flatten_recursive(data, 0)
    
    def _unique(self, data: List[Any], options: Dict[str, Any]) -> List[Any]:
        """Get unique values."""
        field = options.get("field")
        
        seen = set()
        result = []
        
        for item in data:
            if isinstance(item, dict) and field:
                key = str(item.get(field, id(item)))
            else:
                key = str(item) if not isinstance(item, (dict, list)) else json.dumps(item, sort_keys=True)
            
            if key not in seen:
                seen.add(key)
                result.append(item)
        
        return result
    
    def _slice(self, data: List[Any], options: Dict[str, Any]) -> List[Any]:
        """Slice array."""
        start = options.get("start", 0)
        end = options.get("end")
        
        return data[start:end]
    
    def _reverse(self, data: List[Any], options: Dict[str, Any]) -> List[Any]:
        """Reverse array."""
        return list(reversed(data))
    
    def _count(self, data: List[Any], options: Dict[str, Any]) -> int:
        """Count array elements."""
        return len(data)
    
    def _sum(self, data: List[Any], options: Dict[str, Any]) -> float:
        """Sum numeric values."""
        field = options.get("field")
        
        total = 0.0
        for item in data:
            if isinstance(item, dict) and field:
                value = item.get(field)
            else:
                value = item
            
            if self._is_numeric(value):
                total += float(value)
        
        return total
    
    def _avg(self, data: List[Any], options: Dict[str, Any]) -> float:
        """Calculate average."""
        field = options.get("field")
        
        values = []
        for item in data:
            if isinstance(item, dict) and field:
                value = item.get(field)
            else:
                value = item
            
            if self._is_numeric(value):
                values.append(float(value))
        
        return sum(values) / len(values) if values else 0.0
    
    def _parse_value(self, value: str) -> Any:
        """Parse string value to appropriate type."""
        if not value:
            return ""
        
        # Try boolean
        if value.lower() in ("true", "false"):
            return value.lower() == "true"
        
        # Try null
        if value.lower() in ("null", "none", "nil"):
            return None
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Try JSON
        if value.startswith(("{", "[")):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        return value
    
    def _compare(self, value: Any, operator: str, target: Any) -> bool:
        """Compare values."""
        if operator == "eq":
            return value == target
        elif operator == "ne":
            return value != target
        elif operator == "gt":
            return value > target
        elif operator == "gte":
            return value >= target
        elif operator == "lt":
            return value < target
        elif operator == "lte":
            return value <= target
        elif operator == "contains":
            return target in str(value)
        elif operator == "startswith":
            return str(value).startswith(target)
        elif operator == "endswith":
            return str(value).endswith(target)
        elif operator == "in":
            return value in target if isinstance(target, list) else False
        elif operator == "not_in":
            return value not in target if isinstance(target, list) else True
        
        return False
    
    def _transform(self, value: Any, transform: str) -> Any:
        """Apply transformation to value."""
        if transform == "identity":
            return value
        elif transform == "string":
            return str(value)
        elif transform == "int":
            return int(float(value)) if self._is_numeric(value) else 0
        elif transform == "float":
            return float(value) if self._is_numeric(value) else 0.0
        elif transform == "upper":
            return str(value).upper()
        elif transform == "lower":
            return str(value).lower()
        elif transform == "strip":
            return str(value).strip()
        elif transform == "length":
            return len(value) if hasattr(value, "__len__") else 0
        
        return value
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if value is numeric."""
        if isinstance(value, (int, float)):
            return True
        if isinstance(value, str):
            try:
                float(value)
                return True
            except ValueError:
                return False
        return False
