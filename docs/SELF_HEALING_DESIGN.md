# Self-Healing Loop 설계 문서 (대기능2)

## 개요

코드 생성 결과가 검증에 실패할 경우, 에러 컨텍스트를 기반으로 스스로 수정하는 자율 복구 시스템입니다.

## 요구사항

### FR-AC-01: Refactoring Execution
- 영향도 범위 내의 파일들을 대상으로 사용자 요청에 맞는 수정 코드 생성

### FR-AC-02: Self-Healing Loop
- **Process**: Execute → Analyze → Patch → Retry
- **Max Retry**: 3회
- **Failure Handling**: 3회 초과 시 사용자에게 실패 고지

### FR-AC-03: Test Generation
- 변경된 로직을 검증하기 위한 단위 테스트 자동 생성

## LangGraph 아키텍처

### State 정의

```python
class SelfHealingState(TypedDict):
    # 기존 상태
    messages: Annotated[list[BaseMessage], add_messages]
    mode: Literal["SPEED", "PRECISION"]
    impacted_files: List[str]
    
    # Self-Healing 관련
    retry_count: int  # 현재 재시도 횟수 (0-3)
    error_logs: List[str]  # 에러 로그 누적
    
    # 코드 생성 결과
    generated_code: Optional[str]  # 생성된 코드
    generated_tests: Optional[str]  # 생성된 테스트
    test_results: Optional[Dict]  # 테스트 실행 결과
    
    # 수정 히스토리
    code_history: List[Dict]  # 각 시도의 코드 기록
```

### 워크플로우

```
[Code Generation]
       ↓
[Test Generation]
       ↓
[Execute Tests] ──┐
       │          │
       ↓          │
  [Analyze]       │
       │          │
    Success? ─No→ [Self-Healing] ─→ retry_count < 3? ─Yes─┐
       │                                    No             │
      Yes                                   ↓              │
       ↓                              [Report Failure]     │
     [END]                                                 │
                                                           │
                                    ←──────────────────────┘
```

## 노드 구현

### 1. Code Generation Node

```python
def code_generation_node(state: SelfHealingState) -> Dict:
    """FR-AC-01: 영향도 범위 내 파일들을 수정
    
    Input:
        - impacted_files: 수정 대상 파일 목록
        - messages: 사용자 요청
    
    Output:
        - generated_code: 생성된 코드
    """
    llm = create_llm()
    
    prompt = f"""
    다음 파일들을 사용자 요청에 맞게 수정하세요:
    
    파일 목록: {state['impacted_files']}
    사용자 요청: {state['messages'][-1].content}
    
    요구사항:
    1. PEP8 준수
    2. Google Style Docstring
    3. Type hints 포함
    4. Error handling 포함
    """
    
    response = llm.invoke(prompt)
    
    return {
        "generated_code": response.content,
        "code_history": state.get("code_history", []) + [{
            "attempt": state.get("retry_count", 0),
            "code": response.content
        }]
    }
```

### 2. Test Generation Node

```python
def test_generation_node(state: SelfHealingState) -> Dict:
    """FR-AC-03: 단위 테스트 자동 생성
    
    Input:
        - generated_code: 생성된 코드
    
    Output:
        - generated_tests: pytest 테스트 코드
    """
    llm = create_llm()
    
    prompt = f"""
    다음 코드에 대한 pytest 단위 테스트를 생성하세요:
    
    코드:
    {state['generated_code']}
    
    요구사항:
    1. pytest 프레임워크 사용
    2. Edge cases 포함
    3. 모든 함수에 대한 테스트
    4. Mocking이 필요한 경우 pytest-mock 사용
    """
    
    response = llm.invoke(prompt)
    
    return {
        "generated_tests": response.content
    }
```

### 3. Execute Tests Node

```python
def execute_tests_node(state: SelfHealingState) -> Dict:
    """테스트 실행 및 결과 수집
    
    Input:
        - generated_code: 생성된 코드
        - generated_tests: 생성된 테스트
    
    Output:
        - test_results: {
            "success": bool,
            "errors": List[str],
            "stdout": str,
            "stderr": str
        }
    """
    import subprocess
    import tempfile
    from pathlib import Path
    
    # 임시 파일에 코드 작성
    with tempfile.TemporaryDirectory() as tmpdir:
        code_path = Path(tmpdir) / "generated_code.py"
        test_path = Path(tmpdir) / "test_generated_code.py"
        
        code_path.write_text(state['generated_code'])
        test_path.write_text(state['generated_tests'])
        
        # pytest 실행
        result = subprocess.run(
            ["pytest", str(test_path), "-v"],
            capture_output=True,
            text=True,
            cwd=tmpdir
        )
        
        return {
            "test_results": {
                "success": result.returncode == 0,
                "errors": parse_pytest_errors(result.stderr),
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }
```

### 4. Analyze Error Node

```python
def analyze_error_node(state: SelfHealingState) -> Dict:
    """에러 분석 및 분류
    
    Input:
        - test_results: 테스트 실행 결과
    
    Output:
        - error_analysis: {
            "error_type": str,  # syntax, logic, import, etc.
            "error_location": str,
            "suggested_fix": str
        }
    """
    if state['test_results']['success']:
        return {"error_logs": []}
    
    errors = state['test_results']['errors']
    
    # 에러 타입 분류
    error_types = classify_errors(errors)
    
    return {
        "error_logs": state.get("error_logs", []) + [
            f"Attempt {state['retry_count']}: {', '.join(error_types)}"
        ]
    }
```

### 5. Self-Healing Node

```python
def self_healing_node(state: SelfHealingState) -> Dict:
    """FR-AC-02: 에러 기반 코드 수정
    
    Process:
        1. Original Code + Error Log + Related Docs → LLM
        2. LLM이 수정안(Patch) 생성
        3. retry_count 증가
    
    Input:
        - generated_code: 현재 코드
        - error_logs: 에러 로그
        - test_results: 테스트 결과
    
    Output:
        - generated_code: 수정된 코드
        - retry_count: 증가된 재시도 횟수
    """
    llm = create_llm()
    
    prompt = f"""
    다음 코드에 에러가 발생했습니다. 수정해주세요.
    
    원본 코드:
    {state['generated_code']}
    
    에러 로그:
    {state['test_results']['stderr']}
    
    에러 분석:
    {state['error_logs'][-1]}
    
    요구사항:
    1. 에러만 수정하고 다른 부분은 유지
    2. 같은 에러가 반복되지 않도록 근본 원인 해결
    3. 주석으로 수정 사항 설명
    """
    
    response = llm.invoke(prompt)
    
    return {
        "generated_code": response.content,
        "retry_count": state.get("retry_count", 0) + 1,
        "code_history": state.get("code_history", []) + [{
            "attempt": state.get("retry_count", 0) + 1,
            "code": response.content,
            "fix_reason": state['error_logs'][-1]
        }]
    }
```

### 6. Routing Functions

```python
def should_retry(state: SelfHealingState) -> str:
    """재시도 여부 결정
    
    Returns:
        - "retry": 재시도 (retry_count < 3 and test failed)
        - "success": 성공 (test passed)
        - "failure": 실패 (retry_count >= 3)
    """
    # 테스트 성공
    if state.get('test_results', {}).get('success'):
        return "success"
    
    # 재시도 횟수 초과
    if state.get('retry_count', 0) >= 3:
        return "failure"
    
    # 재시도
    return "retry"
```

## Error Classification

### 에러 타입 분류

```python
def classify_errors(error_messages: List[str]) -> List[str]:
    """에러 타입 분류
    
    Types:
        - syntax: 문법 에러
        - import: Import 에러
        - type: Type 관련 에러
        - logic: 로직 에러
        - runtime: 런타임 에러
    """
    error_types = []
    
    for error in error_messages:
        if "SyntaxError" in error:
            error_types.append("syntax")
        elif "ImportError" in error or "ModuleNotFoundError" in error:
            error_types.append("import")
        elif "TypeError" in error or "AttributeError" in error:
            error_types.append("type")
        elif "AssertionError" in error:
            error_types.append("logic")
        else:
            error_types.append("runtime")
    
    return list(set(error_types))
```

## LangGraph Integration

### 그래프 구조

```python
def create_self_healing_agent():
    """Self-Healing 기능이 포함된 에이전트"""
    
    workflow = StateGraph(SelfHealingState)
    
    # 노드 추가
    workflow.add_node("code_generation", code_generation_node)
    workflow.add_node("test_generation", test_generation_node)
    workflow.add_node("execute_tests", execute_tests_node)
    workflow.add_node("analyze_error", analyze_error_node)
    workflow.add_node("self_healing", self_healing_node)
    
    # 엣지 정의
    workflow.set_entry_point("code_generation")
    workflow.add_edge("code_generation", "test_generation")
    workflow.add_edge("test_generation", "execute_tests")
    workflow.add_edge("execute_tests", "analyze_error")
    
    # 조건부 엣지
    workflow.add_conditional_edges(
        "analyze_error",
        should_retry,
        {
            "retry": "self_healing",
            "success": END,
            "failure": END
        }
    )
    
    # Self-Healing → Execute Tests (재시도)
    workflow.add_edge("self_healing", "execute_tests")
    
    return workflow.compile()
```

## 성능 목표

- **Initial Code Generation**: < 10초
- **Test Generation**: < 5초
- **Test Execution**: < 3초
- **Self-Healing (per iteration)**: < 15초
- **Total (worst case, 3 retries)**: < 60초

## 에러 처리

### 재시도 실패 시

```python
def handle_max_retries_exceeded(state: SelfHealingState):
    """최대 재시도 횟수 초과 시 처리"""
    
    failure_report = f"""
    ❌ 자동 수정 실패 (3회 시도 완료)
    
    마지막 에러:
    {state['test_results']['stderr']}
    
    시도 히스토리:
    """
    
    for i, history in enumerate(state['code_history']):
        failure_report += f"""
    
    [시도 {i+1}]
    {history.get('fix_reason', 'Initial generation')}
    """
    
    return {
        "messages": [("system", failure_report)],
        "final_status": "failed"
    }
```

## 테스트 전략

### 단위 테스트

```python
def test_self_healing_node():
    """Self-Healing 노드 테스트"""
    state = {
        "generated_code": "def add(a, b):\n    return a - b",  # 의도적 버그
        "retry_count": 0,
        "error_logs": [],
        "test_results": {
            "success": False,
            "stderr": "AssertionError: Expected 3, got -1"
        }
    }
    
    result = self_healing_node(state)
    
    assert result['retry_count'] == 1
    assert "return a + b" in result['generated_code']  # 수정 확인
```

### 통합 테스트

```python
async def test_full_self_healing_flow():
    """전체 Self-Healing 워크플로우 테스트"""
    agent = create_self_healing_agent()
    
    result = await agent.ainvoke({
        "messages": [("user", "Create a function to add two numbers")],
        "retry_count": 0,
        "error_logs": []
    })
    
    assert result['test_results']['success']
    assert result['retry_count'] <= 3
```

## 다음 단계

1. ✅ 설계 문서 작성
2. Self-Healing 노드 구현
3. LangGraph 통합
4. 테스트 작성
5. 예제 생성
6. 문서화