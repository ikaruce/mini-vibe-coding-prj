"""Code generation example."""

import asyncio
from ai_assistant.agent import create_agent


async def generate_code_example():
    """Example of using the agent for code generation."""
    print("AI Coding Assistant - Code Generation Example")
    print("=" * 50)
    
    agent = create_agent()
    
    # Example task
    task = """
    Write a Python function that:
    1. Takes a list of numbers as input
    2. Filters out even numbers
    3. Squares the remaining odd numbers
    4. Returns the sum of the squared odd numbers
    
    Include error handling and type hints.
    """
    
    print(f"Task:\n{task}\n")
    print("Generating code...\n")
    
    try:
        response = await agent.ainvoke({
            "messages": [("user", task)]
        })
        
        generated_code = response["messages"][-1].content
        print("Generated Code:")
        print("=" * 50)
        print(generated_code)
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Please check your API key and configuration.")


if __name__ == "__main__":
    asyncio.run(generate_code_example())