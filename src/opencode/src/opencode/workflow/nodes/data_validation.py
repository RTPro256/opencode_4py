"""
Data Validation Node

Handles schema validation for workflow data.
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


@NodeRegistry.register("data_validation")
class DataValidationNode(BaseNode):
    """
    Data Validation Node - Schema validation.
    
    This node validates input data against a JSON schema
    and passes through valid data or raises errors.
    
    Configuration:
        schema: JSON schema to validate against
        strict: Whether to fail on validation errors
        coerceTypes: Whether to coerce types (e.g., string to number)
    """
    
    _schema = NodeSchema(
        node_type="data_validation",
        display_name="Data Validation",
        description="Validate data against a JSON schema",
        category="processing",
        icon="check-circle",
        inputs=[
            NodePort(
                name="data",
                data_type=PortDataType.ANY,
                direction=PortDirection.INPUT,
                required=True,
                description="Data to validate",
            ),
            NodePort(
                name="schema",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.INPUT,
                required=False,
                description="Override JSON schema",
            ),
        ],
        outputs=[
            NodePort(
                name="data",
                data_type=PortDataType.ANY,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Validated data (passed through)",
            ),
            NodePort(
                name="valid",
                data_type=PortDataType.BOOLEAN,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Whether validation passed",
            ),
            NodePort(
                name="errors",
                data_type=PortDataType.ARRAY,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Validation errors (if any)",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "schema": {
                    "type": "object",
                    "description": "JSON schema to validate against",
                },
                "strict": {
                    "type": "boolean",
                    "default": True,
                    "description": "Fail on validation errors",
                },
                "coerceTypes": {
                    "type": "boolean",
                    "default": False,
                    "description": "Coerce types where possible",
                },
            },
            "required": ["schema"],
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
        """Execute the data validation node."""
        import time
        start_time = time.time()
        
        try:
            import jsonschema
        except ImportError:
            return ExecutionResult(
                success=False,
                error="jsonschema is required for validation. Install with: pip install jsonschema",
            )
        
        try:
            data = inputs.get("data")
            schema = inputs.get("schema") or self.config.get("schema")
            
            if not schema:
                return ExecutionResult(
                    success=False,
                    error="Schema is required for validation",
                )
            
            errors: List[str] = []
            valid = True
            
            try:
                # Validate against schema
                jsonschema.validate(instance=data, schema=schema)
            except jsonschema.ValidationError as e:
                valid = False
                errors.append(str(e.message))
                if hasattr(e, 'path') and e.path:
                    errors.append(f"Path: {'.'.join(str(p) for p in e.path)}")
            except jsonschema.SchemaError as e:
                return ExecutionResult(
                    success=False,
                    error=f"Invalid schema: {e.message}",
                )
            
            # Check strict mode
            strict = self.config.get("strict", True)
            if not valid and strict:
                duration_ms = (time.time() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    outputs={
                        "data": data,
                        "valid": False,
                        "errors": errors,
                    },
                    error=f"Validation failed: {'; '.join(errors)}",
                    duration_ms=duration_ms,
                )
            
            duration_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=True,
                outputs={
                    "data": data,
                    "valid": valid,
                    "errors": errors if errors else None,
                },
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            logger.exception(f"Data validation failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
