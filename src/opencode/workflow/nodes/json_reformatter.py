"""
JSON Reformatter Node

Handles JSON transformation for workflow data.
"""

import json
from typing import Any, Dict, List, Optional
import logging

from opencode.workflow.node import (
    BaseNode,
    NodePort,
    NodeSchema,
    ExecutionContext,
    ExecutionResult,
    PortDataType,
    PortDirection,
)
from opencode.workflow.registry import NodeRegistry

logger = logging.getLogger(__name__)


@NodeRegistry.register("json_reformatter")
class JsonReformatterNode(BaseNode):
    """
    JSON Reformatter Node - JSON transformation.
    
    This node transforms JSON data using various operations:
    - Field mapping/renaming
    - Field extraction
    - Array operations (map, filter, reduce)
    - Template-based transformation
    
    Configuration:
        operations: List of transformation operations
        template: Template for output structure
        extractPath: JSONPath to extract specific fields
    """
    
    _schema = NodeSchema(
        node_type="json_reformatter",
        display_name="JSON Reformatter",
        description="Transform and reformat JSON data",
        category="processing",
        icon="code",
        inputs=[
            NodePort(
                name="data",
                data_type=PortDataType.ANY,
                direction=PortDirection.INPUT,
                required=True,
                description="Input data to transform",
            ),
            NodePort(
                name="template",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.INPUT,
                required=False,
                description="Override output template",
            ),
        ],
        outputs=[
            NodePort(
                name="output",
                data_type=PortDataType.ANY,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Transformed data",
            ),
            NodePort(
                name="original",
                data_type=PortDataType.ANY,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Original input data",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "operations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": ["map", "filter", "extract", "rename", "merge", "flatten"],
                            },
                            "field": {"type": "string"},
                            "newField": {"type": "string"},
                            "value": {},
                            "expression": {"type": "string"},
                        },
                    },
                    "description": "List of transformation operations",
                },
                "template": {
                    "type": "object",
                    "description": "Template for output structure",
                },
                "extractPath": {
                    "type": "string",
                    "description": "JSONPath to extract specific fields",
                },
            },
        },
        version="1.0.0",
    )
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        return cls._schema
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """Execute the JSON reformatter node."""
        import time
        start_time = time.time()
        
        try:
            data = inputs.get("data")
            original_data = data
            
            # Apply template if provided
            template = inputs.get("template") or self.config.get("template")
            if template:
                data = self._apply_template(data, template)
            
            # Apply operations
            operations = self.config.get("operations", [])
            for op in operations:
                data = self._apply_operation(data, op)
            
            # Extract path if specified
            extract_path = self.config.get("extractPath")
            if extract_path:
                data = self._extract_path(data, extract_path)
            
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=True,
                outputs={
                    "output": data,
                    "original": original_data,
                },
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            logger.exception(f"JSON reformatting failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
    
    def _apply_template(self, data: Any, template: Dict[str, Any]) -> Any:
        """Apply a template to transform data."""
        result = {}
        
        for key, value in template.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to input data
                path = value[1:]  # Remove $ prefix
                result[key] = self._extract_path(data, path)
            elif isinstance(value, dict):
                result[key] = self._apply_template(data, value)
            elif isinstance(value, list):
                result[key] = [self._apply_template(data, item) if isinstance(item, dict) else item for item in value]
            else:
                result[key] = value
        
        return result
    
    def _apply_operation(self, data: Any, operation: Dict[str, Any]) -> Any:
        """Apply a single transformation operation."""
        op_type = operation.get("type")
        
        if op_type == "extract":
            field = operation.get("field")
            if isinstance(data, dict) and field in data:
                return data[field]
            return data
        
        elif op_type == "rename":
            field = operation.get("field")
            new_field = operation.get("newField")
            if isinstance(data, dict) and field in data:
                data[new_field] = data.pop(field)
            return data
        
        elif op_type == "map":
            if isinstance(data, list):
                field = operation.get("field")
                return [item.get(field) if isinstance(item, dict) else item for item in data]
            return data
        
        elif op_type == "filter":
            if isinstance(data, list):
                field = operation.get("field")
                value = operation.get("value")
                return [item for item in data if isinstance(item, dict) and item.get(field) == value]
            return data
        
        elif op_type == "merge":
            if isinstance(data, dict):
                value = operation.get("value", {})
                if isinstance(value, dict):
                    return {**data, **value}
            return data
        
        elif op_type == "flatten":
            if isinstance(data, list):
                result = []
                for item in data:
                    if isinstance(item, list):
                        result.extend(item)
                    else:
                        result.append(item)
                return result
            return data
        
        return data
    
    def _extract_path(self, data: Any, path: str) -> Any:
        """Extract a value from data using a simple path syntax."""
        if not path:
            return data
        
        parts = path.split(".")
        current = data
        
        for part in parts:
            if current is None:
                return None
            
            # Handle array indices
            if "[" in part and part.endswith("]"):
                field = part.split("[")[0]
                index = int(part.split("[")[1].rstrip("]"))
                
                if field:
                    if isinstance(current, dict) and field in current:
                        current = current[field]
                    else:
                        return None
                
                if isinstance(current, list) and 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return None
        
        return current
