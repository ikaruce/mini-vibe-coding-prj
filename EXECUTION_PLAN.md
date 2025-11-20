# AI Coding Assistant - 실행 계획

## 📋 프로젝트 개요

**목표**: LangChain과 LangGraph를 사용한 AI 코딩 어시스턴트 개발

**환경**:
- OS: Windows 11
- Shell: PowerShell
- Python 관리: UV
- LLM Provider: OpenRouter

## ✅ 완료된 설계 작업

1. ✅ **프로젝트 요구사항 분석** ([`SETUP_PLAN.md`](SETUP_PLAN.md))
   - UV 기반 프로젝트 구조 설계
   - OpenRouter 통합 방안
   - Windows PowerShell 환경 고려

2. ✅ **아키텍처 설계** ([`ARCHITECTURE.md`](ARCHITECTURE.md))
   - LangGraph 상태 머신 설계
   - 도구(Tools) 아키텍처
   - 에러 처리 및 최적화 전략

3. ✅ **파일 구조 및 내용 정의** ([`FILES_TO_CREATE.md`](FILES_TO_CREATE.md))
   - 14개 파일의 상세 내용
   - 파일 생성 순서
   - 의존성 관계

## 📁 생성할 파일 목록

### 설정 파일 (3개)
- ✅ `pyproject.toml` - UV 프로젝트 설정
- ✅ `.env.example` - 환경 변수 템플릿
- ✅ `.gitignore` - Git 무시 파일

### 소스 코드 (6개)
- ✅ `src/ai_assistant/__init__.py`
- ✅ `src/ai_assistant/config.py` - 설정 관리
- ✅ `src/ai_assistant/prompts.py` - 프롬프트 템플릿
- ✅ `src/ai_assistant/utils.py` - 유틸리티
- ✅ `src/ai_assistant/tools.py` - 코딩 도구
- ✅ `src/ai_assistant/agent.py` - LangGraph 에이전트

### 테스트 (2개)
- ✅ `tests/__init__.py`
- ✅ `tests/test_agent.py`

### 예제 (2개)
- ✅ `examples/basic_chat.py` - 기본 대화
- ✅ `examples/code_generation.py` - 코드 생성

### 문서 (1개)
- ✅ `README.md` - 업데이트된 프로젝트 문서

**총 14개 파일**

## 🚀 실행 단계

### Phase 1: Code 모드로 전환하여 파일 생성

```
1. pyproject.toml 생성
2. .env.example 생성
3. .gitignore 생성
4. 소스 코드 파일들 생성 (의존성 순서대로)
5. 테스트 파일 생성
6. 예제 파일 생성
7. README.md 업데이트
```

### Phase 2: 프로젝트 초기화 (사용자가 수행)

```powershell
# 1. UV 설치 확인
uv --version

# 2. 가상환경 생성
uv venv

# 3. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 4. 의존성 설치
uv pip install -e ".[dev]"

# 5. 환경 변수 설정
Copy-Item .env.example .env
notepad .env  # OpenRouter API 키 입력
```

### Phase 3: 검증 및 테스트

```powershell
# 1. 테스트 실행
pytest

# 2. 코드 포맷팅 확인
black --check src/ tests/
ruff check src/ tests/

# 3. 타입 체크
mypy src/

# 4. 예제 실행
python examples/basic_chat.py
```

## 📦 주요 의존성

### 핵심 라이브러리
```
langchain >= 0.3.0
langchain-openai >= 0.2.0
langgraph >= 0.2.0
langchain-community >= 0.3.0
python-dotenv >= 1.0.0
```

### 개발 도구
```
pytest >= 8.0.0
black >= 24.0.0
ruff >= 0.6.0
mypy >= 1.11.0
```

## 🔑 필수 준비물

1. ✅ **OpenRouter API 키**
   - 사이트: https://openrouter.ai/keys
   - 무료 크레딧으로 시작 가능
   - 추천 모델: `anthropic/claude-3.5-sonnet`

2. ✅ **Python 3.11 이상**
   ```powershell
   python --version
   ```

3. ✅ **UV 패키지 매니저**
   ```powershell
   irm https://astral.sh/uv/install.ps1 | iex
   ```

4. ⬜ **Git** (선택사항, 버전 관리용)

## 🎯 프로젝트 구조

```
ax-advanced-mini-prj/
│
├── 📄 설정 파일
│   ├── pyproject.toml       # UV 프로젝트 설정
│   ├── .env.example         # 환경 변수 템플릿
│   └── .gitignore           # Git 무시 파일
│
├── 📚 문서
│   ├── README.md            # 프로젝트 README
│   ├── SETUP_PLAN.md        # 설정 가이드
│   ├── ARCHITECTURE.md      # 아키텍처 문서
│   ├── FILES_TO_CREATE.md   # 파일 생성 목록
│   └── EXECUTION_PLAN.md    # 이 파일
│
├── 💻 소스 코드
│   └── src/ai_assistant/
│       ├── __init__.py      # 패키지 초기화
│       ├── config.py        # 설정 관리
│       ├── prompts.py       # 프롬프트 템플릿
│       ├── utils.py         # 유틸리티
│       ├── tools.py         # 코딩 도구
│       └── agent.py         # LangGraph 에이전트
│
├── 🧪 테스트
│   ├── __init__.py
│   └── test_agent.py        # 에이전트 테스트
│
└── 📖 예제
    ├── basic_chat.py        # 기본 대화 예제
    └── code_generation.py   # 코드 생성 예제
```

## 💡 핵심 기능

### 1. 코드 생성
```python
response = await agent.ainvoke({
    "messages": [("user", "Write a Python function to sort a list")]
})
```

### 2. 코드 설명
```python
response = await agent.ainvoke({
    "messages": [("user", "Explain this code: def factorial(n): return 1 if n == 0 else n * factorial(n-1)")]
})
```

### 3. 대화형 상호작용
```python
# CLI를 통한 지속적인 대화
python examples/basic_chat.py
```

## 🔄 LangGraph 워크플로우

```
사용자 입력
    ↓
┌─────────────────┐
│  Agent Node     │ ← LLM이 의도 파악 및 도구 선택
└────────┬────────┘
         │
    도구 필요? ──No──→ 종료
         │
        Yes
         ↓
┌─────────────────┐
│  Tools Node     │ ← 도구 실행 (코드 생성, 설명 등)
└────────┬────────┘
         │
         └─────────→ Agent Node로 복귀
```

## 🛠️ 확장 계획

### 향후 추가 가능한 기능
1. **파일 시스템 접근**
   - 파일 읽기/쓰기
   - 디렉토리 탐색

2. **코드 리뷰**
   - 정적 분석
   - 베스트 프랙티스 확인

3. **디버깅 지원**
   - 에러 분석
   - 해결책 제시

4. **다양한 언어 지원**
   - Python, JavaScript, TypeScript
   - Java, C++, Go 등

## 📊 예상 비용 (OpenRouter)

| 모델 | 1M 입력 토큰 | 1M 출력 토큰 | 추천 용도 |
|------|-------------|-------------|---------|
| Claude 3.5 Sonnet | $3.00 | $15.00 | 프로덕션 |
| GPT-4 Turbo | $10.00 | $30.00 | 고품질 작업 |
| Gemini Pro 1.5 | 무료 | 무료 | 실험/학습 |
| Llama 3.1 70B | $0.35 | $0.40 | 비용 절감 |

*참고: 가격은 변동될 수 있으며, OpenRouter 공식 사이트에서 확인하세요.*

## ⚠️ 주의사항

1. **API 키 보안**
   - `.env` 파일은 절대 Git에 커밋하지 마세요
   - `.gitignore`에 `.env`가 포함되어 있는지 확인

2. **비용 관리**
   - OpenRouter 크레딧 잔액 정기적으로 확인
   - 사용량 제한 설정 권장

3. **PowerShell 실행 정책**
   ```powershell
   # 가상환경 활성화 시 오류 발생 시
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## 🎉 완료 후 다음 단계

1. ✅ **기본 사용**
   ```powershell
   python examples/basic_chat.py
   ```

2. ✅ **코드 생성 테스트**
   ```powershell
   python examples/code_generation.py
   ```

3. ✅ **커스터마이징**
   - `src/ai_assistant/prompts.py` 수정
   - `src/ai_assistant/tools.py`에 새 도구 추가
   - `src/ai_assistant/agent.py`에 새 노드 추가

## 📝 다음 작업

현재 **Architect 모드**에서 모든 설계를 완료했습니다.

**이제 Code 모드로 전환하여 실제 파일들을 생성할 준비가 되었습니다!**

승인하시면:
1. Code 모드로 전환
2. 14개 파일 생성
3. 생성된 파일 검증
4. 다음 단계 안내

---

## 질문 & 답변

**Q: pyproject.toml만 있으면 되나요?**
A: pyproject.toml은 기본이지만, 완전한 프로젝트를 위해서는 소스 코드, 설정 파일, 예제 등이 모두 필요합니다.

**Q: 추가로 필요한 것은?**
A: 
- ✅ OpenRouter API 키 (필수)
- ✅ Python 3.11+ (필수)
- ✅ UV 패키지 매니저 (필수)
- ⬜ LangSmith 계정 (선택사항 - 디버깅용)

**Q: Windows에서 잘 작동하나요?**
A: 네! 모든 설정과 명령어가 Windows PowerShell 환경에 최적화되어 있습니다.

**Q: 비용이 얼마나 드나요?**
A: OpenRouter는 사용한 만큼 지불하는 방식입니다. Gemini Pro 1.5는 무료 티어가 있어 테스트에 적합합니다.