# Mini Project

#### refs. 
- [참고자로 노션](https://bit.ly/SDS-LLM)
- [Excalidraw](https://excalidraw.com/)

## 주제
Agentic Coding Assistant  

## 설계 요구사항 
Excalidraw, DrawIO 등의 도구를 활용하여 이미지 파일로 제공해주세요.

## 구현 요구사항

- DeepAgent(https://blog.langchain.com/doubling-down-on-deepagents/, https://blog.langchain.com/deep-agents/) 의 개념(FileSystem, Planning, SubAgent)을 활용하셔서 ‘**라이브러리**’ 또는 ‘**직접 구현(다른 프레임워크 등)**’ 해주셔야합니다.

### 대기능1: 영향도 분석

- **FR-IA-01 (Dual-Mode Selection):** 시스템은 분석 모드를 `SPEED`(정적 분석)와 `PRECISION`(LSP 분석) 중 선택할 수 있는 인터페이스(LangGraph Platform)
- **FR-IA-02 (Speed Mode Execution):** `SPEED` 모드 선택 시, 시스템은 빌드 과정 없이 Tree-sitter 파싱과 NetworkX 그래프 탐색을 통해 5초 이내(10k 라인 기준)에 잠재적 의존성을 식별해야 한다.
- **FR-IA-03 (Precision Mode Execution):** `PRECISION` 모드 선택 시, 시스템은 LSP(Language Server) 프로토콜을 사용하여 컴파일러 수준의 정확한 참조(Reference) 목록을 반환해야 한다.
    - Python 의 경우 Pyright 을 사용(기 제공된 실습 코드 Day-04 의 SerenaMCP 에서 python 언어 부분을 참고합니다.)
- **FR-IA-04 (Fallback Mechanism):** `PRECISION` 모드 실행 실패 시(빌드 에러 등), 시스템은 사용자에게 `SPEED` 모드로의 전환을 제안하도록 Human-In-the-Loop 기능을 구현한다.
- `SPEED` / `PRECISION` 모드에 대한 세부 설명
    
    ### **Option A. Speed Mode (속도 우선 모드)**
    
    - **기반 기술:** **Tree-sitter** (Parsing) + **NetworkX** (Graph Algorithm)
    - **작동 방식:** 코드를 텍스트/구문 트리(AST) 레벨에서 파싱하여 파일 간의 import 구문과 함수 이름 매칭을 통해 의존성 그래프를 메모리에 구축한다.
    - **장점:**
    - **매우 빠름:** 별도의 빌드 과정 없이 수초 내에 분석 완료.
    - **설정 불필요:** 라이브러리 의존성이 설치되어 있지 않아도 분석 가능.
    - **단점:** 동적 타이핑 언어(Python, JS)에서 이름이 같은 다른 함수를 의존성으로 착각할 수 있음 (False Positive 가능성).
    
    ### **Option B. Precision Mode (정밀 분석 모드)**
    
    - **기반 기술:** **LSP** (Language Server Protocol)
    - **작동 방식:** VS Code 등 IDE가 사용하는 언어 서버(pyright, jdtls 등)와 통신하여, 컴파일러 수준의 정확한 '참조 찾기(Find References)'를 수행한다.
    - **장점:**
    - **정확성:** 실제 호출 관계만 정확히 파악 (False Positive 최소화).
    - **타입 추론:** 복잡한 제네릭이나 상속 관계도 정확히 해석.
    - **단점:**
    - **느림:** 서버 구동 및 인덱싱에 시간이 소요됨.
    
    **환경 종속:** 프로젝트 빌드 환경(의존성 패키지 설치 등)이 완벽해야 작동함.
    
    ```python
    # Pseudo Code
    def analyze_impact_selector(changed_node, mode="SPEED"):
        impact_list = []
    
        if mode == "SPEED":
            # [Option A] 정적 그래프 순회
            # AST(Abstract Syntax Tree) 파싱 결과로 구축된 NetworkX 그래프 사용
            impact_list = nx_graph.get_callers(changed_node, depth=3)
            
        elif mode == "PRECISION":
            # [Option B] LSP 쿼리 수행
            # LSP 서버가 준비되었는지 확인
            if not lsp_client.is_ready():
                raise EnvironmentError("LSP Server is not ready. Build environment required.")
                
            # 컴파일러 기반 참조 찾기
            impact_list = lsp_client.find_references(changed_node.symbol)
    
        return rank_by_criticality(impact_list)
    ```
    

### 대기능2: 자율 코딩 및 복구

코드 생성 결과가 검증에 실패할 경우, 에러 컨텍스트를 기반으로 스스로 수정하는 루프이다.

- 세부 설명
    
    **Process Flow:**
    
    1. **Execute:** 생성된 코드를 컴파일하거나 테스트를 실행한다.
    2. **Analyze:** 에러 메시지를 파싱하여 에러 유형을 분류한다.
    3. **Prompting:** Original Code + Error Log + Related Docs를 LLM에 전달.
    4. **Patch:** LLM이 생성한 수정분(Diff)을 적용.
    
    **Retry:** Retry Count를 증가시키고 재시도 (Max 3회).
    
- **FR-AC-01 (Refactoring Execution):** 시스템은 식별된 영향도 범위 내의 파일들을 대상으로, 사용자의 요청 의도에 맞는 수정 코드를 생성해야 한다.
- **FR-AC-02 (Self-Healing Loop):** 생성된 코드에서 컴파일 에러 또는 테스트 실패 발생 시, 시스템은 에러 로그를 분석하여 최대 3회까지 수정-재시도 루프를 자동으로 수행해야 한다.
    - 만약 최대 횟수에 도달할 경우, 사용자에게 루프의 실패를 고지하고 실행 루프를 멈춘다.
- **FR-AC-03 (Test Generation):** 시스템은 변경된 로직을 검증하기 위한 단위 테스트(Unit Test) 코드를 자동으로 생성하고 실행해야 한다.

### 대기능3: 문서화 동기화

- **FR-DS-01:** 소스 코드 변경 시, 시스템은 해당 코드와 연관된 Docstring, README, Swagger API 문서의 변경 필요 여부를 판단하고 수정안을 제시해야 한다.

### 대기능4: 파일 시스템 심층 탐색 및 조작

DeepAgents Library 에 이미 포함되어 있는 `FilesystemMiddleware`를 활용합니다. 
(**FileSystemBackend 사용 필수**, FileSystemBackend 는 실행 경로를 기반으로 인식합니다.)

https://docs.langchain.com/oss/python/deepagents/backends#filesystembackend-local-disk

- **FR-FS-01 (Contextual Exploration):** 에이전트는 `ls` 도구로 디렉토리 구조를 파악하고, `read_file` 도구를 사용하여 파일의 내용을 읽어 **개발 컨텍스트를 스스로 확보**해야 한다.
- **FR-FS-02 (Pattern-based Search):** 에이전트는 `glob`을 통한 패턴 매칭과 `grep`을 통한 문자열 검색 기능을 사용하여 **수정 대상 위치를 정확히 식별해야** 한다.
- **FR-FS-03 (Precise Code Modification):** 에이전트는 `edit_file` 도구를 사용하여 **파일의 특정 문자열을 정확하게 치환(String Replacement)**하거나, `write_file`을 통해 **새로운 파일을 생성할 수 있어야 한다.**
- **FR-FS-04 (Large Output Handling):** 토큰 제한을 초과하는 대용량 파일이나 검색 결과는 자동으로 파일 시스템에 저장하고, **에이전트에게 경로를 안내하는 처리 메커니즘을 포함해야** 한다.
    - 큰 파일의 경우, 저장하면서 핵심 요점만을 정리해서 따로 처리하도록 하는 SubAgent 를 호출할 수 있으며 이 경우 사용자에게 처리할지 여부를 Human-In-the-Loop 으로 요청합니다.

### 구현 간 참고사항

1. 프로젝트 구성 예시
    1. https://github.com/wassim249/fastapi-langgraph-agent-production-ready-template
2. 프로젝트 배포 예시
    1. Day-08 의 OpenLangGraphPlatform 코드를 참고하여 배포.
    2. Day-09 에서 `langgraph dev` 명령어를 활용한 LangSmith Platform 개발서버 배포.
3. DeepAgent Library 공식 문서
    1. https://docs.langchain.com/oss/python/deepagents/overview
4. Google Style Docstring 및 PEP8 기준 자동 Formatter 를 `uv` 패키지 매니저로 셋팅 하는 방법
    
    ```yaml
    # 대상 파일: pyproject.toml
    
    [tool.ruff]
    # 검사 대상 경로
    src = ["src", "tests"]
    
    [tool.ruff.format]
    # 기본 포매터 설정(black 유사 스타일)
    
    [tool.ruff.lint]
    # 사용할 규칙셋
    select = [
        "E",   # pycodestyle (PEP8)
        "F",   # pyflakes
        "D",   # pydocstyle (Docstring)
    ]
    
    ignore = [
        "D100",  # 모듈 docstring 없음 허용
        "D104",  # 패키지 docstring 없음 허용
    ]
    
    [tool.ruff.lint.pydocstyle]
    # Google 스타일 Docstring
    convention = "google"
    ```
    
    [VSCode Setting]
    
    “Ruff” 확장(charliermarsh.ruff)이 설치되어 있어야 합니다. (`uv add ruff`)
    
    Python 파일 저장 시 다음 2개 과정이 자동으로 수행됩니다.:
    
    > ruff format → 코드 포매팅 (PEP8)
    ruff check → 린트 + Docstring 규칙 검사
    > 
    
    ```yaml
    {
      "python.formatting.provider": "none",
      "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true
      }
    }
    ```
    

---

## 평가 기준

- 코드 구현 품질
    - PEP8 기준에 맞추어 작성 여부
    - DocString 은 Google Style
- 요구사항 구현 여부
    - DeepAgent(개념) 을 활용했는지 여부
    - Search 를 Internal / External 나누어서 구현했는지 여부
- Prompt & Context Engineering
    - 프롬프트 **강건성**: 동일 프롬프트 10회 실행 시 결과물이 안정적으로 나오는지 여부
    - 효율성: 토큰 최적화 여부
- SLM 을 활용하였는지(OpenRouter 에서 활용 가능한 sLM 으로 한정)
    - SLM 으로 `모든` Agent 로직을 적용했으며, SLM 에 최적화되게 구현 했는지
    - SLM 사용한 Agent 1건 이상 들어가 있는지 여부