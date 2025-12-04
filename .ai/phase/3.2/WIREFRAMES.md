# Phase 3.2: LangChain Integration - Wireframes

**Phase:** 3.2
**Name:** LangChain Integration
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 3.1 (OpenRouter Client)

---

## 1. OpenRouterLLM Usage Pattern

### Basic Invocation
```python
from opencode.llm import OpenRouterClient
from opencode.langchain import OpenRouterLLM
from langchain_core.messages import HumanMessage, SystemMessage

# Create client and LLM
client = OpenRouterClient(api_key="sk-or-xxx")
llm = OpenRouterLLM(
    client=client,
    model="anthropic/claude-3-opus",
    temperature=0.7,
    max_tokens=1000,
)

# Invoke with messages
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is the capital of France?"),
]

response = await llm.ainvoke(messages)
print(response.content)
# Output: "The capital of France is Paris."
```

### With Tool Binding
```python
from opencode.tools import ReadTool, WriteTool
from opencode.langchain import adapt_tools_for_langchain

# Adapt OpenCode tools for LangChain
tools = adapt_tools_for_langchain([ReadTool(), WriteTool()])

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# Now responses may include tool calls
response = await llm_with_tools.ainvoke([
    HumanMessage(content="Read the file at /tmp/config.json")
])

if response.tool_calls:
    print(f"Tool call: {response.tool_calls[0]['name']}")
    print(f"Arguments: {response.tool_calls[0]['args']}")
```

---

## 2. Message Conversion Examples

### LangChain to OpenCode
```python
from langchain_core.messages import (
    SystemMessage, HumanMessage, AIMessage, ToolMessage
)
from opencode.langchain import langchain_to_opencode

# System message
lc_sys = SystemMessage(content="Be helpful.")
oc_sys = langchain_to_opencode(lc_sys)
print(oc_sys.to_dict())
# Output: {"role": "system", "content": "Be helpful."}

# Human message
lc_human = HumanMessage(content="Hello!")
oc_human = langchain_to_opencode(lc_human)
print(oc_human.to_dict())
# Output: {"role": "user", "content": "Hello!"}

# AI message with tool calls
lc_ai = AIMessage(
    content="",
    tool_calls=[{
        "id": "call_abc123",
        "name": "read_file",
        "args": {"path": "/tmp/test.txt"}
    }]
)
oc_ai = langchain_to_opencode(lc_ai)
print(oc_ai.to_dict())
# Output:
# {
#     "role": "assistant",
#     "content": null,
#     "tool_calls": [{
#         "id": "call_abc123",
#         "type": "function",
#         "function": {
#             "name": "read_file",
#             "arguments": "{\"path\": \"/tmp/test.txt\"}"
#         }
#     }]
# }

# Tool message
lc_tool = ToolMessage(content="file contents", tool_call_id="call_abc123")
oc_tool = langchain_to_opencode(lc_tool)
print(oc_tool.to_dict())
# Output: {"role": "tool", "tool_call_id": "call_abc123", "content": "file contents"}
```

### OpenCode to LangChain
```python
from opencode.llm import Message
from opencode.langchain import opencode_to_langchain

# System message
oc_sys = Message.system("Be helpful.")
lc_sys = opencode_to_langchain(oc_sys)
print(type(lc_sys).__name__)  # SystemMessage
print(lc_sys.content)  # "Be helpful."

# User message
oc_user = Message.user("Hello!")
lc_user = opencode_to_langchain(oc_user)
print(type(lc_user).__name__)  # HumanMessage

# Assistant with tool calls
from opencode.llm.models import ToolCall
oc_asst = Message.assistant(
    content=None,
    tool_calls=[
        ToolCall(
            id="call_123",
            type="function",
            function={"name": "read_file", "arguments": '{"path": "/tmp"}'}
        )
    ]
)
lc_asst = opencode_to_langchain(oc_asst)
print(lc_asst.tool_calls)
# Output: [{"id": "call_123", "name": "read_file", "args": {"path": "/tmp"}}]
```

---

## 3. Tool Adapter Examples

### OpenCode Tool to LangChain
```python
from opencode.tools import ReadTool
from opencode.langchain import LangChainToolAdapter

# Create adapter
read_tool = ReadTool()
lc_adapter = LangChainToolAdapter(opencode_tool=read_tool)

# Check properties
print(f"Name: {lc_adapter.name}")  # "read"
print(f"Description: {lc_adapter.description}")
print(f"Args schema: {lc_adapter.args_schema.model_json_schema()}")
# Output:
# {
#     "properties": {
#         "file_path": {"type": "string", "description": "Absolute path to file"},
#         "offset": {"type": "integer", "description": "Line offset"},
#         "limit": {"type": "integer", "description": "Max lines to read"}
#     },
#     "required": ["file_path"]
# }

# Invoke
result = await lc_adapter.ainvoke({"file_path": "/tmp/test.txt"})
print(result)
# Output: "     1→Hello, World!\n     2→This is a test file."
```

### LangChain Tool to OpenCode
```python
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from opencode.langchain import opencodeToolAdapter

# Create LangChain tool
wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())

# Adapt for OpenCode
oc_adapter = OpenCodeToolAdapter(langchain_tool=wiki)

# Use in OpenCode
print(f"Name: {oc_adapter.name}")
print(f"Category: {oc_adapter.category}")

# Execute
from opencode.tools.models import ExecutionContext
ctx = ExecutionContext(working_dir="/tmp")
result = await oc_adapter.execute({"query": "Python programming"}, ctx)
print(result.success)  # True
print(result.output[:100])  # First 100 chars of Wikipedia content
```

### Batch Conversion
```python
from opencode.tools import ReadTool, WriteTool, BashTool
from opencode.langchain import adapt_tools_for_langchain

# Convert all tools at once
opencode_tools = [ReadTool(), WriteTool(), BashTool()]
langchain_tools = adapt_tools_for_langchain(opencode_tools)

# Use with LangChain agent
print(f"Converted {len(langchain_tools)} tools")
for tool in langchain_tools:
    print(f"  - {tool.name}: {tool.description[:50]}...")
```

---

## 4. Conversation Memory Examples

### Basic Memory Operations
```python
from opencode.langchain import ConversationMemory
from opencode.llm import Message

memory = ConversationMemory()

# Set system message
memory.set_system_message(Message.system("You are a coding assistant."))

# Add conversation
memory.add_message(Message.user("Hello!"))
memory.add_message(Message.assistant("Hi! How can I help?"))
memory.add_message(Message.user("Write a Python function"))
memory.add_message(Message.assistant("Sure! Here's a function:\n```python\ndef foo(): pass\n```"))

# Get all messages
for msg in memory.get_messages():
    print(f"{msg.role.value}: {msg.content[:30]}...")
# Output:
# system: You are a coding assista...
# user: Hello!...
# assistant: Hi! How can I help?...
# user: Write a Python function...
# assistant: Sure! Here's a function...

# Convert for LangChain
lc_messages = memory.to_langchain_messages()
print(f"LangChain messages: {len(lc_messages)}")
```

### Memory with Limits
```python
# Limit by message count
memory = ConversationMemory(max_messages=10)

# Add many messages
for i in range(20):
    memory.add_message(Message.user(f"Message {i}"))
    memory.add_message(Message.assistant(f"Response {i}"))

print(f"Messages kept: {len(memory)}")  # 10 (most recent)

# Trim by tokens
memory.trim(max_tokens=500)
print(f"Messages after trim: {len(memory)}")
```

### Sliding Window Memory
```python
from opencode.langchain import SlidingWindowMemory

# Keep only last 3 conversation exchanges
memory = SlidingWindowMemory(window_size=3)

memory.set_system_message(Message.system("You are helpful."))

# Add 10 exchanges
for i in range(10):
    memory.add_message(Message.user(f"Question {i}"))
    memory.add_message(Message.assistant(f"Answer {i}"))

# Only last 3 pairs kept
messages = memory.get_messages()
print(f"Total messages: {len(messages)}")  # 7 (1 system + 3 pairs × 2)
```

---

## 5. Callback Handler Examples

### Token Tracking
```python
from opencode.langchain import OpenRouterLLM, TokenTrackingCallback

tracker = TokenTrackingCallback()

llm = OpenRouterLLM(client=client, model="anthropic/claude-3-opus")

# Make multiple calls
for prompt in ["Hello", "How are you?", "What's the weather?"]:
    await llm.ainvoke(
        [HumanMessage(content=prompt)],
        config={"callbacks": [tracker]}
    )

# Check accumulated usage
usage = tracker.get_usage()
print(f"Total prompt tokens: {usage.prompt_tokens}")
print(f"Total completion tokens: {usage.completion_tokens}")
print(f"Total tokens: {usage.total_tokens}")
print(f"API calls: {tracker.call_count}")

# Reset for new session
tracker.reset()
```

### Logging Callback
```python
import logging
from opencode.langchain import LoggingCallback

logging.basicConfig(level=logging.INFO)

logger_callback = LoggingCallback(log_level=logging.INFO)

response = await llm.ainvoke(
    messages,
    config={"callbacks": [logger_callback]}
)

# Console output:
# INFO:opencode.langchain:LLM start: model=anthropic/claude-3-opus, prompts=2
# INFO:opencode.langchain:LLM end: duration=1.23s, tokens=150
```

### Streaming Callback
```python
from opencode.langchain import StreamingCallback

def print_token(token: str):
    print(token, end="", flush=True)

def on_complete(full_text: str):
    print(f"\n\n--- Complete ({len(full_text)} chars) ---")

streamer = StreamingCallback(
    on_token=print_token,
    on_complete=on_complete
)

async for chunk in llm.astream(
    messages,
    config={"callbacks": [streamer]}
):
    pass  # Callback handles output

# Output streams character by character:
# T h e   c a p i t a l   o f   F r a n c e   i s   P a r i s .
#
# --- Complete (35 chars) ---
```

### Composite Callback
```python
from opencode.langchain import (
    CompositeCallback, TokenTrackingCallback, LoggingCallback
)

composite = CompositeCallback(callbacks=[
    TokenTrackingCallback(),
    LoggingCallback(),
])

# Both callbacks receive events
response = await llm.ainvoke(messages, config={"callbacks": [composite]})
```

---

## 6. Agent Execution Examples

### Simple Agent Run
```python
from opencode.langchain import (
    OpenRouterLLM, OpenCodeAgent, ConversationMemory,
    adapt_tools_for_langchain
)
from opencode.tools import ReadTool, WriteTool, BashTool

# Setup
client = OpenRouterClient(api_key="sk-or-xxx")
llm = OpenRouterLLM(client=client, model="anthropic/claude-3-opus")
tools = adapt_tools_for_langchain([ReadTool(), WriteTool(), BashTool()])
memory = ConversationMemory()
memory.set_system_message(Message.system("You are a coding assistant."))

# Create agent
agent = OpenCodeAgent(
    llm=llm,
    tools=tools,
    memory=memory,
    max_iterations=10,
    timeout=300.0,
)

# Run
result = await agent.run("Read /tmp/config.json and tell me what it contains")

print(f"Output: {result.output}")
print(f"Iterations: {result.iterations}")
print(f"Tool calls: {len(result.tool_calls)}")
print(f"Duration: {result.duration:.2f}s")
print(f"Stopped: {result.stopped_reason}")

# Inspect tool calls
for tc in result.tool_calls:
    print(f"  {tc.name}({tc.arguments}) -> {tc.result[:50]}...")
```

### Agent Result Structure
```python
# AgentResult contains:
result = AgentResult(
    output="The config.json file contains database settings...",
    messages=[
        Message(role=USER, content="Read /tmp/config.json..."),
        Message(role=ASSISTANT, tool_calls=[...]),
        Message(role=TOOL, tool_call_id="...", content="..."),
        Message(role=ASSISTANT, content="The config.json file..."),
    ],
    tool_calls=[
        ToolCallRecord(
            id="call_abc123",
            name="read",
            arguments={"file_path": "/tmp/config.json"},
            result='{"database": "postgres", "host": "localhost"}',
            success=True,
            duration=0.05,
        )
    ],
    usage=TokenUsage(prompt_tokens=250, completion_tokens=100, total_tokens=350),
    iterations=2,
    duration=2.5,
    stopped_reason="complete",
)
```

### Streaming Agent
```python
from opencode.langchain import AgentEventType

async for event in agent.stream("Analyze the codebase structure"):
    if event.type == AgentEventType.LLM_START:
        print(f"[Iteration {event.data['iteration']}] Thinking...")

    elif event.type == AgentEventType.LLM_CHUNK:
        print(event.data["content"], end="", flush=True)

    elif event.type == AgentEventType.LLM_END:
        print()  # Newline after streaming

    elif event.type == AgentEventType.TOOL_START:
        print(f"[Tool] {event.data['name']}({event.data['arguments']})")

    elif event.type == AgentEventType.TOOL_END:
        success = "✓" if event.data["success"] else "✗"
        print(f"[Tool] {success} {event.data['duration']:.2f}s")

    elif event.type == AgentEventType.AGENT_END:
        print(f"\n--- Done: {event.data['iterations']} iterations, "
              f"{event.data['tool_calls']} tools ---")

    elif event.type == AgentEventType.ERROR:
        print(f"[Error] {event.data['error']}")
```

### Agent Event Stream Output
```
[Iteration 1] Thinking...
I'll analyze the codebase structure for you. Let me first list the directories.

[Tool] bash({"command": "find . -type d -name '*.py' | head -20"})
[Tool] ✓ 0.15s

[Iteration 2] Thinking...
Now let me look at the main entry points.

[Tool] read({"file_path": "./src/main.py"})
[Tool] ✓ 0.02s

[Iteration 3] Thinking...
Based on my analysis, here's the codebase structure:

1. **src/** - Main source code
   - main.py - Entry point
   - utils/ - Utility modules
   ...

--- Done: 3 iterations, 2 tools ---
```

---

## 7. LCEL Chain Integration

### Basic Chain
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Create chain using LCEL
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that translates {input_language} to {output_language}."),
    ("human", "{text}")
])

chain = prompt | llm | StrOutputParser()

# Invoke
result = await chain.ainvoke({
    "input_language": "English",
    "output_language": "French",
    "text": "Hello, how are you?"
})
print(result)  # "Bonjour, comment allez-vous?"
```

### Chain with Tools
```python
from langchain_core.prompts import ChatPromptTemplate

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# Create chain
chain = prompt | llm_with_tools

# The chain can now return tool calls
response = await chain.ainvoke({"task": "Read the config file"})
if response.tool_calls:
    print("Need to execute tools first")
```

---

## 8. Error Handling Display

### API Error
```python
try:
    response = await llm.ainvoke(messages)
except AuthenticationError as e:
    print(f"Auth failed: {e}")
    # Output: Auth failed: Invalid API key

except RateLimitError as e:
    print(f"Rate limited. Retry after: {e.retry_after}s")
    # Output: Rate limited. Retry after: 30s

except LLMError as e:
    print(f"LLM error: {e}")
```

### Agent Error Handling
```python
result = await agent.run("Do something complex")

if result.stopped_reason == "complete":
    print("Success!")
elif result.stopped_reason == "max_iterations":
    print("Warning: Hit iteration limit")
    print(f"Partial output: {result.output}")
elif result.stopped_reason == "timeout":
    print("Warning: Timed out")
elif result.stopped_reason.startswith("error:"):
    print(f"Error occurred: {result.stopped_reason}")
```

### Tool Error in Agent
```python
# When a tool fails, the error becomes part of the conversation
# Agent output might include:
"""
I tried to read the file but encountered an error:
Error: Permission denied: /etc/shadow

Let me try a different approach...
"""
```

---

## 9. Memory Persistence Pattern

```python
# Save memory state (for Phase 5.1 integration)
import json

def save_memory(memory: ConversationMemory, path: str):
    data = {
        "system": memory.system_message.to_dict() if memory.system_message else None,
        "messages": [m.to_dict() for m in memory.get_history()]
    }
    with open(path, "w") as f:
        json.dump(data, f)

def load_memory(path: str) -> ConversationMemory:
    with open(path) as f:
        data = json.load(f)

    memory = ConversationMemory()
    if data["system"]:
        memory.set_system_message(Message.from_dict(data["system"]))
    for msg_data in data["messages"]:
        memory.add_message(Message.from_dict(msg_data))

    return memory

# Usage
save_memory(memory, "/tmp/session.json")
restored_memory = load_memory("/tmp/session.json")
```

---

## 10. Complete Usage Example

```python
"""Complete example of OpenCode LangChain integration."""

import asyncio
from opencode.llm import OpenRouterClient
from opencode.langchain import (
    OpenRouterLLM,
    OpenCodeAgent,
    ConversationMemory,
    TokenTrackingCallback,
    LoggingCallback,
    adapt_tools_for_langchain,
    AgentEventType,
)
from opencode.tools import ReadTool, WriteTool, EditTool, BashTool, GlobTool
from opencode.llm import Message

async def main():
    # Initialize client
    client = OpenRouterClient(
        api_key="sk-or-xxx",
        app_name="OpenCode",
        timeout=120.0,
    )

    # Create LLM
    llm = OpenRouterLLM(
        client=client,
        model="anthropic/claude-3-opus",
        temperature=0.7,
        max_tokens=4000,
    )

    # Prepare tools
    tools = adapt_tools_for_langchain([
        ReadTool(),
        WriteTool(),
        EditTool(),
        BashTool(),
        GlobTool(),
    ])

    # Setup memory
    memory = ConversationMemory(max_messages=50)
    memory.set_system_message(Message.system(
        "You are OpenCode, an AI coding assistant. "
        "You have access to tools for reading, writing, and executing code. "
        "Be helpful, concise, and accurate."
    ))

    # Setup callbacks
    token_tracker = TokenTrackingCallback()
    logger = LoggingCallback()

    # Create agent
    agent = OpenCodeAgent(
        llm=llm,
        tools=tools,
        memory=memory,
        max_iterations=15,
        timeout=300.0,
    )

    # Run with streaming
    print("OpenCode Agent Ready\n")
    print("=" * 50)

    async for event in agent.stream(
        "Find all Python files in the current directory and show me the first 10 lines of any file containing 'def main'",
        callbacks=[token_tracker, logger],
    ):
        if event.type == AgentEventType.LLM_CHUNK:
            print(event.data["content"], end="", flush=True)
        elif event.type == AgentEventType.TOOL_START:
            print(f"\n[Executing: {event.data['name']}]")
        elif event.type == AgentEventType.TOOL_END:
            status = "✓" if event.data["success"] else "✗"
            print(f"[{status} Done in {event.data['duration']:.2f}s]")
        elif event.type == AgentEventType.AGENT_END:
            print(f"\n\n{'=' * 50}")
            print(f"Completed in {event.data['duration']:.2f}s")
            print(f"Iterations: {event.data['iterations']}")
            print(f"Tool calls: {event.data['tool_calls']}")

    # Show token usage
    usage = token_tracker.get_usage()
    print(f"\nToken Usage:")
    print(f"  Prompt: {usage.prompt_tokens}")
    print(f"  Completion: {usage.completion_tokens}")
    print(f"  Total: {usage.total_tokens}")

    # Cleanup
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Output:
```
OpenCode Agent Ready

==================================================
I'll help you find Python files and show the first 10 lines of files containing 'def main'. Let me start by finding all Python files.

[Executing: bash]
[✓ Done in 0.15s]

I found several Python files. Now let me search for files containing 'def main':

[Executing: bash]
[✓ Done in 0.08s]

Found 3 files with 'def main'. Let me show you the first 10 lines of each:

[Executing: read]
[✓ Done in 0.02s]

**src/main.py:**
```python
#!/usr/bin/env python3
"""Main entry point for OpenCode."""

import asyncio
import sys
from opencode.cli import run

def main():
    """Run the CLI application."""
    asyncio.run(run())
```

[Executing: read]
[✓ Done in 0.02s]
...

==================================================
Completed in 2.45s
Iterations: 3
Tool calls: 4

Token Usage:
  Prompt: 1250
  Completion: 380
  Total: 1630
```
