"""AI Coding Assistant - CLI Runner

실제 사용을 위한 커맨드라인 인터페이스입니다.

사용 방법:
    python run_agent.py                    # 기본 에이전트 (대화형)
    python run_agent.py --mode deep        # DeepAgent (Planning-driven)
    python run_agent.py --mode healing     # Self-Healing Agent
    python run_agent.py --once "요청 내용"  # 한 번만 실행
"""

import asyncio
import argparse
from ai_assistant import create_agent, create_self_healing_agent, create_ai_coding_deep_agent


async def interactive_mode(agent_type: str = "basic"):
    """대화형 모드로 에이전트 실행."""
    print("=" * 70)
    print("🤖 AI Coding Assistant - Interactive Mode")
    print("=" * 70)
    
    # 에이전트 생성
    if agent_type == "deep":
        print("\n🔧 Loading DeepAgent (Planning-driven)...")
        agent = create_ai_coding_deep_agent()
        print("   ✅ DeepAgent with SubAgents ready")
    elif agent_type == "healing":
        print("\n🔧 Loading Self-Healing Agent...")
        agent = create_self_healing_agent()
        print("   ✅ Self-Healing Agent ready")
    else:
        print("\n🔧 Loading Basic Agent...")
        agent = create_agent()
        print("   ✅ Basic Agent ready")
    
    print("\n💡 Tips:")
    print("   - 'exit' or 'quit' to end")
    print("   - Type your coding requests naturally")
    if agent_type == "deep":
        print("   - DeepAgent will create a plan first, then execute")
    if agent_type == "healing":
        print("   - Agent will auto-fix code errors (max 3 retries)")
    
    print("\n" + "=" * 70)
    print()
    
    while True:
        # Get user input
        user_input = input("You: ").strip()
        
        # Check exit
        if user_input.lower() in ["exit", "quit", "q"]:
            print("\nGoodbye! 👋\n")
            break
        
        if not user_input:
            continue
        
        try:
            print("\n⚙️  Processing...\n")
            
            # Invoke agent
            response = await agent.ainvoke({
                "messages": [("user", user_input)]
            })
            
            # Show response
            if response.get("messages"):
                assistant_msg = response["messages"][-1].content
                print("🤖 Assistant:")
                print("-" * 70)
                print(assistant_msg)
                print("-" * 70)
                print()
            else:
                print("⚠️  No response generated\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye! 👋\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            print("Please check your configuration and try again.\n")


async def single_request_mode(request: str, agent_type: str = "basic"):
    """한 번만 실행하는 모드."""
    print("=" * 70)
    print("🤖 AI Coding Assistant - Single Request")
    print("=" * 70)
    
    # 에이전트 생성
    if agent_type == "deep":
        agent = create_ai_coding_deep_agent()
    elif agent_type == "healing":
        agent = create_self_healing_agent()
    else:
        agent = create_agent()
    
    print(f"\n📝 Request: {request}\n")
    print("⚙️  Processing...\n")
    
   # Invoke agent
    response = await agent.ainvoke({
        "messages": [("user", request)]
    })
    
    # Show response
    print("=" * 70)
    print("🤖 Response:")
    print("=" * 70)
    
    if response.get("messages"):
        print(response["messages"][-1].content)
    else:
        print("⚠️  No response generated")
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="AI Coding Assistant CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 대화형 모드 (기본)
  python run_agent.py
  
  # DeepAgent 대화형
  python run_agent.py --mode deep
  
  # Self-Healing Agent 대화형  
  python run_agent.py --mode healing
  
  # 한 번만 실행
  python run_agent.py --once "List all Python files in src"
  
  # DeepAgent로 한 번 실행
  python run_agent.py --mode deep --once "Analyze config.py"
"""
    )
    
    parser.add_argument(
        "--mode",
        choices=["basic", "deep", "healing"],
        default="basic",
        help="Agent mode (basic/deep/healing)"
    )
    
    parser.add_argument(
        "--once",
        type=str,
        help="Single request mode (non-interactive)"
    )
    
    args = parser.parse_args()
    
    # Run in appropriate mode
    if args.once:
        asyncio.run(single_request_mode(args.once, args.mode))
    else:
        asyncio.run(interactive_mode(args.mode))


if __name__ == "__main__":
    main()