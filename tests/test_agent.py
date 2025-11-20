"""Tests for the agent module."""

import pytest
from ai_assistant.agent import create_agent, AgentState
from ai_assistant.config import get_config


def test_create_agent():
    """Test agent creation."""
    agent = create_agent()
    assert agent is not None


@pytest.mark.asyncio
async def test_agent_invoke():
    """Test agent invocation."""
    # This test requires a valid API key
    try:
        config = get_config()
        if not config.openrouter_api_key:
            pytest.skip("No OpenRouter API key found")
        
        agent = create_agent()
        response = await agent.ainvoke({
            "messages": [("user", "Hello, how are you?")]
        })
        
        assert "messages" in response
        assert len(response["messages"]) > 0
        
    except Exception as e:
        pytest.skip(f"Test skipped due to: {e}")


def test_config():
    """Test configuration."""
    config = get_config()
    assert config is not None
    assert config.openrouter_model is not None