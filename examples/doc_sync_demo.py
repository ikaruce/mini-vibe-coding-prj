"""Document Synchronization Demo (FR-DS-01).

This example demonstrates automatic documentation synchronization:
- Docstring generation and updates
- README update proposals
- Documentation consistency checking

The Self-Healing agent automatically includes doc sync after successful tests.
"""

import asyncio
from ai_assistant.agent import create_self_healing_agent


async def demo_doc_sync():
    """Demo: Automatic documentation synchronization."""
    print("=" * 70)
    print("📝 Document Synchronization Demo (FR-DS-01)")
    print("=" * 70)
    
    agent = create_self_healing_agent()
    
    # Request to generate a function (will trigger doc sync)
    initial_state = {
        "messages": [(
            "user",
            "Create a Python function to validate and parse email addresses. "
            "Return a dict with username and domain parts."
        )],
        "mode": "SPEED",
        "changed_file": "email_utils.py",
        "impacted_files": ["email_utils.py"],
        "retry_count": 0,
        "error_logs": [],
        "context": "Email validation utility"
    }
    
    print("\n📊 Request: Email parser function")
    print("Expected: Code generation → Testing → Documentation Sync")
    print("\n⚙️  Running agent with automatic doc sync...\n")
    
    try:
        result = await agent.ainvoke(initial_state)
        
        # Show generated code
        if result.get("generated_code"):
            print("\n" + "=" * 70)
            print("💻 GENERATED CODE")
            print("=" * 70)
            print(result['generated_code'][:600])
            if len(result['generated_code']) > 600:
                print("... (truncated)")
            print()
        
        # Show test results
        test_results = result.get("test_results", {})
        if test_results:
            print("=" * 70)
            print("🧪 TEST RESULTS")
            print("=" * 70)
            print(f"Status: {'✅ Passed' if test_results.get('success') else '❌ Failed'}")
            print()
        
        # Show documentation sync results
        doc_sync = result.get("doc_sync_result", {})
        if doc_sync:
            print("=" * 70)
            print("📝 DOCUMENTATION SYNCHRONIZATION")
            print("=" * 70)
            
            if doc_sync.get("changes_detected"):
                print(f"\n✨ Found {len(doc_sync.get('proposed_changes', []))} documentation updates\n")
                
                for i, change in enumerate(doc_sync.get("proposed_changes", []), 1):
                    print(f"{i}. {change['type'].upper()}")
                    print(f"   Location: {change['location']}")
                    print(f"   Reason: {change['reason']}")
                    print(f"   Confidence: {change['confidence']:.0%}")
                    print()
                    
                    if change.get('proposed'):
                        print(f"   Proposed Update:")
                        print(f"   {'-' * 60}")
                        # Show first 300 chars of proposal
                        proposal = change['proposed']
                        if len(proposal) > 300:
                            print(f"   {proposal[:300]}...")
                        else:
                            print(f"   {proposal}")
                        print(f"   {'-' * 60}")
                    print()
                
                print("\n📋 Summary:")
                print(f"   {doc_sync.get('summary', 'Documentation analysis complete')}")
                
            else:
                print("\n✅ Documentation is already up to date!")
                print("   No changes needed.")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def demo_readme_sync():
    """Demo: README synchronization after adding new feature."""
    print("\n\n")
    print("=" * 70)
    print("📖 README Synchronization Demo")
    print("=" * 70)
    
    agent = create_self_healing_agent()
    
    initial_state = {
        "messages": [(
            "user",
            "Create a new API endpoint function for user authentication with JWT tokens. "
            "Include login and token validation."
        )],
        "mode": "SPEED",
        "changed_file": "api/auth.py",
        "impacted_files": ["api/auth.py", "README.md"],
        "retry_count": 0,
        "error_logs": [],
        "context": "New authentication API"
    }
    
    print("\n📊 Request: JWT authentication API")
    print("Expected: New feature → README update proposal")
    print("\n⚙️  Running agent...\n")
    
    try:
        result = await agent.ainvoke(initial_state)
        
        # Focus on doc sync results
        doc_sync = result.get("doc_sync_result", {})
        
        if doc_sync and doc_sync.get("changes_detected"):
            readme_changes = [
                c for c in doc_sync.get("proposed_changes", [])
                if c['type'] == 'readme'
            ]
            
            if readme_changes:
                print("=" * 70)
                print("📖 README UPDATE PROPOSED")
                print("=" * 70)
                
                for change in readme_changes:
                    print(f"\n📍 Location: {change['location']}")
                    print(f"💡 Reason: {change['reason']}")
                    print(f"\n📝 Suggested Updates:")
                    print("-" * 70)
                    print(change['proposed'])
                    print("-" * 70)
            else:
                print("✅ README doesn't need updates for this change")
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all document synchronization demos."""
    print("\n" + "📝" * 35)
    print("   Document Synchronization Demo")
    print("   FR-DS-01: Automatic Documentation Updates")
    print("📝" * 35)
    
    # Run demos
    await demo_doc_sync()
    await demo_readme_sync()
    
    print("\n" + "✨" * 35)
    print("   All Demos Complete!")
    print("   Documentation is now synchronized! 📚")
    print("✨" * 35 + "\n")


if __name__ == "__main__":
    asyncio.run(main())