"""File System Tools Demo (FR-FS-01, FR-FS-02, FR-FS-03, FR-FS-04).

This example demonstrates file system exploration and manipulation:
- FR-FS-01: Directory listing and file reading
- FR-FS-02: Pattern-based search (glob, grep)
- FR-FS-03: Precise file modification (edit, write)
- FR-FS-04: Large file handling with SubAgent

Based on DeepAgents FileSystemBackend concepts.
"""

# Import implementation functions directly
from ai_assistant.filesystem_tools import (
    _list_directory_impl as list_directory,
    _read_file_impl as read_file,
)

# Import tools for other functions
from ai_assistant import filesystem_tools


def demo_exploration():
    """FR-FS-01: Contextual Exploration Demo."""
    print("=" * 70)
    print("📁 FR-FS-01: Contextual Exploration")
    print("=" * 70)
    
    # 1. List root directory
    print("\n1️⃣ Listing root directory:")
    print("-" * 70)
    result = list_directory(".")
    for item in result[:10]:  # Show first 10
        print(f"   {item}")
    if len(result) > 10:
        print(f"   ... and {len(result) - 10} more items")
    
    # 2. List source directory
    print("\n2️⃣ Listing src/ai_assistant directory:")
    print("-" * 70)
    result = list_directory("src/ai_assistant")
    for item in result:
        print(f"   {item}")
    
    # 3. Read a small file
    print("\n3️⃣ Reading pyproject.toml:")
    print("-" * 70)
    content = read_file("pyproject.toml", max_lines=20)
    print(content)
    
    print("\n" + "=" * 70 + "\n")


def demo_search():
    """FR-FS-02: Pattern-based Search Demo."""
    print("=" * 70)
    print("🔍 FR-FS-02: Pattern-based Search")
    print("=" * 70)
    
    # 1. Glob search for Python files
    print("\n1️⃣ Finding all Python files in src:")
    print("-" * 70)
    py_files = filesystem_tools.glob_search.invoke({"pattern": "**/*.py", "root_dir": "src"})
    for file in py_files[:10]:
        print(f"   📄 {file}")
    if len(py_files) > 10:
        print(f"   ... and {len(py_files) - 10} more files")
    
    # 2. Glob search for docs
    print("\n2️⃣ Finding all markdown files:")
    print("-" * 70)
    md_files = filesystem_tools.glob_search.invoke({"pattern": "**/*.md"})
    for file in md_files:
        print(f"   📝 {file}")
    
    # 3. Grep search for function definitions
    print("\n3️⃣ Searching for 'def create_' functions:")
    print("-" * 70)
    matches = filesystem_tools.grep_search.invoke({
        "search_pattern": r"def create_",
        "file_pattern": "src/**/*.py",
        "context_lines": 1
    })
    
    for match in matches[:5]:  # Show first 5
        if "error" not in match:
            print(f"\n   📍 {match['file']}:{match['line']}")
            print(f"   {match['text']}")
    
    if len(matches) > 5:
        print(f"\n   ... and {len(matches) - 5} more matches")
    
    # 4. Grep search for imports
    print("\n4️⃣ Searching for LangChain imports:")
    print("-" * 70)
    matches = filesystem_tools.grep_search.invoke({
        "search_pattern": r"from langchain",
        "file_pattern": "src/**/*.py",
        "context_lines": 0
    })
    
    print(f"   Found {len(matches)} import statements")
    for match in matches[:3]:
        if "error" not in match:
            print(f"   • {match['file']}:{match['line']} - {match['text']}")
    
    print("\n" + "=" * 70 + "\n")


def demo_modification():
    """FR-FS-03: Precise Code Modification Demo."""
    print("=" * 70)
    print("✏️  FR-FS-03: File Modification")
    print("=" * 70)
    
    # 1. Create a test file
    print("\n1️⃣ Creating a new test file:")
    print("-" * 70)
    test_content = """# Test File for Demo

def greet(name: str) -> str:
    '''Greet someone.'''
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
"""
    
    result = filesystem_tools.write_file.invoke({"file_path": "temp/test_demo.py", "content": test_content})
    print(f"   {result}")
    
    # 2. Read the created file
    print("\n2️⃣ Reading the created file:")
    print("-" * 70)
    content = read_file("temp/test_demo.py")
    print(content)
    
    # 3. Edit the file (replace text)
    print("\n3️⃣ Editing file (changing greeting):")
    print("-" * 70)
    result = filesystem_tools.edit_file.invoke({
        "file_path": "temp/test_demo.py",
        "search_text": 'return f"Hello, {name}!"',
        "replace_text": 'return f"Hi there, {name}! 👋"'
    })
    print(f"   {result}")
    
    # 4. Read modified file
    print("\n4️⃣ Reading modified file:")
    print("-" * 70)
    content = read_file("temp/test_demo.py")
    print(content)
    
    # 5. Append to file
    print("\n5️⃣ Appending to file:")
    print("-" * 70)
    result = filesystem_tools.write_file.invoke({
        "file_path": "temp/test_demo.py",
        "content": "\n\n# Added by demo\ndef farewell(name: str) -> str:\n    return f\"Goodbye, {name}!\"\n",
        "mode": "a"
    })
    print(f"   {result}")
    
    print("\n" + "=" * 70 + "\n")


def demo_large_file_handling():
    """FR-FS-04: Large File Handling Demo."""
    print("=" * 70)
    print("📦 FR-FS-04: Large File Handling")
    print("=" * 70)
    
    # Create a large file for demo
    print("\n1️⃣ Creating a large file (for demo purposes):")
    print("-" * 70)
    
    large_content = "# Large File Demo\n\n"
    large_content += "def dummy_function_{}(x):\n    return x * 2\n\n" * 1000  # 1000 functions
    
    result = filesystem_tools.write_file.invoke({"file_path": "temp/large_file_demo.py", "content": large_content})
    print(f"   {result}")
    
    # Try to read with normal read_file
    print("\n2️⃣ Attempting to read large file:")
    print("-" * 70)
    content = read_file("temp/large_file_demo.py")
    
    if "too large" in content.lower():
        print("   ⚠️  File exceeds size limit")
        print(content)
        
        # Use read_file_with_summary
        print("\n3️⃣ Reading with auto-summarization:")
        print("-" * 70)
        print("   (This would trigger SubAgent summarization)")
        print("   (In auto mode, no user prompt)")
        # Uncomment to actually test:
        # summary = read_file_with_summary("temp/large_file_demo.py", auto_summarize=True)
        # print(summary)
    else:
        print(content[:500])
        print("...")
    
    print("\n" + "=" * 70 + "\n")


def demo_agent_usage():
    """Demo: Using FileSystem tools with agent."""
    print("=" * 70)
    print("🤖 Using FileSystem Tools with Agent")
    print("=" * 70)
    
    print("""
The agent can now use these file system tools:

1. list_directory() - Explore project structure
2. read_file() - Read source code
3. glob_search() - Find files by pattern
4. grep_search() - Search text in files
5. edit_file() - Modify existing files
6. write_file() - Create new files
7. read_file_with_summary() - Handle large files

Example agent workflow:
-----------------------
User: "Find all TODO comments in the project"

Agent思考流程:
1. Use glob_search("**/*.py") to find all Python files
2. Use grep_search(r"# TODO", file_pattern="**/*.py") to find TODOs
3. Present results to user

User: "Update the config file to enable debug mode"

Agent 사고 과정:
1. Use read_file("config.py") to see current config
2. Use edit_file() to change DEBUG = False to DEBUG = True
3. Confirm the change
""")
    
    print("=" * 70 + "\n")


def main():
    """Run all file system tool demos."""
    print("\n" + "📁" * 35)
    print("   File System Tools Demonstration")
    print("   Based on DeepAgents FileSystemBackend")
    print("📁" * 35 + "\n")
    
    # Run demos
    demo_exploration()
    demo_search()
    demo_modification()
    demo_large_file_handling()
    demo_agent_usage()
    
    print("✨" * 35)
    print("   All Demos Complete!")
    print("   Cleanup: temp/ directory created with demo files")
    print("✨" * 35 + "\n")


if __name__ == "__main__":
    main()