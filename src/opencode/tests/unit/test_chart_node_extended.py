"""
Extended tests for Chart workflow node.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from opencode.workflow.nodes.chart import ChartNode
from opencode.workflow.node import (
    NodeSchema,
    NodePort,
    PortDataType,
    PortDirection,
    ExecutionContext,
    ExecutionResult,
)


class TestChartNodeExecuteExtended:
    """Extended tests for ChartNode execution."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_scatter_chart(self):
        """Test execute with scatter chart."""
        node = ChartNode("chart_1", {"chart_type": "scatter"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [{"x": 1, "y": 10}, {"x": 2, "y": 20}]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["chart"]["type"] == "scatter"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_area_chart(self):
        """Test execute with area chart."""
        node = ChartNode("chart_1", {"chart_type": "area"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [10, 20, 30]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["chart"]["type"] == "area"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_histogram_chart(self):
        """Test execute with histogram chart."""
        node = ChartNode("chart_1", {"chart_type": "histogram"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [1, 2, 2, 3, 3, 3, 4, 4, 5]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["chart"]["type"] == "histogram"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_doughnut_chart(self):
        """Test execute with doughnut chart."""
        node = ChartNode("chart_1", {"chart_type": "doughnut"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [30, 40, 30]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["chart"]["type"] == "doughnut"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_radar_chart(self):
        """Test execute with radar chart."""
        node = ChartNode("chart_1", {"chart_type": "radar"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [65, 59, 90, 81, 56]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["chart"]["type"] == "radar"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_polar_chart(self):
        """Test execute with polar chart."""
        node = ChartNode("chart_1", {"chart_type": "polar"})
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [11, 16, 7, 3, 14]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["chart"]["type"] == "polar"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_all_config(self):
        """Test execute with all configuration options."""
        node = ChartNode("chart_1", {
            "chart_type": "bar",
            "title": "Sales Report",
            "x_label": "Month",
            "y_label": "Revenue",
            "width": 1024,
            "height": 768,
            "color_scheme": "pastel",
            "show_legend": True,
            "show_grid": True,
        })
        context = MagicMock(spec=ExecutionContext)
        
        result = await node.execute(
            inputs={"data": [100, 200, 300]},
            context=context
        )
        
        assert result.success is True
        assert result.outputs["chart"]["width"] == 1024
        assert result.outputs["chart"]["height"] == 768

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_with_render_image_enabled(self):
        """Test execute with render_image enabled."""
        node = ChartNode("chart_1", {
            "chart_type": "bar",
            "render_image": True,
        })
        context = MagicMock(spec=ExecutionContext)
        
        # Mock the _render_chart_image method
        with patch.object(node, '_render_chart_image', new_callable=AsyncMock) as mock_render:
            mock_render.return_value = "base64imagedata"
            
            result = await node.execute(
                inputs={"data": [10, 20, 30]},
                context=context
            )
            
            assert result.success is True
            mock_render.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_exception_handling(self):
        """Test execute handles exceptions."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        context = MagicMock(spec=ExecutionContext)
        
        # Pass invalid data that might cause an error
        result = await node.execute(
            inputs={"data": None},
            context=context
        )
        
        # Should handle gracefully
        assert result is not None


class TestChartNodeBuildConfigExtended:
    """Extended tests for ChartNode configuration building."""

    @pytest.mark.unit
    def test_build_config_with_dict_data_name_field(self):
        """Test building config with dict data using name field."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        data = [
            {"name": "Item A", "count": 10},
            {"name": "Item B", "count": 20},
        ]
        config = node._build_chart_config(data, None, None, {})
        
        # Labels should be extracted from 'name' field
        assert config["data"]["labels"] == ["Item A", "Item B"]

    @pytest.mark.unit
    def test_build_config_with_dict_data_label_field(self):
        """Test building config with dict data using label field."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        data = [
            {"label": "First", "value": 10},
            {"label": "Second", "value": 20},
        ]
        config = node._build_chart_config(data, None, None, {})
        
        assert config["data"]["labels"] == ["First", "Second"]

    @pytest.mark.unit
    def test_build_config_with_numeric_labels(self):
        """Test building config generates numeric labels when no labels provided."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        config = node._build_chart_config([10, 20, 30], None, None, {})
        
        assert config["data"]["labels"] == ["0", "1", "2"]

    @pytest.mark.unit
    def test_build_config_merges_options(self):
        """Test building config merges additional options."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        options = {
            "plugins": {
                "tooltip": {
                    "enabled": True,
                },
            },
        }
        config = node._build_chart_config([1, 2, 3], None, None, options)
        
        assert config["plugins"]["tooltip"]["enabled"] is True


class TestChartNodeProcessDataExtended:
    """Extended tests for ChartNode data processing."""

    @pytest.mark.unit
    def test_process_data_with_x_y_fields(self):
        """Test processing data with x/y fields."""
        node = ChartNode("chart_1", {"chart_type": "scatter"})
        
        data = [
            {"x": 1, "y": 10},
            {"x": 2, "y": 20},
            {"x": 3, "y": 30},
        ]
        result = node._process_data(data)
        
        assert len(result) == 3
        assert result[0]["y"] == 10

    @pytest.mark.unit
    def test_process_data_with_count_field(self):
        """Test processing data with count field."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        data = [
            {"name": "A", "count": 5},
            {"name": "B", "count": 10},
        ]
        result = node._process_data(data)
        
        # Should extract the first numeric field (count)
        assert result == [5, 10]

    @pytest.mark.unit
    def test_process_data_simple_values(self):
        """Test processing simple values."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        result = node._process_data([1, 2, 3, 4, 5])
        
        assert result == [1, 2, 3, 4, 5]


class TestChartNodeColorSchemes:
    """Tests for ChartNode color schemes."""

    @pytest.mark.unit
    def test_default_color_scheme(self):
        """Test default color scheme."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        color = node._get_color(0, "border")
        assert color.startswith("#")

    @pytest.mark.unit
    def test_pastel_color_scheme(self):
        """Test pastel color scheme."""
        node = ChartNode("chart_1", {"chart_type": "bar", "color_scheme": "pastel"})
        
        color = node._get_color(0, "border")
        assert color.startswith("#")

    @pytest.mark.unit
    def test_vibrant_color_scheme(self):
        """Test vibrant color scheme."""
        node = ChartNode("chart_1", {"chart_type": "bar", "color_scheme": "vibrant"})
        
        color = node._get_color(0, "border")
        assert color.startswith("#")

    @pytest.mark.unit
    def test_monochrome_color_scheme(self):
        """Test monochrome color scheme."""
        node = ChartNode("chart_1", {"chart_type": "bar", "color_scheme": "monochrome"})
        
        color = node._get_color(0, "border")
        assert color.startswith("#")

    @pytest.mark.unit
    def test_unknown_color_scheme(self):
        """Test unknown color scheme falls back to default."""
        node = ChartNode("chart_1", {"chart_type": "bar", "color_scheme": "unknown"})
        
        color = node._get_color(0, "border")
        assert color.startswith("#")

    @pytest.mark.unit
    def test_color_index_wrapping(self):
        """Test color index wraps around palette."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        # Get colors for indices beyond palette size
        color0 = node._get_color(0, "border")
        color100 = node._get_color(100, "border")
        
        # Both should return valid colors
        assert color0.startswith("#")
        assert color100.startswith("#")


class TestChartNodeDeepMergeExtended:
    """Extended tests for ChartNode deep merge."""

    @pytest.mark.unit
    def test_deep_merge_nested_dicts(self):
        """Test deep merge with nested dictionaries."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        base = {
            "options": {
                "plugins": {
                    "title": {"text": "Old Title"},
                    "legend": {"display": True},
                },
            },
        }
        override = {
            "options": {
                "plugins": {
                    "title": {"text": "New Title"},
                },
            },
        }
        result = node._deep_merge(base, override)
        
        assert result["options"]["plugins"]["title"]["text"] == "New Title"
        assert result["options"]["plugins"]["legend"]["display"] is True

    @pytest.mark.unit
    def test_deep_merge_with_lists(self):
        """Test deep merge with lists."""
        node = ChartNode("chart_1", {"chart_type": "bar"})
        
        base = {"data": {"datasets": [{"label": "A"}]}}
        override = {"data": {"datasets": [{"label": "B"}]}}
        
        result = node._deep_merge(base, override)
        
        # Lists should be replaced, not merged
        assert result["data"]["datasets"][0]["label"] == "B"
