"""
Coordinator agent for multi-agent orchestration.

Based on overstory (https://github.com/jayminwest/overstory)

The coordinator is the top-level agent that decomposes objectives
and dispatches worker agents.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Dict
import json

from .models import (
    Agent, AgentType, AgentState, RuntimeType,
    Message, MessageType, OrchestrationRun
)
from .messaging import MessageBus
from .worktree import WorktreeManager


class Coordinator:
    """
    Coordinates multi-agent workflows.
    
    The coordinator:
    - Runs at project root (not in a worktree)
    - Receives objectives from humans or higher-level agents
    - Decomposes objectives into tasks
    - Dispatches lead agents to handle tasks
    - Monitors progress via messages
    - Handles escalations
    """
    
    def __init__(
        self,
        agent_id: str = "coordinator",
        message_bus: Optional[MessageBus] = None,
        worktree_manager: Optional[WorktreeManager] = None,
    ):
        """
        Initialize the coordinator.
        
        Args:
            agent_id: Unique identifier for this coordinator
            message_bus: Message bus for communication
            worktree_manager: Worktree manager for agent isolation
        """
        self.agent_id = agent_id
        self.message_bus = message_bus or MessageBus()
        self.worktree_manager = worktree_manager or WorktreeManager()
        
        # Create coordinator agent
        self.agent = Agent(
            id=agent_id,
            name="coordinator",
            agent_type=AgentType.COORDINATOR,
            state=AgentState.READY,
            runtime=RuntimeType.CLAUDE_CODE,
            capabilities=["coordinate", "dispatch", "monitor"],
            depth=0,
        )
        
        # Track active agents
        self.active_agents: Dict[str, Agent] = {}
        
        # Current run
        self.current_run: Optional[OrchestrationRun] = None
    
    def start_run(self, name: str, description: str = "") -> OrchestrationRun:
        """
        Start a new orchestration run.
        
        Args:
            name: Run name
            description: Run description
        
        Returns:
            The new orchestration run
        """
        self.current_run = OrchestrationRun(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            is_active=True,
            started_at=datetime.utcnow(),
        )
        return self.current_run
    
    def end_run(self):
        """End the current orchestration run."""
        if self.current_run:
            self.current_run.is_complete = True
            self.current_run.is_active = False
            self.current_run.completed_at = datetime.utcnow()
    
    def spawn_agent(
        self,
        agent_type: AgentType,
        name: str,
        task_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
        file_scope: Optional[List[str]] = None,
    ) -> Agent:
        """
        Spawn a new agent.
        
        Args:
            agent_type: Type of agent to spawn
            name: Agent name
            task_id: Task ID for the agent
            parent_id: Parent agent ID
            capabilities: Agent capabilities
            file_scope: Files the agent can modify
        
        Returns:
            The spawned agent
        """
        agent_id = f"{agent_type.value}-{uuid.uuid4().hex[:6]}"
        
        # Determine depth
        depth = 0
        if parent_id:
            parent = self.active_agents.get(parent_id)
            if parent:
                depth = parent.depth + 1
        
        # Create worktree for the agent (except coordinator and supervisor)
        worktree_path = None
        branch = None
        if agent_type not in [AgentType.COORDINATOR, AgentType.SUPERVISOR]:
            try:
                worktree = self.worktree_manager.create_worktree(agent_id)
                worktree_path = worktree.path
                branch = worktree.branch
            except Exception:
                # Worktree creation might fail if not in a git repo
                pass
        
        agent = Agent(
            id=agent_id,
            name=name,
            agent_type=agent_type,
            state=AgentState.PENDING,
            runtime=RuntimeType.CLAUDE_CODE,
            task_id=task_id,
            parent_id=parent_id,
            capabilities=capabilities or [],
            file_scope=file_scope or [],
            depth=depth,
            worktree_path=worktree_path,
            branch=branch,
            started_at=datetime.utcnow(),
        )
        
        self.active_agents[agent_id] = agent
        
        if self.current_run:
            self.current_run.agent_ids.append(agent_id)
        
        return agent
    
    def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an agent.
        
        Args:
            agent_id: Agent ID to stop
        
        Returns:
            True if successful
        """
        agent = self.active_agents.get(agent_id)
        if not agent:
            return False
        
        agent.state = AgentState.STOPPED
        agent.finished_at = datetime.utcnow()
        
        # Clean up worktree
        if agent.worktree_path:
            try:
                self.worktree_manager.remove_worktree(agent_id, force=True)
            except Exception:
                pass
        
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.active_agents.get(agent_id)
    
    def list_agents(
        self,
        state: Optional[AgentState] = None,
        agent_type: Optional[AgentType] = None,
    ) -> List[Agent]:
        """
        List active agents with optional filters.
        
        Args:
            state: Filter by state
            agent_type: Filter by type
        
        Returns:
            List of matching agents
        """
        agents = list(self.active_agents.values())
        
        if state:
            agents = [a for a in agents if a.state == state]
        
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        
        return agents
    
    def get_status(self) -> Dict:
        """
        Get coordinator status.
        
        Returns:
            Status dictionary
        """
        return {
            "coordinator_id": self.agent_id,
            "current_run": self.current_run.dict() if self.current_run else None,
            "active_agents": len(self.active_agents),
            "agents_by_state": {
                state.value: len([a for a in self.active_agents.values() if a.state == state])
                for state in AgentState
            },
            "agents_by_type": {
                at.value: len([a for a in self.active_agents.values() if a.agent_type == at])
                for at in AgentType
            },
        }
    
    # Convenience methods for spawning specific agent types
    
    def spawn_lead(self, name: str, task_id: str) -> Agent:
        """Spawn a lead agent."""
        return self.spawn_agent(
            AgentType.LEAD,
            name,
            task_id=task_id,
            parent_id=self.agent_id,
            capabilities=["coordinate", "build", "review"],
        )
    
    def spawn_builder(self, name: str, task_id: str, parent_id: str, file_scope: List[str]) -> Agent:
        """Spawn a builder agent."""
        return self.spawn_agent(
            AgentType.BUILDER,
            name,
            task_id=task_id,
            parent_id=parent_id,
            capabilities=["build", "test"],
            file_scope=file_scope,
        )
    
    def spawn_scout(self, name: str, task_id: str, parent_id: str) -> Agent:
        """Spawn a scout agent."""
        return self.spawn_agent(
            AgentType.SCOUT,
            name,
            task_id=task_id,
            parent_id=parent_id,
            capabilities=["explore", "research"],
        )
    
    def spawn_reviewer(self, name: str, task_id: str, parent_id: str, file_scope: List[str]) -> Agent:
        """Spawn a reviewer agent."""
        return self.spawn_agent(
            AgentType.REVIEWER,
            name,
            task_id=task_id,
            parent_id=parent_id,
            capabilities=["review"],
            file_scope=file_scope,
        )
    
    def spawn_merger(self, name: str, parent_id: str) -> Agent:
        """Spawn a merger agent."""
        return self.spawn_agent(
            AgentType.MERGER,
            name,
            parent_id=parent_id,
            capabilities=["merge", "resolve_conflicts"],
        )
