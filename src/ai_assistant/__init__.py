"""AI Coding Assistant using LangChain and LangGraph."""

__version__ = "0.1.0"

from .agent import create_agent
from .config import get_config

__all__ = ["create_agent", "get_config"]