# Phase 6.2: Operating Modes - Implementation Plan

**Phase:** 6.2
**Name:** Operating Modes
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 3.2 (LangChain Integration)

---

## Implementation Order

1. `base.py` - Mode base classes and enums
2. `prompts.py` - Mode-specific prompts
3. `manager.py` - Mode manager
4. `plan.py` - Plan mode implementation
5. `thinking.py` - Thinking mode implementation
6. `headless.py` - Headless mode implementation
7. `__init__.py` - Package exports
8. Integration with REPL

---

## Step 1: Mode Base Classes (base.py)

```python
"""
Base classes for operating modes.

Provides the foundation for implementing different operating modes
that modify assistant behavior, prompts, and interaction patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol


class ModeName(Enum):
    """Available operating modes."""
    NORMAL = "normal"
    PLAN = "plan"
    THINKING = "thinking"
    HEADLESS = "headless"


@dataclass
class ModeConfig:
    """Configuration for an operating mode.

    Attributes:
        name: Mode identifier
        description: Human-readable description
        system_prompt_addition: Text to append to system prompt
        enabled: Whether mode is available
        settings: Mode-specific settings
    """
    name: ModeName
    description: str
    system_prompt_addition: str = ""
    enabled: bool = True
    settings: dict[str, Any] = field(default_factory=dict)

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a mode setting by key."""
        return self.settings.get(key, default)

    def set_setting(self, key: str, value: Any) -> None:
        """Set a mode setting."""
        self.settings[key] = value


class OutputHandler(Protocol):
    """Protocol for output handling."""

    def __call__(self, message: str) -> None:
        """Output a message."""
        ...


def _default_output_handler(message: str) -> None:
    """Default no-op output handler."""
    pass


@dataclass
class ModeContext:
    """Context provided to mode operations.

    Attributes:
        session: Current session object
        config: Application configuration
        output: Output handler function
        data: Additional context data
    """
    session: Any = None
    config: Any = None
    output: OutputHandler = field(default_factory=lambda: _default_output_handler)
    data: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get context data by key."""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set context data."""
        self.data[key] = value


@dataclass
class ModeState:
    """Persistent state for a mode.

    Stored in session for persistence across interactions.
    """
    mode_name: ModeName
    active: bool = False
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "mode_name": self.mode_name.value,
            "active": self.active,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ModeState":
        """Deserialize from dictionary."""
        return cls(
            mode_name=ModeName(data["mode_name"]),
            active=data.get("active", False),
            data=data.get("data", {}),
        )


class Mode(ABC):
    """Abstract base class for operating modes.

    Modes modify assistant behavior through:
    - System prompt additions
    - Response post-processing
    - Custom activation/deactivation logic
    """

    def __init__(self, config: ModeConfig | None = None):
        """Initialize mode with optional configuration."""
        self._config = config or self._default_config()
        self._state = ModeState(mode_name=self.name)

    @property
    @abstractmethod
    def name(self) -> ModeName:
        """Return mode name."""
        ...

    @property
    def config(self) -> ModeConfig:
        """Return mode configuration."""
        return self._config

    @property
    def state(self) -> ModeState:
        """Return mode state."""
        return self._state

    @property
    def is_active(self) -> bool:
        """Check if mode is currently active."""
        return self._state.active

    @abstractmethod
    def _default_config(self) -> ModeConfig:
        """Return default configuration for this mode."""
        ...

    @abstractmethod
    def activate(self, context: ModeContext) -> None:
        """Called when mode is activated.

        Override to perform setup when entering mode.
        """
        self._state.active = True

    @abstractmethod
    def deactivate(self, context: ModeContext) -> None:
        """Called when mode is deactivated.

        Override to perform cleanup when leaving mode.
        """
        self._state.active = False
        self._state.data.clear()

    def modify_prompt(self, base_prompt: str) -> str:
        """Modify system prompt for this mode.

        Default implementation appends the prompt addition.
        Override for custom prompt modification.
        """
        if self._config.system_prompt_addition:
            return f"{base_prompt}\n\n{self._config.system_prompt_addition}"
        return base_prompt

    def modify_response(self, response: str) -> str:
        """Post-process response for this mode.

        Default implementation returns response unchanged.
        Override for custom response processing.
        """
        return response

    def should_auto_activate(self, message: str) -> bool:
        """Check if mode should auto-activate for given message.

        Default returns False. Override to enable auto-activation.
        """
        return False

    def save_state(self) -> dict:
        """Save mode state for persistence."""
        return self._state.to_dict()

    def restore_state(self, data: dict) -> None:
        """Restore mode state from persisted data."""
        self._state = ModeState.from_dict(data)


class NormalMode(Mode):
    """Default operating mode with no modifications."""

    @property
    def name(self) -> ModeName:
        return ModeName.NORMAL

    def _default_config(self) -> ModeConfig:
        return ModeConfig(
            name=ModeName.NORMAL,
            description="Normal operating mode",
            system_prompt_addition="",
        )

    def activate(self, context: ModeContext) -> None:
        """Activate normal mode."""
        super().activate(context)
        context.output("Returned to normal mode.")

    def deactivate(self, context: ModeContext) -> None:
        """Deactivate normal mode."""
        super().deactivate(context)
```

---

## Step 2: Mode Prompts (prompts.py)

```python
"""
System prompt additions for operating modes.

Each mode has specific prompt text that modifies
assistant behavior when active.
"""

PLAN_MODE_PROMPT = """
You are now in PLAN MODE. Focus on creating structured, actionable plans.

When planning:
1. Break down tasks into numbered steps
2. Identify file changes needed for each step
3. Note dependencies between steps
4. Consider risks and edge cases
5. Estimate relative complexity (low/medium/high)

Output format for plans:

## Plan: [Descriptive Title]

### Summary
[1-2 sentence overview of what will be accomplished]

### Steps
1. [ ] First step description
   - Files: file1.py, file2.py
   - Complexity: Low
   - Dependencies: None

2. [ ] Second step description
   - Files: file3.py
   - Complexity: Medium
   - Dependencies: Step 1

### Considerations
- Important consideration or risk 1
- Important consideration or risk 2

### Success Criteria
- How to verify the plan succeeded

IMPORTANT: Do not implement until the plan is approved.
Use /plan execute to begin implementation or /plan cancel to abort.
""".strip()


THINKING_MODE_PROMPT = """
You are now in THINKING MODE with extended reasoning enabled.

When thinking through problems:
1. Take time to analyze the problem thoroughly
2. Consider multiple approaches before choosing
3. Evaluate trade-offs explicitly
4. Show your reasoning process step by step
5. Reach a well-justified conclusion

Structure your response as:

<thinking>
[Your detailed reasoning process here]
- First, consider...
- This suggests...
- However, we should also consider...
- Weighing these factors...
</thinking>

<response>
[Your final, concise response to the user]
</response>

The thinking section helps you reason carefully. The response section
should contain only the final answer or recommendation.
""".strip()


THINKING_MODE_DEEP_PROMPT = """
You are now in DEEP THINKING MODE for complex analysis.

Apply rigorous analytical thinking:
1. Decompose the problem into components
2. Analyze each component thoroughly
3. Consider edge cases and failure modes
4. Evaluate multiple solution approaches
5. Synthesize findings into a coherent recommendation

Structure your extended analysis:

<thinking>
## Problem Analysis
[Break down the core problem]

## Approaches Considered
### Approach 1: [Name]
- Pros: ...
- Cons: ...

### Approach 2: [Name]
- Pros: ...
- Cons: ...

## Trade-off Analysis
[Compare approaches against requirements]

## Recommendation
[Justified recommendation with reasoning]
</thinking>

<response>
[Clear, actionable response]
</response>
""".strip()


HEADLESS_MODE_PROMPT = """
You are now in HEADLESS MODE for non-interactive execution.

Critical constraints:
1. Do NOT ask questions - make reasonable assumptions based on context
2. Do NOT request confirmation - proceed with safe operations
3. Operations marked as "safe" will auto-approve
4. Operations marked as "unsafe" will fail immediately
5. All output must be structured and parseable
6. Complete tasks fully or fail explicitly with clear errors

If you encounter ambiguity:
- Choose the most common/standard approach
- Document assumptions made in output
- Prefer reversible over irreversible actions

If you cannot complete a task safely:
- Do NOT attempt partial completion
- Report specific blocking issues clearly
- Provide structured error information

Output format for headless mode:
{
  "status": "success" | "failure",
  "message": "Human-readable summary",
  "details": { ... },
  "errors": [ ... ] // if any
}
""".strip()


# Mapping of mode names to prompts
MODE_PROMPTS: dict[str, str] = {
    "plan": PLAN_MODE_PROMPT,
    "thinking": THINKING_MODE_PROMPT,
    "thinking_deep": THINKING_MODE_DEEP_PROMPT,
    "headless": HEADLESS_MODE_PROMPT,
}


def get_mode_prompt(mode_name: str, variant: str = "") -> str:
    """Get prompt for a mode with optional variant.

    Args:
        mode_name: Name of the mode
        variant: Optional variant (e.g., "deep" for thinking)

    Returns:
        Prompt text or empty string if not found
    """
    key = f"{mode_name}_{variant}" if variant else mode_name
    return MODE_PROMPTS.get(key, MODE_PROMPTS.get(mode_name, ""))
```

---

## Step 3: Mode Manager (manager.py)

```python
"""
Mode manager for operating modes.

Handles mode registration, switching, and state management.
Provides the central coordination point for mode operations.
"""

from typing import Callable
import logging

from .base import Mode, ModeConfig, ModeContext, ModeName, NormalMode, ModeState


logger = logging.getLogger(__name__)


class ModeError(Exception):
    """Base exception for mode errors."""
    pass


class ModeNotFoundError(ModeError):
    """Raised when requested mode doesn't exist."""
    pass


class ModeSwitchError(ModeError):
    """Raised when mode switch fails."""
    pass


class ModeManager:
    """Manages operating modes.

    Singleton that tracks registered modes and the current
    active mode. Handles mode switching and state persistence.
    """

    _instance: "ModeManager | None" = None

    def __init__(self):
        """Initialize mode manager with normal mode."""
        self._modes: dict[ModeName, Mode] = {}
        self._current_mode: ModeName = ModeName.NORMAL
        self._mode_stack: list[ModeName] = []
        self._on_mode_change: list[Callable[[ModeName, ModeName], None]] = []

        # Register default normal mode
        self.register_mode(NormalMode())

    @classmethod
    def get_instance(cls) -> "ModeManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton instance (for testing)."""
        cls._instance = None

    def register_mode(self, mode: Mode) -> None:
        """Register an operating mode.

        Args:
            mode: Mode instance to register

        Raises:
            ValueError: If mode with same name already registered
        """
        if mode.name in self._modes:
            raise ValueError(f"Mode already registered: {mode.name.value}")
        self._modes[mode.name] = mode
        logger.debug(f"Registered mode: {mode.name.value}")

    def unregister_mode(self, name: ModeName) -> bool:
        """Unregister a mode.

        Args:
            name: Name of mode to unregister

        Returns:
            True if mode was unregistered, False if not found
        """
        if name == ModeName.NORMAL:
            logger.warning("Cannot unregister normal mode")
            return False
        if name in self._modes:
            del self._modes[name]
            logger.debug(f"Unregistered mode: {name.value}")
            return True
        return False

    def get_mode(self, name: ModeName) -> Mode | None:
        """Get mode by name."""
        return self._modes.get(name)

    def get_current_mode(self) -> Mode:
        """Get currently active mode."""
        return self._modes[self._current_mode]

    @property
    def current_mode_name(self) -> ModeName:
        """Get current mode name."""
        return self._current_mode

    def list_modes(self) -> list[Mode]:
        """List all registered modes."""
        return list(self._modes.values())

    def list_enabled_modes(self) -> list[Mode]:
        """List only enabled modes."""
        return [m for m in self._modes.values() if m.config.enabled]

    def switch_mode(
        self,
        name: ModeName,
        context: ModeContext,
        push: bool = False
    ) -> bool:
        """Switch to specified mode.

        Args:
            name: Target mode name
            context: Mode context
            push: If True, push current mode to stack

        Returns:
            True if switch successful

        Raises:
            ModeNotFoundError: If mode not found
            ModeSwitchError: If switch fails
        """
        if name not in self._modes:
            raise ModeNotFoundError(f"Mode not found: {name.value}")

        if not self._modes[name].config.enabled:
            raise ModeSwitchError(f"Mode is disabled: {name.value}")

        old_mode = self._current_mode

        try:
            # Deactivate current mode
            self._modes[old_mode].deactivate(context)

            # Push to stack if requested
            if push:
                self._mode_stack.append(old_mode)

            # Activate new mode
            self._modes[name].activate(context)
            self._current_mode = name

            # Notify listeners
            for callback in self._on_mode_change:
                callback(old_mode, name)

            logger.info(f"Switched mode: {old_mode.value} -> {name.value}")
            return True

        except Exception as e:
            logger.error(f"Mode switch failed: {e}")
            # Try to restore old mode
            try:
                self._modes[old_mode].activate(context)
                self._current_mode = old_mode
            except Exception:
                pass
            raise ModeSwitchError(f"Failed to switch to {name.value}: {e}")

    def pop_mode(self, context: ModeContext) -> ModeName | None:
        """Pop previous mode from stack.

        Returns:
            Previous mode name, or None if stack empty
        """
        if not self._mode_stack:
            return None

        previous = self._mode_stack.pop()
        self.switch_mode(previous, context)
        return previous

    def reset_mode(self, context: ModeContext) -> None:
        """Reset to normal mode, clearing stack."""
        self._mode_stack.clear()
        self.switch_mode(ModeName.NORMAL, context)

    def get_system_prompt(self, base_prompt: str) -> str:
        """Get prompt modified by current mode.

        Args:
            base_prompt: Base system prompt

        Returns:
            Modified prompt
        """
        current = self.get_current_mode()
        return current.modify_prompt(base_prompt)

    def process_response(self, response: str) -> str:
        """Process response through current mode.

        Args:
            response: Raw response text

        Returns:
            Processed response
        """
        current = self.get_current_mode()
        return current.modify_response(response)

    def check_auto_activation(self, message: str) -> ModeName | None:
        """Check if any mode should auto-activate.

        Args:
            message: User message

        Returns:
            Mode name if auto-activation triggered, None otherwise
        """
        for mode in self._modes.values():
            if mode.name != self._current_mode and mode.config.enabled:
                if mode.should_auto_activate(message):
                    return mode.name
        return None

    def on_mode_change(
        self,
        callback: Callable[[ModeName, ModeName], None]
    ) -> None:
        """Register callback for mode changes.

        Callback receives (old_mode, new_mode).
        """
        self._on_mode_change.append(callback)

    def save_state(self) -> dict:
        """Save mode manager state for persistence."""
        return {
            "current_mode": self._current_mode.value,
            "mode_stack": [m.value for m in self._mode_stack],
            "mode_states": {
                name.value: mode.save_state()
                for name, mode in self._modes.items()
            },
        }

    def restore_state(self, data: dict, context: ModeContext) -> None:
        """Restore mode manager state from persisted data."""
        # Restore mode-specific states
        mode_states = data.get("mode_states", {})
        for name_str, state in mode_states.items():
            name = ModeName(name_str)
            if name in self._modes:
                self._modes[name].restore_state(state)

        # Restore stack
        self._mode_stack = [
            ModeName(m) for m in data.get("mode_stack", [])
        ]

        # Restore current mode
        current = data.get("current_mode", "normal")
        target_mode = ModeName(current)
        if target_mode in self._modes:
            self.switch_mode(target_mode, context)
```

---

## Step 4: Plan Mode (plan.py)

```python
"""
Plan mode implementation.

Provides structured planning capabilities with task breakdown,
dependency tracking, and plan execution support.
"""

from dataclasses import dataclass, field
from datetime import datetime
import re
from typing import Any

from .base import Mode, ModeConfig, ModeContext, ModeName
from .prompts import PLAN_MODE_PROMPT


@dataclass
class PlanStep:
    """A step in a plan.

    Attributes:
        number: Step number (1-indexed)
        description: What this step accomplishes
        substeps: Nested substeps if any
        completed: Whether step is done
        files: Files to be modified
        dependencies: Step numbers this depends on
        complexity: Relative complexity estimate
    """
    number: int
    description: str
    substeps: list["PlanStep"] = field(default_factory=list)
    completed: bool = False
    files: list[str] = field(default_factory=list)
    dependencies: list[int] = field(default_factory=list)
    complexity: str = "medium"  # low, medium, high

    def to_markdown(self, indent: int = 0) -> str:
        """Convert step to markdown format."""
        prefix = "  " * indent
        check = "x" if self.completed else " "
        lines = [f"{prefix}{self.number}. [{check}] {self.description}"]

        if self.files:
            lines.append(f"{prefix}   - Files: {', '.join(self.files)}")
        if self.dependencies:
            deps = ", ".join(f"Step {d}" for d in self.dependencies)
            lines.append(f"{prefix}   - Dependencies: {deps}")
        if self.complexity:
            lines.append(f"{prefix}   - Complexity: {self.complexity.title()}")

        for substep in self.substeps:
            lines.append(substep.to_markdown(indent + 1))

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "number": self.number,
            "description": self.description,
            "substeps": [s.to_dict() for s in self.substeps],
            "completed": self.completed,
            "files": self.files,
            "dependencies": self.dependencies,
            "complexity": self.complexity,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlanStep":
        """Deserialize from dictionary."""
        return cls(
            number=data["number"],
            description=data["description"],
            substeps=[cls.from_dict(s) for s in data.get("substeps", [])],
            completed=data.get("completed", False),
            files=data.get("files", []),
            dependencies=data.get("dependencies", []),
            complexity=data.get("complexity", "medium"),
        )


@dataclass
class Plan:
    """A structured plan.

    Represents a complete plan with steps, considerations,
    and success criteria.
    """
    title: str
    summary: str
    steps: list[PlanStep]
    considerations: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_markdown(self) -> str:
        """Convert plan to markdown format."""
        lines = [
            f"## Plan: {self.title}",
            "",
            "### Summary",
            self.summary,
            "",
            "### Steps",
        ]

        for step in self.steps:
            lines.append(step.to_markdown())

        if self.considerations:
            lines.extend([
                "",
                "### Considerations",
            ])
            for c in self.considerations:
                lines.append(f"- {c}")

        if self.success_criteria:
            lines.extend([
                "",
                "### Success Criteria",
            ])
            for sc in self.success_criteria:
                lines.append(f"- {sc}")

        return "\n".join(lines)

    def to_todos(self) -> list[dict]:
        """Convert plan steps to todo items."""
        todos = []
        for step in self.steps:
            todos.append({
                "content": step.description,
                "status": "completed" if step.completed else "pending",
                "activeForm": f"Working on: {step.description}",
            })
        return todos

    @property
    def progress(self) -> tuple[int, int]:
        """Get (completed, total) step counts."""
        total = len(self.steps)
        completed = sum(1 for s in self.steps if s.completed)
        return completed, total

    @property
    def progress_percentage(self) -> float:
        """Get completion percentage."""
        completed, total = self.progress
        return (completed / total * 100) if total > 0 else 0

    def mark_step_complete(self, step_number: int) -> bool:
        """Mark a step as complete."""
        for step in self.steps:
            if step.number == step_number:
                step.completed = True
                self.updated_at = datetime.now()
                return True
        return False

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "title": self.title,
            "summary": self.summary,
            "steps": [s.to_dict() for s in self.steps],
            "considerations": self.considerations,
            "success_criteria": self.success_criteria,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plan":
        """Deserialize from dictionary."""
        return cls(
            title=data["title"],
            summary=data["summary"],
            steps=[PlanStep.from_dict(s) for s in data["steps"]],
            considerations=data.get("considerations", []),
            success_criteria=data.get("success_criteria", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


# Patterns for detecting planning requests
PLANNING_PATTERNS = [
    r"\bplan\b.*\b(how|to|for)\b",
    r"\bbreak\s*down\b",
    r"\bsteps?\s+(to|for)\b",
    r"\bstrategy\s+for\b",
    r"\bapproach\s+to\b",
    r"\bdesign\b.*\bimplementation\b",
    r"\barchitect\b",
    r"\broadmap\b",
]


class PlanMode(Mode):
    """Planning mode for structured task planning.

    Modifies assistant behavior to focus on creating
    actionable, structured plans before implementation.
    """

    def __init__(self, config: ModeConfig | None = None):
        super().__init__(config)
        self.current_plan: Plan | None = None

    @property
    def name(self) -> ModeName:
        return ModeName.PLAN

    def _default_config(self) -> ModeConfig:
        return ModeConfig(
            name=ModeName.PLAN,
            description="Structured planning mode",
            system_prompt_addition=PLAN_MODE_PROMPT,
        )

    def activate(self, context: ModeContext) -> None:
        """Enter plan mode."""
        super().activate(context)
        context.output("Entered plan mode. I'll create a structured plan.")
        context.output("Use /plan execute to implement, /plan cancel to abort.")

    def deactivate(self, context: ModeContext) -> None:
        """Exit plan mode."""
        if self.current_plan:
            # Save plan to state before clearing
            self._state.data["last_plan"] = self.current_plan.to_dict()
        self.current_plan = None
        super().deactivate(context)
        context.output("Exited plan mode.")

    def should_auto_activate(self, message: str) -> bool:
        """Detect planning requests in message."""
        message_lower = message.lower()
        for pattern in PLANNING_PATTERNS:
            if re.search(pattern, message_lower):
                return True
        return False

    def set_plan(self, plan: Plan) -> None:
        """Set the current plan."""
        self.current_plan = plan
        self._state.data["current_plan"] = plan.to_dict()

    def get_plan(self) -> Plan | None:
        """Get current plan."""
        return self.current_plan

    def show_plan(self) -> str:
        """Get plan display text."""
        if not self.current_plan:
            return "No plan created yet."
        return self.current_plan.to_markdown()

    def execute_plan(self) -> list[dict]:
        """Convert plan to executable todos."""
        if not self.current_plan:
            return []
        return self.current_plan.to_todos()

    def cancel_plan(self) -> None:
        """Cancel current plan."""
        self.current_plan = None
        self._state.data.pop("current_plan", None)

    def save_state(self) -> dict:
        """Save plan mode state."""
        state = super().save_state()
        if self.current_plan:
            state["data"]["current_plan"] = self.current_plan.to_dict()
        return state

    def restore_state(self, data: dict) -> None:
        """Restore plan mode state."""
        super().restore_state(data)
        plan_data = self._state.data.get("current_plan")
        if plan_data:
            self.current_plan = Plan.from_dict(plan_data)
```

---

## Step 5: Thinking Mode (thinking.py)

```python
"""
Thinking mode implementation.

Provides extended reasoning capabilities with visible
thinking process and structured analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime
import re
import time
from typing import Any

from .base import Mode, ModeConfig, ModeContext, ModeName
from .prompts import THINKING_MODE_PROMPT, THINKING_MODE_DEEP_PROMPT


@dataclass
class ThinkingConfig:
    """Configuration for thinking mode.

    Attributes:
        max_thinking_tokens: Maximum tokens for thinking
        show_thinking: Whether to display thinking section
        thinking_style: Style of thinking (analytical, creative, thorough)
        deep_mode: Enable deep analysis mode
    """
    max_thinking_tokens: int = 10000
    show_thinking: bool = True
    thinking_style: str = "analytical"
    deep_mode: bool = False


@dataclass
class ThinkingResult:
    """Result of extended thinking.

    Separates thinking process from final response.
    """
    thinking: str
    response: str
    thinking_tokens: int = 0
    response_tokens: int = 0
    time_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "thinking": self.thinking,
            "response": self.response,
            "thinking_tokens": self.thinking_tokens,
            "response_tokens": self.response_tokens,
            "time_seconds": self.time_seconds,
            "timestamp": self.timestamp.isoformat(),
        }


# Pattern to extract thinking and response sections
THINKING_PATTERN = re.compile(
    r"<thinking>\s*(.*?)\s*</thinking>\s*<response>\s*(.*?)\s*</response>",
    re.DOTALL | re.IGNORECASE
)


class ThinkingMode(Mode):
    """Extended thinking mode for complex problems.

    Encourages structured reasoning and shows the
    thinking process alongside the final response.
    """

    def __init__(
        self,
        config: ModeConfig | None = None,
        thinking_config: ThinkingConfig | None = None
    ):
        super().__init__(config)
        self.thinking_config = thinking_config or ThinkingConfig()
        self._start_time: float | None = None

    @property
    def name(self) -> ModeName:
        return ModeName.THINKING

    def _default_config(self) -> ModeConfig:
        return ModeConfig(
            name=ModeName.THINKING,
            description="Extended thinking mode",
            system_prompt_addition=THINKING_MODE_PROMPT,
        )

    def activate(self, context: ModeContext) -> None:
        """Enter thinking mode."""
        super().activate(context)
        self._start_time = time.time()

        deep = self.thinking_config.deep_mode
        mode_type = "deep thinking" if deep else "thinking"

        context.output(f"Entered {mode_type} mode.")
        context.output("I'll show my reasoning process in detail.")

        # Update prompt for deep mode
        if deep:
            self._config.system_prompt_addition = THINKING_MODE_DEEP_PROMPT

    def deactivate(self, context: ModeContext) -> None:
        """Exit thinking mode."""
        self._start_time = None
        super().deactivate(context)
        context.output("Exited thinking mode.")

    def set_deep_mode(self, enabled: bool) -> None:
        """Toggle deep thinking mode."""
        self.thinking_config.deep_mode = enabled
        if enabled:
            self._config.system_prompt_addition = THINKING_MODE_DEEP_PROMPT
        else:
            self._config.system_prompt_addition = THINKING_MODE_PROMPT

    def set_thinking_budget(self, tokens: int) -> None:
        """Set maximum thinking tokens."""
        self.thinking_config.max_thinking_tokens = max(1000, tokens)

    def modify_response(self, response: str) -> str:
        """Extract and format thinking from response."""
        match = THINKING_PATTERN.search(response)

        if not match:
            # No structured thinking found
            return response

        thinking = match.group(1).strip()
        final_response = match.group(2).strip()

        # Create thinking result
        elapsed = time.time() - self._start_time if self._start_time else 0
        result = ThinkingResult(
            thinking=thinking,
            response=final_response,
            time_seconds=elapsed,
        )

        # Store in state
        self._state.data["last_thinking"] = result.to_dict()

        # Format output based on config
        return self.format_thinking_output(result)

    def format_thinking_output(self, result: ThinkingResult) -> str:
        """Format thinking result for display.

        Args:
            result: Thinking result to format

        Returns:
            Formatted output string
        """
        lines = []

        if self.thinking_config.show_thinking:
            lines.extend([
                "### Thinking Process",
                "",
                result.thinking,
                "",
                "---",
                "",
            ])

        lines.append(result.response)

        # Add timing info
        if result.time_seconds > 0:
            lines.extend([
                "",
                f"*Thinking time: {result.time_seconds:.1f}s*",
            ])

        return "\n".join(lines)

    def get_last_thinking(self) -> ThinkingResult | None:
        """Get the last thinking result."""
        data = self._state.data.get("last_thinking")
        if data:
            return ThinkingResult(
                thinking=data["thinking"],
                response=data["response"],
                thinking_tokens=data.get("thinking_tokens", 0),
                response_tokens=data.get("response_tokens", 0),
                time_seconds=data.get("time_seconds", 0),
            )
        return None


# Patterns for detecting complex problems
COMPLEX_PROBLEM_PATTERNS = [
    r"\bcomplex\b",
    r"\bdifficult\b",
    r"\btricky\b",
    r"\btrade-?offs?\b",
    r"\bweigh\b.*\boptions\b",
    r"\banalyze\b",
    r"\bcompare\b.*\bapproaches\b",
    r"\bpros?\s+and\s+cons?\b",
    r"\bthink\s+(through|about|carefully)\b",
    r"\breason\b.*\babout\b",
]


def should_suggest_thinking(message: str) -> bool:
    """Check if thinking mode might help with this message."""
    message_lower = message.lower()
    for pattern in COMPLEX_PROBLEM_PATTERNS:
        if re.search(pattern, message_lower):
            return True
    return False
```

---

## Step 6: Headless Mode (headless.py)

```python
"""
Headless mode implementation.

Provides non-interactive execution for automation,
CI/CD integration, and scripting.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import sys
import time
from pathlib import Path
from typing import Any, TextIO

from .base import Mode, ModeConfig, ModeContext, ModeName
from .prompts import HEADLESS_MODE_PROMPT


class OutputFormat(Enum):
    """Output format options."""
    TEXT = "text"
    JSON = "json"


@dataclass
class HeadlessConfig:
    """Configuration for headless mode.

    Attributes:
        input_file: Path to input file (None for stdin)
        output_file: Path to output file (None for stdout)
        output_format: Format for output (text or json)
        timeout: Maximum execution time in seconds
        auto_approve_safe: Auto-approve safe operations
        fail_on_unsafe: Fail on unsafe operations
        exit_on_complete: Exit process when done
    """
    input_file: str | None = None
    output_file: str | None = None
    output_format: OutputFormat = OutputFormat.TEXT
    timeout: int = 300
    auto_approve_safe: bool = True
    fail_on_unsafe: bool = True
    exit_on_complete: bool = True


@dataclass
class HeadlessResult:
    """Result of headless execution.

    Provides structured output for automation.
    """
    success: bool
    message: str
    output: str = ""
    error: str | None = None
    exit_code: int = 0
    execution_time: float = 0.0
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps({
            "status": "success" if self.success else "failure",
            "message": self.message,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }, indent=2)

    def to_text(self) -> str:
        """Convert to text format."""
        lines = [self.message]
        if self.output:
            lines.extend(["", self.output])
        if self.error:
            lines.extend(["", f"Error: {self.error}"])
        if self.details:
            lines.extend(["", "Details:"])
            for key, value in self.details.items():
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)


class HeadlessMode(Mode):
    """Non-interactive mode for automation.

    Runs without user prompts, suitable for CI/CD
    pipelines and scripting.
    """

    def __init__(
        self,
        config: ModeConfig | None = None,
        headless_config: HeadlessConfig | None = None
    ):
        super().__init__(config)
        self.headless_config = headless_config or HeadlessConfig()
        self._start_time: float | None = None
        self._input_stream: TextIO | None = None
        self._output_stream: TextIO | None = None

    @property
    def name(self) -> ModeName:
        return ModeName.HEADLESS

    def _default_config(self) -> ModeConfig:
        return ModeConfig(
            name=ModeName.HEADLESS,
            description="Non-interactive automation mode",
            system_prompt_addition=HEADLESS_MODE_PROMPT,
        )

    def activate(self, context: ModeContext) -> None:
        """Enter headless mode."""
        super().activate(context)
        self._start_time = time.time()

        # Open input stream
        if self.headless_config.input_file:
            path = Path(self.headless_config.input_file)
            if path.exists():
                self._input_stream = open(path, "r")
            else:
                raise FileNotFoundError(
                    f"Input file not found: {path}"
                )
        else:
            self._input_stream = sys.stdin

        # Open output stream
        if self.headless_config.output_file:
            path = Path(self.headless_config.output_file)
            self._output_stream = open(path, "w")
        else:
            self._output_stream = sys.stdout

    def deactivate(self, context: ModeContext) -> None:
        """Exit headless mode."""
        # Close file streams
        if self._input_stream and self._input_stream != sys.stdin:
            self._input_stream.close()
        if self._output_stream and self._output_stream != sys.stdout:
            self._output_stream.close()

        self._input_stream = None
        self._output_stream = None
        self._start_time = None
        super().deactivate(context)

    def read_input(self) -> str:
        """Read input from configured source.

        Returns:
            Input text
        """
        if self._input_stream:
            return self._input_stream.read()
        return ""

    def write_output(self, result: HeadlessResult) -> None:
        """Write output to configured destination.

        Args:
            result: Execution result to output
        """
        if not self._output_stream:
            return

        if self.headless_config.output_format == OutputFormat.JSON:
            output = result.to_json()
        else:
            output = result.to_text()

        self._output_stream.write(output)
        self._output_stream.write("\n")
        self._output_stream.flush()

    def handle_permission_request(
        self,
        operation: str,
        is_safe: bool
    ) -> bool:
        """Handle permission request non-interactively.

        Args:
            operation: Description of operation
            is_safe: Whether operation is considered safe

        Returns:
            True if operation approved, False if denied
        """
        if is_safe and self.headless_config.auto_approve_safe:
            return True

        if not is_safe and self.headless_config.fail_on_unsafe:
            return False

        # Default to deny for ambiguous cases
        return False

    def create_result(
        self,
        success: bool,
        message: str,
        output: str = "",
        error: str | None = None,
        details: dict | None = None
    ) -> HeadlessResult:
        """Create a headless execution result.

        Args:
            success: Whether execution succeeded
            message: Summary message
            output: Full output text
            error: Error message if failed
            details: Additional details

        Returns:
            HeadlessResult instance
        """
        elapsed = time.time() - self._start_time if self._start_time else 0

        return HeadlessResult(
            success=success,
            message=message,
            output=output,
            error=error,
            exit_code=0 if success else 1,
            execution_time=elapsed,
            details=details or {},
        )

    def modify_response(self, response: str) -> str:
        """Format response for headless output."""
        # In headless mode, responses may need JSON formatting
        if self.headless_config.output_format == OutputFormat.JSON:
            result = self.create_result(
                success=True,
                message="Completed",
                output=response,
            )
            return result.to_json()
        return response

    def check_timeout(self) -> bool:
        """Check if execution has exceeded timeout.

        Returns:
            True if timed out
        """
        if not self._start_time:
            return False
        elapsed = time.time() - self._start_time
        return elapsed > self.headless_config.timeout


def create_headless_config_from_args(
    input_file: str | None = None,
    output_file: str | None = None,
    json_output: bool = False,
    timeout: int = 300,
) -> HeadlessConfig:
    """Create headless config from CLI arguments.

    Args:
        input_file: Path to input file
        output_file: Path to output file
        json_output: Whether to use JSON output format
        timeout: Execution timeout in seconds

    Returns:
        HeadlessConfig instance
    """
    return HeadlessConfig(
        input_file=input_file,
        output_file=output_file,
        output_format=OutputFormat.JSON if json_output else OutputFormat.TEXT,
        timeout=timeout,
    )
```

---

## Step 7: Package Exports (__init__.py)

```python
"""
Operating modes package.

Provides different operating modes that modify assistant
behavior: Plan, Thinking, and Headless modes.
"""

from .base import (
    Mode,
    ModeConfig,
    ModeContext,
    ModeName,
    ModeState,
    NormalMode,
)
from .manager import (
    ModeManager,
    ModeError,
    ModeNotFoundError,
    ModeSwitchError,
)
from .plan import (
    Plan,
    PlanMode,
    PlanStep,
)
from .thinking import (
    ThinkingConfig,
    ThinkingMode,
    ThinkingResult,
    should_suggest_thinking,
)
from .headless import (
    HeadlessConfig,
    HeadlessMode,
    HeadlessResult,
    OutputFormat,
    create_headless_config_from_args,
)
from .prompts import (
    PLAN_MODE_PROMPT,
    THINKING_MODE_PROMPT,
    HEADLESS_MODE_PROMPT,
    get_mode_prompt,
)


__all__ = [
    # Base
    "Mode",
    "ModeConfig",
    "ModeContext",
    "ModeName",
    "ModeState",
    "NormalMode",
    # Manager
    "ModeManager",
    "ModeError",
    "ModeNotFoundError",
    "ModeSwitchError",
    # Plan
    "Plan",
    "PlanMode",
    "PlanStep",
    # Thinking
    "ThinkingConfig",
    "ThinkingMode",
    "ThinkingResult",
    "should_suggest_thinking",
    # Headless
    "HeadlessConfig",
    "HeadlessMode",
    "HeadlessResult",
    "OutputFormat",
    "create_headless_config_from_args",
    # Prompts
    "PLAN_MODE_PROMPT",
    "THINKING_MODE_PROMPT",
    "HEADLESS_MODE_PROMPT",
    "get_mode_prompt",
]


def setup_modes(manager: ModeManager | None = None) -> ModeManager:
    """Set up all default modes.

    Args:
        manager: Existing manager or None to use singleton

    Returns:
        Configured mode manager
    """
    if manager is None:
        manager = ModeManager.get_instance()

    # Register standard modes
    manager.register_mode(PlanMode())
    manager.register_mode(ThinkingMode())
    manager.register_mode(HeadlessMode())

    return manager
```

---

## Step 8: REPL Integration

Integration points in `src/opencode/repl/repl.py`:

```python
# In REPL class

from opencode.modes import (
    ModeManager,
    ModeContext,
    ModeName,
    setup_modes,
)


class REPL:
    def __init__(self, ...):
        # ... existing init ...

        # Initialize mode manager
        self.mode_manager = setup_modes()

        # Register mode change callback
        self.mode_manager.on_mode_change(self._on_mode_change)

    def _create_mode_context(self) -> ModeContext:
        """Create context for mode operations."""
        return ModeContext(
            session=self.session_manager.current,
            config=self.config,
            output=self._output,
        )

    def _on_mode_change(
        self,
        old_mode: ModeName,
        new_mode: ModeName
    ) -> None:
        """Handle mode changes."""
        # Update status line, prompts, etc.
        self._update_mode_display(new_mode)

    def _get_system_prompt(self) -> str:
        """Get system prompt with mode modifications."""
        base = self._load_base_prompt()
        return self.mode_manager.get_system_prompt(base)

    def _process_response(self, response: str) -> str:
        """Process response through current mode."""
        return self.mode_manager.process_response(response)

    async def _handle_input(self, user_input: str) -> None:
        """Handle user input with mode awareness."""
        # Check for auto-activation
        suggested_mode = self.mode_manager.check_auto_activation(
            user_input
        )
        if suggested_mode:
            context = self._create_mode_context()
            self.mode_manager.switch_mode(suggested_mode, context)

        # ... rest of input handling ...
```

---

## Testing Strategy

1. Unit test each mode class
2. Unit test ModeManager
3. Integration test mode switching
4. E2E test headless mode
5. Test mode state persistence
6. Test auto-activation patterns
