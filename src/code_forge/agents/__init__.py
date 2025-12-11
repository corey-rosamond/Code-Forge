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
from .builtin import (
    AGENT_CLASSES,
    CodeReviewAgent,
    ExploreAgent,
    GeneralAgent,
    PlanAgent,
    create_agent,
    list_agent_classes,
    register_agent_class,
    unregister_agent_class,
)
from .executor import (
    AgentExecutionError,
    AgentExecutor,
)
from .manager import (
    AgentManager,
)
from .result import (
    AgentResult,
    AggregatedResult,
)
from .types import (
    CODE_REVIEW_AGENT,
    EXPLORE_AGENT,
    GENERAL_AGENT,
    PLAN_AGENT,
    AgentTypeDefinition,
    AgentTypeRegistry,
)

__all__ = [
    "AGENT_CLASSES",
    "CODE_REVIEW_AGENT",
    "EXPLORE_AGENT",
    "GENERAL_AGENT",
    "PLAN_AGENT",
    # Base
    "Agent",
    "AgentConfig",
    "AgentContext",
    "AgentExecutionError",
    # Executor
    "AgentExecutor",
    # Manager
    "AgentManager",
    # Results
    "AgentResult",
    "AgentState",
    # Types
    "AgentTypeDefinition",
    "AgentTypeRegistry",
    "AggregatedResult",
    "CodeReviewAgent",
    # Built-in agents
    "ExploreAgent",
    "GeneralAgent",
    "PlanAgent",
    "ResourceLimits",
    "ResourceUsage",
    "create_agent",
    "list_agent_classes",
    "register_agent_class",
    "unregister_agent_class",
]
