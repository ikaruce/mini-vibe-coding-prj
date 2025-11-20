"""Configuration management for the AI assistant."""

from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration."""
    
    openrouter_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "")
    )
    openrouter_model: str = Field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_MODEL", 
            "anthropic/claude-3.5-sonnet"
        )
    )
    temperature: float = Field(default=0.7)
    max_tokens: Optional[int] = Field(default=None)
    
    # LangSmith settings
    langchain_tracing: bool = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    )
    langchain_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_API_KEY")
    )
    langchain_project: str = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_PROJECT", "ai-coding-assistant")
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_config() -> Config:
    """Get the application configuration."""
    return Config()


def validate_config(config: Config) -> None:
    """Validate configuration."""
    if not config.openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is required. "
            "Please set it in your .env file or environment variables."
        )


def setup_langsmith_tracing(config: Config) -> None:
    """Setup LangSmith tracing for LangGraph debugging.
    
    This enables:
    - Real-time tracking of LangGraph execution
    - Visualization of node transitions (SPEED/PRECISION branching)
    - State changes at each step
    - Performance metrics
    - Error tracking
    
    Args:
        config: Application configuration with LangSmith settings
        
    Note:
        LangSmith tracing is automatically enabled when LANGCHAIN_TRACING_V2=true
        in your .env file. This function validates the setup.
    """
    if config.langchain_tracing:
        if not config.langchain_api_key:
            print("⚠️  Warning: LANGCHAIN_TRACING_V2 is enabled but LANGCHAIN_API_KEY is not set.")
            print("   LangSmith tracing will be disabled.")
            print("   Get your API key at: https://smith.langchain.com")
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
        else:
            print("✅ LangSmith tracing enabled")
            print(f"   Project: {config.langchain_project}")
            print(f"   Dashboard: https://smith.langchain.com")
            
            # Ensure environment variables are set for LangChain
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = config.langchain_api_key
            os.environ["LANGCHAIN_PROJECT"] = config.langchain_project
            os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
                "LANGCHAIN_ENDPOINT",
                "https://api.smith.langchain.com"
            )
    else:
        print("ℹ️  LangSmith tracing disabled (set LANGCHAIN_TRACING_V2=true to enable)")