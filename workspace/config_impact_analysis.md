# Config.py 의존성 분석 리포트

## 📍 파일 위치
**경로**: `src/ai_assistant/config.py`

## 📋 파일 역할
이 파일은 AI Coding Assistant의 **중앙 설정 관리** 모듈입니다.

### 주요 기능
1. **API 설정 관리**
   - OpenRouter API 키 및 모델 설정
   - LangSmith 추적(tracing) 설정

2. **환경 변수 로딩**
   - `.env` 파일에서 설정 자동 로드
   - Pydantic 기반 타입 안전성 보장

3. **설정 검증**
   - API 키 유효성 검증
   - LangSmith 설정 검증

### 현재 Config 클래스 구조
```python
class Config(BaseModel):
    # OpenRouter 설정
    openrouter_api_key: str
    openrouter_model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    
    # LangSmith 설정
    langchain_tracing: bool
    langchain_api_key: Optional[str]
    langchain_project: str
```

---

## 🔗 직접 의존 파일 (Direct Dependencies)

### 1. **src/ai_assistant/__init__.py** ⭐ 높은 영향도
**의존 관계**: 
```python
from .config import get_config
```

**영향**:
- 패키지의 public API로 `get_config`를 export
- 새로운 설정 함수를 추가하면 여기서도 export 필요

**수정 필요성**: 
- ✅ 새 설정 함수 추가 시 `__all__` 리스트 업데이트 필요

---

### 2. **src/ai_assistant/agent.py** ⭐⭐⭐ 매우 높은 영향도
**의존 관계**:
```python
from .config import get_config, validate_config, setup_langsmith_tracing
```

**사용 위치**:
- `create_llm()` 함수: LLM 인스턴스 생성 시 설정 사용
- `create_agent()`: 에이전트 생성 시 설정 검증 및 추적 설정
- `create_self_healing_agent()`: Self-healing 에이전트 생성 시
- `create_simple_agent()`: 간단한 에이전트 생성 시

**영향**:
- Config에 새로운 LLM 관련 설정 추가 시 `create_llm()` 수정 필요
- 새로운 앱별 설정 추가 시 각 `create_*_agent()` 함수에서 설정 사용 가능

**수정 필요성**:
- ⚠️ 새 앱 설정 추가 시: 해당 앱의 에이전트 생성 로직 수정 필요
- ⚠️ LLM 설정 변경 시: `create_llm()` 함수 업데이트 필요

---

### 3. **src/ai_assistant/deep_agent.py** ⭐⭐ 높은 영향도
**의존 관계**:
```python
from .config import get_config, validate_config, setup_langsmith_tracing
```

**사용 위치**:
- `create_ai_coding_deep_agent()`: DeepAgent 생성 시 설정 사용

**영향**:
- DeepAgent 관련 설정 추가 시 이 파일 수정 필요
- LLM 설정 변경 시 ChatOpenAI 인스턴스 생성 부분 영향

**수정 필요성**:
- ⚠️ DeepAgent 전용 설정 추가 시 수정 필요

---

### 4. **run_agent.py** ⭐ 간접 영향
**의존 관계**:
```python
from ai_assistant import create_agent, create_self_healing_agent, create_ai_coding_deep_agent
```

**영향**:
- 직접적으로 config를 import하지는 않지만, 모든 에이전트 생성 함수가 내부적으로 config 사용
- CLI 인터페이스에서 새로운 에이전트 모드 추가 시 간접적 영향

**수정 필요성**:
- ℹ️ 새 에이전트 타입 추가 시 `--mode` 옵션에 추가 필요
- ℹ️ 설정 관련 CLI 옵션 추가 시 수정 필요

---

### 5. **tests/test_agent.py** ⭐ 낮은 영향도
**의존 관계**:
```python
from ai_assistant.config import get_config
```

**사용 위치**:
- `test_config()`: 설정 테스트
- `test_agent_invoke()`: API 키 검증

**영향**:
- 새로운 설정 추가 시 테스트 케이스 추가 권장

**수정 필요성**:
- ✅ 새 설정 필드 추가 시 테스트 케이스 추가 권장

---

## 🌐 간접 의존 파일 (Indirect Dependencies)

### 6. **src/ai_assistant/tools.py**
**간접 의존**: `agent.py` → `config.py`를 통해 간접 사용

**영향**:
- 도구 관련 설정 추가 시 영향 가능

---

### 7. **src/ai_assistant/subagents.py**
**간접 의존**: SubAgent 생성 시 config 사용 가능성

**영향**:
- SubAgent별 설정 추가 시 영향 가능

---

## 📊 새 앱 추가 시나리오

### 시나리오: "새로운 데이터베이스 앱" 설정 추가

#### 1단계: config.py 수정
```python
class Config(BaseModel):
    # ... 기존 설정 ...
    
    # 새 데이터베이스 앱 설정
    db_app_enabled: bool = Field(default=True)
    db_connection_string: str = Field(
        default_factory=lambda: os.getenv("DB_CONNECTION_STRING", "")
    )
    db_pool_size: int = Field(default=10)
```

#### 2단계: 영향받는 파일 및 수정 작업

| 파일 | 수정 필요성 | 수정 내용 |
|------|------------|----------|
| **src/ai_assistant/__init__.py** | ⚠️ 선택적 | 새 설정 관련 함수 추가 시 export |
| **src/ai_assistant/agent.py** | ✅ 필수 | DB 앱용 에이전트 생성 함수 추가 또는 기존 함수에서 DB 설정 사용 |
| **src/ai_assistant/deep_agent.py** | ⚠️ 선택적 | DeepAgent에서 DB 설정 필요 시 |
| **run_agent.py** | ⚠️ 선택적 | CLI에 `--mode db` 옵션 추가 |
| **tests/test_agent.py** | ✅ 권장 | DB 설정 테스트 추가 |
| **.env.example** | ✅ 필수 | 새 환경 변수 예시 추가 |

---

## 🎯 영향도 요약

### 높은 영향도 (반드시 확인 필요)
1. ✅ **agent.py** - 모든 에이전트 생성 로직
2. ✅ **deep_agent.py** - DeepAgent 로직
3. ✅ **__init__.py** - 패키지 public API

### 중간 영향도 (상황에 따라 수정)
4. ⚠️ **run_agent.py** - CLI 인터페이스
5. ⚠️ **subagents.py** - SubAgent 로직

### 낮은 영향도 (테스트 및 문서)
6. ℹ️ **test_agent.py** - 테스트 코드
7. ℹ️ **.env.example** - 환경 변수 문서

---

## 🔍 의존성 그래프

```
config.py
├── [직접 import]
│   ├── __init__.py (export get_config)
│   ├── agent.py (get_config, validate_config, setup_langsmith_tracing)
│   ├── deep_agent.py (get_config, validate_config, setup_langsmith_tracing)
│   └── tests/test_agent.py (get_config)
│
└── [간접 사용]
    ├── run_agent.py (via agent functions)
    ├── tools.py (via agent.py)
    └── subagents.py (via agent.py)
```

---

## ✅ 체크리스트: 새 앱 설정 추가 시

- [ ] `config.py`에 새 설정 필드 추가
- [ ] `.env.example`에 환경 변수 예시 추가
- [ ] `agent.py`에서 새 설정 사용 (필요 시 새 함수 추가)
- [ ] `__init__.py`에서 새 함수 export (추가한 경우)
- [ ] `run_agent.py`에 CLI 옵션 추가 (필요 시)
- [ ] `test_agent.py`에 테스트 케이스 추가
- [ ] 문서 업데이트 (README.md 등)

---

## 📝 권장사항

1. **설정 추가 시 기본값 제공**: 기존 코드 호환성 유지
2. **환경 변수 우선**: `.env` 파일로 설정 관리
3. **타입 힌트 사용**: Pydantic Field로 타입 안전성 보장
4. **검증 로직 추가**: `validate_config()` 함수에 검증 로직 추가
5. **테스트 작성**: 새 설정에 대한 테스트 케이스 필수

---

**분석 완료 일시**: 2024
**분석 대상**: `src/ai_assistant/config.py`
**프로젝트**: AI Coding Assistant
