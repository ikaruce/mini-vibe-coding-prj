"""AI Coding Assistant using LangChain and LangGraph."""

__version__ = "0.1.0"

# Import logging_config first to setup Rich logging
from .logging_config import setup_logging
setup_logging()

from .agent import create_agent, create_self_healing_agent, create_simple_agent
from .deep_agent import create_ai_coding_deep_agent  # DeepAgents library-based
from .config import get_config

__all__ = [
    "create_agent",
    "create_self_healing_agent",
    "create_simple_agent",
    "create_ai_coding_deep_agent",  # DeepAgents library
    "get_config"
]