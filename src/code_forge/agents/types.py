"""
Agent type definitions and registry.

Provides built-in agent types and a registry for custom types.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any


@dataclass
class AgentTypeDefinition:
    """Definition of an agent type.

    Attributes:
        name: Type identifier.
        description: Human-readable description.
        prompt_template: Additional system prompt.
        default_tools: Tools available (None = all).
        default_max_tokens: Default token limit.
        default_max_time: Default time limit (seconds).
        default_model: Preferred model (None = session default).
    """

    name: str
    description: str
    prompt_template: str
    default_tools: list[str] | None = None
    default_max_tokens: int = 50000
    default_max_time: int = 300
    default_model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "name": self.name,
            "description": self.description,
            "prompt_template": self.prompt_template,
            "default_tools": self.default_tools,
            "default_max_tokens": self.default_max_tokens,
            "default_max_time": self.default_max_time,
            "default_model": self.default_model,
        }


# Built-in agent type definitions
EXPLORE_AGENT = AgentTypeDefinition(
    name="explore",
    description="Explores codebase to answer questions",
    prompt_template="""You are an exploration agent specialized in navigating codebases.

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
- Summary of findings""",
    default_tools=["glob", "grep", "read"],
    default_max_tokens=30000,
    default_max_time=180,
)


PLAN_AGENT = AgentTypeDefinition(
    name="plan",
    description="Creates implementation plans",
    prompt_template="""You are a planning agent specialized in software architecture.

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
- Success criteria""",
    default_tools=["glob", "grep", "read"],
    default_max_tokens=40000,
    default_max_time=240,
)


CODE_REVIEW_AGENT = AgentTypeDefinition(
    name="code-review",
    description="Reviews code changes for issues",
    prompt_template="""You are a code review agent specialized in finding issues.

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
- Overall assessment""",
    default_tools=["glob", "grep", "read", "bash"],
    default_max_tokens=40000,
    default_max_time=300,
)


GENERAL_AGENT = AgentTypeDefinition(
    name="general",
    description="General purpose agent for any task",
    prompt_template="""You are a general purpose coding agent.

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
- Verification performed""",
    default_tools=None,  # All tools
    default_max_tokens=50000,
    default_max_time=300,
)


class AgentTypeRegistry:
    """Registry of available agent types.

    Singleton that maintains the catalog of agent types
    available for spawning.

    Thread-safe implementation using locks.
    """

    _instance: AgentTypeRegistry | None = None
    _instance_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize with built-in types."""
        self._types: dict[str, AgentTypeDefinition] = {}
        self._lock = threading.RLock()
        self._register_builtins()

    @classmethod
    def get_instance(cls) -> AgentTypeRegistry:
        """Get singleton instance.

        Returns:
            The singleton AgentTypeRegistry instance.
        """
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton (for testing)."""
        with cls._instance_lock:
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
            type_def: Type definition to register.

        Raises:
            ValueError: If type name already registered.
        """
        with self._lock:
            if type_def.name in self._types:
                raise ValueError(f"Agent type already registered: {type_def.name}")
            self._types[type_def.name] = type_def

    def unregister(self, name: str) -> bool:
        """Unregister an agent type.

        Args:
            name: Type name to remove.

        Returns:
            True if removed, False if not found.
        """
        with self._lock:
            if name in self._types:
                del self._types[name]
                return True
            return False

    def get(self, name: str) -> AgentTypeDefinition | None:
        """Get type definition by name.

        Args:
            name: Type name to look up.

        Returns:
            AgentTypeDefinition if found, None otherwise.
        """
        with self._lock:
            return self._types.get(name)

    def list_types(self) -> list[str]:
        """List all registered type names.

        Returns:
            List of type names.
        """
        with self._lock:
            return list(self._types.keys())

    def list_definitions(self) -> list[AgentTypeDefinition]:
        """List all type definitions.

        Returns:
            List of AgentTypeDefinitions.
        """
        with self._lock:
            return list(self._types.values())

    def exists(self, name: str) -> bool:
        """Check if type exists.

        Args:
            name: Type name to check.

        Returns:
            True if type is registered.
        """
        with self._lock:
            return name in self._types
