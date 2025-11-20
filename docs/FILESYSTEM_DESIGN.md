# File System Deep Exploration and Manipulation (대기능4)

## FR-FS: File System Requirements

DeepAgents의 FileSystemBackend를 활용한 파일 시스템 작업 구현.

## 요구사항 분석

### FR-FS-01: Contextual Exploration
- **ls**: 디렉토리 구조 파악
- **read_file**: 파일 내용 읽기
- **목적**: 개발 컨텍스트 자율 확보

### FR-FS-02: Pattern-based Search
- **glob**: 패턴 매칭 (예: `**/*.py`)
- **grep**: 문자열 검색
- **목적**: 수정 대상 정확 식별

### FR-FS-03: Precise Code Modification
- **edit_file**: 문자열 치환 (String Replacement)
- **write_file**: 새 파일 생성
- **목적**: 정확한 코드 수정

### FR-FS-04: Large Output Handling
- **파일 저장**: 토큰 제한 초과 시 자동 저장
- **SubAgent**: 대용량 파일 요약 처리
- **HITL**: SubAgent 호출 전 사용자 승인

## 아키텍처

### FileSystemBackend 사용

```python
from langchain.agents.agent_toolkits import FileSystemToolkit

# FileSystemBackend 초기화
toolkit = FileSystemToolkit(
    root_dir=".",  # 실행 경로 기준
    allow_list=["*.py", "*.md", "*.txt"],
    deny_list=["*.env", ".git/*"]
)

# 도구 생성
tools = toolkit.get_tools()
# - list_directory
# - read_file
# - write_file
# - ...
```

### 추가 도구 구현

```python
@tool
def glob_search(pattern: str, root_dir: str = ".") -> List[str]:
    """FR-FS-02: Pattern-based file search."""
    pass

@tool
def grep_search(pattern: str, file_pattern: str = "**/*.py") -> List[dict]:
    """FR-FS-02: String search in files."""
    pass

@tool
def edit_file(file_path: str, search: str, replace: str) -> bool:
    """FR-FS-03: Precise string replacement."""
    pass
```

## 대용량 파일 처리 (FR-FS-04)

### Token Limit Check

```python
MAX_TOKENS = 4000  # Context window 제한

def check_file_size(content: str) -> bool:
    """Check if content exceeds token limit."""
    # Rough estimation: 1 token ≈ 4 chars
    estimated_tokens = len(content) / 4
    return estimated_tokens > MAX_TOKENS
```

### SubAgent for Summarization

```python
class FileSummarizer:
    """SubAgent for summarizing large files."""
    
    def summarize(self, file_path: str, content: str) -> str:
        """Summarize large file content.
        
        Returns:
            Short summary with key points
        """
        prompt = f"""Summarize the following file in 200 words or less.

File: {file_path}

Content:
{content[:10000]}  # First 10k chars

Focus on:
- Main purpose
- Key functions/classes
- Important dependencies
- Notable patterns

Return concise summary:
"""
        # LLM call
        summary = llm.invoke(prompt)
        return summary.content
```

### HITL for SubAgent

```python
def request_summarization_approval(file_path: str, size: int) -> bool:
    """Request user approval for file summarization.
    
    Args:
        file_path: Path to large file
        size: File size in bytes
        
    Returns:
        Whether user approved
    """
    print(f"⚠️  Large file detected: {file_path} ({size:,} bytes)")
    print("This file exceeds token limit.")
    print("\nOptions:")
    print("1. Summarize with SubAgent (recommended)")
    print("2. Skip this file")
    print("3. Try to process anyway (may fail)")
    
    choice = input("\nYour choice (1-3): ")
    
    return choice == "1"
```

## LangGraph Integration

### FileSystem Tools Node

```python
def filesystem_explore_node(state: AgentState) -> dict:
    """FR-FS-01: Explore file system for context."""
    # Use ls to list directories
    # Use read_file to read relevant files
    # Build context from file system
    pass

def filesystem_search_node(state: AgentState) -> dict:
    """FR-FS-02: Search for modification targets."""
    # glob for pattern matching
    # grep for string search
    # Return list of target files
    pass

def filesystem_modify_node(state: AgentState) -> dict:
    """FR-FS-03: Modify files precisely."""
    # edit_file for replacements
    # write_file for new files
    pass
```

## 도구 명세

### 1. list_directory (ls)

```python
@tool
def list_directory(path: str = ".") -> List[str]:
    """List files and directories.
    
    Args:
        path: Directory path
        
    Returns:
        List of file/directory names
    """
```

### 2. read_file

```python
@tool
def read_file(file_path: str, max_size: int = 100000) -> str:
    """Read file content.
    
    Args:
        file_path: Path to file
        max_size: Maximum file size (bytes)
        
    Returns:
        File content (or summary if too large)
    """
```

### 3. glob_search

```python
@tool
def glob_search(pattern: str, root_dir: str = ".") -> List[str]:
    """Search files matching pattern.
    
    Args:
        pattern: Glob pattern (e.g., '**/*.py')
        root_dir: Root directory
        
    Returns:
        List of matching file paths
    """
```

### 4. grep_search

```python
@tool
def grep_search(
    search_pattern: str,
    file_pattern: str = "**/*.py",
    context_lines: int = 2
) -> List[dict]:
    """Search string in files.
    
    Args:
        search_pattern: Regex pattern to search
        file_pattern: File pattern to search in
        context_lines: Lines of context
        
    Returns:
        List of matches with context
    """
```

### 5. edit_file

```python
@tool
def edit_file(
    file_path: str,
    search_text: str,
    replace_text: str,
    occurrence: int = -1
) -> bool:
    """Replace text in file.
    
    Args:
        file_path: File to edit
        search_text: Text to find
        replace_text: Replacement text
        occurrence: Which occurrence (-1 for all)
        
    Returns:
        Success status
    """
```

### 6. write_file

```python
@tool
def write_file(file_path: str, content: str, mode: str = "w") -> bool:
    """Write content to file.
    
    Args:
        file_path: Target file path
        content: Content to write
        mode: Write mode ('w', 'a')
        
    Returns:
        Success status
    """
```

## 워크플로우

```
User Request
    ↓
Explore FileSystem (FR-FS-01)
    ↓
Search for Targets (FR-FS-02)
    ↓
┌──────────┴──────────┐
↓                     ↓
Large File?        Normal File
↓                     ↓
HITL Request      Modify Directly
↓                     ↓
SubAgent Summary  edit_file/write_file
└──────────┬──────────┘
           ↓
      Return Results
```

## 구현 순서

1. ✅ 설계 문서 작성
2. FileSystem Tools 구현
3. SubAgent for Summarization
4. HITL 메커니즘
5. LangGraph 통합
6. 예제 작성
7. 테스트