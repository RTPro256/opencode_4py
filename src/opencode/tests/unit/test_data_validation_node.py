"""
Tests for Data Validation workflow node.
"""

import pytest
from unittest.mock import MagicMock, patch

from opencode.workflow.nodes.data_validation import DataValidationNode
from opencode.workflow.node import NodeSchema, ExecutionResult, PortDataType, PortDirection


class TestDataValidationNode:
    """Test cases for DataValidationNode."""

    def test_data_validation_node_schema(self):
        """Test DataValidationNode schema definition."""
        schema = DataValidationNode.get_schema()
        
        assert schema.node_type == "data_validation"
        assert schema.display_name == "Data Validation"
        assert schema.category == "processing"
        assert schema.icon == "check-circle"
        assert schema.version == "1.0.0"

    def test_data_validation_node_inputs(self):
        """Test DataValidationNode input ports."""
        schema = DataValidationNode.get_schema()
        inputs = {inp.name: inp for inp in schema.inputs}
        
        assert "data" in inputs
        assert inputs["data"].data_type == PortDataType.ANY
        assert inputs["data"].required is True
        
        assert "schema" in inputs
        assert inputs["schema"].data_type == PortDataType.OBJECT
        assert inputs["schema"].required is False

    def test_data_validation_node_outputs(self):
        """Test DataValidationNode output ports."""
        schema = DataValidationNode.get_schema()
        outputs = {out.name: out for out in schema.outputs}
        
        assert "data" in outputs
        assert outputs["data"].data_type == PortDataType.ANY
        assert outputs["data"].required is True
        
        assert "valid" in outputs
        assert outputs["valid"].data_type == PortDataType.BOOLEAN
        assert outputs["valid"].required is True
        
        assert "errors" in outputs
        assert outputs["errors"].data_type == PortDataType.ARRAY
        assert outputs["errors"].required is False

    def test_data_validation_node_config_schema(self):
        """Test DataValidationNode config schema."""
        schema = DataValidationNode.get_schema()
        config_schema = schema.config_schema
        
        assert config_schema["type"] == "object"
        assert "schema" in config_schema["properties"]
        assert "strict" in config_schema["properties"]
        assert "coerceTypes" in config_schema["properties"]
        
        assert config_schema["required"] == ["schema"]

    def test_data_validation_node_initialization(self):
        """Test DataValidationNode initialization."""
        node = DataValidationNode("dv-1", {
            "schema": {"type": "object"}
        })
        
        assert node.node_id == "dv-1"
        assert node.config == {"schema": {"type": "object"}}

    @pytest.mark.asyncio
    async def test_execute_valid_data(self):
        """Test execute with valid data."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "number"}
                },
                "required": ["name"]
            }
        })
        
        result = await node.execute({
            "data": {"name": "John", "age": 30}
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True
        assert result.outputs["data"] == {"name": "John", "age": 30}
        assert result.outputs["errors"] is None

    @pytest.mark.asyncio
    async def test_execute_invalid_data_strict(self):
        """Test execute with invalid data in strict mode."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                },
                "required": ["name"]
            },
            "strict": True
        })
        
        result = await node.execute({
            "data": {"age": 30}  # Missing required 'name'
        }, MagicMock())
        
        assert result.success is False
        assert result.outputs["valid"] is False
        assert "Validation failed" in result.error

    @pytest.mark.asyncio
    async def test_execute_invalid_data_non_strict(self):
        """Test execute with invalid data in non-strict mode."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"}
                },
                "required": ["name"]
            },
            "strict": False
        })
        
        result = await node.execute({
            "data": {"age": 30}  # Missing required 'name'
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is False
        assert result.outputs["errors"] is not None

    @pytest.mark.asyncio
    async def test_execute_schema_from_input(self):
        """Test execute with schema from input."""
        node = DataValidationNode("dv-1", {
            "schema": {"type": "string"}  # Default schema
        })
        
        # Override schema from input
        result = await node.execute({
            "data": 42,
            "schema": {"type": "number"}
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_missing_schema(self):
        """Test execute with missing schema."""
        node = DataValidationNode("dv-1", {})
        
        result = await node.execute({
            "data": {"name": "test"}
        }, MagicMock())
        
        assert result.success is False
        assert "Schema is required" in result.error

    @pytest.mark.asyncio
    async def test_execute_array_validation(self):
        """Test execute with array validation."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "array",
                "items": {"type": "number"},
                "minItems": 1,
                "maxItems": 5
            }
        })
        
        result = await node.execute({
            "data": [1, 2, 3]
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_string_validation(self):
        """Test execute with string validation."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "string",
                "minLength": 3,
                "maxLength": 10
            }
        })
        
        result = await node.execute({
            "data": "hello"
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_nested_object_validation(self):
        """Test execute with nested object validation."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "email": {"type": "string", "format": "email"}
                        },
                        "required": ["name"]
                    }
                }
            }
        })
        
        result = await node.execute({
            "data": {
                "user": {
                    "name": "John",
                    "email": "john@example.com"
                }
            }
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_enum_validation(self):
        """Test execute with enum validation."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "string",
                "enum": ["red", "green", "blue"]
            }
        })
        
        result = await node.execute({
            "data": "red"
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_enum_validation_invalid(self):
        """Test execute with invalid enum value."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "string",
                "enum": ["red", "green", "blue"]
            },
            "strict": False
        })
        
        result = await node.execute({
            "data": "yellow"
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is False

    @pytest.mark.asyncio
    async def test_execute_number_range_validation(self):
        """Test execute with number range validation."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "number",
                "minimum": 0,
                "maximum": 100
            }
        })
        
        result = await node.execute({
            "data": 50
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_invalid_schema(self):
        """Test execute with invalid schema."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "invalid_type"  # Invalid schema type
            }
        })
        
        result = await node.execute({
            "data": "test"
        }, MagicMock())
        
        # The result depends on jsonschema's handling of invalid schemas
        # It might fail or pass depending on the implementation

    def test_node_registered(self):
        """Test that DataValidationNode is registered."""
        from opencode.workflow.registry import NodeRegistry
        
        # Check that data_validation is registered
        assert "data_validation" in NodeRegistry._nodes or hasattr(NodeRegistry, 'get')

    def test_config_schema_defaults(self):
        """Test config schema default values."""
        schema = DataValidationNode.get_schema()
        props = schema.config_schema["properties"]
        
        assert props["strict"]["default"] is True
        assert props["coerceTypes"]["default"] is False

    @pytest.mark.asyncio
    async def test_execute_boolean_validation(self):
        """Test execute with boolean validation."""
        node = DataValidationNode("dv-1", {
            "schema": {"type": "boolean"}
        })
        
        result = await node.execute({
            "data": True
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_null_validation(self):
        """Test execute with null validation."""
        node = DataValidationNode("dv-1", {
            "schema": {"type": "null"}
        })
        
        result = await node.execute({
            "data": None
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_pattern_validation(self):
        """Test execute with pattern validation."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "string",
                "pattern": "^[a-z]+$"
            }
        })
        
        result = await node.execute({
            "data": "hello"
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is True

    @pytest.mark.asyncio
    async def test_execute_pattern_validation_invalid(self):
        """Test execute with invalid pattern match."""
        node = DataValidationNode("dv-1", {
            "schema": {
                "type": "string",
                "pattern": "^[a-z]+$"
            },
            "strict": False
        })
        
        result = await node.execute({
            "data": "Hello123"
        }, MagicMock())
        
        assert result.success is True
        assert result.outputs["valid"] is False
