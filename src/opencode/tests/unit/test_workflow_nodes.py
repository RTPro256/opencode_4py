"""
Tests for Workflow nodes.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.unit
class TestWorkflowNodes:
    """Tests for workflow nodes."""
    
    def test_chart_node_exists(self):
        """Test chart node exists."""
        from opencode.workflow.nodes.chart import ChartNode
        assert ChartNode is not None
    
    def test_data_source_node_exists(self):
        """Test data source node exists."""
        from opencode.workflow.nodes.data_source import DataSourceNode
        assert DataSourceNode is not None
    
    def test_data_validation_node_exists(self):
        """Test data validation node exists."""
        from opencode.workflow.nodes.data_validation import DataValidationNode
        assert DataValidationNode is not None
    
    def test_http_node_exists(self):
        """Test HTTP node exists."""
        from opencode.workflow.nodes.http import HttpNode
        assert HttpNode is not None
    
    def test_json_reformatter_node_exists(self):
        """Test JSON reformatter node exists."""
        from opencode.workflow.nodes.json_reformatter import JsonReformatterNode
        assert JsonReformatterNode is not None
    
    def test_llm_process_node_exists(self):
        """Test LLM process node exists."""
        from opencode.workflow.nodes.llm_process import LlmProcessNode
        assert LlmProcessNode is not None
    
    def test_timer_node_exists(self):
        """Test timer node exists."""
        from opencode.workflow.nodes.timer import TimerNode
        assert TimerNode is not None
    
    def test_tool_node_exists(self):
        """Test tool node exists."""
        from opencode.workflow.nodes.tool import ToolNode
        assert ToolNode is not None


@pytest.mark.unit
class TestWorkflowEngine:
    """Tests for workflow engine."""
    
    def test_workflow_engine_exists(self):
        """Test workflow engine exists."""
        from opencode.workflow.engine import WorkflowEngine
        assert WorkflowEngine is not None
    
    def test_workflow_graph_exists(self):
        """Test workflow graph exists."""
        from opencode.workflow.graph import WorkflowGraph
        assert WorkflowGraph is not None
    
    def test_workflow_registry_exists(self):
        """Test workflow registry exists."""
        from opencode.workflow.registry import NodeRegistry
        assert NodeRegistry is not None
    
    def test_workflow_state_exists(self):
        """Test workflow state exists."""
        from opencode.workflow.state import WorkflowState
        assert WorkflowState is not None


@pytest.mark.unit
class TestWorkflowModels:
    """Tests for workflow models."""
    
    def test_workflow_status_enum(self):
        """Test WorkflowStatus enum exists."""
        from opencode.workflow.models import WorkflowStatus
        assert WorkflowStatus is not None
    
    def test_execution_status_enum(self):
        """Test ExecutionStatus enum exists."""
        from opencode.workflow.models import ExecutionStatus
        assert ExecutionStatus is not None
    
    def test_workflow_model_exists(self):
        """Test Workflow model exists."""
        from opencode.workflow.models import Workflow
        assert Workflow is not None
    
    def test_workflow_execution_exists(self):
        """Test WorkflowExecution exists."""
        from opencode.workflow.models import WorkflowExecution
        assert WorkflowExecution is not None
    
    def test_node_execution_exists(self):
        """Test NodeExecution exists."""
        from opencode.workflow.models import NodeExecution
        assert NodeExecution is not None
    
    def test_workflow_template_exists(self):
        """Test WorkflowTemplate exists."""
        from opencode.workflow.models import WorkflowTemplate
        assert WorkflowTemplate is not None


@pytest.mark.unit
class TestWorkflowTools:
    """Tests for workflow tools."""
    
    def test_brave_search_tool_exists(self):
        """Test brave search tool exists."""
        from opencode.workflow.tools.brave_search import BraveSearchTool
        assert BraveSearchTool is not None
    
    def test_csv_array_tools_exist(self):
        """Test CSV array tools exist."""
        from opencode.workflow.tools import csv_array
        assert csv_array is not None
    
    def test_duckduckgo_search_tool_exists(self):
        """Test DuckDuckGo search tool exists."""
        from opencode.workflow.tools.duckduckgo_search import DuckDuckGoSearchTool
        assert DuckDuckGoSearchTool is not None
    
    def test_weather_tool_exists(self):
        """Test weather tool exists."""
        from opencode.workflow.tools.weather import WeatherTool
        assert WeatherTool is not None
    
    def test_workflow_tools_registry_exists(self):
        """Test workflow tools registry exists."""
        from opencode.workflow.tools.registry import ToolRegistry
        assert ToolRegistry is not None
