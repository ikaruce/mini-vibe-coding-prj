# AI Coding Assistant Setup Plan

## 환경 정보
- **OS**: Windows 11
- **Shell**: PowerShell
- **Python 관리**: UV
- **LLM Provider**: OpenRouter
- **프레임워크**: LangChain + LangGraph

## 1. pyproject.toml 구조

```toml
[project]
name = "ai-coding-assistant"
version = "0.1.0"
description = "AI Coding Assistant using LangChain and LangGraph with OpenRouter"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "langgraph>=0.2.0",
    "langchain-community>=0.3.0",
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

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
```

## 2. 환경 변수 (.env.example)

```env
# OpenRouter API Key (필수)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# OpenRouter Model (선택사항, 기본값: anthropic/claude-3.5-sonnet)
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet

# LangSmith (선택사항 - 디버깅용)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=ai-coding-assistant
```

## 3. 프로젝트 디렉토리 구조

```
ax-advanced-mini-prj/
├── pyproject.toml          # UV 프로젝트 설정
├── .env                     # 환경 변수 (Git 제외)
├── .env.example            # 환경 변수 템플릿
├── .gitignore              # Git 무시 파일
├── README.md               # 프로젝트 문서
├── SETUP_PLAN.md           # 이 파일
│
├── src/
│   └── ai_assistant/       # 메인 패키지
│       ├── __init__.py
│       ├── agent.py        # LangGraph 에이전트
│       ├── tools.py        # 코딩 도구들
│       ├── prompts.py      # 프롬프트 템플릿
│       ├── config.py       # 설정 관리
│       └── utils.py        # 유틸리티
│
├── tests/
│   ├── __init__.py
│   └── test_agent.py
│
└── examples/
    ├── basic_chat.py       # 기본 대화 예제
    └── code_generation.py  # 코드 생성 예제
```

## 4. OpenRouter 연동 설정

### LangChain에서 OpenRouter 사용하기

```python
from langchain_openai import ChatOpenAI
import os

# OpenRouter를 LangChain에서 사용
llm = ChatOpenAI(
    model=os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet"),
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    openai_api_base="https://openrouter.ai/api/v1",
    default_headers={
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "AI Coding Assistant"
    }
)
```

### 사용 가능한 OpenRouter 모델
- `anthropic/claude-3.5-sonnet` (추천)
- `anthropic/claude-3-opus`
- `openai/gpt-4-turbo`
- `google/gemini-pro-1.5`
- `meta-llama/llama-3.1-70b-instruct`

## 5. UV 설치 및 사용 (Windows PowerShell)

### UV 설치
```powershell
# Windows에서 UV 설치
irm https://astral.sh/uv/install.ps1 | iex
```

### 프로젝트 초기화
```powershell
# 가상환경 생성 및 의존성 설치
uv venv
.\.venv\Scripts\Activate.ps1

# 프로젝트 의존성 설치
uv pip install -e .
```

### 개발 의존성 포함 설치
```powershell
uv pip install -e ".[dev]"
```

### 패키지 추가
```powershell
uv pip install langchain langgraph langchain-openai
```

## 6. LangGraph 에이전트 아키텍처

### 기본 워크플로우
```
사용자 입력
    ↓
에이전트 판단
    ↓
┌───────────┬───────────┬───────────┐
│ 코드 생성 │ 코드 설명 │ 질문 응답 │
└───────────┴───────────┴───────────┘
    ↓
결과 생성
    ↓
사용자에게 반환
```

### 상태 정의
```python
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    context: str
    current_task: str
```

### 기본 노드
1. **agent_node**: LLM으로 사용자 의도 파악
2. **code_generator_node**: 코드 생성
3. **code_explainer_node**: 코드 설명
4. **response_node**: 최종 응답 생성

## 7. 필요한 추가 파일

### .gitignore
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
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
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
.venv/
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment
.env

# UV
uv.lock

# Test & Coverage
.pytest_cache/
.coverage
htmlcov/

# Type checking
.mypy_cache/
.dmypy.json
dmypy.json

# Jupyter
.ipynb_checkpoints/
```

## 8. 개발 워크플로우

### 1단계: 환경 설정
```powershell
# 1. UV 설치 확인
uv --version

# 2. 가상환경 생성
uv venv

# 3. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 4. 의존성 설치
uv pip install -e ".[dev]"
```

### 2단계: 환경 변수 설정
```powershell
# .env.example을 .env로 복사
Copy-Item .env.example .env

# .env 파일을 열어 API 키 입력
notepad .env
```

### 3단계: 개발 시작
```powershell
# Python 인터프리터 실행
python

# 또는 IPython 실행
ipython
```

### 4단계: 테스트
```powershell
# 테스트 실행
pytest

# 커버리지와 함께 실행
pytest --cov=src/ai_assistant
```

### 5단계: 코드 포맷팅
```powershell
# Black으로 포맷팅
black src/ tests/

# Ruff로 린팅
ruff check src/ tests/

# 타입 체크
mypy src/
```

## 9. 추가로 필요한 것들

### 필수 준비물
1. ✅ OpenRouter API 키
2. ✅ Python 3.11 이상 설치
3. ✅ UV 패키지 매니저 설치
4. ✅ Git 설치 (버전 관리용)

### 선택 사항
1. LangSmith 계정 (디버깅 및 트레이싱용)
2. VSCode 또는 PyCharm (IDE)
3. Windows Terminal (더 나은 터미널 경험)

## 10. 다음 단계

이 계획이 완료되면:
1. **Code 모드**로 전환하여 실제 파일 생성
2. 기본 에이전트 구현
3. 예제 코드 작성
4. 테스트 작성

## 11. OpenRouter 사용 시 주의사항

### 비용 관리
- OpenRouter는 pay-per-use 모델
- 각 모델마다 다른 가격 정책
- 크레딧 잔액 확인: https://openrouter.ai/credits

### Rate Limiting
- 무료 티어: 제한적
- 유료 티어: 모델별로 다름
- 에러 처리 필요

### 추천 모델 (가격 대비 성능)
1. `anthropic/claude-3.5-sonnet` - 최고 품질
2. `google/gemini-pro-1.5` - 무료 티어 가능
3. `meta-llama/llama-3.1-70b-instruct` - 저렴

## 12. 문제 해결

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
- 크레딧 잔액 확인