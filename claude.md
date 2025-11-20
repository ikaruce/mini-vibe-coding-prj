Project: LangGraph 기반 자율 코딩 AI Assistant (DeepAgents 활용)

당신은 LangChain, LangGraph, 그리고 고급 정적/동적 분석 기술(LSP, Tree-sitter)에 정통한 수석 AI 엔지니어입니다.
아래의 요구사항을 준수하여 AI Coding Assistant의 아키텍처를 설계하고 Python 코드를 구현해야 합니다.

1. 기술 스택 및 환경 (Tech Stack)

Core Framework: LangChain, LangGraph

Agent Library: DeepAgents (특히 FilesystemMiddleware, FileSystemBackend 활용)

Language: Python 3.10+

Static Analysis: Tree-sitter, NetworkX

Dynamic Analysis: LSP (Language Server Protocol) - Python의 경우 Pyright 사용

State Management: LangGraph StateGraph

2. 시스템 아키텍처 개요

이 시스템은 사용자의 코딩 요청을 받아 영향도를 분석하고, 코드를 수정/생성하며, 테스트를 통해 스스로 복구하고, 문서를 동기화하는 자율 에이전트입니다.

주요 워크플로우 (LangGraph)

Input Analysis: 사용자 요청 분석 및 모드 확인 (SPEED vs PRECISION).

Impact Analysis: 변경이 필요한 파일 식별 (Graph 탐색 또는 LSP 참조 찾기).

Code Generation: 영향도 범위 내 코드 리팩토링/생성.

Verification (Self-Healing): 테스트/컴파일 실행 -> 실패 시 에러 분석 -> 재시도 (Max 3회).

Documentation: 코드 변경에 따른 문서(Docstring, README 등) 동기화.

3. 상세 기능 요구사항 (Functional Requirements)

대기능 1: 영향도 분석 (Impact Analysis)

시스템은 코드 변경 전, 변경이 미칠 영향을 미리 파악해야 합니다.

FR-IA-01 (Dual-Mode Selection):

LangGraph의 상태(State) 또는 Config를 통해 분석 모드를 SPEED와 PRECISION 중에서 선택할 수 있어야 합니다.

LangGraph의 Conditional Edge를 사용하여 모드에 따라 다른 노드(SpeedAnalyzer vs PrecisionAnalyzer)로 분기합니다.

FR-IA-02 (Speed Mode Execution):

Trigger: mode="SPEED"

Method: Tree-sitter로 AST 파싱 -> NetworkX로 의존성 그래프 생성 -> 그래프 순회.

Performance: 10k 라인 기준 5초 이내 분석.

Constraint: 빌드 과정 없이 텍스트 기반 파싱만 수행.

FR-IA-03 (Precision Mode Execution):

Trigger: mode="PRECISION"

Method: LSP(Language Server Protocol) 클라이언트 구현.

Tool: Python 분석 시 Pyright Language Server와 통신.

Output: 컴파일러 수준의 정확한 'References' 목록 반환.

FR-IA-04 (Fallback Mechanism - Human-In-the-Loop):

PRECISION 모드 실행 중 에러(빌드 실패, LSP 연결 실패 등) 발생 시, 작업을 중단하지 않습니다.

LangGraph의 interrupt 기능을 사용하여 사용자에게 "SPEED 모드로 전환하시겠습니까?"라고 묻고 승인 시 SPEED 노드로 전환합니다.

대기능 2: 자율 코딩 및 복구 (Autonomous Coding & Healing)

코드를 생성하고 검증하며, 실패 시 스스로 수정합니다.

FR-AC-01 (Refactoring Execution):

식별된 '영향도 범위(Impact Scope)' 내의 파일들만 대상으로 수정을 가합니다.

FR-AC-02 (Self-Healing Loop):

Cycle: Execute (테스트/컴파일) -> Analyze (에러 파싱) -> Patch (수정) -> Retry.

Limit: 최대 3회 재시도(max_retries=3).

Action: 3회 초과 실패 시 루프를 중단하고 사용자에게 실패 리포트를 반환합니다.

FR-AC-03 (Test Generation):

로직 변경 시, 이를 검증할 Unit Test 코드를 자동으로 생성하고 실행 파이프라인에 포함시킵니다.

대기능 3: 문서화 동기화 (Doc Sync)

FR-DS-01:

소스 코드 변경이 확정되면, 연관된 Docstring, README.md, Swagger 문서를 분석합니다.

변경 사항을 반영하여 문서를 업데이트하는 수정안을 제시합니다.

대기능 4: 파일 시스템 심층 탐색 및 조작 (Filesystem)

DeepAgents 라이브러리의 기능을 활용하여 파일 시스템을 조작합니다.

Backend: FilesystemMiddleware 및 FileSystemBackend 사용 필수.

FR-FS-01 (Contextual Exploration):

ls 도구로 구조 파악, read_file로 내용 읽기.

FR-FS-02 (Pattern-based Search):

glob 패턴 매칭과 grep 문자열 검색 도구 구현.

FR-FS-03 (Precise Code Modification):

edit_file: 전체 덮어쓰기가 아닌, 특정 문자열 치환(String Replacement) 기능 구현.

write_file: 신규 파일 생성.

FR-FS-04 (Large Output Handling & SubAgent):

검색 결과나 파일 내용이 토큰 제한을 초과할 경우, 자동으로 별도 파일로 저장하고 경로만 컨텍스트에 남깁니다.

초대형 파일 처리가 필요한 경우, SummarizerSubAgent를 호출하기 전 Human-In-the-Loop을 통해 사용자 승인을 요청합니다.

4. 구현 가이드라인 (Implementation Guide)

A. LangGraph State 설계

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    mode: Literal["SPEED", "PRECISION"]
    impacted_files: List[str]
    retry_count: int
    error_logs: List[str]
    # ... 기타 필요한 상태


B. Pseudo Code for Analysis Node

def impact_analysis_node(state: AgentState):
    mode = state.get("mode", "SPEED")
    changed_node = extract_changed_symbol(state)
    
    if mode == "SPEED":
        impacts = run_tree_sitter_analysis(changed_node)
    elif mode == "PRECISION":
        try:
            impacts = run_lsp_query(changed_node)
        except Exception as e:
            # HITL 요청을 위한 상태 업데이트 또는 인터럽트 발생
            return Command(goto="human_approval_for_fallback", update={"error": str(e)})
            
    return {"impacted_files": impacts}


5. 지시 사항 (Instructions)

위 요구사항을 만족하는 LangGraph 구조를 설계하고 그래프 정의 코드를 작성하세요.

각 노드(SpeedAnalyzer, PrecisionAnalyzer, CodeGenerator, SelfHealingLoop 등)의 핵심 로직을 구현하세요.

DeepAgents의 FileSystemBackend를 사용하는 Tool 정의 부분을 포함하세요.

에러 복구 루프와 Fallback 메커니즘(HITL)이 코드에 명시적으로 드러나야 합니다.