"""Tests for agent executor."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from code_forge.agents.base import Agent, AgentConfig, AgentContext, AgentState
from code_forge.agents.executor import AgentExecutionError, AgentExecutor
from code_forge.agents.result import AgentResult


# Concrete implementation for testing
class ConcreteAgentForTesting(Agent):
    """Concrete Agent implementation for testing."""

    @property
    def agent_type(self) -> str:
        return "testable"

    async def execute(self) -> AgentResult:
        return AgentResult.ok("Test completed")


class TestAgentExecutionError:
    """Tests for AgentExecutionError exception."""

    def test_exception_creation(self) -> None:
        """Test exception can be created."""
        error = AgentExecutionError("Test error")
        assert str(error) == "Test error"

    def test_exception_inheritance(self) -> None:
        """Test exception inherits from Exception."""
        error = AgentExecutionError("Test")
        assert isinstance(error, Exception)


class TestAgentExecutor:
    """Tests for AgentExecutor class."""

    def create_mock_llm(self) -> MagicMock:
        """Create a mock LLM."""
        llm = MagicMock()
        llm.bind_tools = MagicMock(return_value=llm)

        # Create mock response
        response = MagicMock()
        response.content = "Task completed successfully"
        response.tool_calls = []
        response.usage_metadata = {"total_tokens": 100}

        llm.ainvoke = AsyncMock(return_value=response)
        return llm

    def create_mock_registry(self) -> MagicMock:
        """Create a mock tool registry."""
        registry = MagicMock()
        registry.list_tools.return_value = []
        return registry

    def test_init(self) -> None:
        """Test executor initialization."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()

        executor = AgentExecutor(llm=llm, tool_registry=registry)

        assert executor.llm == llm
        assert executor.tool_registry == registry

    @pytest.mark.asyncio
    async def test_execute_success(self) -> None:
        """Test successful execution."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Test task", config=config)

        result = await executor.execute(agent)

        assert result.success is True
        assert "completed" in result.output.lower()
        assert agent.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_tracks_time(self) -> None:
        """Test execution tracks time."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Test", config=config)

        await executor.execute(agent)

        assert agent.usage.time_seconds > 0

    @pytest.mark.asyncio
    async def test_execute_tracks_tokens(self) -> None:
        """Test execution tracks token usage."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Test", config=config)

        await executor.execute(agent)

        assert agent.usage.tokens_used == 100

    @pytest.mark.asyncio
    async def test_execute_with_tool_calls(self) -> None:
        """Test execution with tool calls."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()

        # First response has tool call
        first_response = MagicMock()
        first_response.content = ""
        first_response.tool_calls = [{
            "id": "call_1",
            "name": "read",
            "args": {"path": "/test.txt"},
        }]
        first_response.usage_metadata = {"total_tokens": 50}

        # Second response is final
        second_response = MagicMock()
        second_response.content = "Done"
        second_response.tool_calls = []
        second_response.usage_metadata = {"total_tokens": 50}

        llm.ainvoke = AsyncMock(side_effect=[first_response, second_response])

        # Mock tool
        mock_tool = MagicMock()
        mock_tool.name = "read"
        mock_tool.execute = AsyncMock(return_value=MagicMock(output="file content"))
        registry.list_tools.return_value = [mock_tool]
        registry.get.return_value = mock_tool

        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Read file", config=config)

        result = await executor.execute(agent)

        assert result.success is True
        assert agent.usage.tool_calls == 1

    @pytest.mark.asyncio
    async def test_execute_tool_not_found(self) -> None:
        """Test execution handles tool not found."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()

        # Response with tool call for nonexistent tool
        first_response = MagicMock()
        first_response.content = ""
        first_response.tool_calls = [{
            "id": "call_1",
            "name": "nonexistent",
            "args": {},
        }]
        first_response.usage_metadata = {"total_tokens": 50}

        second_response = MagicMock()
        second_response.content = "Done"
        second_response.tool_calls = []
        second_response.usage_metadata = {"total_tokens": 50}

        llm.ainvoke = AsyncMock(side_effect=[first_response, second_response])
        registry.get.return_value = None  # Tool not found

        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Test", config=config)

        result = await executor.execute(agent)

        # Should still complete
        assert agent.state == AgentState.COMPLETED

    @pytest.mark.asyncio
    async def test_execute_exceeds_token_limit(self) -> None:
        """Test execution stops at token limit."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()

        # Response uses many tokens
        response = MagicMock()
        response.content = ""
        response.tool_calls = [{
            "id": "call_1",
            "name": "test",
            "args": {},
        }]
        response.usage_metadata = {"total_tokens": 60000}

        llm.ainvoke = AsyncMock(return_value=response)

        mock_tool = MagicMock()
        mock_tool.name = "test"
        mock_tool.execute = AsyncMock(return_value=MagicMock(output="result"))
        registry.list_tools.return_value = [mock_tool]
        registry.get.return_value = mock_tool

        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Test", config=config)

        result = await executor.execute(agent)

        assert result.success is False
        assert "max_tokens" in result.error

    @pytest.mark.asyncio
    async def test_execute_cancelled(self) -> None:
        """Test execution handles cancellation."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()

        # Long-running response
        async def slow_invoke(*args, **kwargs):
            import asyncio
            await asyncio.sleep(0.1)
            response = MagicMock()
            response.content = "Done"
            response.tool_calls = []
            response.usage_metadata = {"total_tokens": 50}
            return response

        llm.ainvoke = AsyncMock(side_effect=slow_invoke)

        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Test", config=config)

        # Pre-cancel the agent
        agent.cancel()

        result = await executor.execute(agent)

        assert result.success is False
        assert "cancelled" in result.error.lower()

    @pytest.mark.asyncio
    async def test_execute_error_handling(self) -> None:
        """Test execution handles errors gracefully."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()

        llm.ainvoke = AsyncMock(side_effect=RuntimeError("API error"))

        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Test", config=config)

        result = await executor.execute(agent)

        assert result.success is False
        assert agent.state == AgentState.FAILED
        assert "API error" in result.error

    def test_build_prompt(self) -> None:
        """Test prompt building."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(
            agent_type="explore",
            prompt_addition="Additional instructions",
        )
        agent = ConcreteAgentForTesting(task="Find files", config=config)

        prompt = executor._build_prompt(agent)

        assert "explore" in prompt
        assert "Find files" in prompt
        assert "Additional instructions" in prompt

    def test_filter_tools_all_allowed(self) -> None:
        """Test tool filtering with all tools allowed."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()

        mock_tool1 = MagicMock()
        mock_tool1.name = "read"
        mock_tool2 = MagicMock()
        mock_tool2.name = "write"
        registry.list_all.return_value = [mock_tool1, mock_tool2]

        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable", tools=None)
        agent = ConcreteAgentForTesting(task="Test", config=config)

        tools = executor._filter_tools(agent)

        assert len(tools) == 2

    def test_filter_tools_restricted(self) -> None:
        """Test tool filtering with restricted tools."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()

        mock_tool1 = MagicMock()
        mock_tool1.name = "read"
        mock_tool2 = MagicMock()
        mock_tool2.name = "write"
        registry.list_all.return_value = [mock_tool1, mock_tool2]

        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable", tools=["read"])
        agent = ConcreteAgentForTesting(task="Test", config=config)

        tools = executor._filter_tools(agent)

        assert len(tools) == 1
        assert tools[0].name == "read"

    def test_init_messages_basic(self) -> None:
        """Test message initialization."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        config = AgentConfig(agent_type="testable")
        agent = ConcreteAgentForTesting(task="Test task", config=config)

        messages = executor._init_messages(agent, "System prompt")

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Test task"

    def test_init_messages_with_context(self) -> None:
        """Test message initialization with parent context."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        context = AgentContext(
            parent_messages=[{"role": "user", "content": "Previous message"}]
        )
        config = AgentConfig(agent_type="testable", inherit_context=True)
        agent = ConcreteAgentForTesting(task="Test", config=config, context=context)

        messages = executor._init_messages(agent, "System")

        # Should have system, context summary, and user message
        assert len(messages) == 3
        assert "context" in messages[1]["content"].lower()

    def test_summarize_context(self) -> None:
        """Test context summarization."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]

        summary = executor._summarize_context(messages)

        assert "[user]" in summary.lower()
        assert "[assistant]" in summary.lower()
        assert "Hello" in summary
        assert "Hi" in summary

    def test_summarize_context_truncates_long(self) -> None:
        """Test context summarization truncates long messages."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        long_content = "x" * 500
        messages = [{"role": "user", "content": long_content}]

        summary = executor._summarize_context(messages)

        assert len(summary) < len(long_content) + 50
        assert "..." in summary

    def test_get_partial_output(self) -> None:
        """Test extracting partial output."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "First response"},
            {"role": "user", "content": "More"},
            {"role": "assistant", "content": "Final response"},
        ]

        output = executor._get_partial_output(messages)

        assert output == "Final response"

    def test_get_partial_output_empty(self) -> None:
        """Test extracting partial output with no assistant messages."""
        llm = self.create_mock_llm()
        registry = self.create_mock_registry()
        executor = AgentExecutor(llm=llm, tool_registry=registry)

        messages = [{"role": "user", "content": "Hello"}]

        output = executor._get_partial_output(messages)

        assert output == ""
