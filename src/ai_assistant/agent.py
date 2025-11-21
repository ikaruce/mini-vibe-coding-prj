"""LangGraph agent with SPEED/PRECISION mode branching."""

from typing import TypedDict, Annotated, Literal, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from .config import get_config, validate_config, setup_langsmith_tracing
from .tools import get_tools
from .prompts import SYSTEM_PROMPT

# Import analyzers
try:
    from .analyzers import SpeedAnalyzer, PrecisionAnalyzer, AnalysisResult
    ANALYZERS_AVAILABLE = True
except ImportError:
    ANALYZERS_AVAILABLE = False

# Import healing modules
try:
    from .healing import (
        CodeGenerator, TestGenerator, SelfHealer,
        TestResult, HealingResult
    )
    HEALING_AVAILABLE = True
except ImportError:
    HEALING_AVAILABLE = False

# Import document synchronization
try:
    from .doc_sync import DocumentSynchronizer, DocumentSyncResult, DocumentType
    DOC_SYNC_AVAILABLE = True
except ImportError:
    DOC_SYNC_AVAILABLE = False

# Import planning for DeepAgents
try:
    from .planner import Planner, Plan, Step, get_next_step, mark_step_complete
    PLANNER_AVAILABLE = True
except ImportError:
    PLANNER_AVAILABLE = False


class AgentState(TypedDict):
    """State for the agent with SPEED/PRECISION mode support.
    
    Based on claude.md requirements:
    - mode: SPEED or PRECISION analysis mode
    - impacted_files: List of files affected by changes
    - retry_count: Number of self-healing attempts
    - error_logs: Errors encountered during execution
    """
    messages: Annotated[list[BaseMessage], add_messages]
    context: str
    task_type: Literal["code_generation", "code_explanation", "general_chat"]
    
    # Analysis mode (FR-IA-01)
    mode: Literal["SPEED", "PRECISION"]
    
    # Impact analysis results (FR-IA-02, FR-IA-03)
    impacted_files: List[str]
    changed_file: Optional[str]
    changed_symbol: Optional[str]
    
    # Self-healing (FR-AC-02)
    retry_count: int
    error_logs: List[str]
    
    # Code generation (FR-AC-01)
    generated_code: Optional[str]
    generated_tests: Optional[str]
    test_results: Optional[dict]
    
    # Analysis metadata
    analysis_result: Optional[dict]
    
    # Healing result
    healing_result: Optional[dict]
    
    # Document synchronization (FR-DS-01)
    doc_sync_result: Optional[dict]
    
    # DeepAgents Planning
    plan: Optional[dict]  # Execution plan
    current_step_index: int
    planning_complete: bool


def create_llm():
    """Create and configure the LLM."""
    config = get_config()
    validate_config(config)
    
    return ChatOpenAI(
        model=config.openrouter_model,
        openai_api_key=config.openrouter_api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost:3000",
            "X-Title": "AI Coding Assistant"
        },
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


# Analysis Nodes

def speed_analysis_node(state: AgentState) -> dict:
    """FR-IA-02: SPEED mode analysis using Tree-sitter + NetworkX.
    
    Performance: 10k lines in < 5 seconds
    Method: Text-based AST parsing, no build required
    """
    print(f"🚀 Running SPEED analysis...")
    
    if not ANALYZERS_AVAILABLE:
        return {
            "impacted_files": [state.get("changed_file", "")],
            "error_logs": state.get("error_logs", []) + ["Analyzers not available"],
            "analysis_result": {"error": "Analyzers not installed"}
        }
    
    try:
        analyzer = SpeedAnalyzer()
        result = analyzer.analyze(
            changed_file=state.get("changed_file", ""),
            changed_symbol=state.get("changed_symbol")
        )
        
        return {
            "impacted_files": result.impacted_files,
            "analysis_result": {
                "mode": result.mode_used,
                "time": result.analysis_time,
                "error": result.error,
                "warnings": result.warnings
            }
        }
    
    except Exception as e:
        print(f"❌ SPEED analysis failed: {e}")
        return {
            "impacted_files": [],
            "error_logs": state.get("error_logs", []) + [f"SPEED analysis error: {str(e)}"],
            "analysis_result": {"error": str(e)}
        }


def precision_analysis_node(state: AgentState) -> dict:
    """FR-IA-03: PRECISION mode analysis using LSP.
    
    Method: Language Server Protocol (Pyright for Python)
    Output: Compiler-level accurate references
    """
    print(f"🎯 Running PRECISION analysis...")
    
    if not ANALYZERS_AVAILABLE:
        return {
            "impacted_files": [state.get("changed_file", "")],
            "error_logs": state.get("error_logs", []) + ["Analyzers not available"],
            "analysis_result": {"error": "Analyzers not installed"}
        }
    
    try:
        analyzer = PrecisionAnalyzer()
        result = analyzer.analyze(
            changed_file=state.get("changed_file", ""),
            changed_symbol=state.get("changed_symbol")
        )
        
        # Check if PRECISION failed
        if result.error:
            print(f"⚠️ PRECISION analysis failed: {result.error}")
            # This will trigger fallback mechanism
            return {
                "impacted_files": [],
                "error_logs": state.get("error_logs", []) + [f"PRECISION error: {result.error}"],
                "analysis_result": {
                    "mode": "PRECISION",
                    "error": result.error,
                    "should_fallback": True
                }
            }
        
        return {
            "impacted_files": result.impacted_files,
            "analysis_result": {
                "mode": result.mode_used,
                "time": result.analysis_time,
                "error": result.error,
                "warnings": result.warnings
            }
        }
    
    except Exception as e:
        print(f"❌ PRECISION analysis failed: {e}")
        return {
            "impacted_files": [],
            "error_logs": state.get("error_logs", []) + [f"PRECISION analysis error: {str(e)}"],
            "analysis_result": {
                "error": str(e),
                "should_fallback": True
            }
        }


# Routing Functions (Conditional Edges)

def route_by_mode(state: AgentState) -> str:
    """FR-IA-01: Route to appropriate analyzer based on mode.
    
    Uses LangGraph conditional edge to branch:
    - SPEED -> speed_analysis_node
    - PRECISION -> precision_analysis_node
    """
    mode = state.get("mode", "SPEED")
    print(f"📍 Routing to {mode} mode...")
    
    if mode == "SPEED":
        return "speed_analysis"
    elif mode == "PRECISION":
        return "precision_analysis"
    else:
        # Default to SPEED
        return "speed_analysis"


def check_precision_fallback(state: AgentState) -> str:
    """FR-IA-04: Fallback mechanism - PRECISION to SPEED on error.
    
    Human-in-the-loop: Ask user before falling back.
    For now, auto-fallback is enabled.
    """
    analysis_result = state.get("analysis_result", {})
    
    # Check if PRECISION failed and should fallback
    if analysis_result.get("should_fallback"):
        print("⚠️ PRECISION mode failed.")
        print("🔄 Falling back to SPEED mode...")
        # TODO: Implement Human-in-the-Loop approval using LangGraph interrupt
        return "fallback_to_speed"
    
    # If we have impacted files, proceed to code generation
    if state.get("impacted_files"):
        return "code_agent"
    
    return "end"


# Agent Nodes

def call_model(state: AgentState):
    """Call the LLM with tools."""
    llm = create_llm()
    tools = get_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    messages = state["messages"]
    
    # Add system message if not present
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    """Determine if we should continue to tools or end."""
    messages = state["messages"]
    last_message = messages[-1]
    
    # If there are no tool calls, we're done
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return "end"
    return "continue"


# Self-Healing Nodes (FR-AC-01, FR-AC-02, FR-AC-03)

def code_generation_node(state: AgentState) -> dict:
    """FR-AC-01: Generate code based on user request and impacted files."""
    if not HEALING_AVAILABLE:
        return {
            "error_logs": state.get("error_logs", []) + ["Healing module not available"]
        }
    
    print("💻 Generating code...")
    
    llm = create_llm()
    generator = CodeGenerator(llm)
    
    # Get user request from messages
    user_request = state["messages"][-1].content if state.get("messages") else "Generate code"
    impacted_files = state.get("impacted_files", [])
    
    code = generator.generate(
        request=user_request,
        impacted_files=impacted_files,
        context=state.get("context")
    )
    
    return {"generated_code": code}


def test_generation_node(state: AgentState) -> dict:
    """FR-AC-03: Generate pytest tests for generated code."""
    if not HEALING_AVAILABLE:
        return {
            "error_logs": state.get("error_logs", []) + ["Healing module not available"]
        }
    
    print("🧪 Generating tests...")
    
    llm = create_llm()
    test_gen = TestGenerator(llm)
    
    code = state.get("generated_code", "")
    user_request = state["messages"][-1].content if state.get("messages") else ""
    
    tests = test_gen.generate(code=code, request=user_request)
    
    return {"generated_tests": tests}


def execute_tests_node(state: AgentState) -> dict:
    """Execute tests and collect results."""
    if not HEALING_AVAILABLE:
        return {
            "error_logs": state.get("error_logs", []) + ["Healing module not available"]
        }
    
    print("🔬 Executing tests...")
    
    from .healing import TestExecutor
    
    executor = TestExecutor()
    result = executor.execute(
        code=state.get("generated_code", ""),
        tests=state.get("generated_tests", "")
    )
    
    return {
        "test_results": {
            "success": result.success,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "errors": result.errors,
            "returncode": result.returncode
        }
    }


def self_healing_node(state: AgentState) -> dict:
    """FR-AC-02: Self-healing loop to fix code errors."""
    if not HEALING_AVAILABLE:
        return {
            "error_logs": state.get("error_logs", []) + ["Healing module not available"]
        }
    
    print(f"🔧 Self-healing attempt {state.get('retry_count', 0) + 1}/3...")
    
    llm = create_llm()
    healer = SelfHealer(llm, max_retries=3)
    
    # Perform healing
    result = healer.heal(
        code=state.get("generated_code", ""),
        tests=state.get("generated_tests", ""),
        original_request=state["messages"][-1].content if state.get("messages") else ""
    )
    
    return {
        "generated_code": result.final_code,
        "retry_count": result.retry_count,
        "error_logs": state.get("error_logs", []) + result.error_logs,
        "healing_result": {
            "success": result.success,
            "retry_count": result.retry_count,
            "error_logs": result.error_logs
        }
    }


def check_test_result(state: AgentState) -> str:
    """Check if tests passed or need healing."""
    test_results = state.get("test_results", {})
    retry_count = state.get("retry_count", 0)
    
    # Tests passed - proceed to doc sync
    if test_results.get("success"):
        print("✅ All tests passed!")
        return "doc_sync"
    
    # Max retries exceeded - still do doc sync
    if retry_count >= 3:
        print("❌ Max retries exceeded (3/3)")
        print("📝 Proceeding to documentation sync anyway...")
        return "doc_sync"
    
    # Need healing
    print(f"⚠️ Tests failed, attempting self-healing...")
    return "heal"


# Document Synchronization Node (FR-DS-01)

def doc_sync_node(state: AgentState) -> dict:
    """FR-DS-01: Analyze and propose documentation updates.
    
    Input:
        - generated_code: New/modified code
        - impacted_files: Files that changed
        
    Output:
        - doc_sync_result: Proposed documentation changes
    """
    if not DOC_SYNC_AVAILABLE:
        return {
            "error_logs": state.get("error_logs", []) + ["Doc sync module not available"]
        }
    
    print("📝 Analyzing documentation synchronization...")
    
    llm = create_llm()
    synchronizer = DocumentSynchronizer(llm)
    
    result = synchronizer.analyze_and_propose(
        code=state.get("generated_code", ""),
        changed_files=state.get("impacted_files", [])
    )
    
    # Log results
    if result.changes_detected:
        print(f"📋 Found {len(result.proposed_changes)} documentation updates")
        for change in result.proposed_changes:
            print(f"   - {change.doc_type.value}: {change.location}")
    else:
        print("✅ Documentation is up to date")
    
    return {
        "doc_sync_result": {
            "changes_detected": result.changes_detected,
            "proposed_changes": [
                {
                    "type": change.doc_type.value,
                    "file": change.file_path,
                    "location": change.location,
                    "current": change.current_content[:200],  # Truncate for state
                    "proposed": change.proposed_content[:500],  # Truncate for state
                    "reason": change.reason,
                    "confidence": change.confidence
                }
                for change in result.proposed_changes
            ],
            "summary": result.analysis_summary
        }
    }


# Planning Node (DeepAgents)

def planning_node(state: AgentState) -> dict:
    """DeepAgents Planning: Create step-by-step execution plan.
    
    Input:
        - messages: User request
        
    Output:
        - plan: Structured execution plan
        - planning_complete: True
    """
    if not PLANNER_AVAILABLE:
        return {
            "error_logs": state.get("error_logs", []) + ["Planner module not available"],
            "planning_complete": False
        }
    
    print("🗺️  Creating execution plan...")
    
    llm = create_llm()
    planner = Planner(llm)
    
    user_request = state["messages"][-1].content if state.get("messages") else ""
    context = state.get("context", "")
    
    plan_result = planner.create_plan(user_request, context)
    
    # Log the plan
    print(f"\n📋 Execution Plan ({plan_result.total_steps} steps):")
    print("=" * 70)
    for step in plan_result.steps:
        print(f"  Step {step.id}: [{step.subagent}] {step.description[:60]}...")
    print("=" * 70)
    print(f"Estimated time: {plan_result.estimated_time:.1f}s\n")
    
    return {
        "plan": {
            "steps": [
                {
                    "id": s.id,
                    "action": s.action,
                    "description": s.description,
                    "subagent": s.subagent,
                    "status": s.status
                }
                for s in plan_result.steps
            ],
            "total_steps": plan_result.total_steps,
            "estimated_time": plan_result.estimated_time
        },
        "current_step_index": 0,
        "planning_complete": True
    }


# Graph Construction

def create_agent(enable_tracing: bool = True):
    """Create the LangGraph agent with SPEED/PRECISION branching.
    
    Args:
        enable_tracing: Whether to setup LangSmith tracing (default: True)
    
    Graph structure:
    
        START
          ↓
      [Entry] → mode decision
          ↓
    ┌─────┴──────┐
    ↓            ↓
[SPEED]    [PRECISION]
    ↓            ↓
    └─────┬──────┘
          ↓
    check fallback
          ↓
       [Agent] → tools
          ↓
         END
    """
    # Setup LangSmith tracing if enabled
    if enable_tracing:
        config = get_config()
        setup_langsmith_tracing(config)
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Add analysis nodes
    workflow.add_node("speed_analysis", speed_analysis_node)
    workflow.add_node("precision_analysis", precision_analysis_node)
    
    # Add agent nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(get_tools()))
    
    # Set entry point with conditional routing
    workflow.set_conditional_entry_point(
        route_by_mode,
        {
            "speed_analysis": "speed_analysis",
            "precision_analysis": "precision_analysis"
        }
    )
    
    # After SPEED analysis, go to agent
    workflow.add_edge("speed_analysis", "agent")
    
    # After PRECISION analysis, check if fallback needed
    workflow.add_conditional_edges(
        "precision_analysis",
        check_precision_fallback,
        {
            "fallback_to_speed": "speed_analysis",
            "code_agent": "agent",
            "end": END
        }
    )
    
    # Agent conditional edges (tool use or end)
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        }
    )
    
    # Tools loop back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    return workflow.compile()


def create_self_healing_agent(enable_tracing: bool = True):
    """Create agent with Self-Healing capabilities (FR-AC-01, FR-AC-02, FR-AC-03).
    
    Graph structure:
        START → Mode Analysis → Code Generation → Test Generation
        → Execute Tests → Check Results
        → [Pass: END] or [Fail: Self-Healing → Execute Tests again]
        → Max 3 retries
    
    Args:
        enable_tracing: Whether to enable LangSmith tracing
        
    Returns:
        Compiled LangGraph workflow
    """
    # Setup LangSmith tracing if enabled
    if enable_tracing:
        config = get_config()
        setup_langsmith_tracing(config)
    
    workflow = StateGraph(AgentState)
    
    # Add all nodes
    workflow.add_node("speed_analysis", speed_analysis_node)
    workflow.add_node("precision_analysis", precision_analysis_node)
    workflow.add_node("code_generation", code_generation_node)
    workflow.add_node("test_generation", test_generation_node)
    workflow.add_node("execute_tests", execute_tests_node)
    workflow.add_node("self_healing", self_healing_node)
    workflow.add_node("doc_sync", doc_sync_node)  # FR-DS-01
    
    # Entry point: mode-based routing
    workflow.set_conditional_entry_point(
        route_by_mode,
        {
            "speed_analysis": "speed_analysis",
            "precision_analysis": "precision_analysis"
        }
    )
    
    # After analysis, go to code generation
    workflow.add_edge("speed_analysis", "code_generation")
    
    # PRECISION may fallback to SPEED
    workflow.add_conditional_edges(
        "precision_analysis",
        check_precision_fallback,
        {
            "fallback_to_speed": "speed_analysis",
            "code_agent": "code_generation",
            "end": END
        }
    )
    
    # Code generation → Test generation
    workflow.add_edge("code_generation", "test_generation")
    
    # Test generation → Execute tests
    workflow.add_edge("test_generation", "execute_tests")
    
    # After tests, check results
    workflow.add_conditional_edges(
        "execute_tests",
        check_test_result,
        {
            "doc_sync": "doc_sync",  # Success or Max Retries → Document Sync
            "heal": "self_healing"
        }
    )
    
    # After doc sync, end
    workflow.add_edge("doc_sync", END)
    
    # After healing, execute tests again
    workflow.add_edge("self_healing", "execute_tests")
    
    return workflow.compile()


def create_simple_agent():
    """Create a simple agent without analysis (backward compatibility)."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(get_tools()))
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    # Compile the graph
    return workflow.compile()