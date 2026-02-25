"""
Tests for SwitchMode tool implementation.
"""

import pytest
from opencode.tool.switch_mode import SwitchModeTool


@pytest.mark.unit
class TestSwitchModeTool:
    """Tests for SwitchModeTool class."""
    
    def test_tool_name(self):
        """Test tool name."""
        tool = SwitchModeTool()
        assert tool.name == "switch_mode"
    
    def test_tool_description(self):
        """Test tool has description."""
        tool = SwitchModeTool()
        assert tool.description is not None
        assert len(tool.description) > 0
    
    def test_tool_parameters(self):
        """Test tool parameters schema."""
        tool = SwitchModeTool()
        params = tool.parameters
        
        assert "properties" in params
        assert "mode" in params["properties"]
    
    @pytest.mark.asyncio
    async def test_switch_to_code_mode(self):
        """Test switching to code mode."""
        tool = SwitchModeTool()
        
        result = await tool.execute(mode="code", reason="Need to write code")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_switch_to_architect_mode(self):
        """Test switching to architect mode."""
        tool = SwitchModeTool()
        
        result = await tool.execute(mode="architect", reason="Need to plan architecture")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_switch_to_ask_mode(self):
        """Test switching to ask mode."""
        tool = SwitchModeTool()
        
        result = await tool.execute(mode="ask", reason="Need to ask questions")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_switch_to_debug_mode(self):
        """Test switching to debug mode."""
        tool = SwitchModeTool()
        
        result = await tool.execute(mode="debug", reason="Need to debug issue")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_switch_without_reason(self):
        """Test switching without reason."""
        tool = SwitchModeTool()
        
        result = await tool.execute(mode="code")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_switch_invalid_mode(self):
        """Test switching to invalid mode."""
        tool = SwitchModeTool()
        
        result = await tool.execute(mode="invalid_mode", reason="Test")
        
        # Should handle gracefully
        assert result is not None
