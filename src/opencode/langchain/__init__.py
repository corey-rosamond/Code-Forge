"""
LangChain integration for OpenCode.

This package provides bridges between LangChain and OpenCode,
enabling use of OpenRouter's LLM API through LangChain's
ecosystem of tools, agents, and chains.

Example:
    ```python
    from opencode.llm import OpenRouterClient
    from opencode.langchain import (
        OpenRouterLLM,
        OpenCodeAgent,
        ConversationMemory,
        LangChainToolAdapter,
    )

    # Create client and LLM
    client = OpenRouterClient(api_key="sk-or-xxx")
    llm = OpenRouterLLM(client=client, model="anthropic/claude-3-opus")

    # Create agent with tools
    tools = [LangChainToolAdapter(opencode_tool=ReadTool())]
    memory = ConversationMemory()
    agent = OpenCodeAgent(llm=llm, tools=tools, memory=memory)

    # Run agent
    result = await agent.run("Read /tmp/test.txt and summarize it")
    print(result.output)
    ```
"""

from opencode.langchain.agent import (
    AgentEvent,
    AgentEventType,
    AgentResult,
    OpenCodeAgent,
    ToolCallRecord,
)
from opencode.langchain.callbacks import (
    CompositeCallback,
    LoggingCallback,
    OpenCodeCallbackHandler,
    StreamingCallback,
    TokenTrackingCallback,
)
from opencode.langchain.llm import OpenRouterLLM
from opencode.langchain.memory import (
    ConversationMemory,
    SlidingWindowMemory,
    SummaryMemory,
)
from opencode.langchain.messages import (
    langchain_messages_to_opencode,
    langchain_to_opencode,
    opencode_messages_to_langchain,
    opencode_to_langchain,
)
from opencode.langchain.tools import (
    LangChainToolAdapter,
    OpenCodeToolAdapter,
    adapt_tools_for_langchain,
    adapt_tools_for_opencode,
)

__all__ = [
    "AgentEvent",
    "AgentEventType",
    "AgentResult",
    "CompositeCallback",
    "ConversationMemory",
    "LangChainToolAdapter",
    "LoggingCallback",
    "OpenCodeAgent",
    "OpenCodeCallbackHandler",
    "OpenCodeToolAdapter",
    "OpenRouterLLM",
    "SlidingWindowMemory",
    "StreamingCallback",
    "SummaryMemory",
    "TokenTrackingCallback",
    "ToolCallRecord",
    "adapt_tools_for_langchain",
    "adapt_tools_for_opencode",
    "langchain_messages_to_opencode",
    "langchain_to_opencode",
    "opencode_messages_to_langchain",
    "opencode_to_langchain",
]
