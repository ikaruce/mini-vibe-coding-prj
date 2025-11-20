"""AI Coding Assistant using LangChain and LangGraph."""

__version__ = "0.1.0"

# Import logging_config first to setup Rich logging
import sys
sys.path.insert(0, str(__file__.rsplit('src', 1)[0] + 'src'))
from logging_config import setup_logging
setup_logging()

from .agent import create_agent, create_self_healing_agent, create_simple_agent
from .config import get_config

__all__ = [
    "create_agent",
    "create_self_healing_agent",
    "create_simple_agent",
    "get_config"
]