# AI Coding Assistant - Architecture Design

## 1. 시스템 아키텍처

### 전체 구조도

```
┌─────────────┐
│   사용자    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│     LangGraph Agent (Orchestrator)  │
│  ┌─────────────────────────────┐   │
│  │   State Management          │   │
│  │   - messages                │   │
│  │   - context                 │   │
│  │   - task_type               │   │
│  └─────────────────────────────┘   │
└──────┬──────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│           Node Routing               │
│  ┌────────┬────────┬──────────────┐ │
│  │ Agent  │ Tools  │   Response   │ │
│  │  Node  │  Node  │     Node     │ │
│  └────────┴────────┴──────────────┘ │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│        Tools Layer                   │
│  ┌────────────────────────────────┐ │
│  │ - Code Generator               │ │
│  │ - Code Explainer               │ │
│  │ - Code Reviewer (future)       │ │
│  │ - File Manager (future)        │ │
│  └────────────────────────────────┘ │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│         LLM Provider                 │
│       (OpenRouter)                   │
│  - Claude 3.5 Sonnet                │
│  - GPT-4 Turbo                      │
│  - Gemini Pro 1.5                   │
└──────────────────────────────────────┘
```

## 2. LangGraph 상태 머신

### 상태 정의

```python
from typing import TypedDict, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """에이전트의 상태를 정의"""
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    task_type: Literal["code_generation", "code_explanation", "general_chat"]
    iteration: int
```

### 노드 구성

```
     START
       │
       ▼
   ┌────────┐
   │ Agent  │◄─────┐
   │  Node  │      │
   └───┬────┘      │
       │           │
  ┌────┴────┐      │
  │ Should  │      │
  │Continue?│      │
  └────┬────┘      │
       │           │
   YES │           │
       ▼           │
   ┌────────┐      │
   │ Tools  │──────┘
   │  Node  │
   └────────┘
       │
    NO │
       ▼
      END
```

### 워크플로우 상세

1. **Agent Node**
   - 사용자 메시지 분석
   - 작업 유형 결정 (코드 생성, 설명, 일반 대화)
   - 필요한 도구 선택

2. **Tools Node**
   - 선택된 도구 실행
   - 결과를 상태에 추가
   - Agent Node로 복귀

3. **Conditional Edge**
   - Agent 응답에 도구 호출이 있으면 Tools Node로
   - 없으면 종료

## 3. 도구 (Tools) 설계

### 기본 도구

#### 1. Code Generator
```python
@tool
def generate_code(
    task_description: str,
    language: str = "python",
    framework: str = None
) -> str:
    """
    주어진 설명에 따라 코드를 생성합니다.
    
    Args:
        task_description: 생성할 코드에 대한 설명
        language: 프로그래밍 언어
        framework: 사용할 프레임워크 (선택사항)
    
    Returns:
        생성된 코드
    """
```

#### 2. Code Explainer
```python
@tool
def explain_code(
    code: str,
    detail_level: Literal["brief", "detailed"] = "brief"
) -> str:
    """
    코드를 분석하고 설명합니다.
    
    Args:
        code: 설명할 코드
        detail_level: 설명 수준
    
    Returns:
        코드 설명
    """
```

### 향후 추가 예정 도구

#### 3. Code Reviewer
- 코드 품질 분석
- 베스트 프랙티스 확인
- 보안 취약점 검사

#### 4. File Manager
- 파일 읽기/쓰기
- 디렉토리 탐색
- 파일 검색

## 4. 프롬프트 전략

### System Prompt

```
You are an expert coding assistant powered by advanced AI.
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
```

### Task-Specific Prompts

**코드 생성:**
```
Generate {language} code for the following task:
{task_description}

Requirements:
- Follow {language} best practices
- Include error handling
- Add clear comments
- Use type hints (if applicable)
```

**코드 설명:**
```
Explain the following code in {detail_level} detail:

{code}

Focus on:
- What the code does
- How it works
- Key concepts used
- Potential improvements
```

## 5. OpenRouter 통합

### 클라이언트 설정

```python
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import os

load_dotenv()

def get_llm(model: str = None):
    """OpenRouter LLM 인스턴스 생성"""
    return ChatOpenAI(
        model=model or os.getenv(
            "OPENROUTER_MODEL", 
            "anthropic/claude-3.5-sonnet"
        ),
        openai_api_key=os.getenv("OPENROUTER_API_KEY"),
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI Coding Assistant"
        },
        temperature=0.7,
    )
```

### 추천 모델별 사용 시나리오

| 모델 | 용도 | 장점 |
|------|------|------|
| `anthropic/claude-3.5-sonnet` | 기본, 코드 생성 | 최고 품질, 긴 컨텍스트 |
| `google/gemini-pro-1.5` | 실험, 학습 | 무료 티어 가능 |
| `openai/gpt-4-turbo` | 코드 리뷰, 설명 | 빠른 응답 |
| `meta-llama/llama-3.1-70b` | 비용 절감 | 저렴한 가격 |

## 6. 에러 처리 및 재시도 전략

### 에러 타입

1. **API 에러**
   - Rate limiting
   - Authentication 실패
   - 네트워크 오류

2. **도구 실행 에러**
   - 잘못된 파라미터
   - 실행 실패

3. **상태 관리 에러**
   - 컨텍스트 초과
   - 메모리 부족

### 재시도 로직

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def call_llm_with_retry(llm, messages):
    """LLM 호출 시 자동 재시도"""
    return llm.invoke(messages)
```

## 7. 성능 최적화

### 캐싱 전략

```python
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

# LLM 응답 캐싱
set_llm_cache(InMemoryCache())
```

### 스트리밍 응답

```python
async def stream_agent_response(user_input: str):
    """스트리밍 방식으로 응답 생성"""
    async for event in agent.astream(
        {"messages": [("user", user_input)]}
    ):
        yield event
```

## 8. 로깅 및 모니터링

### LangSmith 통합 (선택사항)

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"
os.environ["LANGCHAIN_PROJECT"] = "ai-coding-assistant"
```

### 로컬 로깅

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
```

## 9. 확장성 고려사항

### 모듈 추가 방법

1. 새 도구 추가: `src/ai_assistant/tools.py`에 `@tool` 데코레이터 사용
2. 새 노드 추가: `src/ai_assistant/agent.py`의 그래프에 노드 추가
3. 프롬프트 수정: `src/ai_assistant/prompts.py` 업데이트

### 플러그인 아키텍처 (향후)

```python
class ToolPlugin:
    """도구 플러그인 인터페이스"""
    def get_tools(self) -> list:
        """플러그인이 제공하는 도구 목록 반환"""
        pass
```

## 10. 보안 고려사항

### API 키 관리
- `.env` 파일에만 저장
- Git에 절대 커밋하지 않음
- 환경 변수로만 접근

### 코드 실행 제한
- 사용자가 생성된 코드를 명시적으로 실행
- 자동 실행 금지
- 샌드박스 환경 고려 (향후)

### Rate Limiting
```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=10, period=60)  # 분당 10회
def call_openrouter_api():
    """API 호출 제한"""
    pass
```

## 11. 테스트 전략

### 단위 테스트
```python
def test_code_generator():
    """코드 생성 도구 테스트"""
    result = generate_code(
        task_description="Create a function to add two numbers",
        language="python"
    )
    assert "def" in result
    assert "add" in result.lower()
```

### 통합 테스트
```python
async def test_agent_workflow():
    """전체 에이전트 워크플로우 테스트"""
    response = await agent.ainvoke({
        "messages": [("user", "Write a Python function to calculate factorial")]
    })
    assert len(response["messages"]) > 0
```

## 12. 배포 고려사항

### CLI 인터페이스
```python
# examples/cli.py
import asyncio
from ai_assistant.agent import create_agent

async def main():
    agent = create_agent()
    print("AI Coding Assistant (type 'exit' to quit)")
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() == 'exit':
            break
            
        response = await agent.ainvoke({
            "messages": [("user", user_input)]
        })
        print(f"\nAssistant: {response['messages'][-1].content}")

if __name__ == "__main__":
    asyncio.run(main())
```

### API 서버 (향후)
- FastAPI 사용
- RESTful API 제공
- WebSocket 스트리밍

## 13. 문서화 계획

### 코드 문서화
- 모든 함수에 docstring
- 타입 힌트 사용
- 복잡한 로직에 주석

### 사용자 문서
- README.md: 빠른 시작 가이드
- SETUP_PLAN.md: 상세 설정 가이드
- ARCHITECTURE.md: 아키텍처 설명 (이 문서)
- API 문서 (향후)

## 14. 다음 단계

설계가 완료되면 Code 모드로 전환하여:

1. ✅ `pyproject.toml` 생성
2. ✅ `.env.example` 생성
3. ✅ `.gitignore` 생성
4. ✅ 디렉토리 구조 생성
5. ✅ 기본 코드 파일 생성
   - `src/ai_assistant/__init__.py`
   - `src/ai_assistant/config.py`
   - `src/ai_assistant/agent.py`
   - `src/ai_assistant/tools.py`
   - `src/ai_assistant/prompts.py`
6. ✅ 예제 파일 생성
7. ✅ 테스트 파일 생성
8. ✅ README.md 업데이트