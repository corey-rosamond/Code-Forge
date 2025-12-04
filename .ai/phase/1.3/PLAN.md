# Phase 1.3: Basic REPL Shell - Architectural Plan

**Phase:** 1.3
**Name:** Basic REPL Shell
**Dependencies:** Phase 1.1, Phase 1.2

---

## Architectural Overview

The REPL follows the Model-View-Controller pattern adapted for terminal applications. It uses async/await for non-blocking input handling.

---

## Design Patterns Applied

### MVC Pattern
- **Model**: Application state (mode, tokens, status)
- **View**: Terminal rendering (Rich, status bar)
- **Controller**: Input handling (prompt_toolkit)

### Command Pattern (Preparation)
- Input is captured but not processed
- Placeholder for future command routing
- Clean separation of input capture from processing

### Observer Pattern
- Status bar observes state changes
- Configuration changes update display
- Event-driven UI updates

---

## Class Design

### Core REPL Class

```python
import asyncio
from typing import Callable, Any
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style

from opencode.config import opencodeConfig
from opencode.core.logging import get_logger

logger = get_logger("repl")

class InputHandler:
    """Handles user input with history and key bindings."""

    def __init__(self, history_path: Path):
        self._history = FileHistory(str(history_path))
        self._bindings = self._create_bindings()
        self._session = PromptSession(
            history=self._history,
            key_bindings=self._bindings,
            enable_history_search=True,
        )

    def _create_bindings(self) -> KeyBindings:
        """Create key bindings."""
        kb = KeyBindings()

        @kb.add('escape')
        def _(event):
            """Clear current input."""
            event.current_buffer.reset()

        @kb.add('c-l')
        def _(event):
            """Clear screen."""
            event.app.renderer.clear()

        return kb

    async def get_input(self, prompt: str, multiline: bool = True) -> str | None:
        """Get input from user."""
        try:
            return await self._session.prompt_async(
                prompt,
                multiline=multiline,
            )
        except EOFError:
            return None
        except KeyboardInterrupt:
            raise


class OutputRenderer:
    """Renders output to the terminal."""

    def __init__(self, console: Console, theme: dict[str, str]):
        self._console = console
        self._theme = theme

    def print(self, content: str, style: str | None = None) -> None:
        """Print content to console."""
        self._console.print(content, style=style)

    def print_markdown(self, content: str) -> None:
        """Print markdown content."""
        from rich.markdown import Markdown
        self._console.print(Markdown(content))

    def print_code(self, code: str, language: str = "python") -> None:
        """Print syntax-highlighted code."""
        from rich.syntax import Syntax
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        self._console.print(syntax)

    def print_panel(self, content: str, title: str = "") -> None:
        """Print content in a panel."""
        self._console.print(Panel(content, title=title))

    def print_error(self, message: str) -> None:
        """Print error message."""
        self._console.print(f"[red]Error:[/red] {message}")

    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self._console.print(f"[yellow]Warning:[/yellow] {message}")

    def clear(self) -> None:
        """Clear the screen."""
        self._console.clear()


class StatusBar:
    """Status bar displayed at bottom of terminal."""

    def __init__(self, config: OpenCodeConfig):
        self._config = config
        self._model = config.model.default
        self._tokens_used = 0
        self._tokens_max = 128000  # Placeholder
        self._mode = "Normal"
        self._status = "Ready"
        self._visible = config.display.status_line

    def set_model(self, model: str) -> None:
        """Update current model."""
        self._model = model

    def set_tokens(self, used: int, max_tokens: int) -> None:
        """Update token counts."""
        self._tokens_used = used
        self._tokens_max = max_tokens

    def set_mode(self, mode: str) -> None:
        """Update operating mode."""
        self._mode = mode

    def set_status(self, status: str) -> None:
        """Update status text."""
        self._status = status

    def render(self, width: int) -> str:
        """Render status bar to string."""
        if not self._visible:
            return ""

        left = f" {self._model}"
        center = f"Tokens: {self._tokens_used:,}/{self._tokens_max:,}"
        right = f"{self._mode} | {self._status} "

        # Calculate padding
        total_content = len(left) + len(center) + len(right)
        if total_content >= width:
            # Truncate if too wide
            return f"{left[:width//3]}...{right[-(width//3):]}"

        left_pad = (width - len(center)) // 2 - len(left)
        right_pad = width - len(left) - left_pad - len(center) - len(right)

        return f"{left}{' ' * left_pad}{center}{' ' * right_pad}{right}"


class OpenCodeREPL:
    """Main REPL application."""

    def __init__(self, config: OpenCodeConfig):
        self._config = config
        self._console = Console(force_terminal=True)
        self._input = InputHandler(self._get_history_path())
        self._output = OutputRenderer(self._console, self._get_theme())
        self._status = StatusBar(config)
        self._running = False
        self._callbacks: list[Callable[[str], Any]] = []

    def _get_history_path(self) -> Path:
        """Get path for command history file."""
        return Path.home() / ".opencode" / "history"

    def _get_theme(self) -> dict[str, str]:
        """Get theme colors based on config."""
        if self._config.display.theme == "light":
            return LIGHT_THEME
        return DARK_THEME

    def _get_prompt(self) -> str:
        """Generate prompt string."""
        return "> "

    def _show_welcome(self) -> None:
        """Display welcome message."""
        from opencode import __version__
        import os

        welcome = f"""
[bold blue]OpenCode[/bold blue] v{__version__}
AI-powered CLI Development Assistant

[dim]Directory:[/dim] {os.getcwd()}
[dim]Type /help for commands, ? for shortcuts[/dim]
"""
        self._output.print(welcome.strip())
        self._output.print("")

    def _show_shortcuts(self) -> None:
        """Display keyboard shortcuts."""
        shortcuts = """
[bold]Keyboard Shortcuts[/bold]

[cyan]Esc[/cyan]       Cancel current input
[cyan]Ctrl+C[/cyan]    Interrupt operation
[cyan]Ctrl+D[/cyan]    Exit (on empty input)
[cyan]Ctrl+L[/cyan]    Clear screen
[cyan]Ctrl+R[/cyan]    Search history
[cyan]↑/↓[/cyan]       Navigate history
[cyan]Shift+Enter[/cyan] New line (multiline)
"""
        self._output.print(shortcuts.strip())

    def on_input(self, callback: Callable[[str], Any]) -> None:
        """Register callback for input processing."""
        self._callbacks.append(callback)

    async def _process_input(self, text: str) -> None:
        """Process user input through callbacks."""
        if not self._callbacks:
            # Default behavior: echo
            self._output.print(f"[dim]Received:[/dim] {text}")
            return

        for callback in self._callbacks:
            result = callback(text)
            if asyncio.iscoroutine(result):
                await result

    async def run(self) -> int:
        """Run the REPL loop."""
        self._running = True
        self._show_welcome()

        while self._running:
            try:
                # Show status bar
                if self._config.display.status_line:
                    width = self._console.width
                    status = self._status.render(width)
                    # Status bar rendering handled by prompt_toolkit bottom_toolbar

                # Get input
                user_input = await self._input.get_input(self._get_prompt())

                if user_input is None:  # Ctrl+D / EOF
                    self._output.print("\n[dim]Goodbye![/dim]")
                    break

                text = user_input.strip()
                if not text:
                    continue

                # Check for shortcuts help
                if text == "?":
                    self._show_shortcuts()
                    continue

                # Process input
                await self._process_input(text)

            except KeyboardInterrupt:
                self._output.print("\n[dim]Interrupted[/dim]")
                continue
            except Exception as e:
                logger.exception("REPL error")
                self._output.print_error(str(e))

        self._running = False
        return 0

    def stop(self) -> None:
        """Stop the REPL loop."""
        self._running = False


# Theme definitions
DARK_THEME = {
    "background": "#1a1b26",
    "foreground": "#c0caf5",
    "accent": "#7aa2f7",
    "success": "#9ece6a",
    "warning": "#e0af68",
    "error": "#f7768e",
    "dim": "#565f89",
    "status_bar_bg": "#24283b",
    "status_bar_fg": "#c0caf5",
}

LIGHT_THEME = {
    "background": "#f5f5f5",
    "foreground": "#1a1b26",
    "accent": "#2563eb",
    "success": "#22c55e",
    "warning": "#eab308",
    "error": "#ef4444",
    "dim": "#6b7280",
    "status_bar_bg": "#e5e7eb",
    "status_bar_fg": "#1a1b26",
}
```

### CLI Main Integration

```python
# src/opencode/cli/main.py updates
import asyncio
from opencode.config import ConfigLoader
from opencode.cli.repl import opencodeREPL

def main() -> int:
    """Main entry point for OpenCode CLI."""
    args = sys.argv[1:]

    if "--version" in args or "-v" in args:
        print(f"opencode {__version__}")
        return 0

    if "--help" in args or "-h" in args:
        print_help()
        return 0

    # Load configuration
    config_loader = ConfigLoader()
    config = config_loader.load_all()

    # Start REPL
    repl = OpenCodeREPL(config)
    return asyncio.run(repl.run())
```

---

## Implementation Order

1. Create `src/opencode/cli/repl.py` with core classes
2. Create `src/opencode/cli/themes.py` with theme definitions
3. Create `src/opencode/cli/status.py` with StatusBar
4. Update `src/opencode/cli/main.py` to use REPL
5. Create history directory on first run
6. Write unit tests for each component
7. Write integration test for full REPL flow

---

## File Structure

```
src/opencode/cli/
├── __init__.py       # Exports
├── main.py           # Entry point (updated)
├── repl.py           # OpenCodeREPL, InputHandler, OutputRenderer
├── themes.py         # Theme definitions
└── status.py         # StatusBar

tests/unit/cli/
├── __init__.py
├── test_repl.py
├── test_status.py
└── test_themes.py
```

---

## Quality Gates

Before completing Phase 1.3:
- [ ] REPL starts and accepts input
- [ ] History persists between sessions
- [ ] All keyboard shortcuts work
- [ ] Status bar renders correctly
- [ ] Both themes work
- [ ] Screen clear works
- [ ] Clean exit on Ctrl+D
- [ ] Graceful interrupt on Ctrl+C
- [ ] Tests pass with ≥90% coverage
- [ ] `mypy --strict` passes
- [ ] `ruff check` passes
