# Phase 7.1: Subagents System - Completion Criteria

**Phase:** 7.1
**Name:** Subagents System
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 2.1 (Tool System)

---

## Completion Checklist

### 1. Agent Base Classes (base.py)

- [ ] `AgentState` enum implemented
  - [ ] PENDING, RUNNING, COMPLETED, FAILED, CANCELLED values

- [ ] `ResourceLimits` dataclass implemented
  - [ ] `max_tokens: int`
  - [ ] `max_time_seconds: int`
  - [ ] `max_tool_calls: int`
  - [ ] `max_iterations: int`

- [ ] `ResourceUsage` dataclass implemented
  - [ ] `tokens_used: int`
  - [ ] `time_seconds: float`
  - [ ] `tool_calls: int`
  - [ ] `iterations: int`
  - [ ] `cost_usd: float`
  - [ ] `exceeds(limits)` method returns limit name or None

- [ ] `AgentConfig` dataclass implemented
  - [ ] `agent_type: str`
  - [ ] `description: str`
  - [ ] `prompt_addition: str`
  - [ ] `tools: list[str] | None`
  - [ ] `inherit_context: bool`
  - [ ] `limits: ResourceLimits`
  - [ ] `model: str | None`
  - [ ] `for_type(agent_type)` class method

- [ ] `AgentContext` dataclass implemented
  - [ ] `parent_messages: list[dict]`
  - [ ] `working_directory: str`
  - [ ] `environment: dict`
  - [ ] `metadata: dict`
  - [ ] `parent_id: UUID | None`

- [ ] `Agent` abstract base class implemented
  - [ ] `id: UUID` auto-generated
  - [ ] `task: str`
  - [ ] `config: AgentConfig`
  - [ ] `context: AgentContext`
  - [ ] `state: AgentState`
  - [ ] Timestamp properties (created_at, started_at, completed_at)
  - [ ] `agent_type` abstract property
  - [ ] `execute()` abstract async method
  - [ ] `cancel()` method
  - [ ] `is_cancelled`, `is_complete`, `is_running` properties
  - [ ] `result` and `usage` properties
  - [ ] `messages` property
  - [ ] `on_progress(callback)` method
  - [ ] `to_dict()` serialization

### 2. Result Handling (result.py)

- [ ] `AgentResult` dataclass implemented
  - [ ] `success: bool`
  - [ ] `output: str`
  - [ ] `data: Any`
  - [ ] `error: str | None`
  - [ ] `tokens_used: int`
  - [ ] `time_seconds: float`
  - [ ] `tool_calls: int`
  - [ ] `metadata: dict`
  - [ ] `timestamp: datetime`
  - [ ] `ok(output, data)` class method
  - [ ] `fail(error, output)` class method
  - [ ] `cancelled()` class method
  - [ ] `timeout()` class method
  - [ ] `to_dict()` and `to_json()` methods
  - [ ] `from_dict(data)` class method

- [ ] `AggregatedResult` dataclass implemented
  - [ ] `results: list[AgentResult]`
  - [ ] `total_tokens`, `total_time`, `total_tool_calls`
  - [ ] `success_count`, `failure_count`
  - [ ] `all_succeeded`, `any_succeeded` properties
  - [ ] `get_successful()`, `get_failed()` methods
  - [ ] `to_dict()` method

### 3. Agent Types (types.py)

- [ ] `AgentTypeDefinition` dataclass implemented
  - [ ] `name: str`
  - [ ] `description: str`
  - [ ] `prompt_template: str`
  - [ ] `default_tools: list[str] | None`
  - [ ] `default_max_tokens: int`
  - [ ] `default_max_time: int`
  - [ ] `default_model: str | None`

- [ ] Built-in type definitions
  - [ ] `EXPLORE_AGENT` defined
  - [ ] `PLAN_AGENT` defined
  - [ ] `CODE_REVIEW_AGENT` defined
  - [ ] `GENERAL_AGENT` defined

- [ ] `AgentTypeRegistry` singleton implemented
  - [ ] `get_instance()` class method
  - [ ] `reset_instance()` class method
  - [ ] Built-in types auto-registered
  - [ ] `register(type_def)` method
  - [ ] `unregister(name)` method
  - [ ] `get(name)` method
  - [ ] `list_types()` method
  - [ ] `list_definitions()` method
  - [ ] `exists(name)` method

### 4. Agent Executor (executor.py)

- [ ] `AgentExecutor` class implemented
  - [ ] `llm` and `tool_registry` injected
  - [ ] `execute(agent)` async method
  - [ ] `_run_agent_loop()` method
  - [ ] `_call_llm()` method
  - [ ] `_execute_tools()` method
  - [ ] `_build_prompt()` method
  - [ ] `_filter_tools()` method
  - [ ] `_init_messages()` method

- [ ] Execution loop
  - [ ] Checks cancellation each iteration
  - [ ] Checks resource limits
  - [ ] Handles tool calls
  - [ ] Captures final response
  - [ ] Tracks usage throughout

- [ ] Error handling
  - [ ] CancelledError handled
  - [ ] General exceptions caught
  - [ ] Errors captured in result

### 5. Agent Manager (manager.py)

- [ ] `AgentManager` singleton implemented
  - [ ] `get_instance()` class method
  - [ ] `reset_instance()` class method
  - [ ] `set_executor(executor)` method

- [ ] Spawning
  - [ ] `spawn(agent_type, task, config, context, wait)` method
  - [ ] `spawn_parallel(tasks)` method
  - [ ] Creates asyncio tasks
  - [ ] Respects max_concurrent limit

- [ ] Queries
  - [ ] `get_agent(agent_id)` method
  - [ ] `list_agents(state)` method

- [ ] Waiting
  - [ ] `wait(agent_id)` async method
  - [ ] `wait_all(agent_ids)` async method
  - [ ] Returns results properly

- [ ] Cancellation
  - [ ] `cancel(agent_id)` method
  - [ ] `cancel_all()` method
  - [ ] Cancels asyncio tasks

- [ ] Callbacks
  - [ ] `on_complete(callback)` method
  - [ ] Callbacks called on completion

- [ ] Statistics
  - [ ] `get_stats()` method
  - [ ] `cleanup_completed()` method

### 6. Built-in Agents (builtin/)

- [ ] `ExploreAgent` implemented
  - [ ] `agent_type = "explore"`
  - [ ] Proper prompt for exploration

- [ ] `PlanAgent` implemented
  - [ ] `agent_type = "plan"`
  - [ ] Proper prompt for planning

- [ ] `CodeReviewAgent` implemented
  - [ ] `agent_type = "code-review"`
  - [ ] Proper prompt for review

- [ ] `GeneralAgent` implemented
  - [ ] `agent_type = "general"`
  - [ ] Proper prompt for general tasks

- [ ] `create_agent()` factory function
- [ ] `register_agent_class()` function

### 7. Package Exports (__init__.py)

- [ ] All public classes exported
- [ ] `__all__` list complete

### 8. Resource Management

- [ ] Token limit enforcement
- [ ] Time limit enforcement
- [ ] Tool call limit enforcement
- [ ] Iteration limit enforcement
- [ ] Limits checked each iteration
- [ ] Graceful termination on limit

### 9. Parallel Execution

- [ ] Semaphore controls concurrency
- [ ] Multiple agents run simultaneously
- [ ] Results aggregated properly
- [ ] No resource conflicts

### 10. Testing

- [ ] Unit tests for Agent base class
- [ ] Unit tests for AgentResult
- [ ] Unit tests for AgentTypeRegistry
- [ ] Unit tests for AgentExecutor (with mocks)
- [ ] Unit tests for AgentManager
- [ ] Integration tests with real LLM
- [ ] Parallel execution tests
- [ ] Resource limit tests
- [ ] Cancellation tests
- [ ] Test coverage ≥ 90%

### 11. Code Quality

- [ ] McCabe complexity ≤ 10 for all functions
- [ ] Type hints on all public methods
- [ ] Docstrings on all public classes/methods
- [ ] No circular imports
- [ ] Follows project code style

---

## Verification Commands

```bash
# Run unit tests
pytest tests/agents/ -v

# Run with coverage
pytest tests/agents/ --cov=src/opencode/agents --cov-report=term-missing

# Check coverage threshold
pytest tests/agents/ --cov=src/opencode/agents --cov-fail-under=90

# Type checking
mypy src/opencode/agents/

# Complexity check
flake8 src/opencode/agents/ --max-complexity=10
```

---

## Test Scenarios

### Agent Creation Tests

```python
def test_create_agent():
    config = AgentConfig.for_type("explore")
    agent = ExploreAgent(task="Find files", config=config)
    assert agent.agent_type == "explore"
    assert agent.state == AgentState.PENDING
    assert agent.id is not None

def test_create_agent_with_custom_limits():
    limits = ResourceLimits(max_tokens=10000)
    config = AgentConfig(
        agent_type="explore",
        limits=limits,
    )
    agent = ExploreAgent(task="Task", config=config)
    assert agent.config.limits.max_tokens == 10000
```

### Agent Manager Tests

```python
async def test_spawn_agent():
    manager = AgentManager()
    manager.set_executor(mock_executor)

    agent = await manager.spawn("explore", "Find files")
    assert agent is not None
    assert agent.id in manager._agents

async def test_spawn_parallel():
    manager = AgentManager()
    agents = await manager.spawn_parallel([
        ("explore", "Task 1"),
        ("explore", "Task 2"),
    ])
    assert len(agents) == 2

async def test_wait_for_agent():
    manager = AgentManager()
    agent = await manager.spawn("explore", "Task")
    result = await manager.wait(agent.id)
    assert result is not None
```

### Resource Limit Tests

```python
def test_token_limit_exceeded():
    usage = ResourceUsage(tokens_used=60000)
    limits = ResourceLimits(max_tokens=50000)
    assert usage.exceeds(limits) == "max_tokens"

def test_within_limits():
    usage = ResourceUsage(tokens_used=10000)
    limits = ResourceLimits(max_tokens=50000)
    assert usage.exceeds(limits) is None
```

### Cancellation Tests

```python
async def test_cancel_agent():
    manager = AgentManager()
    agent = await manager.spawn("explore", "Task")

    assert manager.cancel(agent.id) == True
    assert agent.state == AgentState.CANCELLED
    assert agent.is_cancelled == True
```

---

## Definition of Done

Phase 7.1 is complete when:

1. All checklist items are checked off
2. All unit tests pass
3. Test coverage is ≥ 90%
4. Code complexity is ≤ 10
5. Type checking passes with no errors
6. All built-in agent types work correctly
7. Parallel execution functions properly
8. Resource limits are enforced
9. Cancellation works reliably
10. Results aggregated correctly
11. Documentation is complete
12. Code review approved

---

## Dependencies Verification

Before starting Phase 7.1, verify:

- [ ] Phase 3.2 (LangChain Integration) is complete
  - [ ] LLM client can make async calls
  - [ ] Tool binding works

- [ ] Phase 2.1 (Tool System) is complete
  - [ ] ToolRegistry available
  - [ ] Tools can be filtered by name

---

## Notes

- Agents are autonomous execution units
- Each agent has isolated context and state
- Resource limits prevent runaway execution
- Parallel execution respects concurrency limits
- Results are structured for easy consumption
- Cancellation is cooperative (checked in loop)
- All state changes logged for debugging
