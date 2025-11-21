"""Centralized logging configuration with Rich library.

This module provides beautiful console output with:
- Color-coded log levels
- Distinct styling for AI vs Human messages
- File path highlighting
- Timestamps
"""

import logging
import sys
from typing import Optional
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text

# Custom theme for AI Assistant
CUSTOM_THEME = Theme({
    "ai": "bold cyan",
    "human": "bold green",
    "system": "bold yellow",
    "error": "bold red",
    "success": "bold green",
    "warning": "bold yellow",
    "info": "bold blue",
    "file": "italic magenta",
    "code": "dim white on black",
})

# Global console instance
console = Console(theme=CUSTOM_THEME)


def setup_logging(level: int = logging.INFO) -> None:
    """Configure centralized logging with Rich.
    
    Sets up logging to output to stdout with beautiful formatting.
    Distinguishes between AI and Human messages visually.
    
    Args:
        level: Logging level (default: logging.INFO)
    """
    # Configure Rich handler
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[rich_handler],
        force=True  # Override existing configuration
    )
    
    # Set all loggers to use the same level
    logging.getLogger("ai_assistant").setLevel(level)


def log_ai_message(message: str, title: str = "AI Assistant") -> None:
    """Log an AI assistant message with distinct styling.
    
    Args:
        message: AI response message
        title: Title for the panel (default: "AI Assistant")
    """
    panel = Panel(
        Text(message, style="ai"),
        title=f"🤖 {title}",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)


def log_human_message(message: str, title: str = "User") -> None:
    """Log a human/user message with distinct styling.
    
    Args:
        message: User input message
        title: Title for the panel (default: "User")
    """
    panel = Panel(
        Text(message, style="human"),
        title=f"👤 {title}",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)


def log_system_message(message: str, title: str = "System") -> None:
    """Log a system message.
    
    Args:
        message: System message
        title: Title for the panel (default: "System")
    """
    panel = Panel(
        Text(message, style="system"),
        title=f"⚙️  {title}",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(panel)


def log_code(code: str, language: str = "python", title: str = "Generated Code") -> None:
    """Log code with syntax highlighting.
    
    Args:
        code: Code to display
        language: Programming language (default: "python")
        title: Title for the code block
    """
    from rich.syntax import Syntax
    
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    panel = Panel(
        syntax,
        title=f"💻 {title}",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def log_test_result(success: bool, details: Optional[str] = None) -> None:
    """Log test execution results.
    
    Args:
        success: Whether tests passed
        details: Additional details about the test results
    """
    if success:
        message = "✅ All tests passed!"
        style = "success"
        border_style = "green"
    else:
        message = "❌ Tests failed"
        style = "error"
        border_style = "red"
    
    if details:
        message += f"\n\n{details}"
    
    panel = Panel(
        Text(message, style=style),
        title="🧪 Test Results",
        border_style=border_style,
        padding=(1, 2)
    )
    console.print(panel)


# Auto-configure logging on import
setup_logging()