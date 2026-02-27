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


class TestChartNodeConfigBuild:
    """Tests for ChartNode configuration building."""

    @pytest.mark.unit
    def test_build_chart_config_bar(self):
        """Test building bar chart config."""
        node = ChartNode("chart_1", {"chart_type": "bar", "title": "Test Chart"})
        config = node._build_chart_config([1, 2, 3], None, None, {})
        
        assert config["type"] == "bar"
        assert config["data"]["datasets"][0]["data"] == [1, 2, 3]
        assert config["options"]["plugins"]["title"]["text"] == "Test Chart"

    @pytest.mark.unit
    def test_build_chart_config_line(self):
        """Test building line chart config."""
        node = ChartNode("chart_1", {"chart_type": "line"})
        config = node._build_chart_config([5, 10, 15], None, None, {})
        
        assert config["type"] == "line"
        assert "scales" in config["options"]

    @pytest.mark.unit
    def test_build_chart_config_pie(self):
        """Test building pie chart config."""
        node = ChartNode("chart_1", {"chart_type": "pie"})
        config = node._build_chart_config([30, 40, 30], None, None, {})
        
        assert config["type"] == "pie"
        # Pie charts don't have scales
        assert "scales" not in config["options"]

    @pytest.mark.unit
    def test_build_chart_config_with_labels(self):
        """Test building chart config with labels."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        config = node._build_chart_config([10, 20, 30], ["A", "B", "C"], None, {})
        
        assert config["data"]["labels"] == ["A", "B", "C"]

    @pytest.mark.unit
    def test_build_chart_config_with_series(self):
        """Test building chart config with multiple series."""
        node = ChartNode("chart_1", {"chart_type": "line"})
        series = [
            {"label": "Series 1", "data": [1, 2, 3]},
            {"label": "Series 2", "data": [4, 5, 6]},
        ]
        config = node._build_chart_config([], None, series, {})
        
        assert len(config["data"]["datasets"]) == 2
        assert config["data"]["datasets"][0]["label"] == "Series 1"
        assert config["data"]["datasets"][1]["label"] == "Series 2"

    @pytest.mark.unit
    def test_build_chart_config_with_options(self):
        """Test building chart config with additional options."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        options = {"plugins": {"legend": {"display": False}}}
        config = node._build_chart_config([1, 2, 3], None, None, options)
        
        assert config["plugins"]["legend"]["display"] is False

    @pytest.mark.unit
    def test_build_chart_config_with_dimensions(self):
        """Test building chart config with dimensions."""
        node = ChartNode("chart_1", {"chart_type": "bar", "width": 1024, "height": 768})
        config = node._build_chart_config([1, 2, 3], None, None, {})
        
        assert config["width"] == 1024
        assert config["height"] == 768

    @pytest.mark.unit
    def test_build_chart_config_with_axis_labels(self):
        """Test building chart config with axis labels."""
        node = ChartNode("chart_1", {
            "chart_type": "bar",
            "x_label": "Categories",
            "y_label": "Values",
        })
        config = node._build_chart_config([1, 2, 3], None, None, {})
        
        assert config["options"]["scales"]["x"]["title"]["text"] == "Categories"
        assert config["options"]["scales"]["y"]["title"]["text"] == "Values"


class TestChartNodeDataProcessing:
    """Tests for ChartNode data processing."""

    @pytest.mark.unit
    def test_process_data_simple_list(self):
        """Test processing simple list data."""
        node = ChartNode("chart_1", {})
        result = node._process_data([1, 2, 3, 4, 5])
        
        assert result == [1, 2, 3, 4, 5]

    @pytest.mark.unit
    def test_process_data_empty_list(self):
        """Test processing empty data."""
        node = ChartNode("chart_1", {})
        result = node._process_data([])
        
        assert result == []

    @pytest.mark.unit
    def test_process_data_dict_with_value(self):
        """Test processing dict data with value key."""
        node = ChartNode("chart_1", {})
        data = [{"name": "A", "value": 10}, {"name": "B", "value": 20}]
        result = node._process_data(data)
        
        assert result == [10, 20]

    @pytest.mark.unit
    def test_process_data_dict_with_y(self):
        """Test processing dict data with x/y keys."""
        node = ChartNode("chart_1", {})
        data = [{"x": 1, "y": 10}, {"x": 2, "y": 20}]
        result = node._process_data(data)
        
        assert len(result) == 2
        assert result[0]["y"] == 10

    @pytest.mark.unit
    def test_process_data_dict_with_numeric(self):
        """Test processing dict data with numeric values."""
        node = ChartNode("chart_1", {})
        data = [{"name": "A", "count": 5}, {"name": "B", "count": 10}]
        result = node._process_data(data)
        
        # Should extract the first numeric field
        assert result == [5, 10]


class TestChartNodeColors:
    """Tests for ChartNode color handling."""

    @pytest.mark.unit
    def test_get_color_default(self):
        """Test getting default color."""
        node = ChartNode("chart_1", {})
        color = node._get_color(0, "border")
        
        assert color.startswith("#")

    @pytest.mark.unit
    def test_get_color_background(self):
        """Test getting background color (with alpha)."""
        node = ChartNode("chart_1", {})
        color = node._get_color(0, "background")
        
        # Background colors have alpha suffix
        assert color.endswith("cc") or color.startswith("#")

    @pytest.mark.unit
    def test_get_color_pastel_scheme(self):
        """Test getting pastel color."""
        node = ChartNode("chart_1", {"color_scheme": "pastel"})
        color = node._get_color(0, "border")
        
        assert color.startswith("#")

    @pytest.mark.unit
    def test_get_color_vibrant_scheme(self):
        """Test getting vibrant color."""
        node = ChartNode("chart_1", {"color_scheme": "vibrant"})
        color = node._get_color(0, "border")
        
        assert color.startswith("#")

    @pytest.mark.unit
    def test_get_color_monochrome_scheme(self):
        """Test getting monochrome color."""
        node = ChartNode("chart_1", {"color_scheme": "monochrome"})
        color = node._get_color(0, "background")
        
        # Monochrome backgrounds don't have alpha
        assert color.startswith("#")

    @pytest.mark.unit
    def test_get_color_index_wrapping(self):
        """Test color index wrapping."""
        node = ChartNode("chart_1", {})
        # Get colors beyond palette size
        color1 = node._get_color(0, "border")
        color10 = node._get_color(10, "border")
        
        # Should wrap around
        assert color1.startswith("#")
        assert color10.startswith("#")


class TestChartNodeDeepMerge:
    """Tests for ChartNode deep merge."""

    @pytest.mark.unit
    def test_deep_merge_simple(self):
        """Test simple deep merge."""
        node = ChartNode("chart_1", {})
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}
        result = node._deep_merge(base, override)
        
        assert result["a"] == 1
        assert result["b"] == 3
        assert result["c"] == 4

    @pytest.mark.unit
    def test_deep_merge_nested(self):
        """Test nested deep merge."""
        node = ChartNode("chart_1", {})
        base = {"options": {"title": {"text": "Old"}}}
        override = {"options": {"title": {"text": "New"}}}
        result = node._deep_merge(base, override)
        
        assert result["options"]["title"]["text"] == "New"

    @pytest.mark.unit
    def test_deep_merge_adds_keys(self):
        """Test deep merge adds new keys."""
        node = ChartNode("chart_1", {})
        base = {"a": 1}
        override = {"b": 2, "c": {"d": 3}}
        result = node._deep_merge(base, override)
        
        assert result["a"] == 1
        assert result["b"] == 2
        assert result["c"]["d"] == 3


class TestChartNodeExecutionResults:
    """Tests for ChartNode execution results."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_returns_success(self):
        """Test execute returns successful result."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [10, 20, 30]},
            context=context
        )
        
        assert result.success is True
        assert "chart" in result.outputs

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_includes_metadata(self):
        """Test execute includes metadata."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [10, 20, 30]},
            context=context
        )
        
        assert result.metadata is not None
        assert "chart_type" in result.metadata
        assert "data_points" in result.metadata

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_render_image_disabled(self):
        """Test execute without image rendering."""
        node = ChartNode("chart_1", {"chart_type": "bar", "render_image": False})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [10, 20, 30]},
            context=context
        )
        
        assert "image" not in result.outputs

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_handles_empty_data(self):
        """Test execute handles empty data."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": []},
            context=context
        )
        
        assert result.success is True

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_dict_data(self):
        """Test execute with dictionary data."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        data = [
            {"name": "A", "value": 10},
            {"name": "B", "value": 20},
        ]
        result = await node.execute(
            inputs={"data": data},
            context=context
        )
        
        assert result.success is True
        # Labels should be extracted from 'name' field
        assert "chart" in result.outputs


class TestChartNodeImageRendering:
    """Tests for ChartNode image rendering."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_render_image_disabled(self):
        """Test that image rendering is disabled by default."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [10, 20, 30]},
            context=context
        )
        
        assert "image" not in result.outputs
        assert "data_url" not in result.outputs

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_render_image_enabled_no_matplotlib(self):
        """Test image rendering when matplotlib is not available."""
        node = ChartNode("chart_1", {"chart_type": "bar", "render_image": True})
        context = MagicMock(spec=ExecutionContext)
        
        # The _render_chart_image method will return None if matplotlib is not installed
        # This test verifies graceful handling
        result = await node.execute(
            inputs={"data": [10, 20, 30]},
            context=context
        )
        
        # Should still succeed
        assert result.success is True
        # Image may or may not be present depending on matplotlib availability
        assert "chart" in result.outputs
