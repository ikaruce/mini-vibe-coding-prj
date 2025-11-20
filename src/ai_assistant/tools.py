"""Tools for the AI coding assistant."""

from langchain.tools import tool
from typing import Literal


@tool
def generate_code(
    task_description: str,
    language: str = "python",
    framework: str = None
) -> str:
    """Generate code based on the given task description.
    
    Args:
        task_description: Description of what the code should do
        language: Programming language (default: python)
        framework: Optional framework to use
    
    Returns:
        Generated code as a string
    """
    # This is a placeholder - the actual implementation will be handled by the LLM
    return f"Tool called: generate_code for {language}"


@tool
def explain_code(
    code: str,
    detail_level: Literal["brief", "detailed"] = "brief"
) -> str:
    """Explain the given code.
    
    Args:
        code: The code to explain
        detail_level: Level of detail (brief or detailed)
    
    Returns:
        Explanation of the code
    """
    # This is a placeholder - the actual implementation will be handled by the LLM
    return f"Tool called: explain_code with {detail_level} detail"


def get_tools():
    """Get all available tools."""
    return [generate_code, explain_code]