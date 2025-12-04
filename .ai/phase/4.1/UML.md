# Phase 4.1: Permission System - UML Diagrams

**Phase:** 4.1
**Name:** Permission System
**Dependencies:** Phase 2.1 (Tool System Foundation)

---

## 1. Class Diagram - Permission Models

```mermaid
classDiagram
    class PermissionLevel {
        <<enumeration>>
        ALLOW = "allow"
        ASK = "ask"
        DENY = "deny"
        +__lt__(other) bool
        +__le__(other) bool
        +__gt__(other) bool
        +__ge__(other) bool
    }

    class PermissionCategory {
        <<enumeration>>
        READ = "read_operations"
        WRITE = "write_operations"
        EXECUTE = "execute_operations"
        NETWORK = "network_operations"
        DESTRUCTIVE = "destructive_operations"
        OTHER = "other_operations"
    }

    class PermissionRule {
        +pattern: str
        +permission: PermissionLevel
        +description: str
        +enabled: bool
        +priority: int
        +to_dict() dict
        +from_dict(data)$ PermissionRule
    }

    class PermissionResult {
        +level: PermissionLevel
        +rule: PermissionRule?
        +reason: str
        +allowed: bool
        +needs_confirmation: bool
        +denied: bool
    }

    PermissionRule --> PermissionLevel : has
    PermissionResult --> PermissionLevel : has
    PermissionResult --> PermissionRule : references
```

---

## 2. Class Diagram - Rules and Matching

```mermaid
classDiagram
    class PatternMatcher {
        -_regex_cache: dict
        +match(pattern, tool_name, arguments)$ bool
        +parse_pattern(pattern)$ list
        +specificity(pattern)$ int
        -_match_value(pattern, value)$ bool
        -_is_regex(pattern)$ bool
        -_match_glob(pattern, value)$ bool
        -_match_regex(pattern, value)$ bool
    }

    class RuleSet {
        +rules: list~PermissionRule~
        +default: PermissionLevel
        +add_rule(rule) void
        +remove_rule(pattern) bool
        +get_rule(pattern) PermissionRule?
        +evaluate(tool_name, arguments) PermissionResult
        +to_dict() dict
        +from_dict(data)$ RuleSet
    }

    class PermissionRule {
        +pattern: str
        +permission: PermissionLevel
        +description: str
        +enabled: bool
        +priority: int
    }

    RuleSet o-- PermissionRule : contains
    RuleSet --> PatternMatcher : uses
    RuleSet --> PermissionResult : produces
```

---

## 3. Class Diagram - Permission Checker

```mermaid
classDiagram
    class PermissionChecker {
        +global_rules: RuleSet
        +project_rules: RuleSet?
        +session_rules: RuleSet
        +check(tool_name, arguments) PermissionResult
        +add_session_rule(rule) void
        +remove_session_rule(pattern) bool
        +clear_session_rules() void
        +get_session_rules() list~PermissionRule~
        +allow_always(tool_name, arguments) void
        +deny_always(tool_name, arguments) void
        +from_config(config)$ PermissionChecker
    }

    class RuleSet {
        +rules: list~PermissionRule~
        +default: PermissionLevel
        +evaluate(tool_name, arguments) PermissionResult
    }

    class PermissionError {
        +result: PermissionResult
        +tool_name: str
        +arguments: dict
        -_format_message() str
    }

    PermissionChecker --> RuleSet : uses
    PermissionChecker --> PermissionResult : produces
    PermissionChecker ..> PermissionError : raises
```

---

## 4. Class Diagram - Confirmation Prompts

```mermaid
classDiagram
    class ConfirmationChoice {
        <<enumeration>>
        ALLOW = "allow"
        ALLOW_ALWAYS = "allow_always"
        DENY = "deny"
        DENY_ALWAYS = "deny_always"
        TIMEOUT = "timeout"
    }

    class ConfirmationRequest {
        +tool_name: str
        +arguments: dict
        +description: str
        +timeout: float
    }

    class PermissionPrompt {
        +input_handler: callable
        +output_handler: callable
        +format_request(request) str
        +confirm(request) ConfirmationChoice
        +confirm_async(request) ConfirmationChoice
        -_parse_response(response) ConfirmationChoice
    }

    PermissionPrompt --> ConfirmationRequest : accepts
    PermissionPrompt --> ConfirmationChoice : returns
```

---

## 5. Class Diagram - Configuration

```mermaid
classDiagram
    class PermissionConfig {
        +GLOBAL_FILE: str
        +PROJECT_FILE: str
        +get_global_path()$ Path
        +get_project_path(project_root)$ Path?
        +load_global()$ RuleSet
        +load_project(project_root)$ RuleSet?
        +save_global(rules) void
        +save_project(project_root, rules) void
        +get_default_rules()$ RuleSet
        +reset_to_defaults()$ void
    }

    class DEFAULT_RULES {
        <<list~PermissionRule~>>
        tool:read → ALLOW
        tool:glob → ALLOW
        tool:write → ASK
        tool:bash → ASK
        tool:bash,arg:*rm -rf* → DENY
        ...
    }

    PermissionConfig --> RuleSet : creates
    PermissionConfig --> DEFAULT_RULES : uses
```

---

## 6. Sequence Diagram - Permission Check Flow

```mermaid
sequenceDiagram
    participant TE as ToolExecutor
    participant PC as PermissionChecker
    participant SR as SessionRules
    participant PR as ProjectRules
    participant GR as GlobalRules

    TE->>PC: check(tool_name, arguments)

    PC->>SR: evaluate(tool_name, arguments)
    SR-->>PC: PermissionResult

    alt Session rule matched
        PC-->>TE: PermissionResult (from session)
    else No session rule
        PC->>PR: evaluate(tool_name, arguments)
        PR-->>PC: PermissionResult

        alt Project rule matched
            PC-->>TE: PermissionResult (from project)
        else No project rule
            PC->>GR: evaluate(tool_name, arguments)
            GR-->>PC: PermissionResult

            alt Global rule matched
                PC-->>TE: PermissionResult (from global)
            else No rule matched
                PC-->>TE: PermissionResult (default)
            end
        end
    end
```

---

## 7. Sequence Diagram - User Confirmation Flow

```mermaid
sequenceDiagram
    participant TE as ToolExecutor
    participant PC as PermissionChecker
    participant PP as PermissionPrompt
    participant User

    TE->>PC: check("bash", {command: "ls"})
    PC-->>TE: PermissionResult(ASK)

    TE->>PP: confirm_async(request)
    PP->>PP: format_request()
    PP->>User: Display prompt

    User-->>PP: Input "A" (Allow Always)
    PP-->>TE: ALLOW_ALWAYS

    TE->>TE: create_rule_from_choice()
    TE->>PC: add_session_rule(rule)

    TE->>TE: Execute tool

    Note right of PC: Future calls for "bash"<br/>will be ALLOWED
```

---

## 8. Sequence Diagram - Rule Evaluation

```mermaid
sequenceDiagram
    participant RS as RuleSet
    participant PM as PatternMatcher
    participant Rules as Rules List

    RS->>RS: evaluate(tool_name, arguments)

    loop For each enabled rule
        RS->>Rules: Get rule
        Rules-->>RS: PermissionRule

        RS->>PM: match(pattern, tool_name, arguments)
        PM->>PM: parse_pattern()
        PM->>PM: _match_value()

        alt Pattern matches
            PM-->>RS: True
            RS->>PM: specificity(pattern)
            PM-->>RS: Score
            RS->>RS: Add to matches
        else No match
            PM-->>RS: False
        end
    end

    RS->>RS: Sort matches by priority, specificity, restrictiveness
    RS-->>RS: Return best match result
```

---

## 9. State Diagram - Permission Check States

```mermaid
stateDiagram-v2
    [*] --> Checking: check() called

    Checking --> SessionCheck: Check session rules
    SessionCheck --> SessionMatched: Rule matches
    SessionCheck --> ProjectCheck: No match

    SessionMatched --> ReturnResult: Return result
    ProjectCheck --> ProjectMatched: Rule matches
    ProjectCheck --> GlobalCheck: No match

    ProjectMatched --> ReturnResult
    GlobalCheck --> GlobalMatched: Rule matches
    GlobalCheck --> UseDefault: No match

    GlobalMatched --> ReturnResult
    UseDefault --> ReturnResult: Use default level

    ReturnResult --> [*]: Return PermissionResult
```

---

## 10. State Diagram - Confirmation Flow

```mermaid
stateDiagram-v2
    [*] --> Prompting: ASK permission

    Prompting --> WaitingInput: Display prompt

    WaitingInput --> ParseResponse: User input
    WaitingInput --> Timeout: Timeout exceeded

    ParseResponse --> Allow: Input "a"
    ParseResponse --> AllowAlways: Input "A"
    ParseResponse --> Deny: Input "d"
    ParseResponse --> DenyAlways: Input "D"
    ParseResponse --> Deny: Invalid input

    AllowAlways --> CreateRule: Create ALLOW rule
    DenyAlways --> CreateRule: Create DENY rule

    CreateRule --> AddSession: Add session rule

    Allow --> Execute: Proceed
    AllowAlways --> Execute
    AddSession --> Execute
    AddSession --> BlockExecution

    Deny --> BlockExecution
    DenyAlways --> BlockExecution
    Timeout --> BlockExecution

    Execute --> [*]
    BlockExecution --> [*]: Raise PermissionError
```

---

## 11. Activity Diagram - Pattern Matching

```mermaid
flowchart TD
    START([match pattern]) --> PARSE[Parse pattern into components]

    PARSE --> LOOP{More components?}

    LOOP -->|Yes| GET[Get component type, name, pattern]
    LOOP -->|No| SUCCESS([Return True])

    GET --> CHECK_TYPE{Component type?}

    CHECK_TYPE -->|tool| MATCH_TOOL[Match tool name]
    CHECK_TYPE -->|arg| GET_ARG[Get argument value]
    CHECK_TYPE -->|category| GET_CAT[Get tool category]

    MATCH_TOOL --> TOOL_MATCH{Matches?}
    TOOL_MATCH -->|Yes| LOOP
    TOOL_MATCH -->|No| FAIL([Return False])

    GET_ARG --> ARG_EXISTS{Arg exists?}
    ARG_EXISTS -->|No| FAIL
    ARG_EXISTS -->|Yes| MATCH_ARG[Match argument value]
    MATCH_ARG --> ARG_MATCH{Matches?}
    ARG_MATCH -->|Yes| LOOP
    ARG_MATCH -->|No| FAIL

    GET_CAT --> CAT_MATCH{Category matches?}
    CAT_MATCH -->|Yes| LOOP
    CAT_MATCH -->|No| FAIL
```

---

## 12. Component Diagram - Permission Package

```mermaid
flowchart TB
    subgraph PermPkg["src/opencode/permissions/"]
        INIT["__init__.py"]
        MODELS["models.py<br/>PermissionLevel, Rule, Result"]
        RULES["rules.py<br/>PatternMatcher, RuleSet"]
        CHECKER["checker.py<br/>PermissionChecker"]
        PROMPT["prompt.py<br/>PermissionPrompt"]
        CONFIG["config.py<br/>PermissionConfig"]
    end

    subgraph ToolsPkg["src/opencode/tools/"]
        EXECUTOR["executor.py"]
        BASE["base.py"]
    end

    subgraph ConfigPkg["src/opencode/config/"]
        SETTINGS["settings.py"]
    end

    CHECKER --> MODELS
    CHECKER --> RULES
    CHECKER --> CONFIG

    RULES --> MODELS

    PROMPT --> MODELS

    CONFIG --> RULES
    CONFIG --> MODELS
    CONFIG --> SETTINGS

    EXECUTOR --> CHECKER
    EXECUTOR --> PROMPT
    EXECUTOR --> BASE

    INIT --> MODELS
    INIT --> RULES
    INIT --> CHECKER
    INIT --> PROMPT
    INIT --> CONFIG
```

---

## 13. Data Flow Diagram - Permission Decision

```mermaid
flowchart LR
    subgraph Input
        TN[Tool Name]
        ARGS[Arguments]
    end

    subgraph RuleSources["Rule Sources"]
        SESSION[Session Rules]
        PROJECT[Project Rules]
        GLOBAL[Global Rules]
        DEFAULT[Default Level]
    end

    subgraph Processing
        MATCHER[Pattern Matcher]
        EVALUATOR[Rule Evaluator]
    end

    subgraph Output
        RESULT[PermissionResult]
    end

    TN --> MATCHER
    ARGS --> MATCHER

    SESSION --> EVALUATOR
    PROJECT --> EVALUATOR
    GLOBAL --> EVALUATOR
    DEFAULT --> EVALUATOR

    MATCHER --> EVALUATOR
    EVALUATOR --> RESULT
```

---

## 14. Entity Relationship - Permission Configuration

```mermaid
erDiagram
    PERMISSION_CONFIG ||--o{ RULE_SET : contains
    RULE_SET ||--o{ PERMISSION_RULE : contains
    PERMISSION_RULE }o--|| PERMISSION_LEVEL : has

    PERMISSION_CONFIG {
        string location
        string type
    }

    RULE_SET {
        string default_level
        list rules
    }

    PERMISSION_RULE {
        string pattern
        string permission
        string description
        bool enabled
        int priority
    }

    PERMISSION_LEVEL {
        string ALLOW
        string ASK
        string DENY
    }
```

---

## 15. Confirmation Prompt Display

```
┌────────────────────────────────────────────────────────────────┐
│  Permission Required                                            │
├────────────────────────────────────────────────────────────────┤
│  Tool: bash                                                     │
│  command: git commit -m "Update readme"                         │
│                                                                 │
│  Confirm shell commands                                         │
│                                                                 │
│  [a] Allow    [A] Allow Always    [d] Deny    [D] Deny Always   │
└────────────────────────────────────────────────────────────────┘
```

---

## Notes

- Permission levels are comparable: ALLOW < ASK < DENY
- More specific rules take precedence over general rules
- Session rules have highest priority
- Default rules block dangerous operations
- User can create session rules via "Allow/Deny Always"
- Pattern matching supports glob and regex
