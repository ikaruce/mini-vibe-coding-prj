"""Planning Module for DeepAgents Architecture.

This module implements the Planning concept from DeepAgents:
- Decompose complex tasks into sequential steps
- Identify required SubAgents for each step
- Optimize execution order
- Track progress through steps

Based on LangChain DeepAgents pattern.
"""

from typing import List, Optional, Literal
from dataclasses import dataclass, field
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class Step:
    """Single step in execution plan.
    
    Attributes:
        id: Step identifier
        action: Action type (analyze, code, test, doc, file_ops)
        description: Human-readable description
        subagent: Which SubAgent handles this step
        required_tools: Tools needed for this step
        depends_on: Step IDs that must complete first
        status: Current status (pending, in_progress, completed, failed)
    """
    id: int
    action: Literal["analyze", "code", "test", "doc_sync", "file_ops", "planning"]
    description: str
    subagent: Literal["analysis", "coding", "documentation", "filesystem", "coordinator"]
    required_tools: List[str] = field(default_factory=list)
    depends_on: List[int] = field(default_factory=list)
    status: Literal["pending", "in_progress", "completed", "failed"] = "pending"
    result: Optional[str] = None


@dataclass
class Plan:
    """Complete execution plan.
    
    Attributes:
        steps: List of execution steps
        total_steps: Total number of steps
        current_step_index: Current step being executed
        completed_steps: Number of completed steps
        estimated_time: Estimated total time (seconds)
    """
    steps: List[Step]
    total_steps: int
    current_step_index: int = 0
    completed_steps: int = 0
    estimated_time: float = 0.0


class Planner:
    """DeepAgents Planning: Decompose tasks into executable steps.
    
    The Planner analyzes user requests and creates a detailed execution plan,
    identifying which SubAgents to use and in what order.
    """
    
    def __init__(self, llm):
        """Initialize planner.
        
        Args:
            llm: LangChain LLM instance for planning
        """
        self.llm = llm
    
    def create_plan(self, user_request: str, context: Optional[str] = None) -> Plan:
        """Create execution plan from user request.
        
        Args:
            user_request: User's request description
            context: Additional context about the project
            
        Returns:
            Structured execution plan
        """
        logger.info("Creating execution plan...")
        
        # Generate plan using LLM
        plan_text = self._generate_plan_text(user_request, context)
        
        # Parse into structured steps
        steps = self._parse_plan(plan_text)
        
        # Estimate time
        estimated_time = self._estimate_time(steps)
        
        logger.info(f"Plan created: {len(steps)} steps, estimated {estimated_time:.1f}s")
        
        return Plan(
            steps=steps,
            total_steps=len(steps),
            estimated_time=estimated_time
        )
    
    def _generate_plan_text(self, user_request: str, context: Optional[str] = None) -> str:
        """Generate plan text using LLM.
        
        Args:
            user_request: User's request
            context: Additional context
            
        Returns:
            Plan as text
        """
        prompt = f"""You are a task planning expert for an AI coding assistant.

User Request: {user_request}

{f"Context: {context}" if context else ""}

Available SubAgents and their capabilities:

1. **Analysis SubAgent**
   - SPEED mode: Tree-sitter + NetworkX (fast, 10k lines <5s)
   - PRECISION mode: LSP (accurate, compiler-level)
   - Tools: SpeedAnalyzer, PrecisionAnalyzer

2. **Coding SubAgent**
   - Code generation with PEP8 and type hints
   - Automatic test generation (pytest)
   - Self-healing loop (max 3 retries)
   - Tools: CodeGenerator, TestGenerator, SelfHealer
   - Execution: Docker sandbox

3. **Documentation SubAgent**
   - Docstring generation (Google Style)
   - README update proposals
   - API documentation sync
   - Tools: DocstringExtractor, ReadmeAnalyzer

4. **FileSystem SubAgent**
   - Directory exploration (list_directory)
   - File reading (read_file)
   - Pattern search (glob_search, grep_search)
   - File modification (edit_file, write_file)
   - Large file summarization (FileSummarizer)

Task:
Create a step-by-step execution plan. Each step should:
- Use ONE SubAgent
- Have a clear, specific action
- Indicate required tools
- Note dependencies on previous steps

Format:
STEP 1: [SubAgent] Action description
STEP 2: [SubAgent] Action description (depends on Step 1)
...

Your detailed plan:
"""
        
        response = self.llm.invoke(prompt)
        return response.content
    
    def _parse_plan(self, plan_text: str) -> List[Step]:
        """Parse plan text into structured steps.
        
        Args:
            plan_text: Plan in text format
            
        Returns:
            List of Step objects
        """
        steps = []
        
        # Pattern: STEP N: [SubAgent] Description
        pattern = r"STEP\s+(\d+):\s*\[(\w+)\]\s*(.+?)(?=STEP\s+\d+:|$)"
        matches = re.findall(pattern, plan_text, re.DOTALL)
        
        for step_id, subagent, description in matches:
            step_id = int(step_id)
            description = description.strip()
            
            # Map subagent name to canonical form
            subagent_map = {
                "analysis": "analysis",
                "coding": "coding",
                "code": "coding",
                "documentation": "documentation",
                "doc": "documentation",
                "filesystem": "filesystem",
                "file": "filesystem"
            }
            
            subagent_key = subagent_map.get(subagent.lower(), "coordinator")
            
            # Determine action type
            action = self._determine_action(description, subagent_key)
            
            # Extract tools if mentioned
            tools = self._extract_tools(description)
            
            # Extract dependencies
            depends_on = self._extract_dependencies(description, step_id)
            
            steps.append(Step(
                id=step_id,
                action=action,
                description=description,
                subagent=subagent_key,
                required_tools=tools,
                depends_on=depends_on
            ))
        
        return steps
    
    def _determine_action(self, description: str, subagent: str) -> str:
        """Determine action type from description.
        
        Args:
            description: Step description
            subagent: SubAgent name
            
        Returns:
            Action type
        """
        desc_lower = description.lower()
        
        if "analyz" in desc_lower or "impact" in desc_lower:
            return "analyze"
        elif "test" in desc_lower:
            return "test"
        elif "code" in desc_lower or "generat" in desc_lower:
            return "code"
        elif "doc" in desc_lower or "docstring" in desc_lower or "readme" in desc_lower:
            return "doc_sync"
        elif subagent == "filesystem":
            return "file_ops"
        else:
            return "planning"
    
    def _extract_tools(self, description: str) -> List[str]:
        """Extract mentioned tool names from description.
        
        Args:
            description: Step description
            
        Returns:
            List of tool names
        """
        tools = []
        
        # Common tool names
        tool_patterns = [
            "list_directory", "read_file", "glob_search", "grep_search",
            "edit_file", "write_file",
            "SpeedAnalyzer", "PrecisionAnalyzer",
            "CodeGenerator", "TestGenerator", "SelfHealer",
            "DocstringGenerator", "ReadmeAnalyzer"
        ]
        
        for tool in tool_patterns:
            if tool.lower() in description.lower():
                tools.append(tool)
        
        return tools
    
    def _extract_dependencies(self, description: str, current_step: int) -> List[int]:
        """Extract step dependencies from description.
        
        Args:
            description: Step description
            current_step: Current step ID
            
        Returns:
            List of step IDs this step depends on
        """
        dependencies = []
        
        # Look for patterns like "depends on Step 1" or "after Step 2"
        dep_pattern = r"(?:depends on|after|requires)\s+Step\s+(\d+)"
        matches = re.findall(dep_pattern, description, re.IGNORECASE)
        
        for match in matches:
            dep_id = int(match)
            if dep_id < current_step:
                dependencies.append(dep_id)
        
        # If no explicit dependencies, depend on previous step (if not first)
        if not dependencies and current_step > 1:
            dependencies.append(current_step - 1)
        
        return dependencies
    
    def _estimate_time(self, steps: List[Step]) -> float:
        """Estimate total execution time.
        
        Args:
            steps: List of execution steps
            
        Returns:
            Estimated time in seconds
        """
        # Rough estimates per action type
        time_estimates = {
            "analyze": 5.0,  # SPEED mode ~5s
            "code": 10.0,    # Code generation
            "test": 15.0,    # Testing + potential healing
            "doc_sync": 8.0,  # Documentation
            "file_ops": 3.0,  # File operations
            "planning": 2.0   # Additional planning
        }
        
        total = sum(time_estimates.get(step.action, 5.0) for step in steps)
        
        return total


def get_next_step(plan: Plan) -> Optional[Step]:
    """Get next step to execute.
    
    Args:
        plan: Current execution plan
        
    Returns:
        Next step to execute, or None if all complete
    """
    for step in plan.steps:
        if step.status == "pending":
            # Check if dependencies are met
            deps_met = all(
                plan.steps[dep_id - 1].status == "completed"
                for dep_id in step.depends_on
            )
            
            if deps_met:
                return step
    
    return None


def mark_step_complete(plan: Plan, step_id: int, result: str) -> None:
    """Mark a step as completed.
    
    Args:
        plan: Execution plan
        step_id: Step ID to mark complete
        result: Step execution result
    """
    for step in plan.steps:
        if step.id == step_id:
            step.status = "completed"
            step.result = result
            plan.completed_steps += 1
            logger.info(f"Step {step_id} completed ({plan.completed_steps}/{plan.total_steps})")
            break