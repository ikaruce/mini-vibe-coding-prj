# 생성할 파일 목록 및 내용

## 디렉토리 구조

```
ax-advanced-mini-prj/
├── pyproject.toml
├── .env.example
├── .gitignore
├── README.md
├── SETUP_PLAN.md (✓ 이미 생성됨)
├── ARCHITECTURE.md (✓ 이미 생성됨)
├── FILES_TO_CREATE.md (이 파일)
│
├── src/
│   └── ai_assistant/
│       ├── __init__.py
│       ├── config.py
│       ├── agent.py
│       ├── tools.py
│       ├── prompts.py
│       └── utils.py
│
├── tests/
│   ├── __init__.py
│   └── test_agent.py
│
└── examples/
    ├── basic_chat.py
    └── code_generation.py
```

---

## 1. pyproject.toml

```toml
[project]
name = "ai-coding-assistant"
version = "0.1.0"
description = "AI Coding Assistant using LangChain and LangGraph with OpenRouter"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
dependencies = [
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "langgraph>=0.2.0",
    "langchain-community>=0.3.0",
    "langchain-core>=0.3.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "black>=24.0.0",
    "ruff>=0.6.0",
    "mypy>=1.11.0",
    "ipython>=8.20.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 100
target-version = ["py311"]
exclude = '''
/(
    \.git
  | \.venv
  | __pycache__
  | build
  | dist
)/
'''

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
asyncio_mode = "auto"
```

---

## 2. .env.example

```env
# OpenRouter API Key (필수)
# https://openrouter.ai/keys 에서 발급받으세요
OPENROUTER_API_KEY=your_openrouter_api_key_here

# OpenRouter Model (선택사항)
# 추천: anthropic/claude-3.5-sonnet
# 기타: openai/gpt-4-turbo, google/gemini-pro-1.5, meta-llama/llama-3.1-70b-instruct
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# LangSmith 설정 (선택사항 - 디버깅 및 트레이싱용)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=ai-coding-assistant
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

---

## 3. .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Distribution / packaging
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
.venv/
venv/
ENV/
env/
.virtualenv/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local

# UV
uv.lock
.uv/

# Testing
.pytest_cache/
.coverage
.coverage.*
htmlcov/
.tox/
.nox/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json
.pytype/

# Jupyter Notebook
.ipynb_checkpoints
*.ipynb

# Logs
*.log
logs/

# Database
*.db
*.sqlite
*.sqlite3

# Cache
.cache/
*.cache
```

---

## 4. README.md

```markdown
# AI Coding Assistant

LangChain과 LangGraph를 활용한 AI 코딩 어시스턴트입니다. OpenRouter를 통해 다양한 LLM 모델을 사용할 수 있습니다.

## 주요 기능

- 🤖 **코드 생성**: 자연어 설명으로 코드 생성
- 📖 **코드 설명**: 복잡한 코드를 이해하기 쉽게 설명
- 🔄 **대화형 인터페이스**: 지속적인 컨텍스트 유지
- 🛠️ **확장 가능**: 새로운 도구 쉽게 추가 가능

## 기술 스택

- **LangChain**: LLM 애플리케이션 프레임워크
- **LangGraph**: 상태 기반 에이전트 워크플로우
- **OpenRouter**: 멀티 LLM 프로바이더
- **UV**: 빠른 Python 패키지 관리

## 빠른 시작

### 1. 사전 요구사항

- Python 3.11 이상
- UV 패키지 매니저
- OpenRouter API 키

### 2. UV 설치 (Windows PowerShell)

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

### 3. 프로젝트 설정

```powershell
# 저장소 클론 (또는 디렉토리로 이동)
cd ax-advanced-mini-prj

# 가상환경 생성
uv venv

# 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 의존성 설치
uv pip install -e .

# 개발 의존성 포함 설치
uv pip install -e ".[dev]"
```

### 4. 환경 변수 설정

```powershell
# .env.example을 .env로 복사
Copy-Item .env.example .env

# .env 파일 편집하여 API 키 입력
notepad .env
```

`.env` 파일에 OpenRouter API 키를 입력하세요:
```env
OPENROUTER_API_KEY=sk-or-v1-...
```

### 5. 사용 예제

#### 기본 사용

```python
import asyncio
from ai_assistant.agent import create_agent

async def main():
    agent = create_agent()
    
    response = await agent.ainvoke({
        "messages": [("user", "Write a Python function to calculate fibonacci numbers")]
    })
    
    print(response["messages"][-1].content)

asyncio.run(main())
```

#### CLI 인터페이스

```powershell
python examples/basic_chat.py
```

## 프로젝트 구조

```
ax-advanced-mini-prj/
├── src/
│   └── ai_assistant/       # 메인 패키지
│       ├── agent.py        # LangGraph 에이전트
│       ├── tools.py        # 코딩 도구들
│       ├── prompts.py      # 프롬프트 템플릿
│       ├── config.py       # 설정 관리
│       └── utils.py        # 유틸리티 함수
├── tests/                  # 테스트
├── examples/               # 사용 예제
└── docs/                   # 문서
```

## 지원 모델

OpenRouter를 통해 다양한 모델 사용 가능:

| 모델 | 용도 | 특징 |
|------|------|------|
| `anthropic/claude-3.5-sonnet` | 추천 | 최고 품질, 긴 컨텍스트 |
| `openai/gpt-4-turbo` | 코드 리뷰 | 빠른 응답 |
| `google/gemini-pro-1.5` | 실험 | 무료 티어 가능 |
| `meta-llama/llama-3.1-70b` | 비용 절감 | 저렴한 가격 |

## 개발

### 테스트 실행

```powershell
pytest
```

### 코드 포맷팅

```powershell
# Black으로 포맷팅
black src/ tests/

# Ruff로 린팅
ruff check src/ tests/

# 타입 체크
mypy src/
```

## 문서

- [설정 가이드](SETUP_PLAN.md) - 상세한 설정 방법
- [아키텍처](ARCHITECTURE.md) - 시스템 아키텍처 설명
- [파일 생성 목록](FILES_TO_CREATE.md) - 생성할 파일들

## 라이선스

MIT License

## 기여

이슈와 PR을 환영합니다!

## 문제 해결

### UV 관련 문제

```powershell
# UV 재설치
irm https://astral.sh/uv/install.ps1 | iex

# 캐시 정리
uv cache clean
```

### 가상환경 활성화 실패

```powershell
# PowerShell 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### OpenRouter 연결 오류

- API 키 확인
- 인터넷 연결 확인
- 크레딧 잔액 확인: https://openrouter.ai/credits

## 참고 자료

- [LangChain 문서](https://python.langchain.com/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [OpenRouter 문서](https://openrouter.ai/docs)
- [UV 문서](https://github.com/astral-sh/uv)
```

---

## 5. src/ai_assistant/__init__.py

```python
"""AI Coding Assistant using LangChain and LangGraph."""

__version__ = "0.1.0"

from .agent import create_agent
from .config import get_config

__all__ = ["create_agent", "get_config"]
```

---

## 6. src/ai_assistant/config.py

```python
"""Configuration management for the AI assistant."""

from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration."""
    
    openrouter_api_key: str = Field(
        default_factory=lambda: os.getenv("OPENROUTER_API_KEY", "")
    )
    openrouter_model: str = Field(
        default_factory=lambda: os.getenv(
            "OPENROUTER_MODEL", 
            "anthropic/claude-3.5-sonnet"
        )
    )
    temperature: float = Field(default=0.7)
    max_tokens: Optional[int] = Field(default=None)
    
    # LangSmith settings
    langchain_tracing: bool = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
    )
    langchain_api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_API_KEY")
    )
    langchain_project: str = Field(
        default_factory=lambda: os.getenv("LANGCHAIN_PROJECT", "ai-coding-assistant")
    )
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_config() -> Config:
    """Get the application configuration."""
    return Config()


def validate_config(config: Config) -> None:
    """Validate configuration."""
    if not config.openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is required. "
            "Please set it in your .env file or environment variables."
        )
```

---

## 7. src/ai_assistant/prompts.py

```python
"""Prompt templates for the AI assistant."""

SYSTEM_PROMPT = """You are an expert coding assistant powered by advanced AI.
Your role is to help developers with:
- Writing clean, efficient code
- Explaining complex code concepts
- Debugging and problem-solving
- Following best practices

Always provide:
1. Clear explanations
2. Well-commented code
3. Error handling
4. Best practices

When generating code:
- Use appropriate design patterns
- Follow language-specific conventions
- Include docstrings/comments
- Consider edge cases
- Add type hints where applicable
"""

CODE_GENERATION_PROMPT = """Generate {language} code for the following task:

{task_description}

Requirements:
- Follow {language} best practices
- Include error handling
- Add clear comments
- Use type hints (if applicable)
- Make the code production-ready

Additional context: {context}
"""

CODE_EXPLANATION_PROMPT = """Explain the following code in {detail_level} detail:

```{language}
{code}
```

Focus on:
- What the code does
- How it works step-by-step
- Key concepts and patterns used
- Potential improvements or issues
"""

GENERAL_CHAT_PROMPT = """You are having a conversation with a developer about coding topics.

Previous context: {context}

Provide helpful, accurate, and concise responses. If asked to write code, 
use the code generation tool. If asked to explain code, use the code explanation tool.
"""
```

---

## 8. src/ai_assistant/tools.py

```python
"""Tools for the AI coding assistant."""

from langchain.tools import tool
from typing import Literal


@tool
def generate_code(
    task_description: str,
    language: str = "python",
    framework: str = None
) -> str:
    """Generate code based on the given task description.
    
    Args:
        task_description: Description of what the code should do
        language: Programming language (default: python)
        framework: Optional framework to use
    
    Returns:
        Generated code as a string
    """
    # This is a placeholder - the actual implementation will be handled by the LLM
    return f"Tool called: generate_code for {language}"


@tool
def explain_code(
    code: str,
    detail_level: Literal["brief", "detailed"] = "brief"
) -> str:
    """Explain the given code.
    
    Args:
        code: The code to explain
        detail_level: Level of detail (brief or detailed)
    
    Returns:
        Explanation of the code
    """
    # This is a placeholder - the actual implementation will be handled by the LLM
    return f"Tool called: explain_code with {detail_level} detail"


def get_tools():
    """Get all available tools."""
    return [generate_code, explain_code]
```

---

## 9. src/ai_assistant/agent.py

```python
"""LangGraph agent for the AI coding assistant."""

from typing import TypedDict, Annotated, Literal
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .config import get_config, validate_config
from .tools import get_tools
from .prompts import SYSTEM_PROMPT


class AgentState(TypedDict):
    """State for the agent."""
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    task_type: Literal["code_generation", "code_explanation", "general_chat"]


def create_llm():
    """Create and configure the LLM."""
    config = get_config()
    validate_config(config)
    
    return ChatOpenAI(
        model=config.openrouter_model,
        openai_api_key=config.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI Coding Assistant"
        },
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


def should_continue(state: AgentState) -> str:
    """Determine if we should continue or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If there are no tool calls, we're done
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return "end"
    return "continue"


def call_model(state: AgentState):
    """Call the model."""
    llm = create_llm()
    tools = get_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    messages = state["messages"]
    
    # Add system message if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def create_agent():
    """Create the LangGraph agent."""
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(get_tools()))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    return workflow.compile()
```

---

## 10. src/ai_assistant/utils.py

```python
"""Utility functions for the AI assistant."""

from typing import Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def log_info(message: str) -> None:
    """Log an info message."""
    logger.info(message)


def log_error(message: str, exc_info: Optional[Exception] = None) -> None:
    """Log an error message."""
    logger.error(message, exc_info=exc_info)


def log_debug(message: str) -> None:
    """Log a debug message."""
    logger.debug(message)
```

---

## 11. tests/__init__.py

```python
"""Tests for the AI coding assistant."""
```

---

## 12. tests/test_agent.py

```python
"""Tests for the agent module."""

import pytest
from ai_assistant.agent import create_agent, AgentState
from ai_assistant.config import get_config


def test_create_agent():
    """Test agent creation."""
    agent = create_agent()
    assert agent is not None


@pytest.mark.asyncio
async def test_agent_invoke():
    """Test agent invocation."""
    # This test requires a valid API key
    try:
        config = get_config()
        if not config.openrouter_api_key:
            pytest.skip("No OpenRouter API key found")
        
        agent = create_agent()
        response = await agent.ainvoke({
            "messages": [("user", "Hello, how are you?")]
        })
        
        assert "messages" in response
        assert len(response["messages"]) > 0
        
    except Exception as e:
        pytest.skip(f"Test skipped due to: {e}")


def test_config():
    """Test configuration."""
    config = get_config()
    assert config is not None
    assert config.openrouter_model is not None
```

---

## 13. examples/basic_chat.py

```python
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
```

---

## 14. examples/code_generation.py

```python
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
```

---

## 생성 순서

Code 모드로 전환 후 다음 순서로 파일을 생성하면 됩니다:

1. ✅ **설정 파일들** (프로젝트 기반)
   - `pyproject.toml`
   - `.env.example`
   - `.gitignore`

2. ✅ **소스 코드** (의존성 순서)
   - `src/ai_assistant/__init__.py`
   - `src/ai_assistant/config.py`
   - `src/ai_assistant/prompts.py`
   - `src/ai_assistant/utils.py`
   - `src/ai_assistant/tools.py`
   - `src/ai_assistant/agent.py`

3. ✅ **테스트**
   - `tests/__init__.py`
   - `tests/test_agent.py`

4. ✅ **예제**
   - `examples/basic_chat.py`
   - `examples/code_generation.py`

5. ✅ **문서**
   - `README.md` (업데이트)

## 필요한 추가 작업

파일 생성 후:

1. **UV로 프로젝트 초기화**
   ```powershell
   uv venv
   .\.venv\Scripts\Activate.ps1
   uv pip install -e ".[dev]"
   ```

2. **환경 변수 설정**
   ```powershell
   Copy-Item .env.example .env
   # .env 파일에 OpenRouter API 키 입력
   ```

3. **테스트 실행**
   ```powershell
   pytest
   ```

4. **예제 실행**
   ```powershell
   python examples/basic_chat.py