"""
General purpose agent for any task.
"""

from __future__ import annotations

from ..base import Agent, AgentConfig, AgentContext
from ..result import AgentResult


class GeneralAgent(Agent):
    """General purpose agent with full tool access.

    Handles any task using all available tools.
    """

    def __init__(
        self,
        task: str,
        config: AgentConfig,
        context: AgentContext | None = None,
    ) -> None:
        """Initialize general agent.

        Args:
            task: The task to complete.
            config: Agent configuration.
            context: Execution context.
        """
        super().__init__(task, config, context)

    @property
    def agent_type(self) -> str:
        """Return agent type identifier."""
        return "general"

    async def execute(self) -> AgentResult:
        """Execute general task.

        Returns:
            AgentResult indicating must use AgentExecutor.
        """
        return AgentResult.fail(
            "GeneralAgent must be executed via AgentExecutor"
        )
