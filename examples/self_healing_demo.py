"""Self-Healing Code Generation Demo.

This example demonstrates FR-AC-01, FR-AC-02, and FR-AC-03:
- Automatic code generation based on user request
- Self-healing loop with max 3 retries
- Automatic test generation and execution

Run this demo to see the agent:
1. Generate code based on your request
2. Generate unit tests automatically
3. Execute tests
4. If tests fail, automatically fix the code (up to 3 times)
5. Report final results
"""

import asyncio
from ai_assistant.agent import create_self_healing_agent


async def demo_simple_function():
    """Demo: Generate a simple mathematical function."""
    print("=" * 70)
    print("📝 Demo: Generate Simple Function with Self-Healing")
    print("=" * 70)
    
    agent = create_self_healing_agent()
    
    # Request to generate a function
    initial_state = {
        "messages": [("user", "Create a Python function to calculate the factorial of a number")],
        "mode": "SPEED",
        "changed_file": "math_utils.py",
        "impacted_files": ["math_utils.py"],
        "retry_count": 0,
        "error_logs": [],
        "context": "Create a well-tested factorial function"
    }
    
    print("\n📊 Request: Create factorial function")
    print("Mode: SPEED")
    print("\n⚙️  Running Self-Healing Agent...\n")
    
    try:
        result = await agent.ainvoke(initial_state)
        
        # Show results
        print("\n" + "=" * 70)
        print("📈 RESULTS")
        print("=" * 70)
        
        if result.get("generated_code"):
            print("\n💻 Generated Code:")
            print("-" * 70)
            print(result['generated_code'][:500])
            if len(result['generated_code']) > 500:
                print("... (truncated)")
            print("-" * 70)
        
        if result.get("generated_tests"):
            print("\n🧪 Generated Tests:")
            print("-" * 70)
            print(result['generated_tests'][:500])
            if len(result['generated_tests']) > 500:
                print("... (truncated)")
            print("-" * 70)
        
        # Healing results
        healing_result = result.get("healing_result", {})
        if healing_result:
            print(f"\n🔧 Self-Healing Results:")
            print(f"   Success: {'✅ Yes' if healing_result.get('success') else '❌ No'}")
            print(f"   Retries: {healing_result.get('retry_count', 0)}/3")
            
            if healing_result.get('error_logs'):
                print(f"\n   Error History:")
                for i, error in enumerate(healing_result.get('error_logs', []), 1):
                    print(f"      {i}. {error}")
        
        # Test results
        test_results = result.get("test_results", {})
        if test_results:
            print(f"\n🔬 Final Test Results:")
            print(f"   Status: {'✅ Passed' if test_results.get('success') else '❌ Failed'}")
            if not test_results.get('success') and test_results.get('stderr'):
                print(f"\n   Errors:")
                print(f"   {test_results.get('stderr')[:300]}")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def demo_with_precision_mode():
    """Demo: Use PRECISION mode for analysis before code generation."""
    print("\n\n")
    print("=" * 70)
    print("🎯 Demo: PRECISION Mode with Self-Healing")
    print("=" * 70)
    
    agent = create_self_healing_agent()
    
    initial_state = {
        "messages": [("user", "Create a function to validate email addresses using regex")],
        "mode": "PRECISION",  # Will likely fallback to SPEED
        "changed_file": "validators.py",
        "impacted_files": ["validators.py"],
        "retry_count": 0,
        "error_logs": [],
        "context": "Email validation with comprehensive tests"
    }
    
    print("\n📊 Request: Email validator function")
    print("Mode: PRECISION (may fallback to SPEED)")
    print("\n⚙️  Running Self-Healing Agent...\n")
    
    try:
        result = await agent.ainvoke(initial_state)
        
        # Show analysis results
        analysis_result = result.get("analysis_result", {})
        if analysis_result:
            print(f"\n📊 Analysis Results:")
            print(f"   Mode Used: {analysis_result.get('mode', 'N/A')}")
            if analysis_result.get('time'):
                print(f"   Analysis Time: {analysis_result.get('time'):.2f}s")
        
        # Show final status
        healing_result = result.get("healing_result", {})
        test_results = result.get("test_results", {})
        
        if healing_result and test_results:
            status = "✅ SUCCESS" if (
                healing_result.get('success') and test_results.get('success')
            ) else "❌ FAILED"
            
            print(f"\n{'='*70}")
            print(f"Final Status: {status}")
            print(f"Healing Attempts: {healing_result.get('retry_count', 0)}/3")
            print(f"Tests Passed: {'Yes' if test_results.get('success') else 'No'}")
            print(f"{'='*70}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def demo_complex_function():
    """Demo: Generate a more complex function to showcase self-healing."""
    print("\n\n")
    print("=" * 70)
    print("🔬 Demo: Complex Function with Multiple Self-Healing Attempts")
    print("=" * 70)
    
    agent = create_self_healing_agent()
    
    initial_state = {
        "messages": [(
            "user",
            "Create a function to parse JSON data and calculate statistics "
            "(mean, median, mode) for a list of numbers. Include error handling "
            "for invalid JSON and non-numeric values."
        )],
        "mode": "SPEED",
        "changed_file": "stats_parser.py",
        "impacted_files": ["stats_parser.py"],
        "retry_count": 0,
        "error_logs": [],
        "context": "JSON parsing with statistical calculations"
    }
    
    print("\n📊 Request: JSON parser with statistics")
    print("Expected: Complex function requiring type hints and error handling")
    print("\n⚙️  Running Self-Healing Agent...\n")
    
    try:
        result = await agent.ainvoke(initial_state)
        
        # Detailed healing history
        healing_result = result.get("healing_result", {})
        if healing_result:
            print(f"\n🔧 Self-Healing Journey:")
            print(f"{'='*70}")
            
            retry_count = healing_result.get('retry_count', 0)
            if retry_count == 0:
                print("✨ Code passed on first try! No healing needed.")
            else:
                print(f"🔄 Healing attempts: {retry_count}")
                for i, error in enumerate(healing_result.get('error_logs', []), 1):
                    print(f"\n   Attempt {i}:")
                    print(f"   └─ {error}")
            
            print(f"\n{'='*70}")
            
            # Final result
            if healing_result.get('success'):
                print("\n🎉 Successfully generated and tested code!")
            else:
                print("\n⚠️  Code generation completed but tests may have failed.")
                print("   (This can happen if the problem is very complex)")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all Self-Healing demos."""
    print("\n" + "🔧" * 35)
    print("   Self-Healing Code Generation Demo")
    print("   FR-AC-01: Code Generation")
    print("   FR-AC-02: Self-Healing Loop (Max 3 retries)")
    print("   FR-AC-03: Automatic Test Generation")
    print("🔧" * 35)
    
    # Run demos
    await demo_simple_function()
    await demo_with_precision_mode()
    await demo_complex_function()
    
    print("\n" + "✨" * 35)
    print("   All Demos Complete!")
    print("✨" * 35 + "\n")


if __name__ == "__main__":
    asyncio.run(main())