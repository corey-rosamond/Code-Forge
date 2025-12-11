"""
Explore agent for codebase exploration.
"""

from __future__ import annotations

from ..base import Agent, AgentConfig, AgentContext
from ..result import AgentResult


class ExploreAgent(Agent):
    """Agent specialized for codebase exploration.

    Searches files, reads code, and identifies patterns
    to answer questions about the codebase.
    """

    def __init__(
        self,
        task: str,
        config: AgentConfig,
        context: AgentContext | None = None,
    ) -> None:
        """Initialize explore agent.

        Args:
            task: The exploration task.
            config: Agent configuration.
            context: Execution context.
        """
        super().__init__(task, config, context)

    @property
    def agent_type(self) -> str:
        """Return agent type identifier."""
        return "explore"

    async def execute(self) -> AgentResult:
        """Execute exploration task.

        This method is called by the executor with proper
        LLM and tool integration.

        Returns:
            AgentResult indicating must use AgentExecutor.
        """
        # Actual execution is handled by AgentExecutor
        # This is called as a fallback or for testing
        return AgentResult.fail(
            "ExploreAgent must be executed via AgentExecutor"
        )
