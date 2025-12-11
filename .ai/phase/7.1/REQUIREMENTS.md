# Phase 7.1: Subagents System - Requirements

**Phase:** 7.1
**Name:** Subagents System
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 2.1 (Tool System)

---

## Overview

Phase 7.1 implements the subagents system for Code-Forge, enabling the main agent to spawn specialized child agents for complex, multi-step tasks. Subagents run autonomously with their own context and tools, returning results to the parent agent upon completion.

---

## Goals

1. Spawn autonomous subagents for complex tasks
2. Manage subagent lifecycle (creation, execution, completion)
3. Provide specialized agent types (explore, plan, code-review)
4. Enable parallel subagent execution
5. Aggregate and present subagent results
6. Limit resource usage and prevent runaway agents

---

## Non-Goals (This Phase)

- Inter-agent communication (agents talk to each other)
- Agent hierarchies beyond parent-child
- Persistent agent pools
- Agent learning/memory sharing
- Visual agent workflow editor

---

## Functional Requirements

### FR-1: Subagent Core

**FR-1.1:** Agent definition
- Unique agent ID (UUID)
- Agent type (explore, plan, general, etc.)
- Agent description
- Specialized prompt additions
- Tool access configuration

**FR-1.2:** Agent context
- Inherit parent context optionally
- Independent message history
- Isolated tool state
- Resource limits (tokens, time, tool calls)

**FR-1.3:** Agent state
- PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
- Progress tracking
- Result storage
- Error capture

### FR-2: Agent Types

**FR-2.1:** Explore Agent
- Specialized for codebase exploration
- File search and reading tools
- Pattern matching capabilities
- Returns structured findings

**FR-2.2:** Plan Agent
- Specialized for creating implementation plans
- Architecture analysis tools
- Dependency identification
- Returns structured plan

**FR-2.3:** Code Review Agent
- Specialized for reviewing code changes
- Diff analysis tools
- Best practices checking
- Returns review with findings

**FR-2.4:** General Purpose Agent
- Full tool access
- Flexible task handling
- Returns task result

**FR-2.5:** Custom Agent Types
- Define new types via configuration
- Custom prompts and tools
- Plugin-defined agents

### FR-3: Agent Lifecycle

**FR-3.1:** Creation
- Spawn from parent agent
- Initialize with task description
- Assign resource limits
- Configure tools and context

**FR-3.2:** Execution
- Run independently of parent
- Manage own LLM calls
- Track progress and resources
- Handle errors gracefully

**FR-3.3:** Completion
- Return structured result
- Report resource usage
- Clean up resources
- Notify parent

**FR-3.4:** Cancellation
- Cancel running agent
- Timeout enforcement
- Partial result capture
- Resource cleanup

### FR-4: Agent Manager

**FR-4.1:** Spawning
- Create agents with config
- Track active agents
- Enforce limits on concurrent agents

**FR-4.2:** Monitoring
- Track agent status
- Resource usage monitoring
- Progress reporting

**FR-4.3:** Results
- Collect agent results
- Aggregate multiple results
- Format for parent consumption

**FR-4.4:** Cleanup
- Clean up completed agents
- Handle orphaned agents
- Resource recovery

### FR-5: Parallel Execution

**FR-5.1:** Concurrent agents
- Run multiple agents simultaneously
- Independent execution contexts
- Shared resource pool

**FR-5.2:** Synchronization
- Wait for specific agents
- Wait for all agents
- Collect results when ready

**FR-5.3:** Load balancing
- Limit concurrent API calls
- Queue excess agents
- Fair resource allocation

### FR-6: Resource Management

**FR-6.1:** Token limits
- Per-agent token budget
- Track usage during execution
- Abort on limit exceeded

**FR-6.2:** Time limits
- Per-agent timeout
- Background monitoring
- Graceful timeout handling

**FR-6.3:** Tool call limits
- Maximum tool invocations
- Prevent infinite loops
- Track and enforce

**FR-6.4:** Cost tracking
- Track API costs per agent
- Aggregate to session
- Budget enforcement

---

## Non-Functional Requirements

### NFR-1: Performance
- Agent spawn < 100ms
- Parallel execution efficient
- Minimal overhead per agent

### NFR-2: Reliability
- Agents isolated from each other
- Parent continues if child fails
- No resource leaks

### NFR-3: Observability
- Agent status visible
- Progress trackable
- Logs per agent

---

## Technical Specifications

### Package Structure

```
src/forge/agents/
├── __init__.py           # Package exports
├── base.py               # Base agent classes
├── types.py              # Agent type definitions
├── manager.py            # Agent manager
├── executor.py           # Agent execution
├── result.py             # Result handling
└── builtin/              # Built-in agent types
    ├── __init__.py
    ├── explore.py        # Explore agent
    ├── plan.py           # Plan agent
    ├── review.py         # Code review agent
    └── general.py        # General purpose agent
```

### Class Signatures

```python
# base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from uuid import UUID, uuid4


class AgentState(Enum):
    """Agent lifecycle states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_type: str
    description: str
    prompt_addition: str = ""
    tools: list[str] | None = None  # None = all tools
    inherit_context: bool = False
    max_tokens: int = 50000
    max_time_seconds: int = 300
    max_tool_calls: int = 100


@dataclass
class AgentContext:
    """Execution context for an agent."""
    parent_messages: list[dict] = field(default_factory=list)
    working_directory: str = "."
    environment: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result from agent execution."""
    success: bool
    output: str
    data: Any = None
    error: str | None = None
    tokens_used: int = 0
    time_seconds: float = 0.0
    tool_calls: int = 0


class Agent(ABC):
    """Base class for agents."""

    def __init__(
        self,
        task: str,
        config: AgentConfig,
        context: AgentContext | None = None,
    ):
        self.id: UUID = uuid4()
        self.task = task
        self.config = config
        self.context = context or AgentContext()
        self.state = AgentState.PENDING
        self._result: AgentResult | None = None

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return agent type identifier."""
        ...

    @abstractmethod
    async def execute(self) -> AgentResult:
        """Execute the agent task."""
        ...

    def cancel(self) -> None:
        """Cancel agent execution."""
        self.state = AgentState.CANCELLED

    @property
    def is_complete(self) -> bool:
        """Check if agent has finished."""
        return self.state in (
            AgentState.COMPLETED,
            AgentState.FAILED,
            AgentState.CANCELLED,
        )

    @property
    def result(self) -> AgentResult | None:
        """Get agent result if complete."""
        return self._result


# manager.py
from asyncio import Task
from typing import Awaitable


class AgentManager:
    """Manages agent lifecycle."""

    _instance: "AgentManager | None" = None

    def __init__(self, max_concurrent: int = 5):
        self._agents: dict[UUID, Agent] = {}
        self._tasks: dict[UUID, Task] = {}
        self._max_concurrent = max_concurrent
        self._on_complete: list[Callable[[Agent], None]] = []

    @classmethod
    def get_instance(cls) -> "AgentManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def spawn(
        self,
        agent_type: str,
        task: str,
        config: AgentConfig | None = None,
        context: AgentContext | None = None,
    ) -> Agent:
        """Spawn a new agent."""
        ...

    async def spawn_parallel(
        self,
        tasks: list[tuple[str, str]],  # (agent_type, task)
    ) -> list[Agent]:
        """Spawn multiple agents in parallel."""
        ...

    def get_agent(self, agent_id: UUID) -> Agent | None:
        """Get agent by ID."""
        ...

    def list_agents(
        self,
        state: AgentState | None = None,
    ) -> list[Agent]:
        """List agents, optionally filtered by state."""
        ...

    async def wait(self, agent_id: UUID) -> AgentResult:
        """Wait for specific agent to complete."""
        ...

    async def wait_all(
        self,
        agent_ids: list[UUID] | None = None,
    ) -> list[AgentResult]:
        """Wait for all specified agents."""
        ...

    def cancel(self, agent_id: UUID) -> bool:
        """Cancel a running agent."""
        ...

    def cancel_all(self) -> int:
        """Cancel all running agents."""
        ...

    def on_complete(self, callback: Callable[[Agent], None]) -> None:
        """Register completion callback."""
        ...

    def get_stats(self) -> dict:
        """Get agent statistics."""
        ...


# executor.py
class AgentExecutor:
    """Executes agent tasks."""

    def __init__(
        self,
        llm: Any,  # OpenRouterLLM
        tools: Any,  # ToolRegistry
    ):
        self.llm = llm
        self.tools = tools

    async def execute(self, agent: Agent) -> AgentResult:
        """Execute an agent task."""
        ...

    def _build_prompt(self, agent: Agent) -> str:
        """Build system prompt for agent."""
        ...

    def _filter_tools(self, agent: Agent) -> list:
        """Get tools available to agent."""
        ...

    def _check_limits(self, agent: Agent) -> bool:
        """Check if agent within limits."""
        ...


# types.py
from dataclasses import dataclass


@dataclass
class AgentTypeDefinition:
    """Definition of an agent type."""
    name: str
    description: str
    prompt_template: str
    default_tools: list[str] | None = None
    default_max_tokens: int = 50000
    default_max_time: int = 300


class AgentTypeRegistry:
    """Registry of available agent types."""

    _types: dict[str, AgentTypeDefinition]

    def register(self, type_def: AgentTypeDefinition) -> None:
        """Register an agent type."""
        ...

    def get(self, name: str) -> AgentTypeDefinition | None:
        """Get type definition by name."""
        ...

    def list_types(self) -> list[str]:
        """List all registered types."""
        ...
```

---

## Built-in Agent Types

### Explore Agent

```
Name: explore
Description: Explores codebase to answer questions
Default Tools: glob, grep, read
Prompt Addition:
  You are an exploration agent specialized in navigating codebases.
  Search for files, read code, and identify patterns.
  Return structured findings with file paths and relevant snippets.
```

### Plan Agent

```
Name: plan
Description: Creates implementation plans
Default Tools: glob, grep, read
Prompt Addition:
  You are a planning agent specialized in software architecture.
  Analyze the codebase structure and create detailed implementation plans.
  Return a structured plan with steps, files to modify, and dependencies.
```

### Code Review Agent

```
Name: code-review
Description: Reviews code changes
Default Tools: glob, grep, read, bash(git only)
Prompt Addition:
  You are a code review agent specialized in finding issues.
  Analyze code for bugs, security issues, and best practices.
  Return structured review with findings categorized by severity.
```

### General Purpose Agent

```
Name: general
Description: General purpose agent for any task
Default Tools: all
Prompt Addition:
  You are a general purpose coding agent.
  Complete the assigned task using available tools.
  Return a structured result describing what was accomplished.
```

---

## Agent Communication

### Parent to Agent

```python
# Spawn agent with task
agent = await manager.spawn(
    agent_type="explore",
    task="Find all files that handle user authentication",
    config=AgentConfig(max_tokens=10000),
)

# Wait for result
result = await manager.wait(agent.id)
```

### Agent Result Format

```python
AgentResult(
    success=True,
    output="Found 5 files related to authentication",
    data={
        "files": [
            {"path": "auth/login.py", "relevance": "high"},
            {"path": "auth/session.py", "relevance": "high"},
            {"path": "middleware/auth.py", "relevance": "medium"},
        ],
        "summary": "Authentication is handled by...",
    },
    tokens_used=3500,
    time_seconds=4.2,
    tool_calls=12,
)
```

---

## Integration Points

### With LangChain (Phase 3.2)
- Agents use LangChain for execution
- Tool binding works same as parent
- Message history management

### With Tool System (Phase 2.1)
- Tools filtered per agent type
- Tool calls tracked
- Results captured

### With Session (Phase 5.1)
- Agent results stored in session
- Resource usage tracked
- History preserved

---

## Testing Requirements

1. Unit tests for Agent base class
2. Unit tests for AgentManager
3. Unit tests for AgentExecutor
4. Unit tests for each built-in agent type
5. Integration tests with LLM
6. Parallel execution tests
7. Resource limit tests
8. Test coverage ≥ 90%

---

## Acceptance Criteria

1. Agents spawn and execute correctly
2. All built-in agent types work
3. Parallel execution functions
4. Resource limits enforced
5. Results properly returned
6. Cancellation works
7. Errors handled gracefully
8. Agent state tracked accurately
9. Parent notified on completion
10. No resource leaks
