# Phase 4.1: Permission System - Requirements

**Phase:** 4.1
**Name:** Permission System
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## Overview

Phase 4.1 implements a comprehensive permission system that controls tool execution based on configurable rules. This system provides safety guardrails by requiring user confirmation for potentially dangerous operations while allowing trusted operations to execute automatically.

---

## Goals

1. Define permission levels (ALLOW, ASK, DENY)
2. Create permission rules with pattern matching
3. Implement user confirmation flow for ASK permissions
4. Provide permission persistence and configuration
5. Integrate with tool execution pipeline

---

## Non-Goals (This Phase)

- Complex permission inheritance hierarchies
- Role-based access control (RBAC)
- Permission auditing and logging (beyond basic)
- Network-based permission decisions
- Time-based permission rules

---

## Functional Requirements

### FR-1: Permission Levels

**FR-1.1:** Define three permission levels
- `ALLOW` - Execute without user confirmation
- `ASK` - Require user confirmation before execution
- `DENY` - Block execution entirely

**FR-1.2:** Permission levels should be comparable
- DENY > ASK > ALLOW (in terms of restrictiveness)
- When multiple rules match, most restrictive wins

**FR-1.3:** Default permission level
- Tools without explicit rules default to ASK
- Default can be configured globally

### FR-2: Permission Rules

**FR-2.1:** Rule structure
- Rule has a pattern (glob or regex)
- Rule has a target (tool name, argument value, or both)
- Rule has a permission level
- Rule has optional description

**FR-2.2:** Pattern matching types
- Exact match: `tool:read`
- Glob pattern: `tool:*`, `arg:*.py`
- Regex pattern: `tool:^bash.*`, `arg:^/tmp/.*`

**FR-2.3:** Rule targets
- Tool name: `tool:bash` matches bash tool
- Tool argument: `arg:file_path:/etc/*` matches file_path argument
- Combined: `tool:write,arg:file_path:/etc/*`

**FR-2.4:** Rule precedence
- More specific rules take precedence over general rules
- Explicit rules take precedence over defaults
- DENY rules always take precedence when equal specificity

### FR-3: Permission Checker

**FR-3.1:** Create `PermissionChecker` class
- Check if a tool execution is allowed
- Return the applicable permission level
- Return the matching rule (if any)

**FR-3.2:** Support multiple rule sources
- Global rules (from settings)
- Project rules (from .src/forge/permissions.json)
- Session rules (temporary overrides)

**FR-3.3:** Rule evaluation order
1. Session rules (highest priority)
2. Project rules
3. Global rules
4. Default permission

**FR-3.4:** Provide explanation
- Return which rule matched
- Return why the permission was granted/denied

### FR-4: User Confirmation

**FR-4.1:** Create confirmation prompt interface
- Display tool name and arguments
- Show what will be executed
- Options: Allow, Allow Always, Deny, Deny Always

**FR-4.2:** "Allow Always" option
- Creates a session rule for this tool/argument combination
- Persists until session ends

**FR-4.3:** "Deny Always" option
- Creates a session rule to deny
- Persists until session ends

**FR-4.4:** Timeout handling
- Confirmation prompts should have configurable timeout
- Default action on timeout (configurable: deny or abort)

### FR-5: Permission Configuration

**FR-5.1:** Global permission settings
- Stored in user config directory
- Applied to all projects
- Can be overridden by project settings

**FR-5.2:** Project permission settings
- Stored in `.src/forge/permissions.json`
- Applied only to this project
- Takes precedence over global settings

**FR-5.3:** Permission file format
```json
{
  "default": "ask",
  "rules": [
    {
      "pattern": "tool:read",
      "permission": "allow",
      "description": "Allow reading any file"
    },
    {
      "pattern": "tool:bash,arg:command:rm *",
      "permission": "deny",
      "description": "Never allow rm commands"
    }
  ]
}
```

**FR-5.4:** Runtime permission modification
- Add rules during session
- Remove rules during session
- Rules don't persist unless explicitly saved

### FR-6: Permission Categories

**FR-6.1:** Pre-defined permission categories
- `read_operations` - File reading, globbing
- `write_operations` - File writing, editing
- `execute_operations` - Shell commands
- `network_operations` - Web requests
- `destructive_operations` - Deletion, overwriting

**FR-6.2:** Category-based rules
- Rules can target categories instead of individual tools
- Example: `category:write_operations` → ASK

**FR-6.3:** Tool category mapping
- Each tool declares its category
- Categories used for rule matching

---

## Non-Functional Requirements

### NFR-1: Performance
- Permission check < 1ms for typical rule sets
- Rule loading < 100ms on startup
- Pattern matching optimized with caching

### NFR-2: Security
- Permission files should be readable only by owner
- No way to escalate from ASK to ALLOW without user action
- DENY rules cannot be bypassed programmatically

### NFR-3: Usability
- Clear error messages when permission denied
- Informative confirmation prompts
- Easy rule management

### NFR-4: Reliability
- Fail-safe: default to ASK on errors
- Permission file corruption handled gracefully
- Invalid rules logged but don't break system

---

## Technical Specifications

### Package Structure

```
src/forge/permissions/
├── __init__.py           # Package exports
├── models.py             # Permission data models
├── rules.py              # Rule definition and matching
├── checker.py            # Permission checker
├── prompt.py             # User confirmation prompts
└── config.py             # Permission configuration
```

### Class Signatures

```python
# models.py
from enum import Enum
from dataclasses import dataclass

class PermissionLevel(str, Enum):
    """Permission levels in order of restrictiveness."""
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"

    def __lt__(self, other: "PermissionLevel") -> bool:
        """ALLOW < ASK < DENY."""
        order = [PermissionLevel.ALLOW, PermissionLevel.ASK, PermissionLevel.DENY]
        return order.index(self) < order.index(other)


class PermissionCategory(str, Enum):
    """Categories of operations for permission grouping."""
    READ = "read_operations"
    WRITE = "write_operations"
    EXECUTE = "execute_operations"
    NETWORK = "network_operations"
    DESTRUCTIVE = "destructive_operations"


@dataclass
class PermissionRule:
    """A single permission rule."""
    pattern: str
    permission: PermissionLevel
    description: str = ""
    enabled: bool = True

    def matches(self, tool_name: str, arguments: dict) -> bool:
        """Check if this rule matches the given tool and arguments."""
        ...

    def specificity(self) -> int:
        """Return specificity score (higher = more specific)."""
        ...


@dataclass
class PermissionResult:
    """Result of a permission check."""
    level: PermissionLevel
    rule: PermissionRule | None
    reason: str


# rules.py
class RuleSet:
    """Collection of permission rules with evaluation logic."""

    rules: list[PermissionRule]
    default: PermissionLevel

    def __init__(
        self,
        rules: list[PermissionRule] | None = None,
        default: PermissionLevel = PermissionLevel.ASK,
    ): ...

    def add_rule(self, rule: PermissionRule) -> None: ...
    def remove_rule(self, pattern: str) -> bool: ...
    def evaluate(self, tool_name: str, arguments: dict) -> PermissionResult: ...

    @classmethod
    def from_dict(cls, data: dict) -> "RuleSet": ...
    def to_dict(self) -> dict: ...


class PatternMatcher:
    """Matches tool/argument patterns against rules."""

    @staticmethod
    def match_glob(pattern: str, value: str) -> bool: ...

    @staticmethod
    def match_regex(pattern: str, value: str) -> bool: ...

    @staticmethod
    def parse_pattern(pattern: str) -> tuple[str, str, str]: ...


# checker.py
class PermissionChecker:
    """Checks permissions for tool execution."""

    global_rules: RuleSet
    project_rules: RuleSet | None
    session_rules: RuleSet

    def __init__(
        self,
        global_rules: RuleSet | None = None,
        project_rules: RuleSet | None = None,
    ): ...

    def check(self, tool_name: str, arguments: dict) -> PermissionResult: ...
    def add_session_rule(self, rule: PermissionRule) -> None: ...
    def clear_session_rules(self) -> None: ...

    @classmethod
    def from_config(cls, config: "Config") -> "PermissionChecker": ...


# prompt.py
from enum import Enum

class ConfirmationChoice(str, Enum):
    """User choices for permission confirmation."""
    ALLOW = "allow"
    ALLOW_ALWAYS = "allow_always"
    DENY = "deny"
    DENY_ALWAYS = "deny_always"


@dataclass
class ConfirmationRequest:
    """Request for user confirmation."""
    tool_name: str
    arguments: dict
    description: str
    timeout: float = 30.0


class PermissionPrompt:
    """Handles user confirmation prompts."""

    async def confirm(self, request: ConfirmationRequest) -> ConfirmationChoice: ...
    def format_request(self, request: ConfirmationRequest) -> str: ...


# config.py
class PermissionConfig:
    """Manages permission configuration files."""

    @staticmethod
    def load_global() -> RuleSet: ...

    @staticmethod
    def load_project(path: Path) -> RuleSet | None: ...

    @staticmethod
    def save_global(rules: RuleSet) -> None: ...

    @staticmethod
    def save_project(path: Path, rules: RuleSet) -> None: ...

    @staticmethod
    def get_default_rules() -> list[PermissionRule]: ...
```

---

## Default Permission Rules

The system should include sensible defaults:

```python
DEFAULT_RULES = [
    # Allow read operations
    PermissionRule("tool:read", PermissionLevel.ALLOW, "Allow file reading"),
    PermissionRule("tool:glob", PermissionLevel.ALLOW, "Allow file searching"),
    PermissionRule("tool:grep", PermissionLevel.ALLOW, "Allow content searching"),

    # Ask for write operations
    PermissionRule("tool:write", PermissionLevel.ASK, "Confirm file writing"),
    PermissionRule("tool:edit", PermissionLevel.ASK, "Confirm file editing"),

    # Ask for execution
    PermissionRule("tool:bash", PermissionLevel.ASK, "Confirm shell commands"),

    # Deny dangerous patterns
    PermissionRule("tool:bash,arg:command:*rm -rf*", PermissionLevel.DENY,
                   "Block recursive force delete"),
    PermissionRule("tool:bash,arg:command:*> /dev/*", PermissionLevel.DENY,
                   "Block writing to devices"),
    PermissionRule("tool:write,arg:file_path:/etc/*", PermissionLevel.DENY,
                   "Block writing to /etc"),
]
```

---

## Confirmation Prompt Format

```
┌─────────────────────────────────────────────────────────────┐
│  Permission Required                                         │
├─────────────────────────────────────────────────────────────┤
│  Tool: bash                                                  │
│  Command: git status                                         │
│                                                             │
│  This will execute a shell command.                         │
│                                                             │
│  [a] Allow    [A] Allow Always    [d] Deny    [D] Deny Always│
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### With Tool System (Phase 2.1)
- ToolExecutor calls PermissionChecker before execution
- Tools declare their category for permission grouping
- Permission denied raises PermissionError

### With Configuration (Phase 1.2)
- Global rules stored in user config
- Project rules in .forge directory
- Settings control default behavior

### With Hooks (Phase 4.2)
- Permission events can trigger hooks
- Hooks can modify permission decisions
- Audit logging through hooks

### With REPL (Phase 1.3)
- Confirmation prompts displayed in terminal
- User input handled through REPL

---

## Error Scenarios

| Scenario | Handling |
|----------|----------|
| Invalid rule pattern | Log warning, skip rule |
| Corrupted permission file | Log error, use defaults |
| Permission check timeout | Treat as DENY |
| Missing permission file | Use defaults only |
| Circular rule references | Detect and error |

---

## Testing Requirements

1. Unit tests for PermissionLevel comparison
2. Unit tests for pattern matching (glob and regex)
3. Unit tests for rule evaluation
4. Unit tests for rule precedence
5. Unit tests for PermissionChecker
6. Unit tests for configuration loading
7. Integration tests with tool execution
8. Test permission prompt formatting
9. Test session rule management
10. Test coverage ≥ 90%

---

## Acceptance Criteria

1. Permission levels correctly order (ALLOW < ASK < DENY)
2. Rules match tool names with glob patterns
3. Rules match arguments with glob/regex patterns
4. Most restrictive matching rule wins
5. Session rules override project/global rules
6. Confirmation prompts display correctly
7. "Allow Always" creates session rule
8. "Deny Always" creates session rule
9. Permission files load and save correctly
10. Default rules provide sensible behavior
