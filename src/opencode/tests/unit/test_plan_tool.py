"""
Tests for Plan tool implementation.
"""

import pytest
import asyncio
from opencode.tool.plan import PlanTool, PlanStep


@pytest.mark.unit
class TestPlanStep:
    """Tests for PlanStep dataclass."""
    
    def test_plan_step_creation(self):
        """Test creating a plan step."""
        step = PlanStep(
            id="1",
            description="Test step",
            status="pending",
            dependencies=[],
            notes=None
        )
        
        assert step.id == "1"
        assert step.description == "Test step"
        assert step.status == "pending"
        assert step.dependencies == []
        assert step.notes is None
    
    def test_plan_step_to_dict(self):
        """Test converting plan step to dict."""
        step = PlanStep(
            id="1",
            description="Test step",
            status="in_progress",
            dependencies=["0"],
            notes="Test note"
        )
        
        result = step.to_dict()
        
        assert result["id"] == "1"
        assert result["description"] == "Test step"
        assert result["status"] == "in_progress"
        assert result["dependencies"] == ["0"]
        assert result["notes"] == "Test note"
    
    def test_plan_step_default_values(self):
        """Test plan step default values."""
        step = PlanStep(id="1", description="Test")
        
        assert step.status == "pending"
        assert step.dependencies == []
        assert step.notes is None


@pytest.mark.unit
class TestPlanTool:
    """Tests for PlanTool class."""
    
    def test_plan_tool_name(self):
        """Test plan tool name."""
        tool = PlanTool()
        assert tool.name == "plan"
    
    def test_plan_tool_description(self):
        """Test plan tool has description."""
        tool = PlanTool()
        assert tool.description is not None
        assert len(tool.description) > 0
    
    def test_plan_tool_parameters(self):
        """Test plan tool parameters schema."""
        tool = PlanTool()
        params = tool.parameters
        
        assert "properties" in params
        assert "action" in params["properties"]
        assert "steps" in params["properties"]
    
    def test_plan_tool_permission_level(self):
        """Test plan tool permission level."""
        tool = PlanTool()
        assert tool.permission_level.name == "WRITE"  # Plan tool uses WRITE permission
    
    @pytest.mark.asyncio
    async def test_plan_create(self):
        """Test creating a plan."""
        tool = PlanTool()
        
        result = await tool.execute(
            action="create",
            steps=[
                {"description": "Step 1"},
                {"description": "Step 2"},
            ]
        )
        
        assert result.success
        assert "plan" in result.output.lower() or "created" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_plan_view_empty(self):
        """Test viewing empty plan."""
        tool = PlanTool()
        
        result = await tool.execute(action="view")
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_plan_view_after_create(self):
        """Test viewing plan after creation."""
        tool = PlanTool()
        
        # Create a plan
        await tool.execute(
            action="create",
            steps=[
                {"description": "Step 1"},
                {"description": "Step 2"},
            ]
        )
        
        # View the plan
        result = await tool.execute(action="view")
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_plan_update_step(self):
        """Test updating a step status."""
        tool = PlanTool()
        
        # Create a plan
        await tool.execute(
            action="create",
            steps=[
                {"description": "Step 1"},
                {"description": "Step 2"},
            ]
        )
        
        # Update step status
        result = await tool.execute(
            action="update",
            step_id="1",
            status="completed"
        )
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_plan_delete(self):
        """Test deleting a plan."""
        tool = PlanTool()
        
        # Create a plan
        await tool.execute(
            action="create",
            steps=[{"description": "Step 1"}]
        )
        
        # Delete the plan
        result = await tool.execute(action="delete")
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_plan_with_dependencies(self):
        """Test creating plan with dependencies."""
        tool = PlanTool()
        
        result = await tool.execute(
            action="create",
            steps=[
                {"id": "0", "description": "First step"},
                {"id": "1", "description": "Second step", "dependencies": ["0"]},
            ]
        )
        
        assert result.success
    
    @pytest.mark.asyncio
    async def test_plan_step_statuses(self):
        """Test different step statuses."""
        tool = PlanTool()
        
        # Create a plan
        await tool.execute(
            action="create",
            steps=[
                {"description": "Step 1"},
                {"description": "Step 2"},
                {"description": "Step 3"},
            ]
        )
        
        # Update to different statuses
        await tool.execute(action="update", step_id="1", status="in_progress")
        await tool.execute(action="update", step_id="2", status="completed")
        await tool.execute(action="update", step_id="3", status="blocked", notes="Waiting for dependency")
        
        # View to verify
        result = await tool.execute(action="view")
        assert result.success


@pytest.mark.unit
class TestPlanToolEdgeCases:
    """Tests for edge cases in PlanTool."""
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_step(self):
        """Test updating a step that doesn't exist."""
        tool = PlanTool()
        
        result = await tool.execute(
            action="update",
            step_id="nonexistent",
            status="completed"
        )
        
        # Should handle gracefully
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_create_empty_steps(self):
        """Test creating plan with empty steps."""
        tool = PlanTool()
        
        result = await tool.execute(action="create", steps=[])
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test invalid action."""
        tool = PlanTool()
        
        result = await tool.execute(action="invalid_action")
        
        # Should handle gracefully
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_multiple_plans(self):
        """Test managing multiple plans."""
        tool = PlanTool()
        
        # Create first plan
        await tool.execute(
            action="create",
            plan_id="plan1",
            steps=[{"description": "Plan 1 Step"}]
        )
        
        # Create second plan
        await tool.execute(
            action="create",
            plan_id="plan2",
            steps=[{"description": "Plan 2 Step"}]
        )
        
        # View specific plan
        result = await tool.execute(action="view", plan_id="plan1")
        assert result.success
