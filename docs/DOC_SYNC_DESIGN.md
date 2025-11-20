# Document Synchronization Design (대기능3)

## FR-DS-01: 문서화 동기화

소스 코드 변경 시, 연관된 문서들을 자동으로 분석하고 업데이트 제안을 생성합니다.

## 기능 개요

### 대상 문서 타입
1. **Docstring**: Python 함수/클래스 문서
2. **README.md**: 프로젝트 문서
3. **API Docs**: FastAPI/Swagger 문서 (선택사항)

### 작동 방식

```
Code Change Detected
  ↓
Analyze Impact
  ↓
┌─────────────┬───────────────┬──────────────┐
│  Docstring  │    README     │   API Docs   │
│   Analysis  │   Analysis    │   Analysis   │
└──────┬──────┴───────┬───────┴──────┬───────┘
       ↓              ↓              ↓
   Need Update?   Need Update?   Need Update?
       ↓              ↓              ↓
   Generate      Generate       Generate
   Proposal      Proposal       Proposal
       ↓              ↓              ↓
       └──────────────┴──────────────┘
                 ↓
          Present to User
```

## 설계

### DocumentType Enum

```python
from enum import Enum

class DocumentType(Enum):
    DOCSTRING = "docstring"
    README = "readme"
    API_DOC = "api_doc"
```

### DocumentChange

```python
@dataclass
class DocumentChange:
    """Proposed documentation change."""
    doc_type: DocumentType
    file_path: str
    current_content: str
    proposed_content: str
    reason: str
    confidence: float  # 0.0-1.0
```

### DocumentSyncResult

```python
@dataclass
class DocumentSyncResult:
    """Result of documentation synchronization."""
    changes_detected: bool
    proposed_changes: List[DocumentChange]
    analysis_summary: str
```

## 구현 전략

### 1. Docstring Analyzer

**목적**: 함수/클래스 변경 시 Docstring 업데이트 필요성 판단

**방법**:
- Tree-sitter로 함수 signature 추출
- 기존 Docstring과 비교
- LLM으로 업데이트된 Docstring 생성

**예제**:
```python
# Code changed from:
def calculate(a, b):
    """Add two numbers."""
    return a + b

# To:
def calculate(a: int, b: int, operation: str = "add") -> int:
    """Perform calculation."""
    if operation == "add":
        return a + b
    return a - b

# Proposed Docstring:
"""Perform arithmetic calculation.

Args:
    a: First number
    b: Second number  
    operation: Operation type ('add' or 'subtract')
    
Returns:
    Result of the calculation
"""
```

### 2. README Analyzer

**목적**: 주요 기능 변경 시 README 업데이트

**탐지 기준**:
- 새로운 함수가 public API로 추가됨
- 기존 함수의 signature가 크게 변경됨
- 새로운 모듈 추가됨

**제안 내용**:
- Usage 예제 업데이트
- API 참조 추가
- 기능 목록 업데이트

### 3. API Documentation Analyzer

**목적**: FastAPI 엔드포인트 변경 시 API 문서 업데이트

**대상**:
- OpenAPI/Swagger spec
- 엔드포인트 설명
- 파라미터 문서

**방법**:
- FastAPI 데코레이터 파싱
- 기존 문서와 비교
- 업데이트된 스키마 생성

## LangGraph 노드

### doc_sync_node

```python
def doc_sync_node(state: AgentState) -> dict:
    """FR-DS-01: Analyze and propose documentation updates.
    
    Input:
        - generated_code: New/modified code
        - impacted_files: Files that changed
        
    Output:
        - doc_sync_result: Proposed documentation changes
    """
    llm = create_llm()
    synchronizer = DocumentSynchronizer(llm)
    
    result = synchronizer.analyze_and_propose(
        code=state.get("generated_code", ""),
        changed_files=state.get("impacted_files", [])
    )
    
    return {
        "doc_sync_result": {
            "changes_detected": result.changes_detected,
            "proposed_changes": [
                {
                    "type": change.doc_type.value,
                    "file": change.file_path,
                    "proposal": change.proposed_content,
                    "reason": change.reason
                }
                for change in result.proposed_changes
            ]
        }
    }
```

### Routing Function

```python
def should_sync_docs(state: AgentState) -> str:
    """Check if documentation sync is needed."""
    # If code generation succeeded and tests passed
    if (state.get("healing_result", {}).get("success") and
        state.get("test_results", {}).get("success")):
        return "sync_docs"
    
    return "skip_docs"
```

## 프롬프트 전략

### Docstring Update Prompt

```
You are a technical documentation expert.

Original Function:
{original_code}

Modified Function:
{modified_code}

Current Docstring:
{current_docstring}

Task: Generate an updated Google-style docstring that:
1. Reflects new parameters and return types
2. Explains new functionality
3. Includes usage examples if behavior changed significantly
4. Maintains clarity and conciseness

Return ONLY the updated docstring:
```

### README Update Prompt

```
You are a technical writer maintaining project documentation.

Code Changes:
- Modified files: {changed_files}
- New functions: {new_functions}
- Changed signatures: {changed_signatures}

Current README section:
{current_readme_section}

Task: Propose updates to the README that:
1. Reflect new or changed functionality
2. Update usage examples
3. Add new API references
4. Maintain consistent tone and style

Return ONLY the proposed changes with explanations:
```

## 성능 고려사항

### 선택적 분석
- 모든 변경에 문서 동기화를 실행하지 않음
- 중요도 기준으로 필터링

### 캐싱
- 이전 분석 결과 캐시
- 같은 코드에 대해 중복 분석 방지

### 배치 처리
- 여러 파일 변경을 한 번에 처리
- API 호출 최소화

## 사용자 워크플로우

### 1. 자동 감지
```python
result = await agent.ainvoke({...})

if result["doc_sync_result"]["changes_detected"]:
    print("📝 Documentation updates recommended")
```

### 2. 제안 확인
```python
for change in result["doc_sync_result"]["proposed_changes"]:
    print(f"File: {change['file']}")
    print(f"Type: {change['type']}")
    print(f"Proposal:\n{change['proposal']}")
```

### 3. 적용 (Human-in-the-Loop)
```python
# User approves or modifies proposals
apply_doc_changes(approved_changes)
```

## 구현 우선순위

1. ✅ **Phase 1**: Docstring 동기화 (핵심 기능)
2. ⬜ **Phase 2**: README 동기화
3. ⬜ **Phase 3**: API 문서 동기화 (선택사항)

## 다음 단계

1. DocumentSynchronizer 클래스 구현
2. Docstring 추출 및 비교 로직
3. LLM 기반 제안 생성
4. LangGraph 노드 통합
5. 예제 및 테스트