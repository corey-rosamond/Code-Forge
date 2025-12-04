# Phase 6.2: Operating Modes - Requirements

**Phase:** 6.2
**Name:** Operating Modes
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 3.2 (LangChain Integration)

---

## Overview

Phase 6.2 implements operating modes for OpenCode, allowing the assistant to operate in different behavioral modes: Plan Mode for structured planning, Thinking Mode for extended reasoning, and Headless Mode for non-interactive automation. Each mode modifies the assistant's behavior, prompts, and interaction patterns.

---

## Goals

1. Implement Plan Mode for structured task planning
2. Implement Thinking Mode for extended reasoning
3. Implement Headless Mode for automation/CI
4. Enable mode switching during sessions
5. Persist mode state across interactions
6. Provide mode-specific system prompts

---

## Non-Goals (This Phase)

- Custom user-defined modes
- Mode-specific tool restrictions
- Mode chaining/composition
- Mode-based permission changes
- Visual mode indicators in TUI

---

## Functional Requirements

### FR-1: Mode System Foundation

**FR-1.1:** Mode definitions
- Each mode has unique name
- Modes have descriptions
- Modes can be enabled/disabled
- Modes have activation criteria

**FR-1.2:** Mode manager
- Track current active mode
- Switch between modes
- Reset to default mode
- Query mode capabilities

**FR-1.3:** Mode persistence
- Save mode state in session
- Restore mode on session resume
- Mode survives context compaction

### FR-2: Plan Mode

**FR-2.1:** Activation
- Activate via `/plan` command
- Activate via natural language request
- Auto-detect planning tasks

**FR-2.2:** Behavior modifications
- Use planning-focused system prompt
- Generate structured plans
- Create numbered step lists
- Identify dependencies
- Estimate complexity

**FR-2.3:** Plan output format
- Markdown-formatted plans
- Hierarchical structure
- Checkable task items
- File/code references
- Risk/consideration sections

**FR-2.4:** Plan execution
- Convert plan to todo items
- Track plan progress
- Allow plan modifications
- Exit plan mode when complete

### FR-3: Thinking Mode

**FR-3.1:** Activation
- Activate via `/think` command
- Activate for complex problems
- Configurable thinking depth

**FR-3.2:** Extended reasoning
- Use extended thinking budget
- Show reasoning process
- Support thinking tokens (if available)
- Structured thought blocks

**FR-3.3:** Thinking output
- Separate thinking from response
- Collapsible thinking sections
- Token usage for thinking
- Time tracking

**FR-3.4:** Thinking parameters
- Configurable max thinking tokens
- Thinking style preferences
- Verbosity levels

### FR-4: Headless Mode

**FR-4.1:** Activation
- Activate via CLI flag `--headless`
- Activate via environment variable
- No interactive prompts

**FR-4.2:** Non-interactive behavior
- Read input from stdin/file
- Write output to stdout/file
- Exit codes for success/failure
- JSON output option

**FR-4.3:** Automation support
- CI/CD integration
- Script execution
- Batch processing
- Timeout handling

**FR-4.4:** Headless constraints
- No user prompts
- Auto-approve safe operations
- Fail on unsafe operations
- Structured error output

### FR-5: Mode Switching

**FR-5.1:** Commands
- `/mode` - Show current mode
- `/mode <name>` - Switch to mode
- `/plan` - Enter plan mode
- `/think` - Enter thinking mode
- `/normal` - Return to normal mode

**FR-5.2:** Transition handling
- Save state before switch
- Apply new mode prompts
- Notify user of switch
- Handle pending operations

**FR-5.3:** Mode stacking (future)
- Modes can be combined
- Priority resolution
- Conflict handling

### FR-6: System Prompt Modifications

**FR-6.1:** Mode-specific prompts
- Each mode has prompt additions
- Prompts append to base prompt
- Prompts can override behaviors

**FR-6.2:** Prompt management
- Load prompts from configuration
- Support prompt templates
- Variable substitution in prompts

---

## Non-Functional Requirements

### NFR-1: Performance
- Mode switch < 10ms
- No latency impact on responses
- Minimal memory overhead

### NFR-2: Reliability
- Mode state always consistent
- Graceful fallback to normal mode
- No data loss on mode errors

### NFR-3: Extensibility
- Easy to add new modes
- Mode plugins possible
- Clear mode API

---

## Technical Specifications

### Package Structure

```
src/opencode/modes/
├── __init__.py           # Package exports
├── base.py               # Mode base class
├── manager.py            # Mode manager
├── prompts.py            # Mode prompts
├── plan.py               # Plan mode
├── thinking.py           # Thinking mode
└── headless.py           # Headless mode
```

### Class Signatures

```python
# base.py
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass

class ModeName(Enum):
    """Available operating modes."""
    NORMAL = "normal"
    PLAN = "plan"
    THINKING = "thinking"
    HEADLESS = "headless"


@dataclass
class ModeConfig:
    """Configuration for a mode."""
    name: ModeName
    description: str
    system_prompt_addition: str
    enabled: bool = True
    settings: dict = None


class Mode(ABC):
    """Base class for operating modes."""

    name: ModeName
    config: ModeConfig

    @abstractmethod
    def activate(self, context: "ModeContext") -> None:
        """Called when mode is activated."""
        ...

    @abstractmethod
    def deactivate(self, context: "ModeContext") -> None:
        """Called when mode is deactivated."""
        ...

    @abstractmethod
    def modify_prompt(self, base_prompt: str) -> str:
        """Modify system prompt for this mode."""
        ...

    @abstractmethod
    def modify_response(self, response: str) -> str:
        """Post-process response for this mode."""
        ...

    def should_auto_activate(self, message: str) -> bool:
        """Check if mode should auto-activate for message."""
        return False


# manager.py
@dataclass
class ModeContext:
    """Context for mode operations."""
    session: Any  # Session
    config: Any   # Configuration
    output: Callable[[str], None]


class ModeManager:
    """Manages operating modes."""

    _modes: dict[ModeName, Mode]
    _current_mode: ModeName
    _mode_stack: list[ModeName]

    def __init__(self):
        """Initialize with default mode."""
        ...

    def register_mode(self, mode: Mode) -> None:
        """Register an operating mode."""
        ...

    def get_current_mode(self) -> Mode:
        """Get currently active mode."""
        ...

    def switch_mode(
        self,
        name: ModeName,
        context: ModeContext
    ) -> bool:
        """Switch to specified mode."""
        ...

    def reset_mode(self, context: ModeContext) -> None:
        """Reset to normal mode."""
        ...

    def get_system_prompt(self, base_prompt: str) -> str:
        """Get prompt modified by current mode."""
        ...

    def process_response(self, response: str) -> str:
        """Process response through current mode."""
        ...

    def check_auto_activation(
        self,
        message: str
    ) -> ModeName | None:
        """Check if any mode should auto-activate."""
        ...


# plan.py
@dataclass
class PlanStep:
    """A step in a plan."""
    number: int
    description: str
    substeps: list["PlanStep"]
    completed: bool = False
    files: list[str] = None
    dependencies: list[int] = None


@dataclass
class Plan:
    """A structured plan."""
    title: str
    summary: str
    steps: list[PlanStep]
    considerations: list[str]
    created_at: datetime

    def to_markdown(self) -> str:
        """Convert plan to markdown format."""
        ...

    def to_todos(self) -> list[dict]:
        """Convert plan to todo items."""
        ...


class PlanMode(Mode):
    """Planning mode for structured task planning."""

    name = ModeName.PLAN
    current_plan: Plan | None = None

    def activate(self, context: ModeContext) -> None:
        """Enter plan mode."""
        ...

    def deactivate(self, context: ModeContext) -> None:
        """Exit plan mode, optionally save plan."""
        ...

    def create_plan(self, task: str) -> Plan:
        """Create a plan for given task."""
        ...

    def update_plan(self, updates: dict) -> None:
        """Update current plan."""
        ...

    def should_auto_activate(self, message: str) -> bool:
        """Detect planning requests."""
        ...


# thinking.py
@dataclass
class ThinkingConfig:
    """Configuration for thinking mode."""
    max_thinking_tokens: int = 10000
    show_thinking: bool = True
    thinking_style: str = "analytical"  # analytical, creative, thorough


@dataclass
class ThinkingResult:
    """Result of extended thinking."""
    thinking: str
    conclusion: str
    thinking_tokens: int
    time_seconds: float


class ThinkingMode(Mode):
    """Extended thinking mode for complex problems."""

    name = ModeName.THINKING
    config: ThinkingConfig

    def activate(self, context: ModeContext) -> None:
        """Enter thinking mode."""
        ...

    def set_thinking_budget(self, tokens: int) -> None:
        """Set maximum thinking tokens."""
        ...

    def format_thinking_output(
        self,
        result: ThinkingResult
    ) -> str:
        """Format thinking for display."""
        ...


# headless.py
@dataclass
class HeadlessConfig:
    """Configuration for headless mode."""
    input_file: str | None = None
    output_file: str | None = None
    output_format: str = "text"  # text, json
    timeout: int = 300  # seconds
    auto_approve_safe: bool = True
    fail_on_unsafe: bool = True


@dataclass
class HeadlessResult:
    """Result of headless execution."""
    success: bool
    output: str
    error: str | None = None
    exit_code: int = 0
    execution_time: float = 0


class HeadlessMode(Mode):
    """Non-interactive mode for automation."""

    name = ModeName.HEADLESS
    config: HeadlessConfig

    def activate(self, context: ModeContext) -> None:
        """Enter headless mode."""
        ...

    def read_input(self) -> str:
        """Read input from configured source."""
        ...

    def write_output(self, result: HeadlessResult) -> None:
        """Write output to configured destination."""
        ...

    def handle_permission_request(
        self,
        operation: str
    ) -> bool:
        """Handle permission request non-interactively."""
        ...
```

---

## Mode System Prompts

### Plan Mode Prompt Addition

```
You are now in PLAN MODE. Focus on creating structured, actionable plans.

When planning:
1. Break down tasks into numbered steps
2. Identify file changes needed
3. Note dependencies between steps
4. Consider risks and edge cases
5. Estimate relative complexity

Output format for plans:
## Plan: [Title]

### Summary
[Brief overview]

### Steps
1. [ ] Step description
   - Files: file1.py, file2.py
   - Dependencies: None

2. [ ] Step description
   - Files: file3.py
   - Dependencies: Step 1

### Considerations
- Risk or consideration 1
- Risk or consideration 2

Do not implement until the plan is approved with /plan execute.
```

### Thinking Mode Prompt Addition

```
You are now in THINKING MODE with extended reasoning enabled.

When thinking:
1. Take time to analyze the problem thoroughly
2. Consider multiple approaches
3. Evaluate trade-offs explicitly
4. Show your reasoning process
5. Reach a well-justified conclusion

Structure your response as:
<thinking>
[Your detailed reasoning process]
</thinking>

<response>
[Your final response to the user]
</response>
```

### Headless Mode Prompt Addition

```
You are now in HEADLESS MODE for non-interactive execution.

Constraints:
1. Do not ask questions - make reasonable assumptions
2. Operations marked as "safe" will auto-approve
3. Operations marked as "unsafe" will fail with error
4. Output must be structured and parseable
5. Complete tasks fully or fail explicitly

If you cannot complete a task safely:
- Do not attempt partial completion
- Report specific blocking issues
- Exit with appropriate error code
```

---

## Mode Commands Reference

| Command | Description |
|---------|-------------|
| `/mode` | Show current operating mode |
| `/mode <name>` | Switch to specified mode |
| `/plan` | Enter plan mode |
| `/plan execute` | Execute current plan |
| `/plan show` | Show current plan |
| `/plan cancel` | Cancel plan and exit mode |
| `/think` | Enter thinking mode |
| `/think deep` | Enter deep thinking mode |
| `/normal` | Return to normal mode |

---

## Integration Points

### With REPL (Phase 1.3)
- Mode affects REPL prompts
- Mode commands available
- Mode status displayed

### With LangChain (Phase 3.2)
- Mode prompts prepended
- Extended thinking via tokens
- Response post-processing

### With Session (Phase 5.1)
- Mode saved in session
- Mode restored on resume
- Plans stored in session

### With Slash Commands (Phase 6.1)
- Mode commands registered
- Mode affects command behavior

---

## Testing Requirements

1. Unit tests for Mode base class
2. Unit tests for ModeManager
3. Unit tests for each mode
4. Integration tests with REPL
5. Headless mode E2E tests
6. Test coverage ≥ 90%

---

## Acceptance Criteria

1. All three modes implemented
2. Mode switching works correctly
3. Mode prompts applied correctly
4. Plan mode creates structured plans
5. Thinking mode shows reasoning
6. Headless mode runs non-interactively
7. Mode state persists in sessions
8. Mode commands functional
9. Auto-activation works
10. Graceful fallback on errors
