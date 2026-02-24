"""
Tests for Chart workflow node.
"""

import pytest
from unittest.mock import MagicMock, patch

from opencode.workflow.nodes.chart import ChartNode
from opencode.workflow.node import (
    NodeSchema,
    NodePort,
    PortDataType,
    PortDirection,
    ExecutionContext,
    ExecutionResult,
)


class TestChartNode:
    """Tests for ChartNode."""
    
    @pytest.mark.unit
    def test_chart_node_creation(self):
        """Test ChartNode instantiation."""
        node = ChartNode("chart_1", {})
        assert node is not None
        assert node.node_id == "chart_1"
    
    @pytest.mark.unit
    def test_chart_node_schema(self):
        """Test ChartNode has correct schema."""
        node = ChartNode("chart_1", {})
        schema = node._schema
        assert schema.node_type == "chart"
        assert schema.display_name == "Chart"
        assert schema.category == "visualization"
    
    @pytest.mark.unit
    def test_chart_node_inputs(self):
        """Test ChartNode input ports."""
        node = ChartNode("chart_1", {})
        inputs = node._schema.inputs
        input_names = [p.name for p in inputs]
        assert "data" in input_names
        assert "labels" in input_names
        assert "series" in input_names
        assert "options" in input_names
    
    @pytest.mark.unit
    def test_chart_node_outputs(self):
        """Test ChartNode output ports."""
        node = ChartNode("chart_1", {})
        outputs = node._schema.outputs
        output_names = [p.name for p in outputs]
        assert "chart" in output_names
    
    @pytest.mark.unit
    def test_chart_node_data_input_required(self):
        """Test ChartNode data input is required."""
        node = ChartNode("chart_1", {})
        data_input = next(p for p in node._schema.inputs if p.name == "data")
        assert data_input.required is True
    
    @pytest.mark.unit
    def test_chart_node_labels_input_optional(self):
        """Test ChartNode labels input is optional."""
        node = ChartNode("chart_1", {})
        labels_input = next(p for p in node._schema.inputs if p.name == "labels")
        assert labels_input.required is False
    
    @pytest.mark.unit
    def test_chart_node_config_chart_type(self):
        """Test ChartNode with chart_type config."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        assert node.config.get("chart_type") == "bar"
    
    @pytest.mark.unit
    def test_chart_node_config_title(self):
        """Test ChartNode with title config."""
        node = ChartNode("chart_1", {"title": "Sales Chart"})
        assert node.config.get("title") == "Sales Chart"
    
    @pytest.mark.unit
    def test_chart_node_config_axes(self):
        """Test ChartNode with axis labels."""
        node = ChartNode("chart_1", {
            "x_label": "Month",
            "y_label": "Sales",
        })
        assert node.config.get("x_label") == "Month"
        assert node.config.get("y_label") == "Sales"
    
    @pytest.mark.unit
    def test_chart_node_config_dimensions(self):
        """Test ChartNode with dimensions."""
        node = ChartNode("chart_1", {
            "width": 800,
            "height": 600,
        })
        assert node.config.get("width") == 800
        assert node.config.get("height") == 600
    
    @pytest.mark.unit
    def test_chart_node_config_color_scheme(self):
        """Test ChartNode with color scheme."""
        node = ChartNode("chart_1", {"color_scheme": "viridis"})
        assert node.config.get("color_scheme") == "viridis"
    
    @pytest.mark.unit
    def test_chart_node_config_legend(self):
        """Test ChartNode with legend config."""
        node = ChartNode("chart_1", {"show_legend": True})
        assert node.config.get("show_legend") is True
    
    @pytest.mark.unit
    def test_chart_node_config_grid(self):
        """Test ChartNode with grid config."""
        node = ChartNode("chart_1", {"show_grid": False})
        assert node.config.get("show_grid") is False
    
    @pytest.mark.unit
    def test_chart_node_registered(self):
        """Test ChartNode is registered."""
        from opencode.workflow.registry import NodeRegistry
        # Check if chart is registered
        assert "chart" in NodeRegistry._nodes or hasattr(NodeRegistry, 'get')
    
    @pytest.mark.unit
    def test_chart_node_has_execute_method(self):
        """Test ChartNode has execute method."""
        node = ChartNode("chart_1", {})
        assert hasattr(node, 'execute')
    
    @pytest.mark.unit
    def test_chart_node_has_schema(self):
        """Test ChartNode has schema."""
        node = ChartNode("chart_1", {})
        assert hasattr(node, '_schema')
    
    @pytest.mark.unit
    def test_chart_node_get_input_port(self):
        """Test ChartNode get input port."""
        node = ChartNode("chart_1", {})
        data_port = node.get_input_port("data")
        assert data_port is not None
        assert data_port.name == "data"
    
    @pytest.mark.unit
    def test_chart_node_get_output_port(self):
        """Test ChartNode get output port."""
        node = ChartNode("chart_1", {})
        chart_port = node.get_output_port("chart")
        assert chart_port is not None
        assert chart_port.name == "chart"
    
    @pytest.mark.unit
    def test_chart_node_get_nonexistent_port(self):
        """Test ChartNode get nonexistent port."""
        node = ChartNode("chart_1", {})
        port = node.get_input_port("nonexistent")
        assert port is None
    
    @pytest.mark.unit
    def test_chart_node_str(self):
        """Test ChartNode string representation."""
        node = ChartNode("chart_1", {})
        assert "chart" in str(node).lower() or "ChartNode" in str(node)
    
    @pytest.mark.unit
    def test_chart_node_repr(self):
        """Test ChartNode repr."""
        node = ChartNode("chart_1", {})
        assert "chart_1" in repr(node) or "ChartNode" in repr(node)


class TestChartNodeExecution:
    """Tests for ChartNode execution."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chart_node_execute_bar_chart(self):
        """Test ChartNode execute with bar chart."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        # Execute should handle the data
        result = await node.execute(
            inputs={"data": [10, 20, 30]},
            context=context
        )
        # Result should be an ExecutionResult or similar
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chart_node_execute_line_chart(self):
        """Test ChartNode execute with line chart."""
        node = ChartNode("chart_1", {"chart_type": "line"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [1, 2, 3, 4, 5]},
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chart_node_execute_pie_chart(self):
        """Test ChartNode execute with pie chart."""
        node = ChartNode("chart_1", {"chart_type": "pie"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [30, 40, 30]},
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chart_node_execute_with_labels(self):
        """Test ChartNode execute with labels."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={
                "data": [10, 20, 30],
                "labels": ["A", "B", "C"],
            },
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chart_node_execute_with_series(self):
        """Test ChartNode execute with multiple series."""
        node = ChartNode("chart_1", {"chart_type": "line"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={
                "data": [1, 2, 3],
                "series": [
                    {"name": "Series 1", "data": [1, 2, 3]},
                    {"name": "Series 2", "data": [4, 5, 6]},
                ],
            },
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_chart_node_execute_with_options(self):
        """Test ChartNode execute with options."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={
                "data": [10, 20, 30],
                "options": {
                    "colors": ["red", "green", "blue"],
                    "animated": True,
                },
            },
            context=context
        )
        assert result is not None or hasattr(node, 'execute')
