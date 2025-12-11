# Phase 7.1: Subagents System - UML Diagrams

**Phase:** 7.1
**Name:** Subagents System
**Dependencies:** Phase 3.2 (LangChain Integration), Phase 2.1 (Tool System)

---

## 1. Class Diagram - Agent Base Classes

```mermaid
classDiagram
    class AgentState {
        <<enumeration>>
        PENDING = "pending"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"
    }

    class ResourceLimits {
        +max_tokens: int
        +max_time_seconds: int
        +max_tool_calls: int
        +max_iterations: int
    }

    class ResourceUsage {
        +tokens_used: int
        +time_seconds: float
        +tool_calls: int
        +iterations: int
        +cost_usd: float
        +exceeds(limits) str?
    }

    class AgentConfig {
        +agent_type: str
        +description: str
        +prompt_addition: str
        +tools: list~str~?
        +inherit_context: bool
        +limits: ResourceLimits
        +model: str?
        +for_type(agent_type)$ AgentConfig
    }

    class AgentContext {
        +parent_messages: list~dict~
        +working_directory: str
        +environment: dict
        +metadata: dict
        +parent_id: UUID?
    }

    class Agent {
        <<abstract>>
        +id: UUID
        +task: str
        +config: AgentConfig
        +context: AgentContext
        +state: AgentState
        +created_at: datetime
        +started_at: datetime?
        +completed_at: datetime?
        +agent_type: str*
        +is_complete: bool
        +is_running: bool
        +result: AgentResult?
        +usage: ResourceUsage
        +execute()* AgentResult
        +cancel() void
        +on_progress(callback) void
        +to_dict() dict
    }

    Agent --> AgentState : has
    Agent --> AgentConfig : has
    Agent --> AgentContext : has
    Agent --> ResourceUsage : tracks
    AgentConfig --> ResourceLimits : has
```

---

## 2. Class Diagram - Agent Types

```mermaid
classDiagram
    class Agent {
        <<abstract>>
    }

    class ExploreAgent {
        +agent_type: "explore"
        +execute() AgentResult
    }

    class PlanAgent {
        +agent_type: "plan"
        +execute() AgentResult
    }

    class CodeReviewAgent {
        +agent_type: "code-review"
        +execute() AgentResult
    }

    class GeneralAgent {
        +agent_type: "general"
        +execute() AgentResult
    }

    Agent <|-- ExploreAgent
    Agent <|-- PlanAgent
    Agent <|-- CodeReviewAgent
    Agent <|-- GeneralAgent
```

---

## 3. Class Diagram - Results

```mermaid
classDiagram
    class AgentResult {
        +success: bool
        +output: str
        +data: Any
        +error: str?
        +tokens_used: int
        +time_seconds: float
        +tool_calls: int
        +metadata: dict
        +timestamp: datetime
        +ok(output, data)$ AgentResult
        +fail(error, output)$ AgentResult
        +cancelled(output)$ AgentResult
        +timeout(output)$ AgentResult
        +to_dict() dict
        +to_json() str
        +from_dict(data)$ AgentResult
    }

    class AggregatedResult {
        +results: list~AgentResult~
        +total_tokens: int
        +total_time: float
        +total_tool_calls: int
        +success_count: int
        +failure_count: int
        +all_succeeded: bool
        +any_succeeded: bool
        +get_successful() list~AgentResult~
        +get_failed() list~AgentResult~
        +to_dict() dict
    }

    AggregatedResult --> AgentResult : contains
```

---

## 4. Class Diagram - Type Registry

```mermaid
classDiagram
    class AgentTypeDefinition {
        +name: str
        +description: str
        +prompt_template: str
        +default_tools: list~str~?
        +default_max_tokens: int
        +default_max_time: int
        +default_model: str?
    }

    class AgentTypeRegistry {
        -_instance: AgentTypeRegistry$
        -_types: dict~str, AgentTypeDefinition~
        +get_instance()$ AgentTypeRegistry
        +reset_instance()$ void
        +register(type_def) void
        +unregister(name) bool
        +get(name) AgentTypeDefinition?
        +list_types() list~str~
        +list_definitions() list~AgentTypeDefinition~
        +exists(name) bool
    }

    AgentTypeRegistry o-- AgentTypeDefinition : contains
```

---

## 5. Class Diagram - Executor and Manager

```mermaid
classDiagram
    class AgentExecutor {
        +llm: OpenRouterLLM
        +tool_registry: ToolRegistry
        +execute(agent) AgentResult
        -_run_agent_loop(agent, messages, tools) AgentResult
        -_call_llm(messages, tools, agent) dict
        -_execute_tools(tool_calls, agent) list~dict~
        -_build_prompt(agent) str
        -_filter_tools(agent) list
        -_init_messages(agent, prompt) list~dict~
    }

    class AgentManager {
        -_instance: AgentManager$
        -_executor: AgentExecutor
        -_max_concurrent: int
        -_agents: dict~UUID, Agent~
        -_tasks: dict~UUID, Task~
        -_semaphore: Semaphore
        +get_instance()$ AgentManager
        +spawn(type, task, config, context, wait) Agent
        +spawn_parallel(tasks) list~Agent~
        +get_agent(id) Agent?
        +list_agents(state?) list~Agent~
        +wait(id) AgentResult?
        +wait_all(ids?) AggregatedResult
        +cancel(id) bool
        +cancel_all() int
        +on_complete(callback) void
        +get_stats() dict
        +cleanup_completed() int
    }

    AgentManager --> AgentExecutor : uses
    AgentManager o-- Agent : manages
```

---

## 6. Package Diagram

```mermaid
flowchart TB
    subgraph AgentsPkg["src/forge/agents/"]
        INIT["__init__.py"]
        BASE["base.py<br/>Agent, AgentConfig, AgentState"]
        RESULT["result.py<br/>AgentResult, AggregatedResult"]
        TYPES["types.py<br/>AgentTypeRegistry"]
        EXECUTOR["executor.py<br/>AgentExecutor"]
        MANAGER["manager.py<br/>AgentManager"]

        subgraph BuiltinPkg["builtin/"]
            EXPLORE["explore.py"]
            PLAN["plan.py"]
            REVIEW["review.py"]
            GENERAL["general.py"]
        end
    end

    subgraph LLMPkg["src/forge/llm/"]
        LLM["openrouter.py"]
    end

    subgraph ToolsPkg["src/forge/tools/"]
        TOOLS["registry.py"]
    end

    EXECUTOR --> BASE
    EXECUTOR --> RESULT
    EXECUTOR --> LLM
    EXECUTOR --> TOOLS

    MANAGER --> EXECUTOR
    MANAGER --> BASE
    MANAGER --> RESULT
    MANAGER --> TYPES

    BuiltinPkg --> BASE
    BuiltinPkg --> RESULT

    INIT --> BASE
    INIT --> RESULT
    INIT --> TYPES
    INIT --> EXECUTOR
    INIT --> MANAGER
    INIT --> BuiltinPkg
```

---

## 7. Sequence Diagram - Spawn and Execute Agent

```mermaid
sequenceDiagram
    participant Parent as Parent Agent/REPL
    participant Manager as AgentManager
    participant Registry as AgentTypeRegistry
    participant Agent
    participant Executor as AgentExecutor
    participant LLM

    Parent->>Manager: spawn("explore", task)

    Manager->>Registry: get("explore")
    Registry-->>Manager: AgentTypeDefinition

    Manager->>Manager: Create AgentConfig
    Manager->>Agent: new ExploreAgent(task, config)

    Manager->>Manager: Create asyncio.Task
    Manager-->>Parent: Agent (pending)

    Note over Manager: Running in background

    Manager->>Executor: execute(agent)
    Executor->>Executor: _build_prompt(agent)
    Executor->>Executor: _filter_tools(agent)
    Executor->>Executor: _init_messages(agent)

    loop Agent Loop
        Executor->>LLM: agenerate(messages, tools)
        LLM-->>Executor: Response

        alt Has Tool Calls
            Executor->>Executor: _execute_tools(calls)
            Executor->>Agent: Update usage
        else Final Response
            Executor->>Executor: Break loop
        end
    end

    Executor->>Agent: _complete_execution(result)
    Executor-->>Manager: AgentResult

    Manager->>Manager: Notify callbacks
```

---

## 8. Sequence Diagram - Parallel Execution

```mermaid
sequenceDiagram
    participant Parent
    participant Manager as AgentManager
    participant Semaphore
    participant Agent1
    participant Agent2
    participant Agent3
    participant Executor

    Parent->>Manager: spawn_parallel([<br/>  ("explore", task1),<br/>  ("explore", task2),<br/>  ("explore", task3)<br/>])

    Manager->>Agent1: Create
    Manager->>Agent2: Create
    Manager->>Agent3: Create

    par Execute Agent1
        Manager->>Semaphore: acquire
        Semaphore-->>Manager: OK
        Manager->>Executor: execute(Agent1)
        Executor-->>Manager: Result1
        Manager->>Semaphore: release
    and Execute Agent2
        Manager->>Semaphore: acquire
        Semaphore-->>Manager: OK
        Manager->>Executor: execute(Agent2)
        Executor-->>Manager: Result2
        Manager->>Semaphore: release
    and Execute Agent3
        Manager->>Semaphore: acquire
        Semaphore-->>Manager: OK (when slot available)
        Manager->>Executor: execute(Agent3)
        Executor-->>Manager: Result3
        Manager->>Semaphore: release
    end

    Manager-->>Parent: [Agent1, Agent2, Agent3]

    Parent->>Manager: wait_all()
    Manager-->>Parent: AggregatedResult
```

---

## 9. Sequence Diagram - Resource Limit Exceeded

```mermaid
sequenceDiagram
    participant Executor as AgentExecutor
    participant Agent
    participant LLM

    Executor->>Agent: _start_execution()

    loop Agent Loop
        Executor->>Agent: Check usage.exceeds(limits)

        alt Within Limits
            Executor->>LLM: agenerate(messages, tools)
            LLM-->>Executor: Response
            Executor->>Agent: Update usage
        else Exceeds Limits
            Executor->>Executor: Create fail result
            Note over Executor: "Resource limit exceeded: max_tokens"
            Executor->>Agent: _complete_execution(fail_result)
            Executor-->>Executor: Return result
        end
    end
```

---

## 10. Sequence Diagram - Cancellation

```mermaid
sequenceDiagram
    participant Parent
    participant Manager as AgentManager
    participant Agent
    participant Task as asyncio.Task
    participant Executor

    Note over Agent: Agent is running

    Parent->>Manager: cancel(agent_id)

    Manager->>Agent: cancel()
    Agent->>Agent: _cancelled = True
    Agent->>Agent: state = CANCELLED

    Manager->>Task: cancel()
    Task-->>Executor: CancelledError

    Executor->>Agent: Check is_cancelled
    Executor->>Executor: Create cancelled result
    Executor-->>Manager: AgentResult(cancelled)

    Manager-->>Parent: True
```

---

## 11. State Diagram - Agent Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Created

    PENDING --> RUNNING: Execution starts
    PENDING --> CANCELLED: cancel() before start

    RUNNING --> COMPLETED: Task finished
    RUNNING --> FAILED: Error occurred
    RUNNING --> CANCELLED: cancel() during run
    RUNNING --> FAILED: Resource limit exceeded

    COMPLETED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```

---

## 12. Activity Diagram - Agent Execution Loop

```mermaid
flowchart TD
    START([Start Execution]) --> BUILD[Build System Prompt]
    BUILD --> FILTER[Filter Available Tools]
    FILTER --> INIT[Initialize Messages]
    INIT --> LOOP{Agent Loop}

    LOOP --> CHECK{Check Limits}

    CHECK -->|Exceeded| LIMIT_ERR[Create Limit Error Result]
    LIMIT_ERR --> COMPLETE

    CHECK -->|OK| CANCELLED{Cancelled?}

    CANCELLED -->|Yes| CANCEL_RES[Create Cancelled Result]
    CANCEL_RES --> COMPLETE

    CANCELLED -->|No| LLM[Call LLM]

    LLM --> RESPONSE{Response Type}

    RESPONSE -->|Tool Calls| TOOLS[Execute Tools]
    TOOLS --> UPDATE[Update Usage]
    UPDATE --> ADD_MSG[Add to Messages]
    ADD_MSG --> LOOP

    RESPONSE -->|Final Text| EXTRACT[Extract Response]
    EXTRACT --> SUCCESS[Create Success Result]
    SUCCESS --> COMPLETE

    RESPONSE -->|Empty| ERR[Create Error Result]
    ERR --> COMPLETE

    COMPLETE([Complete Execution])
```

---

## 13. Component Diagram - Agent System

```mermaid
flowchart LR
    subgraph Input
        PARENT[Parent Agent/REPL]
        TASK[Task Description]
    end

    subgraph Management
        MANAGER[AgentManager]
        REGISTRY[TypeRegistry]
        SEMAPHORE[Concurrency Control]
    end

    subgraph Execution
        EXECUTOR[AgentExecutor]
        AGENTS[Agent Instances]
    end

    subgraph Resources
        LLM[LLM Client]
        TOOLS[Tool Registry]
    end

    subgraph Output
        RESULTS[AgentResult]
        AGGREGATED[AggregatedResult]
    end

    PARENT --> MANAGER
    TASK --> MANAGER

    MANAGER --> REGISTRY
    MANAGER --> SEMAPHORE
    MANAGER --> EXECUTOR
    MANAGER --> AGENTS

    EXECUTOR --> LLM
    EXECUTOR --> TOOLS

    AGENTS --> RESULTS
    RESULTS --> AGGREGATED
    AGGREGATED --> PARENT
```

---

## 14. Agent Type Hierarchy

```
AgentTypeRegistry
├── explore
│   ├── Tools: glob, grep, read
│   ├── Max Tokens: 30,000
│   └── Max Time: 180s
├── plan
│   ├── Tools: glob, grep, read
│   ├── Max Tokens: 40,000
│   └── Max Time: 240s
├── code-review
│   ├── Tools: glob, grep, read, bash
│   ├── Max Tokens: 40,000
│   └── Max Time: 300s
└── general
    ├── Tools: all
    ├── Max Tokens: 50,000
    └── Max Time: 300s
```

---

## 15. Resource Tracking Flow

```mermaid
flowchart TB
    subgraph Limits["ResourceLimits"]
        MAX_TOK[max_tokens: 50000]
        MAX_TIME[max_time_seconds: 300]
        MAX_CALLS[max_tool_calls: 100]
        MAX_ITER[max_iterations: 50]
    end

    subgraph Usage["ResourceUsage"]
        TOKENS[tokens_used: 0]
        TIME[time_seconds: 0]
        CALLS[tool_calls: 0]
        ITER[iterations: 0]
    end

    subgraph Loop["Execution Loop"]
        LLM_CALL[LLM Call]
        TOOL_CALL[Tool Execution]
        CHECK[Check exceeds()]
    end

    LLM_CALL --> |add response tokens| TOKENS
    TOOL_CALL --> |increment| CALLS
    Loop --> |track elapsed| TIME
    Loop --> |increment| ITER

    CHECK --> |compare| Limits
    CHECK --> |if exceeded| ABORT[Abort with Error]
```

---

## Notes

- Agents run asynchronously and independently
- Semaphore controls concurrent agent count
- Each agent has isolated message history
- Resource limits prevent runaway execution
- Results aggregated for parallel agents
- Agent state persisted for tracking
- Cancellation is cooperative (checked in loop)
