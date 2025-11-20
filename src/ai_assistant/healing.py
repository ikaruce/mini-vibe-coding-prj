"""Self-Healing Loop for Autonomous Coding and Recovery.

This module implements FR-AC-01, FR-AC-02, and FR-AC-03:
- Code generation and refactoring
- Self-healing loop with max 3 retries
- Automatic test generation

Based on REQUIREMENT.md 대기능2.
"""

from typing import Dict, List, Optional, Literal
from dataclasses import dataclass, field
import subprocess
import tempfile
from pathlib import Path
import logging
import sys
import re

# Import centralized logging setup
from . import utils  # This will configure logging via utils.py

# Docker support (optional)
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    logging.warning("Docker not available. Sandboxed execution disabled.")

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test execution result.
    
    Attributes:
        success: Whether tests passed
        stdout: Standard output from test run
        stderr: Standard error from test run
        errors: Parsed error messages
        returncode: Process return code
    """
    success: bool
    stdout: str
    stderr: str
    errors: List[str]
    returncode: int


@dataclass
class CodeHistory:
    """History of code modifications.
    
    Attributes:
        attempt: Attempt number (0-indexed)
        code: Generated code
        fix_reason: Reason for this modification
        test_result: Test result for this attempt
    """
    attempt: int
    code: str
    fix_reason: Optional[str] = None
    test_result: Optional[TestResult] = None


@dataclass
class HealingResult:
    """Result of self-healing process.
    
    Attributes:
        success: Whether healing succeeded
        final_code: Final generated code
        final_tests: Final generated tests
        retry_count: Number of retries performed
        history: History of all attempts
        error_logs: Accumulated error logs
    """
    success: bool
    final_code: str
    final_tests: str
    retry_count: int
    history: List[CodeHistory] = field(default_factory=list)
    error_logs: List[str] = field(default_factory=list)


class ErrorClassifier:
    """Classify and analyze errors from test execution.
    
    Error Types:
        - syntax: Syntax errors (SyntaxError)
        - import: Import errors (ImportError, ModuleNotFoundError)
        - type: Type-related errors (TypeError, AttributeError)
        - logic: Logic errors (AssertionError)
        - runtime: Other runtime errors
    """
    
    ERROR_PATTERNS = {
        "syntax": [r"SyntaxError", r"IndentationError"],
        "import": [r"ImportError", r"ModuleNotFoundError"],
        "type": [r"TypeError", r"AttributeError", r"NameError"],
        "logic": [r"AssertionError"],
        "runtime": [r"RuntimeError", r"ValueError", r"KeyError"]
    }
    
    @classmethod
    def classify(cls, error_message: str) -> List[str]:
        """Classify error message.
        
        Args:
            error_message: Error message from test execution
            
        Returns:
            List of error types found
        """
        error_types = []
        
        for error_type, patterns in cls.ERROR_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, error_message, re.IGNORECASE):
                    error_types.append(error_type)
                    break
        
        return list(set(error_types)) or ["unknown"]
    
    @classmethod
    def extract_errors(cls, stderr: str) -> List[str]:
        """Extract individual error messages.
        
        Args:
            stderr: Standard error output
            
        Returns:
            List of error messages
        """
        # Split by common error markers
        errors = []
        lines = stderr.split('\n')
        
        current_error = []
        for line in lines:
            # Error indicators
            if any(indicator in line for indicator in [
                "Error:", "FAILED", "ERROR", "Traceback"
            ]):
                if current_error:
                    errors.append('\n'.join(current_error))
                    current_error = []
            
            if line.strip():
                current_error.append(line)
        
        if current_error:
            errors.append('\n'.join(current_error))
        
        return errors


class TestExecutor:
    """Execute tests in Docker container (sandboxed).
    
    This class handles:
    - Writing code to temporary files
    - Running pytest in isolated Docker container
    - Collecting and parsing results
    
    Benefits of Docker execution:
    - Complete isolation from host system
    - Consistent Python environment
    - Safe execution of generated code
    - No dependency conflicts
    """
    
    @staticmethod
    def execute(code: str, tests: str, timeout: int = 30) -> TestResult:
        """Execute tests in Docker container.
        
        Args:
            code: Generated code to test
            tests: Pytest test code
            timeout: Maximum execution time in seconds
            
        Returns:
            TestResult with execution details
        """
        if not DOCKER_AVAILABLE:
            raise ImportError(
                "Docker library not installed. Required for test execution.\n"
                "Install with: uv pip install docker\n"
                "Also ensure Docker Desktop is running."
            )
        
        logger.info("Executing tests in Docker container...")
        
        try:
            client = docker.from_env()
            
            with tempfile.TemporaryDirectory() as tmpdir:
                tmppath = Path(tmpdir)
                
                # Write code and tests
                code_file = tmppath / "generated_code.py"
                test_file = tmppath / "test_generated.py"
                
                logger.info(f"📄 Sandbox directory: {tmpdir}")
                logger.info(f"📝 Code file: {code_file.name}")
                logger.info(f"🧪 Test file: {test_file.name}")
                
                code_file.write_text(code, encoding='utf-8')
                test_file.write_text(tests, encoding='utf-8')
                
                logger.info("✅ Files written to temporary directory")
                
                # Build or get Docker image
                image_name = "ai-assistant-test-runner"
                try:
                    client.images.get(image_name)
                    logger.info(f"Using Docker image: {image_name}")
                except docker.errors.ImageNotFound:
                    logger.info(f"Building Docker image: {image_name}")
                    client.images.build(
                        path="docker/test-runner",
                        tag=image_name,
                        rm=True
                    )
                
                # Run tests in container with timeout handling
                logger.info("Starting Docker container for test execution...")
                
                # Run container in detached mode for timeout control
                container = client.containers.run(
                    image_name,
                    command=["pytest", "/sandbox/test_generated.py", "-v", "--tb=short"],
                    volumes={str(tmppath): {'bind': '/sandbox', 'mode': 'ro'}},
                    working_dir="/sandbox",
                    remove=False,  # Don't auto-remove so we can get logs
                    detach=True,  # Run in background
                    mem_limit="512m",  # Memory limit for safety
                    network_mode="none"  # No network access
                )
                
                # Wait for container to finish with timeout
                try:
                    exit_code = container.wait(timeout=timeout)
                    logger.info(f"Docker container finished with exit code: {exit_code}")
                except Exception as timeout_error:
                    logger.error(f"Container timeout after {timeout}s")
                    container.stop(timeout=1)
                    container.remove()
                    return TestResult(
                        success=False,
                        stdout="",
                        stderr=f"Container execution timeout after {timeout} seconds",
                        errors=["timeout"],
                        returncode=-1
                    )
                
                # Get container logs
                output = container.logs(stdout=True, stderr=True).decode('utf-8')
                
                # Remove container
                container.remove()
                
                logger.info("Docker execution completed")
                
                # Check if tests passed
                success = "passed" in output and "FAILED" not in output
                errors = ErrorClassifier.extract_errors(output)
                
                logger.info(f"Tests {'passed ✅' if success else 'failed ❌'}")
                if not success:
                    logger.info(f"Errors detected: {len(errors)}")
                
                return TestResult(
                    success=success,
                    stdout=output,
                    stderr="" if success else output,
                    errors=errors,
                    returncode=0 if success else 1
                )
                
        except docker.errors.ContainerError as e:
            logger.error(f"Docker container error: {e.exit_status}")
            logger.error(f"Output: {e.stderr.decode('utf-8') if e.stderr else 'No output'}")
            return TestResult(
                success=False,
                stdout="",
                stderr=e.stderr.decode('utf-8') if e.stderr else str(e),
                errors=[str(e)],
                returncode=e.exit_status
            )
        except docker.errors.DockerException as e:
            logger.error(f"Docker error: {str(e)}")
            logger.error("Make sure Docker Desktop is running")
            return TestResult(
                success=False,
                stdout="",
                stderr=f"Docker not available: {str(e)}",
                errors=[str(e)],
                returncode=-1
            )
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return TestResult(
                success=False,
                stdout="",
                stderr=str(e),
                errors=[str(e)],
                returncode=-1
            )


class SelfHealer:
    """FR-AC-02: Self-Healing Loop.
    
    Process Flow:
        1. Execute: Run tests on generated code
        2. Analyze: Parse error messages
        3. Patch: Generate fix using LLM
        4. Retry: Repeat up to max_retries times
    
    Attributes:
        llm: Language model for code generation
        max_retries: Maximum number of retry attempts (default: 3)
    """
    
    def __init__(self, llm, max_retries: int = 3):
        """Initialize Self-Healer.
        
        Args:
            llm: LangChain LLM instance
            max_retries: Maximum retry attempts
        """
        self.llm = llm
        self.max_retries = max_retries
        self.executor = TestExecutor()
    
    def heal(
        self,
        code: str,
        tests: str,
        original_request: str
    ) -> HealingResult:
        """FR-AC-02: Perform self-healing loop.
        
        Args:
            code: Initially generated code
            tests: Generated tests
            original_request: Original user request
            
        Returns:
            HealingResult with final code and history
        """
        logger.info("Starting self-healing process...")
        
        current_code = code
        current_tests = tests
        history: List[CodeHistory] = []
        error_logs: List[str] = []
        retry_count = 0
        
        # Initial attempt
        test_result = self.executor.execute(current_code, current_tests)
        history.append(CodeHistory(
            attempt=0,
            code=current_code,
            test_result=test_result
        ))
        
        if test_result.success:
            logger.info("Initial code passed all tests!")
            return HealingResult(
                success=True,
                final_code=current_code,
                final_tests=current_tests,
                retry_count=0,
                history=history,
                error_logs=error_logs
            )
        
        # Self-healing loop
        while retry_count < self.max_retries and not test_result.success:
            retry_count += 1
            logger.info(f"Retry attempt {retry_count}/{self.max_retries}")
            
            # Analyze errors
            error_types = []
            for error in test_result.errors:
                error_types.extend(ErrorClassifier.classify(error))
            
            error_summary = f"Attempt {retry_count}: {', '.join(set(error_types))}"
            error_logs.append(error_summary)
            logger.info(f"Error analysis: {error_summary}")
            
            # Generate fix
            current_code = self._generate_fix(
                code=current_code,
                tests=current_tests,
                error_message=test_result.stderr,
                error_types=error_types,
                original_request=original_request,
                attempt=retry_count
            )
            
            # Execute tests again
            test_result = self.executor.execute(current_code, current_tests)
            
            # Record history
            history.append(CodeHistory(
                attempt=retry_count,
                code=current_code,
                fix_reason=error_summary,
                test_result=test_result
            ))
            
            if test_result.success:
                logger.info(f"✅ Self-healing succeeded after {retry_count} retries!")
                return HealingResult(
                    success=True,
                    final_code=current_code,
                    final_tests=current_tests,
                    retry_count=retry_count,
                    history=history,
                    error_logs=error_logs
                )
        
        # Max retries exceeded
        logger.warning(f"❌ Self-healing failed after {retry_count} retries")
        return HealingResult(
            success=False,
            final_code=current_code,
            final_tests=current_tests,
            retry_count=retry_count,
            history=history,
            error_logs=error_logs
        )
    
    def _generate_fix(
        self,
        code: str,
        tests: str,
        error_message: str,
        error_types: List[str],
        original_request: str,
        attempt: int
    ) -> str:
        """Generate code fix using LLM.
        
        Args:
            code: Current code
            tests: Test code
            error_message: Error message from test execution
            error_types: Classified error types
            original_request: Original user request
            attempt: Current attempt number
            
        Returns:
            Fixed code
        """
        prompt = f"""Fix the following Python code that has errors.

Original Request: {original_request}

Current Code:
```python
{code}
```

Tests:
```python
{tests}
```

Error Types: {', '.join(error_types)}

Error Message:
```
{error_message}
```

Attempt: {attempt}/{self.max_retries}

Fix Requirements:
1. Identify and fix the root cause of the error
2. Ensure the tests pass
3. Don't modify working parts
4. Follow PEP8 and use type hints
5. Prevent the same error from recurring

Return ONLY the fixed code (comments allowed):
"""
        
        response = self.llm.invoke(prompt)
        
        # Extract code from response
        fixed_code = self._extract_code(response.content)
        
        return fixed_code
    
    @staticmethod
    def _extract_code(response: str) -> str:
        """Extract code from LLM response.
        
        Args:
            response: LLM response text
            
        Returns:
            Extracted Python code
        """
        # Try to extract from code blocks
        code_block_pattern = r"```python\n(.*?)\n```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # Try without language specifier
        code_block_pattern = r"```\n(.*?)\n```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # Return as-is if no code blocks found
        return response.strip()


class CodeGenerator:
    """FR-AC-01: Code generation and refactoring.
    
    Generates code based on user request and impacted files.
    """
    
    def __init__(self, llm):
        """Initialize code generator.
        
        Args:
            llm: LangChain LLM instance
        """
        self.llm = llm
    
    def generate(
        self,
        request: str,
        impacted_files: List[str],
        context: Optional[str] = None
    ) -> str:
        """Generate code based on request.
        
        Args:
            request: User request description
            impacted_files: List of files to modify
            context: Additional context
            
        Returns:
            Generated Python code
        """
        logger.info(f"Generating code for request: {request}")
        
        prompt = f"""Generate Python code based on the following request:

Request: {request}

Impacted Files:
{chr(10).join(f'- {f}' for f in impacted_files)}

{f"Additional Context: {context}" if context else ""}

Requirements:
1. Follow PEP8 style guide
2. Use Google Style docstrings
3. Include type hints
4. Include error handling
5. Make it testable with unit tests

Return ONLY the generated code:
"""
        
        response = self.llm.invoke(prompt)
        
        # Extract code
        code = SelfHealer._extract_code(response.content)
        
        return code


class TestGenerator:
    """FR-AC-03: Automatic test generation.
    
    Generates pytest unit tests for generated code.
    """
    
    def __init__(self, llm):
        """Initialize test generator.
        
        Args:
            llm: LangChain LLM instance
        """
        self.llm = llm
    
    def generate(self, code: str, request: str) -> str:
        """Generate pytest tests for code.
        
        Args:
            code: Code to generate tests for
            request: Original user request
            
        Returns:
            Generated pytest test code
        """
        logger.info("Generating unit tests...")
        
        prompt = f"""Generate pytest unit tests for the following code:

Original Request: {request}

Code to Test:
```python
{code}
```

Test Requirements:
1. Use pytest framework
2. DO NOT import from generated_code - copy the code into the test file
3. Test all functions/methods
4. Include edge cases
5. Use pytest-mock for mocking if needed
6. Use clear, descriptive test names

IMPORTANT: The test file should be self-contained.
Copy the function(s) from the code above directly into your test file,
then write tests for them. Do NOT use import statements.

Example format:
```python
# Copy the function here
def factorial(n):
    if n == 0:
        return 1
    return n * factorial(n - 1)

# Then test it
def test_factorial():
    assert factorial(0) == 1
    assert factorial(5) == 120
```

Return ONLY the self-contained test code:
"""
        
        response = self.llm.invoke(prompt)
        
        # Extract code
        tests = SelfHealer._extract_code(response.content)
        
        return tests