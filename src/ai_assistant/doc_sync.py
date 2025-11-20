"""Document Synchronization Module (FR-DS-01).

This module analyzes code changes and proposes documentation updates for:
- Python Docstrings (Google Style)
- README.md
- API documentation (FastAPI/Swagger)

Based on REQUIREMENT.md 대기능3.
"""

from typing import List, Optional, Literal
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import logging
import re
import ast

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of documentation that can be synchronized."""
    DOCSTRING = "docstring"
    README = "readme"
    API_DOC = "api_doc"


@dataclass
class DocumentChange:
    """Proposed documentation change.
    
    Attributes:
        doc_type: Type of document
        file_path: Path to the file
        location: Specific location (e.g., function name, line number)
        current_content: Current documentation
        proposed_content: Proposed new documentation
        reason: Explanation for the change
        confidence: AI confidence score (0.0-1.0)
    """
    doc_type: DocumentType
    file_path: str
    location: str
    current_content: str
    proposed_content: str
    reason: str
    confidence: float = 0.8


@dataclass
class DocumentSyncResult:
    """Result of documentation synchronization analysis.
    
    Attributes:
        changes_detected: Whether any changes were detected
        proposed_changes: List of proposed changes
        analysis_summary: Summary of analysis
    """
    changes_detected: bool
    proposed_changes: List[DocumentChange] = field(default_factory=list)
    analysis_summary: str = ""


class DocstringExtractor:
    """Extract and analyze docstrings from Python code.
    
    Uses AST parsing to extract function/class signatures and docstrings.
    """
    
    @staticmethod
    def extract_from_code(code: str) -> List[dict]:
        """Extract all docstrings and signatures from code.
        
        Args:
            code: Python source code
            
        Returns:
            List of dicts with function/class info and docstrings
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Failed to parse code: {e}")
            return []
        
        definitions = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                docstring = ast.get_docstring(node)
                
                # Extract function signature
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    signature = DocstringExtractor._get_function_signature(node)
                else:
                    signature = f"class {node.name}"
                
                definitions.append({
                    "type": "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class",
                    "name": node.name,
                    "signature": signature,
                    "docstring": docstring or "",
                    "line_number": node.lineno
                })
        
        return definitions
    
    @staticmethod
    def _get_function_signature(node: ast.FunctionDef) -> str:
        """Extract function signature as string.
        
        Args:
            node: AST FunctionDef node
            
        Returns:
            Function signature string
        """
        params = []
        
        for arg in node.args.args:
            param = arg.arg
            if arg.annotation:
                param += f": {ast.unparse(arg.annotation)}"
            params.append(param)
        
        signature = f"def {node.name}({', '.join(params)})"
        
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"
        
        return signature


class DocstringGenerator:
    """Generate Google-style docstrings using LLM."""
    
    def __init__(self, llm):
        """Initialize docstring generator.
        
        Args:
            llm: LangChain LLM instance
        """
        self.llm = llm
    
    def generate(
        self,
        function_signature: str,
        function_body: str,
        current_docstring: Optional[str] = None
    ) -> str:
        """Generate or update docstring.
        
        Args:
            function_signature: Function signature
            function_body: Function implementation
            current_docstring: Existing docstring (if any)
            
        Returns:
            Generated Google-style docstring
        """
        logger.info(f"Generating docstring for: {function_signature}")
        
        prompt = f"""Generate a Google-style docstring for the following Python function.

Function Signature:
{function_signature}

Function Body:
{function_body}

{f"Current Docstring:\n{current_docstring}\n" if current_docstring else ""}

Requirements:
1. Use Google Style docstring format
2. Include Args, Returns, Raises sections as needed
3. Be concise but informative
4. Include type information in Args section
5. Add usage examples if the function is complex

Return ONLY the docstring content (without triple quotes):
"""
        
        response = self.llm.invoke(prompt)
        
        return response.content.strip()


class ReadmeAnalyzer:
    """Analyze README and propose updates based on code changes."""
    
    def __init__(self, llm):
        """Initialize README analyzer.
        
        Args:
            llm: LangChain LLM instance
        """
        self.llm = llm
    
    def analyze(
        self,
        readme_path: str,
        code_changes_summary: str
    ) -> Optional[DocumentChange]:
        """Analyze if README needs updates.
        
        Args:
            readme_path: Path to README.md
            code_changes_summary: Summary of code changes
            
        Returns:
            DocumentChange if update needed, None otherwise
        """
        logger.info("Analyzing README for potential updates...")
        
        # Read current README
        try:
            readme_content = Path(readme_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            logger.warning(f"README not found: {readme_path}")
            return None
        
        # Ask LLM if updates are needed
        prompt = f"""Analyze if the README needs updates based on code changes.

Current README:
{readme_content[:2000]}  # First 2000 chars
...

Code Changes Summary:
{code_changes_summary}

Task:
1. Determine if README needs updates
2. Identify which sections need changes
3. If updates needed, propose specific changes

Return your analysis in this format:
NEEDS_UPDATE: yes/no
REASON: <explanation>
PROPOSED_CHANGES: <specific changes>
"""
        
        response = self.llm.invoke(prompt)
        content = response.content
        
        # Parse response
        needs_update = "NEEDS_UPDATE: yes" in content.lower()
        
        if not needs_update:
            logger.info("README is up to date")
            return None
        
        # Extract proposed changes
        reason_match = re.search(r"REASON:\s*(.+?)(?:PROPOSED|$)", content, re.DOTALL)
        changes_match = re.search(r"PROPOSED_CHANGES:\s*(.+)", content, re.DOTALL)
        
        reason = reason_match.group(1).strip() if reason_match else "Code changes detected"
        proposed = changes_match.group(1).strip() if changes_match else content
        
        return DocumentChange(
            doc_type=DocumentType.README,
            file_path=readme_path,
            location="README.md",
            current_content=readme_content,
            proposed_content=proposed,
            reason=reason,
            confidence=0.7
        )


class DocumentSynchronizer:
    """FR-DS-01: Main document synchronization coordinator.
    
    Analyzes code changes and proposes documentation updates across
    multiple documentation types.
    """
    
    def __init__(self, llm):
        """Initialize document synchronizer.
        
        Args:
            llm: LangChain LLM instance
        """
        self.llm = llm
        self.docstring_generator = DocstringGenerator(llm)
        self.readme_analyzer = ReadmeAnalyzer(llm)
    
    def analyze_and_propose(
        self,
        code: str,
        changed_files: List[str],
        readme_path: str = "README.md"
    ) -> DocumentSyncResult:
        """FR-DS-01: Analyze code changes and propose doc updates.
        
        Args:
            code: Modified/generated code
            changed_files: List of files that changed
            readme_path: Path to README file
            
        Returns:
            DocumentSyncResult with proposed changes
        """
        logger.info("Starting documentation synchronization analysis...")
        
        proposed_changes: List[DocumentChange] = []
        
        # 1. Analyze Docstrings
        docstring_changes = self._analyze_docstrings(code, changed_files)
        proposed_changes.extend(docstring_changes)
        
        # 2. Analyze README
        if changed_files:
            code_summary = self._summarize_code_changes(code, changed_files)
            readme_change = self.readme_analyzer.analyze(readme_path, code_summary)
            if readme_change:
                proposed_changes.append(readme_change)
        
        # 3. Generate summary
        summary = self._generate_summary(proposed_changes)
        
        logger.info(f"Documentation analysis complete. Found {len(proposed_changes)} potential updates.")
        
        return DocumentSyncResult(
            changes_detected=len(proposed_changes) > 0,
            proposed_changes=proposed_changes,
            analysis_summary=summary
        )
    
    def _analyze_docstrings(self, code: str, changed_files: List[str]) -> List[DocumentChange]:
        """Analyze docstrings in the code.
        
        Args:
            code: Source code to analyze
            changed_files: Files that changed
            
        Returns:
            List of proposed docstring changes
        """
        logger.info("Analyzing docstrings...")
        
        changes = []
        
        # Extract all definitions from code
        definitions = DocstringExtractor.extract_from_code(code)
        
        for defn in definitions:
            # Check if docstring is missing or outdated
            if not defn['docstring'] or len(defn['docstring']) < 20:
                logger.info(f"Missing or insufficient docstring for: {defn['name']}")
                
                # Generate new docstring
                new_docstring = self.docstring_generator.generate(
                    function_signature=defn['signature'],
                    function_body="",  # We don't have the full body here
                    current_docstring=defn['docstring']
                )
                
                changes.append(DocumentChange(
                    doc_type=DocumentType.DOCSTRING,
                    file_path=changed_files[0] if changed_files else "unknown",
                    location=f"Line {defn['line_number']}: {defn['name']}",
                    current_content=defn['docstring'],
                    proposed_content=new_docstring,
                    reason=f"{'Missing' if not defn['docstring'] else 'Insufficient'} docstring",
                    confidence=0.8
                ))
        
        return changes
    
    def _summarize_code_changes(self, code: str, changed_files: List[str]) -> str:
        """Summarize code changes for README analysis.
        
        Args:
            code: Modified code
            changed_files: List of changed files
            
        Returns:
            Summary string
        """
        definitions = DocstringExtractor.extract_from_code(code)
        
        summary = f"Changed files: {', '.join(changed_files)}\n\n"
        summary += f"Modified/Added functions:\n"
        
        for defn in definitions:
            summary += f"- {defn['signature']}\n"
        
        return summary
    
    def _generate_summary(self, changes: List[DocumentChange]) -> str:
        """Generate summary of proposed changes.
        
        Args:
            changes: List of proposed changes
            
        Returns:
            Summary string
        """
        if not changes:
            return "No documentation updates needed."
        
        summary = f"Found {len(changes)} documentation updates:\n\n"
        
        by_type = {}
        for change in changes:
            doc_type = change.doc_type.value
            by_type.setdefault(doc_type, []).append(change)
        
        for doc_type, type_changes in by_type.items():
            summary += f"- {doc_type.upper()}: {len(type_changes)} changes\n"
        
        return summary