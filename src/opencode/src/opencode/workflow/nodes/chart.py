"""
Chart Node

Data visualization node for creating charts and graphs.
"""

import logging
from typing import Any, Dict, List, Optional, ClassVar

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


@NodeRegistry.register("chart")
class ChartNode(BaseNode):
    """
    Chart Node - Data visualization for workflows.
    
    This node creates various types of charts and visualizations
    from input data. Supports bar, line, pie, scatter, and other
    chart types.
    
    Configuration:
        chart_type: Type of chart (bar, line, pie, scatter, area, histogram)
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label
        width: Chart width in pixels
        height: Chart height in pixels
        color_scheme: Color scheme for chart
        show_legend: Whether to show legend
        show_grid: Whether to show grid lines
    
    Example:
        node = ChartNode("chart_1", {
            "chart_type": "bar",
            "title": "Sales by Month",
            "x_label": "Month",
            "y_label": "Sales ($)"
        })
    """
    
    _schema = NodeSchema(
        node_type="chart",
        display_name="Chart",
        description="Create charts and visualizations from data",
        category="visualization",
        icon="chart-bar",
        inputs=[
            NodePort(
                name="data",
                data_type=PortDataType.ARRAY,
                direction=PortDirection.INPUT,
                required=True,
                description="Input data for the chart (array of objects or values)",
            ),
            NodePort(
                name="labels",
                data_type=PortDataType.ARRAY,
                direction=PortDirection.INPUT,
                required=False,
                description="Labels for data points",
            ),
            NodePort(
                name="series",
                data_type=PortDataType.ARRAY,
                direction=PortDirection.INPUT,
                required=False,
                description="Multiple data series for charts",
            ),
            NodePort(
                name="options",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.INPUT,
                required=False,
                description="Additional chart options",
            ),
        ],
        outputs=[
            NodePort(
                name="chart",
                data_type=PortDataType.OBJECT,
                direction=PortDirection.OUTPUT,
                required=True,
                description="Chart configuration object (can be rendered by frontend)",
            ),
            NodePort(
                name="image",
                data_type=PortDataType.STRING,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Base64-encoded image (if render enabled)",
            ),
            NodePort(
                name="data_url",
                data_type=PortDataType.STRING,
                direction=PortDirection.OUTPUT,
                required=False,
                description="Data URL for the chart image",
            ),
        ],
        config_schema={
            "type": "object",
            "properties": {
                "chart_type": {
                    "type": "string",
                    "enum": ["bar", "line", "pie", "scatter", "area", "histogram", "doughnut", "radar", "polar"],
                    "default": "bar",
                },
                "title": {
                    "type": "string",
                    "default": "",
                },
                "x_label": {
                    "type": "string",
                    "default": "",
                },
                "y_label": {
                    "type": "string",
                    "default": "",
                },
                "width": {
                    "type": "integer",
                    "default": 800,
                },
                "height": {
                    "type": "integer",
                    "default": 600,
                },
                "color_scheme": {
                    "type": "string",
                    "default": "default",
                },
                "show_legend": {
                    "type": "boolean",
                    "default": True,
                },
                "show_grid": {
                    "type": "boolean",
                    "default": True,
                },
                "render_image": {
                    "type": "boolean",
                    "default": False,
                },
            },
        },
    )
    
    @classmethod
    def get_schema(cls) -> NodeSchema:
        """Return the schema for this node."""
        return cls._schema
    
    async def execute(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext,
    ) -> ExecutionResult:
        """
        Execute the chart node.
        
        Args:
            inputs: Input data for the chart
            context: Execution context
            
        Returns:
            ExecutionResult with chart configuration
        """
        import time
        start_time = time.time()
        
        try:
            data = inputs.get("data", [])
            labels = inputs.get("labels")
            series = inputs.get("series")
            options = inputs.get("options", {})
            
            # Merge options with config
            chart_config = self._build_chart_config(data, labels, series, options)
            
            result_data: Dict[str, Any] = {
                "chart": chart_config,
            }
            
            # Render image if requested
            if self.config.get("render_image", False):
                image_data = await self._render_chart_image(chart_config)
                if image_data:
                    result_data["image"] = image_data
                    result_data["data_url"] = f"data:image/png;base64,{image_data}"
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                success=True,
                outputs=result_data,
                duration_ms=duration_ms,
                metadata={
                    "chart_type": chart_config.get("type"),
                    "data_points": len(data),
                },
            )
            
        except Exception as e:
            logger.exception(f"Chart node execution failed: {e}")
            return ExecutionResult(
                success=False,
                error=str(e),
            )
    
    def _build_chart_config(
        self,
        data: List[Any],
        labels: Optional[List[str]],
        series: Optional[List[Dict[str, Any]]],
        options: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build chart configuration object.
        
        Args:
            data: Input data
            labels: Optional labels
            series: Optional multiple series
            options: Additional options
            
        Returns:
            Chart configuration dictionary
        """
        chart_type = self.config.get("chart_type", "bar")
        
        # Base configuration
        config: Dict[str, Any] = {
            "type": chart_type,
            "data": {},
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {
                        "display": bool(self.config.get("title")),
                        "text": self.config.get("title", ""),
                    },
                    "legend": {
                        "display": self.config.get("show_legend", True),
                    },
                },
            },
        }
        
        # Add scales for cartesian charts
        if chart_type in ("bar", "line", "scatter", "area", "histogram"):
            config["options"]["scales"] = {
                "x": {
                    "title": {
                        "display": bool(self.config.get("x_label")),
                        "text": self.config.get("x_label", ""),
                    },
                    "grid": {
                        "display": self.config.get("show_grid", True),
                    },
                },
                "y": {
                    "title": {
                        "display": bool(self.config.get("y_label")),
                        "text": self.config.get("y_label", ""),
                    },
                    "grid": {
                        "display": self.config.get("show_grid", True),
                    },
                },
            }
        
        # Process data
        if series:
            # Multiple series provided
            config["data"]["datasets"] = []
            for i, s in enumerate(series):
                dataset = {
                    "label": s.get("label", f"Series {i + 1}"),
                    "data": s.get("data", []),
                    "backgroundColor": self._get_color(i, "background"),
                    "borderColor": self._get_color(i, "border"),
                }
                config["data"]["datasets"].append(dataset)
        else:
            # Single data series
            config["data"]["datasets"] = [
                {
                    "label": self.config.get("title", "Data"),
                    "data": self._process_data(data),
                    "backgroundColor": self._get_color(0, "background"),
                    "borderColor": self._get_color(0, "border"),
                }
            ]
        
        # Add labels
        if labels:
            config["data"]["labels"] = labels
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # Try to extract labels from data
            config["data"]["labels"] = [
                item.get("label", item.get("name", str(i)))
                for i, item in enumerate(data)
            ]
        else:
            config["data"]["labels"] = [str(i) for i in range(len(data))]
        
        # Merge additional options
        if options:
            config = self._deep_merge(config, options)
        
        # Add size configuration
        config["width"] = self.config.get("width", 800)
        config["height"] = self.config.get("height", 600)
        
        return config
    
    def _process_data(self, data: List[Any]) -> List[Any]:
        """Process input data for chart format."""
        if not data:
            return []
        
        if isinstance(data[0], dict):
            # Extract values from dictionaries
            if "value" in data[0]:
                return [item.get("value", 0) for item in data]
            elif "y" in data[0]:
                return [{"x": item.get("x", i), "y": item.get("y", 0)} for i, item in enumerate(data)]
            else:
                # Use first numeric field
                for key, value in data[0].items():
                    if isinstance(value, (int, float)):
                        return [item.get(key, 0) for item in data]
        
        return data
    
    def _get_color(self, index: int, color_type: str) -> str:
        """Get color for dataset by index."""
        color_scheme = self.config.get("color_scheme", "default")
        
        # Default color palettes
        palettes = {
            "default": [
                "#3b82f6", "#ef4444", "#22c55e", "#f59e0b", "#8b5cf6",
                "#ec4899", "#06b6d4", "#84cc16", "#f97316", "#6366f1",
            ],
            "pastel": [
                "#93c5fd", "#fca5a5", "#86efac", "#fcd34d", "#c4b5fd",
                "#f9a8d4", "#67e8f9", "#bef264", "#fdba74", "#a5b4fc",
            ],
            "vibrant": [
                "#2563eb", "#dc2626", "#16a34a", "#d97706", "#7c3aed",
                "#db2777", "#0891b2", "#65a30d", "#ea580c", "#4f46e5",
            ],
            "monochrome": [
                "#1f2937", "#374151", "#4b5563", "#6b7280", "#9ca3af",
                "#d1d5db", "#e5e7eb", "#f3f4f6", "#f9fafb", "#ffffff",
            ],
        }
        
        colors = palettes.get(color_scheme, palettes["default"])
        color = colors[index % len(colors)]
        
        if color_type == "background":
            # Make background slightly transparent
            if color_scheme == "monochrome":
                return color
            return color + "cc"  # Add alpha
        
        return color
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = dict(base)
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    async def _render_chart_image(self, config: Dict[str, Any]) -> Optional[str]:
        """
        Render chart to image (requires optional dependencies).
        
        This method attempts to render the chart using matplotlib if available.
        Returns None if rendering is not possible.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend
            import matplotlib.pyplot as plt
            import base64
            import io
            
            chart_type = config.get("type", "bar")
            data = config.get("data", {})
            datasets = data.get("datasets", [])
            labels = data.get("labels", [])
            
            fig, ax = plt.subplots(figsize=(
                config.get("width", 800) / 100,
                config.get("height", 600) / 100
            ))
            
            if chart_type == "bar":
                for dataset in datasets:
                    ax.bar(labels, dataset.get("data", []), label=dataset.get("label"))
            elif chart_type == "line":
                for dataset in datasets:
                    ax.plot(labels, dataset.get("data", []), label=dataset.get("label"))
            elif chart_type == "pie":
                if datasets:
                    ax.pie(datasets[0].get("data", []), labels=labels, autopct='%1.1f%%')
            elif chart_type == "scatter":
                for dataset in datasets:
                    scatter_data = dataset.get("data", [])
                    x = [d.get("x", i) if isinstance(d, dict) else i for i, d in enumerate(scatter_data)]
                    y = [d.get("y", d) if isinstance(d, dict) else d for d in scatter_data]
                    ax.scatter(x, y, label=dataset.get("label"))
            elif chart_type == "area":
                for dataset in datasets:
                    ax.fill_between(labels, dataset.get("data", []), alpha=0.3, label=dataset.get("label"))
            else:
                # Default to bar
                for dataset in datasets:
                    ax.bar(labels, dataset.get("data", []), label=dataset.get("label"))
            
            # Configure chart
            if self.config.get("title"):
                ax.set_title(self.config.get("title"))
            if self.config.get("x_label"):
                ax.set_xlabel(self.config.get("x_label"))
            if self.config.get("y_label"):
                ax.set_ylabel(self.config.get("y_label"))
            if self.config.get("show_legend", True) and len(datasets) > 1:
                ax.legend()
            if self.config.get("show_grid", True):
                ax.grid(True, alpha=0.3)
            
            # Save to base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            buffer.seek(0)
            
            return base64.b64encode(buffer.read()).decode('utf-8')
            
        except ImportError:
            logger.debug("matplotlib not available for chart rendering")
            return None
        except Exception as e:
            logger.warning(f"Chart rendering failed: {e}")
            return None