"""Tests for built-in agent implementations."""

import pytest

from opencode.agents.base import AgentConfig, AgentContext, AgentState
from opencode.agents.builtin import (
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
from opencode.agents.result import AgentResult


class TestExploreAgent:
    """Tests for ExploreAgent."""

    def test_creation(self) -> None:
        """Test agent creation."""
        config = AgentConfig(agent_type="explore")
        agent = ExploreAgent(task="Find files", config=config)

        assert agent.agent_type == "explore"
        assert agent.task == "Find files"
        assert agent.state == AgentState.PENDING

    def test_creation_with_context(self) -> None:
        """Test agent creation with context."""
        config = AgentConfig(agent_type="explore")
        context = AgentContext(working_directory="/project")
        agent = ExploreAgent(task="Test", config=config, context=context)

        assert agent.context.working_directory == "/project"

    @pytest.mark.asyncio
    async def test_execute_returns_error(self) -> None:
        """Test direct execute returns error (must use executor)."""
        config = AgentConfig(agent_type="explore")
        agent = ExploreAgent(task="Test", config=config)

        result = await agent.execute()

        assert result.success is False
        assert "AgentExecutor" in result.error


class TestPlanAgent:
    """Tests for PlanAgent."""

    def test_creation(self) -> None:
        """Test agent creation."""
        config = AgentConfig(agent_type="plan")
        agent = PlanAgent(task="Create plan", config=config)

        assert agent.agent_type == "plan"
        assert agent.task == "Create plan"
        assert agent.state == AgentState.PENDING

    def test_creation_with_context(self) -> None:
        """Test agent creation with context."""
        config = AgentConfig(agent_type="plan")
        context = AgentContext(metadata={"key": "value"})
        agent = PlanAgent(task="Test", config=config, context=context)

        assert agent.context.metadata["key"] == "value"

    @pytest.mark.asyncio
    async def test_execute_returns_error(self) -> None:
        """Test direct execute returns error."""
        config = AgentConfig(agent_type="plan")
        agent = PlanAgent(task="Test", config=config)

        result = await agent.execute()

        assert result.success is False
        assert "AgentExecutor" in result.error


class TestCodeReviewAgent:
    """Tests for CodeReviewAgent."""

    def test_creation(self) -> None:
        """Test agent creation."""
        config = AgentConfig(agent_type="code-review")
        agent = CodeReviewAgent(task="Review PR #123", config=config)

        assert agent.agent_type == "code-review"
        assert agent.task == "Review PR #123"
        assert agent.state == AgentState.PENDING

    def test_creation_with_context(self) -> None:
        """Test agent creation with context."""
        config = AgentConfig(agent_type="code-review")
        context = AgentContext(environment={"GIT_BRANCH": "main"})
        agent = CodeReviewAgent(task="Test", config=config, context=context)

        assert agent.context.environment["GIT_BRANCH"] == "main"

    @pytest.mark.asyncio
    async def test_execute_returns_error(self) -> None:
        """Test direct execute returns error."""
        config = AgentConfig(agent_type="code-review")
        agent = CodeReviewAgent(task="Test", config=config)

        result = await agent.execute()

        assert result.success is False
        assert "AgentExecutor" in result.error


class TestGeneralAgent:
    """Tests for GeneralAgent."""

    def test_creation(self) -> None:
        """Test agent creation."""
        config = AgentConfig(agent_type="general")
        agent = GeneralAgent(task="Do something", config=config)

        assert agent.agent_type == "general"
        assert agent.task == "Do something"
        assert agent.state == AgentState.PENDING

    def test_creation_with_context(self) -> None:
        """Test agent creation with context."""
        config = AgentConfig(agent_type="general")
        from uuid import uuid4
        parent_id = uuid4()
        context = AgentContext(parent_id=parent_id)
        agent = GeneralAgent(task="Test", config=config, context=context)

        assert agent.context.parent_id == parent_id

    @pytest.mark.asyncio
    async def test_execute_returns_error(self) -> None:
        """Test direct execute returns error."""
        config = AgentConfig(agent_type="general")
        agent = GeneralAgent(task="Test", config=config)

        result = await agent.execute()

        assert result.success is False
        assert "AgentExecutor" in result.error


class TestCreateAgent:
    """Tests for create_agent factory function."""

    def test_create_explore(self) -> None:
        """Test creating explore agent."""
        config = AgentConfig(agent_type="explore")
        agent = create_agent("explore", "Task", config)

        assert isinstance(agent, ExploreAgent)
        assert agent.agent_type == "explore"

    def test_create_plan(self) -> None:
        """Test creating plan agent."""
        config = AgentConfig(agent_type="plan")
        agent = create_agent("plan", "Task", config)

        assert isinstance(agent, PlanAgent)
        assert agent.agent_type == "plan"

    def test_create_code_review(self) -> None:
        """Test creating code review agent."""
        config = AgentConfig(agent_type="code-review")
        agent = create_agent("code-review", "Task", config)

        assert isinstance(agent, CodeReviewAgent)
        assert agent.agent_type == "code-review"

    def test_create_general(self) -> None:
        """Test creating general agent."""
        config = AgentConfig(agent_type="general")
        agent = create_agent("general", "Task", config)

        assert isinstance(agent, GeneralAgent)
        assert agent.agent_type == "general"

    def test_create_unknown_falls_back(self) -> None:
        """Test unknown type falls back to general."""
        config = AgentConfig(agent_type="unknown")
        agent = create_agent("unknown", "Task", config)

        assert isinstance(agent, GeneralAgent)

    def test_create_with_context(self) -> None:
        """Test creating agent with context."""
        config = AgentConfig(agent_type="explore")
        context = AgentContext(working_directory="/test")

        agent = create_agent("explore", "Task", config, context)

        assert agent.context.working_directory == "/test"


class TestAgentClassRegistry:
    """Tests for agent class registration."""

    def test_agent_classes_dict(self) -> None:
        """Test AGENT_CLASSES contains built-in types."""
        assert "explore" in AGENT_CLASSES
        assert "plan" in AGENT_CLASSES
        assert "code-review" in AGENT_CLASSES
        assert "general" in AGENT_CLASSES

    def test_list_agent_classes(self) -> None:
        """Test listing registered agent classes."""
        classes = list_agent_classes()

        assert "explore" in classes
        assert "plan" in classes
        assert "code-review" in classes
        assert "general" in classes

    def test_register_custom_class(self) -> None:
        """Test registering custom agent class."""
        from opencode.agents.base import Agent

        class CustomAgent(Agent):
            @property
            def agent_type(self) -> str:
                return "custom"

            async def execute(self) -> AgentResult:
                return AgentResult.ok("Custom done")

        register_agent_class("custom", CustomAgent)

        assert "custom" in AGENT_CLASSES
        assert AGENT_CLASSES["custom"] == CustomAgent

        # Clean up
        unregister_agent_class("custom")

    def test_unregister_class(self) -> None:
        """Test unregistering agent class."""
        from opencode.agents.base import Agent

        class TempAgent(Agent):
            @property
            def agent_type(self) -> str:
                return "temp"

            async def execute(self) -> AgentResult:
                return AgentResult.ok("Temp")

        register_agent_class("temp", TempAgent)
        assert "temp" in AGENT_CLASSES

        result = unregister_agent_class("temp")
        assert result is True
        assert "temp" not in AGENT_CLASSES

    def test_unregister_nonexistent(self) -> None:
        """Test unregistering nonexistent class."""
        result = unregister_agent_class("nonexistent")
        assert result is False

    def test_create_agent_uses_custom_class(self) -> None:
        """Test create_agent uses custom registered class."""
        from opencode.agents.base import Agent

        class SpecialAgent(Agent):
            @property
            def agent_type(self) -> str:
                return "special"

            async def execute(self) -> AgentResult:
                return AgentResult.ok("Special")

        register_agent_class("special", SpecialAgent)

        config = AgentConfig(agent_type="special")
        agent = create_agent("special", "Task", config)

        assert isinstance(agent, SpecialAgent)

        # Clean up
        unregister_agent_class("special")
