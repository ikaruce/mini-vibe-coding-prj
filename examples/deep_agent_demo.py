"""DeepAgent Demo using LangChain DeepAgents Library.

Uses: from deepagents import create_deep_agent
With: FilesystemMiddleware (REQUIREMENT.md 대기능4)
"""

import asyncio
from ai_assistant import create_ai_coding_deep_agent


async def main():
    print("=" * 70)
    print("🤖 DeepAgent Demo (DeepAgents Library)")
    print("=" * 70)
    
    print("\n🔧 Initializing DeepAgent...")
    print("   Using: from deepagents import create_deep_agent")
    print("   With: FilesystemMiddleware ✅")
    print("   Tools: FileSystem + Code generation")
    
    agent = create_ai_coding_deep_agent()
    
    print("\n✅ DeepAgent initialized!\n")
    
    # Example 1: Simple file exploration
    print("=" * 70)
    print("📝 Example: File System Exploration")
    print("=" * 70)
    
    response = await agent.ainvoke({
        "messages": [("user", "List all Python files in the src/ai_assistant directory")]
    })
    
    print("\n📊 Agent Response:")
    print("-" * 70)
    if response.get("messages"):
        print(response["messages"][-1].content[:800])
    print("-" * 70)
    
    print("\n" + "=" * 70)
    print("✨ DeepAgent Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()