"""SubAgents for DeepAgents Architecture.

This module implements specialized SubAgents following LangChain DeepAgents pattern:
https://docs.langchain.com/oss/python/deepagents/subagents

Each SubAgent is an independent agent specialized for a specific domain:
- AnalysisSubAgent: Code impact analysis
- CodingSubAgent: Code generation and self-healing
- DocumentationSubAgent: Documentation synchronization
- FileSystemSubAgent: File exploration and manipulation
"""

from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage
import logging

# Don't import create_llm here - it will be passed as parameter

logger = logging.getLogger(__name__)


def create_analysis_subagent():
    """Create Analysis SubAgent.
    
    Specialization: Code impact analysis
    Modes: SPEED (Tree-sitter + NetworkX), PRECISION (LSP)
    
    Returns:
        Compiled SubAgent
    """
    from .analyzers import SpeedAnalyzer, PrecisionAnalyzer
    
    # Simple function-based SubAgent
    def analyze(request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Run impact analysis.
        
        Args:
            request_dict: {
                "mode": "SPEED" or "PRECISION",
                "changed_file": str,
                "changed_symbol": str (optional)
            }
            
        Returns:
            Analysis result
        """
        mode = request_dict.get("mode", "SPEED")
        changed_file = request_dict.get("changed_file", "")
        changed_symbol = request_dict.get("changed_symbol")
        
        logger.info(f"[AnalysisSubAgent] Running {mode} analysis on {changed_file}")
        
        if mode == "SPEED":
            analyzer = SpeedAnalyzer()
        else:
            analyzer = PrecisionAnalyzer()
        
        result = analyzer.analyze(changed_file, changed_symbol)
        
        return {
            "impacted_files": result.impacted_files,
            "mode_used": result.mode_used,
            "analysis_time": result.analysis_time,
       "error": result.error
        }
    
    return analyze


def create_coding_subagent():
    """Create Coding SubAgent.
    
    Specialization: Code generation, testing, self-healing
    Features:
        - Generates Python code with PEP8 compliance
        - Creates pytest tests
        - Self-healing loop (max 3 retries)
        - Docker sandbox execution
    
    Returns:
        Compiled SubAgent
    """
    from .healing import CodeGenerator, TestGenerator, SelfHealer
    
    def code_and_heal(request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code, test, and heal if needed.
        
        Args:
            request_dict: {
                "request": str,  # User request
                "impacted_files": List[str],
                "context": str (optional)
            }
            
        Returns:
            Coding result with code, tests, healing info
        """
        llm = create_llm()
        
        user_request = request_dict.get("request", "")
        impacted_files = request_dict.get("impacted_files", [])
        context = request_dict.get("context")
        
        logger.info(f"[CodingSubAgent] Generating code for: {user_request[:50]}...")
        
        # 1. Generate code
        generator = CodeGenerator(llm)
        code = generator.generate(user_request, impacted_files, context)
        
        # 2. Generate tests
        test_gen = TestGenerator(llm)
        tests = test_gen.generate(code, user_request)
        
        # 3. Self-healing
        healer = SelfHealer(llm, max_retries=3)
        healing_result = healer.heal(code, tests, user_request)
        
        return {
            "generated_code": healing_result.final_code,
            "generated_tests": healing_result.final_tests,
            "healing_success": healing_result.success,
            "retry_count": healing_result.retry_count,
            "error_logs": healing_result.error_logs
        }
    
    return code_and_heal


def create_documentation_subagent():
    """Create Documentation SubAgent.
    
    Specialization: Documentation synchronization
    Features:
        - Docstring generation (Google Style)
        - README update proposals
        - API documentation sync
    
    Returns:
        Compiled SubAgent
    """
    from .doc_sync import DocumentSynchronizer
    
    def sync_docs(request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize documentation with code changes.
        
        Args:
            request_dict: {
                "code": str,
                "changed_files": List[str]
            }
            
        Returns:
            Documentation sync result
        """
        llm = create_llm()
        
        code = request_dict.get("code", "")
        changed_files = request_dict.get("changed_files", [])
        
        logger.info(f"[DocumentationSubAgent] Analyzing {len(changed_files)} files")
        
        synchronizer = DocumentSynchronizer(llm)
        result = synchronizer.analyze_and_propose(code, changed_files)
        
        return {
            "changes_detected": result.changes_detected,
            "proposed_changes": [
                {
                    "type": c.doc_type.value,
                    "location": c.location,
                    "proposed": c.proposed_content,
                    "reason": c.reason
                }
                for c in result.proposed_changes
            ],
            "summary": result.analysis_summary
        }
    
    return sync_docs


def create_filesystem_subagent():
    """Create FileSystem SubAgent.
    
    Specialization: File system exploration and manipulation
    Features:
        - Directory listing and navigation
        - File reading with large file handling
        - Pattern-based search (glob, grep)
        - Precise file modification
        - Large file summarization
    
    Returns:
        Compiled SubAgent with FileSystem tools
    """
    from .filesystem_tools import (
        _list_directory_impl,
        _read_file_impl,
        _glob_search_impl,
        _grep_search_impl,
        _edit_file_impl,
        _write_file_impl,
        FileSummarizer
    )
    
    def filesystem_ops(request_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file system operations.
        
        Args:
            request_dict: {
                "operation": str,  # "list", "read", "search", "edit", "write"
                "path": str (optional),
                "pattern": str (optional),
                "content": str (optional),
                ...
            }
            
        Returns:
            Operation result
        """
        operation = request_dict.get("operation", "list")
        
        logger.info(f"[FileSystemSubAgent] Operation: {operation}")
        
        if operation == "list":
            path = request_dict.get("path", ".")
            return {"result": _list_directory_impl(path)}
        
        elif operation == "read":
            file_path = request_dict.get("path", "")
            max_lines = request_dict.get("max_lines")
            return {"result": _read_file_impl(file_path, max_lines)}
        
        elif operation == "glob":
            pattern = request_dict.get("pattern", "**/*.py")
            root_dir = request_dict.get("root_dir", ".")
            return {"result": _glob_search_impl(pattern, root_dir)}
        
        elif operation == "grep":
            search_pattern = request_dict.get("pattern", "")
            file_pattern = request_dict.get("file_pattern", "**/*.py")
            root_dir = request_dict.get("root_dir", ".")
            context_lines = request_dict.get("context_lines", 2)
            return {"result": _grep_search_impl(search_pattern, file_pattern, root_dir, context_lines)}
        
        elif operation == "edit":
            file_path = request_dict.get("path", "")
            search_text = request_dict.get("search", "")
            replace_text = request_dict.get("replace", "")
            return {"result": _edit_file_impl(file_path, search_text, replace_text)}
        
        elif operation == "write":
            file_path = request_dict.get("path", "")
            content = request_dict.get("content", "")
            mode = request_dict.get("mode", "w")
            return {"result": _write_file_impl(file_path, content, mode)}
        
        else:
            return {"error": f"Unknown operation: {operation}"}
    
    return filesystem_ops


# SubAgent registry
SUBAGENTS = {
    "analysis": create_analysis_subagent,
    "coding": create_coding_subagent,
    "documentation": create_documentation_subagent,
    "filesystem": create_filesystem_subagent
}


def get_subagent(name: str):
    """Get a SubAgent by name.
    
    Args:
        name: SubAgent name (analysis, coding, documentation, filesystem)
        
    Returns:
        SubAgent function
        
    Raises:
        ValueError: If SubAgent name not found
    """
    if name not in SUBAGENTS:
        raise ValueError(f"Unknown SubAgent: {name}. Available: {list(SUBAGENTS.keys())}")
    
    return SUBAGENTS[name]()