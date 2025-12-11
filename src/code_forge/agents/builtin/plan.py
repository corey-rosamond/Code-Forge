"""
Plan agent for creating implementation plans.
"""

from __future__ import annotations

from ..base import Agent, AgentConfig, AgentContext
from ..result import AgentResult


class PlanAgent(Agent):
    """Agent specialized for creating implementation plans.

    Analyzes codebase structure and creates detailed plans
    with steps, dependencies, and complexity estimates.
    """

    def __init__(
        self,
        task: str,
        config: AgentConfig,
        context: AgentContext | None = None,
    ) -> None:
        """Initialize plan agent.

        Args:
            task: The planning task.
            config: Agent configuration.
            context: Execution context.
        """
        super().__init__(task, config, context)

    @property
    def agent_type(self) -> str:
        """Return agent type identifier."""
        return "plan"

    async def execute(self) -> AgentResult:
        """Execute planning task.

        Returns:
            AgentResult indicating must use AgentExecutor.
        """
        return AgentResult.fail(
            "PlanAgent must be executed via AgentExecutor"
        )
