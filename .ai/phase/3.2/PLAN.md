# Phase 3.2: LangChain Integration - Implementation Plan

**Phase:** 3.2
**Name:** LangChain Integration
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 3.1 (OpenRouter Client)

---

## Implementation Order

1. Message conversion utilities
2. OpenRouterLLM wrapper
3. Tool adapters
4. Conversation memory
5. Callback handlers
6. Agent executor
7. Package exports and tests

---

## Step 1: Message Conversion Utilities

Create `src/forge/langchain/messages.py`:

```python
"""Message conversion between LangChain and Code-Forge formats."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

if TYPE_CHECKING:
    from forge.llm.models import Message, MessageRole, ToolCall


def langchain_to_forge(message: BaseMessage) -> "Message":
    """
    Convert a LangChain message to an Code-Forge message.

    Args:
        message: LangChain message to convert

    Returns:
        Equivalent Code-Forge Message

    Raises:
        ValueError: If message type is not supported
    """
    from forge.llm.models import Message, ToolCall

    if isinstance(message, SystemMessage):
        return Message.system(str(message.content))

    elif isinstance(message, HumanMessage):
        return Message.user(str(message.content))

    elif isinstance(message, AIMessage):
        tool_calls = None
        if message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc["id"],
                    type="function",
                    function={
                        "name": tc["name"],
                        "arguments": json.dumps(tc["args"]) if isinstance(tc["args"], dict) else tc["args"],
                    },
                )
                for tc in message.tool_calls
            ]
        content = str(message.content) if message.content else None
        return Message.assistant(content=content, tool_calls=tool_calls)

    elif isinstance(message, ToolMessage):
        return Message.tool_result(
            tool_call_id=message.tool_call_id,
            content=str(message.content),
        )

    else:
        raise ValueError(f"Unsupported message type: {type(message).__name__}")


def forge_to_langchain(message: "Message") -> BaseMessage:
    """
    Convert an Code-Forge message to a LangChain message.

    Args:
        message: Code-Forge message to convert

    Returns:
        Equivalent LangChain message

    Raises:
        ValueError: If message role is not supported
    """
    from forge.llm.models import MessageRole

    if message.role == MessageRole.SYSTEM:
        return SystemMessage(content=message.content or "")

    elif message.role == MessageRole.USER:
        return HumanMessage(content=message.content or "")

    elif message.role == MessageRole.ASSISTANT:
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                args = tc.function.get("arguments", "{}")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {}
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function["name"],
                    "args": args,
                })
        return AIMessage(
            content=message.content or "",
            tool_calls=tool_calls if tool_calls else [],
        )

    elif message.role == MessageRole.TOOL:
        return ToolMessage(
            content=message.content or "",
            tool_call_id=message.tool_call_id or "",
        )

    else:
        raise ValueError(f"Unsupported message role: {message.role}")


def langchain_messages_to_forge(messages: list[BaseMessage]) -> list["Message"]:
    """Convert a list of LangChain messages to Code-Forge messages."""
    return [langchain_to_forge(m) for m in messages]


def forge_messages_to_langchain(messages: list["Message"]) -> list[BaseMessage]:
    """Convert a list of Code-Forge messages to LangChain messages."""
    return [forge_to_langchain(m) for m in messages]
```

---

## Step 2: OpenRouterLLM Wrapper

Create `src/forge/langchain/llm.py`:

```python
"""LangChain LLM wrapper for OpenRouter client."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any, ClassVar, TYPE_CHECKING

from langchain_core.callbacks import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from pydantic import PrivateAttr
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult

from forge.langchain.messages import (
    langchain_messages_to_forge,
    forge_to_langchain,
)

if TYPE_CHECKING:
    from forge.llm.client import OpenRouterClient
    from forge.llm.models import ToolDefinition


class OpenRouterLLM(BaseChatModel):
    """
    LangChain chat model wrapper for OpenRouter API.

    This class bridges LangChain's BaseChatModel interface with
    Code-Forge's OpenRouterClient, enabling use of OpenRouter's
    400+ models through LangChain's ecosystem.

    Example:
        ```python
        from forge.llm import OpenRouterClient
        from forge.langchain import OpenRouterLLM

        client = OpenRouterClient(api_key="sk-or-xxx")
        llm = OpenRouterLLM(client=client, model="anthropic/claude-3-opus")

        response = llm.invoke([HumanMessage(content="Hello!")])
        ```
    """

    # Pydantic fields
    client: Any  # OpenRouterClient - use Any to avoid Pydantic issues
    model: str
    temperature: float = 1.0
    max_tokens: int | None = None
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop: list[str] | None = None

    # Internal state - use PrivateAttr to avoid mutable default issues
    _bound_tools: list[Any] = PrivateAttr(default_factory=list)

    # Maximum number of tools that can be bound
    MAX_BOUND_TOOLS: ClassVar[int] = 64

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        """Return identifier for this LLM type."""
        return "openrouter"

    @property
    def _identifying_params(self) -> dict[str, Any]:
        """Return parameters that identify this LLM configuration."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
        }

    def _build_request(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> "CompletionRequest":
        """Build a CompletionRequest from LangChain messages."""
        from forge.llm.models import CompletionRequest

        forge_messages = langchain_messages_to_forge(messages)

        # Merge stop sequences
        all_stops = list(self.stop or [])
        if stop:
            all_stops.extend(stop)

        # Build tools list if bound
        tools = None
        if self._bound_tools:
            tools = [
                t.to_dict() if hasattr(t, "to_dict") else t
                for t in self._bound_tools
            ]

        return CompletionRequest(
            model=self.model,
            messages=forge_messages,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.max_tokens),
            top_p=kwargs.get("top_p", self.top_p),
            frequency_penalty=kwargs.get("frequency_penalty", self.frequency_penalty),
            presence_penalty=kwargs.get("presence_penalty", self.presence_penalty),
            stop=all_stops if all_stops else None,
            tools=tools,
            stream=stream,
        )

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate a response synchronously.

        Args:
            messages: List of messages to send
            stop: Optional stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Returns:
            ChatResult with generated response

        Note:
            Uses asyncio.run() for Python 3.10+ compatibility, with fallback
            to get_event_loop() for nested event loop scenarios.
        """
        try:
            # Prefer asyncio.run() - cleaner and handles loop lifecycle
            return asyncio.run(
                self._agenerate(messages, stop, run_manager, **kwargs)
            )
        except RuntimeError:
            # Fallback for nested event loops (e.g., in Jupyter)
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self._agenerate(messages, stop, run_manager, **kwargs)
            )

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        """
        Generate a response asynchronously.

        Args:
            messages: List of messages to send
            stop: Optional stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Returns:
            ChatResult with generated response
        """
        request = self._build_request(messages, stop, stream=False, **kwargs)
        response = await self.client.complete(request)

        # Convert response to LangChain format
        generations = []
        for choice in response.choices:
            lc_message = forge_to_langchain(choice.message)
            generations.append(
                ChatGeneration(
                    message=lc_message,
                    generation_info={
                        "finish_reason": choice.finish_reason,
                    },
                )
            )

        return ChatResult(
            generations=generations,
            llm_output={
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            },
        )

    def _stream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """
        Stream response synchronously.

        Args:
            messages: List of messages to send
            stop: Optional stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Yields:
            ChatGenerationChunk for each streamed piece

        Note:
            Sync streaming from async requires special handling.
            Uses a queue-based approach for proper async-to-sync bridging.
        """
        import queue
        import threading

        result_queue: queue.Queue[ChatGenerationChunk | Exception | None] = queue.Queue()

        async def _producer():
            """Async producer that puts chunks into the queue."""
            try:
                async for chunk in self._astream(messages, stop, run_manager, **kwargs):
                    result_queue.put(chunk)
            except Exception as e:
                result_queue.put(e)
            finally:
                result_queue.put(None)  # Sentinel to signal completion

        def _run_producer():
            """Run the async producer in a new event loop."""
            asyncio.run(_producer())

        # Start producer in background thread
        producer_thread = threading.Thread(target=_run_producer, daemon=True)
        producer_thread.start()

        # Consume from queue
        while True:
            item = result_queue.get()
            if item is None:
                break
            if isinstance(item, Exception):
                raise item
            yield item

        producer_thread.join(timeout=1.0)

    async def _astream(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """
        Stream response asynchronously.

        Args:
            messages: List of messages to send
            stop: Optional stop sequences
            run_manager: Callback manager
            **kwargs: Additional parameters

        Yields:
            ChatGenerationChunk for each streamed piece
        """
        request = self._build_request(messages, stop, stream=True, **kwargs)

        async for chunk in self.client.stream(request):
            # Convert delta to message chunk
            content = chunk.delta.content or ""
            tool_call_chunks = []

            if chunk.delta.tool_calls:
                for tc in chunk.delta.tool_calls:
                    tool_call_chunks.append({
                        "index": tc.get("index", 0),
                        "id": tc.get("id"),
                        "name": tc.get("function", {}).get("name"),
                        "args": tc.get("function", {}).get("arguments", ""),
                    })

            message_chunk = AIMessageChunk(
                content=content,
                tool_call_chunks=tool_call_chunks if tool_call_chunks else [],
            )

            yield ChatGenerationChunk(
                message=message_chunk,
                generation_info={
                    "finish_reason": chunk.finish_reason,
                },
            )

            if run_manager:
                await run_manager.on_llm_new_token(content)

    def bind_tools(
        self,
        tools: Sequence[Any],
        *,
        tool_choice: str | dict | None = None,
        **kwargs: Any,
    ) -> "OpenRouterLLM":
        """
        Bind tools to this LLM instance.

        Args:
            tools: Tools to bind (Code-Forge ToolDefinition or LangChain tools)
            tool_choice: How to choose tools ("auto", "none", or specific)
            **kwargs: Additional parameters

        Returns:
            New OpenRouterLLM instance with tools bound

        Raises:
            ValueError: If too many tools are provided (max: MAX_BOUND_TOOLS)
        """
        from forge.llm.models import ToolDefinition

        # Check tool count limit
        if len(tools) > self.MAX_BOUND_TOOLS:
            raise ValueError(
                f"Too many tools: {len(tools)} exceeds maximum of {self.MAX_BOUND_TOOLS}. "
                f"Consider using fewer tools or splitting into multiple requests."
            )

        # Convert tools to ToolDefinition format
        converted_tools = []
        for tool in tools:
            if isinstance(tool, ToolDefinition):
                converted_tools.append(tool)
            elif hasattr(tool, "to_openai_schema"):
                # Code-Forge BaseTool
                converted_tools.append(tool.to_openai_schema())
            elif hasattr(tool, "name") and hasattr(tool, "description"):
                # LangChain-style tool
                schema = getattr(tool, "args_schema", None)
                params = {}
                if schema:
                    params = schema.model_json_schema()
                converted_tools.append(
                    ToolDefinition(
                        name=tool.name,
                        description=tool.description,
                        parameters=params,
                    )
                )
            else:
                raise ValueError(f"Cannot convert tool: {tool}")

        # Create new instance with tools bound
        new_llm = self.model_copy()
        new_llm._bound_tools = converted_tools
        return new_llm

    def with_structured_output(
        self,
        schema: type | dict,
        *,
        method: str = "json_mode",
        **kwargs: Any,
    ) -> "OpenRouterLLM":
        """
        Configure LLM for structured output.

        Args:
            schema: Pydantic model or JSON schema
            method: Output method ("json_mode" or "function_calling")
            **kwargs: Additional parameters

        Returns:
            Configured LLM instance
        """
        # For now, just bind as a tool if using function calling
        if method == "function_calling":
            from forge.llm.models import ToolDefinition

            if isinstance(schema, type):
                # Pydantic model
                json_schema = schema.model_json_schema()
                name = schema.__name__
            else:
                # Dict schema
                json_schema = schema
                name = schema.get("title", "structured_output")

            tool = ToolDefinition(
                name=name,
                description=f"Output structured data as {name}",
                parameters=json_schema,
            )
            return self.bind_tools([tool], tool_choice={"type": "function", "function": {"name": name}})

        # JSON mode - just return self (response format handled at API level)
        return self
```

---

## Step 3: Tool Adapters

Create `src/forge/langchain/tools.py`:

```python
"""Tool adapters between LangChain and Code-Forge."""

from __future__ import annotations

import asyncio
import json
from typing import Any, TYPE_CHECKING

from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field, create_model

if TYPE_CHECKING:
    from forge.tools.base import BaseTool as Code-ForgeBaseTool
    from forge.tools.executor import ToolExecutor
    from forge.tools.models import ExecutionContext


class LangChainToolAdapter(LangChainBaseTool):
    """
    Adapts an Code-Forge BaseTool to LangChain's tool interface.

    This allows Code-Forge tools to be used seamlessly with LangChain
    agents and chains.

    Example:
        ```python
        from forge.tools import ReadTool
        from forge.langchain.tools import LangChainToolAdapter

        read_tool = ReadTool()
        lc_tool = LangChainToolAdapter(forge_tool=read_tool)

        # Now usable with LangChain agents
        result = lc_tool.invoke({"file_path": "/path/to/file"})
        ```
    """

    forge_tool: Any  # Code-Forge BaseTool
    executor: Any = None  # Optional ToolExecutor
    context: Any = None  # Optional ExecutionContext

    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True

    @property
    def name(self) -> str:
        """Return tool name."""
        return self.forge_tool.name

    @property
    def description(self) -> str:
        """Return tool description."""
        return self.forge_tool.description

    @property
    def args_schema(self) -> type[BaseModel]:
        """
        Generate Pydantic model from Code-Forge tool parameters.

        Returns:
            Dynamically created Pydantic model for arguments
        """
        fields = {}
        for param in self.forge_tool.parameters:
            # Map Code-Forge types to Python types
            type_map = {
                "string": str,
                "integer": int,
                "number": float,
                "boolean": bool,
                "array": list,
                "object": dict,
            }
            python_type = type_map.get(param.type, str)

            # Create field with or without default
            if param.required:
                fields[param.name] = (python_type, Field(description=param.description))
            else:
                fields[param.name] = (
                    python_type | None,
                    Field(default=param.default, description=param.description),
                )

        # Create dynamic model
        model_name = f"{self.forge_tool.name.title().replace('_', '')}Args"
        return create_model(model_name, **fields)

    def _run(self, **kwargs: Any) -> str:
        """
        Execute tool synchronously.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool result as string
        """
        return asyncio.get_event_loop().run_until_complete(
            self._arun(**kwargs)
        )

    async def _arun(self, **kwargs: Any) -> str:
        """
        Execute tool asynchronously.

        Args:
            **kwargs: Tool arguments

        Returns:
            Tool result as string
        """
        from forge.tools.executor import ToolExecutor
        from forge.tools.models import ExecutionContext

        # Get or create executor
        executor = self.executor
        if executor is None:
            executor = ToolExecutor()

        # Get or create context
        context = self.context
        if context is None:
            context = ExecutionContext()

        # Execute through Code-Forge
        result = await executor.execute(
            self.forge_tool,
            kwargs,
            context,
        )

        # Format result
        if result.success:
            if isinstance(result.output, str):
                return result.output
            return json.dumps(result.output, indent=2)
        else:
            return f"Error: {result.error}"


class Code-ForgeToolAdapter:
    """
    Adapts a LangChain tool to Code-Forge's BaseTool interface.

    This allows existing LangChain tools to be used within Code-Forge's
    tool system.

    Example:
        ```python
        from langchain_community.tools import WikipediaQueryRun
        from forge.langchain.tools import forgeToolAdapter

        wiki_tool = WikipediaQueryRun()
        forge_tool = Code-ForgeToolAdapter(langchain_tool=wiki_tool)

        # Now usable with Code-Forge
        result = await tool_executor.execute(forge_tool, {"query": "Python"}, ctx)
        ```
    """

    def __init__(self, langchain_tool: LangChainBaseTool):
        """
        Initialize adapter.

        Args:
            langchain_tool: LangChain tool to wrap
        """
        self.langchain_tool = langchain_tool
        self._parameters = self._extract_parameters()

    @property
    def name(self) -> str:
        """Return tool name."""
        return self.langchain_tool.name

    @property
    def description(self) -> str:
        """Return tool description."""
        return self.langchain_tool.description

    @property
    def category(self) -> str:
        """Return tool category."""
        from forge.tools.models import ToolCategory
        return ToolCategory.OTHER

    @property
    def parameters(self) -> list:
        """Return tool parameters."""
        return self._parameters

    @property
    def requires_confirmation(self) -> bool:
        """Whether tool requires user confirmation."""
        return False

    def _extract_parameters(self) -> list:
        """Extract parameters from LangChain tool schema."""
        from forge.tools.models import ToolParameter

        params = []
        schema = getattr(self.langchain_tool, "args_schema", None)

        if schema:
            json_schema = schema.model_json_schema()
            properties = json_schema.get("properties", {})
            required = json_schema.get("required", [])

            for name, prop in properties.items():
                params.append(
                    ToolParameter(
                        name=name,
                        type=prop.get("type", "string"),
                        description=prop.get("description", ""),
                        required=name in required,
                        default=prop.get("default"),
                    )
                )

        return params

    async def execute(self, params: dict, context: Any) -> Any:
        """
        Execute the LangChain tool.

        Args:
            params: Tool parameters
            context: Execution context

        Returns:
            ToolResult with execution output
        """
        from forge.tools.models import ToolResult

        try:
            # Try async first
            if hasattr(self.langchain_tool, "ainvoke"):
                output = await self.langchain_tool.ainvoke(params)
            else:
                # Fall back to sync
                output = self.langchain_tool.invoke(params)

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=output,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(e),
            )

    def to_openai_schema(self) -> dict:
        """Convert to OpenAI function calling schema."""
        schema = getattr(self.langchain_tool, "args_schema", None)
        params = {}
        if schema:
            params = schema.model_json_schema()

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": params,
            },
        }


def adapt_tools_for_langchain(
    tools: list,
    executor: Any = None,
    context: Any = None,
) -> list[LangChainBaseTool]:
    """
    Convert a list of Code-Forge tools to LangChain tools.

    Args:
        tools: List of Code-Forge BaseTool instances
        executor: Optional ToolExecutor to use
        context: Optional ExecutionContext to use

    Returns:
        List of LangChain-compatible tools
    """
    return [
        LangChainToolAdapter(
            forge_tool=tool,
            executor=executor,
            context=context,
        )
        for tool in tools
    ]


def adapt_tools_for_forge(tools: list[LangChainBaseTool]) -> list:
    """
    Convert a list of LangChain tools to Code-Forge tools.

    Args:
        tools: List of LangChain tools

    Returns:
        List of Code-Forge-compatible tools
    """
    return [Code-ForgeToolAdapter(langchain_tool=tool) for tool in tools]
```

---

## Step 4: Conversation Memory

Create `src/forge/langchain/memory.py`:

```python
"""Conversation memory management for agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from langchain_core.messages import BaseMessage

from forge.langchain.messages import (
    langchain_to_forge,
    forge_to_langchain,
    forge_messages_to_langchain,
)

if TYPE_CHECKING:
    from forge.llm.models import Message


@dataclass
class ConversationMemory:
    """
    Manages conversation history for agent interactions.

    Supports message windowing, token-based truncation, and
    conversion between Code-Forge and LangChain message formats.

    Example:
        ```python
        memory = ConversationMemory(max_messages=100)

        memory.set_system_message(Message.system("You are helpful."))
        memory.add_message(Message.user("Hello!"))
        memory.add_message(Message.assistant("Hi there!"))

        messages = memory.get_messages()  # Returns all messages
        lc_messages = memory.to_langchain_messages()  # For LangChain
        ```
    """

    messages: list["Message"] = field(default_factory=list)
    system_message: "Message | None" = None
    max_messages: int | None = None
    max_tokens: int | None = None
    _token_counter: any = None  # Optional token counter function

    def add_message(self, message: "Message") -> None:
        """
        Add a message to the conversation history.

        Args:
            message: Message to add

        If max_messages is set and exceeded, oldest messages
        (excluding system) are removed.
        """
        from forge.llm.models import MessageRole

        # Don't add system messages to history, use set_system_message
        if message.role == MessageRole.SYSTEM:
            self.system_message = message
            return

        self.messages.append(message)

        # Enforce max messages
        if self.max_messages and len(self.messages) > self.max_messages:
            self._trim_to_count(self.max_messages)

    def add_messages(self, messages: list["Message"]) -> None:
        """
        Add multiple messages to the conversation history.

        Args:
            messages: List of messages to add
        """
        for message in messages:
            self.add_message(message)

    def add_langchain_message(self, message: BaseMessage) -> None:
        """
        Add a LangChain message (will be converted).

        Args:
            message: LangChain message to add
        """
        forge_msg = langchain_to_forge(message)
        self.add_message(forge_msg)

    def get_messages(self) -> list["Message"]:
        """
        Get all messages including system message.

        Returns:
            List of messages with system message first (if set)
        """
        result = []
        if self.system_message:
            result.append(self.system_message)
        result.extend(self.messages)
        return result

    def get_history(self) -> list["Message"]:
        """
        Get only conversation history (no system message).

        Returns:
            List of conversation messages
        """
        return list(self.messages)

    def set_system_message(self, message: "Message") -> None:
        """
        Set or update the system message.

        Args:
            message: System message to set
        """
        from forge.llm.models import MessageRole

        if message.role != MessageRole.SYSTEM:
            from forge.llm.models import Message
            message = Message.system(message.content)

        self.system_message = message

    def clear(self) -> None:
        """Clear all messages (including system message)."""
        self.messages = []
        self.system_message = None

    def clear_history(self) -> None:
        """Clear conversation history but keep system message."""
        self.messages = []

    def _trim_to_count(self, max_count: int) -> None:
        """
        Trim messages to a maximum count.

        Removes oldest messages first, keeping the most recent.

        Args:
            max_count: Maximum number of messages to keep
        """
        if len(self.messages) > max_count:
            self.messages = self.messages[-max_count:]

    def trim(self, max_tokens: int) -> None:
        """
        Trim messages to fit within a token budget.

        Removes oldest messages first until under budget.
        System message is never removed.

        Args:
            max_tokens: Maximum total tokens allowed
        """
        if not self._token_counter:
            # Without token counter, fall back to character estimate
            # Rough estimate: 4 characters per token
            def estimate_tokens(msg):
                content = msg.content or ""
                return len(content) // 4

            self._token_counter = estimate_tokens

        # Count system message tokens
        system_tokens = 0
        if self.system_message:
            system_tokens = self._token_counter(self.system_message)

        available = max_tokens - system_tokens

        # Trim from front until under budget
        while self.messages:
            total = sum(self._token_counter(m) for m in self.messages)
            if total <= available:
                break
            self.messages.pop(0)

    def to_langchain_messages(self) -> list[BaseMessage]:
        """
        Convert all messages to LangChain format.

        Returns:
            List of LangChain BaseMessage instances
        """
        return forge_messages_to_langchain(self.get_messages())

    def from_langchain_messages(self, messages: list[BaseMessage]) -> None:
        """
        Replace history with LangChain messages.

        Args:
            messages: LangChain messages to set
        """
        from forge.llm.models import MessageRole

        self.messages = []
        self.system_message = None

        for msg in messages:
            forge_msg = langchain_to_forge(msg)
            if forge_msg.role == MessageRole.SYSTEM:
                self.system_message = forge_msg
            else:
                self.messages.append(forge_msg)

    def __len__(self) -> int:
        """Return number of messages (excluding system)."""
        return len(self.messages)

    def __iter__(self):
        """Iterate over all messages."""
        return iter(self.get_messages())


@dataclass
class SlidingWindowMemory(ConversationMemory):
    """
    Memory with sliding window over recent messages.

    Keeps only the most recent N message pairs (user + assistant).
    Useful for long conversations where only recent context matters.
    """

    window_size: int = 10  # Number of exchange pairs to keep

    def add_message(self, message: "Message") -> None:
        """Add message and enforce sliding window."""
        super().add_message(message)
        self._enforce_window()

    def _enforce_window(self) -> None:
        """Ensure only window_size pairs are kept."""
        from forge.llm.models import MessageRole

        # Count pairs (user + assistant = 1 pair)
        pair_count = 0
        user_seen = False

        for msg in reversed(self.messages):
            if msg.role == MessageRole.ASSISTANT:
                if user_seen:
                    pair_count += 1
                    user_seen = False
            elif msg.role == MessageRole.USER:
                user_seen = True

        # If over window, trim from front
        while pair_count > self.window_size and len(self.messages) > 2:
            self.messages.pop(0)
            # Recount after removal
            pair_count = 0
            user_seen = False
            for msg in reversed(self.messages):
                if msg.role == MessageRole.ASSISTANT:
                    if user_seen:
                        pair_count += 1
                        user_seen = False
                elif msg.role == MessageRole.USER:
                    user_seen = True


@dataclass
class SummaryMemory(ConversationMemory):
    """
    Memory that summarizes old messages to save tokens.

    When messages exceed a threshold, older messages are
    summarized into a single message, preserving context
    while reducing token usage.
    """

    summary_threshold: int = 20  # Messages before summarizing
    summary: str | None = None
    summarizer: any = None  # LLM to use for summarization

    def get_messages(self) -> list["Message"]:
        """Get messages with summary prepended if available."""
        from forge.llm.models import Message

        result = []

        # Add system message
        if self.system_message:
            result.append(self.system_message)

        # Add summary as a system note if available
        if self.summary:
            result.append(
                Message.system(f"[Previous conversation summary: {self.summary}]")
            )

        # Add recent messages
        result.extend(self.messages)

        return result

    async def maybe_summarize(self) -> None:
        """
        Summarize if messages exceed threshold.

        Requires a summarizer LLM to be set.
        """
        if not self.summarizer or len(self.messages) <= self.summary_threshold:
            return

        # Keep most recent messages, summarize older ones
        to_summarize = self.messages[:-10]
        to_keep = self.messages[-10:]

        if to_summarize:
            # Generate summary
            summary_prompt = (
                "Summarize this conversation in 2-3 sentences, "
                "capturing key points and context:\n\n"
            )
            for msg in to_summarize:
                summary_prompt += f"{msg.role.value}: {msg.content}\n"

            from langchain_core.messages import HumanMessage
            response = await self.summarizer.ainvoke([HumanMessage(content=summary_prompt)])

            # Update state
            if self.summary:
                self.summary = f"{self.summary}\n{response.content}"
            else:
                self.summary = response.content

            self.messages = to_keep
```

---

## Step 5: Callback Handlers

Create `src/forge/langchain/callbacks.py`:

```python
"""Callback handlers for LangChain integration."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult


@dataclass
class Code-ForgeCallbackHandler(BaseCallbackHandler):
    """
    Base callback handler for Code-Forge.

    Provides a foundation for custom callback handlers with
    common utility methods.
    """

    name: str = "forge"
    raise_error: bool = False

    def _safe_call(self, func, *args, **kwargs) -> None:
        """Safely call a function, handling errors."""
        try:
            func(*args, **kwargs)
        except Exception as e:
            if self.raise_error:
                raise
            logging.warning(f"Callback error in {func.__name__}: {e}")


@dataclass
class TokenTrackingCallback(Code-ForgeCallbackHandler):
    """
    Tracks token usage across LLM calls.

    Aggregates prompt and completion tokens for monitoring
    costs and usage patterns.

    Example:
        ```python
        tracker = TokenTrackingCallback()
        llm = OpenRouterLLM(client=client, model="...")

        response = llm.invoke(messages, config={"callbacks": [tracker]})

        print(f"Tokens used: {tracker.get_usage().total_tokens}")
        ```
    """

    name: str = "token_tracker"
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    call_count: int = 0

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Record token usage from LLM response."""
        self.call_count += 1

        if response.llm_output:
            usage = response.llm_output.get("usage", {})
            self.total_prompt_tokens += usage.get("prompt_tokens", 0)
            self.total_completion_tokens += usage.get("completion_tokens", 0)

    def get_usage(self) -> "TokenUsage":
        """
        Get accumulated token usage.

        Returns:
            TokenUsage dataclass with totals
        """
        from forge.llm.models import TokenUsage

        return TokenUsage(
            prompt_tokens=self.total_prompt_tokens,
            completion_tokens=self.total_completion_tokens,
            total_tokens=self.total_prompt_tokens + self.total_completion_tokens,
        )

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.call_count = 0


@dataclass
class LoggingCallback(Code-ForgeCallbackHandler):
    """
    Logs all LLM and tool events for debugging.

    Provides detailed logging of the agent execution flow
    including timing information.

    Example:
        ```python
        import logging
        logging.basicConfig(level=logging.INFO)

        logger = LoggingCallback()
        agent.run(input, callbacks=[logger])
        ```
    """

    name: str = "logger"
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("forge.langchain"))
    log_level: int = logging.INFO
    _start_times: dict = field(default_factory=dict)

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM call start."""
        self._start_times[run_id] = time.time()
        model = serialized.get("kwargs", {}).get("model", "unknown")
        self.logger.log(
            self.log_level,
            f"LLM start: model={model}, prompts={len(prompts)}",
        )

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM call completion."""
        duration = time.time() - self._start_times.pop(run_id, time.time())
        usage = response.llm_output.get("usage", {}) if response.llm_output else {}
        self.logger.log(
            self.log_level,
            f"LLM end: duration={duration:.2f}s, tokens={usage.get('total_tokens', 0)}",
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log LLM errors."""
        self._start_times.pop(run_id, None)
        self.logger.error(f"LLM error: {error}")

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log tool execution start."""
        self._start_times[run_id] = time.time()
        name = serialized.get("name", "unknown")
        self.logger.log(
            self.log_level,
            f"Tool start: {name}",
        )

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log tool execution completion."""
        duration = time.time() - self._start_times.pop(run_id, time.time())
        output_preview = output[:100] + "..." if len(output) > 100 else output
        self.logger.log(
            self.log_level,
            f"Tool end: duration={duration:.2f}s, output={output_preview}",
        )

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Log tool errors."""
        self._start_times.pop(run_id, None)
        self.logger.error(f"Tool error: {error}")


@dataclass
class StreamingCallback(Code-ForgeCallbackHandler):
    """
    Handles streaming output for display.

    Collects streamed tokens and provides callbacks for
    real-time display updates.

    Example:
        ```python
        def on_token(token: str):
            print(token, end="", flush=True)

        streamer = StreamingCallback(on_token=on_token)
        llm.invoke(messages, config={"callbacks": [streamer]})
        ```
    """

    name: str = "streamer"
    on_token: Any = None  # Callable[[str], None]
    on_complete: Any = None  # Callable[[str], None]
    _buffer: str = ""

    def on_llm_new_token(
        self,
        token: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle new streamed token."""
        self._buffer += token
        if self.on_token:
            self.on_token(token)

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        """Handle stream completion."""
        if self.on_complete:
            self.on_complete(self._buffer)
        self._buffer = ""

    def get_buffer(self) -> str:
        """Get accumulated content."""
        return self._buffer

    def clear_buffer(self) -> None:
        """Clear the buffer."""
        self._buffer = ""


@dataclass
class CompositeCallback(Code-ForgeCallbackHandler):
    """
    Combines multiple callbacks into one.

    Useful when you want to apply several callbacks
    without managing them separately.

    Example:
        ```python
        composite = CompositeCallback(callbacks=[
            TokenTrackingCallback(),
            LoggingCallback(),
            StreamingCallback(on_token=print),
        ])

        llm.invoke(messages, config={"callbacks": [composite]})
        ```
    """

    name: str = "composite"
    callbacks: list[BaseCallbackHandler] = field(default_factory=list)

    def on_llm_start(self, *args, **kwargs) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "on_llm_start"):
                cb.on_llm_start(*args, **kwargs)

    def on_llm_end(self, *args, **kwargs) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "on_llm_end"):
                cb.on_llm_end(*args, **kwargs)

    def on_llm_error(self, *args, **kwargs) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "on_llm_error"):
                cb.on_llm_error(*args, **kwargs)

    def on_llm_new_token(self, *args, **kwargs) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "on_llm_new_token"):
                cb.on_llm_new_token(*args, **kwargs)

    def on_tool_start(self, *args, **kwargs) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "on_tool_start"):
                cb.on_tool_start(*args, **kwargs)

    def on_tool_end(self, *args, **kwargs) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "on_tool_end"):
                cb.on_tool_end(*args, **kwargs)

    def on_tool_error(self, *args, **kwargs) -> None:
        for cb in self.callbacks:
            if hasattr(cb, "on_tool_error"):
                cb.on_tool_error(*args, **kwargs)
```

---

## Step 6: Agent Executor

Create `src/forge/langchain/agent.py`:

```python
"""Agent executor for tool-calling workflows."""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal, TYPE_CHECKING

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from forge.langchain.memory import ConversationMemory
from forge.langchain.tools import LangChainToolAdapter

if TYPE_CHECKING:
    from forge.langchain.llm import OpenRouterLLM
    from forge.llm.models import Message, TokenUsage


class AgentEventType(str, Enum):
    """Types of events during agent execution."""
    LLM_START = "llm_start"
    LLM_CHUNK = "llm_chunk"
    LLM_END = "llm_end"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    AGENT_END = "agent_end"
    ERROR = "error"


@dataclass
class AgentEvent:
    """Event during agent execution."""
    type: AgentEventType
    data: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ToolCallRecord:
    """Record of a tool call during agent execution."""
    id: str
    name: str
    arguments: dict
    result: str
    success: bool
    duration: float


@dataclass
class AgentResult:
    """Result of agent execution."""
    output: str
    messages: list["Message"]
    tool_calls: list[ToolCallRecord]
    usage: "TokenUsage"
    iterations: int
    duration: float
    stopped_reason: str  # "complete", "max_iterations", "timeout", "error"


class Code-ForgeAgent:
    """
    Agent executor for tool-calling workflows.

    Implements a ReAct-style agent loop that:
    1. Sends messages to LLM with tool definitions
    2. Parses tool calls from response
    3. Executes tools
    4. Adds tool results to conversation
    5. Continues until done or limit reached

    Example:
        ```python
        from forge.langchain import OpenRouterLLM, Code-ForgeAgent
        from forge.langchain.memory import ConversationMemory

        llm = OpenRouterLLM(client=client, model="anthropic/claude-3-opus")
        memory = ConversationMemory()
        tools = [ReadTool(), WriteTool(), BashTool()]

        agent = Code-ForgeAgent(
            llm=llm,
            tools=tools,
            memory=memory,
            max_iterations=10,
        )

        result = await agent.run("Read the file at /tmp/test.txt")
        print(result.output)
        ```
    """

    def __init__(
        self,
        llm: "OpenRouterLLM",
        tools: list[Any],
        memory: ConversationMemory | None = None,
        max_iterations: int = 10,
        timeout: float = 300.0,
        iteration_timeout: float = 60.0,
    ):
        """
        Initialize agent.

        Args:
            llm: LLM to use for generation
            tools: List of tools available to the agent
            memory: Conversation memory (created if not provided)
            max_iterations: Maximum tool-calling iterations
            timeout: Overall timeout in seconds
            iteration_timeout: Timeout per iteration in seconds
        """
        self.llm = llm
        self.tools = tools
        self.memory = memory or ConversationMemory()
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.iteration_timeout = iteration_timeout

        # Create tool lookup
        self._tool_map: dict[str, Any] = {}
        for tool in tools:
            if hasattr(tool, "name"):
                self._tool_map[tool.name] = tool

        # Bind tools to LLM
        self._bound_llm = self.llm.bind_tools(tools)

    async def run(
        self,
        input: str,
        *,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> AgentResult:
        """
        Run the agent to completion.

        Args:
            input: User input to process
            callbacks: Optional callback handlers

        Returns:
            AgentResult with output and metadata
        """
        from forge.llm.models import Message, TokenUsage

        start_time = time.time()
        tool_call_records: list[ToolCallRecord] = []
        total_usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        iterations = 0
        stopped_reason = "complete"

        # Add user message
        self.memory.add_message(Message.user(input))

        try:
            while iterations < self.max_iterations:
                # Check overall timeout
                if time.time() - start_time > self.timeout:
                    stopped_reason = "timeout"
                    break

                iterations += 1

                # Get LLM response
                messages = self.memory.to_langchain_messages()

                try:
                    response = await asyncio.wait_for(
                        self._bound_llm.ainvoke(
                            messages,
                            config={"callbacks": callbacks} if callbacks else None,
                        ),
                        timeout=self.iteration_timeout,
                    )
                except asyncio.TimeoutError:
                    stopped_reason = "timeout"
                    break

                # Track usage if available
                # (usage tracked via callbacks in practice)

                # Check for tool calls
                if isinstance(response, AIMessage) and response.tool_calls:
                    # Add assistant message to memory
                    from forge.langchain.messages import langchain_to_forge
                    self.memory.add_message(langchain_to_forge(response))

                    # Execute tools
                    for tool_call in response.tool_calls:
                        tool_start = time.time()
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        tool_id = tool_call["id"]

                        tool = self._tool_map.get(tool_name)
                        if tool:
                            try:
                                # Execute tool
                                if isinstance(tool, LangChainToolAdapter):
                                    result = await tool._arun(**tool_args)
                                elif hasattr(tool, "ainvoke"):
                                    result = await tool.ainvoke(tool_args)
                                else:
                                    result = tool.invoke(tool_args)

                                success = True
                            except Exception as e:
                                result = f"Error executing {tool_name}: {e}"
                                success = False
                        else:
                            result = f"Unknown tool: {tool_name}"
                            success = False

                        tool_duration = time.time() - tool_start

                        # Record tool call
                        tool_call_records.append(
                            ToolCallRecord(
                                id=tool_id,
                                name=tool_name,
                                arguments=tool_args,
                                result=result,
                                success=success,
                                duration=tool_duration,
                            )
                        )

                        # Add tool result to memory
                        self.memory.add_message(
                            Message.tool_result(tool_id, result)
                        )

                else:
                    # No tool calls - agent is done
                    content = response.content if hasattr(response, "content") else str(response)
                    self.memory.add_message(Message.assistant(content))
                    break

            else:
                # Max iterations reached
                stopped_reason = "max_iterations"

        except Exception as e:
            stopped_reason = f"error: {e}"

        # Get final output
        messages = self.memory.get_messages()
        output = ""
        if messages:
            last_msg = messages[-1]
            if last_msg.content:
                output = last_msg.content

        return AgentResult(
            output=output,
            messages=messages,
            tool_calls=tool_call_records,
            usage=total_usage,
            iterations=iterations,
            duration=time.time() - start_time,
            stopped_reason=stopped_reason,
        )

    async def stream(
        self,
        input: str,
        *,
        callbacks: list[BaseCallbackHandler] | None = None,
    ) -> AsyncIterator[AgentEvent]:
        """
        Stream agent execution with events.

        Args:
            input: User input to process
            callbacks: Optional callback handlers

        Yields:
            AgentEvent for each significant occurrence
        """
        from forge.llm.models import Message, TokenUsage

        start_time = time.time()
        tool_call_records: list[ToolCallRecord] = []
        iterations = 0

        # Add user message
        self.memory.add_message(Message.user(input))

        try:
            while iterations < self.max_iterations:
                # Check timeout
                if time.time() - start_time > self.timeout:
                    yield AgentEvent(
                        type=AgentEventType.ERROR,
                        data={"error": "timeout", "iterations": iterations},
                    )
                    break

                iterations += 1

                # Yield LLM start event
                yield AgentEvent(
                    type=AgentEventType.LLM_START,
                    data={"iteration": iterations},
                )

                # Stream LLM response
                messages = self.memory.to_langchain_messages()
                full_response = None
                accumulated_content = ""

                async for chunk in self._bound_llm.astream(
                    messages,
                    config={"callbacks": callbacks} if callbacks else None,
                ):
                    if hasattr(chunk, "content") and chunk.content:
                        accumulated_content += chunk.content
                        yield AgentEvent(
                            type=AgentEventType.LLM_CHUNK,
                            data={"content": chunk.content},
                        )
                    full_response = chunk

                # Yield LLM end event
                yield AgentEvent(
                    type=AgentEventType.LLM_END,
                    data={"content": accumulated_content},
                )

                # Check for tool calls
                if hasattr(full_response, "tool_call_chunks") and full_response.tool_call_chunks:
                    # Reconstruct tool calls from chunks
                    # (In streaming, tool calls come as chunks that need assembly)
                    # For simplicity, fall back to non-streaming for tool detection
                    response = await self._bound_llm.ainvoke(messages)

                    if isinstance(response, AIMessage) and response.tool_calls:
                        from forge.langchain.messages import langchain_to_forge
                        self.memory.add_message(langchain_to_forge(response))

                        for tool_call in response.tool_calls:
                            tool_name = tool_call["name"]
                            tool_args = tool_call["args"]
                            tool_id = tool_call["id"]

                            yield AgentEvent(
                                type=AgentEventType.TOOL_START,
                                data={"name": tool_name, "arguments": tool_args},
                            )

                            tool_start = time.time()
                            tool = self._tool_map.get(tool_name)

                            if tool:
                                try:
                                    if isinstance(tool, LangChainToolAdapter):
                                        result = await tool._arun(**tool_args)
                                    elif hasattr(tool, "ainvoke"):
                                        result = await tool.ainvoke(tool_args)
                                    else:
                                        result = tool.invoke(tool_args)
                                    success = True
                                except Exception as e:
                                    result = f"Error: {e}"
                                    success = False
                            else:
                                result = f"Unknown tool: {tool_name}"
                                success = False

                            tool_duration = time.time() - tool_start

                            yield AgentEvent(
                                type=AgentEventType.TOOL_END,
                                data={
                                    "name": tool_name,
                                    "result": result,
                                    "success": success,
                                    "duration": tool_duration,
                                },
                            )

                            tool_call_records.append(
                                ToolCallRecord(
                                    id=tool_id,
                                    name=tool_name,
                                    arguments=tool_args,
                                    result=result,
                                    success=success,
                                    duration=tool_duration,
                                )
                            )

                            self.memory.add_message(
                                Message.tool_result(tool_id, result)
                            )
                else:
                    # No tool calls - done
                    self.memory.add_message(Message.assistant(accumulated_content))
                    break

            # Yield completion event
            yield AgentEvent(
                type=AgentEventType.AGENT_END,
                data={
                    "iterations": iterations,
                    "tool_calls": len(tool_call_records),
                    "duration": time.time() - start_time,
                },
            )

        except Exception as e:
            yield AgentEvent(
                type=AgentEventType.ERROR,
                data={"error": str(e)},
            )

    def reset(self) -> None:
        """Reset agent state (clears memory history)."""
        self.memory.clear_history()
```

---

## Step 7: Package Exports

Create `src/forge/langchain/__init__.py`:

```python
"""
LangChain integration for Code-Forge.

This package provides bridges between LangChain and Code-Forge,
enabling use of OpenRouter's LLM API through LangChain's
ecosystem of tools, agents, and chains.

Example:
    ```python
    from forge.llm import OpenRouterClient
    from forge.langchain import (
        OpenRouterLLM,
        Code-ForgeAgent,
        ConversationMemory,
        LangChainToolAdapter,
    )

    # Create client and LLM
    client = OpenRouterClient(api_key="sk-or-xxx")
    llm = OpenRouterLLM(client=client, model="anthropic/claude-3-opus")

    # Create agent with tools
    tools = [LangChainToolAdapter(forge_tool=ReadTool())]
    memory = ConversationMemory()
    agent = Code-ForgeAgent(llm=llm, tools=tools, memory=memory)

    # Run agent
    result = await agent.run("Read /tmp/test.txt and summarize it")
    print(result.output)
    ```
"""

from forge.langchain.llm import OpenRouterLLM
from forge.langchain.tools import (
    LangChainToolAdapter,
    Code-ForgeToolAdapter,
    adapt_tools_for_langchain,
    adapt_tools_for_forge,
)
from forge.langchain.memory import (
    ConversationMemory,
    SlidingWindowMemory,
    SummaryMemory,
)
from forge.langchain.agent import (
    Code-ForgeAgent,
    AgentEvent,
    AgentEventType,
    AgentResult,
    ToolCallRecord,
)
from forge.langchain.callbacks import (
    Code-ForgeCallbackHandler,
    TokenTrackingCallback,
    LoggingCallback,
    StreamingCallback,
    CompositeCallback,
)
from forge.langchain.messages import (
    langchain_to_forge,
    forge_to_langchain,
    langchain_messages_to_forge,
    forge_messages_to_langchain,
)

__all__ = [
    # LLM
    "OpenRouterLLM",
    # Tools
    "LangChainToolAdapter",
    "Code-ForgeToolAdapter",
    "adapt_tools_for_langchain",
    "adapt_tools_for_forge",
    # Memory
    "ConversationMemory",
    "SlidingWindowMemory",
    "SummaryMemory",
    # Agent
    "Code-ForgeAgent",
    "AgentEvent",
    "AgentEventType",
    "AgentResult",
    "ToolCallRecord",
    # Callbacks
    "Code-ForgeCallbackHandler",
    "TokenTrackingCallback",
    "LoggingCallback",
    "StreamingCallback",
    "CompositeCallback",
    # Message conversion
    "langchain_to_forge",
    "forge_to_langchain",
    "langchain_messages_to_forge",
    "forge_messages_to_langchain",
]
```

---

## Testing Strategy

### Test Files Structure

```
tests/unit/langchain/
├── __init__.py
├── test_messages.py
├── test_llm.py
├── test_tools.py
├── test_memory.py
├── test_callbacks.py
└── test_agent.py
```

### Key Test Cases

1. **test_messages.py**
   - Test all message type conversions both directions
   - Test tool calls in messages
   - Test empty/null content handling

2. **test_llm.py**
   - Test _generate with mocked client
   - Test _agenerate with mocked client
   - Test streaming
   - Test bind_tools

3. **test_tools.py**
   - Test LangChainToolAdapter parameter extraction
   - Test tool execution
   - Test Code-ForgeToolAdapter

4. **test_memory.py**
   - Test message addition
   - Test windowing
   - Test trimming
   - Test conversion to/from LangChain

5. **test_callbacks.py**
   - Test token tracking
   - Test logging output
   - Test streaming buffer

6. **test_agent.py**
   - Test simple completion
   - Test tool calling loop
   - Test max iterations
   - Test timeout handling

---

## Dependencies Update

Add to `pyproject.toml`:

```toml
[tool.poetry.dependencies]
langchain = "^0.3"
langchain-core = "^0.3"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
```
