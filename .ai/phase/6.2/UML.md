# Phase 6.2: Operating Modes - UML Diagrams

**Phase:** 6.2
**Name:** Operating Modes
**Dependencies:** Phase 1.3 (Basic REPL Shell), Phase 3.2 (LangChain Integration)

---

## 1. Class Diagram - Mode Base Classes

```mermaid
classDiagram
    class ModeName {
        <<enumeration>>
        NORMAL = "normal"
        PLAN = "plan"
        THINKING = "thinking"
        HEADLESS = "headless"
    }

    class ModeConfig {
        +name: ModeName
        +description: str
        +system_prompt_addition: str
        +enabled: bool
        +settings: dict
        +get_setting(key, default) Any
        +set_setting(key, value) void
    }

    class ModeContext {
        +session: Any
        +config: Any
        +output: Callable
        +data: dict
        +get(key, default) Any
        +set(key, value) void
    }

    class ModeState {
        +mode_name: ModeName
        +active: bool
        +data: dict
        +to_dict() dict
        +from_dict(data)$ ModeState
    }

    class Mode {
        <<abstract>>
        #_config: ModeConfig
        #_state: ModeState
        +name: ModeName*
        +config: ModeConfig
        +state: ModeState
        +is_active: bool
        +activate(context)* void
        +deactivate(context)* void
        +modify_prompt(base) str
        +modify_response(response) str
        +should_auto_activate(message) bool
        +save_state() dict
        +restore_state(data) void
        #_default_config()* ModeConfig
    }

    Mode --> ModeConfig : has
    Mode --> ModeState : has
    Mode --> ModeName : identifies
    ModeConfig --> ModeName : has
```

---

## 2. Class Diagram - Concrete Modes

```mermaid
classDiagram
    class Mode {
        <<abstract>>
    }

    class NormalMode {
        +name: NORMAL
        +activate(context) void
        +deactivate(context) void
    }

    class PlanMode {
        +name: PLAN
        +current_plan: Plan?
        +activate(context) void
        +deactivate(context) void
        +should_auto_activate(message) bool
        +set_plan(plan) void
        +get_plan() Plan?
        +show_plan() str
        +execute_plan() list~dict~
        +cancel_plan() void
    }

    class ThinkingMode {
        +name: THINKING
        +thinking_config: ThinkingConfig
        -_start_time: float?
        +activate(context) void
        +deactivate(context) void
        +set_deep_mode(enabled) void
        +set_thinking_budget(tokens) void
        +modify_response(response) str
        +format_thinking_output(result) str
        +get_last_thinking() ThinkingResult?
    }

    class HeadlessMode {
        +name: HEADLESS
        +headless_config: HeadlessConfig
        -_input_stream: TextIO?
        -_output_stream: TextIO?
        +activate(context) void
        +deactivate(context) void
        +read_input() str
        +write_output(result) void
        +handle_permission_request(op, safe) bool
        +create_result(...) HeadlessResult
        +check_timeout() bool
    }

    Mode <|-- NormalMode
    Mode <|-- PlanMode
    Mode <|-- ThinkingMode
    Mode <|-- HeadlessMode
```

---

## 3. Class Diagram - Plan Mode Data

```mermaid
classDiagram
    class PlanStep {
        +number: int
        +description: str
        +substeps: list~PlanStep~
        +completed: bool
        +files: list~str~
        +dependencies: list~int~
        +complexity: str
        +to_markdown(indent) str
        +to_dict() dict
        +from_dict(data)$ PlanStep
    }

    class Plan {
        +title: str
        +summary: str
        +steps: list~PlanStep~
        +considerations: list~str~
        +success_criteria: list~str~
        +created_at: datetime
        +updated_at: datetime
        +to_markdown() str
        +to_todos() list~dict~
        +progress: tuple~int, int~
        +progress_percentage: float
        +mark_step_complete(number) bool
        +to_dict() dict
        +from_dict(data)$ Plan
    }

    class PlanMode {
        +current_plan: Plan?
        +set_plan(plan) void
        +show_plan() str
        +execute_plan() list~dict~
    }

    PlanMode --> Plan : manages
    Plan --> PlanStep : contains
    PlanStep --> PlanStep : substeps
```

---

## 4. Class Diagram - Thinking Mode Data

```mermaid
classDiagram
    class ThinkingConfig {
        +max_thinking_tokens: int
        +show_thinking: bool
        +thinking_style: str
        +deep_mode: bool
    }

    class ThinkingResult {
        +thinking: str
        +response: str
        +thinking_tokens: int
        +response_tokens: int
        +time_seconds: float
        +timestamp: datetime
        +to_dict() dict
    }

    class ThinkingMode {
        +thinking_config: ThinkingConfig
        +modify_response(response) str
        +format_thinking_output(result) str
        +get_last_thinking() ThinkingResult?
    }

    ThinkingMode --> ThinkingConfig : configured by
    ThinkingMode --> ThinkingResult : produces
```

---

## 5. Class Diagram - Headless Mode Data

```mermaid
classDiagram
    class OutputFormat {
        <<enumeration>>
        TEXT = "text"
        JSON = "json"
    }

    class HeadlessConfig {
        +input_file: str?
        +output_file: str?
        +output_format: OutputFormat
        +timeout: int
        +auto_approve_safe: bool
        +fail_on_unsafe: bool
        +exit_on_complete: bool
    }

    class HeadlessResult {
        +success: bool
        +message: str
        +output: str
        +error: str?
        +exit_code: int
        +execution_time: float
        +details: dict
        +timestamp: datetime
        +to_json() str
        +to_text() str
    }

    class HeadlessMode {
        +headless_config: HeadlessConfig
        +read_input() str
        +write_output(result) void
        +create_result(...) HeadlessResult
    }

    HeadlessMode --> HeadlessConfig : configured by
    HeadlessMode --> HeadlessResult : produces
    HeadlessConfig --> OutputFormat : uses
```

---

## 6. Class Diagram - Mode Manager

```mermaid
classDiagram
    class ModeManager {
        -_instance: ModeManager$
        -_modes: dict~ModeName, Mode~
        -_current_mode: ModeName
        -_mode_stack: list~ModeName~
        -_on_mode_change: list~Callable~
        +get_instance()$ ModeManager
        +reset_instance()$ void
        +register_mode(mode) void
        +unregister_mode(name) bool
        +get_mode(name) Mode?
        +get_current_mode() Mode
        +current_mode_name: ModeName
        +list_modes() list~Mode~
        +list_enabled_modes() list~Mode~
        +switch_mode(name, context, push) bool
        +pop_mode(context) ModeName?
        +reset_mode(context) void
        +get_system_prompt(base) str
        +process_response(response) str
        +check_auto_activation(message) ModeName?
        +on_mode_change(callback) void
        +save_state() dict
        +restore_state(data, context) void
    }

    class Mode {
        <<abstract>>
    }

    class ModeContext {
        +session: Any
        +config: Any
        +output: Callable
    }

    ModeManager o-- Mode : manages
    ModeManager --> ModeContext : uses
```

---

## 7. Package Diagram

```mermaid
flowchart TB
    subgraph ModesPkg["src/forge/modes/"]
        INIT["__init__.py"]
        BASE["base.py<br/>Mode, ModeConfig, ModeContext"]
        PROMPTS["prompts.py<br/>Mode prompt templates"]
        MANAGER["manager.py<br/>ModeManager"]
        PLAN["plan.py<br/>PlanMode, Plan"]
        THINKING["thinking.py<br/>ThinkingMode"]
        HEADLESS["headless.py<br/>HeadlessMode"]
    end

    subgraph REPLPkg["src/forge/repl/"]
        REPL["repl.py"]
    end

    subgraph SessionsPkg["src/forge/sessions/"]
        SESSION["manager.py"]
    end

    subgraph CommandsPkg["src/forge/commands/"]
        COMMANDS["builtin/"]
    end

    MANAGER --> BASE
    PLAN --> BASE
    PLAN --> PROMPTS
    THINKING --> BASE
    THINKING --> PROMPTS
    HEADLESS --> BASE
    HEADLESS --> PROMPTS

    INIT --> BASE
    INIT --> MANAGER
    INIT --> PLAN
    INIT --> THINKING
    INIT --> HEADLESS

    REPL --> MANAGER
    COMMANDS --> MANAGER
    MANAGER --> SESSION
```

---

## 8. Sequence Diagram - Mode Switch

```mermaid
sequenceDiagram
    participant User
    participant REPL
    participant Manager as ModeManager
    participant OldMode as Current Mode
    participant NewMode as Target Mode
    participant Context as ModeContext

    User->>REPL: /plan
    REPL->>REPL: Create ModeContext
    REPL->>Manager: switch_mode(PLAN, context)

    Manager->>OldMode: deactivate(context)
    OldMode->>OldMode: Save state
    OldMode-->>Manager: Done

    Manager->>Manager: Push to mode stack

    Manager->>NewMode: activate(context)
    NewMode->>Context: output("Entered plan mode...")
    NewMode-->>Manager: Done

    Manager->>Manager: Update current_mode

    Manager->>Manager: Notify listeners
    Manager-->>REPL: True (success)

    REPL->>User: Display mode change message
```

---

## 9. Sequence Diagram - Plan Creation

```mermaid
sequenceDiagram
    participant User
    participant REPL
    participant PlanMode
    participant LLM

    User->>REPL: "Plan how to add auth"

    REPL->>REPL: Check auto-activation
    Note over REPL: Matches planning pattern

    REPL->>PlanMode: activate(context)
    PlanMode-->>User: "Entered plan mode..."

    REPL->>REPL: Modify system prompt
    REPL->>LLM: Send with plan prompt

    LLM-->>REPL: Plan response

    REPL->>PlanMode: Parse plan from response
    PlanMode->>PlanMode: Create Plan object

    PlanMode->>PlanMode: set_plan(plan)
    PlanMode-->>User: Display formatted plan

    User->>REPL: /plan execute

    REPL->>PlanMode: execute_plan()
    PlanMode-->>REPL: list of todos

    REPL->>REPL: Create TodoWrite items
```

---

## 10. Sequence Diagram - Thinking Response

```mermaid
sequenceDiagram
    participant User
    participant REPL
    participant ThinkingMode
    participant LLM

    User->>REPL: /think

    REPL->>ThinkingMode: activate(context)
    ThinkingMode->>ThinkingMode: Start timer
    ThinkingMode-->>User: "Entered thinking mode..."

    User->>REPL: "Compare REST vs GraphQL"

    REPL->>REPL: get_system_prompt()
    Note over REPL: Includes thinking prompt

    REPL->>LLM: Send query

    LLM-->>REPL: Response with<br/><thinking>...</thinking><br/><response>...</response>

    REPL->>ThinkingMode: modify_response(response)

    ThinkingMode->>ThinkingMode: Extract thinking section
    ThinkingMode->>ThinkingMode: Extract response section
    ThinkingMode->>ThinkingMode: Create ThinkingResult

    ThinkingMode->>ThinkingMode: format_thinking_output()
    ThinkingMode-->>REPL: Formatted output

    REPL-->>User: Display thinking + response
```

---

## 11. Sequence Diagram - Headless Execution

```mermaid
sequenceDiagram
    participant CLI
    participant HeadlessMode
    participant REPL
    participant LLM
    participant Output

    CLI->>HeadlessMode: activate(context)
    HeadlessMode->>HeadlessMode: Open input/output streams

    HeadlessMode->>HeadlessMode: read_input()
    HeadlessMode-->>REPL: Input text

    REPL->>REPL: Process with headless prompt
    REPL->>LLM: Execute task

    loop Permission Requests
        LLM-->>REPL: Permission needed
        REPL->>HeadlessMode: handle_permission_request()
        alt Safe Operation
            HeadlessMode-->>REPL: Approve
        else Unsafe Operation
            HeadlessMode-->>REPL: Deny
            HeadlessMode->>HeadlessMode: create_result(failure)
        end
    end

    LLM-->>REPL: Complete response

    REPL->>HeadlessMode: modify_response()
    HeadlessMode->>HeadlessMode: create_result(success)

    HeadlessMode->>HeadlessMode: write_output(result)
    HeadlessMode-->>Output: JSON/Text result

    HeadlessMode->>CLI: Exit with code
```

---

## 12. State Diagram - Mode Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Normal: Application Start

    Normal --> Plan: /plan or auto-detect
    Normal --> Thinking: /think
    Normal --> Headless: --headless flag

    Plan --> Normal: /plan cancel
    Plan --> Normal: /plan execute (complete)
    Plan --> Thinking: /think

    Thinking --> Normal: /normal
    Thinking --> Plan: /plan

    Headless --> [*]: Task Complete
    Headless --> [*]: Error/Timeout

    state Plan {
        [*] --> Creating
        Creating --> HasPlan: Plan created
        HasPlan --> Executing: /plan execute
        Executing --> Complete: Steps done
    }

    state Thinking {
        [*] --> Regular
        Regular --> Deep: /think deep
        Deep --> Regular: /think
    }
```

---

## 13. Activity Diagram - Auto-Activation

```mermaid
flowchart TD
    START([Receive User Input]) --> CHECK{Is Command?}

    CHECK -->|Yes| HANDLE[Handle Command]
    CHECK -->|No| AUTO[Check Auto-Activation]

    AUTO --> PATTERNS{Match Patterns?}

    PATTERNS -->|No| PROCESS[Process Normally]
    PATTERNS -->|Plan Pattern| PLAN_CHECK{Already in<br/>Plan Mode?}
    PATTERNS -->|Thinking Pattern| THINK_CHECK{Already in<br/>Thinking Mode?}

    PLAN_CHECK -->|Yes| PROCESS
    PLAN_CHECK -->|No| SWITCH_PLAN[Switch to Plan Mode]

    THINK_CHECK -->|Yes| PROCESS
    THINK_CHECK -->|No| SUGGEST[Suggest Thinking Mode]

    SWITCH_PLAN --> PROCESS
    SUGGEST --> PROCESS

    HANDLE --> END([Continue])
    PROCESS --> END
```

---

## 14. Activity Diagram - Response Processing

```mermaid
flowchart TD
    START([Receive LLM Response]) --> MODE{Current Mode?}

    MODE -->|Normal| NORMAL[Return unchanged]
    MODE -->|Plan| PLAN[Parse plan structure]
    MODE -->|Thinking| THINK[Extract thinking/response]
    MODE -->|Headless| HEADLESS[Format as JSON/text]

    PLAN --> PLAN_OBJ{Plan found?}
    PLAN_OBJ -->|Yes| STORE_PLAN[Store plan object]
    PLAN_OBJ -->|No| FORMAT_PLAN[Format as markdown]
    STORE_PLAN --> FORMAT_PLAN

    THINK --> MATCH{Has thinking tags?}
    MATCH -->|Yes| EXTRACT[Extract sections]
    MATCH -->|No| PASSTHROUGH[Pass through]

    EXTRACT --> RESULT[Create ThinkingResult]
    RESULT --> FORMAT_THINK[Format output]

    HEADLESS --> CREATE[Create HeadlessResult]
    CREATE --> WRITE[Write to output stream]

    NORMAL --> OUTPUT([Return to User])
    FORMAT_PLAN --> OUTPUT
    PASSTHROUGH --> OUTPUT
    FORMAT_THINK --> OUTPUT
    WRITE --> OUTPUT
```

---

## 15. Component Diagram - Mode System

```mermaid
flowchart LR
    subgraph Input
        USER[User Input]
        CLI[CLI Args]
        FILE[Input File]
    end

    subgraph ModeSystem[Mode System]
        MANAGER[ModeManager]
        MODES[Mode Registry]

        subgraph Modes
            NORMAL[NormalMode]
            PLAN[PlanMode]
            THINK[ThinkingMode]
            HEADLESS[HeadlessMode]
        end
    end

    subgraph Processing
        PROMPT[Prompt Modification]
        RESPONSE[Response Processing]
    end

    subgraph Output
        DISPLAY[Display]
        JSON[JSON Output]
        TODOS[Todo Items]
    end

    USER --> MANAGER
    CLI --> HEADLESS
    FILE --> HEADLESS

    MANAGER --> MODES
    MODES --> NORMAL
    MODES --> PLAN
    MODES --> THINK
    MODES --> HEADLESS

    MODES --> PROMPT
    MODES --> RESPONSE

    RESPONSE --> DISPLAY
    RESPONSE --> JSON
    PLAN --> TODOS
```

---

## 16. Mode Interaction Overview

```
                    ModeManager (Singleton)
                           |
           +---------------+---------------+
           |               |               |
      NormalMode       PlanMode      ThinkingMode      HeadlessMode
           |               |               |               |
           |          +----+----+    +-----+-----+    +----+----+
           |          |         |    |           |    |         |
           |        Plan    PlanStep  ThinkingResult   HeadlessResult
           |                          ThinkingConfig   HeadlessConfig

    Flow:
    1. ModeManager tracks current mode
    2. REPL queries manager for prompt modifications
    3. Modes process responses as needed
    4. State persisted in session
    5. Commands trigger mode switches
```

---

## Notes

- Mode is an abstract base class for extensibility
- ModeManager is singleton for global state
- Each mode has its own data structures
- Modes modify system prompt and responses
- State is serializable for session persistence
- Headless mode has special I/O handling
- Auto-activation uses regex pattern matching
