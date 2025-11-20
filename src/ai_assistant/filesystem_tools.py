"""File System Tools for Deep Exploration and Manipulation (FR-FS).

This module implements file system operations using patterns similar to
DeepAgents' FilesystemMiddleware and FileSystemBackend.

Based on REQUIREMENT.md 대기능4.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import logging
import re

from langchain.tools import tool

logger = logging.getLogger(__name__)

# Token limit for large file handling (FR-FS-04)
MAX_TOKEN_ESTIMATE = 4000  # ~16000 characters
MAX_FILE_SIZE = 100000  # 100KB


# Implementation functions (can be called directly)

def _list_directory_impl(path: str = ".") -> List[str]:
    """Implementation of list_directory."""
    logger.info(f"Listing directory: {path}")
    
    try:
        target_path = Path(path)
        
        if not target_path.exists():
            return [f"❌ Error: Directory not found: {path}"]
        
        if not target_path.is_dir():
            return [f"❌ Error: Not a directory: {path}"]
        
        items = []
        for item in sorted(target_path.iterdir()):
            if item.is_dir():
                items.append(f"📁 {item.name}/")
            else:
                size_kb = item.stat().st_size / 1024
                items.append(f"📄 {item.name} ({size_kb:.1f} KB)")
        
        logger.info(f"Found {len(items)} items in {path}")
        return items
        
    except Exception as e:
        logger.error(f"Failed to list directory: {e}")
        return [f"❌ Error: {str(e)}"]


def _read_file_impl(file_path: str, max_lines: Optional[int] = None) -> str:
    """Implementation of read_file."""
    logger.info(f"Reading file: {file_path}")
    
    try:
        target_path = Path(file_path)
        
        if not target_path.exists():
            return f"❌ Error: File not found: {file_path}"
        
        if not target_path.is_file():
            return f"❌ Error: Not a file: {file_path}"
        
        # Check file size (FR-FS-04)
        file_size = target_path.stat().st_size
        
        if file_size > MAX_FILE_SIZE:
            logger.warning(f"Large file detected: {file_size} bytes")
            return (
                f"⚠️  File too large: {file_size:,} bytes\n"
                f"Use a SubAgent to summarize, or read specific lines.\n"
                f"File: {file_path}"
            )
        
        # Read content
        content = target_path.read_text(encoding='utf-8')
        
        # Apply line limit if specified
        if max_lines:
            lines = content.split('\n')
            if len(lines) > max_lines:
                content = '\n'.join(lines[:max_lines])
                content += f"\n\n... (truncated, {len(lines) - max_lines} more lines)"
        
        logger.info(f"Read {file_size} bytes from {file_path}")
        return content
        
    except UnicodeDecodeError:
        return f"❌ Error: Binary file or encoding issue: {file_path}"
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        return f"❌ Error: {str(e)}"


def _glob_search_impl(pattern: str, root_dir: str = ".") -> List[str]:
    """Implementation of glob_search."""
    logger.info(f"Glob search: {pattern} in {root_dir}")
    
    try:
        root_path = Path(root_dir)
        
        if not root_path.exists():
            return [f"❌ Error: Directory not found: {root_dir}"]
        
        # Perform glob search
        matches = list(root_path.glob(pattern))
        
        # Convert to relative paths and filter
        result = []
        for match in matches:
            # Skip hidden files and common exclusions
            if any(part.startswith('.') for part in match.parts):
                continue
            if any(excluded in match.parts for excluded in ['__pycache__', 'node_modules', '.venv']):
                continue
            
            result.append(str(match))
        
        logger.info(f"Found {len(result)} matches for pattern: {pattern}")
        return sorted(result)
        
    except Exception as e:
        logger.error(f"Glob search failed: {e}")
        return [f"❌ Error: {str(e)}"]


def _grep_search_impl(
    search_pattern: str,
    file_pattern: str = "**/*.py",
    root_dir: str = ".",
    context_lines: int = 2
) -> List[Dict[str, Any]]:
    """Implementation of grep_search."""
    logger.info(f"Grep search: '{search_pattern}' in {file_pattern}")
    
    try:
        # Find files matching pattern
        root_path = Path(root_dir)
        files = list(root_path.glob(file_pattern))
        
        # Filter out excluded paths
        files = [
            f for f in files
            if not any(part.startswith('.') for part in f.parts)
            and not any(excluded in f.parts for excluded in ['__pycache__', 'node_modules', '.venv'])
        ]
        
        # Compile regex
        try:
            pattern = re.compile(search_pattern, re.MULTILINE)
        except re.error as e:
            return [{"error": f"Invalid regex pattern: {str(e)}"}]
        
        # Search in each file
        matches = []
        for file_path in files:
            try:
                content = file_path.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for i, line in enumerate(lines, start=1):
                    if pattern.search(line):
                        # Get context lines
                        start = max(0, i - context_lines - 1)
                        end = min(len(lines), i + context_lines)
                        context = '\n'.join(lines[start:end])
                        
                        matches.append({
                            "file": str(file_path),
                            "line": i,
                            "text": line.strip(),
                            "context": context
                        })
            
            except (UnicodeDecodeError, PermissionError):
                # Skip binary files or inaccessible files
                continue
        
        logger.info(f"Found {len(matches)} matches")
        return matches
        
    except Exception as e:
        logger.error(f"Grep search failed: {e}")
        return [{"error": str(e)}]


def _edit_file_impl(
    file_path: str,
    search_text: str,
    replace_text: str,
    occurrence: int = -1
) -> str:
    """Implementation of edit_file."""
    logger.info(f"Editing file: {file_path}")
    logger.info(f"Search: {search_text[:50]}...")
    
    try:
        target_path = Path(file_path)
        
        if not target_path.exists():
            return f"❌ Error: File not found: {file_path}"
        
        # Read current content
        content = target_path.read_text(encoding='utf-8')
        
        # Check if search text exists
        if search_text not in content:
            return f"❌ Error: Search text not found in {file_path}"
        
        # Perform replacement
        if occurrence == -1:
            # Replace all occurrences
            new_content = content.replace(search_text, replace_text)
            count = content.count(search_text)
        else:
            # Replace specific occurrence
            parts = content.split(search_text)
            if len(parts) <= occurrence:
                return f"❌ Error: Occurrence {occurrence} not found (only {len(parts) - 1} occurrences)"
            
            new_content = search_text.join(parts[:occurrence]) + replace_text + search_text.join(parts[occurrence:])
            count = 1
        
        # Write back
        target_path.write_text(new_content, encoding='utf-8')
        
        logger.info(f"Replaced {count} occurrence(s) in {file_path}")
        return f"✅ Replaced {count} occurrence(s) in {file_path}"
        
    except Exception as e:
        logger.error(f"Failed to edit file: {e}")
        return f"❌ Error: {str(e)}"


def _write_file_impl(file_path: str, content: str, mode: str = "w") -> str:
    """Implementation of write_file."""
    logger.info(f"Writing to file: {file_path} (mode: {mode})")
    
    try:
        target_path = Path(file_path)
        
        # Create parent directories if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content
        if mode == "w":
            target_path.write_text(content, encoding='utf-8')
            action = "Written"
        elif mode == "a":
            with open(target_path, 'a', encoding='utf-8') as f:
                f.write(content)
            action = "Appended"
        else:
            return f"❌ Error: Invalid mode '{mode}'. Use 'w' or 'a'"
        
        size = len(content.encode('utf-8'))
        logger.info(f"{action} {size} bytes to {file_path}")
        return f"✅ {action} {size} bytes to {file_path}"
        
    except Exception as e:
        logger.error(f"Failed to write file: {e}")
        return f"❌ Error: {str(e)}"


# Tool wrappers (for LangChain agent use)

@tool
def list_directory(path: str = ".") -> List[str]:
    """FR-FS-01: List files and directories."""
    return _list_directory_impl(path)


@tool
def read_file(file_path: str, max_lines: Optional[int] = None) -> str:
    """FR-FS-01: Read file content."""
    return _read_file_impl(file_path, max_lines)


@tool
def glob_search(pattern: str, root_dir: str = ".") -> List[str]:
    """FR-FS-02: Search files matching glob pattern."""
    return _glob_search_impl(pattern, root_dir)


@tool
def grep_search(
    search_pattern: str,
    file_pattern: str = "**/*.py",
    root_dir: str = ".",
    context_lines: int = 2
) -> List[Dict[str, Any]]:
    """FR-FS-02: Search for text pattern in files."""
    return _grep_search_impl(search_pattern, file_pattern, root_dir, context_lines)


@tool
def edit_file(
    file_path: str,
    search_text: str,
    replace_text: str,
    occurrence: int = -1
) -> str:
    """FR-FS-03: Edit file with precise string replacement."""
    return _edit_file_impl(file_path, search_text, replace_text, occurrence)


@tool
def write_file(file_path: str, content: str, mode: str = "w") -> str:
    """FR-FS-03: Write content to file."""
    return _write_file_impl(file_path, content, mode)


# SubAgent for large file handling (FR-FS-04)

class FileSummarizer:
    """FR-FS-04: SubAgent for summarizing large files."""
    
    def __init__(self, llm):
        """Initialize file summarizer."""
        self.llm = llm
    
    def summarize(self, file_path: str, content: str, focus: Optional[str] = None) -> str:
        """Summarize large file content."""
        logger.info(f"Summarizing large file: {file_path}")
        
        truncated_content = content[:20000]  # First 20k chars
        
        prompt = f"""Summarize the following file concisely.

File: {file_path}
Size: {len(content):,} characters

Content (truncated):
```
{truncated_content}
```

{f"Focus on: {focus}" if focus else ""}

Provide a summary (max 300 words) covering:
1. Main purpose and functionality
2. Key functions/classes and their roles
3. Important dependencies and imports
4. Notable patterns or architecture
5. Any critical configuration or constants

Return concise summary:
"""
        
        response = self.llm.invoke(prompt)
        summary = response.content.strip()
        
        logger.info(f"Generated summary ({len(summary)} chars)")
        return summary


@tool
def read_file_with_summary(
    file_path: str,
    max_lines: Optional[int] = None,
    auto_summarize: bool = False
) -> str:
    """FR-FS-04: Read file with automatic summarization for large files."""
    logger.info(f"Reading file with summary support: {file_path}")
    
    try:
        target_path = Path(file_path)
        
        if not target_path.exists():
            return f"❌ Error: File not found: {file_path}"
        
        file_size = target_path.stat().st_size
        
        # Check if file is too large
        if file_size > MAX_FILE_SIZE:
            if auto_summarize:
                # Import here to avoid circular dependency
                from .agent import create_llm
                
                logger.warning(f"Large file: {file_size} bytes - auto-summarizing")
                
                summarizer = FileSummarizer(create_llm())
                content = target_path.read_text(encoding='utf-8')
                summary = summarizer.summarize(file_path, content)
                
                return (
                    f"📋 SUMMARY (Large file: {file_size:,} bytes)\n"
                    f"File: {file_path}\n\n"
                    f"{summary}\n\n"
                    f"💡 Tip: Use grep_search to find specific content"
                )
            else:
                return (
                    f"⚠️  File too large: {file_size:,} bytes\n"
                    f"Use read_file_with_summary(auto_summarize=True) to summarize.\n"
                    f"File: {file_path}"
                )
        
        # Normal file size - read directly
        return _read_file_impl(file_path, max_lines)
        
    except Exception as e:
        logger.error(f"Failed to read file with summary: {e}")
        return f"❌ Error: {str(e)}"


def get_filesystem_tools() -> List:
    """Get all file system tools.
    
    Returns:
        List of LangChain tools for file system operations
    """
    return [
        list_directory,
        read_file,
        read_file_with_summary,
        glob_search,
        grep_search,
        edit_file,
        write_file
    ]