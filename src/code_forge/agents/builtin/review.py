"""
Code review agent for analyzing code changes.
"""

from __future__ import annotations

from ..base import Agent, AgentConfig, AgentContext
from ..result import AgentResult


class CodeReviewAgent(Agent):
    """Agent specialized for code review.

    Analyzes code for bugs, security issues, and
    best practices violations.
    """

    def __init__(
        self,
        task: str,
        config: AgentConfig,
        context: AgentContext | None = None,
    ) -> None:
        """Initialize code review agent.

        Args:
            task: The review task.
            config: Agent configuration.
            context: Execution context.
        """
        super().__init__(task, config, context)

    @property
    def agent_type(self) -> str:
        """Return agent type identifier."""
        return "code-review"

    async def execute(self) -> AgentResult:
        """Execute code review task.

        Returns:
            AgentResult indicating must use AgentExecutor.
        """
        return AgentResult.fail(
            "CodeReviewAgent must be executed via AgentExecutor"
        )
