# Code-Forge: Extension Patterns

How to extend the system with new functionality.

---

## Adding a New Tool

### 1. Create the tool class

```python
# src/code_forge/tools/file/my_tool.py
from code_forge.tools.base import BaseTool, ToolCategory, ToolParameter, ToolResult, ExecutionContext

class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Description for the LLM explaining what this tool does."

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE  # or EXECUTION, WEB, etc.

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="input",
                type="string",
                description="The input to process",
                required=True,
            ),
            ToolParameter(
                name="optional_flag",
                type="boolean",
                description="An optional flag",
                required=False,
                default=False,
            ),
        ]

    async def _execute(self, context: ExecutionContext, **kwargs) -> ToolResult:
        input_value = kwargs["input"]
        flag = kwargs.get("optional_flag", False)

        try:
            # Do the work
            result = f"Processed: {input_value}"
            return ToolResult.ok(result)
        except Exception as e:
            return ToolResult.fail(str(e))
```

### 2. Register the tool

```python
# src/code_forge/tools/__init__.py
from code_forge.tools.file.my_tool import MyTool

def register_all_tools() -> None:
    registry = ToolRegistry()
    # ... existing tools ...
    registry.register(MyTool())
```

### 3. Write tests

```python
# tests/unit/tools/file/test_my_tool.py
import pytest
from code_forge.tools.file.my_tool import MyTool
from code_forge.tools.base import ExecutionContext

@pytest.fixture
def tool():
    return MyTool()

@pytest.fixture
def context():
    return ExecutionContext(working_dir="/tmp")

async def test_my_tool_success(tool, context):
    result = await tool.execute(context, input="test")
    assert result.success
    assert "Processed: test" in result.output

async def test_my_tool_missing_param(tool, context):
    result = await tool.execute(context)  # Missing required 'input'
    assert not result.success
    assert "Missing required parameter" in result.error
```

---

## Adding a New Slash Command

### 1. Create the command class

```python
# src/code_forge/commands/builtin/my_commands.py
from code_forge.commands.base import Command, CommandCategory, CommandResult, CommandArgument, ArgumentType

class MyCommand(Command):
    name = "mycommand"
    description = "Does something useful"
    category = CommandCategory.OTHER
    aliases = ["mc", "my"]

    arguments = [
        CommandArgument(
            name="target",
            type=ArgumentType.STRING,
            description="The target to operate on",
            required=True,
        ),
    ]

    async def execute(
        self,
        args: list[str],
        kwargs: dict[str, any],
        context: CommandContext,
    ) -> CommandResult:
        target = kwargs.get("target") or (args[0] if args else None)

        if not target:
            return CommandResult.error("Target required")

        # Do the work
        return CommandResult.success(f"Processed: {target}")
```

### 2. Register the command

```python
# src/code_forge/commands/executor.py
from code_forge.commands.builtin.my_commands import MyCommand

def register_builtin_commands() -> None:
    registry = CommandRegistry.get_instance()
    # ... existing commands ...
    registry.register(MyCommand())
```

---

## Adding a New Agent Type

### 1. Define the agent type

```python
# src/code_forge/agents/types.py
CUSTOM_AGENT = AgentTypeDefinition(
    type_id="custom",
    name="Custom Agent",
    description="Specialized agent for custom tasks",
    prompt_template="""You are a specialized agent for custom tasks.
Your goal is to: {task}

Focus on:
- Specific capability 1
- Specific capability 2
""",
    default_tools=["read", "write", "glob", "grep"],
    default_max_tokens=30000,
    default_max_time=180,
)

# Register in AgentTypeRegistry._builtin_types
```

### 2. Create agent implementation (optional)

```python
# src/code_forge/agents/builtin/custom.py
from code_forge.agents.base import Agent, AgentConfig, AgentContext
from code_forge.agents.result import AgentResult

class CustomAgent(Agent):
    @property
    def agent_type(self) -> str:
        return "custom"

    async def execute(self) -> AgentResult:
        self._start_execution()
        try:
            # Custom execution logic
            output = await self._run_custom_logic()
            result = AgentResult.ok(output)
            self._complete_execution(result)
            return result
        except Exception as e:
            result = AgentResult.fail(str(e))
            self._complete_execution(result, success=False)
            return result
```

---

## Adding a New Skill

### Option A: YAML file (recommended)

```yaml
# ~/.forge/skills/my_skill.yaml
name: my-skill
description: Does specialized work
version: 1.0.0
author: Your Name
tags: [utility, custom]
aliases: [ms]

prompt: |
  You are now operating in my-skill mode.

  When activated, you should:
  - Focus on specific task type
  - Use these tools preferentially: {tools}

  Guidelines:
  - Guideline 1
  - Guideline 2

tools:
  - read
  - write
  - bash

config:
  - name: max_depth
    type: integer
    description: Maximum depth to search
    default: 3
```

### Option B: Markdown file

```markdown
---
name: my-skill
description: Does specialized work
version: 1.0.0
tools: [read, write, bash]
---

# My Skill

You are now operating in my-skill mode.

## Guidelines

- Guideline 1
- Guideline 2
```

Skills are auto-discovered from `~/.forge/skills/` and `.forge/skills/`.

---

## Adding a New Operating Mode

```python
# src/code_forge/modes/custom.py
from code_forge.modes.base import Mode, ModeConfig, ModeContext, ModeName

class CustomMode(Mode):
    def __init__(self):
        config = ModeConfig(
            system_prompt_addition="You are now in custom mode...",
            tools_allowed=None,  # None = all tools
            tools_denied=["dangerous_tool"],
        )
        super().__init__(ModeName.CUSTOM, config)  # Add to ModeName enum

    def activate(self, context: ModeContext) -> None:
        super().activate(context)
        context.output("Custom mode activated")

    def deactivate(self, context: ModeContext) -> None:
        super().deactivate(context)
        context.output("Custom mode deactivated")

    def modify_prompt(self, base_prompt: str) -> str:
        return base_prompt + "\n\n" + self.config.system_prompt_addition
```

---

## Adding Permission Rules

```python
# src/code_forge/permissions/config.py
DEFAULT_RULES.append(
    PermissionRule(
        name="my_custom_rule",
        pattern="tool:my_tool:*",
        level=PermissionLevel.ASK,
        description="Require confirmation for my_tool",
        priority=50,
    )
)
```

Or via config file:
```yaml
# ~/.forge/permissions.yaml
rules:
  - name: allow_my_tool
    pattern: "tool:my_tool:safe_*"
    level: allow
  - name: deny_dangerous
    pattern: "tool:my_tool:dangerous_*"
    level: deny
```

---

## Adding Lifecycle Hooks

```yaml
# ~/.forge/hooks.yaml
hooks:
  - event: "tool:pre_execute:my_tool"
    command: "echo 'About to run my_tool' >> /tmp/tool.log"
    timeout: 5.0

  - event: "tool:post_execute:my_tool"
    command: "notify-send 'my_tool completed'"
    timeout: 5.0
```

Or programmatically:
```python
from code_forge.hooks import HookRegistry, Hook

registry = HookRegistry.get_instance()
registry.register(Hook(
    event_pattern="tool:post_execute:my_tool",
    command="echo 'Done!'",
    timeout=5.0,
))
```
