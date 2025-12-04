# Phase 1.3: Basic REPL Shell - UML Diagrams

**Phase:** 1.3
**Name:** Basic REPL Shell
**Dependencies:** Phase 1.1, Phase 1.2

---

## 1. Class Diagram - REPL Components

```mermaid
classDiagram
    class OpenCodeREPL {
        -_config: OpenCodeConfig
        -_console: Console
        -_input: InputHandler
        -_output: OutputRenderer
        -_status: StatusBar
        -_running: bool
        -_callbacks: List~Callable~
        +run() int
        +stop() void
        +on_input(callback) void
        -_show_welcome() void
        -_show_shortcuts() void
        -_process_input(text) void
        -_get_prompt() str
    }

    class InputHandler {
        -_history: FileHistory
        -_bindings: KeyBindings
        -_session: PromptSession
        +get_input(prompt, multiline) str?
        -_create_bindings() KeyBindings
    }

    class OutputRenderer {
        -_console: Console
        -_theme: Dict
        +print(content, style) void
        +print_markdown(content) void
        +print_code(code, language) void
        +print_panel(content, title) void
        +print_error(message) void
        +print_warning(message) void
        +clear() void
    }

    class StatusBar {
        -_config: OpenCodeConfig
        -_model: str
        -_tokens_used: int
        -_tokens_max: int
        -_mode: str
        -_status: str
        -_visible: bool
        +set_model(model) void
        +set_tokens(used, max) void
        +set_mode(mode) void
        +set_status(status) void
        +render(width) str
    }

    OpenCodeREPL --> InputHandler
    OpenCodeREPL --> OutputRenderer
    OpenCodeREPL --> StatusBar
    OpenCodeREPL --> OpenCodeConfig
```

---

## 2. Sequence Diagram - REPL Startup

```mermaid
sequenceDiagram
    participant U as User
    participant CLI as main.py
    participant CL as ConfigLoader
    participant R as OpenCodeREPL
    participant I as InputHandler
    participant O as OutputRenderer
    participant S as StatusBar

    U->>CLI: opencode
    CLI->>CL: load_all()
    CL-->>CLI: OpenCodeConfig

    CLI->>R: OpenCodeREPL(config)
    R->>I: InputHandler(history_path)
    R->>O: OutputRenderer(console, theme)
    R->>S: StatusBar(config)

    CLI->>R: run()
    R->>O: print(welcome)
    O-->>U: Welcome message

    loop REPL Loop
        R->>I: get_input(prompt)
        I-->>U: Display prompt
        U->>I: Enter text
        I-->>R: user_input

        alt Empty input
            R->>R: continue
        else Input is "?"
            R->>O: print(shortcuts)
        else Normal input
            R->>R: _process_input(text)
            R->>O: print(response)
        end
    end

    Note over R: Ctrl+D pressed
    R->>O: print("Goodbye!")
    R-->>CLI: return 0
    CLI-->>U: Exit
```

---

## 3. Sequence Diagram - Keyboard Shortcuts

```mermaid
sequenceDiagram
    participant U as User
    participant PT as prompt_toolkit
    participant KB as KeyBindings
    participant R as OpenCodeREPL
    participant O as OutputRenderer

    Note over U,O: Escape - Cancel Input
    U->>PT: Press Escape
    PT->>KB: escape event
    KB->>PT: buffer.reset()
    PT-->>U: Input cleared

    Note over U,O: Ctrl+L - Clear Screen
    U->>PT: Press Ctrl+L
    PT->>KB: c-l event
    KB->>PT: renderer.clear()
    PT-->>U: Screen cleared

    Note over U,O: Ctrl+C - Interrupt
    U->>PT: Press Ctrl+C
    PT->>R: KeyboardInterrupt
    R->>O: print("Interrupted")
    O-->>U: Shows interrupted
    R->>R: continue loop

    Note over U,O: Ctrl+D - Exit
    U->>PT: Press Ctrl+D
    PT->>R: EOFError (None)
    R->>O: print("Goodbye!")
    R-->>R: break loop
```

---

## 4. State Diagram - REPL State

```mermaid
stateDiagram-v2
    [*] --> Initializing: Start

    Initializing --> ShowingWelcome: Config loaded
    ShowingWelcome --> WaitingInput: Welcome displayed

    WaitingInput --> ProcessingInput: Input received
    WaitingInput --> ShowingShortcuts: "?" entered
    WaitingInput --> Exiting: Ctrl+D / EOF

    ProcessingInput --> DisplayingOutput: Process complete
    ProcessingInput --> Interrupted: Ctrl+C

    DisplayingOutput --> WaitingInput: Output complete
    ShowingShortcuts --> WaitingInput: Shortcuts shown

    Interrupted --> WaitingInput: Continue

    Exiting --> [*]: Cleanup complete

    state WaitingInput {
        [*] --> Idle
        Idle --> Typing: Key pressed
        Typing --> Idle: Escape
        Typing --> Multiline: Shift+Enter
        Multiline --> Typing: More input
        Typing --> [*]: Enter
    }
```

---

## 5. Component Diagram

```mermaid
flowchart TB
    subgraph CLI["CLI Layer"]
        MAIN[main.py]
        REPL[repl.py]
        THEMES[themes.py]
        STATUS[status.py]
    end

    subgraph External["External Libraries"]
        RICH[rich]
        PT[prompt_toolkit]
    end

    subgraph Core["Core Layer (Phase 1.1/1.2)"]
        CONFIG[ConfigLoader]
        LOGGING[Logging]
    end

    MAIN --> REPL
    MAIN --> CONFIG
    REPL --> THEMES
    REPL --> STATUS
    REPL --> RICH
    REPL --> PT
    REPL --> LOGGING
    STATUS --> CONFIG
```

---

## 6. Activity Diagram - Input Processing

```mermaid
flowchart TD
    START([Start REPL]) --> WELCOME[Show Welcome]
    WELCOME --> PROMPT[Display Prompt]

    PROMPT --> INPUT{Wait for Input}

    INPUT -->|Text entered| CHECK_EMPTY{Is empty?}
    INPUT -->|Ctrl+D| EXIT[Show Goodbye]
    INPUT -->|Ctrl+C| INTERRUPT[Show Interrupted]

    CHECK_EMPTY -->|Yes| PROMPT
    CHECK_EMPTY -->|No| CHECK_HELP{Is "?"?}

    CHECK_HELP -->|Yes| SHORTCUTS[Show Shortcuts]
    CHECK_HELP -->|No| PROCESS[Process Input]

    SHORTCUTS --> PROMPT
    PROCESS --> OUTPUT[Display Output]
    OUTPUT --> PROMPT

    INTERRUPT --> PROMPT

    EXIT --> END([Exit with 0])
```

---

## 7. Status Bar Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Terminal Width                              │
├─────────────────────────────────────────────────────────────────────┤
│ [Model]          [Tokens: used/max]          [Mode] | [Status]      │
│ ◀─ Left ─▶       ◀──── Center ────▶         ◀────── Right ──────▶  │
└─────────────────────────────────────────────────────────────────────┘

Example (80 columns):
┌──────────────────────────────────────────────────────────────────────────────┐
│ gpt-5                    Tokens: 1,234/128,000                Normal | Ready │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Theme Color Mapping

```mermaid
flowchart LR
    subgraph Dark["Dark Theme"]
        D_BG["#1a1b26 Background"]
        D_FG["#c0caf5 Foreground"]
        D_ACC["#7aa2f7 Accent"]
        D_OK["#9ece6a Success"]
        D_WARN["#e0af68 Warning"]
        D_ERR["#f7768e Error"]
    end

    subgraph Light["Light Theme"]
        L_BG["#f5f5f5 Background"]
        L_FG["#1a1b26 Foreground"]
        L_ACC["#2563eb Accent"]
        L_OK["#22c55e Success"]
        L_WARN["#eab308 Warning"]
        L_ERR["#ef4444 Error"]
    end

    subgraph Usage["Usage"]
        U_TITLE["Title/Headers → Accent"]
        U_CODE["Code → Foreground"]
        U_DONE["Success → Success"]
        U_ALERT["Warnings → Warning"]
        U_FAIL["Errors → Error"]
    end
```

---

## 9. Package Dependencies

```mermaid
flowchart TD
    subgraph phase1_3["Phase 1.3 - REPL"]
        CLI_REPL[cli/repl.py]
        CLI_THEMES[cli/themes.py]
        CLI_STATUS[cli/status.py]
    end

    subgraph phase1_2["Phase 1.2 - Config"]
        CONFIG[config/loader.py]
        MODELS[config/models.py]
    end

    subgraph phase1_1["Phase 1.1 - Foundation"]
        INTERFACES[core/interfaces.py]
        ERRORS[core/errors.py]
        LOGGING[core/logging.py]
    end

    subgraph external["External"]
        RICH[rich]
        PROMPT[prompt_toolkit]
    end

    CLI_REPL --> CLI_THEMES
    CLI_REPL --> CLI_STATUS
    CLI_REPL --> CONFIG
    CLI_REPL --> LOGGING
    CLI_REPL --> RICH
    CLI_REPL --> PROMPT
    CLI_STATUS --> MODELS
```

---

## Notes

- Phase 1.3 creates the UI shell without AI integration
- Callbacks system allows future phases to plug in processing
- Status bar is prepared but token values are placeholders
- Theme system supports future customization
