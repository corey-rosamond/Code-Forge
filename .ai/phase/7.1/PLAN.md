# Phase 7.1: Subagents System - Implementation Plan

**Phase:** 7.1
**Name:** Subagents System
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 2.1 (Tool System)

---

## Implementation Order

1. `base.py` - Agent base classes and state
2. `result.py` - Result handling
3. `types.py` - Agent type registry
4. `executor.py` - Agent execution
5. `manager.py` - Agent lifecycle management
6. `builtin/` - Built-in agent types
7. `__init__.py` - Package exports
8. Integration with REPL

---

## Step 1: Agent Base Classes (base.py)

```python
"""
Base classes for the subagent system.

Provides foundational classes for creating and managing
autonomous subagents that execute specialized tasks.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
from uuid import UUID, uuid4


class AgentState(Enum):
    """Agent lifecycle states."""
    PENDING = "pending"      # Created but not started
    RUNNING = "running"      # Currently executing
    COMPLETED = "completed"  # Finished successfully
    FAILED = "failed"        # Finished with error
    CANCELLED = "cancelled"  # Manually cancelled


@dataclass
class ResourceLimits:
    """Resource limits for agent execution.

    Attributes:
        max_tokens: Maximum tokens for LLM calls
        max_time_seconds: Maximum execution time
        max_tool_calls: Maximum tool invocations
        max_iterations: Maximum agent loop iterations
    """
    max_tokens: int = 50000
    max_time_seconds: int = 300
    max_tool_calls: int = 100
    max_iterations: int = 50


@dataclass
class ResourceUsage:
    """Tracked resource usage during execution.

    Attributes:
        tokens_used: Total tokens consumed
        time_seconds: Execution time
        tool_calls: Number of tool invocations
        iterations: Number of agent loop iterations
        cost_usd: Estimated API cost
    """
    tokens_used: int = 0
    time_seconds: float = 0.0
    tool_calls: int = 0
    iterations: int = 0
    cost_usd: float = 0.0

    def exceeds(self, limits: ResourceLimits) -> str | None:
        """Check if usage exceeds any limit.

        Returns:
            Name of exceeded limit, or None if within limits
        """
        if self.tokens_used > limits.max_tokens:
            return "max_tokens"
        if self.time_seconds > limits.max_time_seconds:
            return "max_time_seconds"
        if self.tool_calls > limits.max_tool_calls:
            return "max_tool_calls"
        if self.iterations > limits.max_iterations:
            return "max_iterations"
        return None


@dataclass
class AgentConfig:
    """Configuration for an agent.

    Attributes:
        agent_type: Type identifier (explore, plan, etc.)
        description: Human-readable description
        prompt_addition: Additional system prompt text
        tools: Tool names to allow (None = all)
        inherit_context: Whether to include parent context
        limits: Resource limits
        model: Specific model to use (None = default)
    """
    agent_type: str
    description: str = ""
    prompt_addition: str = ""
    tools: list[str] | None = None
    inherit_context: bool = False
    limits: ResourceLimits = field(default_factory=ResourceLimits)
    model: str | None = None

    @classmethod
    def for_type(cls, agent_type: str, **overrides) -> "AgentConfig":
        """Create config for a known agent type."""
        from .types import AgentTypeRegistry
        registry = AgentTypeRegistry.get_instance()
        type_def = registry.get(agent_type)

        if type_def is None:
            return cls(agent_type=agent_type, **overrides)

        config = cls(
            agent_type=agent_type,
            description=type_def.description,
            prompt_addition=type_def.prompt_template,
            tools=type_def.default_tools,
            limits=ResourceLimits(
                max_tokens=type_def.default_max_tokens,
                max_time_seconds=type_def.default_max_time,
            ),
        )

        # Apply overrides
        for key, value in overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config


@dataclass
class AgentContext:
    """Execution context for an agent.

    Attributes:
        parent_messages: Messages from parent context
        working_directory: Working directory path
        environment: Environment variables
        metadata: Additional context data
        parent_id: ID of parent agent (if any)
    """
    parent_messages: list[dict] = field(default_factory=list)
    working_directory: str = "."
    environment: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_id: UUID | None = None


class Agent(ABC):
    """Base class for subagents.

    Agents are autonomous execution units that perform specific
    tasks and return structured results.
    """

    def __init__(
        self,
        task: str,
        config: AgentConfig,
        context: AgentContext | None = None,
    ):
        """Initialize agent.

        Args:
            task: The task description
            config: Agent configuration
            context: Execution context
        """
        self.id: UUID = uuid4()
        self.task = task
        self.config = config
        self.context = context or AgentContext()
        self.state = AgentState.PENDING
        self.created_at = datetime.now()
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None

        self._result: "AgentResult | None" = None
        self._usage = ResourceUsage()
        self._messages: list[dict] = []
        self._on_progress: list[Callable[[str], None]] = []
        self._cancelled = False

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Return agent type identifier."""
        ...

    @abstractmethod
    async def execute(self) -> "AgentResult":
        """Execute the agent task.

        Returns:
            AgentResult with execution outcome
        """
        ...

    def cancel(self) -> None:
        """Request cancellation of agent execution."""
        self._cancelled = True
        if self.state == AgentState.RUNNING:
            self.state = AgentState.CANCELLED
            self.completed_at = datetime.now()

    @property
    def is_cancelled(self) -> bool:
        """Check if cancellation requested."""
        return self._cancelled

    @property
    def is_complete(self) -> bool:
        """Check if agent has finished."""
        return self.state in (
            AgentState.COMPLETED,
            AgentState.FAILED,
            AgentState.CANCELLED,
        )

    @property
    def is_running(self) -> bool:
        """Check if agent is currently running."""
        return self.state == AgentState.RUNNING

    @property
    def result(self) -> "AgentResult | None":
        """Get agent result if complete."""
        return self._result

    @property
    def usage(self) -> ResourceUsage:
        """Get current resource usage."""
        return self._usage

    @property
    def messages(self) -> list[dict]:
        """Get agent message history."""
        return self._messages.copy()

    def on_progress(self, callback: Callable[[str], None]) -> None:
        """Register progress callback."""
        self._on_progress.append(callback)

    def _report_progress(self, message: str) -> None:
        """Report progress to callbacks."""
        for callback in self._on_progress:
            try:
                callback(message)
            except Exception:
                pass

    def _start_execution(self) -> None:
        """Mark execution as started."""
        self.state = AgentState.RUNNING
        self.started_at = datetime.now()

    def _complete_execution(
        self,
        result: "AgentResult",
        success: bool = True
    ) -> None:
        """Mark execution as complete."""
        self.state = AgentState.COMPLETED if success else AgentState.FAILED
        self.completed_at = datetime.now()
        self._result = result

    def to_dict(self) -> dict:
        """Serialize agent state."""
        return {
            "id": str(self.id),
            "agent_type": self.agent_type,
            "task": self.task,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "usage": {
                "tokens_used": self._usage.tokens_used,
                "time_seconds": self._usage.time_seconds,
                "tool_calls": self._usage.tool_calls,
            },
            "result": self._result.to_dict() if self._result else None,
        }
```

---

## Step 2: Result Handling (result.py)

```python
"""
Agent result handling.

Provides structured result types for agent execution outcomes.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import json


@dataclass
class AgentResult:
    """Result from agent execution.

    Attributes:
        success: Whether execution succeeded
        output: Human-readable output text
        data: Structured data (varies by agent type)
        error: Error message if failed
        tokens_used: Tokens consumed
        time_seconds: Execution time
        tool_calls: Number of tool invocations
        metadata: Additional result metadata
    """
    success: bool
    output: str
    data: Any = None
    error: str | None = None
    tokens_used: int = 0
    time_seconds: float = 0.0
    tool_calls: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @classmethod
    def ok(
        cls,
        output: str,
        data: Any = None,
        **kwargs
    ) -> "AgentResult":
        """Create successful result."""
        return cls(success=True, output=output, data=data, **kwargs)

    @classmethod
    def fail(
        cls,
        error: str,
        output: str = "",
        **kwargs
    ) -> "AgentResult":
        """Create failure result."""
        return cls(success=False, output=output, error=error, **kwargs)

    @classmethod
    def cancelled(cls, output: str = "") -> "AgentResult":
        """Create cancelled result."""
        return cls(
            success=False,
            output=output,
            error="Agent execution was cancelled",
        )

    @classmethod
    def timeout(cls, output: str = "") -> "AgentResult":
        """Create timeout result."""
        return cls(
            success=False,
            output=output,
            error="Agent execution timed out",
        )

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "output": self.output,
            "data": self._serialize_data(self.data),
            "error": self.error,
            "tokens_used": self.tokens_used,
            "time_seconds": self.time_seconds,
            "tool_calls": self.tool_calls,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }

    def _serialize_data(self, data: Any) -> Any:
        """Serialize data for JSON compatibility."""
        if data is None:
            return None
        if isinstance(data, (str, int, float, bool)):
            return data
        if isinstance(data, (list, tuple)):
            return [self._serialize_data(item) for item in data]
        if isinstance(data, dict):
            return {k: self._serialize_data(v) for k, v in data.items()}
        return str(data)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "AgentResult":
        """Deserialize from dictionary."""
        return cls(
            success=data["success"],
            output=data["output"],
            data=data.get("data"),
            error=data.get("error"),
            tokens_used=data.get("tokens_used", 0),
            time_seconds=data.get("time_seconds", 0.0),
            tool_calls=data.get("tool_calls", 0),
            metadata=data.get("metadata", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
        )


@dataclass
class AggregatedResult:
    """Aggregated results from multiple agents.

    Used when running parallel agents and combining results.
    """
    results: list[AgentResult]
    total_tokens: int = 0
    total_time: float = 0.0
    total_tool_calls: int = 0
    success_count: int = 0
    failure_count: int = 0

    def __post_init__(self):
        """Calculate totals from results."""
        for result in self.results:
            self.total_tokens += result.tokens_used
            self.total_time += result.time_seconds
            self.total_tool_calls += result.tool_calls
            if result.success:
                self.success_count += 1
            else:
                self.failure_count += 1

    @property
    def all_succeeded(self) -> bool:
        """Check if all agents succeeded."""
        return self.failure_count == 0

    @property
    def any_succeeded(self) -> bool:
        """Check if any agent succeeded."""
        return self.success_count > 0

    def get_successful(self) -> list[AgentResult]:
        """Get only successful results."""
        return [r for r in self.results if r.success]

    def get_failed(self) -> list[AgentResult]:
        """Get only failed results."""
        return [r for r in self.results if not r.success]

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "results": [r.to_dict() for r in self.results],
            "total_tokens": self.total_tokens,
            "total_time": self.total_time,
            "total_tool_calls": self.total_tool_calls,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }
```

---

## Step 3: Agent Types (types.py)

```python
"""
Agent type definitions and registry.

Provides built-in agent types and a registry for custom types.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AgentTypeDefinition:
    """Definition of an agent type.

    Attributes:
        name: Type identifier
        description: Human-readable description
        prompt_template: Additional system prompt
        default_tools: Tools available (None = all)
        default_max_tokens: Default token limit
        default_max_time: Default time limit (seconds)
        default_model: Preferred model (None = session default)
    """
    name: str
    description: str
    prompt_template: str
    default_tools: list[str] | None = None
    default_max_tokens: int = 50000
    default_max_time: int = 300
    default_model: str | None = None


# Built-in agent type definitions
EXPLORE_AGENT = AgentTypeDefinition(
    name="explore",
    description="Explores codebase to answer questions",
    prompt_template="""
You are an exploration agent specialized in navigating codebases.

Your task is to search for files, read code, and identify patterns
to answer the given question.

Guidelines:
1. Use glob to find files by pattern
2. Use grep to search for content
3. Use read to examine file contents
4. Be thorough but efficient
5. Focus on relevant information

Return structured findings with:
- File paths discovered
- Relevant code snippets
- Key observations
- Summary of findings
""".strip(),
    default_tools=["glob", "grep", "read"],
    default_max_tokens=30000,
    default_max_time=180,
)


PLAN_AGENT = AgentTypeDefinition(
    name="plan",
    description="Creates implementation plans",
    prompt_template="""
You are a planning agent specialized in software architecture.

Your task is to analyze the codebase and create a detailed
implementation plan for the given task.

Guidelines:
1. Explore existing code structure first
2. Identify affected files and modules
3. Consider dependencies and impacts
4. Break down into concrete steps
5. Note risks and considerations

Return a structured plan with:
- Summary of approach
- Numbered steps with file references
- Dependencies between steps
- Estimated complexity per step
- Success criteria
""".strip(),
    default_tools=["glob", "grep", "read"],
    default_max_tokens=40000,
    default_max_time=240,
)


CODE_REVIEW_AGENT = AgentTypeDefinition(
    name="code-review",
    description="Reviews code changes for issues",
    prompt_template="""
You are a code review agent specialized in finding issues.

Your task is to analyze code for bugs, security issues,
performance problems, and best practices violations.

Guidelines:
1. Read the relevant code carefully
2. Check for common bug patterns
3. Look for security vulnerabilities
4. Evaluate code style and clarity
5. Consider performance implications

Return a structured review with:
- Findings categorized by severity (critical, warning, suggestion)
- Specific file and line references
- Explanation of each issue
- Suggested fixes where applicable
- Overall assessment
""".strip(),
    default_tools=["glob", "grep", "read", "bash"],
    default_max_tokens=40000,
    default_max_time=300,
)


GENERAL_AGENT = AgentTypeDefinition(
    name="general",
    description="General purpose agent for any task",
    prompt_template="""
You are a general purpose coding agent.

Your task is to complete the assigned work using available tools.
Work autonomously to achieve the goal.

Guidelines:
1. Understand the task fully before acting
2. Use appropriate tools for each step
3. Handle errors gracefully
4. Verify your work when possible
5. Report what was accomplished

Return a structured result with:
- Summary of what was done
- Details of changes made
- Any issues encountered
- Verification performed
""".strip(),
    default_tools=None,  # All tools
    default_max_tokens=50000,
    default_max_time=300,
)


class AgentTypeRegistry:
    """Registry of available agent types.

    Singleton that maintains the catalog of agent types
    available for spawning.
    """

    _instance: "AgentTypeRegistry | None" = None

    def __init__(self):
        """Initialize with built-in types."""
        self._types: dict[str, AgentTypeDefinition] = {}
        self._register_builtins()

    @classmethod
    def get_instance(cls) -> "AgentTypeRegistry":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        cls._instance = None

    def _register_builtins(self) -> None:
        """Register built-in agent types."""
        for type_def in [
            EXPLORE_AGENT,
            PLAN_AGENT,
            CODE_REVIEW_AGENT,
            GENERAL_AGENT,
        ]:
            self._types[type_def.name] = type_def

    def register(self, type_def: AgentTypeDefinition) -> None:
        """Register an agent type.

        Args:
            type_def: Type definition to register

        Raises:
            ValueError: If type name already registered
        """
        if type_def.name in self._types:
            raise ValueError(f"Agent type already registered: {type_def.name}")
        self._types[type_def.name] = type_def

    def unregister(self, name: str) -> bool:
        """Unregister an agent type.

        Args:
            name: Type name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self._types:
            del self._types[name]
            return True
        return False

    def get(self, name: str) -> AgentTypeDefinition | None:
        """Get type definition by name."""
        return self._types.get(name)

    def list_types(self) -> list[str]:
        """List all registered type names."""
        return list(self._types.keys())

    def list_definitions(self) -> list[AgentTypeDefinition]:
        """List all type definitions."""
        return list(self._types.values())

    def exists(self, name: str) -> bool:
        """Check if type exists."""
        return name in self._types
```

---

## Step 4: Agent Executor (executor.py)

```python
"""
Agent execution engine.

Handles the actual execution of agent tasks using LangChain.
"""

import asyncio
import time
import logging
from typing import Any

from .base import Agent, AgentState, ResourceUsage
from .result import AgentResult


logger = logging.getLogger(__name__)


class AgentExecutionError(Exception):
    """Error during agent execution."""
    pass


class AgentExecutor:
    """Executes agent tasks.

    Manages the LLM interaction loop, tool execution,
    and resource tracking for agents.
    """

    def __init__(
        self,
        llm: Any,  # OpenRouterLLM
        tool_registry: Any,  # ToolRegistry
    ):
        """Initialize executor.

        Args:
            llm: LLM client for API calls
            tool_registry: Registry of available tools
        """
        self.llm = llm
        self.tool_registry = tool_registry

    async def execute(self, agent: Agent) -> AgentResult:
        """Execute an agent task.

        Args:
            agent: Agent to execute

        Returns:
            AgentResult with execution outcome
        """
        agent._start_execution()
        start_time = time.time()

        try:
            # Build agent prompt and tools
            system_prompt = self._build_prompt(agent)
            tools = self._filter_tools(agent)

            # Initialize messages
            messages = self._init_messages(agent, system_prompt)

            # Execute agent loop
            result = await self._run_agent_loop(
                agent=agent,
                messages=messages,
                tools=tools,
                start_time=start_time,
            )

            # Update usage and complete
            agent._usage.time_seconds = time.time() - start_time
            agent._complete_execution(result, success=result.success)

            return result

        except asyncio.CancelledError:
            agent._usage.time_seconds = time.time() - start_time
            result = AgentResult.cancelled()
            agent._complete_execution(result, success=False)
            return result

        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            agent._usage.time_seconds = time.time() - start_time
            result = AgentResult.fail(str(e))
            agent._complete_execution(result, success=False)
            return result

    async def _run_agent_loop(
        self,
        agent: Agent,
        messages: list[dict],
        tools: list,
        start_time: float,
    ) -> AgentResult:
        """Run the agent execution loop.

        Args:
            agent: Agent being executed
            messages: Message history
            tools: Available tools
            start_time: Execution start time

        Returns:
            AgentResult from execution
        """
        limits = agent.config.limits
        final_response = ""

        while not agent.is_cancelled:
            # Check resource limits
            agent._usage.time_seconds = time.time() - start_time
            exceeded = agent._usage.exceeds(limits)
            if exceeded:
                return AgentResult.fail(
                    f"Resource limit exceeded: {exceeded}",
                    output=final_response,
                    tokens_used=agent._usage.tokens_used,
                    time_seconds=agent._usage.time_seconds,
                    tool_calls=agent._usage.tool_calls,
                )

            # Increment iteration count
            agent._usage.iterations += 1

            # Call LLM
            response = await self._call_llm(
                messages=messages,
                tools=tools,
                agent=agent,
            )

            # Process response
            if response.get("tool_calls"):
                # Handle tool calls
                tool_results = await self._execute_tools(
                    response["tool_calls"],
                    agent,
                )
                messages.extend(tool_results)
                agent._report_progress(
                    f"Executed {len(response['tool_calls'])} tool(s)"
                )

            elif response.get("content"):
                # Final response
                final_response = response["content"]
                break

            else:
                # No content or tools - shouldn't happen
                break

        # Build successful result
        return AgentResult.ok(
            output=final_response,
            tokens_used=agent._usage.tokens_used,
            time_seconds=agent._usage.time_seconds,
            tool_calls=agent._usage.tool_calls,
        )

    async def _call_llm(
        self,
        messages: list[dict],
        tools: list,
        agent: Agent,
    ) -> dict:
        """Make LLM API call.

        Args:
            messages: Message history
            tools: Available tools
            agent: Agent for tracking

        Returns:
            LLM response dict
        """
        model = agent.config.model or self.llm.default_model

        response = await self.llm.agenerate(
            messages=messages,
            tools=tools if tools else None,
            model=model,
        )

        # Track token usage
        if hasattr(response, "usage"):
            agent._usage.tokens_used += response.usage.total_tokens

        return response

    async def _execute_tools(
        self,
        tool_calls: list[dict],
        agent: Agent,
    ) -> list[dict]:
        """Execute tool calls.

        Args:
            tool_calls: Tool calls from LLM
            agent: Agent for tracking

        Returns:
            Tool result messages
        """
        results = []

        for call in tool_calls:
            agent._usage.tool_calls += 1

            tool_name = call["name"]
            tool_args = call.get("arguments", {})

            try:
                tool = self.tool_registry.get(tool_name)
                if tool is None:
                    result = f"Tool not found: {tool_name}"
                else:
                    result = await tool.execute(**tool_args)
            except Exception as e:
                result = f"Tool error: {e}"

            results.append({
                "role": "tool",
                "tool_call_id": call.get("id"),
                "content": str(result),
            })

        return results

    def _build_prompt(self, agent: Agent) -> str:
        """Build system prompt for agent.

        Args:
            agent: Agent to build prompt for

        Returns:
            Complete system prompt
        """
        parts = [
            f"You are a {agent.config.agent_type} agent.",
            f"Task: {agent.task}",
        ]

        if agent.config.prompt_addition:
            parts.append(agent.config.prompt_addition)

        parts.append(
            "Work autonomously to complete this task. "
            "When finished, provide a clear summary of your findings or actions."
        )

        return "\n\n".join(parts)

    def _filter_tools(self, agent: Agent) -> list:
        """Get tools available to agent.

        Args:
            agent: Agent to filter tools for

        Returns:
            List of tool definitions
        """
        all_tools = self.tool_registry.list_tools()

        if agent.config.tools is None:
            # All tools allowed
            return all_tools

        # Filter to allowed tools
        allowed = set(agent.config.tools)
        return [t for t in all_tools if t.name in allowed]

    def _init_messages(
        self,
        agent: Agent,
        system_prompt: str,
    ) -> list[dict]:
        """Initialize message history.

        Args:
            agent: Agent to init for
            system_prompt: System prompt to use

        Returns:
            Initial message list
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Include parent context if configured
        if agent.config.inherit_context and agent.context.parent_messages:
            # Add summary of parent context
            summary = self._summarize_context(agent.context.parent_messages)
            messages.append({
                "role": "system",
                "content": f"Parent context summary:\n{summary}",
            })

        # Add the task as user message
        messages.append({
            "role": "user",
            "content": agent.task,
        })

        return messages

    def _summarize_context(self, messages: list[dict]) -> str:
        """Summarize parent context messages.

        Args:
            messages: Parent messages

        Returns:
            Summary text
        """
        # Simple summary - just last few messages
        recent = messages[-5:] if len(messages) > 5 else messages
        parts = []

        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if len(content) > 200:
                content = content[:200] + "..."
            parts.append(f"[{role}]: {content}")

        return "\n".join(parts)
```

---

## Step 5: Agent Manager (manager.py)

```python
"""
Agent lifecycle manager.

Handles spawning, tracking, and coordinating agents.
"""

import asyncio
import logging
from typing import Any, Callable, Awaitable
from uuid import UUID

from .base import Agent, AgentState, AgentConfig, AgentContext
from .executor import AgentExecutor
from .result import AgentResult, AggregatedResult
from .types import AgentTypeRegistry


logger = logging.getLogger(__name__)


class AgentManager:
    """Manages agent lifecycle.

    Singleton that handles spawning, tracking, and
    coordinating agents.
    """

    _instance: "AgentManager | None" = None

    def __init__(
        self,
        executor: AgentExecutor | None = None,
        max_concurrent: int = 5,
    ):
        """Initialize manager.

        Args:
            executor: Agent executor (created lazily if None)
            max_concurrent: Maximum concurrent agents
        """
        self._executor = executor
        self._max_concurrent = max_concurrent
        self._agents: dict[UUID, Agent] = {}
        self._tasks: dict[UUID, asyncio.Task] = {}
        # Note: Semaphore is created lazily to avoid issues when
        # __init__ is called outside of an async context
        self._semaphore: asyncio.Semaphore | None = None
        self._on_complete: list[Callable[[Agent], None]] = []
        self._type_registry = AgentTypeRegistry.get_instance()

    def _get_semaphore(self) -> asyncio.Semaphore:
        """Get or create the concurrency semaphore.

        Creates the semaphore lazily to avoid issues when the manager
        is instantiated outside of an async context.
        """
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_concurrent)
        return self._semaphore

    @classmethod
    def get_instance(cls, **kwargs) -> "AgentManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls(**kwargs)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        if cls._instance:
            cls._instance.cancel_all()
        cls._instance = None

    def set_executor(self, executor: AgentExecutor) -> None:
        """Set the agent executor."""
        self._executor = executor

    async def spawn(
        self,
        agent_type: str,
        task: str,
        config: AgentConfig | None = None,
        context: AgentContext | None = None,
        wait: bool = False,
    ) -> Agent:
        """Spawn a new agent.

        Args:
            agent_type: Type of agent to spawn
            task: Task description
            config: Optional config override
            context: Optional execution context
            wait: If True, wait for completion

        Returns:
            The spawned agent
        """
        # Build config from type if not provided
        if config is None:
            config = AgentConfig.for_type(agent_type)

        # Create agent instance
        agent = self._create_agent(agent_type, task, config, context)
        self._agents[agent.id] = agent

        # Start execution
        task_coro = self._run_agent(agent)
        self._tasks[agent.id] = asyncio.create_task(task_coro)

        logger.info(f"Spawned agent {agent.id} ({agent_type})")

        if wait:
            await self.wait(agent.id)

        return agent

    async def spawn_parallel(
        self,
        tasks: list[tuple[str, str]],
    ) -> list[Agent]:
        """Spawn multiple agents in parallel.

        Args:
            tasks: List of (agent_type, task) tuples

        Returns:
            List of spawned agents
        """
        agents = []
        for agent_type, task in tasks:
            agent = await self.spawn(agent_type, task, wait=False)
            agents.append(agent)
        return agents

    def _create_agent(
        self,
        agent_type: str,
        task: str,
        config: AgentConfig,
        context: AgentContext | None,
    ) -> Agent:
        """Create an agent instance.

        Args:
            agent_type: Type identifier
            task: Task description
            config: Agent config
            context: Execution context

        Returns:
            Agent instance
        """
        from .builtin import create_agent

        return create_agent(
            agent_type=agent_type,
            task=task,
            config=config,
            context=context,
        )

    async def _run_agent(self, agent: Agent) -> None:
        """Run an agent with semaphore control.

        Args:
            agent: Agent to run
        """
        async with self._get_semaphore():
            if agent.is_cancelled:
                return

            try:
                if self._executor is None:
                    raise RuntimeError("No executor configured")

                result = await self._executor.execute(agent)

                # Notify completion callbacks
                for callback in self._on_complete:
                    try:
                        callback(agent)
                    except Exception as e:
                        logger.error(f"Completion callback error: {e}")

            except Exception as e:
                logger.error(f"Agent {agent.id} failed: {e}")

    def get_agent(self, agent_id: UUID) -> Agent | None:
        """Get agent by ID."""
        return self._agents.get(agent_id)

    def list_agents(
        self,
        state: AgentState | None = None,
    ) -> list[Agent]:
        """List agents, optionally filtered by state.

        Args:
            state: Filter by state (None = all)

        Returns:
            List of matching agents
        """
        agents = list(self._agents.values())
        if state is not None:
            agents = [a for a in agents if a.state == state]
        return agents

    async def wait(self, agent_id: UUID) -> AgentResult | None:
        """Wait for specific agent to complete.

        Args:
            agent_id: ID of agent to wait for

        Returns:
            Agent result, or None if not found
        """
        task = self._tasks.get(agent_id)
        if task is None:
            agent = self._agents.get(agent_id)
            return agent.result if agent else None

        await task
        agent = self._agents.get(agent_id)
        return agent.result if agent else None

    async def wait_all(
        self,
        agent_ids: list[UUID] | None = None,
    ) -> AggregatedResult:
        """Wait for all specified agents.

        Args:
            agent_ids: IDs to wait for (None = all)

        Returns:
            Aggregated results
        """
        if agent_ids is None:
            tasks = list(self._tasks.values())
        else:
            tasks = [
                self._tasks[aid]
                for aid in agent_ids
                if aid in self._tasks
            ]

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Collect results
        results = []
        for aid, agent in self._agents.items():
            if agent_ids is None or aid in agent_ids:
                if agent.result:
                    results.append(agent.result)

        return AggregatedResult(results=results)

    def cancel(self, agent_id: UUID) -> bool:
        """Cancel a running agent.

        Args:
            agent_id: ID of agent to cancel

        Returns:
            True if cancelled, False if not found
        """
        agent = self._agents.get(agent_id)
        if agent is None:
            return False

        agent.cancel()

        task = self._tasks.get(agent_id)
        if task and not task.done():
            task.cancel()

        logger.info(f"Cancelled agent {agent_id}")
        return True

    def cancel_all(self) -> int:
        """Cancel all running agents.

        Returns:
            Number of agents cancelled
        """
        count = 0
        for agent_id in list(self._agents.keys()):
            if self.cancel(agent_id):
                count += 1
        return count

    def on_complete(self, callback: Callable[[Agent], None]) -> None:
        """Register completion callback.

        Args:
            callback: Function called when any agent completes
        """
        self._on_complete.append(callback)

    def get_stats(self) -> dict:
        """Get agent statistics.

        Returns:
            Statistics dictionary
        """
        agents = list(self._agents.values())
        by_state = {}
        for state in AgentState:
            by_state[state.value] = len([
                a for a in agents if a.state == state
            ])

        total_tokens = sum(a.usage.tokens_used for a in agents)
        total_time = sum(a.usage.time_seconds for a in agents)
        total_tool_calls = sum(a.usage.tool_calls for a in agents)

        return {
            "total_agents": len(agents),
            "by_state": by_state,
            "total_tokens": total_tokens,
            "total_time_seconds": total_time,
            "total_tool_calls": total_tool_calls,
            "max_concurrent": self._max_concurrent,
        }

    def cleanup_completed(self) -> int:
        """Remove completed agents from tracking.

        Returns:
            Number of agents cleaned up
        """
        to_remove = [
            aid for aid, agent in self._agents.items()
            if agent.is_complete
        ]

        for aid in to_remove:
            del self._agents[aid]
            self._tasks.pop(aid, None)

        return len(to_remove)
```

---

## Step 6: Built-in Agents (builtin/)

### builtin/__init__.py

```python
"""
Built-in agent implementations.
"""

from typing import Any

from ..base import Agent, AgentConfig, AgentContext
from .explore import ExploreAgent
from .plan import PlanAgent
from .review import CodeReviewAgent
from .general import GeneralAgent


# Agent class registry
AGENT_CLASSES: dict[str, type[Agent]] = {
    "explore": ExploreAgent,
    "plan": PlanAgent,
    "code-review": CodeReviewAgent,
    "general": GeneralAgent,
}


def create_agent(
    agent_type: str,
    task: str,
    config: AgentConfig,
    context: AgentContext | None = None,
) -> Agent:
    """Create an agent of the specified type.

    Args:
        agent_type: Type identifier
        task: Task description
        config: Agent configuration
        context: Execution context

    Returns:
        Agent instance

    Raises:
        ValueError: If unknown agent type
    """
    agent_class = AGENT_CLASSES.get(agent_type)

    if agent_class is None:
        # Fall back to general agent for unknown types
        agent_class = GeneralAgent

    return agent_class(task=task, config=config, context=context)


def register_agent_class(name: str, agent_class: type[Agent]) -> None:
    """Register a custom agent class.

    Args:
        name: Type identifier
        agent_class: Agent class to register
    """
    AGENT_CLASSES[name] = agent_class


__all__ = [
    "ExploreAgent",
    "PlanAgent",
    "CodeReviewAgent",
    "GeneralAgent",
    "create_agent",
    "register_agent_class",
]
```

### builtin/explore.py

```python
"""
Explore agent for codebase exploration.
"""

from ..base import Agent, AgentConfig, AgentContext
from ..result import AgentResult


class ExploreAgent(Agent):
    """Agent specialized for codebase exploration.

    Searches files, reads code, and identifies patterns
    to answer questions about the codebase.
    """

    @property
    def agent_type(self) -> str:
        return "explore"

    async def execute(self) -> AgentResult:
        """Execute exploration task.

        This method is called by the executor with proper
        LLM and tool integration.
        """
        # Actual execution is handled by AgentExecutor
        # This is called as a fallback or for testing
        return AgentResult.fail(
            "ExploreAgent must be executed via AgentExecutor"
        )
```

### builtin/plan.py

```python
"""
Plan agent for creating implementation plans.
"""

from ..base import Agent, AgentConfig, AgentContext
from ..result import AgentResult


class PlanAgent(Agent):
    """Agent specialized for creating implementation plans.

    Analyzes codebase structure and creates detailed plans
    with steps, dependencies, and complexity estimates.
    """

    @property
    def agent_type(self) -> str:
        return "plan"

    async def execute(self) -> AgentResult:
        """Execute planning task."""
        return AgentResult.fail(
            "PlanAgent must be executed via AgentExecutor"
        )
```

### builtin/review.py

```python
"""
Code review agent for analyzing code changes.
"""

from ..base import Agent, AgentConfig, AgentContext
from ..result import AgentResult


class CodeReviewAgent(Agent):
    """Agent specialized for code review.

    Analyzes code for bugs, security issues, and
    best practices violations.
    """

    @property
    def agent_type(self) -> str:
        return "code-review"

    async def execute(self) -> AgentResult:
        """Execute code review task."""
        return AgentResult.fail(
            "CodeReviewAgent must be executed via AgentExecutor"
        )
```

### builtin/general.py

```python
"""
General purpose agent for any task.
"""

from ..base import Agent, AgentConfig, AgentContext
from ..result import AgentResult


class GeneralAgent(Agent):
    """General purpose agent with full tool access.

    Handles any task using all available tools.
    """

    @property
    def agent_type(self) -> str:
        return "general"

    async def execute(self) -> AgentResult:
        """Execute general task."""
        return AgentResult.fail(
            "GeneralAgent must be executed via AgentExecutor"
        )
```

---

## Step 7: Package Exports (__init__.py)

```python
"""
Subagents system package.

Provides autonomous agents for complex, multi-step tasks.
"""

from .base import (
    Agent,
    AgentConfig,
    AgentContext,
    AgentState,
    ResourceLimits,
    ResourceUsage,
)
from .result import (
    AgentResult,
    AggregatedResult,
)
from .types import (
    AgentTypeDefinition,
    AgentTypeRegistry,
    EXPLORE_AGENT,
    PLAN_AGENT,
    CODE_REVIEW_AGENT,
    GENERAL_AGENT,
)
from .executor import (
    AgentExecutor,
    AgentExecutionError,
)
from .manager import (
    AgentManager,
)
from .builtin import (
    ExploreAgent,
    PlanAgent,
    CodeReviewAgent,
    GeneralAgent,
    create_agent,
    register_agent_class,
)


__all__ = [
    # Base
    "Agent",
    "AgentConfig",
    "AgentContext",
    "AgentState",
    "ResourceLimits",
    "ResourceUsage",
    # Results
    "AgentResult",
    "AggregatedResult",
    # Types
    "AgentTypeDefinition",
    "AgentTypeRegistry",
    "EXPLORE_AGENT",
    "PLAN_AGENT",
    "CODE_REVIEW_AGENT",
    "GENERAL_AGENT",
    # Executor
    "AgentExecutor",
    "AgentExecutionError",
    # Manager
    "AgentManager",
    # Built-in agents
    "ExploreAgent",
    "PlanAgent",
    "CodeReviewAgent",
    "GeneralAgent",
    "create_agent",
    "register_agent_class",
]
```

---

## Testing Strategy

1. Unit test each base class
2. Unit test AgentTypeRegistry
3. Unit test AgentExecutor with mocks
4. Unit test AgentManager
5. Integration test with real LLM
6. Test parallel execution
7. Test resource limits and cancellation
