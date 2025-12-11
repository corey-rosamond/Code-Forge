# Phase 5.2: Context Management - UML Diagrams

**Phase:** 5.2
**Name:** Context Management
**Dependencies:** Phase 5.1 (Session Management), Phase 3.2 (LangChain Integration)

---

## 1. Class Diagram - Token Counting

```mermaid
classDiagram
    class TokenCounter {
        <<abstract>>
        +count(text: str) int
        +count_messages(messages: list) int
        +count_message(message: dict) int
    }

    class TiktokenCounter {
        +model: str
        -_encoding: Encoding
        -_fallback: ApproximateCounter
        +MESSAGE_OVERHEAD: int$
        +REPLY_OVERHEAD: int$
        +__init__(model: str?)
        +count(text: str) int
        +count_messages(messages: list) int
    }

    class ApproximateCounter {
        +tokens_per_word: float
        +tokens_per_char: float
        -_word_pattern: Pattern
        +__init__(tokens_per_word, tokens_per_char)
        +count(text: str) int
        +count_messages(messages: list) int
    }

    class CachingCounter {
        -_counter: TokenCounter
        -_cache: dict
        -_max_size: int
        +__init__(counter, max_cache_size)
        +count(text: str) int
        +count_messages(messages: list) int
        +clear_cache() void
    }

    TokenCounter <|-- TiktokenCounter
    TokenCounter <|-- ApproximateCounter
    TokenCounter <|-- CachingCounter
    CachingCounter o-- TokenCounter : wraps
    TiktokenCounter --> ApproximateCounter : fallback
```

---

## 2. Class Diagram - Context Limits

```mermaid
classDiagram
    class ContextBudget {
        +total: int
        +system_prompt: int
        +conversation: int
        +tools: int
        +response_reserve: int
        +available: int
        +conversation_budget: int
        +update_system_prompt(tokens) void
        +update_tools(tokens) void
        +update_conversation(tokens) void
    }

    class ContextLimits {
        +model: str
        +max_tokens: int
        +max_output_tokens: int
        +reserved_tokens: int
        +for_model(model)$ ContextLimits
        +effective_limit: int
    }

    class ContextTracker {
        +limits: ContextLimits
        +counter: TokenCounter
        +budget: ContextBudget
        +messages: list
        +system_prompt: str
        +tool_definitions: list
        +for_model(model)$ ContextTracker
        +set_system_prompt(prompt) int
        +set_tool_definitions(tools) int
        +update(messages) int
        +add_message(message) int
        +current_tokens() int
        +exceeds_limit() bool
        +overflow_amount() int
        +available_tokens() int
        +usage_percentage() float
        +reset() void
    }

    ContextTracker --> ContextLimits : uses
    ContextTracker --> ContextBudget : uses
    ContextTracker --> TokenCounter : uses
```

---

## 3. Class Diagram - Truncation Strategies

```mermaid
classDiagram
    class TruncationStrategy {
        <<abstract>>
        +truncate(messages, target_tokens, counter) list
        #_count_messages(messages, counter) int
    }

    class SlidingWindowStrategy {
        +window_size: int
        +preserve_system: bool
        +__init__(window_size, preserve_system)
        +truncate(messages, target_tokens, counter) list
    }

    class TokenBudgetStrategy {
        +preserve_system: bool
        +__init__(preserve_system)
        +truncate(messages, target_tokens, counter) list
    }

    class SmartTruncationStrategy {
        +preserve_first: int
        +preserve_last: int
        +preserve_system: bool
        +__init__(preserve_first, preserve_last, preserve_system)
        +truncate(messages, target_tokens, counter) list
    }

    class SelectiveTruncationStrategy {
        +preserve_roles: set
        +preserve_marked: bool
        +mark_key: str
        +truncate(messages, target_tokens, counter) list
    }

    class CompositeStrategy {
        +strategies: list~TruncationStrategy~
        +__init__(strategies)
        +truncate(messages, target_tokens, counter) list
    }

    TruncationStrategy <|-- SlidingWindowStrategy
    TruncationStrategy <|-- TokenBudgetStrategy
    TruncationStrategy <|-- SmartTruncationStrategy
    TruncationStrategy <|-- SelectiveTruncationStrategy
    TruncationStrategy <|-- CompositeStrategy
    CompositeStrategy o-- TruncationStrategy : contains
```

---

## 4. Class Diagram - Compaction

```mermaid
classDiagram
    class ContextCompactor {
        +llm: Any
        +summary_prompt: str
        +max_summary_tokens: int
        +min_messages_to_summarize: int
        +__init__(llm, summary_prompt, max_summary_tokens)
        +compact(messages, target_tokens, counter, preserve_last) list
        +summarize_messages(messages) str
        -_format_for_summary(messages) str
    }

    class ToolResultCompactor {
        +max_result_tokens: int
        +truncation_message: str
        +__init__(max_result_tokens, truncation_message)
        +compact_result(result, counter) str
        +compact_message(message, counter) dict
    }

    ContextCompactor --> TokenCounter : uses
    ToolResultCompactor --> TokenCounter : uses
```

---

## 5. Class Diagram - Context Manager

```mermaid
classDiagram
    class TruncationMode {
        <<enumeration>>
        SLIDING_WINDOW = "sliding_window"
        TOKEN_BUDGET = "token_budget"
        SMART = "smart"
        SUMMARIZE = "summarize"
    }

    class ContextManager {
        +model: str
        +mode: TruncationMode
        +auto_truncate: bool
        +counter: TokenCounter
        +tracker: ContextTracker
        +strategy: TruncationStrategy
        +compactor: ContextCompactor?
        +tool_compactor: ToolResultCompactor
        -_messages: list
        -_system_prompt: str
        +__init__(model, mode, llm, auto_truncate)
        +set_system_prompt(prompt) int
        +set_tool_definitions(tools) int
        +add_message(message) void
        +add_messages(messages) void
        +get_messages() list
        +get_context_for_request() list
        +compact_if_needed(threshold) bool
        +token_usage: int
        +available_tokens: int
        +usage_percentage: float
        +is_near_limit: bool
        +reset() void
        +get_stats() dict
    }

    ContextManager --> TruncationMode : uses
    ContextManager --> TokenCounter : uses
    ContextManager --> ContextTracker : uses
    ContextManager --> TruncationStrategy : uses
    ContextManager --> ContextCompactor : uses
    ContextManager --> ToolResultCompactor : uses
```

---

## 6. Package Diagram

```mermaid
flowchart TB
    subgraph ContextPkg["src/forge/context/"]
        INIT["__init__.py"]
        TOKENS["tokens.py<br/>TokenCounter, TiktokenCounter"]
        LIMITS["limits.py<br/>ContextLimits, ContextTracker"]
        STRATEGIES["strategies.py<br/>TruncationStrategy implementations"]
        COMPACTION["compaction.py<br/>ContextCompactor, ToolResultCompactor"]
        MANAGER["manager.py<br/>ContextManager, TruncationMode"]
    end

    subgraph SessionsPkg["src/forge/sessions/"]
        SESSION_MGR["manager.py"]
    end

    subgraph LangChainPkg["src/forge/langchain/"]
        LLM["llm.py<br/>OpenRouterLLM"]
    end

    MANAGER --> TOKENS
    MANAGER --> LIMITS
    MANAGER --> STRATEGIES
    MANAGER --> COMPACTION

    SESSION_MGR --> MANAGER
    COMPACTION --> LLM

    INIT --> TOKENS
    INIT --> LIMITS
    INIT --> STRATEGIES
    INIT --> COMPACTION
    INIT --> MANAGER
```

---

## 7. Sequence Diagram - Add Message with Truncation

```mermaid
sequenceDiagram
    participant Client
    participant Manager as ContextManager
    participant Tracker as ContextTracker
    participant Counter as TokenCounter
    participant Strategy as TruncationStrategy

    Client->>Manager: add_message(message)

    alt Tool result message
        Manager->>Manager: tool_compactor.compact_message()
    end

    Manager->>Manager: _messages.append(message)

    Manager->>Tracker: add_message(message)
    Tracker->>Counter: count_message(message)
    Counter-->>Tracker: token_count
    Tracker->>Tracker: budget.conversation += tokens
    Tracker-->>Manager: token_count

    alt auto_truncate enabled
        Manager->>Tracker: exceeds_limit()

        alt Over limit
            Tracker-->>Manager: True
            Manager->>Manager: _truncate()

            Manager->>Strategy: truncate(messages, target, counter)
            Strategy->>Counter: count_messages()
            Counter-->>Strategy: current_count

            loop Until within budget
                Strategy->>Strategy: Remove messages
                Strategy->>Counter: count_messages()
            end

            Strategy-->>Manager: truncated_messages

            Manager->>Manager: _messages = truncated
            Manager->>Tracker: update(truncated)
        else Under limit
            Tracker-->>Manager: False
        end
    end
```

---

## 8. Sequence Diagram - Smart Truncation

```mermaid
sequenceDiagram
    participant Manager as ContextManager
    participant Smart as SmartTruncationStrategy
    participant Counter as TokenCounter

    Manager->>Smart: truncate(messages, target_tokens, counter)

    Smart->>Smart: Separate system messages

    Smart->>Smart: Check if small enough
    alt Messages ≤ preserve_first + preserve_last
        Smart-->>Manager: All messages
    else Messages need truncation
        Smart->>Smart: first_msgs = messages[:preserve_first]
        Smart->>Smart: last_msgs = messages[-preserve_last:]
        Smart->>Smart: Add truncation marker

        loop While over budget
            Smart->>Counter: count_messages(result)
            Counter-->>Smart: token_count

            alt Over budget
                Smart->>Smart: Remove from last_msgs
            else Within budget
                Smart-->>Manager: result
            end
        end
    end
```

---

## 9. Sequence Diagram - Context Compaction

```mermaid
sequenceDiagram
    participant Manager as ContextManager
    participant Compactor as ContextCompactor
    participant LLM
    participant Counter as TokenCounter

    Manager->>Manager: compact_if_needed(threshold=0.9)

    Manager->>Manager: Check usage_percentage()

    alt Usage > threshold
        Manager->>Compactor: compact(messages, target, counter)

        Compactor->>Compactor: Separate system messages
        Compactor->>Compactor: Split to_summarize / to_preserve

        alt Enough messages to summarize
            Compactor->>Compactor: Format messages

            Compactor->>LLM: ainvoke(summary_prompt)
            LLM-->>Compactor: summary_text

            Compactor->>Compactor: Create summary message

            Compactor->>Counter: count_messages(result)

            alt Within budget
                Compactor-->>Manager: compacted_messages
                Manager->>Manager: _messages = compacted
            else Still over budget
                Compactor-->>Manager: original_messages
            end
        else Too few messages
            Compactor-->>Manager: original_messages
        end

        Manager-->>Manager: True/False
    else Usage OK
        Manager-->>Manager: False
    end
```

---

## 10. State Diagram - Context State

```mermaid
stateDiagram-v2
    [*] --> Empty: ContextManager()

    Empty --> WithSystemPrompt: set_system_prompt()
    Empty --> WithMessages: add_message()

    WithSystemPrompt --> WithMessages: add_message()

    WithMessages --> WithMessages: add_message()
    WithMessages --> CheckLimit: auto_truncate check

    CheckLimit --> WithMessages: Under limit
    CheckLimit --> Truncating: Over limit

    Truncating --> WithMessages: Strategy applied

    WithMessages --> Compacting: compact_if_needed()
    Compacting --> WithMessages: Compaction complete

    WithMessages --> Ready: get_context_for_request()
    Ready --> WithMessages: Continue

    WithMessages --> Empty: reset()
```

---

## 11. State Diagram - Token Budget

```mermaid
stateDiagram-v2
    [*] --> Allocated: ContextBudget created

    state Allocated {
        [*] --> Available

        Available --> SystemAllocated: update_system_prompt()
        SystemAllocated --> ToolsAllocated: update_tools()
        ToolsAllocated --> ConversationAllocated: update_conversation()

        ConversationAllocated --> Available: reset allocations

        state ConversationAllocated {
            [*] --> UnderBudget
            UnderBudget --> NearLimit: usage > 80%
            NearLimit --> OverBudget: usage > 100%
            OverBudget --> UnderBudget: truncation
        }
    }
```

---

## 12. Activity Diagram - Message Addition Flow

```mermaid
flowchart TD
    START([add_message]) --> IS_TOOL{Is tool<br/>result?}

    IS_TOOL -->|Yes| COMPACT_TOOL[Compact tool result]
    IS_TOOL -->|No| APPEND

    COMPACT_TOOL --> APPEND[Append to messages]

    APPEND --> COUNT[Count message tokens]
    COUNT --> UPDATE[Update tracker]

    UPDATE --> AUTO{auto_truncate<br/>enabled?}

    AUTO -->|No| DONE([Done])
    AUTO -->|Yes| CHECK_LIMIT{Exceeds<br/>limit?}

    CHECK_LIMIT -->|No| DONE
    CHECK_LIMIT -->|Yes| TRUNCATE[Apply truncation strategy]

    TRUNCATE --> UPDATE_MESSAGES[Update message list]
    UPDATE_MESSAGES --> UPDATE_TRACKER[Update tracker]
    UPDATE_TRACKER --> DONE
```

---

## 13. Activity Diagram - Truncation Strategy Selection

```mermaid
flowchart TD
    START([Select Strategy]) --> MODE{Truncation<br/>Mode?}

    MODE -->|SLIDING_WINDOW| SW[SlidingWindowStrategy]
    MODE -->|TOKEN_BUDGET| TB[TokenBudgetStrategy]
    MODE -->|SMART| SM[SmartTruncationStrategy]
    MODE -->|SUMMARIZE| SUM[CompositeStrategy]

    SW --> RETURN([Return strategy])
    TB --> RETURN
    SM --> RETURN

    SUM --> COMPOSITE[SmartTruncation + TokenBudget]
    COMPOSITE --> RETURN
```

---

## 14. Data Flow Diagram

```mermaid
flowchart LR
    subgraph Input
        MSG[Messages]
        SYS[System Prompt]
        TOOLS[Tool Definitions]
    end

    subgraph Processing
        COUNTER[TokenCounter]
        TRACKER[ContextTracker]
        STRATEGY[TruncationStrategy]
        COMPACTOR[ContextCompactor]
    end

    subgraph Output
        CONTEXT[Context for LLM]
        STATS[Usage Stats]
    end

    MSG --> COUNTER
    SYS --> COUNTER
    TOOLS --> COUNTER

    COUNTER --> TRACKER
    TRACKER --> STRATEGY
    STRATEGY --> COMPACTOR

    TRACKER --> STATS
    COMPACTOR --> CONTEXT
```

---

## 15. Component Interaction

```mermaid
flowchart TB
    subgraph ContextManager
        MANAGER[ContextManager]
    end

    subgraph TokenCounting
        TIKTOKEN[TiktokenCounter]
        APPROX[ApproximateCounter]
        CACHE[CachingCounter]
    end

    subgraph Tracking
        LIMITS[ContextLimits]
        BUDGET[ContextBudget]
        TRACKER[ContextTracker]
    end

    subgraph Strategies
        SLIDING[SlidingWindowStrategy]
        TOKEN_BUDGET[TokenBudgetStrategy]
        SMART[SmartTruncationStrategy]
        COMPOSITE[CompositeStrategy]
    end

    subgraph Compaction
        CTX_COMPACT[ContextCompactor]
        TOOL_COMPACT[ToolResultCompactor]
    end

    MANAGER --> CACHE
    CACHE --> TIKTOKEN
    TIKTOKEN --> APPROX

    MANAGER --> TRACKER
    TRACKER --> LIMITS
    TRACKER --> BUDGET

    MANAGER --> COMPOSITE
    COMPOSITE --> SMART
    COMPOSITE --> TOKEN_BUDGET

    MANAGER --> CTX_COMPACT
    MANAGER --> TOOL_COMPACT
```

---

## 16. Token Budget Visualization

```
Total Context Window: 200,000 tokens
├── System Prompt:      2,000 tokens (1%)
├── Tool Definitions:   5,000 tokens (2.5%)
├── Response Reserve:   4,096 tokens (2%)
└── Conversation:     188,904 tokens (94.5%)
    ├── Used:          50,000 tokens
    └── Available:    138,904 tokens

Effective Limit = Total - Response Reserve - Reserved
                = 200,000 - 4,096 - 1,000
                = 194,904 tokens
```

---

## Notes

- Token counting uses tiktoken when available, falls back to approximation
- Caching improves performance for repeated text
- Multiple truncation strategies available for different use cases
- Summarization requires LLM but provides best context preservation
- Tool result compaction prevents large outputs from consuming context
- Auto-truncation ensures context never exceeds model limits
