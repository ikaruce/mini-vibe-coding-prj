"""Demonstration of SPEED/PRECISION mode branching in LangGraph.

This example shows how the agent automatically routes to different
analysis modes based on the state configuration.

Based on claude.md requirements:
- FR-IA-01: Dual-mode selection via state
- FR-IA-02: SPEED mode using Tree-sitter + NetworkX
- FR-IA-03: PRECISION mode using LSP
- FR-IA-04: Fallback mechanism from PRECISION to SPEED
"""

import asyncio
from ai_assistant.agent import create_agent


async def test_speed_mode():
    """Test SPEED mode analysis."""
    print("=" * 70)
    print("🚀 Testing SPEED MODE")
    print("=" * 70)
    
    agent = create_agent()
    
    # Initial state with SPEED mode
    initial_state = {
        "messages": [("user", "Analyze the impact of changing config.py")],
        "mode": "SPEED",
        "changed_file": "src/ai_assistant/config.py",
        "changed_symbol": "get_config",
        "impacted_files": [],
        "retry_count": 0,
        "error_logs": [],
        "context": "",
        "task_type": "code_generation",
        "analysis_result": None
    }
    
    print(f"\n📊 Initial State:")
    print(f"   Mode: {initial_state['mode']}")
    print(f"   Changed File: {initial_state['changed_file']}")
    print(f"   Changed Symbol: {initial_state['changed_symbol']}")
    
    try:
        print(f"\n⚙️  Running agent with SPEED mode...")
        result = await agent.ainvoke(initial_state)
        
        print(f"\n✅ Analysis Complete!")
        print(f"\n📈 Results:")
        print(f"   Impacted Files: {len(result.get('impacted_files', []))}")
        for file in result.get('impacted_files', []):
            print(f"      - {file}")
        
        analysis_result = result.get('analysis_result', {})
        if analysis_result:
            print(f"\n📊 Analysis Metadata:")
            print(f"   Mode Used: {analysis_result.get('mode', 'N/A')}")
            print(f"   Analysis Time: {analysis_result.get('time', 0):.2f}s")
            if analysis_result.get('warnings'):
                print(f"   Warnings: {analysis_result.get('warnings')}")
        
        # Show final message
        if result.get('messages'):
            last_message = result['messages'][-1]
            print(f"\n💬 Agent Response:")
            print(f"   {last_message.content[:200]}...")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_precision_mode():
    """Test PRECISION mode analysis with fallback."""
    print("\n" * 2)
    print("=" * 70)
    print("🎯 Testing PRECISION MODE (with expected fallback to SPEED)")
    print("=" * 70)
    
    agent = create_agent()
    
    # Initial state with PRECISION mode
    initial_state = {
        "messages": [("user", "Precisely analyze the impact of changing agent.py")],
        "mode": "PRECISION",
        "changed_file": "src/ai_assistant/agent.py",
        "changed_symbol": "create_agent",
        "impacted_files": [],
        "retry_count": 0,
        "error_logs": [],
        "context": "",
        "task_type": "code_generation",
        "analysis_result": None
    }
    
    print(f"\n📊 Initial State:")
    print(f"   Mode: {initial_state['mode']}")
    print(f"   Changed File: {initial_state['changed_file']}")
    print(f"   Changed Symbol: {initial_state['changed_symbol']}")
    
    try:
        print(f"\n⚙️  Running agent with PRECISION mode...")
        print(f"   (Note: PRECISION may fallback to SPEED if LSP unavailable)")
        
        result = await agent.ainvoke(initial_state)
        
        print(f"\n✅ Analysis Complete!")
        print(f"\n📈 Results:")
        print(f"   Impacted Files: {len(result.get('impacted_files', []))}")
        for file in result.get('impacted_files', []):
            print(f"      - {file}")
        
        analysis_result = result.get('analysis_result', {})
        if analysis_result:
            print(f"\n📊 Analysis Metadata:")
            print(f"   Mode Requested: PRECISION")
            print(f"   Mode Actually Used: {analysis_result.get('mode', 'N/A')}")
            print(f"   Analysis Time: {analysis_result.get('time', 0):.2f}s")
            
            if analysis_result.get('error'):
                print(f"   ⚠️  Error encountered: {analysis_result.get('error')}")
                print(f"   ℹ️  This triggered automatic fallback to SPEED mode")
            
            if analysis_result.get('warnings'):
                print(f"   Warnings:")
                for warning in analysis_result.get('warnings'):
                    print(f"      - {warning}")
        
        # Show error logs if any
        if result.get('error_logs'):
            print(f"\n📋 Error Logs:")
            for error in result.get('error_logs'):
                print(f"   - {error}")
        
        # Show final message
        if result.get('messages'):
            last_message = result['messages'][-1]
            print(f"\n💬 Agent Response:")
            print(f"   {last_message.content[:200]}...")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def compare_modes():
    """Compare SPEED vs PRECISION modes side by side."""
    print("\n" * 2)
    print("=" * 70)
    print("⚖️  COMPARING SPEED vs PRECISION MODES")
    print("=" * 70)
    
    from ai_assistant.analyzers import SpeedAnalyzer, PrecisionAnalyzer
    import time
    
    changed_file = "src/ai_assistant/config.py"
    
    print(f"\nAnalyzing: {changed_file}")
    print(f"\n{'Mode':<15} {'Time (s)':<12} {'Files':<8} {'Status'}")
    print("-" * 70)
    
    # Test SPEED mode
    try:
        speed_analyzer = SpeedAnalyzer(".")
        start = time.time()
        speed_result = speed_analyzer.analyze(changed_file)
        speed_time = time.time() - start
        
        speed_status = "✅ Success" if not speed_result.error else f"❌ {speed_result.error[:20]}"
        print(f"{'SPEED':<15} {speed_time:<12.3f} {len(speed_result.impacted_files):<8} {speed_status}")
        
    except Exception as e:
        print(f"{'SPEED':<15} {'N/A':<12} {'N/A':<8} ❌ {str(e)[:30]}")
    
    # Test PRECISION mode
    try:
        precision_analyzer = PrecisionAnalyzer(".")
        start = time.time()
        precision_result = precision_analyzer.analyze(changed_file)
        precision_time = time.time() - start
        
        precision_status = "✅ Success" if not precision_result.error else f"⚠️  {precision_result.error[:20]}"
        print(f"{'PRECISION':<15} {precision_time:<12.3f} {len(precision_result.impacted_files):<8} {precision_status}")
        
        if precision_result.warnings:
            print(f"\n   PRECISION Warnings:")
            for warning in precision_result.warnings:
                print(f"      - {warning}")
        
    except Exception as e:
        print(f"{'PRECISION':<15} {'N/A':<12} {'N/A':<8} ❌ {str(e)[:30]}")
    
    print("\n" + "=" * 70)
    print("📝 Summary:")
    print("   - SPEED: Fast, text-based analysis (Tree-sitter + NetworkX)")
    print("   - PRECISION: Accurate, compiler-level analysis (LSP)")
    print("   - Fallback: PRECISION → SPEED on error (FR-IA-04)")
    print("=" * 70)


async def main():
    """Run all mode branching demonstrations."""
    print("\n" + "🔬" * 35)
    print("   LangGraph Mode Branching Demonstration")
    print("   Based on claude.md Requirements")
    print("🔬" * 35)
    
    # Test individual modes
    await test_speed_mode()
    await test_precision_mode()
    
    # Compare modes
    await compare_modes()
    
    print("\n" + "✨" * 35)
    print("   Demo Complete!")
    print("✨" * 35 + "\n")


if __name__ == "__main__":
    asyncio.run(main())