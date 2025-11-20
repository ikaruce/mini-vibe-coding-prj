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
    
    # Analysis metadata
    analysis_result: Optional[dict]


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