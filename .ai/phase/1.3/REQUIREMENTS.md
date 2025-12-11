# Phase 1.3: Basic REPL Shell - Requirements

**Phase:** 1.3
**Name:** Basic REPL Shell
**Status:** Not Started
**Dependencies:** Phase 1.1 (Project Foundation), Phase 1.2 (Configuration System)

---

## Overview

This phase implements the basic Read-Eval-Print Loop (REPL) shell that provides the interactive command-line interface. This is the foundation for all user interaction.

---

## Functional Requirements

### FR-1.3.1: REPL Loop
- Start interactive prompt when `forge` runs without arguments
- Accept user input with multiline support
- Display welcome message on startup
- Handle graceful exit (Ctrl+D, Ctrl+C)
- Return to prompt after each interaction

### FR-1.3.2: Input Handling
- Single-line input with Enter to submit
- Multiline input with Shift+Enter to continue
- Input history navigation with Up/Down arrows
- Reverse search with Ctrl+R
- Clear input with Ctrl+U
- Clear screen with Ctrl+L

### FR-1.3.3: Output Display
- Stream output character by character (prepare for AI streaming)
- Syntax highlighting for code blocks
- Markdown rendering in terminal
- Progress indicators for long operations
- Color-coded output (errors in red, info in blue, etc.)

### FR-1.3.4: Status Bar
- Display at bottom of terminal
- Show current model name
- Show token usage (placeholder for Phase 5.2)
- Show operating mode (Normal/Plan/Read-Only)
- Show connection status

### FR-1.3.5: Basic Keyboard Shortcuts
- Esc: Cancel current input
- Ctrl+C: Interrupt operation
- Ctrl+D: Exit (on empty input)
- Ctrl+L: Clear screen
- ?: Show keyboard shortcuts help

### FR-1.3.6: Welcome Screen
- Show application name and version
- Show current working directory
- Show loaded configuration path
- Show help hint ("/help for commands")

### FR-1.3.7: Theme Support
- Dark theme (default)
- Light theme (from config)
- Consistent color palette
- Readable in common terminals

---

## Non-Functional Requirements

### NFR-1.3.1: Performance
- Input latency < 10ms
- Smooth cursor movement
- No flickering on redraw
- Efficient screen updates

### NFR-1.3.2: Compatibility
- Works in standard terminals (bash, zsh)
- Works in VS Code integrated terminal
- Works over SSH
- Minimum 80x24 terminal size
- Graceful degradation for limited terminals

### NFR-1.3.3: Accessibility
- Works without mouse
- Clear visual hierarchy
- Readable default colors
- Screen reader compatible (basic)

---

## Technical Specifications

### Technology Stack
- **Rich**: Terminal formatting, syntax highlighting, markdown
- **Textual**: TUI application framework
- **prompt_toolkit**: Advanced input handling, history, completion

### REPL Architecture

```python
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings

class Code-ForgeREPL:
    """Main REPL interface for Code-Forge."""

    def __init__(self, config: Code-ForgeConfig):
        self._config = config
        self._console = Console(theme=self._get_theme())
        self._session = PromptSession(
            history=FileHistory(self._history_path),
            key_bindings=self._create_key_bindings(),
            multiline=True,
        )
        self._running = False

    async def run(self) -> int:
        """Run the REPL loop."""
        self._running = True
        self._show_welcome()

        while self._running:
            try:
                user_input = await self._get_input()
                if user_input is None:  # Ctrl+D
                    break
                if not user_input.strip():
                    continue

                await self._process_input(user_input)

            except KeyboardInterrupt:
                self._console.print("\n[dim]Interrupted[/dim]")
                continue

        return 0

    async def _get_input(self) -> str | None:
        """Get input from user with prompt."""
        try:
            return await self._session.prompt_async(
                self._get_prompt(),
                multiline=True,
            )
        except EOFError:
            return None

    async def _process_input(self, text: str) -> None:
        """Process user input."""
        # Placeholder - will route to agent in Phase 3.2
        self._console.print(f"[dim]Received: {text}[/dim]")
```

### Key Bindings

```python
def _create_key_bindings(self) -> KeyBindings:
    """Create key bindings for the REPL."""
    bindings = KeyBindings()

    @bindings.add('escape')
    def _(event):
        """Cancel current input."""
        event.current_buffer.reset()

    @bindings.add('c-l')
    def _(event):
        """Clear screen."""
        event.app.renderer.clear()

    @bindings.add('c-c')
    def _(event):
        """Raise KeyboardInterrupt."""
        raise KeyboardInterrupt

    @bindings.add('?')
    def _(event):
        """Show help."""
        # Only if buffer is empty
        if not event.current_buffer.text:
            self._show_shortcuts()

    return bindings
```

### Status Bar

```python
class StatusBar:
    """Status bar at bottom of terminal."""

    def __init__(self, config: Code-ForgeConfig):
        self._config = config
        self._model = config.model.default
        self._tokens = (0, 0)  # (used, max)
        self._mode = "Normal"
        self._status = "Ready"

    def render(self) -> str:
        """Render status bar."""
        left = f" {self._model}"
        center = f"Tokens: {self._tokens[0]}/{self._tokens[1]}"
        right = f"{self._mode} | {self._status} "

        # Calculate spacing
        width = get_terminal_size().columns
        # ... formatting logic

        return f"[status_bar]{left}{center:^}{right}[/status_bar]"
```

### Theme Configuration

```python
DARK_THEME = {
    "background": "#1a1b26",
    "foreground": "#c0caf5",
    "accent": "#7aa2f7",
    "success": "#9ece6a",
    "warning": "#e0af68",
    "error": "#f7768e",
    "dim": "#565f89",
    "status_bar": "#24283b",
}

LIGHT_THEME = {
    "background": "#f5f5f5",
    "foreground": "#1a1b26",
    "accent": "#2563eb",
    "success": "#22c55e",
    "warning": "#eab308",
    "error": "#ef4444",
    "dim": "#6b7280",
    "status_bar": "#e5e7eb",
}
```

---

## Acceptance Criteria

### Definition of Done

- [ ] REPL starts when running `forge` without arguments
- [ ] Welcome message displays correctly
- [ ] User can type and submit input
- [ ] Multiline input works with Shift+Enter
- [ ] Input history works with Up/Down arrows
- [ ] Ctrl+D exits cleanly
- [ ] Ctrl+C interrupts and returns to prompt
- [ ] Ctrl+L clears screen
- [ ] Status bar displays at bottom
- [ ] Dark theme renders correctly
- [ ] Light theme renders correctly (via config)
- [ ] Syntax highlighting works for code
- [ ] Tests achieve ≥90% coverage

### Verification Commands

```bash
# 1. Start REPL
forge
# Expected: Welcome screen, prompt appears

# 2. Test input
> Hello world
# Expected: Shows received message

# 3. Test multiline (Shift+Enter)
> Line 1
  Line 2
  Line 3
# Expected: All three lines sent as one input

# 4. Test history
# Press Up arrow
# Expected: Previous input appears

# 5. Test Ctrl+L
# Press Ctrl+L
# Expected: Screen clears

# 6. Test Ctrl+D
# Press Ctrl+D
# Expected: Clean exit

# 7. Run tests
pytest tests/unit/cli/ -v --cov=forge.cli
```

---

## Out of Scope

The following are NOT part of Phase 1.3:
- AI model integration (Phase 3.1, 3.2)
- Slash command processing (Phase 6.1)
- Tool execution (Phase 2.x)
- Permission prompts (Phase 4.1)
- Session persistence (Phase 5.1)
- Image/file paste support (Phase 8.2)

---

## Notes

This phase creates the shell without the AI brain. Users can type input, but responses are placeholders. The goal is a solid, responsive UI foundation.
