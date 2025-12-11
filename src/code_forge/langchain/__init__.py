"""
LangChain integration for Code-Forge.

This package provides bridges between LangChain and Code-Forge,
enabling use of OpenRouter's LLM API through LangChain's
ecosystem of tools, agents, and chains.

Example:
    ```python
    from code_forge.llm import OpenRouterClient
    from code_forge.langchain import (
        OpenRouterLLM,
        CodeForgeAgent,
        ConversationMemory,
        LangChainToolAdapter,
    )

    # Create client and LLM
    client = OpenRouterClient(api_key="sk-or-xxx")
    llm = OpenRouterLLM(client=client, model="anthropic/claude-3-opus")

    # Create agent with tools
    tools = [LangChainToolAdapter(forge_tool=ReadTool())]
    memory = ConversationMemory()
    agent = CodeForgeAgent(llm=llm, tools=tools, memory=memory)

    # Run agent
    result = await agent.run("Read /tmp/test.txt and summarize it")
    print(result.output)
    ```
"""

from code_forge.langchain.agent import (
    AgentEvent,
    AgentEventType,
    AgentResult,
    CodeForgeAgent,
    ToolCallRecord,
)
from code_forge.langchain.callbacks import (
    CompositeCallback,
    LoggingCallback,
    CodeForgeCallbackHandler,
    StreamingCallback,
    TokenTrackingCallback,
)
from code_forge.langchain.llm import OpenRouterLLM
from code_forge.langchain.memory import (
    ConversationMemory,
    SlidingWindowMemory,
    SummaryMemory,
)
from code_forge.langchain.messages import (
    langchain_messages_to_forge,
    langchain_to_forge,
    forge_messages_to_langchain,
    forge_to_langchain,
)
from code_forge.langchain.prompts import get_minimal_prompt, get_system_prompt
from code_forge.langchain.tools import (
    LangChainToolAdapter,
    CodeForgeToolAdapter,
    adapt_tools_for_langchain,
    adapt_tools_for_forge,
)

__all__ = [
    "get_minimal_prompt",
    "get_system_prompt",
    "AgentEvent",
    "AgentEventType",
    "AgentResult",
    "CompositeCallback",
    "ConversationMemory",
    "LangChainToolAdapter",
    "LoggingCallback",
    "CodeForgeAgent",
    "CodeForgeCallbackHandler",
    "CodeForgeToolAdapter",
    "OpenRouterLLM",
    "SlidingWindowMemory",
    "StreamingCallback",
    "SummaryMemory",
    "TokenTrackingCallback",
    "ToolCallRecord",
    "adapt_tools_for_langchain",
    "adapt_tools_for_forge",
    "langchain_messages_to_forge",
    "langchain_to_forge",
    "forge_messages_to_langchain",
    "forge_to_langchain",
]
