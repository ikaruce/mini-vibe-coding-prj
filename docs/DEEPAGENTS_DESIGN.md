# DeepAgents Architecture Design

## DeepAgents란?

LangChain의 DeepAgents는 복잡한 작업을 효율적으로 처리하기 위한 아키텍처 패턴입니다.

### 핵심 개념 3가지

1. **Planning**: 복잡한 작업을 단계별로 분해
2. **SubAgent**: 특정 도메인에 특화된 하위 에이전트
3. **FileSystem**: 파일 시스템 작업을 위한 도구 세트

## 현재 구현 vs DeepAgents

### 이미 구현된 요소

#### ✅ FileSystem (대기능4)
- `list_directory`, `read_file` (FR-FS-01)
- `glob_search`, `grep_search` (FR-FS-02)
- `edit_file`, `write_file` (FR-FS-03)
- `FileSummarizer` SubAgent (FR-FS-04)

#### ✅ SubAgent 패턴
- `FileSummarizer`: 대용량 파일 요약
- `SelfHealer`: 코드 자동 수정
- `DocumentSynchronizer`: 문서 동기화

### 추가 필요한 요소

#### ⬜ Planning
- 사용자 요청을 단계별 계획으로 분해
- 각 단계에 필요한 도구/SubAgent 식별
- 실행 순서 최적화

## DeepAgents 아키텍처

### 전체 구조

```
User Request
    ↓
┌─────────────────────┐
│  Planning Agent     │ ← 작업을 단계로 분해
│  (Coordinator)      │
└──────────┬──────────┘
           │
    ┌──────┴──────┬──────────┬───────────┐
    ↓             ↓          ↓           ↓
┌────────┐  ┌─────────┐ ┌────────┐ ┌─────────┐
│AnalysisAnalyzer    │ │Healing │ │Doc Sync │
│SubAgent│  │SubAgent │ │SubAgent│ │SubAgent │
└────────┘  └─────────┘ └────────┘ └─────────┘
    │             │          │           │
    └─────────────┴──────────┴───────────┘
                   ↓
           FileSystem Tools
          (Exploration, Search,
           Modification)
```

### 역할 분담

#### 1. Main Agent (Coordinator)
- **역할**: 전체 워크플로우 조율
- **책임**: Planning, SubAgent 호출, 결과 통합
- **도구**: 모든 SubAgent에 접근 가능

#### 2. Planning SubAgent
- **역할**: 복잡한 요청을 실행 가능한 단계로 분해
- **입력**: 사용자 요청
- **출력**: Step-by-step 실행 계획

#### 3. Analysis SubAgent
- **역할**: 코드 영향도 분석
- **종류**: SpeedAnalyzer, PrecisionAnalyzer
- **도구**: Tree-sitter, LSP

#### 4. Coding SubAgent
- **역할**: 코드 생성 및 Self-Healing
- **구성요소**: CodeGenerator, TestGenerator, SelfHealer
- **도구**: Docker 샌드박스

#### 5. Documentation SubAgent
- **역할**: 문서 동기화
- **구성요소**: DocstringGenerator, ReadmeAnalyzer
- **도구**: AST 파싱

#### 6. FileSystem SubAgent
- **역할**: 파일 시스템 작업
- **구성요소**: FileSummarizer
- **도구**: ls, read, glob, grep, edit, write

## Planning 구현

### Plan 데이터 구조

```python
@dataclass
class Step:
    """Single step in execution plan."""
    id: int
    action: str  # "analyze", "code", "test", "doc_sync", "file_read"
    description: str
    required_tools: List[str]
    depends_on: List[int]  # Step IDs
    subagent: str  # "analysis", "coding", "doc", "filesystem"

@dataclass
class Plan:
    """Complete execution plan."""
    steps: List[Step]
    total_steps: int
    estimated_time: float  # seconds
```

### Planning Node

```python
def planning_node(state: AgentState) -> dict:
    """Decompose user request into executable steps.
    
    Input:
        - messages: User request
        
    Output:
        - plan: List of execution steps
        - current_step: 0
    """
    llm = create_llm()
    
    prompt = f"""Analyze the user request and create a step-by-step execution plan.

User Request: {state['messages'][-1].content}

Available SubAgents:
1. Analysis SubAgent - Code impact analysis (SPEED/PRECISION modes)
2. Coding SubAgent - Code generation, testing, self-healing
3. Documentation SubAgent - Docstring, README updates
4. FileSystem SubAgent - File exploration, search, modification

Task:
Create a numbered, sequential plan with:
- What to do in each step
- Which SubAgent to use
- Required tools/resources
- Dependencies between steps

Format your response as:
STEP 1: [SubAgent] Description
STEP 2: [SubAgent] Description
...

Example:
STEP 1: [FileSystem] Explore project structure with list_directory
STEP 2: [FileSystem] Search for config files using glob_search
STEP 3: [Analysis] Analyze impact of changing config.py (SPEED mode)
STEP 4: [Coding] Generate updated config code
STEP 5: [Coding] Run tests with self-healing
STEP 6: [Documentation] Update docstrings and README

Your plan:
"""
    
    response = llm.invoke(prompt)
    
    # Parse plan from response
    plan_steps = parse_plan(response.content)
    
    return {
        "plan": plan_steps,
        "current_step": 0,
        "planning_complete": True
    }
```

## 실행 흐름 (DeepAgents)

### 기존 흐름
```
Request → Analysis → Code Generation → Testing → Doc Sync → END
```

### DeepAgents 흐름
```
Request 
   ↓
Planning (작업 분해)
   ↓
Execute Step 1 → SubAgent A
   ↓
Execute Step 2 → SubAgent B
   ↓
Execute Step 3 → SubAgent A (재사용)
   ↓
Consolidate Results
   ↓
END
```

## SubAgent 통신 패턴

### 1. Direct Call
```python
# Main agent directly invokes subagent
analysis_result = analysis_subagent.invoke(request)
```

### 2. Message Passing
```python
# Use LangGraph state to pass context
state["subagent_request"] = {...}
# SubAgent reads from state
result = subagent_node(state)
```

### 3. Tool-based
```python
# SubAgent exposed as a tool
@tool
def call_analysis_subagent(request: str) -> str:
    return analysis_subagent.run(request)
```

## 장점

### 1. 모듈성
- 각 SubAgent가 독립적
- 쉬운 테스트 및 유지보수
- 재사용 가능

### 2. 확장성
- 새 SubAgent 쉽게 추가
- 도메인별 최적화 가능
- 다른 LLM 모델 사용 가능

### 3. 효율성
- 단순 작업은 간단한 SubAgent
- 복잡 작업은 Planning + 여러 SubAgent
- 병렬 실행 가능

## 구현 계획

1. ✅ 개념 분석 및 설계
2. Planning 노드 구현
3. SubAgent 패턴 명확화
4. State에 planning 필드 추가
5. 실행 coordinator 구현
6. 예제 작성

## 참고

- LangChain DeepAgents Blog: https://blog.langchain.com/deep-agents/
- FileSystemBackend: https://docs.langchain.com/oss/python/deepagents/backends