# Phase 4.1: Permission System - Wireframes

**Phase:** 4.1
**Name:** Permission System
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## 1. Permission Check Usage

### Basic Permission Check
```python
from forge.permissions import (
    PermissionChecker,
    PermissionLevel,
    PermissionResult,
)

# Create checker (typically done once at startup)
checker = PermissionChecker.from_config(config)

# Check permission for a tool
result = checker.check("bash", {"command": "git status"})

# Handle result
if result.allowed:
    # Execute immediately without confirmation
    print("Executing...")
elif result.needs_confirmation:
    # Need to ask user
    print(f"Please confirm: {result.reason}")
else:  # result.denied
    # Cannot execute
    print(f"Permission denied: {result.reason}")
```

### Check Result Properties
```python
result = checker.check("bash", {"command": "rm -rf /"})

print(f"Level: {result.level}")          # PermissionLevel.DENY
print(f"Rule: {result.rule}")            # PermissionRule(pattern="tool:bash,arg:command:*rm -rf*")
print(f"Reason: {result.reason}")        # "Block recursive force delete"
print(f"Allowed: {result.allowed}")      # False
print(f"Needs confirm: {result.needs_confirmation}")  # False
print(f"Denied: {result.denied}")        # True
```

---

## 2. Permission Rules

### Creating Rules
```python
from forge.permissions import PermissionRule, PermissionLevel

# Simple tool rule
rule1 = PermissionRule(
    pattern="tool:read",
    permission=PermissionLevel.ALLOW,
    description="Allow file reading",
)

# Argument-specific rule
rule2 = PermissionRule(
    pattern="tool:bash,arg:command:*git*",
    permission=PermissionLevel.ALLOW,
    description="Allow git commands",
)

# Category rule
rule3 = PermissionRule(
    pattern="category:write_operations",
    permission=PermissionLevel.ASK,
    description="Confirm all write operations",
)

# High priority deny rule
rule4 = PermissionRule(
    pattern="tool:bash,arg:command:*rm -rf*",
    permission=PermissionLevel.DENY,
    description="Block recursive force delete",
    priority=50,  # Higher priority
)
```

### Rule Serialization
```python
# Serialize
data = rule1.to_dict()
print(data)
# Output:
# {
#     "pattern": "tool:read",
#     "permission": "allow",
#     "description": "Allow file reading",
#     "enabled": true,
#     "priority": 0
# }

# Deserialize
rule = PermissionRule.from_dict(data)
```

---

## 3. Pattern Matching Examples

### Pattern Syntax
```python
from forge.permissions import PatternMatcher

# Tool patterns
PatternMatcher.match("tool:bash", "bash", {})          # True
PatternMatcher.match("tool:bash*", "bash_output", {})  # True
PatternMatcher.match("tool:*", "any_tool", {})         # True

# Argument patterns
PatternMatcher.match(
    "arg:command:*git*",
    "bash",
    {"command": "git status"}
)  # True

PatternMatcher.match(
    "arg:file_path:*.py",
    "read",
    {"file_path": "/src/main.py"}
)  # True

# Regex patterns (starts with ^, contains +, etc.)
PatternMatcher.match(
    "arg:file_path:^/etc/.*",
    "write",
    {"file_path": "/etc/passwd"}
)  # True

# Combined patterns (all must match)
PatternMatcher.match(
    "tool:bash,arg:command:*rm*",
    "bash",
    {"command": "rm file.txt"}
)  # True

PatternMatcher.match(
    "tool:bash,arg:command:*rm*",
    "read",  # Wrong tool
    {"command": "rm file.txt"}
)  # False

# Category patterns
PatternMatcher.match(
    "category:execute_operations",
    "bash",  # bash is in execute_operations
    {}
)  # True
```

### Pattern Specificity
```python
# More specific patterns have higher scores
PatternMatcher.specificity("tool:bash,arg:command:git")  # Highest
PatternMatcher.specificity("tool:bash,arg:command:*")    # High
PatternMatcher.specificity("tool:bash")                  # Medium
PatternMatcher.specificity("tool:*")                     # Low
PatternMatcher.specificity("category:execute_operations") # Lowest
```

---

## 4. Rule Set Management

### Creating and Using RuleSets
```python
from forge.permissions import RuleSet, PermissionRule, PermissionLevel

# Create empty rule set
rules = RuleSet(default=PermissionLevel.ASK)

# Add rules
rules.add_rule(PermissionRule("tool:read", PermissionLevel.ALLOW))
rules.add_rule(PermissionRule("tool:bash", PermissionLevel.ASK))
rules.add_rule(PermissionRule(
    "tool:bash,arg:command:*rm -rf*",
    PermissionLevel.DENY,
    priority=50
))

# Evaluate
result = rules.evaluate("read", {})
print(result.level)  # ALLOW

result = rules.evaluate("bash", {"command": "ls"})
print(result.level)  # ASK

result = rules.evaluate("bash", {"command": "rm -rf /"})
print(result.level)  # DENY

# Remove rule
rules.remove_rule("tool:read")

# Serialize
data = rules.to_dict()
# {
#     "default": "ask",
#     "rules": [
#         {"pattern": "tool:bash", "permission": "ask", ...},
#         {"pattern": "tool:bash,arg:command:*rm -rf*", "permission": "deny", ...}
#     ]
# }

# Deserialize
rules2 = RuleSet.from_dict(data)
```

---

## 5. Permission Checker

### Multi-Source Checking
```python
from forge.permissions import PermissionChecker, RuleSet, PermissionRule, PermissionLevel

# Create with multiple rule sources
global_rules = RuleSet(default=PermissionLevel.ASK)
global_rules.add_rule(PermissionRule("tool:read", PermissionLevel.ALLOW))
global_rules.add_rule(PermissionRule("tool:bash", PermissionLevel.ASK))

project_rules = RuleSet()
project_rules.add_rule(PermissionRule("tool:write", PermissionLevel.ALLOW))  # Project allows writes

checker = PermissionChecker(
    global_rules=global_rules,
    project_rules=project_rules,
)

# Check uses priority: session > project > global
result = checker.check("write", {})
print(result.level)  # ALLOW (from project rules)

result = checker.check("bash", {})
print(result.level)  # ASK (from global rules)
```

### Session Rules
```python
# Add session rule (highest priority)
checker.add_session_rule(PermissionRule(
    "tool:bash",
    PermissionLevel.ALLOW,
    "User allowed bash",
    priority=100
))

# Now bash is allowed without asking
result = checker.check("bash", {})
print(result.level)  # ALLOW (session rule)

# Convenience methods
checker.allow_always("write", {"file_path": "/tmp/test.txt"})
checker.deny_always("bash", {"command": "sudo"})

# Get session rules
for rule in checker.get_session_rules():
    print(f"{rule.pattern} -> {rule.permission}")

# Clear session rules
checker.clear_session_rules()
```

---

## 6. User Confirmation

### Confirmation Prompt Display
```
┌────────────────────────────────────────────────────────────────┐
│  Permission Required                                            │
├────────────────────────────────────────────────────────────────┤
│  Tool: bash                                                     │
│  command: git commit -m "Update readme"                         │
│                                                                 │
│  Confirm shell commands                                         │
│                                                                 │
│  [a] Allow    [A] Allow Always    [d] Deny    [D] Deny Always   │
└────────────────────────────────────────────────────────────────┘

Choice [a/A/d/D]: _
```

### Prompt Implementation
```python
from forge.permissions import (
    PermissionPrompt,
    ConfirmationRequest,
    ConfirmationChoice,
)

# Create prompt handler
prompt = PermissionPrompt()

# Create request
request = ConfirmationRequest(
    tool_name="bash",
    arguments={"command": "git status"},
    description="Execute shell command",
    timeout=30.0,
)

# Synchronous confirmation
choice = prompt.confirm(request)

# Asynchronous confirmation with timeout
choice = await prompt.confirm_async(request)

# Handle choice
if choice == ConfirmationChoice.ALLOW:
    print("User allowed this time")
elif choice == ConfirmationChoice.ALLOW_ALWAYS:
    print("User allowed and wants to remember")
elif choice == ConfirmationChoice.DENY:
    print("User denied this time")
elif choice == ConfirmationChoice.DENY_ALWAYS:
    print("User denied and wants to remember")
elif choice == ConfirmationChoice.TIMEOUT:
    print("User didn't respond in time")
```

### Custom Prompt Handlers
```python
# Custom input/output for testing or GUI
def mock_input(prompt: str) -> str:
    return "a"  # Always allow

def mock_output(text: str) -> None:
    print(f"[MOCK] {text}")

prompt = PermissionPrompt(
    input_handler=mock_input,
    output_handler=mock_output,
)
```

---

## 7. Configuration Files

### Global Configuration (~/.config/src/forge/permissions.json)
```json
{
  "default": "ask",
  "rules": [
    {
      "pattern": "tool:read",
      "permission": "allow",
      "description": "Allow file reading"
    },
    {
      "pattern": "tool:glob",
      "permission": "allow",
      "description": "Allow file searching"
    },
    {
      "pattern": "tool:grep",
      "permission": "allow",
      "description": "Allow content searching"
    },
    {
      "pattern": "tool:write",
      "permission": "ask",
      "description": "Confirm file writing"
    },
    {
      "pattern": "tool:bash",
      "permission": "ask",
      "description": "Confirm shell commands"
    },
    {
      "pattern": "tool:bash,arg:command:*rm -rf*",
      "permission": "deny",
      "description": "Block recursive force delete",
      "priority": 50
    }
  ]
}
```

### Project Configuration (.src/forge/permissions.json)
```json
{
  "default": "ask",
  "rules": [
    {
      "pattern": "tool:bash,arg:command:npm *",
      "permission": "allow",
      "description": "Allow npm commands in this project"
    },
    {
      "pattern": "tool:bash,arg:command:pytest*",
      "permission": "allow",
      "description": "Allow pytest in this project"
    },
    {
      "pattern": "tool:write,arg:file_path:./build/*",
      "permission": "allow",
      "description": "Allow writing to build directory"
    }
  ]
}
```

### Loading Configuration
```python
from forge.permissions import PermissionConfig

# Load global rules
global_rules = PermissionConfig.load_global()

# Load project rules (returns None if no config)
project_rules = PermissionConfig.load_project(Path("/path/to/project"))

# Save rules
PermissionConfig.save_global(global_rules)
PermissionConfig.save_project(Path("/path/to/project"), project_rules)

# Get default rules
defaults = PermissionConfig.get_default_rules()

# Reset to defaults
PermissionConfig.reset_to_defaults()
```

---

## 8. Tool Executor Integration

### With Permission Checking
```python
from forge.tools import ToolExecutor, ToolRegistry
from forge.permissions import (
    PermissionChecker,
    PermissionPrompt,
    PermissionError,
)

# Create executor with permissions
executor = ToolExecutor(
    registry=ToolRegistry.get_instance(),
    permission_checker=PermissionChecker.from_config(config),
    permission_prompt=PermissionPrompt(),
)

# Execute tool (permission checked automatically)
try:
    result = await executor.execute(
        tool=bash_tool,
        params={"command": "ls -la"},
        context=context,
    )
    print(result.output)
except PermissionError as e:
    print(f"Permission denied: {e}")
    print(f"Tool: {e.tool_name}")
    print(f"Reason: {e.result.reason}")
```

### Execution Flow
```python
# Internal flow of executor.execute():

# 1. Check permission
result = permission_checker.check(tool.name, params)

if result.denied:
    raise PermissionError(result, tool.name, params)

if result.needs_confirmation:
    # 2. Prompt user
    choice = await permission_prompt.confirm_async(request)

    # 3. Handle "always" choices
    if choice == ConfirmationChoice.ALLOW_ALWAYS:
        permission_checker.allow_always(tool.name, params)
    elif choice == ConfirmationChoice.DENY_ALWAYS:
        permission_checker.deny_always(tool.name, params)

    # 4. Check if allowed
    if choice not in (ALLOW, ALLOW_ALWAYS):
        raise PermissionError(...)

# 5. Execute tool
return await tool.execute(params, context)
```

---

## 9. Permission Error Handling

### Error Structure
```python
from forge.permissions import PermissionError, PermissionResult, PermissionLevel

# Create error
result = PermissionResult(
    level=PermissionLevel.DENY,
    rule=rule,
    reason="Blocked by security rule",
)
error = PermissionError(result, "bash", {"command": "rm -rf /"})

# Access attributes
print(error.tool_name)           # "bash"
print(error.arguments)           # {"command": "rm -rf /"}
print(error.result.level)        # PermissionLevel.DENY
print(error.result.reason)       # "Blocked by security rule"
print(str(error))                # "Permission denied for tool 'bash': Blocked by security rule"
```

### Catching Errors
```python
try:
    await executor.execute(tool, params, context)
except PermissionError as e:
    if e.result.denied:
        # Absolutely blocked
        logger.error(f"Tool {e.tool_name} blocked: {e.result.reason}")
    else:
        # User denied during confirmation
        logger.info(f"User declined {e.tool_name}")
```

---

## 10. Default Rules Reference

```python
from forge.permissions import DEFAULT_RULES

# Default rules include:

# ALLOW by default:
# - tool:read          (file reading)
# - tool:glob          (file searching)
# - tool:grep          (content searching)
# - tool:bash_output   (reading shell output)

# ASK by default:
# - tool:write         (file writing)
# - tool:edit          (file editing)
# - tool:notebook_edit (notebook editing)
# - tool:bash          (shell commands)
# - tool:kill_shell    (killing shells)

# DENY always:
# - tool:bash,arg:command:*rm -rf*  (recursive force delete)
# - tool:bash,arg:command:*rm -fr*  (recursive force delete)
# - tool:bash,arg:command:*> /dev/* (device writing)
# - tool:bash,arg:command:*mkfs*    (filesystem creation)
# - tool:bash,arg:command:*dd if=*  (disk copy)
# - tool:write,arg:file_path:/etc/* (system config)
# - tool:write,arg:file_path:/usr/* (system binaries)
# - tool:edit,arg:file_path:/etc/*  (system config editing)
```

---

## 11. Complete Usage Example

```python
"""Complete example of permission system usage."""

import asyncio
from pathlib import Path

from forge.config import Config
from forge.permissions import (
    PermissionChecker,
    PermissionPrompt,
    PermissionError,
    ConfirmationRequest,
    ConfirmationChoice,
    create_rule_from_choice,
)

async def execute_with_permissions(
    checker: PermissionChecker,
    prompt: PermissionPrompt,
    tool_name: str,
    arguments: dict,
):
    """Execute a tool with permission checking."""

    # Check permission
    result = checker.check(tool_name, arguments)

    print(f"Permission check for {tool_name}:")
    print(f"  Level: {result.level.value}")
    print(f"  Reason: {result.reason}")

    if result.denied:
        print("  -> DENIED: Cannot execute")
        return

    if result.needs_confirmation:
        print("  -> Needs confirmation...")

        request = ConfirmationRequest(
            tool_name=tool_name,
            arguments=arguments,
            description=f"Execute {tool_name}",
            timeout=30.0,
        )

        choice = await prompt.confirm_async(request)
        print(f"  -> User choice: {choice.value}")

        # Handle "always" choices
        rule = create_rule_from_choice(choice, tool_name, arguments)
        if rule:
            checker.add_session_rule(rule)
            print(f"  -> Created session rule: {rule.pattern}")

        if choice not in (ConfirmationChoice.ALLOW, ConfirmationChoice.ALLOW_ALWAYS):
            print("  -> Execution denied by user")
            return

    print("  -> Executing tool...")
    # Here you would actually execute the tool
    print("  -> Done!")


async def main():
    # Load configuration
    config = Config.load()

    # Create checker from config
    checker = PermissionChecker.from_config(config)

    # Create prompt handler
    prompt = PermissionPrompt()

    # Test various scenarios
    print("=" * 60)
    print("Test 1: Read operation (should be ALLOW)")
    await execute_with_permissions(
        checker, prompt,
        "read",
        {"file_path": "/tmp/test.txt"}
    )

    print("\n" + "=" * 60)
    print("Test 2: Shell command (should be ASK)")
    await execute_with_permissions(
        checker, prompt,
        "bash",
        {"command": "ls -la"}
    )

    print("\n" + "=" * 60)
    print("Test 3: Dangerous command (should be DENY)")
    await execute_with_permissions(
        checker, prompt,
        "bash",
        {"command": "rm -rf /"}
    )

    print("\n" + "=" * 60)
    print("Test 4: Same shell command again (check session rule)")
    await execute_with_permissions(
        checker, prompt,
        "bash",
        {"command": "ls -la"}
    )

    # Show session rules
    print("\n" + "=" * 60)
    print("Session rules created:")
    for rule in checker.get_session_rules():
        print(f"  {rule.pattern} -> {rule.permission.value}")


if __name__ == "__main__":
    asyncio.run(main())
```

Output:
```
============================================================
Test 1: Read operation (should be ALLOW)
Permission check for read:
  Level: allow
  Reason: Allow file reading
  -> Executing tool...
  -> Done!

============================================================
Test 2: Shell command (should be ASK)
Permission check for bash:
  Level: ask
  Reason: Confirm shell commands
  -> Needs confirmation...
┌────────────────────────────────────────────────────────────────┐
│  Permission Required                                            │
├────────────────────────────────────────────────────────────────┤
│  Tool: bash                                                     │
│  command: ls -la                                                │
│                                                                 │
│  Execute bash                                                   │
│                                                                 │
│  [a] Allow    [A] Allow Always    [d] Deny    [D] Deny Always   │
└────────────────────────────────────────────────────────────────┘

Choice [a/A/d/D]: A
  -> User choice: allow_always
  -> Created session rule: tool:bash
  -> Executing tool...
  -> Done!

============================================================
Test 3: Dangerous command (should be DENY)
Permission check for bash:
  Level: deny
  Reason: Block recursive force delete
  -> DENIED: Cannot execute

============================================================
Test 4: Same shell command again (check session rule)
Permission check for bash:
  Level: allow
  Reason: Session allow: tool:bash
  -> Executing tool...
  -> Done!

============================================================
Session rules created:
  tool:bash -> allow
```
