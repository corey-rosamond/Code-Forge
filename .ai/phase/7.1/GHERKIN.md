# Phase 7.1: Subagents System - Gherkin Specifications

**Phase:** 7.1
**Name:** Subagents System
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 2.1 (Tool System)

---

## Feature: Agent Creation

### Scenario: Create agent with default config
```gherkin
Given an AgentTypeRegistry with "explore" type
When I create an agent with type "explore" and task "Find auth files"
Then agent.agent_type should be "explore"
And agent.state should be PENDING
And agent.id should be a valid UUID
```

### Scenario: Create agent with custom config
```gherkin
Given an AgentConfig with max_tokens=10000
When I create an ExploreAgent with that config
Then agent.config.limits.max_tokens should be 10000
```

### Scenario: Create agent with context
```gherkin
Given an AgentContext with parent_messages
When I create an agent with that context
And inherit_context is True
Then agent.context.parent_messages should be populated
```

### Scenario: Unknown agent type falls back to general
```gherkin
Given a request to create "unknown-type" agent
When I call create_agent("unknown-type", task)
Then result should be a GeneralAgent
```

---

## Feature: Agent Type Registry

### Scenario: Get singleton instance
```gherkin
When I call AgentTypeRegistry.get_instance() twice
Then I should get the same instance both times
```

### Scenario: Built-in types registered
```gherkin
Given a new AgentTypeRegistry
Then it should contain "explore" type
And it should contain "plan" type
And it should contain "code-review" type
And it should contain "general" type
```

### Scenario: Register custom type
```gherkin
Given an AgentTypeRegistry
And a custom AgentTypeDefinition with name "my-agent"
When I call register(type_def)
Then exists("my-agent") should return True
```

### Scenario: Prevent duplicate registration
```gherkin
Given an AgentTypeRegistry with "explore" registered
When I try to register another "explore" type
Then it should raise ValueError
```

---

## Feature: Agent Manager

### Scenario: Get singleton instance
```gherkin
When I call AgentManager.get_instance()
Then I should get the singleton instance
```

### Scenario: Spawn agent
```gherkin
Given an AgentManager with configured executor
When I call spawn("explore", "Find config files")
Then an agent should be created
And agent.state should be RUNNING or PENDING
And agent should be in manager._agents
```

### Scenario: Spawn agent and wait
```gherkin
Given an AgentManager
When I call spawn("explore", task, wait=True)
Then call should block until agent completes
And return value should be the agent
And agent.is_complete should be True
```

### Scenario: Spawn parallel agents
```gherkin
Given an AgentManager
When I call spawn_parallel([<br/>  ("explore", "task1"),<br/>  ("explore", "task2")<br/>])
Then two agents should be created
And both should start executing
```

### Scenario: List agents by state
```gherkin
Given an AgentManager with agents in various states
When I call list_agents(state=COMPLETED)
Then only completed agents should be returned
```

### Scenario: Wait for specific agent
```gherkin
Given a running agent with known ID
When I call wait(agent_id)
Then call should block until that agent completes
And return the AgentResult
```

### Scenario: Wait for all agents
```gherkin
Given multiple running agents
When I call wait_all()
Then call should block until all complete
And return AggregatedResult with all results
```

### Scenario: Cancel agent
```gherkin
Given a running agent
When I call cancel(agent_id)
Then agent.is_cancelled should be True
And agent.state should be CANCELLED
And cancel should return True
```

### Scenario: Cancel nonexistent agent
```gherkin
Given an AgentManager
When I call cancel with an unknown UUID
Then it should return False
```

### Scenario: Cancel all agents
```gherkin
Given 3 running agents
When I call cancel_all()
Then it should return 3
And all agents should be cancelled
```

### Scenario: Concurrent agent limit
```gherkin
Given an AgentManager with max_concurrent=2
When I spawn 5 agents
Then only 2 should run simultaneously
And remaining 3 should wait for slots
```

### Scenario: Get agent statistics
```gherkin
Given an AgentManager with completed agents
When I call get_stats()
Then result should contain total_agents
And result should contain by_state counts
And result should contain total_tokens
```

### Scenario: Cleanup completed agents
```gherkin
Given an AgentManager with 3 completed agents
When I call cleanup_completed()
Then it should return 3
And those agents should be removed from tracking
```

---

## Feature: Agent Execution

### Scenario: Execute explore agent
```gherkin
Given an AgentExecutor with LLM and tools
And an ExploreAgent with task "Find all Python files"
When I call executor.execute(agent)
Then agent should complete
And result should contain findings
```

### Scenario: Tool calls tracked
```gherkin
Given an agent that calls 5 tools
When execution completes
Then agent.usage.tool_calls should be 5
```

### Scenario: Token usage tracked
```gherkin
Given an agent that uses 1000 tokens
When execution completes
Then agent.usage.tokens_used should be 1000
```

### Scenario: Time tracked
```gherkin
Given an agent that runs for 2 seconds
When execution completes
Then agent.usage.time_seconds should be approximately 2
```

### Scenario: Tool filtering
```gherkin
Given an agent with config.tools = ["read", "glob"]
When executor filters tools
Then only "read" and "glob" should be available
```

### Scenario: All tools when not filtered
```gherkin
Given an agent with config.tools = None
When executor filters tools
Then all tools should be available
```

---

## Feature: Resource Limits

### Scenario: Token limit exceeded
```gherkin
Given an agent with max_tokens=1000
And LLM responses use 2000 tokens
When agent executes
Then result.success should be False
And result.error should mention "max_tokens"
```

### Scenario: Time limit exceeded
```gherkin
Given an agent with max_time_seconds=5
And task takes 10 seconds
When agent executes
Then result.success should be False
And result.error should mention "timeout" or "max_time"
```

### Scenario: Tool call limit exceeded
```gherkin
Given an agent with max_tool_calls=10
And agent tries to call 20 tools
When agent executes
Then result.success should be False
And result.error should mention "max_tool_calls"
```

### Scenario: Iteration limit exceeded
```gherkin
Given an agent with max_iterations=5
And agent loops 10 times
When agent executes
Then result.success should be False
And result.error should mention "max_iterations"
```

---

## Feature: Agent Results

### Scenario: Create success result
```gherkin
When I call AgentResult.ok("Completed", data={"files": 5})
Then result.success should be True
And result.output should be "Completed"
And result.data["files"] should be 5
```

### Scenario: Create failure result
```gherkin
When I call AgentResult.fail("Something went wrong")
Then result.success should be False
And result.error should be "Something went wrong"
```

### Scenario: Create cancelled result
```gherkin
When I call AgentResult.cancelled()
Then result.success should be False
And result.error should contain "cancelled"
```

### Scenario: Serialize result to dict
```gherkin
Given an AgentResult with data
When I call to_dict()
Then result should be JSON-serializable
And should contain all fields
```

### Scenario: Deserialize result from dict
```gherkin
Given a serialized AgentResult dict
When I call AgentResult.from_dict(data)
Then result should match original
```

### Scenario: Aggregate results
```gherkin
Given 3 AgentResults (2 success, 1 failure)
When I create AggregatedResult(results)
Then success_count should be 2
And failure_count should be 1
And all_succeeded should be False
And any_succeeded should be True
```

### Scenario: Filter successful results
```gherkin
Given an AggregatedResult with mixed results
When I call get_successful()
Then only successful results should be returned
```

---

## Feature: Agent State

### Scenario: State transitions
```gherkin
Given a new agent
Then state should be PENDING
When execution starts
Then state should be RUNNING
When execution completes successfully
Then state should be COMPLETED
```

### Scenario: Failed state
```gherkin
Given a running agent
When an error occurs during execution
Then state should be FAILED
And is_complete should be True
```

### Scenario: Cancelled state
```gherkin
Given a running agent
When cancel() is called
Then state should be CANCELLED
And is_complete should be True
```

### Scenario: Check is_running
```gherkin
Given an agent in RUNNING state
Then is_running should be True
And is_complete should be False
```

---

## Feature: Agent Context

### Scenario: Inherit parent context
```gherkin
Given parent context with 5 messages
And agent config with inherit_context=True
When agent initializes messages
Then summary of parent context should be included
```

### Scenario: Isolated context
```gherkin
Given parent context with 5 messages
And agent config with inherit_context=False
When agent initializes messages
Then parent messages should not be included
```

### Scenario: Working directory passed
```gherkin
Given AgentContext with working_directory="/project"
When agent executes tools
Then tools should use that working directory
```

---

## Feature: Built-in Agent Types

### Scenario: Explore agent finds files
```gherkin
Given an ExploreAgent with task "Find auth files"
And a codebase with auth/login.py
When agent executes
Then result.data should contain file paths
And "auth/login.py" should be in findings
```

### Scenario: Plan agent creates plan
```gherkin
Given a PlanAgent with task "Add user authentication"
When agent executes
Then result should contain structured plan
And plan should have numbered steps
```

### Scenario: Code review agent finds issues
```gherkin
Given a CodeReviewAgent with task "Review security"
And code with obvious vulnerability
When agent executes
Then result should contain findings
And findings should have severity levels
```

### Scenario: General agent completes task
```gherkin
Given a GeneralAgent with task "Create a config file"
When agent executes
Then task should be completed
And result should describe what was done
```

---

## Feature: Completion Callbacks

### Scenario: Callback on completion
```gherkin
Given an AgentManager
And a registered on_complete callback
When an agent completes
Then callback should be called with that agent
```

### Scenario: Multiple callbacks
```gherkin
Given an AgentManager
And 3 registered callbacks
When an agent completes
Then all 3 callbacks should be called
```

### Scenario: Callback error doesn't break execution
```gherkin
Given a callback that raises an exception
When an agent completes
Then agent should still complete normally
And error should be logged
```

---

## Feature: Agent Serialization

### Scenario: Serialize agent state
```gherkin
Given a completed agent with result
When I call agent.to_dict()
Then result should contain id, agent_type, task
And result should contain state, timestamps
And result should contain usage and result
```

### Scenario: Serialize agent for session
```gherkin
Given an active agent
When session is saved
Then agent state should be serializable
And should be restorable on resume
```

---

## Feature: Progress Reporting

### Scenario: Register progress callback
```gherkin
Given an agent
When I call on_progress(callback)
Then callback should be registered
```

### Scenario: Progress reported during execution
```gherkin
Given an agent with progress callback
When agent executes tools
Then callback should be called with progress message
```

---

## Feature: Error Handling

### Scenario: LLM error handled
```gherkin
Given an agent
When LLM call raises an exception
Then agent should fail gracefully
And result.error should contain error message
And state should be FAILED
```

### Scenario: Tool error handled
```gherkin
Given an agent
When a tool call raises an exception
Then tool result should contain error
And agent should continue or fail gracefully
```

### Scenario: No executor configured
```gherkin
Given an AgentManager without executor
When I try to spawn an agent
Then it should raise RuntimeError
```

---

## Feature: Integration with REPL

### Scenario: Spawn agent from REPL
```gherkin
Given a REPL with AgentManager
When user requests exploration task
Then agent should be spawned
And progress should be displayed
And result should be shown when complete
```

### Scenario: Cancel agent from REPL
```gherkin
Given a running agent
When user presses cancel
Then agent should be cancelled
And partial result should be shown
```
