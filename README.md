# AI Coding Assistant

LangChain과 LangGraph를 활용한 AI 코딩 어시스턴트입니다. OpenRouter를 통해 다양한 LLM 모델을 사용할 수 있습니다.

## 주요 기능

- 🤖 **코드 생성**: 자연어 설명으로 코드 생성
- 📖 **코드 설명**: 복잡한 코드를 이해하기 쉽게 설명
- 🔄 **대화형 인터페이스**: 지속적인 컨텍스트 유지
- 🛠️ **확장 가능**: 새로운 도구 쉽게 추가 가능
- ⚡ **SPEED/PRECISION 모드**: LangGraph 기반 이중 분석 모드
  - **SPEED 모드**: Tree-sitter + NetworkX로 빠른 영향도 분석 (10k 라인 <5초)
  - **PRECISION 모드**: LSP 기반 컴파일러 수준 정확도
  - **자동 Fallback**: PRECISION 실패 시 SPEED로 자동 전환

## 기술 스택

- **LangChain**: LLM 애플리케이션 프레임워크
- **LangGraph**: 상태 기반 에이전트 워크플로우 및 조건부 분기
- **OpenRouter**: 멀티 LLM 프로바이더
- **UV**: 빠른 Python 패키지 관리
- **Tree-sitter**: 빠른 AST 파싱
- **NetworkX**: 의존성 그래프 분석
- **LSP (pygls)**: 정밀 코드 분석

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

#### SPEED/PRECISION 모드 사용

```python
import asyncio
from ai_assistant.agent import create_agent

async def main():
    agent = create_agent()
    
    # SPEED 모드: 빠른 분석
    speed_result = await agent.ainvoke({
        "messages": [("user", "Analyze impact of config.py changes")],
        "mode": "SPEED",
        "changed_file": "src/ai_assistant/config.py",
        "impacted_files": [],
        "retry_count": 0,
        "error_logs": []
    })
    
    # PRECISION 모드: 정밀 분석 (자동 fallback)
    precision_result = await agent.ainvoke({
        "messages": [("user", "Precisely analyze agent.py changes")],
        "mode": "PRECISION",
        "changed_file": "src/ai_assistant/agent.py",
        "impacted_files": [],
        "retry_count": 0,
        "error_logs": []
    })

asyncio.run(main())
```

#### 모드 분기 데모

```powershell
python examples/mode_branching_demo.py
```

## 프로젝트 구조

```
ax-advanced-mini-prj/
├── src/
│   └── ai_assistant/       # 메인 패키지
│       ├── agent.py        # LangGraph 에이전트 (모드 분기)
│       ├── analyzers.py    # SPEED/PRECISION 분석기
│       ├── tools.py        # 코딩 도구들
│       ├── prompts.py      # 프롬프트 템플릿
│       ├── config.py       # 설정 관리
│       └── utils.py        # 유틸리티 함수
├── tests/                  # 테스트
├── examples/               # 사용 예제
│   ├── basic_chat.py       # 기본 대화
│   ├── code_generation.py  # 코드 생성
│   └── mode_branching_demo.py  # 모드 분기 데모
└── docs/                   # 문서
```

## SPEED vs PRECISION 모드

### 🚀 SPEED 모드
- **방법**: Tree-sitter AST 파싱 + NetworkX 그래프 분석
- **성능**: 10,000 라인 < 5초
- **장점**: 빌드 불필요, 빠른 실행
- **용도**: 빠른 영향도 파악, 초기 분석

### 🎯 PRECISION 모드
- **방법**: LSP (Language Server Protocol) - Pyright
- **정확도**: 컴파일러 수준
- **장점**: 100% 정확한 참조 찾기
- **용도**: 정밀한 리팩토링, 프로덕션 배포 전

### ⚙️ 자동 Fallback
PRECISION 모드 실패 시 (빌드 에러, LSP 연결 실패 등) 자동으로 SPEED 모드로 전환됩니다.
```python
# PRECISION 시도 → 실패 → SPEED로 자동 전환
result = await agent.ainvoke({
    "mode": "PRECISION",  # 시작은 PRECISION
    # ... 에러 발생 시 자동으로 SPEED 모드 실행
})
# result["analysis_result"]["mode"]로 실제 사용된 모드 확인 가능
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

##📊 LangSmith로 LangGraph 추적하기

LangSmith를 사용하면 LangGraph 실행을 실시간으로 추적하고 디버깅할 수 있습니다.

### 빠른 설정

1. **LangSmith 계정 생성**: https://smith.langchain.com
2. **API 키 발급** 및 `.env` 파일에 추가:
```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxxxxxxxxxxx
```
3. **실행 및 확인**:
```powershell
python examples/mode_branching_demo.py
# 콘솔에 "✅ LangSmith tracing enabled" 표시됨
```

### 추적 가능한 내용

- 🔀 **모드 분기**: SPEED vs PRECISION 선택 과정
- 🔄 **Fallback**: PRECISION → SPEED 자동 전환
- 📈 **성능**: 각 노드 실행 시간
- 🐛 **에러**: 실패 지점 및 원인
- 📊 **상태 변화**: 각 단계별 state 변화

자세한 내용은 [LangSmith 가이드](docs/LANGSMITH_GUIDE.md)를 참조하세요.

## 문서

- [설정 가이드](SETUP_PLAN.md) - 상세한 설정 방법
- [아키텍처](ARCHITECTURE.md) - 시스템 아키텍처 설명
- [LangSmith 가이드](docs/LANGSMITH_GUIDE.md) - LangGraph 추적 및 디버깅
- [파일 생성 목록](FILES_TO_CREATE.md) - 생성할 파일들
- [실행 계획](EXECUTION_PLAN.md) - 실행 단계별 가이드

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