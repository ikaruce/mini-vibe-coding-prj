# LangSmith로 LangGraph 추적하기

LangSmith는 LangChain과 LangGraph 애플리케이션을 디버깅하고 모니터링하는 플랫폼입니다.

## 왜 LangSmith가 필요한가?

AI 코딩 어시스턴트는 복잡한 LangGraph 워크플로우를 사용합니다:
- **조건부 분기**: SPEED vs PRECISION 모드 선택
- **Fallback 메커니즘**: PRECISION 실패 시 SPEED로 자동 전환
- **상태 관리**: 여러 노드 간 상태 전달
- **도구 실행**: 코드 생성, 분석 등

LangSmith를 사용하면 이 모든 과정을 **실시간으로 시각화**할 수 있습니다.

## 🚀 빠른 시작

### 1. LangSmith 계정 생성

1. https://smith.langchain.com 방문
2. 계정 생성 (무료)
3. API 키 발급

### 2. 환경 변수 설정

```powershell
# .env 파일 편집
notepad .env
```

다음 내용 추가:
```env
# LangSmith 추적 활성화
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_pt_xxxxxxxxxxxxx  # 발급받은 API 키
LANGCHAIN_PROJECT=ai-coding-assistant
```

### 3. 실행 및 확인

```powershell
# 모드 분기 데모 실행
python examples/mode_branching_demo.py
```

콘솔에 다음 메시지가 표시됩니다:
```
✅ LangSmith tracing enabled
   Project: ai-coding-assistant
   Dashboard: https://smith.langchain.com
```

### 4. 대시보드 확인

1. https://smith.langchain.com 접속
2. 왼쪽 메뉴에서 **"Projects"** 클릭
3. **"ai-coding-assistant"** 프로젝트 선택
4. 실행 추적(Trace) 확인

## 📊 LangGraph 추적 보기

### 그래프 구조 시각화

LangSmith는 LangGraph의 실행 흐름을 시각적으로 보여줍니다:

```
START
  ↓
route_by_mode (condition)
  ↓
┌─────┴──────┐
↓            ↓
SPEED    PRECISION
  ↓            ↓
  └──→ Agent ←─┘
        ↓
      Tools
        ↓
       END
```

### 각 노드에서 확인할 수 있는 정보

#### 1. route_by_mode (조건부 분기)
- **입력**: 현재 state (mode: "SPEED" 또는 "PRECISION")
- **결정**: 어느 분석기로 라우팅할지
- **출력**: "speed_analysis" 또는 "precision_analysis"

#### 2. speed_analysis_node
- **실행 시간**: Tree-sitter 파싱 소요 시간
- **입력 파일**: changed_file 경로
- **출력**: impacted_files 리스트
- **메타데이터**: analysis_time, warnings 등

#### 3. precision_analysis_node
- **실행 시간**: LSP 쿼리 소요 시간
- **에러 여부**: LSP 연결 실패 시 표시
- **Fallback 트리거**: should_fallback 플래그

#### 4. check_precision_fallback
- **조건**: analysis_result에 에러가 있는가?
- **결정**: "fallback_to_speed", "code_agent", 또는 "end"
- **Fallback 카운트**: 몇 번 재시도했는지

### 상태(State) 변화 추적

각 노드 실행 후 상태가 어떻게 변하는지 확인할 수 있습니다:

```python
# 초기 상태
{
  "mode": "PRECISION",
  "changed_file": "src/ai_assistant/agent.py",
  "impacted_files": [],
  "error_logs": [],
  "retry_count": 0
}

# precision_analysis_node 실행 후
{
  "mode": "PRECISION",
  "changed_file": "src/ai_assistant/agent.py",
  "impacted_files": [],  # 여전히 비어있음 (에러 발생)
  "error_logs": ["PRECISION analysis error: LSP not available"],
  "retry_count": 0,
  "analysis_result": {
    "error": "LSP not available",
    "should_fallback": true
  }
}

# Fallback 후 speed_analysis_node 실행
{
  "mode": "PRECISION",  # 원래 모드는 유지
  "changed_file": "src/ai_assistant/agent.py",
  "impacted_files": [  # SPEED 모드로 분석 완료
    "src/ai_assistant/agent.py",
    "examples/basic_chat.py",
    "examples/code_generation.py"
  ],
  "error_logs": ["PRECISION analysis error: LSP not available"],
  "analysis_result": {
    "mode": "SPEED",  # 실제 사용된 모드
    "time": 0.45,
    "warnings": []
  }
}
```

## 🔍 고급 사용법

### 1. 특정 세션 추적

```python
import os
os.environ["LANGCHAIN_SESSION"] = "debug-session-001"

agent = create_agent()
# 이제 모든 실행이 "debug-session-001"로 그룹화됨
```

### 2. 추적 비활성화 (프로덕션)

```python
# 추적 없이 에이전트 생성
agent = create_agent(enable_tracing=False)
```

또는 환경 변수:
```env
LANGCHAIN_TRACING_V2=false
```

### 3. 커스텀 메타데이터 추가

```python
from langsmith import traceable

@traceable(name="custom_analysis", metadata={"version": "1.0"})
def my_analysis(file_path):
    # 커스텀 분석 로직
    pass
```

## 📈 성능 분석

LangSmith는 각 노드의 실행 시간을 측정합니다:

### SPEED 모드 성능
- **Tree-sitter 파싱**: ~0.2초
- **그래프 구축**: ~0.1초
- **의존성 탐색**: ~0.15초
- **총 시간**: ~0.45초 (10k 라인 기준)

### PRECISION 모드 성능
- **LSP 초기화**: ~1.0초
- **References 쿼리**: ~0.5초
- **결과 파싱**: ~0.1초
- **총 시간**: ~1.6초

### Fallback 오버헤드
- **PRECISION 시도 + 실패**: ~0.3초
- **SPEED로 전환**: ~0.45초
- **총 오버헤드**: ~0.75초 (허용 가능)

## 🐛 디버깅 팁

### 1. 모드 분기 추적

**문제**: PRECISION 모드를 요청했는데 SPEED 모드가 실행됨

**해결**:
1. LangSmith에서 `route_by_mode` 노드 확인
2. 입력 상태의 `mode` 필드 확인
3. 조건부 엣지 결정 로직 확인

### 2. Fallback 원인 파악

**문제**: PRECISION → SPEED fallback이 발생함

**해결**:
1. `precision_analysis_node` 노드의 출력 확인
2. `error_logs`에 에러 메시지 확인
3. `analysis_result.error` 필드 확인

### 3. 상태 불일치

**문제**: impacted_files가 예상과 다름

**해결**:
1. 각 분석 노드의 입출력 확인
2. `changed_file` 경로가 정확한지 확인
3. 의존성 그래프 구축 로그 확인

## 📝 LangSmith 대시보드 활용

### Traces (추적)
- **필터링**: 모드별, 에러 여부, 실행 시간으로 필터
- **검색**: 특정 파일명으로 검색
- **비교**: SPEED vs PRECISION 모드 비교

### Datasets (데이터셋)
- 반복 테스트를 위한 입력 데이터셋 생성
- 회귀 테스트 자동화

### Playground
- 개별 노드 테스트
- 프롬프트 수정 및 비교
- A/B 테스트

## 🔗 참고 자료

- [LangSmith 공식 문서](https://docs.smith.langchain.com/)
- [LangGraph 디버깅 가이드](https://langchain-ai.github.io/langgraph/how-tos/debug/)
- [Tracing FAQs](https://docs.smith.langchain.com/tracing/faq)

## 💡 베스트 프랙티스

1. **개발 중**: 항상 추적 활성화
2. **프로덕션**: 샘플링 추적 (LANGCHAIN_SAMPLE_RATE=0.1)
3. **디버깅**: 세션 이름으로 그룹화
4. **성능**: 백그라운드 콜백 사용 (LANGCHAIN_CALLBACKS_BACKGROUND=true)
5. **보안**: API 키를 절대 코드에 하드코딩하지 않기

## ❓ 문제 해결

### API 키 오류
```
Error: Invalid API key
```
**해결**: API 키가 올바른지 확인, `lsv2_pt_`로 시작해야 함

### 추적이 표시되지 않음
```
Warning: LANGCHAIN_TRACING_V2 is enabled but LANGCHAIN_API_KEY is not set.
```
**해결**: .env 파일에 LANGCHAIN_API_KEY 설정 확인

### 프로젝트가 보이지 않음
**해결**: 
1. LangSmith 대시보드 새로고침
2. 프로젝트 이름 확인 (LANGCHAIN_PROJECT)
3. API 키 권한 확인