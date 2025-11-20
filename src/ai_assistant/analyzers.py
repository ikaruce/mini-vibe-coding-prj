"""Impact analysis modules for SPEED and PRECISION modes.

This module implements the dual-mode analysis system described in claude.md:
- FR-IA-02: SPEED mode using Tree-sitter + NetworkX
- FR-IA-03: PRECISION mode using LSP (Language Server Protocol)

The mode selection and branching is handled by LangGraph in agent.py.
"""

from typing import List, Optional, Literal
from pathlib import Path
import logging
from dataclasses import dataclass, field
import time

# Tree-sitter and NetworkX for SPEED mode
try:
    import tree_sitter_python as tspython
    from tree_sitter import Language, Parser
    import networkx as nx
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    logging.warning("Tree-sitter not available. SPEED mode will be limited.")

# LSP for PRECISION mode
try:
    from pygls.lsp.client import BaseLanguageClient
    LSP_AVAILABLE = True
except ImportError:
    LSP_AVAILABLE = False
    logging.warning("pygls not available. PRECISION mode will be limited.")

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of impact analysis.
    
    Attributes:
        impacted_files: List of files affected by the change
        mode_used: Which analysis mode was used
        analysis_time: Time taken for analysis in seconds
        error: Error message if analysis failed
        warnings: List of warning messages
    """
    impacted_files: List[str]
    mode_used: Literal["SPEED", "PRECISION"]
    analysis_time: float
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class SpeedAnalyzer:
    """FR-IA-02: Fast analysis using Tree-sitter + NetworkX.
    
    This analyzer performs text-based AST parsing without requiring a build step.
    
    Performance Target:
        - 10,000 lines of code analyzed in < 5 seconds
    
    Method:
        1. Parse Python files using Tree-sitter
        2. Extract imports to build dependency graph with NetworkX
        3. Traverse graph to find impacted files
    
    Constraints:
        - No build process required
        - Text-based parsing only
        - May have false positives
    
    Example:
        >>> analyzer = SpeedAnalyzer(workspace_path="./src")
        >>> result = analyzer.analyze("src/module.py", "function_name")
        >>> print(result.impacted_files)
        ['src/module.py', 'src/dependent.py']
    """
    
    def __init__(self, workspace_path: str = "."):
        """Initialize SPEED analyzer.
        
        Args:
            workspace_path: Root directory of the workspace
        """
        self.workspace_path = Path(workspace_path)
        self.graph = nx.DiGraph()
        
        if not TREE_SITTER_AVAILABLE:
            raise ImportError(
                "Tree-sitter not installed. Required for SPEED mode.\n"
                "Install with: uv pip install tree-sitter tree-sitter-python"
            )
        
        # Initialize Tree-sitter parser with Python language
        self.parser = Parser(Language(tspython.language()))
        logger.info("SPEED analyzer initialized")
    
    def analyze(
        self,
        changed_file: str,
        changed_symbol: Optional[str] = None
    ) -> AnalysisResult:
        """Perform SPEED mode impact analysis.
        
        Args:
            changed_file: Path to the file that was changed
            changed_symbol: Optional specific symbol (function/class) that changed
            
        Returns:
            AnalysisResult containing list of impacted files and metadata
        """
        start_time = time.time()
        logger.info(f"Starting SPEED analysis for {changed_file}")
        
        try:
            # Build dependency graph from workspace
            self._build_dependency_graph()
            
            # Find all files that depend on the changed file
            impacted = self._find_impacted_files(changed_file, changed_symbol)
            
            analysis_time = time.time() - start_time
            logger.info(
                f"SPEED analysis completed in {analysis_time:.2f}s. "
                f"Found {len(impacted)} impacted files."
            )
            
            return AnalysisResult(
                impacted_files=impacted,
                mode_used="SPEED",
                analysis_time=analysis_time
            )
            
        except Exception as e:
            analysis_time = time.time() - start_time
            logger.error(f"SPEED analysis failed: {str(e)}", exc_info=True)
            return AnalysisResult(
                impacted_files=[],
                mode_used="SPEED",
                analysis_time=analysis_time,
                error=str(e)
            )
    
    def _build_dependency_graph(self):
        """Build dependency graph by parsing all Python files in workspace."""
        logger.debug("Building dependency graph with Tree-sitter...")
        
        # Find all Python files (excluding virtual environments and build dirs)
        python_files = [
            f for f in self.workspace_path.rglob("*.py")
            if not any(part.startswith('.') for part in f.parts)
            and 'venv' not in f.parts
            and '__pycache__' not in f.parts
        ]
        
        logger.debug(f"Found {len(python_files)} Python files to analyze")
        
        for file_path in python_files:
            try:
                with open(file_path, 'rb') as f:
                    source_code = f.read()
                
                # Parse file with Tree-sitter
                tree = self.parser.parse(source_code)
                
                # Extract dependencies (imports)
                self._extract_dependencies(file_path, tree)
                
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")
        
        logger.debug(f"Dependency graph built: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
    
    def _extract_dependencies(self, file_path: Path, tree):
        """Extract import statements from AST to build dependency graph.
        
        Args:
            file_path: Path to the source file
            tree: Tree-sitter AST
        """
        root_node = tree.root_node
        
        # Add file to graph
        file_str = str(file_path.relative_to(self.workspace_path))
        if file_str not in self.graph:
            self.graph.add_node(file_str)
        
        # Find all import statements
        imports = self._find_imports(root_node)
        
        # Add edges for each import
        for imported_module in imports:
            # Try to resolve module to file path
            # This is a simplified resolution - production would be more sophisticated
            possible_file = self._resolve_import_to_file(imported_module)
            if possible_file:
                self.graph.add_edge(file_str, possible_file)
    
    def _find_imports(self, node) -> List[str]:
        """Recursively find all import statements in AST.
        
        Args:
            node: Tree-sitter node to search
            
        Returns:
            List of imported module names
        """
        imports = []
        
        if node.type == 'import_statement':
            # import module
            for child in node.children:
                if child.type == 'dotted_name':
                    imports.append(child.text.decode('utf-8'))
        
        elif node.type == 'import_from_statement':
            # from module import something
            for child in node.children:
                if child.type == 'dotted_name':
                    imports.append(child.text.decode('utf-8'))
        
        # Recursively search children
        for child in node.children:
            imports.extend(self._find_imports(child))
        
        return imports
    
    def _resolve_import_to_file(self, module_name: str) -> Optional[str]:
        """Attempt to resolve a module name to a file path.
        
        Args:
            module_name: Python module name (e.g., 'package.module')
            
        Returns:
            Relative file path if found, None otherwise
        """
        # Convert module name to file path
        # e.g., 'ai_assistant.config' -> 'ai_assistant/config.py'
        possible_path = module_name.replace('.', '/') + '.py'
        full_path = self.workspace_path / possible_path
        
        if full_path.exists():
            return possible_path
        
        # Try __init__.py
        possible_init = module_name.replace('.', '/') + '/__init__.py'
        full_init = self.workspace_path / possible_init
        
        if full_init.exists():
            return possible_init
        
        return None
    
    def _find_impacted_files(
        self,
        changed_file: str,
        changed_symbol: Optional[str] = None
    ) -> List[str]:
        """Find all files that depend on the changed file.
        
        Args:
            changed_file: File that was modified
            changed_symbol: Optional specific symbol that changed
            
        Returns:
            List of impacted file paths
        """
        if changed_file not in self.graph:
            logger.warning(f"{changed_file} not found in dependency graph")
            return [changed_file]
        
        # Find all descendants (files that directly or indirectly import this file)
        try:
            descendants = nx.descendants(self.graph, changed_file)
        except nx.NodeNotFound:
            descendants = set()
        
        # Include the changed file itself
        impacted = [changed_file] + sorted(list(descendants))
        
        logger.debug(f"Found {len(impacted)} impacted files for {changed_file}")
        
        return impacted


class PrecisionAnalyzer:
    """FR-IA-03: Precise analysis using LSP (Language Server Protocol).
    
    This analyzer uses compiler-level analysis for accurate reference finding.
    
    Method:
        - Communicates with Pyright Language Server
        - Uses textDocument/references LSP request
        - Returns compiler-accurate results
    
    Advantages:
        - Highly accurate (compiler-level)
        - Finds all true references
        - No false positives
    
    Disadvantages:
        - Requires build/type checking
        - Slower than SPEED mode
        - May fail if code doesn't compile
    
    Note:
        This is a simplified implementation. Full production implementation
        would start an LSP server process and communicate via JSON-RPC.
    
    Example:
        >>> analyzer = PrecisionAnalyzer(workspace_path="./src")
        >>> result = analyzer.analyze("src/module.py", "function_name")
        >>> print(result.impacted_files)
        ['src/module.py', 'src/caller.py']
    """
    
    def __init__(self, workspace_path: str = "."):
        """Initialize PRECISION analyzer.
        
        Args:
            workspace_path: Root directory of the workspace
        """
        self.workspace_path = Path(workspace_path)
        
        if not LSP_AVAILABLE:
            logger.warning(
                "pygls not installed. PRECISION mode will use simulation.\n"
                "Install with: uv pip install pygls pyright"
            )
        
        logger.info("PRECISION analyzer initialized (using simulation)")
    
    def analyze(
        self,
        changed_file: str,
        changed_symbol: Optional[str] = None
    ) -> AnalysisResult:
        """Perform PRECISION mode impact analysis.
        
        Args:
            changed_file: Path to the file that was changed
            changed_symbol: Optional specific symbol (function/class) that changed
            
        Returns:
            AnalysisResult containing list of impacted files and metadata
        """
        start_time = time.time()
        logger.info(f"Starting PRECISION analysis for {changed_file}")
        
        try:
            # TODO: Full LSP implementation
            # This would:
            # 1. Start Pyright language server
            # 2. Initialize LSP client
            # 3. Send textDocument/references request
            # 4. Parse response to get all reference locations
            # 5. Extract unique file paths
            
            # For now, use simulation
            impacted = self._simulate_lsp_analysis(changed_file, changed_symbol)
            
            analysis_time = time.time() - start_time
            logger.info(
                f"PRECISION analysis completed in {analysis_time:.2f}s. "
                f"Found {len(impacted)} impacted files."
            )
            
            return AnalysisResult(
                impacted_files=impacted,
                mode_used="PRECISION",
                analysis_time=analysis_time,
                warnings=["Using simulated LSP analysis. Full LSP integration pending."]
            )
            
        except Exception as e:
            analysis_time = time.time() - start_time
            logger.error(f"PRECISION analysis failed: {str(e)}", exc_info=True)
            return AnalysisResult(
                impacted_files=[],
                mode_used="PRECISION",
                analysis_time=analysis_time,
                error=str(e)
            )
    
    def _simulate_lsp_analysis(
        self,
        changed_file: str,
        changed_symbol: Optional[str] = None
    ) -> List[str]:
        """Simulate LSP analysis (placeholder for full implementation).
        
        Args:
            changed_file: File that was modified
            changed_symbol: Symbol that changed
            
        Returns:
            List of impacted files (currently just the changed file)
        """
        logger.warning(
            "Using simulated LSP analysis. "
            "Full implementation requires LSP server integration."
        )
        
        # In a real implementation, this would:
        # 1. Initialize LSP client with Pyright server
        # 2. Open the changed file
        # 3. Find the symbol position
        # 4. Send textDocument/references request
        # 5. Collect all reference locations
        # 6. Return unique file paths
        
        # For now, just return the changed file
        # This allows the system to work without full LSP setup
        return [changed_file]