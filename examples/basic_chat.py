"""Basic chat example with the AI coding assistant."""

import asyncio
from ai_assistant.agent import create_agent


async def main():
    """Run a basic chat session."""
    print("AI Coding Assistant - Basic Chat")
    print("=" * 50)
    print("Type 'exit' or 'quit' to end the session\n")
    
    agent = create_agent()
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nGoodbye! 👋")
            break
        
        if not user_input:
            continue
        
        try:
            # Invoke the agent
            response = await agent.ainvoke({
                "messages": [("user", user_input)]
            })
            
            # Print the response
            assistant_message = response["messages"][-1].content
            print(f"\nAssistant: {assistant_message}\n")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            print("Please check your API key and internet connection.\n")


if __name__ == "__main__":
    asyncio.run(main())