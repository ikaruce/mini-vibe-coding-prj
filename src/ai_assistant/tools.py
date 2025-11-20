"""Tools for the AI coding assistant."""

from langchain.tools import tool
from typing import Literal

# Import FileSystem tools (FR-FS-01, FR-FS-02, FR-FS-03, FR-FS-04)
try:
    from .filesystem_tools import get_filesystem_tools
    FILESYSTEM_TOOLS_AVAILABLE = True
except ImportError:
    FILESYSTEM_TOOLS_AVAILABLE = False


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


def get_tools(include_filesystem: bool = True):
    """Get all available tools.
    
    Args:
        include_filesystem: Whether to include file system tools (default: True)
        
    Returns:
        List of all available LangChain tools
    """
    tools = [generate_code, explain_code]
    
    # Add file system tools if available (FR-FS)
    if include_filesystem and FILESYSTEM_TOOLS_AVAILABLE:
        tools.extend(get_filesystem_tools())
    
    return tools