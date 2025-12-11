# Phase 3.2: LangChain Integration - Gherkin Specifications

**Phase:** 3.2
**Name:** LangChain Integration
**Dependencies:** Phase 2.1 (Tool System Foundation), Phase 3.1 (OpenRouter Client)

---

## Feature: Message Conversion

### Scenario: Convert SystemMessage to Code-Forge
```gherkin
Given a LangChain SystemMessage with content "You are helpful."
When I call langchain_to_forge(message)
Then the result should be an Code-Forge Message
And the role should be MessageRole.SYSTEM
And the content should be "You are helpful."
```

### Scenario: Convert HumanMessage to Code-Forge
```gherkin
Given a LangChain HumanMessage with content "Hello!"
When I call langchain_to_forge(message)
Then the result should be an Code-Forge Message
And the role should be MessageRole.USER
And the content should be "Hello!"
```

### Scenario: Convert AIMessage to Code-Forge
```gherkin
Given a LangChain AIMessage with content "Hi there!"
When I call langchain_to_forge(message)
Then the result should be an Code-Forge Message
And the role should be MessageRole.ASSISTANT
And the content should be "Hi there!"
```

### Scenario: Convert AIMessage with tool calls
```gherkin
Given a LangChain AIMessage with tool_calls:
  | id       | name      | args                    |
  | call_123 | read_file | {"path": "/tmp/test"}   |
When I call langchain_to_forge(message)
Then the result should have tool_calls
And tool_calls[0].id should be "call_123"
And tool_calls[0].function["name"] should be "read_file"
And tool_calls[0].function["arguments"] should be JSON '{"path": "/tmp/test"}'
```

### Scenario: Convert ToolMessage to Code-Forge
```gherkin
Given a LangChain ToolMessage with:
  | content      | "file contents here" |
  | tool_call_id | "call_123"           |
When I call langchain_to_forge(message)
Then the result should be an Code-Forge Message
And the role should be MessageRole.TOOL
And the tool_call_id should be "call_123"
And the content should be "file contents here"
```

### Scenario: Convert Code-Forge system message to LangChain
```gherkin
Given an Code-Forge Message with role=SYSTEM and content="Be helpful"
When I call forge_to_langchain(message)
Then the result should be a SystemMessage
And the content should be "Be helpful"
```

### Scenario: Convert Code-Forge assistant message with tool calls
```gherkin
Given an Code-Forge Message with role=ASSISTANT and tool_calls
When I call forge_to_langchain(message)
Then the result should be an AIMessage
And the tool_calls should be converted to LangChain format
And each tool call should have id, name, and args (as dict)
```

### Scenario: Convert list of messages
```gherkin
Given a list of 3 LangChain messages [SystemMessage, HumanMessage, AIMessage]
When I call langchain_messages_to_forge(messages)
Then the result should be a list of 3 Code-Forge Messages
And each message should have the correct role
```

---

## Feature: OpenRouterLLM

### Scenario: Initialize LLM with client
```gherkin
Given an OpenRouterClient with api_key="sk-or-xxx"
When I create OpenRouterLLM(client=client, model="anthropic/claude-3-opus")
Then the LLM should be configured with the client
And the model should be "anthropic/claude-3-opus"
And temperature should default to 1.0
```

### Scenario: Generate response synchronously
```gherkin
Given an OpenRouterLLM configured with a model
And a list of messages [HumanMessage("Hello!")]
When I call llm.invoke(messages)
Then I should receive an AIMessage
And the content should be the model's response
```

### Scenario: Generate response asynchronously
```gherkin
Given an OpenRouterLLM configured with a model
And a list of messages [HumanMessage("Hello!")]
When I call await llm.ainvoke(messages)
Then I should receive an AIMessage
And the underlying client.complete() should have been called
```

### Scenario: Stream response
```gherkin
Given an OpenRouterLLM configured with a model
And a list of messages
When I iterate async for chunk in llm.astream(messages)
Then I should receive ChatGenerationChunk objects
And each chunk should have content
And chunks should arrive progressively
```

### Scenario: Bind tools to LLM
```gherkin
Given an OpenRouterLLM
And a list of tool definitions
When I call llm.bind_tools(tools)
Then I should receive a new OpenRouterLLM instance
And the new instance should have tools bound
And requests should include tools in the payload
```

### Scenario: LLM with bound tools returns tool calls
```gherkin
Given an OpenRouterLLM with tools bound
And a request that should trigger tool use
When I call llm.invoke(messages)
Then the response should be an AIMessage
And the message should have tool_calls populated
And I can extract tool call details
```

### Scenario: Pass custom parameters
```gherkin
Given an OpenRouterLLM with default temperature=1.0
When I call llm.invoke(messages, temperature=0.5)
Then the request should use temperature=0.5
And the default should not be modified
```

---

## Feature: Tool Adapters

### Scenario: Adapt Code-Forge tool to LangChain
```gherkin
Given an Code-Forge ReadTool
When I create LangChainToolAdapter(forge_tool=read_tool)
Then the adapter should implement LangChain BaseTool
And adapter.name should match read_tool.name
And adapter.description should match read_tool.description
```

### Scenario: Generate args schema from Code-Forge parameters
```gherkin
Given an Code-Forge tool with parameters:
  | name      | type   | required | description       |
  | file_path | string | true     | Path to the file  |
  | encoding  | string | false    | File encoding     |
When I access adapter.args_schema
Then it should be a Pydantic model
And file_path should be a required string field
And encoding should be an optional string field
```

### Scenario: Execute adapted tool
```gherkin
Given a LangChainToolAdapter wrapping ReadTool
When I call adapter.invoke({"file_path": "/tmp/test.txt"})
Then the tool should execute through ToolExecutor
And I should receive the file contents as a string
```

### Scenario: Handle tool execution error
```gherkin
Given a LangChainToolAdapter wrapping ReadTool
When I call adapter.invoke({"file_path": "/nonexistent"})
Then I should receive an error message
And the error should contain "Error:"
```

### Scenario: Adapt LangChain tool to Code-Forge
```gherkin
Given a LangChain tool (e.g., WikipediaQueryRun)
When I create Code-ForgeToolAdapter(langchain_tool=wiki_tool)
Then the adapter should implement Code-Forge BaseTool interface
And I can call adapter.execute(params, context)
And it should return a ToolResult
```

### Scenario: Convert batch of tools
```gherkin
Given a list of 3 Code-Forge tools
When I call adapt_tools_for_langchain(tools)
Then I should receive a list of 3 LangChainToolAdapters
And each adapter should be usable with LangChain agents
```

---

## Feature: Conversation Memory

### Scenario: Add messages to memory
```gherkin
Given a new ConversationMemory
When I add a user message "Hello"
And I add an assistant message "Hi there!"
Then get_messages() should return 2 messages
And the messages should be in order
```

### Scenario: Set system message
```gherkin
Given a ConversationMemory
When I call set_system_message(Message.system("Be helpful"))
And I add user and assistant messages
Then get_messages() should return system message first
And system message should be followed by other messages
```

### Scenario: System message not duplicated in history
```gherkin
Given a ConversationMemory with max_messages=5
When I add a system message via add_message()
Then it should be stored as system_message
And it should NOT be in the messages list
```

### Scenario: Enforce max messages limit
```gherkin
Given a ConversationMemory with max_messages=3
When I add 5 messages
Then get_messages() should return only the last 3 messages
And older messages should be removed
```

### Scenario: Trim by token count
```gherkin
Given a ConversationMemory with messages totaling 1000 tokens
When I call trim(max_tokens=500)
Then oldest messages should be removed
And total tokens should be under 500
And system message should remain intact
```

### Scenario: Convert to LangChain messages
```gherkin
Given a ConversationMemory with mixed messages
When I call to_langchain_messages()
Then I should receive a list of LangChain BaseMessage objects
And each message type should be correctly converted
```

### Scenario: Clear conversation history
```gherkin
Given a ConversationMemory with system message and 10 messages
When I call clear_history()
Then get_history() should return empty list
And system_message should still be set
```

### Scenario: Full clear
```gherkin
Given a ConversationMemory with system message and messages
When I call clear()
Then get_messages() should return empty list
And system_message should be None
```

---

## Feature: Sliding Window Memory

### Scenario: Keep only recent exchanges
```gherkin
Given a SlidingWindowMemory with window_size=2
When I add 10 user/assistant message pairs
Then get_history() should contain only the last 2 pairs
And the window should slide as new messages arrive
```

### Scenario: System message preserved in window
```gherkin
Given a SlidingWindowMemory with system message
When the window slides and removes old messages
Then the system message should always remain
```

---

## Feature: Summary Memory

### Scenario: Summarize when threshold exceeded
```gherkin
Given a SummaryMemory with summary_threshold=5 and a summarizer LLM
When I add 10 messages
And I call maybe_summarize()
Then old messages should be summarized
And summary should contain key points
And only recent messages should remain in history
```

### Scenario: Include summary in messages
```gherkin
Given a SummaryMemory with an existing summary
When I call get_messages()
Then the summary should be included as a system note
And the summary should come after the system message
```

---

## Feature: Callback Handlers

### Scenario: Track token usage
```gherkin
Given a TokenTrackingCallback
When an LLM call completes with usage {prompt: 100, completion: 50}
Then tracker.total_prompt_tokens should be 100
And tracker.total_completion_tokens should be 50
And get_usage().total_tokens should be 150
```

### Scenario: Accumulate usage across calls
```gherkin
Given a TokenTrackingCallback with existing counts
When another LLM call completes with usage {prompt: 50, completion: 25}
Then the totals should be accumulated
And call_count should be incremented
```

### Scenario: Reset token tracking
```gherkin
Given a TokenTrackingCallback with accumulated usage
When I call reset()
Then all counters should be zero
And call_count should be zero
```

### Scenario: Log LLM events
```gherkin
Given a LoggingCallback with a logger
When an LLM call starts
Then "LLM start" should be logged
When the LLM call ends
Then "LLM end" should be logged with duration
```

### Scenario: Log tool events
```gherkin
Given a LoggingCallback
When a tool starts execution
Then "Tool start: {name}" should be logged
When the tool completes
Then "Tool end: duration={X}s" should be logged
```

### Scenario: Stream tokens to callback
```gherkin
Given a StreamingCallback with on_token handler
When LLM streams tokens ["Hello", " ", "World"]
Then on_token should be called 3 times
And get_buffer() should return "Hello World"
```

### Scenario: Composite callback
```gherkin
Given a CompositeCallback with [TokenTracker, Logger]
When an LLM event occurs
Then both callbacks should receive the event
And events should be dispatched in order
```

---

## Feature: Agent Execution

### Scenario: Simple completion without tools
```gherkin
Given an Code-ForgeAgent with LLM and empty tools list
When I call agent.run("What is 2+2?")
Then the agent should return an AgentResult
And result.output should contain the answer
And result.iterations should be 1
And result.tool_calls should be empty
```

### Scenario: Agent with tool execution
```gherkin
Given an Code-ForgeAgent with ReadTool
When I call agent.run("Read /tmp/test.txt")
Then the agent should:
  1. Send request to LLM with tool definitions
  2. Receive tool call from LLM
  3. Execute the tool
  4. Send tool result back to LLM
  5. Receive final response
And result.tool_calls should have 1 entry
And result.iterations should be 2
```

### Scenario: Multiple tool calls in one turn
```gherkin
Given an Code-ForgeAgent with multiple tools
When the LLM returns multiple tool_calls in one response
Then all tools should be executed
And all results should be sent back together
And agent should continue to next iteration
```

### Scenario: Max iterations limit
```gherkin
Given an Code-ForgeAgent with max_iterations=3
When the agent keeps calling tools without completing
Then execution should stop after 3 iterations
And result.stopped_reason should be "max_iterations"
```

### Scenario: Timeout handling
```gherkin
Given an Code-ForgeAgent with timeout=5.0
When execution takes longer than 5 seconds
Then execution should be interrupted
And result.stopped_reason should be "timeout"
```

### Scenario: Stream agent execution
```gherkin
Given an Code-ForgeAgent
When I iterate async for event in agent.stream("Do something")
Then I should receive AgentEvent objects
And events should include LLM_START, LLM_CHUNK, LLM_END
And tool events should include TOOL_START, TOOL_END
And final event should be AGENT_END
```

### Scenario: Tool execution error handling
```gherkin
Given an Code-ForgeAgent with a tool
When the tool execution fails
Then the error should be returned as tool result
And the agent should continue execution
And the LLM should see the error message
```

### Scenario: Agent reset
```gherkin
Given an Code-ForgeAgent with conversation history
When I call agent.reset()
Then memory.get_history() should be empty
And system message should be preserved
```

---

## Feature: Integration with LangChain Chains

### Scenario: Use OpenRouterLLM in LCEL chain
```gherkin
Given an OpenRouterLLM
And a prompt template
When I create chain = prompt | llm | parser
Then the chain should work correctly
And I can call chain.invoke({"input": "..."})
```

### Scenario: Use with LangChain retrieval chain
```gherkin
Given an OpenRouterLLM with tools
And a retrieval setup
When I create a retrieval chain
Then the chain should be able to use the LLM
And tool calls should work within the chain
```

---

## Feature: Error Scenarios

### Scenario: Handle LLM API error in agent
```gherkin
Given an Code-ForgeAgent
When the LLM API returns an error
Then the agent should propagate the error
And result.stopped_reason should contain "error"
```

### Scenario: Handle invalid tool call
```gherkin
Given an Code-ForgeAgent with tools
When the LLM returns a call to unknown tool "fake_tool"
Then the agent should return error as tool result
And execution should continue
```

### Scenario: Handle malformed tool arguments
```gherkin
Given an Code-ForgeAgent
When the LLM returns tool call with invalid JSON arguments
Then the agent should handle gracefully
And return appropriate error message
```

---

## Feature: Async Context Manager

### Scenario: Use LLM as context manager
```gherkin
Given an OpenRouterLLM
When I use:
  async with llm:
      response = await llm.ainvoke(messages)
Then the LLM should work correctly
And resources should be cleaned up after
```

---

## Feature: Model Parameters

### Scenario: Override temperature per request
```gherkin
Given an OpenRouterLLM with temperature=1.0
When I call invoke with temperature=0.5
Then the request should use temperature=0.5
And the LLM's default should remain 1.0
```

### Scenario: Set max tokens
```gherkin
Given an OpenRouterLLM with max_tokens=1000
When I make a request
Then the request payload should include max_tokens=1000
```

### Scenario: Add stop sequences
```gherkin
Given an OpenRouterLLM with stop=["END"]
When I call invoke with stop=["STOP"]
Then the request should include both stop sequences
```
