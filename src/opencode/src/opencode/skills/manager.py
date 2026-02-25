"""
Skill Manager

Manages skill execution and state.
"""

import asyncio
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from opencode.skills.models import (
    Skill,
    SkillConfig,
    SkillResult,
    SkillExecutionContext,
    SkillStatus,
    SkillType,
)
from opencode.skills.discovery import SkillDiscovery

logger = logging.getLogger(__name__)


class SkillManager:
    """
    Manager for the skills system.
    
    Handles skill discovery, execution, and state management.
    
    Example:
        manager = SkillManager()
        
        # Discover skills
        skills = manager.discover_skills()
        
        # Execute a skill
        result = await manager.execute_skill("test", "arg1 arg2")
        
        # Parse and execute from message
        result = await manager.parse_and_execute("/test arg1 arg2")
    """
    
    def __init__(
        self,
        skill_dirs: Optional[List[Path]] = None,
        auto_discover: bool = True,
    ):
        """
        Initialize the skill manager.
        
        Args:
            skill_dirs: Directories to search for skills
            auto_discover: Whether to automatically discover skills
        """
        self._discovery = SkillDiscovery(skill_dirs)
        self._skills: Dict[str, Skill] = {}
        self._execution_hooks: List[Callable] = []
        
        if auto_discover:
            self.discover_skills()
    
    def discover_skills(self, reload: bool = False) -> Dict[str, Skill]:
        """
        Discover all available skills.
        
        Args:
            reload: Force reload from directories
            
        Returns:
            Dictionary of discovered skills
        """
        if reload:
            self._skills = self._discovery.reload()
        else:
            self._skills = self._discovery.discover_all()
        
        return self._skills
    
    def add_skill(self, skill: Skill) -> None:
        """
        Add a skill manually.
        
        Args:
            skill: Skill to add
        """
        self._skills[skill.name] = skill
        self._discovery._skills[skill.name] = skill
    
    def remove_skill(self, name: str) -> bool:
        """
        Remove a skill.
        
        Args:
            name: Name of the skill to remove
            
        Returns:
            True if skill was removed
        """
        if name in self._skills:
            del self._skills[name]
            if name in self._discovery._skills:
                del self._discovery._skills[name]
            return True
        return False
    
    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name.
        
        Args:
            name: Name of the skill
            
        Returns:
            Skill or None if not found
        """
        return self._skills.get(name)
    
    def list_skills(self) -> List[str]:
        """List all available skill names."""
        return list(self._skills.keys())
    
    def get_all_skills(self) -> Dict[str, Skill]:
        """Get all available skills."""
        return self._skills
    
    def is_skill_trigger(self, message: str) -> bool:
        """
        Check if a message is a skill trigger.
        
        Args:
            message: Message to check
            
        Returns:
            True if message starts with a skill trigger
        """
        if not message.startswith("/"):
            return False
        
        # Extract potential trigger
        parts = message.split(maxsplit=1)
        trigger = parts[0]
        
        return any(s.trigger == trigger for s in self._skills.values())
    
    def parse_trigger(self, message: str) -> Optional[tuple[str, str]]:
        """
        Parse a message for skill trigger.
        
        Args:
            message: Message to parse
            
        Returns:
            Tuple of (skill_name, arguments) or None
        """
        if not message.startswith("/"):
            return None
        
        parts = message.split(maxsplit=1)
        trigger = parts[0]
        arguments = parts[1] if len(parts) > 1 else ""
        
        for skill in self._skills.values():
            if skill.trigger == trigger:
                return skill.name, arguments
        
        return None
    
    async def execute_skill(
        self,
        name: str,
        arguments: str = "",
        context: Optional[SkillExecutionContext] = None,
    ) -> SkillResult:
        """
        Execute a skill by name.
        
        Args:
            name: Name of the skill to execute
            arguments: Arguments to pass to the skill
            context: Execution context
            
        Returns:
            SkillResult from the execution
        """
        skill = self._skills.get(name)
        if not skill:
            return SkillResult(
                success=False,
                error=f"Skill not found: {name}",
            )
        
        if skill.status == SkillStatus.DISABLED:
            return SkillResult(
                success=False,
                error=f"Skill is disabled: {name}",
            )
        
        # Create context if not provided
        if context is None:
            context = SkillExecutionContext(
                skill_name=name,
                arguments=arguments,
            )
        
        # Parse arguments
        context.parsed_args = self._parse_arguments(skill, arguments)
        
        # Execute based on skill type
        start_time = time.time()
        
        try:
            if skill.config.skill_type == SkillType.PROMPT:
                result = await self._execute_prompt_skill(skill, context)
            elif skill.config.skill_type == SkillType.FUNCTION:
                result = await self._execute_function_skill(skill, context)
            elif skill.config.skill_type == SkillType.WORKFLOW:
                result = await self._execute_workflow_skill(skill, context)
            elif skill.config.skill_type == SkillType.CHAIN:
                result = await self._execute_chain_skill(skill, context)
            else:
                result = SkillResult(
                    success=False,
                    error=f"Unknown skill type: {skill.config.skill_type}",
                )
            
            # Update skill stats
            skill.last_used_at = datetime.utcnow()
            skill.use_count += 1
            
            # Add duration
            result.duration_ms = (time.time() - start_time) * 1000
            
            # Run execution hooks
            for hook in self._execution_hooks:
                try:
                    await hook(skill, context, result)
                except Exception as e:
                    logger.warning(f"Execution hook error: {e}")
            
            return result
            
        except asyncio.TimeoutError:
            return SkillResult(
                success=False,
                error=f"Skill execution timed out after {skill.config.timeout_seconds}s",
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            logger.exception(f"Skill execution error: {e}")
            return SkillResult(
                success=False,
                error=str(e),
                duration_ms=(time.time() - start_time) * 1000,
            )
    
    async def parse_and_execute(
        self,
        message: str,
        context: Optional[SkillExecutionContext] = None,
    ) -> Optional[SkillResult]:
        """
        Parse a message and execute the skill if it's a trigger.
        
        Args:
            message: Message to parse
            context: Execution context
            
        Returns:
            SkillResult if a skill was triggered, None otherwise
        """
        parsed = self.parse_trigger(message)
        if not parsed:
            return None
        
        name, arguments = parsed
        return await self.execute_skill(name, arguments, context)
    
    async def _execute_prompt_skill(
        self,
        skill: Skill,
        context: SkillExecutionContext,
    ) -> SkillResult:
        """
        Execute a prompt-type skill.
        
        Args:
            skill: Skill to execute
            context: Execution context
            
        Returns:
            SkillResult with the rendered prompt
        """
        template = skill.config.template
        
        # Substitute variables
        output = self._render_template(template, context)
        
        return SkillResult(
            success=True,
            output=output,
            data={"template": template, "args": context.parsed_args},
        )
    
    async def _execute_function_skill(
        self,
        skill: Skill,
        context: SkillExecutionContext,
    ) -> SkillResult:
        """
        Execute a function-type skill.
        
        Args:
            skill: Skill to execute
            context: Execution context
            
        Returns:
            SkillResult from the function
        """
        executor = skill._executor
        if not executor:
            return SkillResult(
                success=False,
                error=f"No executor function for skill: {skill.name}",
            )
        
        # Execute with timeout
        result = await asyncio.wait_for(
            executor(context),
            timeout=skill.config.timeout_seconds,
        )
        
        if isinstance(result, SkillResult):
            return result
        
        # Wrap string results
        if isinstance(result, str):
            return SkillResult(success=True, output=result)
        
        return SkillResult(success=True, data=result)
    
    async def _execute_workflow_skill(
        self,
        skill: Skill,
        context: SkillExecutionContext,
    ) -> SkillResult:
        """
        Execute a workflow-type skill.
        
        Args:
            skill: Skill to execute
            context: Execution context
            
        Returns:
            SkillResult from the workflow
        """
        # Import workflow engine
        from opencode.workflow.engine import WorkflowEngine
        from opencode.workflow.graph import WorkflowGraph
        
        workflow_id = skill.config.workflow_id
        if not workflow_id:
            return SkillResult(
                success=False,
                error="No workflow_id configured for skill",
            )
        
        # This would need to load the workflow from storage
        # For now, return a placeholder
        return SkillResult(
            success=False,
            error="Workflow execution not yet implemented",
        )
    
    async def _execute_chain_skill(
        self,
        skill: Skill,
        context: SkillExecutionContext,
    ) -> SkillResult:
        """
        Execute a chain-type skill (multiple skills in sequence).
        
        Args:
            skill: Skill to execute
            context: Execution context
            
        Returns:
            Combined SkillResult
        """
        chain = skill.config.chain
        if not chain:
            return SkillResult(
                success=False,
                error="No chain configured for skill",
            )
        
        results = []
        combined_output = []
        
        for skill_name in chain:
            result = await self.execute_skill(skill_name, context.arguments, context)
            results.append(result)
            
            if result.success:
                combined_output.append(result.output)
            else:
                return SkillResult(
                    success=False,
                    error=f"Chain failed at {skill_name}: {result.error}",
                    data={"results": [r.to_dict() for r in results]},
                )
        
        return SkillResult(
            success=True,
            output="\n\n".join(combined_output),
            data={"results": [r.to_dict() for r in results]},
        )
    
    def _parse_arguments(
        self,
        skill: Skill,
        arguments: str,
    ) -> Dict[str, Any]:
        """
        Parse arguments based on skill parameter definitions.
        
        Args:
            skill: Skill with parameter definitions
            arguments: Raw argument string
            
        Returns:
            Parsed arguments dictionary
        """
        params = skill.config.parameters
        if not params:
            return {"args": arguments}
        
        result = {}
        args_list = arguments.split()
        
        for i, (param_name, param_config) in enumerate(params.items()):
            if isinstance(param_config, dict):
                if param_config.get("type") == "flag":
                    # Boolean flag
                    result[param_name] = f"--{param_name}" in arguments or f"-{param_name[0]}" in arguments
                elif i < len(args_list):
                    # Positional argument
                    result[param_name] = args_list[i]
            elif i < len(args_list):
                result[param_name] = args_list[i]
        
        # Store remaining args
        result["_raw"] = arguments
        result["_args"] = args_list
        
        return result
    
    def _render_template(
        self,
        template: str,
        context: SkillExecutionContext,
    ) -> str:
        """
        Render a template with context variables.
        
        Args:
            template: Template string
            context: Execution context
            
        Returns:
            Rendered string
        """
        output = template
        
        # Replace {{args}} with arguments
        output = output.replace("{{args}}", context.arguments)
        
        # Replace {{arg0}}, {{arg1}}, etc.
        for i, arg in enumerate(context.parsed_args.get("_args", [])):
            output = output.replace(f"{{{{arg{i}}}}}", arg)
        
        # Replace named parameters
        for key, value in context.parsed_args.items():
            if not key.startswith("_"):
                output = output.replace(f"{{{{{key}}}}}", str(value))
        
        # Replace context variables
        for key, value in context.variables.items():
            output = output.replace(f"{{{{{key}}}}}", str(value))
        
        return output
    
    def add_execution_hook(self, hook: Callable) -> None:
        """
        Add a hook to be called after skill execution.
        
        Args:
            hook: Async function(skill, context, result)
        """
        self._execution_hooks.append(hook)
    
    def remove_execution_hook(self, hook: Callable) -> None:
        """Remove an execution hook."""
        if hook in self._execution_hooks:
            self._execution_hooks.remove(hook)
