"""True DeepAgent Implementation with Planning-driven Dynamic Execution.

This implements the DeepAgent pattern as described:
1. Planning: LLM creates todo_list first
2. While Loop: Dynamic execution of tasks
3. SubAgent Spawning: Create specialized agents on-demand
4. FileSystem Context: Save intermediate results to files (save tokens)
5. Self-Correction: Dynamically modify plan based on results

Based on the example:
```python
class DeepAgent:
    def run(self, user_goal):
        todo_list = self.llm.plan(user_goal)
        
        while not todo_list.is_empty():
            current_task = todo_list.pop()
            
            if needs_subagent(current_task):
                subagent = create_subagent(role=...)
                result = subagent.work(current_task)
                filesystem.write_file("result.txt", result)
            
            if check_completeness(result) == "insufficient":
                todo_list.add("additional_task")
        
        return filesystem.read_file("final_result")
```
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Task:
    """Single task in todo list."""
    id: int
    description: str
    task_type: str  # "analyze", "code", "test", "doc", "search", "custom"
    requires_subagent: bool = False
    subagent_role: Optional[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result_file: Optional[str] = None  # Where result is saved


@dataclass
class TodoList:
    """Dynamic todo list that can be modified during execution."""
    tasks: List[Task] = field(default_factory=list)
    completed: List[Task] = field(default_factory=list)
    
    def add(self, task: Task):
        """Add new task to list."""
        self.tasks.append(task)
        logger.info(f"➕ Added task: {task.description}")
    
    def pop(self) -> Optional[Task]:
        """Get next task."""
        if self.tasks:
            task = self.tasks.pop(0)
            task.status = "in_progress"
            return task
        return None
    
    def is_empty(self) -> bool:
        """Check if all tasks done."""
        return len(self.tasks) == 0
    
    def mark_complete(self, task: Task, result_file: Optional[str] = None):
        """Mark task as completed."""
        task.status = "completed"
        task.result_file = result_file
        self.completed.append(task)
        logger.info(f"✅ Completed task {task.id}: {task.description}")


class DeepAgent:
    """True DeepAgent with Planning-driven execution.
    
    Core Concepts:
    1. Planning First: Create todo_list before execution
    2. Dynamic Execution: while loop through tasks
    3.SubAgent Spawning: Create specialized agents on-demand
    4. FileSystem Context: Save results to files (not in memory)
    5. Self-Correction: Add tasks if needed
    """
    
    def __init__(self, llm, workspace_dir: str = "./workspace"):
        """Initialize DeepAgent.
        
        Args:
            llm: LangChain LLM for planning and execution
            workspace_dir: Directory for saving intermediate results
        """
        self.llm = llm
        self.workspace = Path(workspace_dir).resolve()  # Use absolute path
        self.workspace.mkdir(parents=True, exist_ok=True)  # Create parent dirs too
        
        # Load SubAgents
        from .subagents import get_subagent
        self.get_subagent = get_subagent
        
        logger.info(f"🗂️  DeepAgent workspace: {self.workspace}")
        logger.info(f"   Directory created: ✅")
    
    def run(self, user_goal: str, context: Optional[str] = None) -> str:
        """Execute user goal with Planning-driven approach.
        
        Args:
            user_goal: User's request
            context: Additional context
            
        Returns:
            Final result
        """
        logger.info("=" * 70)
        logger.info("🚀 DeepAgent Starting")
        logger.info("=" * 70)
        logger.info(f"Goal: {user_goal}")
        
        # [핵심 1] Planning: Create todo_list
        todo_list = self._create_plan(user_goal, context)
        
        logger.info(f"\n📋 Plan created with {len(todo_list.tasks)} tasks")
        for task in todo_list.tasks:
            logger.info(f"  {task.id}. [{task.task_type}] {task.description}")
        logger.info("")
        
        # [핵심 2] Dynamic Execution: While loop
        step = 0
        while not todo_list.is_empty():
            step += 1
            current_task = todo_list.pop()
            
            logger.info(f"\n{'='*70}")
            logger.info(f"📌 Step {step}: Executing task {current_task.id}")
            logger.info(f"   Type: {current_task.task_type}")
            logger.info(f"   Description: {current_task.description}")
            logger.info(f"{'='*70}")
            
            # Execute task
            result, result_file = self._execute_task(current_task)
            
            # Mark as completed
            todo_list.mark_complete(current_task, result_file)
            
            # [핵심 4] Self-Correction: Check if need more tasks
            if self._needs_additional_work(current_task, result):
                new_tasks = self._suggest_additional_tasks(current_task, result)
                for new_task in new_tasks:
                    todo_list.add(new_task)
        
        # Consolidate final result
        logger.info("\n" + "=" * 70)
        logger.info("🎯 All tasks completed")
        logger.info("=" * 70)
        
        final_result = self._consolidate_results(todo_list.completed)
        
        return final_result
    
    def _create_plan(self, user_goal: str, context: Optional[str] = None) -> TodoList:
        """[핵심 1] Planning: LLM creates todo_list.
        
        Args:
            user_goal: User's request
            context: Additional context
            
        Returns:
            TodoList with tasks
        """
        prompt = f"""Create a step-by-step execution plan for the following goal.

Goal: {user_goal}

{f"Context: {context}" if context else ""}

Available SubAgents:
- analysis: Code impact analysis
- coding: Code generation and testing
- documentation: Doc synchronization

Available Actions:
- explore: Use FileSystem tools to explore code
- analyze: Analyze code dependencies
- code: Generate code
- test: Run tests
- doc: Update documentation
- custom: Custom action

Create a sequential todo list. For each task, specify:
1. Task description
2. Task type (explore/analyze/code/test/doc/custom)
3. Whether it needs a SubAgent (yes/no)
4. SubAgent role (if needed)

Format (one per line):
TASK 1: [type] description | subagent:role (or subagent:none)
TASK 2: [type] description | subagent:role

Example:
TASK 1: [explore] List all Python files | subagent:none
TASK 2: [analyze] Analyze dependencies | subagent:analysis
TASK 3: [code] Generate new function | subagent:coding

Your plan:
"""
        
        response = self.llm.invoke(prompt)
        
        # Parse into TodoList
        return self._parse_todo_list(response.content)
    
    def _parse_todo_list(self, plan_text: str) -> TodoList:
        """Parse LLM plan into TodoList."""
        import re
        
        todo_list = TodoList()
        
        # Pattern: TASK N: [type] description | subagent:role
        pattern = r"TASK\s+(\d+):\s*\[(\w+)\]\s*(.+?)\s*\|\s*subagent:(\w+)"
        matches = re.findall(pattern, plan_text)
        
        for task_id, task_type, description, subagent_role in matches:
            task = Task(
                id=int(task_id),
                description=description.strip(),
                task_type=task_type.lower(),
                requires_subagent=(subagent_role != "none"),
                subagent_role=subagent_role if subagent_role != "none" else None
            )
            todo_list.add(task)
        
        return todo_list
    
    def _execute_task(self, task: Task) -> tuple[str, Optional[str]]:
        """Execute a single task.
        
        Returns:
            (result, result_file_path)
        """
        # [핵심 2] SubAgent Spawning
        if task.requires_subagent:
            logger.info(f"🤖 Spawning SubAgent: {task.subagent_role}")
            subagent = self.get_subagent(task.subagent_role)
            
            # Execute with subagent
            result = subagent({"request": task.description})
            
            if isinstance(result, dict):
                result_str = str(result)
            else:
                result_str = result
        else:
            # Execute directly with FileSystem tools
            result_str = self._execute_filesystem_task(task)
        
        # [핵심 3] FileSystem Context: Save to file to save tokens
        result_file = self.workspace / f"task_{task.id}_result.txt"
        result_file.write_text(result_str, encoding='utf-8')
        
        logger.info(f"💾 Result saved to: {result_file.name}")
        logger.info(f"   Result preview: {result_str[:100]}...")
        
        return result_str, str(result_file)
    
    def _execute_filesystem_task(self, task: Task) -> str:
        """Execute FileSystem task."""
        from .filesystem_tools import (
            _list_directory_impl,
            _read_file_impl,
            _glob_search_impl,
            _grep_search_impl
        )
        
        if task.task_type == "explore":
            # List directories
            result = _list_directory_impl(".")
            return "\n".join(result)
        
        elif task.task_type == "search":
            # Grep search
            results = _grep_search_impl(r"def ", "**/*.py")
            return str(results[:10])  # First 10 results
        
        else:
            return f"Executed: {task.description}"
    
    def _needs_additional_work(self, task: Task, result: str) -> bool:
        """[핵심 4] Check if additional work needed."""
        # Simple heuristic: if result mentions "error" or "not found"
        if "error" in result.lower() or "not found" in result.lower():
            return True
        
        # If result is too short (< 50 chars), might need more work
        if len(result) < 50:
            return True
        
        return False
    
    def _suggest_additional_tasks(self, task: Task, result: str) -> List[Task]:
        """[핵심 4] Suggest additional tasks based on result."""
        new_tasks = []
        
        # Example: If analysis found many files, add documentation task
        if task.task_type == "analyze" and "files" in result:
            new_tasks.append(Task(
                id=100 + len(new_tasks),
                description="Update documentation for analyzed files",
                task_type="doc",
                requires_subagent=True,
                subagent_role="documentation"
            ))
        
        return new_tasks
    
    def _consolidate_results(self, completed_tasks: List[Task]) -> str:
        """Consolidate all results into final output."""
        logger.info("\n📊 Consolidating results...")
        
        final_report = "# DeepAgent Execution Report\n\n"
        
        for task in completed_tasks:
            final_report += f"## Task {task.id}: {task.description}\n"
            
            if task.result_file and Path(task.result_file).exists():
                result_content = Path(task.result_file).read_text(encoding='utf-8')
                final_report += f"```\n{result_content[:500]}\n```\n\n"
            else:
                final_report += "*No result file*\n\n"
        
        # Save final report
        final_path = self.workspace / "final_report.md"
        final_path.write_text(final_report, encoding='utf-8')
        
        logger.info(f"📄 Final report saved to: {final_path}")
        
        return final_report