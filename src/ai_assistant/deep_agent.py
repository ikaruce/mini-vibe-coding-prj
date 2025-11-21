"""DeepAgent using LangChain DeepAgents Library.

REQUIREMENT.md 대기능4:
"DeepAgents Library에 이미 포함되어 있는 FilesystemMiddleware를 활용합니다.
(FileSystemBackend 사용 필수)"

Official docs: https://docs.langchain.com/oss/python/deepagents/subagents
"""

import logging
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend  # 소문자 's'
from langchain_openai import ChatOpenAI

from .config import get_config, validate_config, setup_langsmith_tracing
from .tools import get_tools
from .filesystem_tools import get_filesystem_tools

logger = logging.getLogger(__name__)


def create_ai_coding_deep_agent(enable_tracing: bool = True):
    """Create AI Coding Assistant using DeepAgents library.
    
    Follows official pattern from:
    https://docs.langchain.com/oss/python/deepagents/subagents
    
    With subagents parameter as shown in documentation.
    
    Args:
        enable_tracing: Enable LangSmith tracing
        
    Returns:
        DeepAgent (CompiledStateGraph)
    """
    # Setup tracing
    if enable_tracing:
        config = get_config()
        setup_langsmith_tracing(config)
    
    config = get_config()
    validate_config(config)
    
    logger.info("Creating DeepAgent with subagents...")
    
    # Create ChatOpenAI instance for OpenRouter
    llm = ChatOpenAI(
        model=config.openrouter_model,
        openai_api_key=config.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI Coding Assistant"
        },
        temperature=config.temperature,
    )
    
    # Get all tools
    all_tools = get_tools() + get_filesystem_tools()
    
    # Define SubAgents (as dicts, matching official docs)
    subagents = [
        {
            "name": "analysis",
            "description": "Analyze code dependencies and impact",
            "system_prompt": "You are a code analysis expert. Analyze dependencies using Tree-sitter or LSP."
        },
        {
            "name": "coding",
            "description": "Generate code and tests with self-healing",
            "system_prompt": "You are an expert Python developer. Generate PEP8-compliant code with tests."
        },
        {
            "name": "documentation",
            "description": "Sync documentation with code changes",
            "system_prompt": "You are a technical writer. Generate Google-style docstrings."
        }
    ]
    
    # Create FilesystemBackend (REQUIREMENT.md: "FileSystemBackend 사용 필수")
    fs_backend = FilesystemBackend(root_dir=".")
    
    # Create DeepAgent with backend
    agent = create_deep_agent(
        model=llm,  # ChatOpenAI instance for OpenRouter
        tools=all_tools,
        system_prompt="""You are an expert AI Coding Assistant.

You have specialized SubAgents:
- analysis: Code impact analysis
- coding: Code generation with testing
- documentation: Documentation updates

You have FileSystem tools for exploration and modification.

Delegate complex tasks to SubAgents. Always follow PEP8.""",
        subagents=subagents,  # SubAgents list
        backend=fs_backend  # FileSystemBackend (required by REQUIREMENT.md)
    )
    
    logger.info("✅ DeepAgent created with SubAgents")
    
    return agent