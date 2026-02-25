"""
Agent Registry

Registry for managing agents in the orchestration system.
"""

import logging
from typing import Any, Dict, List, Optional, Type

from opencode.core.orchestration.agent import Agent, AgentDescription, AgentCapability

logger = logging.getLogger(__name__)


class AgentRegistry:
    """
    Registry for managing agents.
    
    Provides a central place to register, discover, and manage agents.
    Supports capability-based lookup and priority-based selection.
    
    Example:
        registry = AgentRegistry()
        
        # Register an agent
        registry.register(my_agent)
        
        # Find agents by capability
        code_agents = registry.find_by_capability(AgentCapability.CODE_GENERATION)
        
        # Get best agent for a task
        best = registry.get_best_agent(
            capabilities=[AgentCapability.CODE_GENERATION],
            available_only=True,
        )
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._agents: Dict[str, Agent] = {}
        self._capability_index: Dict[AgentCapability, List[str]] = {
            cap: [] for cap in AgentCapability
        }
    
    def register(self, agent: Agent) -> None:
        """
        Register an agent.
        
        Args:
            agent: Agent to register
            
        Raises:
            ValueError: If agent ID already exists
        """
        agent_id = agent.agent_id
        
        if agent_id in self._agents:
            raise ValueError(f"Agent already registered: {agent_id}")
        
        self._agents[agent_id] = agent
        
        # Update capability index
        for capability in agent.description.capabilities:
            if capability in self._capability_index:
                self._capability_index[capability].append(agent_id)
        
        logger.info(f"Registered agent: {agent_id}")
    
    def unregister(self, agent_id: str) -> bool:
        """
        Unregister an agent.
        
        Args:
            agent_id: ID of agent to unregister
            
        Returns:
            True if agent was unregistered
        """
        if agent_id not in self._agents:
            return False
        
        agent = self._agents[agent_id]
        
        # Remove from capability index
        for capability in agent.description.capabilities:
            if capability in self._capability_index:
                try:
                    self._capability_index[capability].remove(agent_id)
                except ValueError:
                    pass
        
        del self._agents[agent_id]
        logger.info(f"Unregistered agent: {agent_id}")
        return True
    
    def get(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent or None if not found
        """
        return self._agents.get(agent_id)
    
    def get_all(self) -> List[Agent]:
        """Get all registered agents."""
        return list(self._agents.values())
    
    def get_all_descriptions(self) -> List[AgentDescription]:
        """Get all agent descriptions."""
        return [agent.description for agent in self._agents.values()]
    
    def find_by_capability(
        self,
        capability: AgentCapability,
        available_only: bool = False,
    ) -> List[Agent]:
        """
        Find agents by capability.
        
        Args:
            capability: Capability to search for
            available_only: Only return available agents
            
        Returns:
            List of matching agents
        """
        agent_ids = self._capability_index.get(capability, [])
        agents = [self._agents[aid] for aid in agent_ids if aid in self._agents]
        
        if available_only:
            agents = [a for a in agents if a.is_available]
        
        return agents
    
    def find_by_capabilities(
        self,
        capabilities: List[AgentCapability],
        match_all: bool = False,
        available_only: bool = False,
    ) -> List[Agent]:
        """
        Find agents by multiple capabilities.
        
        Args:
            capabilities: Capabilities to search for
            match_all: Require all capabilities (vs any)
            available_only: Only return available agents
            
        Returns:
            List of matching agents
        """
        if not capabilities:
            return self.get_all() if not available_only else [
                a for a in self._agents.values() if a.is_available
            ]
        
        # Get agents for each capability
        agent_sets = []
        for cap in capabilities:
            agent_sets.append(set(self._capability_index.get(cap, [])))
        
        if match_all:
            # Intersection - agents with all capabilities
            matching_ids = set.intersection(*agent_sets) if agent_sets else set()
        else:
            # Union - agents with any capability
            matching_ids = set.union(*agent_sets) if agent_sets else set()
        
        agents = [self._agents[aid] for aid in matching_ids if aid in self._agents]
        
        if available_only:
            agents = [a for a in agents if a.is_available]
        
        return agents
    
    def get_best_agent(
        self,
        capabilities: Optional[List[AgentCapability]] = None,
        available_only: bool = True,
        prefer_higher_priority: bool = True,
    ) -> Optional[Agent]:
        """
        Get the best agent for given criteria.
        
        Args:
            capabilities: Required capabilities
            available_only: Only return available agents
            prefer_higher_priority: Prefer higher priority agents
            
        Returns:
            Best matching agent or None
        """
        if capabilities:
            agents = self.find_by_capabilities(
                capabilities,
                match_all=True,
                available_only=available_only,
            )
        else:
            agents = self.get_all()
            if available_only:
                agents = [a for a in agents if a.is_available]
        
        if not agents:
            return None
        
        # Sort by priority
        agents.sort(
            key=lambda a: a.description.priority,
            reverse=prefer_higher_priority,
        )
        
        return agents[0]
    
    def get_available_agents(self) -> List[Agent]:
        """Get all available agents."""
        return [a for a in self._agents.values() if a.is_available]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total = len(self._agents)
        available = len(self.get_available_agents())
        
        capability_counts = {
            cap.value: len(self._capability_index[cap])
            for cap in AgentCapability
        }
        
        return {
            "total_agents": total,
            "available_agents": available,
            "capability_counts": capability_counts,
        }
    
    def clear(self) -> None:
        """Clear all registered agents."""
        self._agents.clear()
        for cap in AgentCapability:
            self._capability_index[cap] = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agents": {aid: agent.to_dict() for aid, agent in self._agents.items()},
            "stats": self.get_stats(),
        }
